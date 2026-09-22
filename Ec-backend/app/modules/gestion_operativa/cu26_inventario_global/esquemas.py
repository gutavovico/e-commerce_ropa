"""Esquemas Pydantic v2 para CU26: Consultar inventario global.

Define los contratos DTO fuertemente tipados de entrada y salida para la consulta
analitica consolidada de existencias fisicas y reservas en red multi-sucursal.
"""

from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class ExistenciaSucursalItemOut(BaseModel):
    """Detalle de existencias fisicas en una boutique activa."""

    model_config = ConfigDict(from_attributes=True)

    id_sucursal: int = Field(..., description="Identificador unico de la sucursal")
    nombre_sucursal: str = Field(..., description="Denominacion comercial de la boutique")
    ciudad: str = Field(..., description="Ciudad de localizacion")
    direccion: str = Field(..., description="Direccion fisica de la boutique")
    telefono: Optional[str] = Field(default=None, description="Telefono de contacto de la sede")
    cantidad_disponible: int = Field(default=0, ge=0, description="Unidades fisicas disponibles para venta")
    cantidad_reservada: int = Field(default=0, ge=0, description="Unidades comprometidas en reservas activas")

    @field_validator("cantidad_disponible", "cantidad_reservada", mode="before")
    @classmethod
    def validar_no_nulo(cls, v: Optional[int]) -> int:
        return v if v is not None else 0


class InventarioGlobalItemOut(BaseModel):
    """Ficha consolidada de existencias por variante comercial y prenda."""

    model_config = ConfigDict(from_attributes=True)

    id_variante: int = Field(..., description="Identificador unico de la variante")
    id_producto: int = Field(..., description="Identificador del producto base")
    nombre_producto: str = Field(..., description="Denominacion editorial de la prenda")
    sku: str = Field(..., description="Codigo identificador SKU unico de la variante")
    categoria: str = Field(..., description="Categoria textil asignada")
    talla: str = Field(..., description="Talla de confeccion")
    color: str = Field(..., description="Nombre comercial del color")
    swatches_hex: Optional[str] = Field(default=None, description="Codigo hexadecimal cromático del color")
    total_disponible: int = Field(..., ge=0, description="Suma consolidada de unidades disponibles en red")
    total_reservado: int = Field(..., ge=0, description="Suma consolidada de unidades reservadas en red")
    total_fisico: int = Field(..., ge=0, description="Total de unidades fisicas (disponible + reservado)")
    estado_stock: Literal["optimo", "alerta_baja", "agotado"] = Field(
        ..., description="Clasificacion semaforica de inventario"
    )
    desglose_sucursales: List[ExistenciaSucursalItemOut] = Field(
        default_factory=list, description="Desglose de existencias por boutique activa"
    )

    @field_validator("total_disponible", "total_reservado", "total_fisico", mode="before")
    @classmethod
    def validar_totales_no_nulos(cls, v: Optional[int]) -> int:
        return v if v is not None else 0


class MetricasInventarioGlobalOut(BaseModel):
    """Indicadores cuantitativos consolidados de la red comercial."""

    model_config = ConfigDict(from_attributes=True)

    total_unidades_red: int = Field(default=0, ge=0, description="Total de unidades fisicas disponibles en red")
    variantes_monitoreadas: int = Field(default=0, ge=0, description="Total de variantes comerciales activas")
    alertas_stock_bajo: int = Field(default=0, ge=0, description="Total de variantes en o bajo umbral de alerta")
    sedes_activas: int = Field(default=0, ge=0, description="Cantidad de sucursales activas operativas")


class InventarioGlobalFiltrosIn(BaseModel):
    """Parametros de consulta y filtrado multicriterio."""

    q: Optional[str] = Field(default=None, max_length=100, description="Busqueda textual por prenda o SKU")
    id_categoria: Optional[int] = Field(default=None, ge=1, description="Filtro opcional por categoria")
    id_sucursal: Optional[int] = Field(default=None, ge=1, description="Filtro opcional por sucursal")
    estado_stock: Optional[Literal["optimo", "alerta_baja", "agotado", "todos"]] = Field(
        default="todos", description="Estado de existencias a filtrar"
    )
    ordenar_por: Optional[Literal["stock_asc", "stock_desc", "nombre_asc", "nombre_desc", "sku_asc"]] = Field(
        default="nombre_asc", description="Criterio de ordenacion"
    )
    pagina: int = Field(default=1, ge=1, description="Numero de pagina actual")
    limite: int = Field(default=10, ge=1, le=100, description="Cantidad de registros por pagina")

    @field_validator("q", mode="before")
    @classmethod
    def sanitizar_texto(cls, v: Optional[str]) -> Optional[str]:
        if isinstance(v, str):
            v_limpio = v.strip()
            return v_limpio if len(v_limpio) > 0 else None
        return None


class RespuestaInventarioGlobalOut(BaseModel):
    """Contrato de respuesta paginada y analitica de inventario global."""

    model_config = ConfigDict(from_attributes=True)

    items: List[InventarioGlobalItemOut] = Field(default_factory=list, description="Registros de variantes consolidadas")
    metricas: MetricasInventarioGlobalOut = Field(..., description="Metricas globales calculadas de la red")
    total: int = Field(..., ge=0, description="Total de registros coincidentes con los filtros")
    pagina: int = Field(..., ge=1, description="Pagina actual devuelta")
    limite: int = Field(..., ge=1, le=100, description="Limite de registros por pagina")
    total_paginas: int = Field(..., ge=1, description="Total de paginas disponibles calculadas")
