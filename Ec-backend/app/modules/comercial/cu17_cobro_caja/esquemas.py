"""Esquemas Pydantic v2 para CU17: Registrar cobro en caja."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field


class DetallePrendaCajaOut(BaseModel):
    """Linea de detalle de prenda incluida en una orden de venta."""

    model_config = ConfigDict(from_attributes=True)

    id_venta_detalle: int
    id_variante: int
    sku: str
    nombre_producto: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal


class OrdenPendienteOut(BaseModel):
    """Ficha completa de orden pendiente para visualizacion en mostrador de caja."""

    model_config = ConfigDict(from_attributes=True)

    id_venta: int
    numero_comprobante: str
    fecha_venta: datetime
    id_sucursal: int
    nombre_sucursal: str
    id_cliente: Optional[int] = None
    cliente_nombre: str
    cliente_documento: Optional[str] = None
    cliente_telefono: Optional[str] = None
    tipo_venta: str
    estado: str
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    detalles: List[DetallePrendaCajaOut] = Field(default_factory=list)


class ListadoOrdenesPendientesOut(BaseModel):
    """Respuesta paginada del buscador de ordenes pendientes."""

    total: int
    items: List[OrdenPendienteOut]


MetodoPagoCajaTipo = Literal[
    "efectivo",
    "tarjeta_pos",
    "qr_estatico",
    "tarjeta_debito",
    "tarjeta_credito",
    "qr",
]


class CobroCajaIn(BaseModel):
    """Payload de entrada para asentar el cobro de una orden en mostrador."""

    id_venta: int = Field(..., description="Identificador de la orden a liquidar")
    monto_recibido: Decimal = Field(..., gt=0, description="Importe entregado por el cliente en BOB")
    metodo_pago: MetodoPagoCajaTipo = Field(..., description="Metodo de pago utilizado en terminal fisica")
    observaciones: Optional[str] = Field(None, max_length=255, description="Anotaciones u observaciones de caja")


class CobroCajaOut(BaseModel):
    """Comprobante y confirmacion de liquidacion emitida por la caja."""

    id_pago: int
    id_venta: int
    numero_comprobante: str
    monto_total: Decimal
    monto_recibido: Decimal
    cambio_devuelto: Decimal
    metodo_pago: str
    estado_venta: str
    estado_pago: str
    cajero_id: Optional[int]
    cajero_nombre: str
    fecha_cobro: datetime
    observaciones: Optional[str] = None
