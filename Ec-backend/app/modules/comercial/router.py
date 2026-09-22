"""Router agregador para el paquete de Gestion Comercial de FashionStore."""

from fastapi import APIRouter
from modules.comercial.cu27_promociones.router import router as router_promociones
from modules.comercial.cu28_ventas_reservas.router import (
    router as router_ventas_reservas,
)
from modules.comercial.cu29_indicadores.router import (
    router as router_indicadores,
)

router = APIRouter()
router.include_router(router_promociones)
router.include_router(router_ventas_reservas)
router.include_router(router_indicadores)
