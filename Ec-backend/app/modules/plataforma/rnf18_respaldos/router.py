"""Router FastAPI de RNF18: respaldo manual de la base por el super administrador."""

from typing import Optional

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.dependencias import exigir_super_administrador
from modules.plataforma.rnf18_respaldos.servicio import RespaldosServicio

router = APIRouter(tags=["Plataforma - Respaldos (RNF18)"])


@router.get(
    "/respaldos",
    summary="Descargar un respaldo SQL de datos de toda la plataforma o de una empresa",
    response_class=Response,
    responses={200: {"content": {"application/sql": {}}}},
)
def descargar_respaldo(
    request: Request,
    id_tenant: Optional[int] = Query(default=None, gt=0, description="Sin valor: toda la plataforma"),
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(exigir_super_administrador),
) -> Response:
    respaldo = RespaldosServicio.generar(
        db, usuario, id_tenant=id_tenant, direccion_ip=request.client.host if request.client else None
    )
    return Response(
        content=respaldo.contenido,
        media_type="application/sql",
        headers={
            "Content-Disposition": f'attachment; filename="{respaldo.nombre_archivo}"',
            "Cache-Control": "no-store",
            "X-Respaldo-Tablas": str(respaldo.tablas),
            "X-Respaldo-Filas": str(respaldo.filas),
        },
    )
