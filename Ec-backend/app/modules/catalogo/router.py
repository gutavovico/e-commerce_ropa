"""Router centralizador del paquete de dominio catalogo."""

from fastapi import APIRouter

from modules.catalogo.cu06_buscar_filtrar.router import (
    router as cu06_router,
)

router = APIRouter()

# Montar endpoints de cada caso de uso del paquete de catálogo
router.include_router(cu06_router)
