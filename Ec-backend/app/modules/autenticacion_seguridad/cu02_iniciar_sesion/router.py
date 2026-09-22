from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.cu02_iniciar_sesion.esquemas import (
    LoginIn,
    LoginOut,
)
from modules.autenticacion_seguridad.cu02_iniciar_sesion.servicio import (
    ServicioAutenticarLogin,
)

router = APIRouter()
servicio_login = ServicioAutenticarLogin()


@router.post(
    "/login",
    response_model=LoginOut,
    status_code=status.HTTP_200_OK,
    summary="Iniciar sesion de usuario",
    description=(
        "Autentica a un usuario existente mediante sus credenciales (email y password). "
        "Verifica la clave con Argon2id, actualiza el timestamp de ultimo acceso y retorna "
        "un token Bearer JWT con sus claims de autorizacion."
    ),
)
def iniciar_sesion(
    datos: LoginIn,
    request: Request,
    db: Session = Depends(get_db),
) -> LoginOut:
    """Endpoint publico para inicio de sesion (login)."""
    ip_cliente = request.client.host if request.client else None
    return servicio_login.autenticar_usuario(db=db, datos=datos, direccion_ip=ip_cliente)
