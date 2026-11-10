"""P2-CU20 · Resolver conflictos de sincronización (AC-20.1 a AC-20.9).

Visibilidad (A2): el administrador ve toda su empresa; el encargado, solo sus sucursales
autorizadas (RN07). Un conflicto fuera de su alcance no existe para él (404).

Estados: `pendiente` → (aceptar) `reembolso_pendiente` → (cierre de mes) `resuelto`. La compra en
conflicto nunca llegó a confirmarse y su retención se devolvió al abrir el conflicto (CU19), así
que aceptar el reembolso **no toca el inventario**.
"""

import logging
from datetime import timedelta
from typing import Optional

from sqlalchemy.orm import Session

from core.errors import ConflictError, NotFoundError
from core.tenant import tenant_actual
from core.tiempo import ahora, hoy
from integrations.stripe_service import PasarelaPagos, StripeService
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.compras_pagos.cu16_realizar_pago.servicio import PagoServicio
from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria
from modules.sincronizacion.avisos_cliente.servicio import AvisosServicio
from modules.sincronizacion.comun import nombre_usuario
from modules.sincronizacion.cu20_conflictos.esquemas import (
    CierreOut,
    ConflictoDetalleOut,
    ConflictoResumenOut,
    EstadoCierreOut,
    LineaCompraOut,
    PagoConflictoOut,
    ReembolsoFallidoOut,
    ResumenConflictosOut,
)
from modules.sincronizacion.cu20_conflictos.repositorio import ConflictosRepositorio
from modules.sincronizacion.modelos import ESTADOS_CONFLICTO, ConflictoSyncORM

logger = logging.getLogger("fashionstore.conflictos")

MENSAJE_REEMBOLSO_ACEPTADO = "Recibirá su reembolso al finalizar el mes o en 15 días hábiles."


def es_ultimo_dia_del_mes() -> bool:
    """Último día del mes en la hora de Bolivia (S11)."""
    dia = hoy()
    return (dia + timedelta(days=1)).month != dia.month


class ConflictosServicio:
    # ------------------------------------------------------------------
    # Consulta
    # ------------------------------------------------------------------

    @staticmethod
    def listar(db: Session, usuario: UsuarioORM, estado: Optional[str] = None) -> list[ConflictoResumenOut]:
        if estado is not None and estado not in ESTADOS_CONFLICTO:
            estado = None
        conflictos = ConflictosRepositorio.listar(db, SucursalesEmpleadoServicio.autorizadas(usuario), estado)
        return [ConflictosServicio._resumen(db, c) for c in conflictos]

    @staticmethod
    def detalle(db: Session, usuario: UsuarioORM, id_conflicto: int) -> ConflictoDetalleOut:
        conflicto = ConflictosServicio._visible(db, usuario, id_conflicto)
        return ConflictosServicio._detalle(db, conflicto)

    @staticmethod
    def resumen(db: Session, usuario: UsuarioORM) -> ResumenConflictosOut:
        conteo = ConflictosRepositorio.contar(db, SucursalesEmpleadoServicio.autorizadas(usuario))
        return ResumenConflictosOut(
            pendiente=conteo.get("pendiente", 0), reembolso_pendiente=conteo.get("reembolso_pendiente", 0)
        )

    @staticmethod
    def estado_cierre(db: Session) -> EstadoCierreOut:
        return EstadoCierreOut(
            es_ultimo_dia_del_mes=es_ultimo_dia_del_mes(),
            reembolsos_pendientes=len(ConflictosRepositorio.ids_por_reembolsar(db)),
        )

    # ------------------------------------------------------------------
    # Aceptar el reembolso (pasos 3 y 4)
    # ------------------------------------------------------------------

    @staticmethod
    def aceptar_reembolso(db: Session, usuario: UsuarioORM, id_conflicto: int) -> ConflictoDetalleOut:
        conflicto = ConflictosServicio._visible(db, usuario, id_conflicto, bloquear=True)
        if conflicto.estado != "pendiente":
            db.rollback()
            raise ConflictError(
                "Otro usuario ya resolvió este conflicto. Actualiza la lista.", code="CONFLICTO_YA_RESUELTO"
            )

        venta, _pago = PagoServicio.cargar_compra_para_cobro(db, conflicto.id_venta, conflicto.id_pago)
        if venta.estado == "pendiente":
            venta.estado = "anulada"  # sin tocar el inventario: la retención ya se devolvió en CU19
        conflicto.estado = "reembolso_pendiente"
        conflicto.aceptado_por = usuario.id_usuario
        conflicto.aceptado_en = ahora()

        if venta.id_cliente:
            AvisosServicio.crear(
                db,
                id_cliente=venta.id_cliente,
                tipo="reembolso_aceptado",
                titulo=f"Reembolso de la compra {venta.numero_comprobante}",
                mensaje=MENSAJE_REEMBOLSO_ACEPTADO,
                id_venta=venta.id_venta,
            )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario(usuario),
            accion="REEMBOLSO_ACEPTADO",
            tabla_modulo="conflictos_sync",
            payload_anterior={"estado": "pendiente"},
            payload_nuevo={
                "id_conflicto": conflicto.id_conflicto,
                "id_venta": venta.id_venta,
                "estado": conflicto.estado,
            },
            db=db,
        )
        db.commit()
        db.refresh(conflicto)
        return ConflictosServicio._detalle(db, conflicto)

    # ------------------------------------------------------------------
    # Cierre de mes (paso 5, decisión D2)
    # ------------------------------------------------------------------

    @staticmethod
    def procesar_cierre(
        db: Session, usuario: UsuarioORM, forzar: bool = False, pasarela: Optional[PasarelaPagos] = None
    ) -> CierreOut:
        ultimo_dia = es_ultimo_dia_del_mes()
        if not ultimo_dia and not forzar:
            raise ConflictError(
                "Los reembolsos se procesan el último día del mes. Para hacerlo antes, confirma un "
                "cierre anticipado de prueba.",
                code="CIERRE_NO_DISPONIBLE",
            )
        forzado = not ultimo_dia
        pasarela = pasarela or StripeService()
        id_tenant = tenant_actual(db)

        ids = ConflictosRepositorio.ids_por_reembolsar(db)
        db.commit()
        reembolsados = 0
        fallidos: list[ReembolsoFallidoOut] = []
        procesados = 0
        for id_conflicto in ids:
            # Una transacción por conflicto: un fallo de Stripe no deshace los demás (A1).
            conflicto = ConflictosRepositorio.tomar_para_reembolso(db, id_conflicto)
            if conflicto is None:
                db.rollback()  # lo está procesando otro cierre, o ya no está pendiente
                continue
            procesados += 1
            exito, motivo = ConflictosServicio._reembolsar(db, usuario, conflicto, pasarela, id_tenant)
            db.commit()
            if exito:
                reembolsados += 1
            else:
                fallidos.append(ReembolsoFallidoOut(id_conflicto=id_conflicto, motivo=motivo or ""))

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario(usuario),
            accion="CIERRE_REEMBOLSOS",
            tabla_modulo="conflictos_sync",
            severidad="WARNING" if forzado else "INFO",
            payload_nuevo={
                "forzado": forzado,
                "detalle": "cierre anticipado de prueba" if forzado else "cierre de mes",
                "procesados": procesados,
                "reembolsados": reembolsados,
                "fallidos": len(fallidos),
            },
            db=db,
        )
        db.commit()
        return CierreOut(forzado=forzado, procesados=procesados, reembolsados=reembolsados, fallidos=fallidos)

    @staticmethod
    def _reembolsar(
        db: Session,
        usuario: UsuarioORM,
        conflicto: ConflictoSyncORM,
        pasarela: PasarelaPagos,
        id_tenant: Optional[int],
    ) -> tuple[bool, Optional[str]]:
        venta, pago = PagoServicio.cargar_compra_para_cobro(db, conflicto.id_venta, conflicto.id_pago)
        intento = conflicto.intentos_reembolso + 1
        # La clave solo cambia tras un fallo registrado: si el proceso se cae después de que Stripe
        # reembolsó pero antes de guardar, el reintento usa la misma clave y Stripe no repite.
        clave = f"reembolso-{id_tenant}-{conflicto.id_conflicto}-{intento}"
        escenario = (pago.payload_respuesta or {}).get("escenario_prueba")
        resultado = pasarela.reembolsar(pago.referencia_pasarela, pago.monto, clave, escenario_prueba=escenario)

        conflicto.intentos_reembolso = intento
        if not resultado.exitoso:
            conflicto.ultimo_error = resultado.mensaje
            ServicioBitacoraAuditoria.registrar_evento_seguro(
                id_usuario=usuario.id_usuario,
                usuario_nombre=nombre_usuario(usuario),
                accion="REEMBOLSO_FALLIDO",
                tabla_modulo="conflictos_sync",
                severidad="WARNING",
                payload_nuevo={"id_conflicto": conflicto.id_conflicto, "intento": intento, "motivo": resultado.mensaje},
                db=db,
            )
            return False, resultado.mensaje

        momento = ahora()
        pago.estado = "reembolsado"
        pago.payload_respuesta = {
            **(pago.payload_respuesta or {}),
            "reembolso": {"referencia": resultado.referencia, "en": momento.isoformat()},
        }
        conflicto.estado = "resuelto"
        conflicto.resuelto_en = momento
        conflicto.referencia_reembolso = resultado.referencia
        conflicto.ultimo_error = None
        if venta.id_cliente:
            AvisosServicio.crear(
                db,
                id_cliente=venta.id_cliente,
                tipo="reembolso_procesado",
                titulo=f"Reembolso procesado · {venta.numero_comprobante}",
                mensaje="Procesamos el reembolso de tu compra. Puede tardar unos días en verse en tu tarjeta.",
                id_venta=venta.id_venta,
            )
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario(usuario),
            accion="REEMBOLSO_PROCESADO",
            tabla_modulo="conflictos_sync",
            payload_nuevo={"id_conflicto": conflicto.id_conflicto, "id_pago": pago.id_pago, "intento": intento},
            db=db,
        )
        return True, None

    # ------------------------------------------------------------------
    # Apoyo
    # ------------------------------------------------------------------

    @staticmethod
    def _visible(db: Session, usuario: UsuarioORM, id_conflicto: int, bloquear: bool = False) -> ConflictoSyncORM:
        conflicto = ConflictosRepositorio.obtener(
            db, id_conflicto, SucursalesEmpleadoServicio.autorizadas(usuario), bloquear=bloquear
        )
        if conflicto is None:
            raise NotFoundError("El conflicto no existe.", code="CONFLICTO_NO_ENCONTRADO")
        return conflicto

    @staticmethod
    def _nombre(db: Session, id_usuario: Optional[int]) -> Optional[str]:
        if not id_usuario:
            return None
        usuario = db.get(UsuarioORM, id_usuario)
        return nombre_usuario(usuario) if usuario is not None else None

    @staticmethod
    def _resumen(db: Session, conflicto: ConflictoSyncORM, venta=None) -> ConflictoResumenOut:
        if venta is None:
            venta, _ = PagoServicio.cargar_compra_para_cobro(db, conflicto.id_venta, conflicto.id_pago, bloquear=False)
        sucursal = next(
            (d.sucursal for d in venta.detalles if getattr(d, "sucursal", None) is not None
             and d.sucursal.id_sucursal == conflicto.id_sucursal),
            None,
        )
        return ConflictoResumenOut(
            id_conflicto=conflicto.id_conflicto,
            tipo=conflicto.tipo,
            estado=conflicto.estado,
            creado_en=conflicto.creado_en,
            id_sucursal=conflicto.id_sucursal,
            nombre_sucursal=sucursal.nombre if sucursal is not None else None,
            id_venta=venta.id_venta,
            numero_comprobante=venta.numero_comprobante,
            total=venta.total,
            cliente=ConflictosServicio._nombre(db, venta.id_cliente),
        )

    @staticmethod
    def _detalle(db: Session, conflicto: ConflictoSyncORM) -> ConflictoDetalleOut:
        venta, pago = PagoServicio.cargar_compra_para_cobro(db, conflicto.id_venta, conflicto.id_pago, bloquear=False)
        base = ConflictosServicio._resumen(db, conflicto, venta)
        return ConflictoDetalleOut(
            **base.model_dump(),
            detalle=conflicto.detalle or {},
            lineas=[
                LineaCompraOut(
                    id_variante=d.id_variante,
                    nombre_producto=d.variante.producto.nombre,
                    sku=d.variante.sku,
                    cantidad=d.cantidad,
                    precio_unitario=d.precio_unitario,
                )
                for d in venta.detalles
            ],
            pago=PagoConflictoOut(
                id_pago=pago.id_pago,
                metodo_pago=str(pago.metodo_pago),
                monto=pago.monto,
                estado=str(pago.estado),
                confirmado_en=pago.confirmado_en,
            ),
            fecha_compra=venta.fecha_venta,
            aceptado_por=ConflictosServicio._nombre(db, conflicto.aceptado_por),
            aceptado_en=conflicto.aceptado_en,
            resuelto_en=conflicto.resuelto_en,
            referencia_reembolso=conflicto.referencia_reembolso,
            intentos_reembolso=conflicto.intentos_reembolso,
            ultimo_error=conflicto.ultimo_error,
        )
