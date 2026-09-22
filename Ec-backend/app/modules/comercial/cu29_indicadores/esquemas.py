"""Esquemas Pydantic v2 para CU29: Visualizar indicadores empresariales.
Nomenclatura oficial: Visualizar indicadores empresariales
"""

from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional
from pydantic import BaseModel, ConfigDict, Field, model_validator


PeriodoPreset = Literal["7d", "30d", "mes_actual", "anio_actual", "personalizado"]


class IndicadoresFiltrosIn(BaseModel):
    """Filtros de consulta analitica temporal y territorial."""

    periodo: PeriodoPreset = Field(
        default="30d",
        description="Rango de periodo predeterminado o personalizado",
    )
    fecha_desde: Optional[date] = Field(
        default=None,
        description="Fecha de inicio requerida para periodo personalizado",
    )
    fecha_hasta: Optional[date] = Field(
        default=None,
        description="Fecha de culminacion requerida para periodo personalizado",
    )
    id_sucursal: Optional[int] = Field(
        default=None,
        description="Identificador de sucursal opcional para administradores",
    )

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="after")
    def validar_fechas(self) -> "IndicadoresFiltrosIn":
        if self.periodo == "personalizado":
            if not self.fecha_desde or not self.fecha_hasta:
                raise ValueError("Para periodo personalizado debe proporcionar fecha_desde y fecha_hasta.")
            if self.fecha_desde > self.fecha_hasta:
                raise ValueError("La fecha_desde no puede ser posterior a fecha_hasta.")
        return self


class ResumenEjecutivoOut(BaseModel):
    """Indicadores ejecutivos de alto nivel con variacion contra el periodo anterior."""

    periodo_inicio: date
    periodo_fin: date
    ingresos_totales: Decimal
    variacion_porcentual: Decimal = Field(
        description="Variacion porcentual de ingresos con respecto al periodo anterior",
    )
    total_transacciones: int
    variacion_porcentual_transacciones: Decimal
    margen_estimado: Decimal = Field(
        description="Porcentaje estimado de margen comercial bruto",
    )
    ticket_promedio: Decimal
    variacion_porcentual_ticket: Decimal
    unidades_vendidas: int
    variacion_porcentual_unidades: Decimal

    model_config = ConfigDict(from_attributes=True)


class PuntoSerieTemporalOut(BaseModel):
    """Punto de datos en una serie cronologica de ingresos."""

    etiqueta_tiempo: str
    fecha_inicio: date
    monto_ingresos: Decimal
    cantidad_ordenes: int

    model_config = ConfigDict(from_attributes=True)


class SerieTemporalIngresosOut(BaseModel):
    """Coleccion cronologica de ingresos ordenados por fecha."""

    agrupacion: Literal["diaria", "semanal", "mensual"]
    puntos: List[PuntoSerieTemporalOut]

    model_config = ConfigDict(from_attributes=True)


class ItemRankingProductoOut(BaseModel):
    """Prenda individual dentro del ranking de mayor volumen y recaudacion."""

    id_producto: int
    nombre_producto: str
    sku_referencia: str
    categoria_nombre: str
    unidades_vendidas: int
    monto_total_generado: Decimal
    porcentaje_contribucion: Decimal

    model_config = ConfigDict(from_attributes=True)


class RankingProductosOut(BaseModel):
    """Ranking ordenado de las prendas mas vendidas de la red."""

    limite: int
    productos: List[ItemRankingProductoOut]

    model_config = ConfigDict(from_attributes=True)


class CategoriaDistribucionOut(BaseModel):
    """Distribucion de ventas por categoria taxonomica."""

    id_categoria: int
    nombre_categoria: str
    monto_facturado: Decimal
    unidades_vendidas: int
    porcentaje_participacion: Decimal

    model_config = ConfigDict(from_attributes=True)


class CanalDistribucionOut(BaseModel):
    """Distribucion de ventas por canal de comercializacion."""

    canal_codigo: str
    canal_nombre: str
    monto_facturado: Decimal
    total_ordenes: int
    porcentaje_participacion: Decimal

    model_config = ConfigDict(from_attributes=True)


class DistribucionVentasOut(BaseModel):
    """Desglose consolidado de ventas por categoria y canal."""

    por_categoria: List[CategoriaDistribucionOut]
    por_canal: List[CanalDistribucionOut]

    model_config = ConfigDict(from_attributes=True)


class SucursalDesempenoOut(BaseModel):
    """Desempeno transaccional de una sede fisica activa."""

    id_sucursal: int
    nombre_sucursal: str
    ciudad: str
    monto_facturado: Decimal
    total_ventas: int
    ticket_promedio: Decimal
    porcentaje_red: Decimal

    model_config = ConfigDict(from_attributes=True)


class ComparativaSucursalesOut(BaseModel):
    """Comparativa de rendimiento entre todas las sucursales activas de la cadena."""

    sucursales: List[SucursalDesempenoOut]

    model_config = ConfigDict(from_attributes=True)


class DashboardIndicadoresCompletoOut(BaseModel):
    """Consolidado analitico integral para reduccion de latencia HTTP."""

    resumen: ResumenEjecutivoOut
    serie_temporal: SerieTemporalIngresosOut
    top_productos: RankingProductosOut
    distribucion: DistribucionVentasOut
    comparativa_sucursales: Optional[ComparativaSucursalesOut] = None

    model_config = ConfigDict(from_attributes=True)
