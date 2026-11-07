"""Esquemas Pydantic para CU17: Consultar historial de compras."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ItemHistorialCompraOut(BaseModel):
    """Línea de detalle de un pedido dentro del historial de compras del cliente."""

    id_venta_detalle: int
    id_producto: int
    id_variante: int
    sku: str
    nombre_producto: str
    imagen_url: Optional[str] = None
    talla: str
    color: str
    color_hex: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal
    nombre_sucursal: Optional[str] = None


class PedidoHistorialOut(BaseModel):
    """Cabecera, estado de pago y desglose de un pedido del cliente."""

    id_venta: int
    numero_comprobante: str
    fecha_venta: datetime
    tipo_venta: str
    estado: str
    tipo_entrega: str
    nombre_sucursal: Optional[str] = None
    nombre_sucursal_retiro: Optional[str] = None
    direccion_envio: Optional[str] = None
    codigo_promocion: Optional[str] = None
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    metodo_pago: Optional[str] = None
    referencia_pasarela: Optional[str] = None
    items: List[ItemHistorialCompraOut] = Field(default_factory=list)


class HistorialComprasOut(BaseModel):
    """Respuesta consolidada del historial de compras del cliente autenticado."""

    total_pedidos: int
    pedidos_completados: int
    pedidos: List[PedidoHistorialOut] = Field(default_factory=list)

