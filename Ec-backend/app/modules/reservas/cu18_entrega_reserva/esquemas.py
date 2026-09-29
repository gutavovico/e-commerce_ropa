"""Esquemas Pydantic v2 para CU18: Atender entrega de reserva en boutique."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class PrendaReservaCajaOut(BaseModel):
    """Detalle de una prenda apartada para la cita en boutique."""

    model_config = ConfigDict(from_attributes=True)

    id_reserva_detalle: int
    id_variante: int
    sku: str
    nombre_producto: str
    talla: str
    color: str
    cantidad: int
    precio_unitario: Decimal
    ubicacion_percha: Optional[str] = None


class ReservaPendienteCajaOut(BaseModel):
    """Ficha de reserva para atencion en recepcion y mostrador de boutique."""

    model_config = ConfigDict(from_attributes=True)

    id_reserva: int
    codigo_reserva: str
    id_cliente: int
    cliente_nombre: str
    cliente_documento: Optional[str] = None
    cliente_telefono: Optional[str] = None
    id_sucursal: int
    nombre_sucursal: str
    fecha_hora_atencion: datetime
    estado: str
    canal_origen: str
    observacion: Optional[str] = None
    prendas: List[PrendaReservaCajaOut] = Field(default_factory=list)


class ListadoReservasPendientesOut(BaseModel):
    """Respuesta paginada del buscador de reservas en mostrador."""

    total: int
    items: List[ReservaPendienteCajaOut]


class ConfirmarEntregaIn(BaseModel):
    """Payload opcional al confirmar la entrega de prendas al cliente."""

    observaciones: Optional[str] = Field(None, max_length=255, description="Anotaciones de atencion")


class EntregaReservaOut(BaseModel):
    """Confirmacion de recepcion y entrega de cita de prueba."""

    id_reserva: int
    codigo_reserva: str
    estado: str
    atendido_por: Optional[int]
    atendido_en: Optional[datetime]
    mensaje: str


class NoAsistioReservaOut(BaseModel):
    """Resultado del cierre por inasistencia y liberacion de stock."""

    id_reserva: int
    codigo_reserva: str
    estado: str
    items_liberados: int
    mensaje: str


class ConvertirVentaReservaOut(BaseModel):
    """Resultado de la conversion de reserva a orden de compra presencial lista para caja."""

    id_venta: int
    numero_comprobante: str
    id_reserva: int
    total: Decimal
    estado_venta: str
    mensaje: str
