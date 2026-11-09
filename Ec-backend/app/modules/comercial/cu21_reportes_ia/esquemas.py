"""Esquemas Pydantic v2 para P2-CU21: Generar reporte con IA."""

from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from modules.plataforma.cu22_catalogo_reportes.esquemas import CatalogoReporteOut

EstadoSolicitudIa = Literal[
    "procesando",
    "completada",
    "ambigua",
    "no_soportada",
    "rechazada",
    "error",
]

FormatoVisualizacionIa = Literal["tabla", "barras", "linea", "torta", "ambos"]


class GenerarReporteIaIn(BaseModel):
    """Petición de generación de reporte con IA en lenguaje natural (escrito o transcrito por voz)."""

    prompt_texto: str = Field(
        ...,
        min_length=2,
        max_length=1000,
        description="Solicitud en lenguaje natural escrita o dictada por el administrador",
    )
    codigo_reporte_forzado: Optional[str] = Field(
        default=None,
        description="Opcional: código del catálogo elegido explícitamente para desambiguar",
    )
    formato_preferido: Optional[FormatoVisualizacionIa] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    id_sucursal: Optional[int] = Field(default=None, gt=0)
    id_categoria: Optional[int] = Field(default=None, gt=0)
    id_tenant_solicitado: Optional[int] = Field(
        default=None,
        description="Campo para detectar y rechazar intentos de consultar otra empresa (CU21 A7)",
    )
    moneda_visualizacion: str = Field(default="BOB", pattern=r"^(BOB|USD|EUR)$")
    tipo_cambio_bob: Decimal = Field(default=Decimal("6.96"), gt=Decimal("0"))


class InterpretacionReporteIaOut(BaseModel):
    """Resultado estructurado de la interpretación semántica de la IA contra el catálogo permitido."""

    estado: EstadoSolicitudIa
    codigo_reporte: Optional[str] = None
    nombre_reporte: Optional[str] = None
    vista_origen: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    id_sucursal: Optional[int] = None
    nombre_sucursal: Optional[str] = None
    id_categoria: Optional[int] = None
    nombre_categoria: Optional[str] = None
    tipo_grafico_sugerido: Literal["tabla", "barras", "linea", "torta"] = "barras"
    formato_visualizacion: FormatoVisualizacionIa = "ambos"
    explicacion_ia: str
    origen_motor: str = "gemini_o_semantico_determinista"


class PuntoGraficoReporteOut(BaseModel):
    """Punto de datos para renderizar gráficos de barras, línea o torta en el frontend."""

    etiqueta: str
    valor: float
    valor_secundario: Optional[float] = None
    unidad: str = "Bs."


class SolicitudReporteIaResultadoOut(BaseModel):
    """Respuesta completa de P2-CU21 con datos tabulares, serie gráfica, KPIs en Bolivianos (Bs./BOB) y estado."""

    id_solicitud: int
    estado: EstadoSolicitudIa
    mensaje_estado: str
    prompt_original: str
    codigo_reporte: Optional[str] = None
    titulo_reporte: Optional[str] = None
    interpretacion: InterpretacionReporteIaOut
    moneda: str = "BOB"
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("6.96")
    formato_visualizacion: FormatoVisualizacionIa = "ambos"
    tipo_grafico: Literal["tabla", "barras", "linea", "torta"] = "barras"
    columnas: list[str] = Field(default_factory=list)
    filas: list[list[Any]] = Field(default_factory=list)
    serie_grafico: list[PuntoGraficoReporteOut] = Field(default_factory=list)
    resumen_kpis_bob: dict[str, Any] = Field(default_factory=dict)
    sin_datos: bool = False
    ejemplos_sugeridos: list[str] = Field(default_factory=list)
    exportaciones: list[dict[str, Any]] = Field(default_factory=list)
    creado_en: datetime


class SolicitudReporteIaHistorialOut(BaseModel):
    """Elemento del historial de solicitudes de reportes con IA de la empresa (CU21 paso 8, RN47)."""

    model_config = ConfigDict(from_attributes=True)

    id_solicitud: int
    comando_voz_texto: str
    tipo_reporte: Optional[str] = None
    estado: str
    formato_visualizacion: str
    mensaje_estado: Optional[str] = None
    exportaciones: list[dict[str, Any]] = Field(default_factory=list)
    creado_en: datetime


class ContextoReportesIaEmpresaOut(BaseModel):
    """Catálogo activo y metadatos de la empresa para inicializar el centro de reportes con IA (P2-CU21)."""

    id_tenant: int
    nombre_empresa: str
    moneda_empresa: str
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("6.96")
    catalogo_activo: list[CatalogoReporteOut]
    sucursales_activas: list[dict[str, Any]]
    categorias_empresa: list[dict[str, Any]]
    ejemplos_destacados: list[str]

