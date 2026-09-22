"""Esquemas Pydantic v2 para CU31: Generar reportes ejecutivos y consultas por voz."""

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class ModuloReporteEnum(str, Enum):
    """Modulos o dominios de informacion reportables."""

    VENTAS = "ventas"
    RESERVAS = "reservas"
    INVENTARIO = "inventario"
    BITACORA = "bitacora"


class FormatoReporteEnum(str, Enum):
    """Formatos binarios soportados para exportacion."""

    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"


class RangoTemporalEnum(str, Enum):
    """Periodos predefinidos o personalizados para consolidacion."""

    HOY = "hoy"
    AYER = "ayer"
    ESTA_SEMANA = "esta_semana"
    ESTE_MES = "este_mes"
    ANIO_ACTUAL = "anio_actual"
    PERSONALIZADO = "personalizado"


class IntencionVozEnum(str, Enum):
    """Intenciones operativas extraidas de las ordenes habladas."""

    EXPORTAR = "exportar"
    CONSULTAR = "consultar"
    FILTRAR = "filtrar"


class ComandoVozIn(BaseModel):
    """Entrada recibida desde la Web Speech API del frontend."""

    model_config = ConfigDict(extra="forbid")

    texto_dictado: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Texto o comando dictado por el operador corporativo",
        examples=["Descargar reporte de ventas de este mes en excel"],
    )


class ComandoVozOut(BaseModel):
    """Resultado estructurado del parser determinista de lenguaje natural."""

    texto_dictado: str
    intencion: IntencionVozEnum
    modulo: ModuloReporteEnum
    formato: FormatoReporteEnum
    periodo: RangoTemporalEnum
    id_sucursal: Optional[int] = None
    nombre_sucursal: Optional[str] = None
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None
    confianza: float = Field(default=1.0, ge=0.0, le=1.0)
    accion_recomendada: str = Field(
        default="ejecutar_exportacion",
        description="Accion sugerida para la interfaz ('ejecutar_exportacion' o 'actualizar_filtros')",
    )


class ReporteFiltrosIn(BaseModel):
    """Parametros de consulta y exportacion de datos tabulares."""

    model_config = ConfigDict(extra="forbid")

    modulo: ModuloReporteEnum
    formato: FormatoReporteEnum = FormatoReporteEnum.EXCEL
    periodo: RangoTemporalEnum = RangoTemporalEnum.ESTE_MES
    id_sucursal: Optional[int] = Field(
        default=None,
        description="Identificador de sucursal o null para consolidado corporativo",
    )
    fecha_inicio: Optional[date] = None
    fecha_fin: Optional[date] = None


class ReportePrevisualizacionOut(BaseModel):
    """Resumen preliminar de registros y metricas antes de compilar el archivo."""

    modulo: ModuloReporteEnum
    formato: FormatoReporteEnum
    total_registros: int
    fecha_corte: datetime
    nombre_archivo_sugerido: str
    resumen_financiero: Optional[Dict[str, Any]] = None
