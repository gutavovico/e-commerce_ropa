"""Modelos ORM de SQLAlchemy 2.0 para CU28: Consultar ventas y reservas.

Mapea con precision las tablas del esquema `fashionstore`:
- fashionstore.ventas
- fashionstore.venta_detalle
- fashionstore.pagos
- fashionstore.reservas
- fashionstore.reserva_detalle
- fashionstore.empleados
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from modules.catalogo.modelos import VarianteProductoORM

from sqlalchemy import (
    BigInteger,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM

# Enums existentes en la base de datos PostgreSQL
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

estado_pago_enum = PG_ENUM(
    "pendiente",
    "autorizado",
    "confirmado",
    "rechazado",
    "reembolsado",
    name="estado_pago",
    schema="fashionstore",
    create_type=False,
)

metodo_pago_enum = PG_ENUM(
    "efectivo",
    "tarjeta_debito",
    "tarjeta_credito",
    "pasarela_digital",
    "qr",
    "transferencia",
    name="metodo_pago",
    schema="fashionstore",
    create_type=False,
)

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


class EmpleadoORM(Base):
    """Mapeo de la tabla `fashionstore.empleados`."""

    __tablename__ = "empleados"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_empleado: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario", ondelete="CASCADE"),
        primary_key=True,
    )
    codigo_empleado: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    fecha_contratacion: Mapped[date] = mapped_column(Date, nullable=False, default=date.today)
    cargo: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    usuario: Mapped[Optional["UsuarioORM"]] = relationship(
        "UsuarioORM",
        lazy="selectin",
    )


class VentaORM(Base):
    """Mapeo de la tabla `fashionstore.ventas`."""

    __tablename__ = "ventas"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_venta: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    numero_comprobante: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, index=True)
    id_cliente: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente"), nullable=True, index=True
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=False, index=True
    )
    id_cajero: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.empleados.id_empleado"), nullable=True
    )
    id_reserva: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.reservas.id_reserva"), nullable=True
    )
    tipo_venta: Mapped[str] = mapped_column(tipo_venta_enum, nullable=False, index=True)
    estado: Mapped[str] = mapped_column(estado_venta_enum, nullable=False, default="pendiente", index=True)
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    descuento: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, default=Decimal("0.00"))
    fecha_venta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )
    tipo_entrega: Mapped[str] = mapped_column(String(20), nullable=False, default="domicilio")
    id_sucursal_retiro: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=True
    )
    direccion_envio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    id_promocion: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.promociones.id_promocion"), nullable=True
    )

    # Relaciones
    cliente: Mapped[Optional["ClienteORM"]] = relationship(
        "ClienteORM",
        foreign_keys=[id_cliente],
        lazy="selectin",
    )
    sucursal: Mapped["SucursalORM"] = relationship(
        "SucursalORM",
        foreign_keys=[id_sucursal],
        lazy="selectin",
    )
    sucursal_retiro: Mapped[Optional["SucursalORM"]] = relationship(
        "SucursalORM",
        foreign_keys=[id_sucursal_retiro],
        lazy="selectin",
    )
    promocion: Mapped[Optional["PromocionORM"]] = relationship(
        "PromocionORM",
        foreign_keys=[id_promocion],
        lazy="selectin",
    )
    cajero: Mapped[Optional["EmpleadoORM"]] = relationship(
        "EmpleadoORM",
        foreign_keys=[id_cajero],
        lazy="selectin",
    )
    reserva: Mapped[Optional["ReservaORM"]] = relationship(
        "ReservaORM",
        foreign_keys=[id_reserva],
        lazy="selectin",
    )
    detalles: Mapped[List["VentaDetalleORM"]] = relationship(
        "VentaDetalleORM",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pagos: Mapped[List["PagoORM"]] = relationship(
        "PagoORM",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class VentaDetalleORM(Base):
    """Mapeo de la tabla `fashionstore.venta_detalle`."""

    __tablename__ = "venta_detalle"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_venta_detalle: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_venta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.ventas.id_venta", ondelete="CASCADE"), nullable=False, index=True
    )
    id_variante: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.variantes_producto.id_variante"), nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False)
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    subtotal_linea: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    id_sucursal: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=True, index=True
    )

    venta: Mapped["VentaORM"] = relationship("VentaORM", back_populates="detalles")
    variante: Mapped["VarianteProductoORM"] = relationship(
        "VarianteProductoORM",
        foreign_keys=[id_variante],
        lazy="selectin",
    )
    sucursal: Mapped[Optional["SucursalORM"]] = relationship(
        "SucursalORM",
        foreign_keys=[id_sucursal],
        lazy="selectin",
    )


class PagoORM(Base):
    """Mapeo de la tabla `fashionstore.pagos` (CU16 y CU28).

    `id_venta` NO es único a propósito: la tabla acumula todos los intentos de cobro de una
    misma orden, de modo que un rechazo seguido de un reintento exitoso deja ambos registros y
    el historial financiero queda completo.
    """

    __tablename__ = "pagos"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_pago: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_venta: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.ventas.id_venta", ondelete="CASCADE"), nullable=False, index=True
    )
    metodo_pago: Mapped[str] = mapped_column(metodo_pago_enum, nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(estado_pago_enum, nullable=False, default="pendiente", index=True)
    referencia_pasarela: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)
    payload_respuesta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmado_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    venta: Mapped["VentaORM"] = relationship("VentaORM", back_populates="pagos")


class ReservaORM(Base):
    """Mapeo de la tabla `fashionstore.reservas`."""

    __tablename__ = "reservas"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_reserva: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.clientes.id_cliente"), nullable=False, index=True
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer, ForeignKey("fashionstore.sucursales.id_sucursal"), nullable=False, index=True
    )
    fecha_hora_atencion: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    estado: Mapped[str] = mapped_column(estado_reserva_enum, nullable=False, default="pendiente", index=True)
    canal_origen: Mapped[str] = mapped_column(canal_origen_enum, nullable=False)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    atendido_por: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("fashionstore.empleados.id_empleado"), nullable=True
    )
    atendido_en: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    observacion: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cliente: Mapped["ClienteORM"] = relationship(
        "ClienteORM",
        foreign_keys=[id_cliente],
        lazy="selectin",
    )
    sucursal: Mapped["SucursalORM"] = relationship(
        "SucursalORM",
        foreign_keys=[id_sucursal],
        lazy="selectin",
    )
    empleado_atencion: Mapped[Optional["EmpleadoORM"]] = relationship(
        "EmpleadoORM",
        foreign_keys=[atendido_por],
        lazy="selectin",
    )
    detalles: Mapped[List["ReservaDetalleORM"]] = relationship(
        "ReservaDetalleORM",
        back_populates="reserva",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class ReservaDetalleORM(Base):
    """Mapeo de la tabla `fashionstore.reserva_detalle`."""

    __tablename__ = "reserva_detalle"
    __table_args__ = {"schema": "fashionstore", "extend_existing": True}

    id_reserva_detalle: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_reserva: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.reservas.id_reserva", ondelete="CASCADE"), nullable=False, index=True
    )
    id_variante: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("fashionstore.variantes_producto.id_variante"), nullable=False, index=True
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    reserva: Mapped["ReservaORM"] = relationship("ReservaORM", back_populates="detalles")
    variante: Mapped["VarianteProductoORM"] = relationship(
        "VarianteProductoORM",
        foreign_keys=[id_variante],
        lazy="selectin",
    )
