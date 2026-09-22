"""Router REST y Streaming binario para CU31: Generar reportes ejecutivos y consultas por voz."""

import io
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu31_reportes_voz.esquemas import (
    ComandoVozIn,
    ComandoVozOut,
    FormatoReporteEnum,
    ModuloReporteEnum,
    RangoTemporalEnum,
    ReporteFiltrosIn,
    ReportePrevisualizacionOut,
)
from modules.comercial.cu31_reportes_voz.servicio import ServicioReportesVoz

router = APIRouter(tags=["Gestion Comercial - Reportes Ejecutivos y Voz"])


@router.post(
    "/admin/reportes/interpretar-voz",
    response_model=ComandoVozOut,
    status_code=status.HTTP_200_OK,
    summary="Interpretar comando de voz para reportes",
    description="Parsea la orden hablada transcrita por Web Speech API y extrae modulo, formato, periodo y sucursal.",
)
@router.post(
    "/admin/reportes/interpretar-comando-voz",
    response_model=ComandoVozOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def interpretar_comando_voz(
    datos: ComandoVozIn,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(
        require_roles(["administrador", "admin", "encargado_sucursal"])
    ),
) -> ComandoVozOut:
    """Endpoint de procesamiento semantico de ordenes de voz dictadas."""
    return ServicioReportesVoz.interpretar_comando(
        db=db, peticion=datos, usuario_actual=usuario_actual
    )


@router.post(
    "/admin/reportes/previsualizar",
    response_model=ReportePrevisualizacionOut,
    status_code=status.HTTP_200_OK,
    summary="Previsualizar metricas y conteo del reporte",
    description="Calcula el conteo de registros y resumen preliminar antes de compilar el archivo binario.",
)
def previsualizar_reporte(
    filtros: ReporteFiltrosIn,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(
        require_roles(["administrador", "admin", "encargado_sucursal"])
    ),
) -> ReportePrevisualizacionOut:
    """Endpoint para previsualizacion cuantitativa previa a la exportacion."""
    return ServicioReportesVoz.previsualizar_reporte(
        db=db, filtros=filtros, usuario_actual=usuario_actual
    )


@router.post(
    "/admin/reportes/exportar",
    status_code=status.HTTP_200_OK,
    summary="Exportar reporte ejecutivo (Streaming binario POST)",
    description="Genera y transmite en streaming el archivo binario (Excel, PDF o CSV) segun filtros especificados.",
)
def exportar_reporte_post(
    filtros: ReporteFiltrosIn,
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(
        require_roles(["administrador", "admin", "encargado_sucursal"])
    ),
) -> StreamingResponse:
    """Endpoint principal de emision y streaming de archivos de reporte."""
    contenido, nombre_archivo, media_type = ServicioReportesVoz.generar_archivo_reporte(
        db=db, filtros=filtros, usuario_actual=usuario_actual
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        io.BytesIO(contenido),
        media_type=media_type,
        headers=headers,
    )


@router.get(
    "/admin/reportes/exportar",
    status_code=status.HTTP_200_OK,
    summary="Exportar reporte ejecutivo (Streaming binario GET)",
    description="Permite la descarga directa mediante query parameters en navegadores.",
)
def exportar_reporte_get(
    modulo: ModuloReporteEnum = Query(..., description="Modulo de informacion"),
    formato: FormatoReporteEnum = Query(FormatoReporteEnum.EXCEL, description="Formato binario"),
    periodo: RangoTemporalEnum = Query(RangoTemporalEnum.ESTE_MES, description="Periodo temporal"),
    id_sucursal: Optional[int] = Query(None, description="Sucursal o null para consolidado"),
    db: Session = Depends(get_db),
    usuario_actual: UsuarioORM = Depends(
        require_roles(["administrador", "admin", "encargado_sucursal"])
    ),
) -> StreamingResponse:
    """Variante GET para navegacion y descargas directas via enlace."""
    filtros = ReporteFiltrosIn(
        modulo=modulo,
        formato=formato,
        periodo=periodo,
        id_sucursal=id_sucursal,
    )

    contenido, nombre_archivo, media_type = ServicioReportesVoz.generar_archivo_reporte(
        db=db, filtros=filtros, usuario_actual=usuario_actual
    )

    headers = {
        "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        "Access-Control-Expose-Headers": "Content-Disposition",
    }

    return StreamingResponse(
        io.BytesIO(contenido),
        media_type=media_type,
        headers=headers,
    )
