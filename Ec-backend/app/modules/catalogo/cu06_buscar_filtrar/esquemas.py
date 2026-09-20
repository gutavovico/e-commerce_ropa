"""Esquemas Pydantic para el CU06 - Buscar y Filtrar Productos."""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class CriterioOrdenamiento(str, Enum):
    """Criterios de ordenamiento admitidos en el catálogo."""

    RECIENTES = "recientes"
    PRECIO_ASC = "precio_asc"
    PRECIO_DESC = "precio_desc"
    NOMBRE_ASC = "nombre_asc"
    RELEVANCIA = "relevancia"


class VarianteResumenOut(BaseModel):
    """Resumen de una variante de producto (talla, color, stock)."""

    model_config = ConfigDict(from_attributes=True)

    id_variante: int
    sku: str
    talla: str
    id_talla: int
    color: str
    id_color: int
    codigo_hex: Optional[str] = None
    precio_extra: Decimal = Decimal("0.00")
    disponible: bool = True
    cantidad_disponible: int = 0


class ProductoItemOut(BaseModel):
    """Información de un producto en el listado de resultados."""

    model_config = ConfigDict(from_attributes=True)

    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    categoria: str
    id_categoria: int
    coleccion: Optional[str] = None
    id_coleccion: Optional[int] = None
    temporada: Optional[str] = None
    id_temporada: Optional[int] = None
    precio_base: Decimal
    imagen_url: Optional[str] = None
    modelo_ar_url: Optional[str] = None
    activo: bool = True
    badge_editorial: Optional[str] = None
    subtitulo_atelier: Optional[str] = None
    talla_sugerida: Optional[str] = None
    color_sugerido: Optional[str] = None
    variantes: List[VarianteResumenOut] = []


class PaginacionMetaOut(BaseModel):
    """Metadatos de paginación para respuestas de lista."""

    total_registros: int
    pagina_actual: int
    limite: int
    total_paginas: int
    tiene_siguiente: bool
    tiene_anterior: bool


class ProductoPaginadoOut(BaseModel):
    """Respuesta paginada del catálogo de prendas."""

    items: List[ProductoItemOut]
    paginacion: PaginacionMetaOut
    filtros_aplicados: Dict[str, Any] = {}


class OpcionFiltroItem(BaseModel):
    """Elemento genérico para opciones de filtros en frontend/móvil."""

    id: int
    codigo: Optional[str] = None
    nombre: str
    conteo: Optional[int] = None
    extra: Optional[str] = None  # ej. codigo_hex para colores o tipo para temporada


class FiltrosDisponiblesOut(BaseModel):
    """Opciones de filtros actualmente disponibles en el catálogo."""

    temporadas: List[OpcionFiltroItem] = []
    colecciones: List[OpcionFiltroItem] = []
    categorias: List[OpcionFiltroItem] = []
    tallas: List[OpcionFiltroItem] = []
    colores: List[OpcionFiltroItem] = []
    precio_min_global: Decimal = Decimal("0.00")
    precio_max_global: Decimal = Decimal("0.00")


# --- Esquemas para el endpoint POST /catalogo/buscar (compatibilidad SI2-Parcial1.md) ---


class FiltrosDetalleIn(BaseModel):
    """Filtros anidados para búsqueda POST."""

    id_categoria: Optional[int] = None
    id_coleccion: Optional[int] = None
    id_temporada: Optional[int] = None
    id_talla: Optional[int] = None
    id_color: Optional[int] = None
    precio_min: Optional[Decimal] = Field(default=None, ge=0)
    precio_max: Optional[Decimal] = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_rango_precios(self) -> "FiltrosDetalleIn":
        if (
            self.precio_min is not None
            and self.precio_max is not None
            and self.precio_max < self.precio_min
        ):
            raise ValueError("El precio_max no puede ser menor que precio_min.")
        return self


class CatalogoBuscarIn(BaseModel):
    """Entrada del endpoint POST /api/v1/catalogo/buscar."""

    termino_busqueda: Optional[str] = Field(default="", max_length=150)
    filtros: Optional[FiltrosDetalleIn] = None
    pagina: int = Field(default=1, ge=1)
    limite: int = Field(default=12, ge=1, le=50)
