"""Routers del paquete de operación sin conexión (P2-CU14, CU19, CU20 y avisos)."""

from fastapi import APIRouter

from modules.sincronizacion.avisos_cliente.router import router as router_avisos
from modules.sincronizacion.cu14_dispositivo_catalogo.esquemas import DispositivoTokenPushOut
from modules.sincronizacion.cu14_dispositivo_catalogo.router import (
    registrar_token_push,
    router as router_cu14,
)
from modules.sincronizacion.cu19_sincronizar.router import router as router_cu19
from modules.sincronizacion.cu20_conflictos.router import router as router_cu20

router = APIRouter()
router.include_router(router_cu14)
router.include_router(router_cu19)
router.include_router(router_cu20)
router.include_router(router_avisos)

# Alias para cumplir /api/v1/sincronizacion/dispositivos/token-push
router.add_api_route(
    "/sincronizacion/dispositivos/token-push",
    registrar_token_push,
    methods=["POST"],
    response_model=DispositivoTokenPushOut,
    tags=["P2-CU14 Catálogo sin conexión"],
    summary="Asociar token push FCM (alias)",
)
