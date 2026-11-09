"""Router FastAPI para P2-CU21: Generar reporte con IA (lenguaje natural, Bolivianos Bs./BOB y exportación PDF/Excel)."""

from typing import Literal

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu21_reportes_ia.esquemas import (
    ContextoReportesIaEmpresaOut,
    GenerarReporteIaIn,
    SolicitudReporteIaHistorialOut,
    SolicitudReporteIaResultadoOut,
)
from modules.comercial.cu21_reportes_ia.servicio import ReportesIaServicio

router = APIRouter(
    prefix="/reportes-ia",
    tags=["Comercial · P2-CU21 · Generar Reporte con IA (Plan Profesional)"],
)

exigir_administrador_empresa = require_roles(["administrador", "admin"])


@router.get(
    "/catalogo-activo",
    response_model=ContextoReportesIaEmpresaOut,
    summary="Obtener el catálogo activo de reportes permitidos (CU22), sucursales, categorías y tipo de cambio en Bolivianos (P2-CU21)",
)
def obtener_catalogo_activo_reportes_ia(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> ContextoReportesIaEmpresaOut:
    return ReportesIaServicio.obtener_contexto_empresa(db, usuario)


@router.post(
    "/generar",
    response_model=SolicitudReporteIaResultadoOut,
    summary="Interpretar petición en lenguaje natural (texto o voz) y generar reporte controlado con montos en Bolivianos Bs./BOB (P2-CU21)",
)
def generar_reporte_ia(
    datos: GenerarReporteIaIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> SolicitudReporteIaResultadoOut:
    ip = request.client.host if request.client else None
    return ReportesIaServicio.generar_reporte(db, datos, usuario, direccion_ip=ip)


@router.get(
    "/historial",
    response_model=list[SolicitudReporteIaHistorialOut],
    summary="Listar el historial de solicitudes de reportes con IA de la empresa (P2-CU21, RN47)",
)
def listar_historial_reportes_ia(
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> list[SolicitudReporteIaHistorialOut]:
    return ReportesIaServicio.listar_historial(db, usuario)


@router.get(
    "/solicitudes/{id_solicitud}/exportar",
    summary="Exportar un reporte generado con IA a PDF o Excel (XLSX) registrando la exportación (P2-CU21, RN48)",
)
def exportar_reporte_ia(
    id_solicitud: int,
    request: Request,
    formato: Literal["pdf", "excel"] = Query(default="pdf"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_administrador_empresa),
) -> Response:
    ip = request.client.host if request.client else None
    contenido, media_type, nombre_archivo = ReportesIaServicio.exportar_solicitud(
        db,
        id_solicitud=id_solicitud,
        formato=formato,
        usuario=usuario,
        direccion_ip=ip,
    )
    return Response(
        content=contenido,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{nombre_archivo}"',
        },
    )

