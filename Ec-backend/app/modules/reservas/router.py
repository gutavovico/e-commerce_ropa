"""Router centralizador del paquete de dominio reservas."""

from fastapi import APIRouter

from modules.reservas.cu12_reservar_prendas.router import (
    router as cu12_router,
)
from modules.reservas.cu18_entrega_reserva.router import (
    router as cu18_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de reservas
router.include_router(cu12_router)
router.include_router(cu18_router)

