"""Esquemas Pydantic v2 para el caso de uso CU21: Gestionar Sucursales y Ciudades.

P2-CU04 B6: las ciudades son un catálogo global de solo lectura para el administrador; su
gestión es del super administrador (P2-CU08).
"""

from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class CiudadBase(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100, description="Nombre de la ciudad")
    pais: str = Field(default="Bolivia", min_length=2, max_length=100, description="Pais")


class CiudadOut(CiudadBase):
    id_ciudad: int
    creado_en: datetime
    total_sucursales: int = 0

    model_config = ConfigDict(from_attributes=True)


class SucursalBase(BaseModel):
    id_ciudad: int = Field(..., gt=0, description="Identificador de la ciudad asociada")
    nombre: str = Field(..., min_length=2, max_length=150, description="Nombre comercial de la boutique")
    direccion: str = Field(..., min_length=5, max_length=255, description="Direccion fisica de la sucursal")
    telefono: Optional[str] = Field(None, max_length=30, description="Telefono de contacto")
    horario_apertura: time = Field(default=time(9, 0), description="Hora de apertura")
    horario_cierre: time = Field(default=time(20, 0), description="Hora de cierre")


class SucursalCrearIn(SucursalBase):
    @field_validator("nombre", "direccion")
    @classmethod
    def limpiar_texto(cls, v: str) -> str:
        return v.strip()

    @model_validator(mode="after")
    def validar_horarios(self) -> "SucursalCrearIn":
        if self.horario_cierre <= self.horario_apertura:
            raise ValueError("El horario de cierre debe ser cronologicamente posterior al de apertura.")
        return self


class SucursalActualizarIn(BaseModel):
    id_ciudad: Optional[int] = Field(None, gt=0)
    nombre: Optional[str] = Field(None, min_length=2, max_length=150)
    direccion: Optional[str] = Field(None, min_length=5, max_length=255)
    telefono: Optional[str] = Field(None, max_length=30)
    horario_apertura: Optional[time] = None
    horario_cierre: Optional[time] = None

    @model_validator(mode="after")
    def validar_horarios_actualizacion(self) -> "SucursalActualizarIn":
        if self.horario_apertura is not None and self.horario_cierre is not None:
            if self.horario_cierre <= self.horario_apertura:
                raise ValueError("El horario de cierre debe ser cronologicamente posterior al de apertura.")
        return self


class SucursalEstadoIn(BaseModel):
    activa: bool = Field(..., description="Nuevo estado operativo de la sucursal")


class SucursalPublicaOut(BaseModel):
    id_sucursal: int
    id_ciudad: int
    ciudad_nombre: str
    nombre: str
    direccion: str
    telefono: Optional[str] = None
    horario_apertura: str
    horario_cierre: str

    model_config = ConfigDict(from_attributes=True)


class SucursalAdminOut(SucursalPublicaOut):
    activa: bool
    creado_en: datetime
    total_empleados: int = 0
    total_prendas_stock: int = 0
    reservas_activas_conteo: int = 0


class UsoPlanSucursalesOut(BaseModel):
    """P2-CU04 B7: sucursales activas frente al límite del plan (`limite=None`: sin límite)."""

    uso: int
    limite: Optional[int] = None
    plan: Optional[str] = None


class MiSucursalOut(BaseModel):
    """P2-CU03 B5: una sucursal en la que puede operar el empleado de la sesión."""

    id_sucursal: int
    nombre: str
    ciudad: str
    es_principal: bool = False
