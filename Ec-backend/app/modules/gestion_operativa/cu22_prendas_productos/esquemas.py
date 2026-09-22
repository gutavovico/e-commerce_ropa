"""Esquemas Pydantic v2 para CU22: Gestionar Prendas, Productos y Variantes (SKUs)."""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


# =============================================================================
# ESQUEMAS DE PRENDAS / PRODUCTOS
# =============================================================================


class ProductoBaseIn(BaseModel):
    """Esquema base de datos para productos/prendas."""

    nombre: str = Field(..., min_length=3, max_length=200, description="Nombre comercial unico")
    id_categoria: int = Field(..., gt=0, description="ID de la categoria taxonomica obligatoria")
    precio_base: Decimal = Field(..., gt=Decimal("0.00"), description="Precio base mayor a cero")
    descripcion: Optional[str] = Field(None, description="Descripcion editorial de diseno y tejido")
    id_coleccion: Optional[int] = Field(None, gt=0, description="ID de la coleccion opcional")
    imagen_url: Optional[str] = Field(None, max_length=500, description="URL de la fotografia principal")
    modelo_ar_url: Optional[str] = Field(None, max_length=500, description="URL del recurso 3D/AR")

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre(cls, v: str) -> str:
        v_limpio = " ".join(v.strip().split())
        if len(v_limpio) < 3:
            raise ValueError("El nombre del producto debe contener al menos 3 caracteres.")
        return v_limpio


class ProductoCrearIn(ProductoBaseIn):
    """Payload para alta de nueva prenda."""

    activo: bool = Field(True, description="Estado de publicacion inicial")


class ProductoActualizarIn(BaseModel):
    """Payload para actualizacion editorial de prenda."""

    nombre: Optional[str] = Field(None, min_length=3, max_length=200)
    id_categoria: Optional[int] = Field(None, gt=0)
    precio_base: Optional[Decimal] = Field(None, gt=Decimal("0.00"))
    descripcion: Optional[str] = None
    id_coleccion: Optional[int] = Field(None, gt=0)
    imagen_url: Optional[str] = Field(None, max_length=500)
    modelo_ar_url: Optional[str] = Field(None, max_length=500)
    activo: Optional[bool] = None

    @field_validator("nombre")
    @classmethod
    def normalizar_nombre_opcional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            v_limpio = " ".join(v.strip().split())
            if len(v_limpio) < 3:
                raise ValueError("El nombre debe contener al menos 3 caracteres.")
            return v_limpio
        return v


class ProductoEstadoIn(BaseModel):
    """Payload para conmutacion logica de visibilidad comercial."""

    activo: bool = Field(..., description="Nuevo estado logico de publicacion")


class ProductoResumenOut(BaseModel):
    """DTO resumido para listados administrativos."""

    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    id_categoria: int
    categoria_nombre: Optional[str] = None
    id_coleccion: Optional[int] = None
    coleccion_nombre: Optional[str] = None
    imagen_url: Optional[str] = None
    modelo_ar_url: Optional[str] = None
    activo: bool
    total_variantes: int = 0
    stock_total: int = 0
    creado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =============================================================================
# ESQUEMAS DE VARIANTES Y MATRIZ DE SKUs
# =============================================================================


class VarianteItemIn(BaseModel):
    """Item para creacion individual de variante."""

    id_talla: int = Field(..., gt=0, description="ID de la talla")
    id_color: int = Field(..., gt=0, description="ID del color")
    sku: Optional[str] = Field(None, max_length=64, description="SKU manual opcional")
    precio_extra: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Recargo sobre precio base")


class MatrizGenerarIn(BaseModel):
    """Payload para generacion masiva de variantes mediante matriz cartesiana."""

    ids_tallas: List[int] = Field(..., min_length=1, description="Lista de IDs de tallas seleccionadas")
    ids_colores: List[int] = Field(..., min_length=1, description="Lista de IDs de colores seleccionados")
    precio_extra_defecto: Decimal = Field(Decimal("0.00"), ge=Decimal("0.00"), description="Recargo por defecto")


class VarianteActualizarIn(BaseModel):
    """Payload para actualizacion de variante."""

    sku: Optional[str] = Field(None, min_length=3, max_length=64)
    precio_extra: Optional[Decimal] = Field(None, ge=Decimal("0.00"))
    activo: Optional[bool] = None


class VarianteOut(BaseModel):
    """DTO de salida para una variante de producto."""

    id_variante: int
    id_producto: int
    id_talla: int
    talla_codigo: str
    id_color: int
    color_nombre: str
    color_hex: Optional[str] = None
    sku: str
    precio_extra: Decimal
    precio_final: Decimal
    activo: bool
    stock_disponible: int = 0
    creado_en: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ProductoDetalleOut(ProductoResumenOut):
    """DTO detallado que incluye la coleccion de variantes del producto."""

    variantes: List[VarianteOut] = []


class ListaPaginadaProductosOut(BaseModel):
    """DTO de paginacion para listados de catalogo."""

    items: List[ProductoResumenOut]
    total: int
    pagina: int
    limite: int
    total_paginas: int


class ImagenSubidaOut(BaseModel):
    """Respuesta tras la carga exitosa de imagen de prenda."""

    url: str = Field(..., description="Ruta relativa del archivo estatico almacenado")
