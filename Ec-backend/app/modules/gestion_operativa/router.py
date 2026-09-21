"""Router agregador para el paquete de Gestion Operativa de FashionStore."""

from fastapi import APIRouter

from modules.gestion_operativa.cu21_sucursales_ciudades.router import (
    router as router_sucursales,
)
from modules.gestion_operativa.cu22_prendas_productos.router import (
    router as router_productos,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.router import (
    router as router_atributos,
)

router = APIRouter()
router.include_router(router_sucursales)
router.include_router(router_productos)
router.include_router(router_atributos)


