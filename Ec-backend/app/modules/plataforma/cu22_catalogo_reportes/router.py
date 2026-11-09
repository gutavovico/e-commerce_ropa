"""Router FastAPI para P2-CU22: Gestionar catálogo de reportes permitidos (Super Administrador)."""

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu22_catalogo_reportes.esquemas import (
    CambiarEstadoCatalogoReporteIn,
    CatalogoReporteGuardarIn,
    CatalogoReporteOut,
    MetadatosCatalogoReportesOut,
)
from modules.plataforma.cu22_catalogo_reportes.servicio import CatalogoReportesServicio
from modules.plataforma.dependencias import exigir_super_administrador

router = APIRouter(
    prefix="/catalogo-reportes",
    tags=["Plataforma · P2-CU22 · Catálogo de Reportes Permitidos IA"],
)


@router.get(
    "",
    response_model=MetadatosCatalogoReportesOut,
    summary="Listar el catálogo de reportes permitidos para la IA y las vistas autorizadas (P2-CU22)",
)
def listar_catalogo_reportes(
    solo_activos: bool = Query(default=False),
    db: Session = Depends(get_db),
    _superadmin: UsuarioORM = Depends(exigir_super_administrador),
) -> MetadatosCatalogoReportesOut:
    return CatalogoReportesServicio.listar_catalogo(db, solo_activos=solo_activos)


@router.post(
    "",
    response_model=CatalogoReporteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Crear un nuevo reporte en el catálogo permitido validando vista y elementos (P2-CU22)",
)
def crear_reporte_catalogo(
    datos: CatalogoReporteGuardarIn,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: UsuarioORM = Depends(exigir_super_administrador),
) -> CatalogoReporteOut:
    ip = request.client.host if request.client else None
    return CatalogoReportesServicio.crear_reporte(db, datos, superadmin, direccion_ip=ip)


@router.put(
    "/{id_reporte}",
    response_model=CatalogoReporteOut,
    summary="Actualizar un reporte existente del catálogo permitido (P2-CU22)",
)
def actualizar_reporte_catalogo(
    id_reporte: int,
    datos: CatalogoReporteGuardarIn,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: UsuarioORM = Depends(exigir_super_administrador),
) -> CatalogoReporteOut:
    ip = request.client.host if request.client else None
    return CatalogoReportesServicio.actualizar_reporte(
        db, id_reporte, datos, superadmin, direccion_ip=ip
    )


@router.patch(
    "/{id_reporte}/estado",
    response_model=CatalogoReporteOut,
    summary="Activar o desactivar un reporte del catálogo sin borrar solicitudes previas (CU22 A3)",
)
def cambiar_estado_reporte_catalogo(
    id_reporte: int,
    datos: CambiarEstadoCatalogoReporteIn,
    request: Request,
    db: Session = Depends(get_db),
    superadmin: UsuarioORM = Depends(exigir_super_administrador),
) -> CatalogoReporteOut:
    ip = request.client.host if request.client else None
    return CatalogoReportesServicio.cambiar_estado_reporte(
        db, id_reporte, datos.activo, superadmin, direccion_ip=ip
    )

