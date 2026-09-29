"""Acceso a datos para CU13/CU14: Consultar y Cancelar Reservas.

Sin lógica de negocio: solo consultas y bloqueos. `ReservaORM.sucursal`, `ReservaORM.detalles`,
`ReservaDetalleORM.variante` y `VarianteProductoORM.producto/talla/color` ya están declaradas
`lazy="selectin"` en sus modelos, así que no hace falta repetir `.options(selectinload(...))` aquí:
SQLAlchemy las trae en consultas aparte automáticamente, sin JOIN (por eso conviven con
`FOR UPDATE` sin problema — ver la nota de `cu12_reservar_prendas.repositorio`).
"""

from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from modules.catalogo.modelos import InventarioSucursalORM
from modules.reservas.modelos import MovimientoInventarioORM, ReservaORM


class ReservaConsultaRepositorio:
    """Repositorio de solo lectura (más el bloqueo puntual que exige cancelar/vencer)."""

    @staticmethod
    def buscar_reservas_de_cliente(db: Session, id_cliente: int) -> List[ReservaORM]:
        """Todas las reservas del cliente, sin bloqueo: es una lectura de listado."""
        stmt = select(ReservaORM).where(ReservaORM.id_cliente == id_cliente)
        return list(db.execute(stmt).scalars().all())

    @staticmethod
    def obtener_reserva_para_actualizar(db: Session, id_reserva: int) -> Optional[ReservaORM]:
        """Carga una reserva con bloqueo de fila, para cancelarla o vencerla sin condición de carrera."""
        stmt = (
            select(ReservaORM)
            .where(ReservaORM.id_reserva == id_reserva)
            .with_for_update(of=ReservaORM)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def buscar_movimiento_reserva(
        db: Session, id_reserva: int, id_variante: int
    ) -> Optional[MovimientoInventarioORM]:
        """Localiza el movimiento `reserva` que CU12 escribió para esta línea.

        Es la única forma fiable de saber de qué fila de `inventario_sucursal` (qué temporada)
        salieron las unidades: `reserva_detalle` no lo guarda, y una variante puede tener stock
        repartido en varias temporadas dentro de la misma boutique.
        """
        stmt = (
            select(MovimientoInventarioORM)
            .join(
                InventarioSucursalORM,
                InventarioSucursalORM.id_inventario == MovimientoInventarioORM.id_inventario,
            )
            .where(
                MovimientoInventarioORM.referencia_documento == f"RESERVA-{id_reserva}",
                MovimientoInventarioORM.tipo_movimiento == "reserva",
                InventarioSucursalORM.id_variante == id_variante,
            )
            .order_by(MovimientoInventarioORM.id_movimiento.desc())
            .limit(1)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def obtener_inventario_por_id(
        db: Session, id_inventario: int
    ) -> Optional[InventarioSucursalORM]:
        """Carga la fila exacta de inventario a liberar, bloqueada para la misma transacción."""
        stmt = (
            select(InventarioSucursalORM)
            .where(InventarioSucursalORM.id_inventario == id_inventario)
            .with_for_update(of=InventarioSucursalORM)
        )
        return db.execute(stmt).scalars().first()

    @staticmethod
    def registrar_movimiento_liberacion(
        db: Session,
        id_inventario: int,
        cantidad: int,
        id_usuario: int,
        referencia: str,
        motivo: str,
        saldo_anterior: int,
        saldo_nuevo: int,
    ) -> MovimientoInventarioORM:
        """Registra en `movimientos_inventario` la devolución de existencias al liberar una reserva."""
        movimiento = MovimientoInventarioORM(
            id_inventario=id_inventario,
            tipo_movimiento="liberacion_reserva",
            cantidad=cantidad,
            id_usuario=id_usuario,
            referencia_documento=referencia,
            motivo=motivo,
            saldo_anterior=saldo_anterior,
            saldo_nuevo=saldo_nuevo,
        )
        db.add(movimiento)
        return movimiento
