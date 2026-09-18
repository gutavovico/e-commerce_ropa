"""Punto de entrada de la aplicacion FashionStore Backend.

Crea la instancia de FastAPI, configura CORS, registra los exception handlers
para la jerarquia de DomainError, y expone los endpoints base (health, root).
"""

from datetime import datetime, timezone

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

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
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


# --- Schemas ---


class HealthResponse(BaseModel):
    status: str = Field(default="online", description="Estado del servicio")
    service: str = Field(default="fashionstore-backend", description="Identificador del servicio")
    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="Fecha y hora UTC actual en formato ISO-8601",
    )


# --- Endpoints ---


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
