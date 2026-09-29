"""Servicio transaccional de dominio para CU13 (Consultar y cancelar reservas) y CU14 (Consultar
estado de reserva).

**Invariante de inventario:** liberar una reserva mueve las unidades de `cantidad_reservada` a
`cantidad_disponible` en la **misma fila** que CU12 apartó — nunca se recalcula la temporada, se
localiza por el movimiento `reserva` que CU12 dejó escrito. Ver `RESERVA_SIN_TRAZA` en `spec.md`.
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from core.errors import AuthorizationError, ConflictError, NotFoundError
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.reservas.cu13_consultar_cancelar_reservas.esquemas import (
    MisReservasOut,
    ReservaCancelarIn,
    ReservaItemOut,
    ReservaOut,
    ResumenProximaReservaOut,
    ResumenReservasOut,
    SucursalReservaOut,
)
from modules.reservas.cu13_consultar_cancelar_reservas.repositorio import (
    ReservaConsultaRepositorio,
)
from modules.reservas.modelos import ReservaORM
from modules.reservas.utilidades import formatear_codigo_reserva

# Estados desde los que el cliente puede cancelar (spec.md, D3): mientras no haya arrancado la
# atención en boutique. `en_atencion`/`atendida` son transiciones de tienda, fuera de alcance.
ESTADOS_CANCELABLES = ("pendiente", "confirmada")

# Estados que cuentan como "próxima" en el panel del cliente, no como historial.
ESTADOS_ACTIVOS = ("pendiente", "confirmada", "en_atencion")

# Tolerancia tras la hora de la cita antes de considerar la reserva vencida (spec.md, D1-A).
TOLERANCIA_VENCIMIENTO = timedelta(hours=2)

MOTIVO_VENCIMIENTO = "Vencida sin atención dentro del plazo."


class ReservaConsultaServicio:
    """Orquesta la consulta (CU14) y la cancelación (CU13) de reservas de citas presenciales."""

    # ------------------------------------------------------------------
    # Lectura
    # ------------------------------------------------------------------

    @staticmethod
    def listar_mis_reservas(db: Session, usuario: UsuarioORM) -> MisReservasOut:
        """Reservas del cliente autenticado, separadas en próximas e historial.

        Antes de construir la respuesta, vence (y libera stock de) cualquier reserva
        `pendiente`/`confirmada` cuya cita ya pasó de la tolerancia: es la única forma de que las
        9 reservas hoy retenidas indefinidamente (ver `spec.md` §0.3) alguna vez suelten su stock.
        """
        reservas = ReservaConsultaRepositorio.buscar_reservas_de_cliente(db, usuario.id_usuario)

        for reserva in reservas:
            if not ReservaConsultaServicio._es_candidata_a_vencer(reserva):
                continue
            # Se relee con bloqueo antes de mutar: dos peticiones simultáneas no deben liberar el
            # mismo stock dos veces. `bloqueada` es el mismo objeto que `reserva` (identity map de
            # SQLAlchemy dentro de la misma sesión), así que tras el commit sus atributos quedan
            # expirados y se releen solos la próxima vez que se accede a ellos.
            bloqueada = ReservaConsultaRepositorio.obtener_reserva_para_actualizar(
                db, reserva.id_reserva
            )
            if bloqueada and ReservaConsultaServicio._vencer_si_corresponde(db, bloqueada, usuario):
                db.commit()

        proximas = []
        historial = []
        for reserva in reservas:
            salida = ReservaConsultaServicio._construir_salida(reserva)
            (proximas if reserva.estado in ESTADOS_ACTIVOS else historial).append(salida)

        proximas.sort(key=lambda r: r.fecha_hora_atencion)
        historial.sort(key=lambda r: r.fecha_hora_atencion, reverse=True)

        activas = [r for r in proximas if r.estado in ("pendiente", "confirmada")]
        proxima_resumen = None
        if activas:
            primera = activas[0]
            proxima_resumen = ResumenProximaReservaOut(
                id_reserva=primera.id_reserva,
                fecha_hora_atencion=primera.fecha_hora_atencion,
                nombre_sucursal=primera.sucursal.nombre,
            )

        return MisReservasOut(
            resumen=ResumenReservasOut(activas=len(activas), proxima=proxima_resumen),
            proximas=proximas,
            historial=historial,
        )

    # ------------------------------------------------------------------
    # Escritura
    # ------------------------------------------------------------------

    @staticmethod
    def cancelar_reserva(
        db: Session, usuario: UsuarioORM, id_reserva: int, payload: ReservaCancelarIn
    ) -> ReservaOut:
        """Cancela una reserva propia y libera de inmediato las existencias apartadas."""
        reserva = ReservaConsultaRepositorio.obtener_reserva_para_actualizar(db, id_reserva)
        if not reserva:
            raise NotFoundError(
                f"La reserva #{id_reserva} no existe.", code="RESERVA_NO_ENCONTRADA"
            )

        # Se responde 403 y no 404 de forma deliberada: el recurso existe, pero es ajeno.
        if reserva.id_cliente != usuario.id_usuario:
            raise AuthorizationError(
                "Esta reserva pertenece a otro cliente.", code="RESERVA_AJENA"
            )

        if ReservaConsultaServicio._vencer_si_corresponde(db, reserva, usuario):
            db.commit()
            raise ConflictError(
                f"La reserva {formatear_codigo_reserva(reserva.id_reserva, reserva.creado_en)} "
                "venció sin ser atendida y sus prendas ya volvieron a estar disponibles.",
                code="RESERVA_VENCIDA",
            )

        if reserva.estado not in ESTADOS_CANCELABLES:
            raise ConflictError(
                f"La reserva está en estado '{reserva.estado}' y no admite cancelación.",
                code="RESERVA_NO_CANCELABLE",
            )

        if datetime.now(timezone.utc) >= ReservaConsultaServicio._con_tz(reserva.fecha_hora_atencion):
            raise ConflictError(
                "La hora de la cita ya llegó; no puede cancelarse desde aquí.",
                code="RESERVA_NO_CANCELABLE",
            )

        ReservaConsultaServicio._liberar_stock(db, reserva, usuario, payload.motivo)
        reserva.estado = "cancelada"

        db.commit()
        db.refresh(reserva)

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

        nombre_usuario = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario,
            accion="CANCELAR_RESERVA",
            tabla_modulo="reservas",
            severidad="INFO",
            payload_anterior={"estado": "pendiente_o_confirmada"},
            payload_nuevo={"id_reserva": reserva.id_reserva, "motivo": payload.motivo},
            db=db,
        )

        return ReservaConsultaServicio._construir_salida(reserva)

    # ------------------------------------------------------------------
    # Apoyo interno
    # ------------------------------------------------------------------

    @staticmethod
    def _con_tz(fecha: datetime) -> datetime:
        return fecha if fecha.tzinfo is not None else fecha.replace(tzinfo=timezone.utc)

    @staticmethod
    def _es_candidata_a_vencer(reserva: ReservaORM) -> bool:
        """Filtro barato (sin bloqueo) para no releer con `FOR UPDATE` cada reserva del listado."""
        if reserva.estado not in ("pendiente", "confirmada"):
            return False
        limite = ReservaConsultaServicio._con_tz(reserva.fecha_hora_atencion) + TOLERANCIA_VENCIMIENTO
        return datetime.now(timezone.utc) > limite

    @staticmethod
    def _vencer_si_corresponde(db: Session, reserva: ReservaORM, usuario: UsuarioORM) -> bool:
        """Revalida con datos frescos (ya bloqueados) y vence la reserva si sigue correspondiendo."""
        if not ReservaConsultaServicio._es_candidata_a_vencer(reserva):
            return False

        ReservaConsultaServicio._liberar_stock(db, reserva, usuario, MOTIVO_VENCIMIENTO)
        reserva.estado = "vencida"

        from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

        nombre_usuario = f"{usuario.nombres} {usuario.apellidos}".strip() or usuario.email
        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=nombre_usuario,
            accion="VENCER_RESERVA",
            tabla_modulo="reservas",
            severidad="INFO",
            payload_anterior={"estado": "pendiente_o_confirmada"},
            payload_nuevo={"id_reserva": reserva.id_reserva, "motivo": MOTIVO_VENCIMIENTO},
            db=db,
        )

        return True

    @staticmethod
    def _liberar_stock(
        db: Session, reserva: ReservaORM, usuario: UsuarioORM, motivo: str
    ) -> None:
        """Devuelve a `cantidad_disponible` las unidades que esta reserva apartó, línea por línea."""
        codigo = formatear_codigo_reserva(reserva.id_reserva, reserva.creado_en)

        for detalle in reserva.detalles:
            movimiento = ReservaConsultaRepositorio.buscar_movimiento_reserva(
                db, reserva.id_reserva, detalle.id_variante
            )
            if not movimiento:
                raise ConflictError(
                    f"No se encontró el apartado original de "
                    f"'{detalle.variante.producto.nombre}' para la reserva {codigo}.",
                    code="RESERVA_SIN_TRAZA",
                )

            inventario = ReservaConsultaRepositorio.obtener_inventario_por_id(
                db, movimiento.id_inventario
            )
            if not inventario or inventario.cantidad_reservada < detalle.cantidad:
                raise ConflictError(
                    f"El inventario apartado para la reserva {codigo} es inconsistente y no "
                    "puede liberarse automáticamente. Contacta con la boutique.",
                    code="RESERVA_SIN_TRAZA",
                )

            # Saldos referidos a `cantidad_disponible`, igual que el resto de liberaciones del
            # proyecto (`cancelacion_pedido` en CU15): es la magnitud que este movimiento aumenta.
            saldo_anterior = inventario.cantidad_disponible
            inventario.cantidad_reservada -= detalle.cantidad
            inventario.cantidad_disponible += detalle.cantidad

            ReservaConsultaRepositorio.registrar_movimiento_liberacion(
                db=db,
                id_inventario=inventario.id_inventario,
                cantidad=detalle.cantidad,
                id_usuario=usuario.id_usuario,
                referencia=f"RESERVA-{reserva.id_reserva}",
                motivo=motivo,
                saldo_anterior=saldo_anterior,
                saldo_nuevo=inventario.cantidad_disponible,
            )

    @staticmethod
    def _construir_salida(reserva: ReservaORM) -> ReservaOut:
        items = []
        total_prendas = 0
        for detalle in reserva.detalles:
            variante = detalle.variante
            precio_unitario = variante.producto.precio_base + (variante.precio_extra or Decimal("0.00"))
            items.append(
                ReservaItemOut(
                    id_variante=variante.id_variante,
                    nombre_producto=variante.producto.nombre,
                    talla_codigo=variante.talla.codigo,
                    color_nombre=variante.color.nombre,
                    color_hex=variante.color.codigo_hex,
                    imagen_url=variante.producto.imagen_url,
                    cantidad=detalle.cantidad,
                    precio_unitario=precio_unitario,
                )
            )
            total_prendas += detalle.cantidad

        fecha_cita = ReservaConsultaServicio._con_tz(reserva.fecha_hora_atencion)
        puede_cancelar = (
            reserva.estado in ESTADOS_CANCELABLES and datetime.now(timezone.utc) < fecha_cita
        )

        return ReservaOut(
            id_reserva=reserva.id_reserva,
            codigo_reserva=formatear_codigo_reserva(reserva.id_reserva, reserva.creado_en),
            estado=reserva.estado,
            fecha_hora_atencion=reserva.fecha_hora_atencion,
            creado_en=reserva.creado_en,
            sucursal=SucursalReservaOut(
                id_sucursal=reserva.sucursal.id_sucursal,
                nombre=reserva.sucursal.nombre,
                direccion=reserva.sucursal.direccion,
            ),
            items=items,
            total_prendas=total_prendas,
            observacion=reserva.observacion,
            puede_cancelar=puede_cancelar,
        )
