"""Router agregador para el paquete de Gestion Comercial de FashionStore."""

from fastapi import APIRouter
from modules.comercial.cu27_promociones.router import router as router_promociones
from modules.comercial.cu28_ventas_reservas.router import (
    router as router_ventas_reservas,
)
from modules.comercial.cu29_indicadores.router import (
    router as router_indicadores,
)
from modules.comercial.cu31_reportes_voz.router import (
    router as router_reportes_voz,
)
from modules.comercial.cu21_reportes_ia.router import (
    router as router_reportes_ia,
)
from modules.comercial.cu23_cu25_aprendizaje_ml.router import (
    router as router_aprendizaje_ml,
)

router = APIRouter()
router.include_router(router_promociones)
router.include_router(router_ventas_reservas)
router.include_router(router_indicadores)
router.include_router(router_reportes_voz)
router.include_router(router_reportes_ia)
router.include_router(router_aprendizaje_ml)

