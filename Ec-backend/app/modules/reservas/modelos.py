"""Modelos ORM de SQLAlchemy 2.0 para el paquete de Reservas y Movimientos de Inventario.

Mapea las tablas del esquema `fashionstore`:
- reservas
- reserva_detalle
- movimientos_inventario

Actúa como módulo puente reexportando las entidades desde sus casos de uso.
"""

from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM

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

# Reexportación de modelos ORM desde sus módulos definitivos
from modules.comercial.cu28_ventas_reservas.modelos import ReservaORM, ReservaDetalleORM
from modules.gestion_operativa.cu24_inventario_stock.modelos import MovimientoInventarioORM

__all__ = [
    "estado_reserva_enum",
    "canal_origen_enum",
    "tipo_movimiento_inv_enum",
    "ReservaORM",
    "ReservaDetalleORM",
    "MovimientoInventarioORM",
]