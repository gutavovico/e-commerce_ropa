"""Esquemas Pydantic v2 para P2-CU23, P2-CU24 y P2-CU25 (Aprendizaje Automático en Bolivianos Bs. / BOB)."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

OrigenDatosMl = Literal["sintetico", "real", "mixto"]
TipoModeloMl = Literal["supervisado", "no_supervisado"]
EstadoModeloMl = Literal["entrenando", "evaluado", "activo", "archivado", "fallido"]


class CrearDatasetMlIn(BaseModel):
    """Solicitud de creación y preprocesamiento de un conjunto de datos (P2-CU23 pasos 1-3)."""

    nombre: str = Field(..., min_length=3, max_length=140)
    origen: OrigenDatosMl = Field(default="sintetico")
    cantidad_registros_sinteticos: int = Field(default=120, ge=20, le=2000)
    horizonte_meses: int = Field(default=6, ge=1, le=24)
    variables_seleccionadas: list[str] = Field(
        default_factory=lambda: [
            "precio_bob",
            "frecuencia_compra",
            "recencia_dias",
            "monto_acumulado_bob",
            "temporada_estacional",
            "sucursal_codificada",
        ],
        min_length=1,
    )
    tipo_cambio_bob: Decimal = Field(default=Decimal("6.96"), ge=Decimal("1.00"))


class DatasetMlOut(BaseModel):
    """Representación de un conjunto de datos preprocesado (P2-CU23)."""

    model_config = ConfigDict(from_attributes=True)

    id_dataset: int
    id_tenant: int
    nombre: str
    origen: str
    cantidad_registros: int
    variables_seleccionadas: list[str]
    parametros_generacion: dict[str, Any]
    resumen_preprocesamiento: dict[str, Any]
    muestra_datos: list[dict[str, Any]]
    creado_en: datetime


class EntrenarModeloMlIn(BaseModel):
    """Solicitud para entrenar y evaluar un modelo supervisado o no supervisado (P2-CU23 pasos 4-6)."""

    id_dataset: int
    nombre: str = Field(..., min_length=3, max_length=140)
    tipo_modelo: TipoModeloMl
    algoritmo: Optional[str] = Field(default=None, max_length=80)
    variable_objetivo: Optional[str] = Field(default=None, max_length=80)
    variables_entrada: list[str] = Field(default_factory=list)
    numero_clusters: int = Field(default=3, ge=2, le=6)
    activar_inmediatamente: bool = Field(default=False)
    forzar_fallo_entrenamiento: bool = Field(default=False)
    tipo_cambio_bob: Decimal = Field(default=Decimal("6.96"), ge=Decimal("1.00"))


class ModeloMlOut(BaseModel):
    """Representación de un modelo de aprendizaje automático y sus métricas (P2-CU23, RN49)."""

    model_config = ConfigDict(from_attributes=True)

    id_modelo: int
    id_tenant: int
    id_dataset: int
    nombre: str
    tipo_modelo: str
    algoritmo: str
    variable_objetivo: Optional[str] = None
    variables_entrada: list[str]
    origen_datos: str
    estado: str
    activo: bool
    motivo_error: Optional[str] = None
    metricas_entrenamiento: dict[str, Any]
    metricas_validacion: dict[str, Any]
    metricas_prueba: dict[str, Any]
    creado_en: datetime
    actualizado_en: datetime


class ResumenAprendizajeMlOut(BaseModel):
    """Contexto completo para el panel de gestión de datos y modelos ML (P2-CU23)."""

    id_tenant: int
    nombre_empresa: str
    moneda: str = "BOB"
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("6.96")
    registros_reales_ventas: int
    registros_reales_clientes: int
    variables_disponibles: list[dict[str, str]]
    variables_objetivo_supervisado: list[dict[str, str]]
    productos_empresa: list[dict[str, Any]]
    sucursales_empresa: list[dict[str, Any]]
    datasets: list[DatasetMlOut]
    modelos: list[ModeloMlOut]
    modelo_supervisado_activo: Optional[ModeloMlOut] = None
    modelo_no_supervisado_activo: Optional[ModeloMlOut] = None


class PrediccionItemOut(BaseModel):
    """Fila individual de predicción de demanda e ingresos en Bolivianos (P2-CU24, RN50)."""

    id_prediccion: int
    id_modelo: int
    id_producto: Optional[int] = None
    nombre_producto: str
    id_sucursal: Optional[int] = None
    nombre_sucursal: str
    periodo: str
    demanda_esperada: int
    ingresos_esperados_bob: Decimal
    equivalente_usd: Decimal
    probabilidad: Decimal = Field(..., ge=Decimal("0.0000"), le=Decimal("1.0000"))
    nivel_confianza: str


class ConsultaPrediccionesOut(BaseModel):
    """Respuesta del dashboard de predicciones supervisadas (P2-CU24)."""

    tiene_modelo_activo: bool
    mensaje_estado: str
    aviso_datos_sinteticos: bool = False
    mensaje_datos_sinteticos: Optional[str] = None
    moneda: str = "BOB"
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("6.96")
    modelo_activo: Optional[ModeloMlOut] = None
    periodos_disponibles: list[str] = Field(default_factory=list)
    resumen_kpis_bob: dict[str, Any] = Field(default_factory=dict)
    predicciones: list[PrediccionItemOut] = Field(default_factory=list)


class SegmentoClienteItemOut(BaseModel):
    """Segmento o cluster de clientes con métricas RFM en Bolivianos (P2-CU25)."""

    id_segmento: int
    id_modelo: int
    codigo_grupo: str
    nombre_grupo: str
    descripcion: str
    cantidad_clientes: int
    porcentaje_clientes: float
    sin_clientes: bool = False
    caracteristicas: dict[str, Any]
    clientes_muestra: list[dict[str, Any]]


class ConsultaSegmentosOut(BaseModel):
    """Respuesta del dashboard de segmentación no supervisada de clientes (P2-CU25)."""

    tiene_modelo_activo: bool
    mensaje_estado: str
    aviso_datos_sinteticos: bool = False
    mensaje_datos_sinteticos: Optional[str] = None
    moneda: str = "BOB"
    simbolo_moneda: str = "Bs."
    tipo_cambio_bob: Decimal = Decimal("6.96")
    modelo_activo: Optional[ModeloMlOut] = None
    total_clientes_segmentados: int = 0
    segmentos: list[SegmentoClienteItemOut] = Field(default_factory=list)

