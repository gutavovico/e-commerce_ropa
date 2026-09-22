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

