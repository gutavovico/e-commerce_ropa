"""Esquemas Pydantic del punto de venta presencial (CU31-CU32).

Todo importe es `Decimal` (FastAPI lo serializa como cadena JSON). Los importes que envíe el
cliente web se ignoran: el servidor los recalcula siempre.
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

#: Métodos de cobro admitidos en caja (D6). `pasarela_digital` no se ofrece en mostrador.
MetodoPagoCaja = Literal["efectivo", "tarjeta_debito", "tarjeta_credito", "qr", "transferencia"]


# ---------------------------------------------------------------------------
# Entradas
# ---------------------------------------------------------------------------


class LineaPosIn(BaseModel):
    id_variante: int = Field(..., gt=0)
    cantidad: int = Field(..., gt=0, le=99)


class VentaPosIn(BaseModel):
    """Cuerpo de `POST /pos/ventas` y `POST /pos/ventas/previsualizar`."""

    #: Solo el administrador la envía; cajero y encargado operan en la suya (D9).
    id_sucursal: Optional[int] = Field(None, gt=0)
    id_cliente: Optional[int] = Field(None, gt=0)
    #: Id numérico o código `RES-AAAA-NNNN`.
    reserva: Optional[str] = Field(None, max_length=30)
    codigo_cupon: Optional[str] = Field(None, max_length=50)
    lineas: List[LineaPosIn] = Field(default_factory=list)
    #: Variantes de la reserva que el cliente no se lleva (se liberan al cobrar).
    lineas_reserva_excluidas: List[int] = Field(default_factory=list)


class CobroPosIn(BaseModel):
    """Cuerpo de `POST /pos/ventas/{id}/cobrar`."""

    metodo_pago: MetodoPagoCaja
    #: Obligatorio en efectivo: lo entregado por el cliente.
    monto_recibido: Optional[Decimal] = Field(None, ge=Decimal("0"))
    #: Autorización del datáfono, id de QR o de transferencia: obligatoria salvo en efectivo.
    referencia: Optional[str] = Field(None, max_length=150)
    #: `False` registra el rechazo del datáfono (la venta sigue pendiente).
    aprobado: bool = True

    @field_validator("referencia")
    @classmethod
    def _limpiar(cls, valor: Optional[str]) -> Optional[str]:
        return valor.strip() or None if valor else None


class AnulacionPosIn(BaseModel):
    motivo: str = Field(..., min_length=3, max_length=250)


# ---------------------------------------------------------------------------
# Salidas
# ---------------------------------------------------------------------------


class VariantePosOut(BaseModel):
    id_variante: int
    sku: str
    id_producto: int
    nombre_producto: str
    categoria_nombre: Optional[str] = None
    talla_codigo: str
    color_nombre: str
    imagen_url: Optional[str] = None
    precio_lista: Decimal
    precio_final: Decimal
    disponible_en_sucursal: int


class ClientePosOut(BaseModel):
    id_cliente: int
    nombres: str
    apellidos: str
    email: str


class LineaReservaPosOut(BaseModel):
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    cantidad: int


class ReservaPosOut(BaseModel):
    id_reserva: int
    codigo: str
    estado: str
    fecha_hora_atencion: datetime
    cliente: Optional[ClientePosOut] = None
    lineas: List[LineaReservaPosOut]


class LineaVentaPosOut(BaseModel):
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    imagen_url: Optional[str] = None
    cantidad: int
    precio_lista: Decimal
    precio_unitario: Decimal
    subtotal_linea: Decimal
    motivo_descuento: Optional[str] = None
    #: `reserva` si procede de la reserva cargada; `caja` si la añadió el cajero.
    origen: Literal["reserva", "caja"]


class PagoPosOut(BaseModel):
    id_pago: int
    metodo_pago: str
    monto: Decimal
    estado: str
    referencia: Optional[str] = None
    monto_recibido: Optional[Decimal] = None
    cambio: Optional[Decimal] = None
    creado_en: datetime
    confirmado_en: Optional[datetime] = None


class TotalesPosOut(BaseModel):
    subtotal: Decimal
    descuento: Decimal
    total: Decimal
    iva_incluido: Decimal
    cupon_aplicado: Optional[str] = None


class PrevisualizacionPosOut(TotalesPosOut):
    lineas: List[LineaVentaPosOut]
    lineas_reserva_excluidas: List[LineaReservaPosOut] = Field(default_factory=list)


class VentaPosOut(TotalesPosOut):
    id_venta: int
    numero_comprobante: str
    estado: str
    fecha_venta: datetime
    id_sucursal: int
    nombre_sucursal: str
    direccion_sucursal: Optional[str] = None
    cajero_nombre: Optional[str] = None
    cliente: Optional[ClientePosOut] = None
    reserva_codigo: Optional[str] = None
    lineas: List[LineaVentaPosOut]
    lineas_reserva_excluidas: List[LineaReservaPosOut] = Field(default_factory=list)
    pagos: List[PagoPosOut] = Field(default_factory=list)


class CuponPosOut(BaseModel):
    """Cupón vigente y con usos disponibles, para elegirlo en caja. El descuento lo calcula
    siempre `previsualizar`; estos campos solo describen el cupón."""

    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    tipo_descuento: str
    valor_descuento: Decimal
    alcance: str
    fecha_fin: datetime
    usos_restantes: Optional[int] = None


class PedidoWebEfectivoOut(BaseModel):
    """Pedido web con pago en efectivo pendiente de cobro en esta boutique (D10, endpoints de CU16)."""

    id_pago: int
    id_venta: int
    numero_comprobante: str
    cliente_nombre: Optional[str] = None
    total: Decimal
    creado_en: datetime
