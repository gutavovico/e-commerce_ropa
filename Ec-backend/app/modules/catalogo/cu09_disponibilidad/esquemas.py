"""Esquemas Pydantic para CU09: Consultar Disponibilidad por Sucursal."""

from datetime import time
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class DisponibilidadSucursalItemOut(BaseModel):
    """Disponibilidad de una variante o prenda en una boutique insignia física."""
    id_sucursal: int
    nombre: str = Field(..., description="Nombre de la boutique (ej. Flagship Serrano (Madrid))")
    ciudad: str = Field(..., description="Ciudad (Madrid, París, etc.)")
    direccion: str = Field(..., description="Dirección física")
    telefono: Optional[str] = None
    horario_apertura: str = "09:00"
    horario_cierre: str = "20:00"
    cantidad_disponible: int = 0
    cantidad_reservada: int = 0
    estado_stock: str = Field(..., description="disponible, ultimas_unidades, agotada")
    badge_stock: str = Field(..., description="2 UDS EN STOCK, 1 UD EN STOCK, CITA CON SASTRE JEFE, etc.")
    citas_disponibles_texto: str = Field(..., description="Citas de prueba disponibles hoy y mañana")
    permite_reserva_directa: bool = True

    @field_validator("horario_apertura", "horario_cierre", mode="before")
    @classmethod
    def normalizar_horario(cls, v):
        if isinstance(v, time):
            return v.strftime("%H:%M")
        if v is None:
            return "09:00"
        return str(v)[:5]



class DisponibilidadSucursalesOut(BaseModel):
    """Respuesta agregada de disponibilidad física en la red de boutiques de FashionStore."""
    id_producto: int
    id_variante: Optional[int] = None
    sku: Optional[str] = None
    sucursales: List[DisponibilidadSucursalItemOut] = Field(default_factory=list)
    total_disponible_global: int = 0
