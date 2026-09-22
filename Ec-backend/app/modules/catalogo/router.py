"""Router centralizador del paquete de dominio catalogo."""

from fastapi import APIRouter

from modules.catalogo.cu06_buscar_filtrar.router import (
    router as cu06_router,
)
from modules.catalogo.cu24_temporadas_colecciones.router import (
    router as cu24_temporadas_colecciones_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de catalogo
router.include_router(cu06_router)
router.include_router(cu24_temporadas_colecciones_router)
