"""Router centralizador del paquete de dominio reservas."""

from fastapi import APIRouter

from modules.reservas.cu12_reservar_prendas.router import (
    router as cu12_router,
)
from modules.reservas.cu13_consultar_cancelar_reservas.router import (
    router as cu13_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de reservas
router.include_router(cu12_router)
router.include_router(cu13_router)
