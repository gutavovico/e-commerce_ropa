"""Router agregador del paquete Plataforma (P2-CU05 a P2-CU08)."""

from fastapi import APIRouter

from modules.plataforma.cu05_empresas_supervision.router import (
    router as router_cu05_empresas_supervision,
)
from modules.plataforma.cu06_planes_funcionalidades.router import (
    router as router_cu06_planes_funcionalidades,
)
from modules.plataforma.cu07_suscripciones.router import (
    router as router_cu07_suscripciones,
)
from modules.plataforma.cu08_catalogos_globales.router import (
    router as router_cu08_catalogos_globales,
)
from modules.plataforma.cu09_cu10_suscripcion_empresa.router import (
    router as router_cu09_cu10_suscripcion_empresa,
)
from modules.plataforma.cu22_catalogo_reportes.router import (
    router as router_cu22_catalogo_reportes,
)
from modules.plataforma.rnf18_respaldos.router import router as router_rnf18_respaldos

router = APIRouter(prefix="/plataforma")

router.include_router(router_cu05_empresas_supervision)
router.include_router(router_cu06_planes_funcionalidades)
router.include_router(router_cu07_suscripciones)
router.include_router(router_cu08_catalogos_globales)
router.include_router(router_cu09_cu10_suscripcion_empresa)
router.include_router(router_cu22_catalogo_reportes)
router.include_router(router_rnf18_respaldos)

