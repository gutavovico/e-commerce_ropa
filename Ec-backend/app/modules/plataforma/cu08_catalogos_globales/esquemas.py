"""Esquemas Pydantic v2 para P2-CU08: Gestionar catálogos globales (ciudades, tallas y colores).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` §3.2 (CU08).
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class CambiarEstadoCatalogoIn(BaseModel):
    """Solicitud para activar o desactivar un elemento del catálogo global (CU08 A2)."""

    activo: bool


class EliminacionCatalogoOut(BaseModel):
    """Confirmación de eliminación física de un elemento sin referencias."""

    eliminado: bool = True
    mensaje: str


# --- Ciudades ---


class CiudadGlobalIn(BaseModel):
    """Datos de entrada para crear o editar una ciudad global."""

    nombre: str = Field(..., min_length=2, max_length=100)
    pais: str = Field(default="Bolivia", min_length=2, max_length=100)


class CiudadGlobalOut(BaseModel):
    """Representación de una ciudad del catálogo global (RN21)."""

    model_config = ConfigDict(from_attributes=True)

    id_ciudad: int
    nombre: str
    pais: str
    activo: bool
    creado_en: datetime
    sucursales_asociadas: int = 0


# --- Tallas ---


class TallaGlobalIn(BaseModel):
    """Datos de entrada para crear o editar una talla global."""

    codigo: str = Field(..., min_length=1, max_length=10)
    orden: int = Field(default=0, ge=0, le=32767)


class TallaGlobalOut(BaseModel):
    """Representación de una talla del catálogo global (RN21)."""

    model_config = ConfigDict(from_attributes=True)

    id_talla: int
    codigo: str
    orden: int
    activo: bool
    variantes_asociadas: int = 0


# --- Colores ---


class ColorGlobalIn(BaseModel):
    """Datos de entrada para crear o editar un color global."""

    nombre: str = Field(..., min_length=2, max_length=50)
    codigo_hex: str = Field(
        ...,
        pattern=r"^#[0-9A-Fa-f]{6}$",
        description="Código hexadecimal de color en formato #RRGGBB",
    )

    @field_validator("codigo_hex", mode="before")
    @classmethod
    def normalizar_hex(cls, v: str) -> str:
        if isinstance(v, str):
            return v.strip().upper()
        return v


class ColorGlobalOut(BaseModel):
    """Representación de un color del catálogo global (RN21)."""

    model_config = ConfigDict(from_attributes=True)

    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None
    activo: bool
    variantes_asociadas: int = 0

