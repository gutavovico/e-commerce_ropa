"""Modelos ORM de SQLAlchemy 2.0 para el paquete de Catálogo y Exploración.

Mapea las tablas del esquema `fashionstore` definidas en SI2-Parcial1.md:
- categorias
- temporadas
- colecciones
- tallas
- colores
- productos
- variantes_producto
- inventario_sucursal
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base

# Enums existentes en PostgreSQL
tipo_temporada_enum = PG_ENUM(
    "primavera_verano",
    "otono_invierno",
    "escolar",
    "promocion_especial",
    "nueva_coleccion",
    name="tipo_temporada",
    schema="fashionstore",
    create_type=False,
)

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


class CategoriaORM(Base):
    """Mapeo de la tabla `fashionstore.categorias`."""

    __tablename__ = "categorias"
    __table_args__ = {"schema": "fashionstore"}

    id_categoria: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    id_categoria_padre: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.categorias.id_categoria"), nullable=True
    )

    categoria_padre: Mapped[Optional["CategoriaORM"]] = relationship(
        "CategoriaORM", remote_side=[id_categoria], back_populates="subcategorias"
    )
    subcategorias: Mapped[List["CategoriaORM"]] = relationship(
        "CategoriaORM", back_populates="categoria_padre"
    )
    productos: Mapped[List["ProductoORM"]] = relationship("ProductoORM", back_populates="categoria")


class TemporadaORM(Base):
    """Mapeo de la tabla `fashionstore.temporadas`."""

    __tablename__ = "temporadas"
    __table_args__ = {"schema": "fashionstore"}

    id_temporada: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    tipo: Mapped[str] = mapped_column(tipo_temporada_enum, nullable=False)
    fecha_inicio: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_fin: Mapped[date] = mapped_column(Date, nullable=False)
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    colecciones: Mapped[List["ColeccionORM"]] = relationship(
        "ColeccionORM", back_populates="temporada"
    )


class ColeccionORM(Base):
    """Mapeo de la tabla `fashionstore.colecciones`."""

    __tablename__ = "colecciones"
    __table_args__ = {"schema": "fashionstore"}

    id_coleccion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_temporada: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.temporadas.id_temporada"), nullable=False, index=True
    )
    id_proveedor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    temporada: Mapped["TemporadaORM"] = relationship("TemporadaORM", back_populates="colecciones")
    productos: Mapped[List["ProductoORM"]] = relationship("ProductoORM", back_populates="coleccion")


class TallaORM(Base):
    """Mapeo de la tabla `fashionstore.tallas`."""

    __tablename__ = "tallas"
    __table_args__ = {"schema": "fashionstore"}

    id_talla: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    orden: Mapped[int] = mapped_column(SmallInteger, nullable=False, default=0)


class ColorORM(Base):
    """Mapeo de la tabla `fashionstore.colores`."""

    __tablename__ = "colores"
    __table_args__ = {"schema": "fashionstore"}

    id_color: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    codigo_hex: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)


class ProductoORM(Base):
    """Mapeo de la tabla `fashionstore.productos`."""

    __tablename__ = "productos"
    __table_args__ = {"schema": "fashionstore"}

    id_producto: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_categoria: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.categorias.id_categoria"), nullable=False, index=True
    )
    id_coleccion: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.colecciones.id_coleccion"), nullable=True, index=True
    )
    id_proveedor: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    precio_base: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    imagen_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    modelo_ar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    categoria: Mapped["CategoriaORM"] = relationship("CategoriaORM", back_populates="productos")
    coleccion: Mapped[Optional["ColeccionORM"]] = relationship(
        "ColeccionORM", back_populates="productos"
    )
    variantes: Mapped[List["VarianteProductoORM"]] = relationship(
        "VarianteProductoORM", back_populates="producto", cascade="all, delete-orphan"
    )


class VarianteProductoORM(Base):
    """Mapeo de la tabla `fashionstore.variantes_producto`."""

    __tablename__ = "variantes_producto"
    __table_args__ = (
        UniqueConstraint("id_producto", "id_talla", "id_color", name="uq_variante_producto_talla_color"),
        {"schema": "fashionstore"},
    )

    id_variante: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_producto: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.productos.id_producto", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_talla: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.tallas.id_talla"), nullable=False, index=True
    )
    id_color: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.colores.id_color"), nullable=False, index=True
    )
    sku: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    precio_extra: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True, index=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    producto: Mapped["ProductoORM"] = relationship("ProductoORM", back_populates="variantes")
    talla: Mapped["TallaORM"] = relationship("TallaORM")
    color: Mapped["ColorORM"] = relationship("ColorORM")
    inventarios: Mapped[List["InventarioSucursalORM"]] = relationship(
        "InventarioSucursalORM", back_populates="variante"
    )


class InventarioSucursalORM(Base):
    """Mapeo de la tabla `fashionstore.inventario_sucursal`."""

    __tablename__ = "inventario_sucursal"
    __table_args__ = (
        UniqueConstraint("id_sucursal", "id_variante", "id_temporada", name="uq_inventario_sucursal_variante_temporada"),
        CheckConstraint("cantidad_disponible >= 0", name="chk_inventario_disponible_positivo"),
        CheckConstraint("cantidad_reservada >= 0", name="chk_inventario_reservada_positivo"),
        CheckConstraint("stock_minimo >= 0", name="chk_inventario_stock_minimo_positivo"),
        CheckConstraint("stock_alerta >= 0", name="chk_inventario_stock_alerta_positivo"),
        {"schema": "fashionstore", "extend_existing": True},
    )

    id_inventario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_variante: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.variantes_producto.id_variante"),
        nullable=False,
        index=True,
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fashionstore.sucursales.id_sucursal"),
        nullable=False,
        index=True,
    )
    id_temporada: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fashionstore.temporadas.id_temporada"),
        nullable=False,
        default=1,
    )
    cantidad_disponible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_reservada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_alerta: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    estado: Mapped[str] = mapped_column(
        estado_prenda_stock_enum, nullable=False, default="disponible", index=True
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    variante: Mapped["VarianteProductoORM"] = relationship(
        "VarianteProductoORM", back_populates="inventarios"
    )
    sucursal = relationship(
        "SucursalORM",
        foreign_keys=[id_sucursal],
        lazy="joined",
    )




