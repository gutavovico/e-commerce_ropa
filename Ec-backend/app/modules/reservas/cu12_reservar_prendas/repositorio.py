"""Repositorio de acceso a datos para CU12: Reservas de prendas en boutique."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import InventarioSucursalORM, SucursalORM, VarianteProductoORM
from modules.reservas.modelos import MovimientoInventarioORM, ReservaDetalleORM, ReservaORM


class ReservaRepositorio:
    """Acceso a datos y persistencia transaccional de citas y reservas en boutique."""

    @staticmethod
    def obtener_sucursal_activa(db: Session, id_sucursal: int) -> Optional[SucursalORM]:
        """Obtiene una sucursal activa por ID."""
        stmt = (
            select(SucursalORM)
            .options(selectinload(SucursalORM.ciudad))
            .where(SucursalORM.id_sucursal == id_sucursal, SucursalORM.activa.is_(True))
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_sucursales_activas(db: Session) -> List[SucursalORM]:
        """Obtiene todas las boutiques físicas activas para agendar citas."""
        stmt = (
            select(SucursalORM)
            .options(selectinload(SucursalORM.ciudad))
            .where(SucursalORM.activa.is_(True))
            .order_by(SucursalORM.id_sucursal.asc())
        )
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def asegurar_cliente(db: Session, usuario: UsuarioORM) -> ClienteORM:
        """Verifica o crea la ficha de cliente para el usuario autenticado."""
        stmt = select(ClienteORM).where(ClienteORM.id_cliente == usuario.id_usuario)
        cliente = db.execute(stmt).scalar_one_or_none()
        if not cliente:
            cliente = ClienteORM(
                id_cliente=usuario.id_usuario,
                talla_preferida="38",
                acepta_marketing=True,
            )
            db.add(cliente)
            db.flush()
        return cliente

    @staticmethod
    def obtener_variante_con_prenda(db: Session, id_variante: int) -> Optional[VarianteProductoORM]:
        """Obtiene la variante con sus relaciones de talla, color y producto."""
        stmt = (
            select(VarianteProductoORM)
            .options(
                selectinload(VarianteProductoORM.producto),
                selectinload(VarianteProductoORM.talla),
                selectinload(VarianteProductoORM.color),
            )
            .where(VarianteProductoORM.id_variante == id_variante)
        )
        return db.execute(stmt).scalar_one_or_none()

    @staticmethod
    def obtener_inventario_para_reserva(
        db: Session, id_variante: int, id_sucursal: int, cantidad: int = 1
    ) -> Optional[InventarioSucursalORM]:
        """Obtiene el inventario de la variante en la sucursal con bloqueo de concurrencia.

        La clave única real de `inventario_sucursal` es (id_variante, id_sucursal, id_temporada),
        de modo que una misma variante puede tener existencias repartidas en varias temporadas
        dentro de la misma boutique. Por eso no se puede usar `scalar_one_or_none()` sobre el par
        (variante, sucursal): en cuanto hubiese stock de una segunda temporada lanzaría
        `MultipleResultsFound` y la reserva respondería 500.

        Se elige de forma determinista la fila de la temporada más reciente que ya cubra la
        cantidad solicitada y, si ninguna la cubre, la de mayor stock, para que el mensaje de
        existencias insuficientes informe la disponibilidad real más favorable.
        """
        base = select(InventarioSucursalORM).where(
            InventarioSucursalORM.id_variante == id_variante,
            InventarioSucursalORM.id_sucursal == id_sucursal,
        )

        stmt = (
            base.where(InventarioSucursalORM.cantidad_disponible >= cantidad)
            .order_by(InventarioSucursalORM.id_temporada.desc())
            .limit(1)
            .with_for_update()
        )
        inventario = db.execute(stmt).scalars().first()
        if inventario:
            return inventario

        stmt_sin_stock = (
            base.order_by(
                InventarioSucursalORM.cantidad_disponible.desc(),
                InventarioSucursalORM.id_temporada.desc(),
            )
            .limit(1)
            .with_for_update()
        )
        return db.execute(stmt_sin_stock).scalars().first()

    @staticmethod
    def crear_reserva(
        db: Session,
        id_cliente: int,
        id_sucursal: int,
        fecha_hora_atencion: datetime,
        canal_origen: str,
        observacion: Optional[str] = None,
    ) -> ReservaORM:
        """Crea la cabecera de la reserva en estado pendiente."""
        reserva = ReservaORM(
            id_cliente=id_cliente,
            id_sucursal=id_sucursal,
            fecha_hora_atencion=fecha_hora_atencion,
            estado="pendiente",
            canal_origen=canal_origen,
            observacion=observacion,
        )
        db.add(reserva)
        db.flush()
        return reserva

    @staticmethod
    def crear_detalle_reserva(
        db: Session, id_reserva: int, id_variante: int, cantidad: int
    ) -> ReservaDetalleORM:
        """Registra una línea de prenda en la reserva."""
        detalle = ReservaDetalleORM(
            id_reserva=id_reserva,
            id_variante=id_variante,
            cantidad=cantidad,
        )
        db.add(detalle)
        db.flush()
        return detalle

    @staticmethod
    def registrar_movimiento_inventario(
        db: Session,
        id_inventario: int,
        cantidad: int,
        id_usuario: int,
        referencia: str,
        observacion: str,
        saldo_anterior: int = 0,
        saldo_nuevo: int = 0,
    ) -> MovimientoInventarioORM:
        """Registra la auditoría física inmutable de reserva en movimientos_inventario."""
        movimiento = MovimientoInventarioORM(
            id_inventario=id_inventario,
            tipo_movimiento="reserva",
            cantidad=cantidad,
            id_usuario_responsable=id_usuario,
            referencia_documento=referencia,
            observacion=observacion,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
        )
        db.add(movimiento)
        return movimiento
