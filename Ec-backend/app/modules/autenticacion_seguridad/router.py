"""Router centralizador del paquete de dominio autenticacion_seguridad."""

from fastapi import APIRouter

from modules.autenticacion_seguridad.cu01_registrarse.router import (
    router as cu01_router,
)
from modules.autenticacion_seguridad.cu02_iniciar_sesion.router import (
    router as cu02_router,
)

router = APIRouter(prefix="/autenticacion", tags=["Autenticacion y Seguridad"])

# Montar endpoints de cada caso de uso del paquete
router.include_router(cu01_router)
router.include_router(cu02_router)
