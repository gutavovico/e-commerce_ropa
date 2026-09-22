"""Punto de entrada de la aplicacion FashionStore Backend.

Crea la instancia de FastAPI, configura CORS, registra los exception handlers
para la jerarquia de DomainError, y expone los endpoints base (health, root).
"""
import sys
from pathlib import Path

# Permite resolver imports como 'from core...' y 'from modules...' directamente
sys.path.insert(0, str(Path(__file__).resolve().parent))

import logging
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("fashionstore.api")

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core.config import settings
from core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
)

app = FastAPI(
    title="FashionStore API",
    description="Backend API del e-commerce omnicanal de FashionStore",
    version="0.1.0",
)

RESPUESTA_ERROR_INTERNO = {
    "detail": "Ha ocurrido un error interno en el servidor. El equipo ha sido notificado.",
    "code": "ERROR_INTERNO",
}


# --- Captura de errores no controlados ---
# IMPORTANTE: debe registrarse ANTES que el CORSMiddleware. `add_middleware` antepone cada
# middleware, así que el último en registrarse queda por fuera; declarando este primero, CORS
# acaba envolviéndolo y la respuesta 500 que genera sí recibe `Access-Control-Allow-Origin`.
#
# No basta con `@app.exception_handler(Exception)`: Starlette monta ese manejador en el
# `ServerErrorMiddleware`, que envuelve a todos los middlewares de usuario (CORS incluido). Su
# respuesta sale sin cabeceras CORS y el navegador la reporta como un genérico "Failed to fetch",
# indistinguible de un backend caído. Ese fue precisamente el síntoma que ocultó, en la web y en
# la app Flutter, un simple desajuste de nombres de columna contra PostgreSQL.
@app.middleware("http")
async def capturar_errores_no_controlados(request: Request, call_next):
    """Traduce cualquier excepción imprevista a un 500 JSON que atraviesa el CORSMiddleware."""
    try:
        return await call_next(request)
    except Exception as exc:  # noqa: BLE001 - red de seguridad deliberada
        logger.exception(
            "Error no controlado en %s %s", request.method, request.url.path, exc_info=exc
        )
        return JSONResponse(status_code=500, content=RESPUESTA_ERROR_INTERNO)


# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_origin_regex=settings.CORS_ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Exception handlers ---


def _domain_error_response(status_code: int, exc: DomainError) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"detail": exc.message, "code": exc.code},
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(_request: Request, exc: NotFoundError) -> JSONResponse:
    return _domain_error_response(404, exc)


@app.exception_handler(ConflictError)
async def conflict_handler(_request: Request, exc: ConflictError) -> JSONResponse:
    return _domain_error_response(409, exc)


@app.exception_handler(AuthenticationError)
async def authentication_handler(_request: Request, exc: AuthenticationError) -> JSONResponse:
    return _domain_error_response(401, exc)


@app.exception_handler(AuthorizationError)
async def authorization_handler(_request: Request, exc: AuthorizationError) -> JSONResponse:
    return _domain_error_response(403, exc)


@app.exception_handler(DomainError)
async def domain_error_handler(_request: Request, exc: DomainError) -> JSONResponse:
    return _domain_error_response(400, exc)


@app.exception_handler(Exception)
async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Último recurso para fallos ocurridos por encima de `capturar_errores_no_controlados`.

    Starlette monta este manejador en el `ServerErrorMiddleware`, la capa más externa, así que su
    respuesta no lleva cabeceras CORS. Sirve únicamente para errores del propio CORSMiddleware,
    que el middleware interno no puede interceptar; el caso normal lo cubre aquel. Su valor aquí
    es garantizar que jamás se filtre un traceback al cliente.
    """
    logger.exception(
        "Error no controlado (capa externa) en %s %s",
        request.method,
        request.url.path,
        exc_info=exc,
    )
    return JSONResponse(status_code=500, content=RESPUESTA_ERROR_INTERNO)


# --- Schemas ---


class HealthResponse(BaseModel):
    status: str = Field(default="online", description="Estado del servicio")
    service: str = Field(default="fashionstore-backend", description="Identificador del servicio")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Fecha y hora UTC actual en formato ISO-8601",
    )


from modules.autenticacion_seguridad.cu04_gestionar_perfil.router import (
    router as router_perfil,
)
from modules.autenticacion_seguridad.router import router as router_autenticacion
from modules.catalogo.router import router as router_catalogo
from modules.compras_pagos.router import router as router_compras_pagos
from modules.reservas.router import router as router_reservas

app.include_router(router_autenticacion, prefix="/api/v1")
app.include_router(router_perfil, prefix="/api/v1")
app.include_router(router_catalogo, prefix="/api/v1")
app.include_router(router_reservas, prefix="/api/v1")
app.include_router(router_compras_pagos, prefix="/api/v1")


@app.get("/api/v1/health", response_model=HealthResponse, tags=["Health"])
async def get_health() -> HealthResponse:
    """Endpoint de comprobacion de estado del backend."""
    return HealthResponse()


@app.get("/", tags=["Root"])
async def root() -> dict:
    """Informacion basica del servicio."""
    return {
        "service": "FashionStore API",
        "version": "0.1.0",
        "docs": "/docs",
        "health": "/api/v1/health",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
