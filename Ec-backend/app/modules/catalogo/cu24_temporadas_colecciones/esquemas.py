"""Esquemas Pydantic v2 para CU24: Gestionar temporadas y colecciones."""

from datetime import date, datetime
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ============================================================================
# DTOs para Temporadas
# ============================================================================

class TemporadaCrearIn(BaseModel):
    """Payload para creacion de una nueva temporada comercial."""
    nombre: str = Field(..., min_length=3, max_length=100, description="Denominacion formal de la temporada")
    anio: int = Field(..., ge=2020, le=2100, description="Ano estacional de la campana")
    fecha_inicio: date = Field(..., description="Fecha de inicio formal de la temporada")
    fecha_fin: date = Field(..., description="Fecha de finalizacion formal de la temporada")

    @field_validator("nombre")
    @classmethod
    def sanitizar_nombre(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 3:
            raise ValueError("El nombre de la temporada debe contener al menos 3 caracteres validos.")
        return s

    @model_validator(mode="after")
    def validar_rango_fechas(self) -> "TemporadaCrearIn":
        if self.fecha_fin <= self.fecha_inicio:
            raise ValueError("La fecha de finalizacion debe ser estrictamente posterior a la fecha de inicio.")
        return self


class TemporadaActualizarIn(BaseModel):
    """Payload para actualizacion parcial de una temporada comercial."""
    nombre: Optional[str] = Field(None, min_length=3, max_length=100)
    anio: Optional[int] = Field(None, ge=2020, le=2100)
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None

    @field_validator("nombre")
    @classmethod
    def sanitizar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if len(s) < 3:
                raise ValueError("El nombre de la temporada debe contener al menos 3 caracteres validos.")
            return s
        return None

    @model_validator(mode="after")
    def validar_rango_fechas(self) -> "TemporadaActualizarIn":
        if self.fecha_inicio is not None and self.fecha_fin is not None:
            if self.fecha_fin <= self.fecha_inicio:
                raise ValueError("La fecha de finalizacion debe ser estrictamente posterior a la fecha de inicio.")
        return self


class TemporadaFiltrosIn(BaseModel):
    """Filtros multicriterio para consulta paginada de temporadas."""
    q: Optional[str] = Field(None, description="Busqueda por texto en nombre de temporada")
    anio: Optional[int] = Field(None, ge=2020, le=2100, description="Filtrar por ano especifico")
    estado_activo: Literal["todos", "activas", "inactivas"] = Field("todos", description="Filtro de estado")
    ordenar_por: Literal["anio_desc", "anio_asc", "nombre_asc", "nombre_desc", "fecha_desc"] = Field(
        "anio_desc", description="Criterio de ordenacion"
    )
    pagina: int = Field(1, ge=1, description="Numero de pagina")
    limite: int = Field(10, ge=1, le=100, description="Registros por pagina")


class TemporadaItemOut(BaseModel):
    """DTO de salida con los datos de una temporada comercial."""
    model_config = ConfigDict(from_attributes=True)

    id_temporada: int
    nombre: str
    anio: int
    fecha_inicio: date
    fecha_fin: date
    estado_activo: bool
    total_colecciones: int = 0
    creado_en: datetime
    actualizado_en: datetime


class ListaPaginadaTemporadasOut(BaseModel):
    """Respuesta paginada del listado de temporadas."""
    items: List[TemporadaItemOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int


# ============================================================================
# DTOs para Colecciones
# ============================================================================

class ColeccionCrearIn(BaseModel):
    """Payload para creacion de una coleccion capsula."""
    id_temporada: int = Field(..., gt=0, description="Identificador de la temporada matriz")
    nombre: str = Field(..., min_length=3, max_length=150, description="Nombre de la coleccion")
    descripcion: Optional[str] = Field(None, max_length=1000, description="Concepto creativo o descripcion")

    @field_validator("nombre")
    @classmethod
    def sanitizar_nombre(cls, v: str) -> str:
        s = v.strip()
        if len(s) < 3:
            raise ValueError("El nombre de la coleccion debe contener al menos 3 caracteres validos.")
        return s


class ColeccionActualizarIn(BaseModel):
    """Payload para actualizacion parcial de una coleccion capsula."""
    id_temporada: Optional[int] = Field(None, gt=0)
    nombre: Optional[str] = Field(None, min_length=3, max_length=150)
    descripcion: Optional[str] = Field(None, max_length=1000)

    @field_validator("nombre")
    @classmethod
    def sanitizar_nombre(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            s = v.strip()
            if len(s) < 3:
                raise ValueError("El nombre de la coleccion debe contener al menos 3 caracteres validos.")
            return s
        return None


class ColeccionFiltrosIn(BaseModel):
    """Filtros multicriterio para consulta paginada de colecciones."""
    q: Optional[str] = Field(None, description="Busqueda por nombre o descripcion de coleccion")
    id_temporada: Optional[int] = Field(None, gt=0, description="Filtrar por temporada matriz")
    estado_activo: Literal["todos", "activas", "inactivas"] = Field("todos", description="Filtro de estado")
    pagina: int = Field(1, ge=1, description="Numero de pagina")
    limite: int = Field(10, ge=1, le=100, description="Registros por pagina")


class ColeccionItemOut(BaseModel):
    """DTO de salida con los datos de una coleccion capsula."""
    model_config = ConfigDict(from_attributes=True)

    id_coleccion: int
    id_temporada: int
    temporada_nombre: str
    temporada_anio: int
    nombre: str
    descripcion: Optional[str]
    estado_activo: bool
    total_productos: int = 0
    creado_en: datetime
    actualizado_en: datetime


class ListaPaginadaColeccionesOut(BaseModel):
    """Respuesta paginada del listado de colecciones."""
    items: List[ColeccionItemOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int


# ============================================================================
# DTOs Compartidos
# ============================================================================

class EstadoConmutarIn(BaseModel):
    """Payload para conmutacion de estado activo/inactivo (baja logica)."""
    estado_activo: bool
