"""Esquemas Pydantic para CU11: Gestionar carrito de compras (Bolsa de Compra)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ItemAgregarIn(BaseModel):
    """Payload para añadir una prenda a la bolsa."""

    id_variante: int = Field(..., description="Variante (talla + color) de la prenda")
    cantidad: int = Field(default=1, ge=1, le=10, description="Unidades a añadir")
    id_sucursal: Optional[int] = Field(
        None,
        description=(
            "Boutique de expedición. Si se omite, el servicio elige la que tenga mayor "
            "disponibilidad para esa variante en la temporada vigente."
        ),
    )


class ItemCantidadIn(BaseModel):
    """Payload para fijar la cantidad de una línea.

    La cantidad es absoluta, no un incremento: hace la operación idempotente y segura ante la
    doble pulsación de `+`. Para eliminar una línea se usa DELETE, no `cantidad: 0`.
    """

    cantidad: int = Field(..., ge=1, le=10, description="Cantidad final deseada para la línea")


class CarritoItemOut(BaseModel):
    """Una prenda de la bolsa, con su precio, su boutique de expedición y su stock vigente."""

    id_carrito_detalle: int
    id_variante: int
    id_producto: int
    nombre_producto: str
    linea_confeccion: Optional[str] = None
    sku: str
    talla_codigo: str
    color_nombre: str
    color_hex: Optional[str] = None
    imagen_url: Optional[str] = None

    precio_lista: Decimal = Field(..., description="Precio sin descuentos, para mostrar tachado")
    precio_unitario: Decimal = Field(..., description="Precio efectivo tras promoción vigente")
    descuento_linea: Decimal = Field(
        default=Decimal("0.00"), description="Ahorro total de la línea (precio_lista - efectivo)"
    )
    motivo_descuento: Optional[str] = Field(
        None, description="Nombre de la promoción que origina el descuento"
    )

    cantidad: int
    id_sucursal: int
    nombre_sucursal: str
    stock_disponible: int = Field(..., description="Existencias actuales en esa boutique")
    cantidad_maxima: int = Field(
        ..., description="Tope para el botón '+' sin necesidad de una llamada extra"
    )
    subtotal_linea: Decimal


class CarritoResumenOut(BaseModel):
    """Resumen financiero de la bolsa.

    `subtotal` agrega precios de lista y `descuento` el ahorro aplicado, de modo que siempre se
    cumple `total = subtotal - descuento`, en coherencia con las columnas de `ventas`.
    """

    total_prendas: int = Field(..., description="Suma de cantidades, no de líneas")
    total_lineas: int
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    iva_incluido: Decimal = Field(
        ..., description="IVA contenido en el total (21%). Informativo: no se persiste"
    )
    moneda: str = "EUR"


class SucursalExpedicionOut(BaseModel):
    """Boutique desde la que se expide parte de la bolsa."""

    id_sucursal: int
    nombre: str
    total_lineas: int


class CarritoOut(BaseModel):
    """Contrato consolidado de la Bolsa de Compra."""

    id_carrito: int
    items: List[CarritoItemOut] = Field(default_factory=list)
    resumen: CarritoResumenOut
    expira_en: Optional[datetime] = Field(
        None,
        description=(
            "Fin de la ventana informativa de la bolsa (línea más antigua + 25 min). "
            "NO retiene existencias: la garantía firme se obtiene al tramitar el pedido."
        ),
    )
    sucursales_expedicion: List[SucursalExpedicionOut] = Field(default_factory=list)
