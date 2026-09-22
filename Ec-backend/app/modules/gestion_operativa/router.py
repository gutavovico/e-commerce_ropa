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
from modules.gestion_operativa.cu24_inventario_stock.router import (
    router as router_inventario,
)
from modules.gestion_operativa.cu25_proveedores.router import (
    router as router_proveedores,
)
from modules.gestion_operativa.cu26_inventario_global.router import (
    router as router_inventario_global,
)

router = APIRouter()
router.include_router(router_sucursales)
router.include_router(router_productos)
router.include_router(router_atributos)
router.include_router(router_inventario)
router.include_router(router_proveedores)
router.include_router(router_inventario_global)



