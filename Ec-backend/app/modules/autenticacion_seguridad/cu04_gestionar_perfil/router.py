"""Router HTTP de FastAPI para CU04: Gestionar Perfil del Cliente."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from core.deps import require_roles
from modules.autenticacion_seguridad.cu04_gestionar_perfil.esquemas import (
    PerfilClienteOut,
    PerfilClienteUpdateIn,
)
from modules.autenticacion_seguridad.cu04_gestionar_perfil.servicio import (
    ServicioPerfilCliente,
)
from modules.autenticacion_seguridad.modelos import UsuarioORM

router = APIRouter(prefix="/perfil", tags=["Perfil del Cliente"])


@router.get(
    "",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    summary="Consultar perfil del cliente autenticado",
    description="Devuelve la información de cuenta, perfil de cliente y resumen de membresía atelier.",
)
@router.get(
    "/",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def consultar_perfil(
    usuario: UsuarioORM = Depends(require_roles(["cliente"])),
    db: Session = Depends(get_db),
) -> PerfilClienteOut:
    """Consulta el perfil del usuario cliente identificado por el token JWT."""
    return ServicioPerfilCliente.obtener_perfil(db, usuario)


@router.patch(
    "",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    summary="Actualizar parcialmente datos del perfil del cliente",
    description="Permite modificar nombres, teléfono, talla preferida, género y suscripción.",
)
@router.patch(
    "/",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.put(
    "",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
@router.put(
    "/",
    response_model=PerfilClienteOut,
    status_code=status.HTTP_200_OK,
    include_in_schema=False,
)
def actualizar_perfil(
    datos: PerfilClienteUpdateIn,
    usuario: UsuarioORM = Depends(require_roles(["cliente"])),
    db: Session = Depends(get_db),
) -> PerfilClienteOut:
    """Aplica y persiste cambios en los datos personales y preferencias del cliente."""
    return ServicioPerfilCliente.actualizar_perfil(db, usuario, datos)
