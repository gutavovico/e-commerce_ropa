"""Esquemas Pydantic para CU13 (Consultar y cancelar reservas) y CU14 (Consultar estado de
reserva). Un único `ReservaOut` cubre ambos: ya expone el estado completo de la cita, así que CU14
no necesita un esquema de detalle aparte (decisión D5 de `spec.md`)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from pydantic import BaseModel, Field


class ReservaItemOut(BaseModel):
    """Prenda apartada en la cita, con lo necesario para mostrarla sin literales inventados."""

    id_variante: int
    nombre_producto: str
    talla_codigo: str
    color_nombre: str
    color_hex: Optional[str] = None
    imagen_url: Optional[str] = None
    cantidad: int
    precio_unitario: Decimal


class SucursalReservaOut(BaseModel):
    id_sucursal: int
    nombre: str
    direccion: str


class ReservaOut(BaseModel):
    """Cabecera y detalle de una reserva, tal como CU13/CU14 la muestran en el panel del cliente."""

    id_reserva: int
    codigo_reserva: str
    estado: str
    fecha_hora_atencion: datetime
    creado_en: datetime
    sucursal: SucursalReservaOut
    items: List[ReservaItemOut]
    total_prendas: int
    observacion: Optional[str] = None
    # Decidido en el servidor: el cliente no debe derivar por su cuenta si la reserva es
    # cancelable a partir del estado y la fecha, que es justo la regla que más adelante podría
    # cambiar (tolerancias, nuevos estados) sin que el cliente se entere.
    puede_cancelar: bool


class ResumenProximaReservaOut(BaseModel):
    id_reserva: int
    fecha_hora_atencion: datetime
    nombre_sucursal: str


class ResumenReservasOut(BaseModel):
    activas: int
    proxima: Optional[ResumenProximaReservaOut] = None


class MisReservasOut(BaseModel):
    """Respuesta de `GET /reservas/mias`: resumen para la tarjeta del Perfil + listas completas."""

    resumen: ResumenReservasOut
    proximas: List[ReservaOut]
    historial: List[ReservaOut]


class ReservaCancelarIn(BaseModel):
    """Payload de `POST /reservas/{id_reserva}/cancelar`. El motivo es obligatorio (CU13, paso 4)."""

    motivo: str = Field(..., min_length=3, max_length=250)
