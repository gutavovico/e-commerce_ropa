"""Modelos ORM para CU27: Gestionar promociones.

Mapeo de la tabla fashionstore.promociones sobre PostgreSQL Neon.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from core.database import Base
from modules.catalogo.modelos import CategoriaORM, ProductoORM


class PromocionORM(Base):
    """Entidad ORM representativa de una promocion comercial o cupon de descuento."""

    __tablename__ = "promociones"
    __table_args__ = (
        CheckConstraint("fecha_fin > fecha_inicio", name="chk_promociones_fechas_orden"),
        CheckConstraint(
            "tipo_descuento IN ('porcentaje', 'monto_fijo')",
            name="chk_promociones_tipo_descuento",
        ),
        CheckConstraint("valor_descuento > 0", name="chk_promociones_valor_positivo"),
        CheckConstraint(
            "tipo_descuento != 'porcentaje' OR (valor_descuento >= 1.00 AND valor_descuento <= 100.00)",
            name="chk_promociones_porcentaje_tope",
        ),
        CheckConstraint(
            "tope_descuento IS NULL OR tope_descuento >= 0",
            name="chk_promociones_tope_positivo",
        ),
        CheckConstraint("usos_actuales >= 0", name="chk_promociones_usos_no_negativos"),
        CheckConstraint(
            "limite_usos IS NULL OR limite_usos > 0",
            name="chk_promociones_limite_positivo",
        ),
        CheckConstraint(
            "alcance IN ('global', 'categoria', 'producto')",
            name="chk_promociones_alcance_tipo",
        ),
        Index(
            "uq_promociones_codigo_cupon_lower",
            func.lower(func.trim(func.coalesce("codigo_cupon", ""))),
            unique=True,
            postgresql_where=func.coalesce("codigo_cupon", "").isnot(None),
        ),
        {"schema": "fashionstore"},
    )

    id_promocion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    codigo_cupon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tipo_descuento: Mapped[str] = mapped_column(String(20), nullable=False, default="porcentaje")
    valor_descuento: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    tope_descuento: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    limite_usos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usos_actuales: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alcance: Mapped[str] = mapped_column(String(20), nullable=False, default="global")
    id_categoria: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.categorias.id_categoria", ondelete="SET NULL"), nullable=True
    )
    id_producto: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.productos.id_producto", ondelete="SET NULL"), nullable=True
    )
    estado_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Compatibilidad con nomenclatura previa
    activa = synonym("estado_activo")

    # Relaciones relacionales
    categoria = relationship(CategoriaORM, foreign_keys=[id_categoria], lazy="joined")
    producto = relationship(ProductoORM, foreign_keys=[id_producto], lazy="joined")
