"""Modelos ORM de SQLAlchemy 2.0 para el paquete de Compras y Pagos (CU11 y CU15).

Mapea las tablas del esquema `fashionstore`:
- carritos
- carrito_detalle

`VentaORM` y `VentaDetalleORM` NO se declaran aquí: ya existían en
`modules/catalogo/modelos.py`, donde las introdujo CU18 para el cálculo de afinidad. Declararlas
de nuevo produciría un `InvalidRequestError` por tabla duplicada en el mismo `MetaData`. Se
reexportan al final del módulo para que el paquete disponga de ellas con un único origen de
verdad; las columnas de entrega y de expedición por línea que necesita CU15 se añadieron sobre
aquellas definiciones.

Los nombres de columna se verificaron por introspección directa contra PostgreSQL el 2026-09-22.
La migración `alembic/versions/0001_base_ddl.py` NO describe el esquema desplegado y no debe
usarse como referencia (ver `CHANGELOG.md`, defecto 34).
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from core.database import Base
from modules.catalogo.modelos import (
    SucursalORM,
    VarianteProductoORM,
    VentaDetalleORM,
    VentaORM,
)

# Enums de pago existentes en PostgreSQL Neon (verificados por introspección el 2026-09-22).
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

# Modalidades de entrega admitidas, alineadas con el CHECK `ck_ventas_tipo_entrega`
# introducido por la migración 0009.
TIPO_ENTREGA_DOMICILIO = "domicilio"
TIPO_ENTREGA_RECOGIDA = "recogida_boutique"
TIPOS_ENTREGA_VALIDOS = (TIPO_ENTREGA_DOMICILIO, TIPO_ENTREGA_RECOGIDA)

# Ventana de garantía de existencias una vez tramitado el pedido (§1.4 de la especificación).
MINUTOS_RETENCION_VENTA = 25


class CarritoORM(Base):
    """Mapeo de la tabla `fashionstore.carritos`.

    Existe como máximo un carrito activo por cliente; el servicio lo crea de forma perezosa la
    primera vez que el cliente añade una prenda o consulta su bolsa.
    """

    __tablename__ = "carritos"
    __table_args__ = {"schema": "fashionstore"}

    id_carrito: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_cliente: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.clientes.id_cliente"),
        nullable=False,
        index=True,
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    actualizado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    detalles: Mapped[List["CarritoDetalleORM"]] = relationship(
        "CarritoDetalleORM",
        back_populates="carrito",
        cascade="all, delete-orphan",
    )


class CarritoDetalleORM(Base):
    """Mapeo de la tabla `fashionstore.carrito_detalle`.

    Cada línea guarda su propia `id_sucursal`: la bolsa es multi-boutique por diseño, tal y como
    muestran las maquetas de la pantalla de Bolsa de Compra.
    """

    __tablename__ = "carrito_detalle"
    __table_args__ = (
        # Una variante aparece una sola vez por carrito y sucursal; añadir de nuevo la misma
        # combinación consolida cantidades en lugar de duplicar la línea.
        UniqueConstraint(
            "id_carrito",
            "id_variante",
            "id_sucursal",
            name="uq_carrito_detalle_carrito_variante_sucursal",
        ),
        {"schema": "fashionstore"},
    )

    id_carrito_detalle: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True
    )
    id_carrito: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.carritos.id_carrito", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    id_variante: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.variantes_producto.id_variante"),
        nullable=False,
    )
    id_sucursal: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("fashionstore.sucursales.id_sucursal"),
        nullable=False,
    )
    cantidad: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    agregado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    carrito: Mapped["CarritoORM"] = relationship("CarritoORM", back_populates="detalles")
    variante: Mapped["VarianteProductoORM"] = relationship("VarianteProductoORM")
    sucursal: Mapped["SucursalORM"] = relationship("SucursalORM")


class PagoORM(Base):
    """Mapeo de la tabla `fashionstore.pagos` (CU16).

    `id_venta` NO es único a propósito: la tabla acumula todos los intentos de cobro de una
    misma orden, de modo que un rechazo seguido de un reintento exitoso deja ambos registros y
    el historial financiero queda completo.
    """

    __tablename__ = "pagos"
    __table_args__ = {"schema": "fashionstore"}

    id_pago: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_venta: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.ventas.id_venta", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    metodo_pago: Mapped[str] = mapped_column(metodo_pago_enum, nullable=False)
    monto: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    estado: Mapped[str] = mapped_column(
        estado_pago_enum, nullable=False, default="pendiente", index=True
    )
    referencia_pasarela: Mapped[Optional[str]] = mapped_column(String(150), nullable=True)

    # `jsonb` nativo: se escribe como diccionario, no como cadena serializada a mano. Guarda la
    # respuesta cruda de la pasarela para auditoría financiera. Nunca contiene PAN ni CVV.
    payload_respuesta: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    confirmado_en: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    venta: Mapped["VentaORM"] = relationship("VentaORM")


__all__ = [
    "CarritoORM",
    "CarritoDetalleORM",
    "PagoORM",
    "VentaORM",
    "VentaDetalleORM",
    "TIPO_ENTREGA_DOMICILIO",
    "TIPO_ENTREGA_RECOGIDA",
    "TIPOS_ENTREGA_VALIDOS",
    "MINUTOS_RETENCION_VENTA",
]
