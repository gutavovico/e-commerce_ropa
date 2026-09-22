"""Esquemas Pydantic para CU12: Reservar Varias Prendas (Cita de Prueba en Boutique)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, Field


class ReservaItemIn(BaseModel):
    """Ítem o variante a incluir en la reserva presencial."""
    id_variante: int = Field(..., description="ID de la variante de prenda")
    cantidad: int = Field(default=1, ge=1, le=5, description="Cantidad de unidades a apartar")


class ReservaCrearIn(BaseModel):
    """Payload para solicitar una cita de prueba presencial en boutique física."""
    id_sucursal: int = Field(..., description="ID de la boutique elegida")
    fecha_hora_atencion: datetime = Field(..., description="Fecha y hora de la cita programada")
    canal_origen: str = Field(default="web", description="'web' o 'movil'")
    observacion: Optional[str] = Field(None, description="Notas de ajuste o preferencias para el equipo de sastrería")
    items: List[ReservaItemIn] = Field(..., min_length=1, description="Prendas seleccionadas para la cita")


class ReservaItemOut(BaseModel):
    """Detalle de una prenda reservada en la cita."""
    id_reserva_detalle: Optional[int] = Field(None, description="ID autoincremental de la línea")
    id_variante: int
    sku: str
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    cantidad: int
    precio_unitario: Decimal


class ReservaCreadaOut(BaseModel):
    """Confirmación formal de la reserva de cita presencial en boutique."""
    id_reserva: int
    codigo_reserva: str
    id_sucursal: int
    nombre_sucursal: str
    direccion_sucursal: str
    fecha_hora_atencion: datetime
    estado: str = "pendiente"
    canal_origen: str
    items: List[ReservaItemOut]
    mensaje_confirmacion: str = "Cita de prueba presencial confirmada con nuestro equipo de sastrería."
    cortesias_incluidas: List[str] = Field(
        default_factory=lambda: [
            "Champán de cortesía o infusión artesanal de bienvenida",
            "Asesoramiento privado de estilista sénior de atelier",
            "Ajustes menores de costura y entallado sin coste adicional"
        ]
    )
    creado_en: datetime
