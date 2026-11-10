"""P2-CU19 · Sincronizar operaciones pendientes (AC-19.2 a AC-19.9, AC-19.12, AC-T.2).

**Una transacción por operación.** Cada operación se procesa y se confirma por separado: una que
falla no tumba las demás, y lo ya confirmado sobrevive aunque el lote se corte a la mitad.

**Idempotencia (RN35).** El registro en `operaciones_sync` se inserta en la misma transacción que
el efecto (la reserva o la venta). Si dos envíos del mismo UUID compiten, el segundo choca con
`UNIQUE (id_tenant, uuid_operacion)` al terminar, se deshace entero (también su reserva) y devuelve
el resultado guardado por el primero. Nunca hay doble efecto.

**Dinero (RN38, RN40).** Una compra cobrada nunca queda `rechazada`: si no puede completarse, el
pago queda `confirmado`, la retención se devuelve y se abre un conflicto para reembolsarla (CU20).

Las reglas de stock y de cobro no se copian: se reutilizan `ReservaServicio.registrar` (CU15) y las
piezas sin `commit` de `PagoServicio` (CU16).
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Optional

from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from core.errors import AuthorizationError, ConflictError, DomainError, NotFoundError
from core.tiempo import ahora
from integrations.stripe_service import ErrorPasarela, PasarelaPagos
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu15_comprar_plataforma.servicio import CheckoutServicio
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.reservas.cu12_reservar_prendas.esquemas import ReservaCrearIn
from modules.reservas.cu12_reservar_prendas.repositorio import ReservaRepositorio
from modules.reservas.cu12_reservar_prendas.servicio import ReservaServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
from modules.sincronizacion.avisos_cliente.servicio import AvisosServicio
from modules.sincronizacion.comun import nombre_usuario
from modules.sincronizacion.cu14_dispositivo_catalogo.repositorio import DispositivoRepositorio
from modules.sincronizacion.cu14_dispositivo_catalogo.servicio import DispositivoServicio
from modules.sincronizacion.cu19_sincronizar.esquemas import (
    LoteIn,
    LoteOut,
    OperacionIn,
    OperacionOut,
    ResultadoOperacionOut,
)
from modules.sincronizacion.cu19_sincronizar.repositorio import SincronizacionRepositorio
from modules.sincronizacion.cu19_sincronizar.saneado import sanear
from modules.sincronizacion.modelos import ConflictoSyncORM, OperacionSyncORM

logger = logging.getLogger("fashionstore.sincronizacion")

#: Tolerancia al desfase del reloj del dispositivo (plan.md §5).
MARGEN_RELOJ = timedelta(minutes=5)

MENSAJES = {
    "STOCK_INSUFICIENTE": "Ya no quedan unidades suficientes en la sucursal.",
    "ANTIGUEDAD_EXCEDIDA": "La operación es más antigua de lo que la tienda acepta.",
    "FECHA_INVALIDA": "La fecha del dispositivo no es válida.",
    "SUSCRIPCION_NO_VIGENTE": "La tienda no tiene la suscripción vigente.",
    "FUNCIONALIDAD_NO_INCLUIDA": "El plan de la tienda no incluye esta operación.",
    "SUCURSAL_INACTIVA": "La sucursal ya no está disponible.",
    "PRODUCTO_INACTIVO": "Una de las prendas ya no está disponible.",
    "DATOS_INVALIDOS": "La operación llegó incompleta o con datos no válidos.",
    "PAGO_NO_APROBADO": "El pago no fue aprobado; no se cobró nada.",
    "VENTA_NO_ENCONTRADA": "La compra no existe en esta tienda.",
    "VENTA_AJENA": "La compra pertenece a otra cuenta.",
    "UUID_DUPLICADO": "Otro dispositivo ya envió una operación con este identificador.",
}

#: Motivo de rechazo → tipo de conflicto, para una compra ya cobrada (CU20).
TIPO_CONFLICTO = {
    "STOCK_INSUFICIENTE": "stock_insuficiente",
    "SUSCRIPCION_NO_VIGENTE": "suscripcion_no_vigente",
    "FUNCIONALIDAD_NO_INCLUIDA": "suscripcion_no_vigente",
    "SUCURSAL_INACTIVA": "sucursal_inactiva",
    "PRODUCTO_INACTIVO": "producto_inactivo",
    "ANTIGUEDAD_EXCEDIDA": "antiguedad_excedida",
}


class _Rechazo(Exception):
    """Una regla de AC-19.2 no se cumple."""

    def __init__(self, motivo: str, mensaje: Optional[str] = None, detalle: Optional[dict] = None):
        self.motivo = motivo
        self.mensaje = mensaje or MENSAJES.get(motivo, motivo)
        self.detalle = detalle or {}
        super().__init__(motivo)


class _Reintentar(Exception):
    """El servidor no puede decidir ahora (pasarela caída): la app conserva la operación."""

    def __init__(self, motivo: str):
        self.motivo = motivo
        super().__init__(motivo)


@dataclass
class _Desenlace:
    estado: str
    motivo: Optional[str] = None
    mensaje: Optional[str] = None
    id_sucursal: Optional[int] = None
    id_reserva: Optional[int] = None
    codigo_reserva: Optional[str] = None
    id_venta: Optional[int] = None
    id_conflicto: Optional[int] = None
    #: Para `en_conflicto`: id_pago, tipo y detalle del conflicto.
    conflicto: Optional[dict[str, Any]] = None
    #: Aviso al cliente que acompaña al desenlace.
    aviso: Optional[dict[str, Any]] = None
    resultado_extra: dict[str, Any] = field(default_factory=dict)


class SincronizacionServicio:
    # ------------------------------------------------------------------
    # Lote
    # ------------------------------------------------------------------

    @staticmethod
    def sincronizar(
        db: Session, usuario: UsuarioORM, lote: LoteIn, pasarela: Optional[PasarelaPagos] = None
    ) -> LoteOut:
        dispositivo = DispositivoServicio.del_cliente(db, usuario, lote.dispositivo)
        id_dispositivo = dispositivo.id_dispositivo
        canal = "movil" if dispositivo.plataforma == "flutter" else "web"
        inicio = ahora()
        db.commit()

        resultados = [
            SincronizacionServicio._procesar(db, usuario, id_dispositivo, canal, op, pasarela)
            for op in lote.operaciones
        ]

        conteo = {e: sum(1 for r in resultados if r.estado == e) for e in ("confirmada", "rechazada", "en_conflicto", "reintentar")}
        fin = ahora()
        dispositivo = SincronizacionRepositorio.dispositivo(db, id_dispositivo)
        dispositivo.ultima_sincronizacion_en = fin
        log = DispositivoRepositorio.registrar_log(
            db,
            id_dispositivo=id_dispositivo,
            tipo="sincronizacion",
            iniciado_en=inicio,
            finalizado_en=fin,
            resultado="ok" if conteo["reintentar"] == 0 else ("parcial" if conteo["reintentar"] < len(resultados) else "error"),
            enviadas=len(resultados),
            confirmadas=conteo["confirmada"],
            rechazadas=conteo["rechazada"],
            en_conflicto=conteo["en_conflicto"],
            mensaje=f"Pendientes de reintento: {conteo['reintentar']}." if conteo["reintentar"] else None,
        )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario(usuario),
            accion="SINCRONIZACION",
            tabla_modulo="operaciones_sync",
            payload_nuevo={"id_dispositivo": id_dispositivo, "id_sync_log": log.id_sync_log, **conteo},
            db=db,
        )
        db.commit()
        return LoteOut(id_sync_log=log.id_sync_log, resultados=resultados)

    @staticmethod
    def operaciones(db: Session, usuario: UsuarioORM, identificador: uuid.UUID) -> list[OperacionOut]:
        dispositivo = DispositivoServicio.del_cliente(db, usuario, identificador)
        salida = []
        for op, estado_conflicto in SincronizacionRepositorio.operaciones_del_dispositivo(db, dispositivo.id_dispositivo):
            salida.append(
                OperacionOut(
                    uuid=op.uuid_operacion,
                    tipo=op.tipo,
                    estado=op.estado,
                    motivo=op.motivo,
                    codigo_provisional=op.codigo_provisional,
                    codigo_reserva=(op.resultado or {}).get("codigo_reserva"),
                    id_reserva=op.id_reserva,
                    id_venta=op.id_venta,
                    registrada_en=op.registrada_en,
                    recibida_en=op.recibida_en,
                    estado_conflicto=estado_conflicto,
                )
            )
        return salida

    # ------------------------------------------------------------------
    # Una operación
    # ------------------------------------------------------------------

    @staticmethod
    def _procesar(
        db: Session,
        usuario: UsuarioORM,
        id_dispositivo: int,
        canal: str,
        op: OperacionIn,
        pasarela: Optional[PasarelaPagos],
    ) -> ResultadoOperacionOut:
        previa = SincronizacionRepositorio.operacion(db, op.uuid)
        if previa is not None:
            db.rollback()
            return SincronizacionServicio._resultado_guardado(previa, id_dispositivo)

        try:
            if op.tipo == "reserva":
                desenlace = SincronizacionServicio._reserva(db, usuario, canal, op)
            else:
                desenlace = SincronizacionServicio._compra(db, usuario, op, pasarela)
        except _Reintentar as reintentar:
            db.rollback()
            return ResultadoOperacionOut(
                uuid=op.uuid, estado="reintentar", motivo=reintentar.motivo,
                mensaje="La pasarela de pagos no respondió. Se volverá a intentar.",
            )

        return SincronizacionServicio._registrar(db, usuario, id_dispositivo, op, desenlace)

    @staticmethod
    def _registrar(
        db: Session, usuario: UsuarioORM, id_dispositivo: int, op: OperacionIn, d: _Desenlace
    ) -> ResultadoOperacionOut:
        """Guarda el desenlace junto con su efecto y confirma. Ante el mismo UUID enviado a la vez,
        se deshace todo y se devuelve lo que guardó el otro envío."""
        resultado = ResultadoOperacionOut(
            uuid=op.uuid,
            estado=d.estado,
            motivo=d.motivo,
            mensaje=d.mensaje,
            codigo_reserva=d.codigo_reserva,
            id_reserva=d.id_reserva,
            id_venta=d.id_venta,
            id_conflicto=d.id_conflicto,
        )
        try:
            fila = OperacionSyncORM(
                uuid_operacion=op.uuid,
                id_dispositivo=id_dispositivo,
                id_sucursal=d.id_sucursal,
                tipo=op.tipo,
                estado=d.estado,
                codigo_provisional=op.codigo_provisional,
                registrada_en=op.registrada_en,
                datos=sanear(op.tipo, op.datos),
                resultado={},
                motivo=d.motivo,
                id_reserva=d.id_reserva,
                id_venta=d.id_venta,
            )
            db.add(fila)
            db.flush()

            if d.conflicto is not None:
                conflicto = ConflictoSyncORM(
                    id_operacion_sync=fila.id_operacion_sync,
                    id_venta=d.id_venta,
                    id_pago=d.conflicto["id_pago"],
                    id_sucursal=d.conflicto["id_sucursal"],
                    tipo=d.conflicto["tipo"],
                    detalle=d.conflicto["detalle"],
                    estado="pendiente",
                )
                db.add(conflicto)
                db.flush()
                resultado.id_conflicto = conflicto.id_conflicto
                ServicioBitacoraAuditoria.registrar_evento_seguro(
                    id_usuario=usuario.id_usuario,
                    usuario_nombre=nombre_usuario(usuario),
                    accion="CONFLICTO_REGISTRADO",
                    tabla_modulo="conflictos_sync",
                    severidad="WARNING",
                    payload_nuevo={
                        "id_conflicto": conflicto.id_conflicto,
                        "id_venta": d.id_venta,
                        "tipo": conflicto.tipo,
                    },
                    db=db,
                )

            if d.aviso is not None:
                AvisosServicio.crear(db, id_cliente=usuario.id_usuario, **d.aviso)

            fila.resultado = resultado.model_dump(mode="json", exclude={"uuid", "repetida"})
            db.commit()
            return resultado
        except IntegrityError:
            db.rollback()
            previa = SincronizacionRepositorio.operacion(db, op.uuid)
            if previa is None:
                raise
            db.rollback()
            return SincronizacionServicio._resultado_guardado(previa, id_dispositivo)

    @staticmethod
    def _resultado_guardado(previa: OperacionSyncORM, id_dispositivo: int) -> ResultadoOperacionOut:
        if previa.id_dispositivo != id_dispositivo:
            # No se revela el resultado de una operación de otro dispositivo.
            return ResultadoOperacionOut(
                uuid=previa.uuid_operacion, estado="rechazada", motivo="UUID_DUPLICADO",
                mensaje=MENSAJES["UUID_DUPLICADO"],
            )
        guardado = dict(previa.resultado or {})
        guardado.pop("uuid", None)
        guardado.pop("repetida", None)
        guardado.setdefault("estado", previa.estado)
        return ResultadoOperacionOut(uuid=previa.uuid_operacion, repetida=True, **guardado)

    # ------------------------------------------------------------------
    # Reglas comunes
    # ------------------------------------------------------------------

    @staticmethod
    def _validar_suscripcion(db: Session, funcionalidad: str) -> None:
        try:
            SuscripcionServicio.validar(db, funcionalidad=funcionalidad)
        except AuthorizationError as exc:
            raise _Rechazo(exc.code, exc.message) from exc

    @staticmethod
    def _dias_antiguedad(db: Session) -> int:
        return ParametrosEmpresaServicio.vigentes(db).dias_antiguedad_offline

    # ------------------------------------------------------------------
    # Reserva (CU15 A1/A2)
    # ------------------------------------------------------------------

    @staticmethod
    def _reserva(db: Session, usuario: UsuarioORM, canal: str, op: OperacionIn) -> _Desenlace:
        try:
            id_sucursal, payload = SincronizacionServicio._validar_reserva(db, usuario, canal, op)
            registrada = ReservaServicio.registrar(db, usuario, payload, codigo_provisional=op.codigo_provisional)
            ReservaServicio.auditar(db, usuario, registrada)
            reserva = registrada.reserva
            return _Desenlace(
                estado="confirmada",
                id_sucursal=id_sucursal,
                id_reserva=reserva.id_reserva,
                codigo_reserva=ReservaServicio.codigo(reserva),
                mensaje="Reserva confirmada.",
            )
        except (_Rechazo, DomainError) as exc:
            db.rollback()
            if isinstance(exc, _Rechazo):
                rechazo = exc
            elif exc.code == "STOCK_INSUFICIENTE_RESERVA":
                rechazo = _Rechazo("STOCK_INSUFICIENTE", detalle=exc.datos)
            else:
                rechazo = _Rechazo(exc.code, exc.message)
            provisional = op.codigo_provisional or "sin código"
            return _Desenlace(
                estado="rechazada",
                motivo=rechazo.motivo,
                mensaje=rechazo.mensaje,
                id_sucursal=getattr(rechazo, "id_sucursal", None),
                aviso={
                    "tipo": "reserva_cancelada",
                    "titulo": f"Reserva {provisional} cancelada",
                    "mensaje": f"No pudimos confirmar tu reserva {provisional}: {rechazo.mensaje}",
                },
            )

    @staticmethod
    def _validar_reserva(
        db: Session, usuario: UsuarioORM, canal: str, op: OperacionIn
    ) -> tuple[int, ReservaCrearIn]:
        """AC-19.2 en orden: suscripción y plan, antigüedad, sucursal, prendas (el stock lo valida
        `ReservaServicio.registrar` con `FOR UPDATE`)."""
        SincronizacionServicio._validar_suscripcion(db, "reservas")

        instante = ahora()
        registrada_en = op.registrada_en
        if registrada_en.tzinfo is None:
            raise _Rechazo("FECHA_INVALIDA")
        if registrada_en > instante + MARGEN_RELOJ:
            raise _Rechazo("FECHA_INVALIDA")
        dias = SincronizacionServicio._dias_antiguedad(db)
        if registrada_en < instante - timedelta(days=dias) - MARGEN_RELOJ:
            raise _Rechazo("ANTIGUEDAD_EXCEDIDA", f"La reserva tiene más de {dias} días sin sincronizar.")

        if op.id_sucursal is None:
            raise _Rechazo("DATOS_INVALIDOS")
        try:
            payload = ReservaCrearIn(id_sucursal=op.id_sucursal, canal_origen=canal, **sanear("reserva", op.datos))
        except (ValidationError, TypeError) as exc:
            raise _Rechazo("DATOS_INVALIDOS") from exc

        # Con RLS, una sucursal de otra empresa no se ve: también es «inactiva» (PI-14).
        if ReservaRepositorio.obtener_sucursal_activa(db, op.id_sucursal) is None:
            raise _Rechazo("SUCURSAL_INACTIVA")
        for item in payload.items:
            variante = ReservaRepositorio.obtener_variante_con_prenda(db, item.id_variante)
            if variante is None or not variante.activo or not variante.producto.activo:
                raise _Rechazo("PRODUCTO_INACTIVO", detalle={"id_variante": item.id_variante})
        return op.id_sucursal, payload

    # ------------------------------------------------------------------
    # Compra interrumpida (solo móvil)
    # ------------------------------------------------------------------

    @staticmethod
    def _compra(
        db: Session, usuario: UsuarioORM, op: OperacionIn, pasarela: Optional[PasarelaPagos]
    ) -> _Desenlace:
        datos = sanear("compra_interrumpida", op.datos)
        id_venta, id_pago = datos.get("id_venta"), datos.get("id_pago")
        if not isinstance(id_venta, int) or not isinstance(id_pago, int):
            db.rollback()
            return SincronizacionServicio._rechazada("DATOS_INVALIDOS")

        try:
            venta, pago = PagoServicio.cargar_compra_para_cobro(db, id_venta, id_pago)
        except DomainError as exc:
            db.rollback()
            motivo = "VENTA_NO_ENCONTRADA" if isinstance(exc, NotFoundError) else "DATOS_INVALIDOS"
            return SincronizacionServicio._rechazada(motivo)
        if venta.id_cliente != usuario.id_usuario:
            db.rollback()
            return SincronizacionServicio._rechazada("VENTA_AJENA")

        if pago.estado == "confirmado" and venta.estado == "pagada":
            # El webhook (o un envío anterior) ya la completó.
            return _Desenlace(estado="confirmada", id_venta=venta.id_venta, mensaje="Compra confirmada.")
        if pago.estado == "confirmado":
            existente = SincronizacionRepositorio.conflicto_de_venta(db, venta.id_venta)
            if existente is not None:
                # Cobrada y ya en conflicto por otro envío: no se abre un segundo reembolso.
                db.rollback()
                return _Desenlace(
                    estado="en_conflicto", motivo="CONFLICTO_EXISTENTE", id_venta=existente.id_venta,
                    id_conflicto=existente.id_conflicto,
                    mensaje="Tu pago se registró y su reembolso ya está en revisión.",
                )
        if pago.estado == "pendiente":
            try:
                resultado = PagoServicio.verificar_cobro(pago, pasarela)
            except ErrorPasarela as exc:
                raise _Reintentar("PASARELA_NO_DISPONIBLE") from exc
            if not resultado.aprobado:
                # No hubo cobro: se deja constancia en el pago y la operación se rechaza.
                PagoServicio.marcar_cobro_rechazado(db, pago, resultado)
                return SincronizacionServicio._rechazada("PAGO_NO_APROBADO", id_venta=venta.id_venta)
            PagoServicio.marcar_cobro_confirmado(db, pago, resultado)
        elif pago.estado != "confirmado":
            db.rollback()
            return SincronizacionServicio._rechazada("PAGO_NO_APROBADO", id_venta=venta.id_venta)

        # Desde aquí el dinero está cobrado: o se completa la compra o se abre un conflicto.
        id_sucursal = next(
            (d.id_sucursal for d in venta.detalles if d.id_sucursal), venta.id_sucursal
        )
        try:
            with db.begin_nested():
                SincronizacionServicio._completar_compra(db, usuario, venta)
            return _Desenlace(
                estado="confirmada", id_sucursal=id_sucursal, id_venta=venta.id_venta, mensaje="Compra confirmada."
            )
        except _Rechazo as rechazo:
            if venta.estado == "pendiente":
                # La retención ya no sirve: las unidades vuelven a estar disponibles. La venta sigue
                # `pendiente` hasta que se acepte el reembolso (CU20), sin tocar más el inventario.
                CheckoutServicio.devolver_existencias(db, venta, usuario.id_usuario)
            return _Desenlace(
                estado="en_conflicto",
                motivo=rechazo.motivo,
                mensaje="Tu pago se registró, pero la compra no pudo completarse. Te devolveremos el importe.",
                id_sucursal=id_sucursal,
                id_venta=venta.id_venta,
                conflicto={
                    "id_pago": pago.id_pago,
                    "id_sucursal": id_sucursal,
                    "tipo": TIPO_CONFLICTO.get(rechazo.motivo, "stock_insuficiente"),
                    "detalle": {"motivo": rechazo.motivo, "mensaje": rechazo.mensaje, **rechazo.detalle},
                },
            )

    @staticmethod
    def _completar_compra(db: Session, usuario: UsuarioORM, venta) -> None:
        """AC-19.2 sobre una compra cobrada. Lanza `_Rechazo`; el punto de guardado deshace lo hecho."""
        SincronizacionServicio._validar_suscripcion(db, "ventas")

        # La antigüedad de una compra se mide desde la orden, que fechó el servidor (no el reloj
        # del dispositivo).
        dias = SincronizacionServicio._dias_antiguedad(db)
        fecha = venta.fecha_venta
        if fecha.tzinfo is not None and fecha < ahora() - timedelta(days=dias):
            raise _Rechazo(
                "ANTIGUEDAD_EXCEDIDA",
                detalle={"esperado": f"≤ {dias} días", "encontrado": fecha.isoformat()},
            )

        sucursales = {
            d.sucursal.id_sucursal: d.sucursal for d in venta.detalles if getattr(d, "sucursal", None) is not None
        }
        if not sucursales and getattr(venta, "sucursal", None) is not None:
            sucursales = {venta.sucursal.id_sucursal: venta.sucursal}
        for sucursal in sucursales.values():
            if not sucursal.activa:
                raise _Rechazo(
                    "SUCURSAL_INACTIVA",
                    detalle={"id_sucursal": sucursal.id_sucursal, "esperado": "activa", "encontrado": "inactiva"},
                )
        for detalle in venta.detalles:
            variante = detalle.variante
            if not variante.activo or not variante.producto.activo:
                raise _Rechazo(
                    "PRODUCTO_INACTIVO",
                    detalle={"id_variante": variante.id_variante, "esperado": "activo", "encontrado": "inactivo"},
                )

        if venta.estado == "pendiente":
            PagoServicio.completar_venta_cobrada(db, venta, usuario.id_usuario)
        elif venta.estado == "anulada":
            try:
                PagoServicio.retomar_y_completar_venta_cobrada(db, venta, usuario.id_usuario)
            except ConflictError as exc:
                raise _Rechazo("STOCK_INSUFICIENTE", detalle=exc.datos) from exc
        # `pagada` con el pago recién confirmado no puede darse: el pago y la venta cambian juntos.

    @staticmethod
    def _rechazada(motivo: str, id_venta: Optional[int] = None) -> _Desenlace:
        return _Desenlace(estado="rechazada", motivo=motivo, mensaje=MENSAJES.get(motivo, motivo), id_venta=id_venta)
