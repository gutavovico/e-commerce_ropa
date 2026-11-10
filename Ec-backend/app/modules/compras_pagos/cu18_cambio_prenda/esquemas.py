"""Esquemas de P2-CU18 · Registrar cambio de prenda. Los importes son `Decimal` (cadena en JSON)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

MetodoPagoCambio = Literal["efectivo", "tarjeta_debito", "tarjeta_credito", "qr", "transferencia"]


class LineaDevueltaIn(BaseModel):
    id_venta_detalle: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=99)


class LineaNuevaIn(BaseModel):
    id_variante: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=99)


class CobroDiferenciaIn(BaseModel):
    """Solo cuando la diferencia es a favor de la tienda (el cliente paga)."""

    metodo_pago: MetodoPagoCambio
    monto_recibido: Optional[Decimal] = Field(None, ge=Decimal("0"))
    referencia: Optional[str] = Field(None, max_length=150)


class CambioIn(BaseModel):
    """La app solo envía qué se devuelve y qué se lleva; todo importe lo calcula el servidor."""

    id_venta: int = Field(..., gt=0)
    id_sucursal: Optional[int] = Field(None, gt=0)
    devueltas: List[LineaDevueltaIn] = Field(..., min_length=1)
    nuevas: List[LineaNuevaIn] = Field(..., min_length=1)
    cobro: Optional[CobroDiferenciaIn] = None


class LineaCambiableOut(BaseModel):
    id_venta_detalle: int
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    vendidas: int
    ya_cambiadas: int
    cambiables: int
    #: Lo pagado por unidad: precio de la línea con su parte del cupón (decisión F2).
    valor_unitario: Decimal


class VentaCambiableOut(BaseModel):
    id_venta: int
    numero_comprobante: str
    fecha_venta: datetime
    cliente_nombre: Optional[str] = None
    total: Decimal
    dias_transcurridos: int
    plazo_dias: int
    lineas: List[LineaCambiableOut]


class LineaCambioOut(BaseModel):
    tipo: Literal["devuelta", "nueva"]
    id_venta_detalle: Optional[int] = None
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    motivo_descuento: Optional[str] = None


class CambioPrevioOut(BaseModel):
    devueltas: List[LineaCambioOut]
    nuevas: List[LineaCambioOut]
    valor_devuelto: Decimal
    valor_nuevo: Decimal
    #: nuevo − devuelto: positivo, el cliente paga; negativo, se le devuelve en efectivo (F1).
    diferencia: Decimal


class CambioOut(CambioPrevioOut):
    id_cambio: int
    numero_comprobante: str
    creado_en: datetime
    id_venta: int
    comprobante_venta: str
    id_sucursal: int
    nombre_sucursal: str
    atendido_por: Optional[str] = None
    metodo_pago: Optional[str] = None
    monto_recibido: Optional[Decimal] = None
    vuelto: Optional[Decimal] = None
    referencia: Optional[str] = None
    #: Efectivo que se entrega al cliente cuando la diferencia es a su favor.
    devuelto_al_cliente: Decimal = Decimal("0.00")
