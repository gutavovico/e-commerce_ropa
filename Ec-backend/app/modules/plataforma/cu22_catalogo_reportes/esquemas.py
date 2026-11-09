"""Esquemas Pydantic v2 para P2-CU22: Gestionar catálogo de reportes permitidos."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

VISTAS_DATOS_PERMITIDAS = frozenset({
    "vw_ventas_por_sucursal",
    "ranking_productos",
    "vw_inventario_consolidado",
    "vw_reservas_pendientes",
})

TIPOS_GRAFICO_PERMITIDOS = frozenset({"tabla", "barras", "linea", "torta"})

FILTROS_CATALOGO_PERMITIDOS = frozenset({
    "fecha_inicio",
    "fecha_fin",
    "id_sucursal",
    "id_categoria",
    "id_producto",
    "moneda",
    "estado",
})


class MetricaReporteInOut(BaseModel):
    """Definición de una métrica autorizada dentro de un reporte del catálogo (CU22 paso 4)."""

    codigo: str = Field(..., min_length=2, max_length=60)
    etiqueta: str = Field(..., min_length=2, max_length=100)
    expresion: str = Field(..., max_length=200)
    es_monetaria: bool = False


class DimensionReporteInOut(BaseModel):
    """Definición de una dimensión autorizada dentro de un reporte del catálogo (CU22 paso 4)."""

    codigo: str = Field(..., min_length=2, max_length=60)
    etiqueta: str = Field(..., min_length=2, max_length=100)
    expresion: str = Field(..., max_length=200)


class CatalogoReporteGuardarIn(BaseModel):
    """Payload para crear o actualizar un reporte del catálogo permitido (P2-CU22)."""

    codigo: str = Field(
        ...,
        min_length=3,
        max_length=60,
        pattern=r"^[a-z0-9_]{3,60}$",
        description="Identificador técnico único del reporte",
    )
    nombre: str = Field(..., min_length=3, max_length=120)
    descripcion: Optional[str] = Field(default=None, max_length=500)
    vista_origen: str = Field(..., min_length=3, max_length=80)
    metricas: list[MetricaReporteInOut] = Field(..., min_length=1)
    dimensiones: list[DimensionReporteInOut] = Field(..., min_length=1)
    filtros_permitidos: list[str] = Field(default_factory=list)
    tipos_grafico: list[str] = Field(..., min_length=1)
    ejemplos_consulta: list[str] = Field(default_factory=list)
    activo: bool = True


class CambiarEstadoCatalogoReporteIn(BaseModel):
    """Solicitud para activar o desactivar un reporte del catálogo (CU22 A3)."""

    activo: bool


class CatalogoReporteOut(BaseModel):
    """Representación de un reporte del catálogo permitido (P2-CU22)."""

    model_config = ConfigDict(from_attributes=True)

    id_reporte_catalogo: int
    codigo: str
    nombre: str
    descripcion: Optional[str] = None
    vista_origen: str
    metricas: list[MetricaReporteInOut]
    dimensiones: list[DimensionReporteInOut]
    filtros_permitidos: list[str]
    tipos_grafico: list[str]
    ejemplos_consulta: list[str]
    activo: bool
    creado_en: datetime
    actualizado_en: datetime


class MetadatosCatalogoReportesOut(BaseModel):
    """Metadatos de apoyo para el formulario del Super Administrador en P2-CU22."""

    vistas_permitidas: list[str]
    tipos_grafico_permitidos: list[str]
    filtros_permitidos: list[str]
    reportes: list[CatalogoReporteOut]

