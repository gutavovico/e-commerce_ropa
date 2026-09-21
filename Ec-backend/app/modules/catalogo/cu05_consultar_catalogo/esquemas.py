"""Esquemas Pydantic v2 para CU05: Consultar Catálogo de Productos."""

from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ColorItemOut(BaseModel):
    """Representación de color disponible para una prenda."""

    id_color: int
    nombre: str
    codigo_hex: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class CategoriaResumenOut(BaseModel):
    """Resumen de categoría con conteo de prendas activas para chips superiores."""

    id_categoria: int
    nombre: str
    total_prendas: int

    model_config = ConfigDict(from_attributes=True)


class ProductoCatalogoOut(BaseModel):
    """Tarjeta de prenda de alta costura dentro del catálogo general."""

    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    precio_final: Decimal
    tiene_descuento: bool = False
    porcentaje_descuento: Optional[int] = None
    imagen_url: Optional[str] = None
    categoria_id: int
    categoria_nombre: str
    subtitulo_atelier: str
    etiqueta_badge: Optional[str] = None
    rating_promedio: float = 5.0
    tallas_disponibles: List[str] = Field(default_factory=list)
    colores_disponibles: List[ColorItemOut] = Field(default_factory=list)
    stock_total_disponible: int = 0
    tiene_stock: bool = True
    es_favorito: bool = False

    model_config = ConfigDict(from_attributes=True)


class CatalogoOut(BaseModel):
    """Respuesta consolidada del catálogo general paginado con resumen de categorías."""

    resumen_categorias: List[CategoriaResumenOut]
    total_articulos: int
    pagina_actual: int
    limite: int
    total_paginas: int
    tiene_siguiente: bool
    tiene_anterior: bool
    categoria_seleccionada_id: Optional[int] = None
    items: List[ProductoCatalogoOut]

    model_config = ConfigDict(from_attributes=True)
