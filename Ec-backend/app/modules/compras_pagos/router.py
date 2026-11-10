"""Router centralizador del paquete de dominio compras_pagos."""

from fastapi import APIRouter

from modules.compras_pagos.cu11_gestionar_carrito.router import router as cu11_router
from modules.compras_pagos.cu15_comprar_plataforma.router import router as cu15_router
from modules.compras_pagos.cu16_realizar_pago.router import router as cu16_router
from modules.compras_pagos.cu17_historial_compras.router import router as cu17_router
from modules.compras_pagos.cu18_cambio_prenda.router import router as cu18_router
from modules.compras_pagos.cu31_cu32_punto_venta.router import router as cu31_cu32_router

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de compras y pagos
router.include_router(cu11_router)
router.include_router(cu15_router)
router.include_router(cu16_router)
router.include_router(cu17_router)
router.include_router(cu18_router)
router.include_router(cu31_cu32_router)
