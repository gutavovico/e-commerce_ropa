"""Router del perfil del empleado. Solo HTTP."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.cu04_perfil_empleado.esquemas import (
    CambioContrasenaIn,
    PerfilEmpleadoActualizarIn,
    PerfilEmpleadoOut,
)
from modules.autenticacion_seguridad.cu04_perfil_empleado.servicio import PerfilEmpleadoServicio
from modules.autenticacion_seguridad.modelos import UsuarioORM

router = APIRouter(prefix="/mi-perfil-empleado", tags=["Perfil del empleado"])

_empleado = require_roles(["administrador", "encargado_sucursal", "cajero"])


def _ip(request: Request) -> str | None:
    return request.client.host if request.client else None


@router.get("", response_model=PerfilEmpleadoOut, summary="Datos, empresa y sucursales del empleado")
def obtener(db: Session = Depends(get_db), usuario: UsuarioORM = Depends(_empleado)) -> PerfilEmpleadoOut:
    return PerfilEmpleadoServicio.obtener(db, usuario)


@router.patch("", response_model=PerfilEmpleadoOut, summary="Cambiar nombre, apellidos o teléfono")
def actualizar(
    datos: PerfilEmpleadoActualizarIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_empleado),
) -> PerfilEmpleadoOut:
    return PerfilEmpleadoServicio.actualizar(db, usuario, datos, _ip(request))


@router.post("/contrasena", status_code=status.HTTP_204_NO_CONTENT, summary="Cambiar la propia contraseña")
def cambiar_contrasena(
    datos: CambioContrasenaIn,
    request: Request,
    db: Session = Depends(get_db),
    usuario: UsuarioORM = Depends(_empleado),
) -> None:
    PerfilEmpleadoServicio.cambiar_contrasena(db, usuario, datos, _ip(request))
