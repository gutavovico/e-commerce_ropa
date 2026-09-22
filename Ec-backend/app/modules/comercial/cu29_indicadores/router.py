"""Router REST para CU29: Visualizar indicadores empresariales.
Nomenclatura oficial: Visualizar indicadores empresariales
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu29_indicadores.errores import RangoTemporalInvalidoError
from modules.comercial.cu29_indicadores.esquemas import (
    ComparativaSucursalesOut,
    DashboardIndicadoresCompletoOut,
    DistribucionVentasOut,
    IndicadoresFiltrosIn,
    PeriodoPreset,
    RankingProductosOut,
    ResumenEjecutivoOut,
    SerieTemporalIngresosOut,
)
from modules.comercial.cu29_indicadores.servicio import (
    ServicioIndicadoresEmpresariales,
)

router = APIRouter(tags=["Gestion Comercial - Indicadores Empresariales (Admin)"])
servicio_indicadores = ServicioIndicadoresEmpresariales()


def _construir_filtros(
    periodo: PeriodoPreset,
    fecha_desde: Optional[date],
    fecha_hasta: Optional[date],
    id_sucursal: Optional[int],
) -> IndicadoresFiltrosIn:
    """Valida y construye el esquema de filtros analiticos."""
    try:
        return IndicadoresFiltrosIn(
            periodo=periodo,
            fecha_desde=fecha_desde,
            fecha_hasta=fecha_hasta,
            id_sucursal=id_sucursal,
        )
    except ValidationError as e:
        raise RangoTemporalInvalidoError(
            message=str(e.errors()[0].get("msg") if e.errors() else "Filtros temporales invalidos.")
        )


@router.get(
    "/admin/indicadores/dashboard",
    response_model=DashboardIndicadoresCompletoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar dashboard consolidado de indicadores empresariales",
    description="Retorna el paquete analitico integral (resumen, serie temporal, top productos, distribucion y comparativa) en una sola llamada.",
)
def obtener_dashboard_indicadores(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo administradores)"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> DashboardIndicadoresCompletoOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, id_sucursal)
    return servicio_indicadores.obtener_dashboard_consolidado(db, filtros, usuario)


@router.get(
    "/admin/indicadores/resumen",
    response_model=ResumenEjecutivoOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar resumen ejecutivo de indicadores",
    description="Retorna indicadores clave de facturacion, transacciones, margen y comparativa contra el periodo anterior.",
)
def obtener_resumen_ejecutivo(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo administradores)"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ResumenEjecutivoOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, id_sucursal)
    return servicio_indicadores.obtener_resumen_ejecutivo(db, filtros, usuario)


@router.get(
    "/admin/indicadores/serie-temporal",
    response_model=SerieTemporalIngresosOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar serie temporal de ingresos",
    description="Retorna serie cronologica agrupada por fecha para graficar curvas de ingresos y volumen de transacciones.",
)
def obtener_serie_temporal(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo administradores)"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> SerieTemporalIngresosOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, id_sucursal)
    return servicio_indicadores.obtener_serie_temporal(db, filtros, usuario)


@router.get(
    "/admin/indicadores/top-productos",
    response_model=RankingProductosOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar top de prendas mas vendidas",
    description="Retorna el ranking ordenado de las prendas con mayor volumen de venta y recaudacion monetaria.",
)
def obtener_top_productos(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo administradores)"),
    limite: int = Query(5, ge=1, le=20, description="Cantidad maxima de prendas en el ranking"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> RankingProductosOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, id_sucursal)
    return servicio_indicadores.obtener_top_productos(db, filtros, usuario, limite=limite)


@router.get(
    "/admin/indicadores/distribucion",
    response_model=DistribucionVentasOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar distribucion de ventas por categoria y canal",
    description="Retorna el desglose analitico de ventas por categoria de prenda y canal de origen.",
)
def obtener_distribucion_ventas(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal a filtrar (solo administradores)"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> DistribucionVentasOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, id_sucursal)
    return servicio_indicadores.obtener_distribucion_ventas(db, filtros, usuario)


@router.get(
    "/admin/indicadores/comparativa-sucursales",
    response_model=ComparativaSucursalesOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar comparativa de rendimiento entre sucursales",
    description="Retorna el desempeno comparado de todas las sucursales activas. Acceso restringido exclusivamente a administradores.",
)
def obtener_comparativa_sucursales(
    periodo: PeriodoPreset = Query("30d", description="Periodo de consulta"),
    fecha_desde: Optional[date] = Query(None, description="Fecha de inicio para periodo personalizado"),
    fecha_hasta: Optional[date] = Query(None, description="Fecha de fin para periodo personalizado"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(require_roles(["administrador", "encargado_sucursal"])),
) -> ComparativaSucursalesOut:
    filtros = _construir_filtros(periodo, fecha_desde, fecha_hasta, None)
    return servicio_indicadores.obtener_comparativa_sucursales(db, filtros, usuario)
