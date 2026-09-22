"""Modelos ORM de SQLAlchemy 2.0 para el paquete de Reservas y Movimientos de Inventario.

Mapea las tablas del esquema `fashionstore`:
- reservas
- reserva_detalle
- movimientos_inventario
"""

from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from modules.catalogo.modelos import InventarioSucursalORM, SucursalORM, VarianteProductoORM

# Enums existentes en PostgreSQL Neon
estado_reserva_enum = PG_ENUM(
    "pendiente",
    "confirmada",
    "en_atencion",
    "atendida",
    "cancelada",
    "vencida",
    name="estado_reserva",
    schema="fashionstore",
    create_type=False,
)

canal_origen_enum = PG_ENUM(
    "web",
    "movil",
    "sucursal",
    name="canal_origen",
    schema="fashionstore",
    create_type=False,
)

# Los 12 valores del enum `fashionstore.tipo_movimiento_inv` tal y como existen en PostgreSQL
# (verificado por introspección el 2026-09-22). Declarar menos de los reales no es inocuo:
# SQLAlchemy valida en Python antes de escribir, así que registrar un movimiento
# `venta_confirmada` o `cancelacion_pedido` fallaría pese a ser válido en la base.
tipo_movimiento_inv_enum = PG_ENUM(
    "ingreso_proveedor",
    "reserva",
    "liberacion_reserva",
    "venta",
    "devolucion",
    "ajuste",
    "transferencia_salida",
    "transferencia_entrada",
    "ajuste_positivo",
    "ajuste_negativo",
    "venta_confirmada",
    "cancelacion_pedido",
    name="tipo_movimiento_inv",
    schema="fashionstore",
    create_type=False,
)


from modules.comercial.cu28_ventas_reservas.modelos import ReservaORM, ReservaDetalleORM
from modules.gestion_operativa.cu24_inventario_stock.modelos import MovimientoInventarioORM

<<<<<<< Updated upstream
=======
    __tablename__ = "reservas"
    __table_args__ = {"schema": "fashionstore"}

    id_reserva: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente"), nullable=False, index=True
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=False, index=True
    )
    fecha_hora_atencion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    estado: Mapped[str] = mapped_column(
        estado_reserva_enum, nullable=False, default="pendiente", index=True
    )
    canal_origen: Mapped[str] = mapped_column(canal_origen_enum, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atendido_por: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    atendido_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    sucursal: Mapped["SucursalORM"] = relationship("SucursalORM")
    detalles: Mapped[List["ReservaDetalleORM"]] = relationship(
        "ReservaDetalleORM", back_populates="reserva", cascade="all, delete-orphan"
    )


class ReservaDetalleORM(Base):
    """Mapeo de la tabla `fashionstore.reserva_detalle`."""

    __tablename__ = "reserva_detalle"
    __table_args__ = (
        # Presente en el DDL (0001_base_ddl.py) pero ausente del ORM: sin declararla, el código
        # no "ve" que dos líneas de la misma variante son ilegales y el IntegrityError resultante
        # escapa del árbol de DomainError como un 500.
        UniqueConstraint("id_reserva", "id_variante", name="uq_reserva_detalle_reserva_variante"),
        {"schema": "fashionstore"},
    )

    id_reserva_detalle: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_reserva: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.reservas.id_reserva", ondelete="CASCADE"), nullable=False, index=True
    )
    id_variante: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.variantes_producto.id_variante"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    reserva: Mapped["ReservaORM"] = relationship("ReservaORM", back_populates="detalles")
    variante: Mapped["VarianteProductoORM"] = relationship("VarianteProductoORM")


class MovimientoInventarioORM(Base):
    """Mapeo de la tabla `fashionstore.movimientos_inventario` para auditoría física."""

    __tablename__ = "movimientos_inventario"
    __table_args__ = {"schema": "fashionstore"}

    id_movimiento: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_inventario: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.inventario_sucursal.id_inventario"), nullable=False, index=True
    )
    tipo_movimiento: Mapped[str] = mapped_column(tipo_movimiento_inv_enum, nullable=False, index=True)
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    id_usuario_responsable: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.usuarios.id_usuario"), nullable=True
    )
    referencia_documento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # Existencias antes y después del movimiento. Son `NOT NULL DEFAULT 0` en PostgreSQL y hasta
    # el 2026-09-22 no estaban mapeadas, de modo que toda la bitácora se escribía en `0 -> 0`:
    # registraba qué se movió, pero no desde dónde hasta dónde, que es lo que la hace auditable.
    # Quien escriba un movimiento debe informarlos con los valores reales.
    saldo_anterior: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saldo_nuevo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    inventario: Mapped["InventarioSucursalORM"] = relationship("InventarioSucursalORM")
>>>>>>> Stashed changes
