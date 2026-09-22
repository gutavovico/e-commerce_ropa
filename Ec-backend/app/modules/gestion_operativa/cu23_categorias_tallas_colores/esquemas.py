"""Esquemas Pydantic v2 para CU23: Gestionar Categorias, Tallas y Colores.

Define modelos de validacion estricta para entrada y salida de datos,
con normalizacion automatica de cadenas, codigos de talla y formato hexadecimal #HEX.
"""

import re
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator

REGEX_HEX_COLOR = r"^#[0-9A-Fa-f]{6}$"


# =============================================================================
# SCHEMAS: CATEGORIAS
# =============================================================================


class CategoriaBaseIn(BaseModel):
    """Esquema base de entrada para creacion de categoria."""

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Denominacion taxonomica de la categoria (2 a 100 caracteres)",
    )
    id_categoria_padre: Optional[int] = Field(
        None,
        gt=0,
        description="Identificador de la categoria padre si constituye una subcategoria",
    )

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        v_limpio = " ".join(v.strip().split())
        if len(v_limpio) < 2:
            raise ValueError("El nombre de la categoria debe contener al menos 2 caracteres.")
        return v_limpio


class CategoriaCrearIn(CategoriaBaseIn):
    """Esquema para creacion de nueva categoria."""

    pass


class CategoriaActualizarIn(BaseModel):
    """Esquema para modificacion de categoria existente."""

    nombre: Optional[str] = Field(
        None,
        min_length=2,
        max_length=100,
        description="Nuevo nombre de la categoria",
    )
    id_categoria_padre: Optional[int] = Field(
        None,
        description="Nuevo ID de la categoria padre, o null para convertir en categoria raiz",
    )

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = " ".join(v.strip().split())
            if len(v_limpio) < 2:
                raise ValueError("El nombre de la categoria debe contener al menos 2 caracteres.")
            return v_limpio
        return v


class CategoriaOut(BaseModel):
    """Esquema publico de representacion de categoria."""

    id_categoria: int
    nombre: str
    id_categoria_padre: Optional[int] = None
    padre_nombre: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoriaAdminOut(CategoriaOut):
    """Esquema administrativo enriquecido con estadisticas de catalogo."""

    total_productos: int = 0
    total_subcategorias: int = 0


class CategoriaJerarquicaOut(CategoriaOut):
    """Esquema jerarquico recursivo para representacion en arbol."""

    subcategorias: List["CategoriaJerarquicaOut"] = []


# =============================================================================
# SCHEMAS: TALLAS
# =============================================================================


class TallaBaseIn(BaseModel):
    """Esquema base para definicion de talla comercial."""

    codigo: str = Field(
        ...,
        min_length=1,
        max_length=10,
        description="Codigo comercial estandarizado de la talla (ej. XS, S, M, 38)",
    )
    orden: int = Field(
        default=0,
        ge=0,
        le=32767,
        description="Orden secuencial numerico para presentacion comercial en selectores y filtros",
    )

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo(cls, v: str) -> str:
        v_limpio = v.strip().upper()
        if not v_limpio:
            raise ValueError("El codigo de talla no puede estar vacio.")
        return v_limpio


class TallaCrearIn(TallaBaseIn):
    """Esquema para creacion de talla."""

    pass


class TallaActualizarIn(BaseModel):
    """Esquema para actualizacion de talla."""

    codigo: Optional[str] = Field(None, min_length=1, max_length=10)
    orden: Optional[int] = Field(None, ge=0, le=32767)

    @field_validator("codigo")
    @classmethod
    def normalizar_codigo_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip().upper()
            if not v_limpio:
                raise ValueError("El codigo de talla no puede estar vacio.")
            return v_limpio
        return v


class TallaOut(BaseModel):
    """Esquema de salida para talla comercial."""

    id_talla: int
    codigo: str
    orden: int

    model_config = ConfigDict(from_attributes=True)


class TallaAdminOut(TallaOut):
    """Esquema administrativo de talla con conteo de variantes vinculadas."""

    total_variantes: int = 0


# =============================================================================
# SCHEMAS: COLORES
# =============================================================================


class ColorBaseIn(BaseModel):
    """Esquema base para definicion de color textil corporativo."""

    nombre: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="Denominacion textil de diseno del color (ej. Rojo Carmin, Negro Ebano)",
    )
    codigo_hex: str = Field(
        ...,
        description="Codigo hexadecimal estandar de 7 caracteres iniciando con '#' (ej. #991B1B)",
    )

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_color(cls, v: str) -> str:
        v_limpio = " ".join(v.strip().split())
        if len(v_limpio) < 2:
            raise ValueError("El nombre del color debe contener al menos 2 caracteres.")
        return v_limpio

    @field_validator("codigo_hex")
    @classmethod
    def validar_formato_hex(cls, v: str) -> str:
        v_limpio = v.strip()
        if not re.match(REGEX_HEX_COLOR, v_limpio):
            raise ValueError(
                "El codigo hexadecimal debe iniciar con '#' seguido de 6 digitos hexadecimales (ej. #FFFFFF)."
            )
        return v_limpio.upper()


class ColorCrearIn(ColorBaseIn):
    """Esquema para creacion de color."""

    pass


class ColorActualizarIn(BaseModel):
    """Esquema para modificacion de color existente."""

    nombre: Optional[str] = Field(None, min_length=2, max_length=50)
    codigo_hex: Optional[str] = Field(None)

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = " ".join(v.strip().split())
            if len(v_limpio) < 2:
                raise ValueError("El nombre del color debe contener al menos 2 caracteres.")
            return v_limpio
        return v

    @field_validator("codigo_hex")
    @classmethod
    def validar_formato_hex_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = v.strip()
            if not re.match(REGEX_HEX_COLOR, v_limpio):
                raise ValueError(
                    "El codigo hexadecimal debe iniciar con '#' seguido de 6 digitos hexadecimales (ej. #FFFFFF)."
                )
            return v_limpio.upper()
        return v


class ColorOut(BaseModel):
    """Esquema de salida para color textil."""

    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ColorAdminOut(ColorOut):
    """Esquema administrativo de color con conteo de variantes asociadas."""

    total_variantes: int = 0
