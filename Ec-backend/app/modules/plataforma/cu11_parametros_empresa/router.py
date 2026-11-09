"""Router de P2-CU11 · Parámetros de la empresa. Solo HTTP."""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu11_parametros_empresa.esquemas import ParametrosEmpresaIn, ParametrosEmpresaOut
from modules.plataforma.cu11_parametros_empresa.servicio import ParametrosEmpresaServicio

router = APIRouter(prefix="/admin/configuracion", tags=["P2-CU11 Parámetros de la empresa"])

_admin = require_roles(["administrador"])


@router.get("", response_model=ParametrosEmpresaOut, summary="Parámetros de la empresa")
def obtener(db: Session = Depends(get_db), _usuario: UsuarioORM = Depends(_admin)) -> ParametrosEmpresaOut:
    return ParametrosEmpresaServicio.obtener(db)


@router.put("", response_model=ParametrosEmpresaOut, summary="Cambiar los parámetros de la empresa")
def actualizar(
    datos: ParametrosEmpresaIn,
    request: Request,
    db: Session = Depends(get_db),
    admin: UsuarioORM = Depends(_admin),
) -> ParametrosEmpresaOut:
    ip = request.client.host if request.client else None
    return ParametrosEmpresaServicio.actualizar(db, datos, actor=admin, ip=ip)
