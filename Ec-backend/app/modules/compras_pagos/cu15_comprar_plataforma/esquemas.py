"""Esquemas Pydantic para CU15: Comprar desde la plataforma (tramitación del pedido)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class CheckoutIn(BaseModel):
    """Payload para transformar la bolsa en una venta formal en estado `pendiente`.

    Deliberadamente NO admite importes: el servidor recalcula siempre subtotal, descuento y total
    a partir del catálogo y las promociones vigentes. Cualquier cifra enviada por el cliente se
    ignora, según la regla «el servidor es la fuente de verdad» de la constitución de backend.
    """

    tipo_venta: Literal["digital_web", "digital_movil"] = Field(
        ..., description="Canal desde el que se tramita el pedido"
    )
    tipo_entrega: Literal["domicilio", "recogida_boutique"] = Field(
        default="domicilio", description="Modalidad de entrega elegida"
    )
    direccion_envio: Optional[str] = Field(
        None,
        max_length=500,
        description="Obligatoria cuando tipo_entrega = 'domicilio'",
    )
    id_sucursal_retiro: Optional[int] = Field(
        None, description="Obligatoria cuando tipo_entrega = 'recogida_boutique'"
    )
    codigo_cupon: Optional[str] = Field(
        None, max_length=50, description="Código de invitación o bono atelier (opcional)"
    )


class VentaItemOut(BaseModel):
    """Línea de la orden con el precio ya congelado."""

    id_venta_detalle: Optional[int] = None
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    imagen_url: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal
    subtotal_linea: Decimal
    id_sucursal: Optional[int] = None
    nombre_sucursal: Optional[str] = None


class VentaCreadaOut(BaseModel):
    """Confirmación de la orden registrada, lista para la pasarela de pago (CU16)."""

    id_venta: int
    numero_comprobante: str
    estado: str = "pendiente"
    tipo_venta: str
    tipo_entrega: str
    direccion_envio: Optional[str] = None
    id_sucursal_retiro: Optional[int] = None
    nombre_sucursal_retiro: Optional[str] = None

    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    iva_incluido: Decimal = Field(
        ..., description="IVA contenido en el total (21%). Informativo: no se persiste"
    )
    moneda: str = "EUR"

    cupon_aplicado: Optional[str] = None
    nombre_promocion: Optional[str] = None

    items: List[VentaItemOut] = Field(default_factory=list)
    total_prendas: int

    fecha_venta: datetime
    expira_en: datetime = Field(
        ...,
        description=(
            "Vencimiento de la retención de existencias (fecha_venta + 25 min). Pasado ese "
            "instante la orden puede liberarse y el stock vuelve a estar disponible."
        ),
    )
    mensaje_confirmacion: str = (
        "Tu orden ha sido registrada. Dispones de 25 minutos para completar el pago."
    )


class RetencionLiberadaOut(BaseModel):
    """Resultado de liberar la retención de existencias de una venta."""

    id_venta: int
    numero_comprobante: str
    estado: str
    unidades_liberadas: int
    mensaje: str
