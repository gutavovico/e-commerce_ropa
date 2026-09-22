"""Router centralizador del paquete de dominio compras_pagos."""

from fastapi import APIRouter

from modules.compras_pagos.cu11_gestionar_carrito.router import router as cu11_router
from modules.compras_pagos.cu15_comprar_plataforma.router import router as cu15_router

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de compras y pagos
router.include_router(cu11_router)
router.include_router(cu15_router)
