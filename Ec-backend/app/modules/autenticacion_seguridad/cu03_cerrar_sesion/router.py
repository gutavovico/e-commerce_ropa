"""Router HTTP para el caso de uso CU03: Cerrar Sesión (Logout)."""

from fastapi import APIRouter, Depends, status
from core.deps import get_current_user, oauth2_scheme
from modules.autenticacion_seguridad.cu03_cerrar_sesion.esquemas import LogoutOut
from modules.autenticacion_seguridad.cu03_cerrar_sesion.servicio import ServicioLogout
from modules.autenticacion_seguridad.modelos import UsuarioORM

router = APIRouter(tags=["Autenticacion y Seguridad"])


@router.post(
    "/logout",
    response_model=LogoutOut,
    status_code=status.HTTP_200_OK,
    summary="Cerrar sesión activa y revocar token",
    description="Invalida el token Bearer JWT en el servidor y finaliza la sesión activa del usuario.",
)
def logout(
    token: str = Depends(oauth2_scheme),
    usuario: UsuarioORM = Depends(get_current_user),
) -> LogoutOut:
    """Ejecuta el cierre de sesión e invalidación del token en la lista negra."""
    return ServicioLogout.cerrar_sesion(token=token, usuario=usuario)
