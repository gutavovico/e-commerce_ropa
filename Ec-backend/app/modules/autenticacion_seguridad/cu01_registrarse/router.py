"""Router HTTP de FastAPI para CU01: Registrarse."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.cu01_registrarse.esquemas import (
    RegistroClienteIn,
    RegistroClienteOut,
)
from modules.autenticacion_seguridad.cu01_registrarse.servicio import (
    ServicioRegistroUsuario,
)

router = APIRouter()
servicio_registro = ServicioRegistroUsuario()


@router.post(
    "/registrarse",
    response_model=RegistroClienteOut,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una nueva cuenta de cliente",
    description=(
        "Permite el auto-registro de un nuevo cliente. Valida la unicidad del correo, "
        "hashea la contrasena, crea el perfil extendido de cliente de forma atomica "
        "y emite un token JWT de acceso inmediato."
    ),
)
def registrar_cliente(
    datos: RegistroClienteIn,
    db: Session = Depends(get_db),
) -> RegistroClienteOut:
    """Endpoint publico para registro de clientes."""
    return servicio_registro.registrar_cliente(db=db, datos=datos)
