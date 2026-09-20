"""Router FastAPI para CU33 - Recuperar Acceso de Cuenta / Recuperar Contraseña."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.orm import Session

from core.database import get_db
from modules.autenticacion_seguridad.cu33_recuperar_acceso.esquemas import (
    RestablecerPasswordIn,
    RestablecerPasswordOut,
    SolicitarCodigoIn,
    SolicitarCodigoOut,
)
from modules.autenticacion_seguridad.cu33_recuperar_acceso.servicio import (
    servicio_recuperar_password,
)

router = APIRouter(
    prefix="/recuperar-password",
    tags=["Autenticacion y Seguridad"],
)


@router.post(
    "/solicitar",
    response_model=SolicitarCodigoOut,
    status_code=status.HTTP_200_OK,
    summary="Solicitar código de verificación para recuperar contraseña",
    description=(
        "Genera un código OTP temporal de 6 dígitos y lo envía al correo del usuario vía SMTP. "
        "Aplica protección anti-enumeración respondiendo siempre con 200 OK."
    ),
)
async def solicitar_codigo(
    datos: SolicitarCodigoIn,
    request: Request,
    db: Session = Depends(get_db),
) -> SolicitarCodigoOut:
    """Punto de entrada público para la solicitud de código OTP."""
    ip_solicitante = request.client.host if request.client else None
    return await servicio_recuperar_password.solicitar_codigo(
        db=db,
        email=datos.email,
        ip_solicitante=ip_solicitante,
    )


@router.post(
    "/restablecer",
    response_model=RestablecerPasswordOut,
    status_code=status.HTTP_200_OK,
    summary="Restablecer contraseña mediante código de verificación OTP",
    description=(
        "Valida el código numérico de 6 dígitos contra el hash en base de datos, "
        "comprueba expiración y límite de intentos, y actualiza la contraseña con Argon2id."
    ),
)
def restablecer_password(
    datos: RestablecerPasswordIn,
    db: Session = Depends(get_db),
) -> RestablecerPasswordOut:
    """Punto de entrada público para el restablecimiento atómico de contraseña."""
    return servicio_recuperar_password.restablecer_password(
        db=db,
        datos=datos,
    )
