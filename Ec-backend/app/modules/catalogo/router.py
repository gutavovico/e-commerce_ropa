"""Router centralizador del paquete de dominio catalogo."""

from fastapi import APIRouter

from modules.catalogo.cu05_consultar_catalogo.router import (
    router as cu05_router,
)
from modules.catalogo.cu06_buscar_filtrar.router import (
    router as cu06_router,
)
from modules.catalogo.cu07_detalle_producto.router import (
    router as cu07_router,
)
from modules.catalogo.cu09_disponibilidad.router import (
    router as cu09_router,
)
from modules.catalogo.cu18_recomendaciones.router import (
    router as cu18_router,
)
from modules.catalogo.cu36_colecciones.router import (
    router as cu36_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de catálogo
router.include_router(cu05_router)
router.include_router(cu06_router)
router.include_router(cu07_router)
router.include_router(cu09_router)
router.include_router(cu18_router)
router.include_router(cu36_router)


