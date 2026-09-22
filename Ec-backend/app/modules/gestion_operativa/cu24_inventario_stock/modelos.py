"""Modelos ORM de SQLAlchemy 2.0 para CU24: Gestionar Inventario, Stock y Existencias por Sucursal.

Mapeo de existencias fisicas por sucursal y registro auditable de movimientos (Kardex)
sobre el esquema fashionstore en PostgreSQL Neon.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from core.database import Base
from modules.catalogo.modelos import InventarioSucursalORM


# Tipos Enumerados PostgreSQL mapeados en esquema fashionstore
estado_prenda_stock_enum = PG_ENUM(
    "disponible",
    "reservada",
    "vendida",
    "agotada",
    "proxima_ingreso",
    "devuelta",
    name="estado_prenda_stock",
    schema="fashionstore",
    create_type=False,
)

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


class MovimientoInventarioORM(Base):
    """Registro inmutable de trazabilidad contable y operativa (Kardex)."""

    __tablename__ = "movimientos_inventario"
    __table_args__ = (
        CheckConstraint("cantidad <> 0", name="chk_movimiento_cantidad_no_cero"),
        {"schema": "fashionstore", "extend_existing": True},
    )

    id_movimiento: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_inventario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.inventario_sucursal.id_inventario"),
        nullable=False,
        index=True,
    )
    tipo_movimiento: Mapped[str] = mapped_column(
        tipo_movimiento_inv_enum,
        nullable=False,
        index=True,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    saldo_anterior: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    saldo_nuevo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    motivo: Mapped[str] = mapped_column(
        "observacion",
        Text,
        nullable=False,
    )
    id_usuario: Mapped[Optional[int]] = mapped_column(
        "id_usuario_responsable",
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario"),
        nullable=True,
        index=True,
    )
    referencia_documento: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    inventario = relationship(
        InventarioSucursalORM,
        back_populates="movimientos",
    )
    usuario_responsable = relationship(
        "UsuarioORM",
        foreign_keys=[id_usuario],
        lazy="joined",
    )

    id_usuario_responsable = synonym("id_usuario")
    observacion = synonym("motivo")

    def __init__(self, **kwargs):
        if "id_usuario_responsable" in kwargs and "id_usuario" not in kwargs:
            kwargs["id_usuario"] = kwargs.pop("id_usuario_responsable")
        if "observacion" in kwargs and "motivo" not in kwargs:
            kwargs["motivo"] = kwargs.pop("observacion")
        super().__init__(**kwargs)



# Asociacion bidireccional de movimientos sobre la entidad canonica InventarioSucursalORM
InventarioSucursalORM.movimientos = relationship(
    MovimientoInventarioORM,
    back_populates="inventario",
    cascade="all, delete-orphan",
    order_by=MovimientoInventarioORM.creado_en.desc(),
)


__all__ = [
    "InventarioSucursalORM",
    "MovimientoInventarioORM",
    "estado_prenda_stock_enum",
    "tipo_movimiento_inv_enum",
]


