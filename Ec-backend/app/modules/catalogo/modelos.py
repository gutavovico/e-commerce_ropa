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
    Date,
    DateTime,
    FetchedValue,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
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

tipo_venta_enum = PG_ENUM(
    "presencial",
    "digital_web",
    "digital_movil",
    name="tipo_venta",
    schema="fashionstore",
    create_type=False,
)

estado_venta_enum = PG_ENUM(
    "pendiente",
    "pagada",
    "anulada",
    "devuelta",
    name="estado_venta",
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
    # La columna real en PostgreSQL es `estado_activo`, no `activa`. El atributo Python conserva
    # el nombre de dominio para no alterar las consultas (`TemporadaORM.activa`).
    # Ojo: `alembic/versions/0001_base_ddl.py` declara `activa` y NO refleja la base real.
    activa: Mapped[bool] = mapped_column("estado_activo", Boolean, nullable=False, default=True)

    colecciones: Mapped[List["ColeccionORM"]] = relationship(
        "ColeccionORM", back_populates="temporada"
    )


class ProveedorORM(Base):
    """Mapeo de la tabla `fashionstore.proveedores`."""

    __tablename__ = "proveedores"
    __table_args__ = {"schema": "fashionstore"}

    id_proveedor: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_usuario: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    razon_social: Mapped[str] = mapped_column(String(200), nullable=False)
    # La columna real en PostgreSQL es `nit_rut` (la migración 0001 declara `nit`).
    nit: Mapped[Optional[str]] = mapped_column("nit_rut", String(30), unique=True, nullable=True)
    contacto_nombre: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    # La columna real en PostgreSQL es `estado_activo` (la migración 0001 declara `activo`).
    activo: Mapped[bool] = mapped_column("estado_activo", Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    colecciones: Mapped[List["ColeccionORM"]] = relationship("ColeccionORM", back_populates="proveedor")


class ColeccionORM(Base):
    """Mapeo de la tabla `fashionstore.colecciones`."""

    __tablename__ = "colecciones"
    __table_args__ = {"schema": "fashionstore"}

    id_coleccion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_temporada: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.temporadas.id_temporada"), nullable=False, index=True
    )
    id_proveedor: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.proveedores.id_proveedor"), nullable=True, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    temporada: Mapped["TemporadaORM"] = relationship("TemporadaORM", back_populates="colecciones")
    proveedor: Mapped[Optional["ProveedorORM"]] = relationship("ProveedorORM", back_populates="colecciones")
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
    __table_args__ = {"schema": "fashionstore"}

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
    sku: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    precio_extra: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, default=Decimal("0.00"))

    producto: Mapped["ProductoORM"] = relationship("ProductoORM", back_populates="variantes")
    talla: Mapped["TallaORM"] = relationship("TallaORM")
    color: Mapped["ColorORM"] = relationship("ColorORM")
    inventarios: Mapped[List["InventarioSucursalORM"]] = relationship(
        "InventarioSucursalORM", back_populates="variante"
    )


class InventarioSucursalORM(Base):
    """Mapeo de la tabla `fashionstore.inventario_sucursal`."""

    __tablename__ = "inventario_sucursal"
    __table_args__ = {"schema": "fashionstore"}

    id_inventario: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_variante: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.variantes_producto.id_variante"),
        nullable=False,
        index=True,
    )
    id_sucursal: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    id_temporada: Mapped[int] = mapped_column(Integer, nullable=False)
    cantidad_disponible: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cantidad_reservada: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    stock_minimo: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    estado: Mapped[str] = mapped_column(
        estado_prenda_stock_enum, nullable=False, default="disponible", index=True
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    variante: Mapped["VarianteProductoORM"] = relationship(
        "VarianteProductoORM", back_populates="inventarios"
    )


class CiudadORM(Base):
    """Mapeo de la tabla `fashionstore.ciudades`."""

    __tablename__ = "ciudades"
    __table_args__ = {"schema": "fashionstore"}

    id_ciudad: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    pais: Mapped[str] = mapped_column(String(100), nullable=False, default="España")
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )


class SucursalORM(Base):
    """Mapeo de la tabla `fashionstore.sucursales`."""

    __tablename__ = "sucursales"
    __table_args__ = {"schema": "fashionstore"}

    id_sucursal: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    id_ciudad: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.ciudades.id_ciudad"), nullable=False, index=True
    )
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    direccion: Mapped[str] = mapped_column(String(255), nullable=False)
    telefono: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    horario_apertura: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="09:00")
    horario_cierre: Mapped[Optional[str]] = mapped_column(String(10), nullable=True, default="20:00")
    activa: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    ciudad: Mapped[Optional["CiudadORM"]] = relationship("CiudadORM")


class VentaORM(Base):
    """Mapeo de la tabla `fashionstore.ventas`."""

    __tablename__ = "ventas"
    __table_args__ = {"schema": "fashionstore"}

    id_venta: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(30), unique=True, nullable=False)
    id_cliente: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente"), nullable=True, index=True
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=False, index=True
    )
    id_cajero: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    id_reserva: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    tipo_venta: Mapped[str] = mapped_column(tipo_venta_enum, nullable=False)
    estado: Mapped[str] = mapped_column(estado_venta_enum, nullable=False, default="pendiente", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    descuento: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    fecha_venta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    # --- Columnas añadidas por la migración 0009 para CU15 (Comprar desde la plataforma) ---
    # `id_sucursal` (arriba) es la sucursal RESPONSABLE de la orden; la boutique concreta desde
    # la que se expide cada prenda vive en `VentaDetalleORM.id_sucursal`, porque la bolsa es
    # multi-boutique por diseño.
    tipo_entrega: Mapped[str] = mapped_column(String(20), nullable=False, default="domicilio")
    id_sucursal_retiro: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=True
    )
    direccion_envio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_promocion: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.promociones.id_promocion"), nullable=True
    )

    sucursal: Mapped["SucursalORM"] = relationship("SucursalORM", foreign_keys=[id_sucursal])
    sucursal_retiro: Mapped[Optional["SucursalORM"]] = relationship(
        "SucursalORM", foreign_keys=[id_sucursal_retiro]
    )
    promocion: Mapped[Optional["PromocionORM"]] = relationship("PromocionORM")
    detalles: Mapped[List["VentaDetalleORM"]] = relationship(
        "VentaDetalleORM", back_populates="venta", cascade="all, delete-orphan"
    )


class VentaDetalleORM(Base):
    """Mapeo de la tabla `fashionstore.venta_detalle`."""

    __tablename__ = "venta_detalle"
    __table_args__ = {"schema": "fashionstore"}

    id_venta_detalle: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_venta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.ventas.id_venta", ondelete="CASCADE"), nullable=False, index=True
    )
    id_variante: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.variantes_producto.id_variante"), nullable=False
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)

    # `subtotal_linea` está definida en PostgreSQL como GENERATED ALWAYS AS
    # (cantidad * precio_unitario). Se mapea en SOLO LECTURA: incluirla en un INSERT o UPDATE
    # hace que PostgreSQL rechace la sentencia.
    subtotal_linea: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(12, 2),
        server_default=FetchedValue(),
        server_onupdate=FetchedValue(),
        nullable=True,
    )

    # Añadida por la migración 0009: boutique desde la que se expide esta prenda concreta.
    id_sucursal: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=True, index=True
    )

    venta: Mapped["VentaORM"] = relationship("VentaORM", back_populates="detalles")
    variante: Mapped["VarianteProductoORM"] = relationship("VarianteProductoORM")
    sucursal: Mapped[Optional["SucursalORM"]] = relationship("SucursalORM")


class RecomendacionIAORM(Base):
    """Mapeo de la tabla `fashionstore.recomendaciones_ia`."""

    __tablename__ = "recomendaciones_ia"
    __table_args__ = {"schema": "fashionstore"}

    id_recomendacion: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente"), nullable=False, index=True
    )
    id_producto: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.productos.id_producto"), nullable=False, index=True
    )
    score_relevancia: Mapped[Decimal] = mapped_column(Numeric(5, 4), nullable=False)
    motivo: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    generado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    producto: Mapped["ProductoORM"] = relationship("ProductoORM")


class PromocionORM(Base):
    """Mapeo de la tabla `fashionstore.promociones`."""

    __tablename__ = "promociones"
    __table_args__ = {"schema": "fashionstore"}

    id_promocion: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    nombre: Mapped[str] = mapped_column(String(150), nullable=False)
    descripcion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    porcentaje_descuento: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    # En PostgreSQL ambas columnas son TIMESTAMPTZ, no DATE. Declararlas como `Date` hacía que
    # SQLAlchemy devolviese `datetime` donde el código esperaba `date`, y cualquier comparación
    # en Python fallaba con "can't compare datetime.datetime to datetime.date".
    fecha_inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fecha_fin: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    # La columna real en PostgreSQL es `estado_activo` (la migración 0001 declara `activa`).
    activa: Mapped[bool] = mapped_column("estado_activo", Boolean, nullable=False, default=True)

    # --- Soporte de cupones y bonos atelier (CU15) ---
    # Estas columnas ya existían en PostgreSQL pero no estaban mapeadas, de modo que el modelo
    # sólo podía expresar promociones por porcentaje ligadas a producto. Mapearlas no requiere
    # ningún cambio de esquema.
    codigo_cupon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    tipo_descuento: Mapped[str] = mapped_column(
        String(20), nullable=False, default="porcentaje"
    )
    valor_descuento: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00")
    )
    tope_descuento: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    limite_usos: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    usos_actuales: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alcance: Mapped[str] = mapped_column(String(20), nullable=False, default="global")
    id_categoria: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    id_producto: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)


class PromocionProductoORM(Base):
    """Mapeo de la tabla de asociación `fashionstore.promocion_producto`."""

    __tablename__ = "promocion_producto"
    __table_args__ = {"schema": "fashionstore"}

    id_promocion: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.promociones.id_promocion", ondelete="CASCADE"), primary_key=True
    )
    id_producto: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.productos.id_producto", ondelete="CASCADE"), primary_key=True
    )

