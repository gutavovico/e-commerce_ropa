"""Pruebas para el health check y los exception handlers de dominio.

Criterios de aceptacion:
- AC-10: GET /api/v1/health retorna 200 con status, service, timestamp.
- AC-15: Test de health check verificado.
- AC-9: Exception handlers traducen DomainError y sus subclases a respuestas JSON
  con codigo HTTP adecuado y formato {"detail": ..., "code": ...}.
"""

from datetime import datetime

from app.main import app
from core.errors import (
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DomainError,
    NotFoundError,
)


# Rutas de prueba para verificar exception handlers sin depender de endpoints de dominio
@app.get("/_test/errors/not-found")
async def _trigger_not_found():
    raise NotFoundError("Recurso solicitado no existe")


@app.get("/_test/errors/conflict")
async def _trigger_conflict():
    raise ConflictError("Ya existe un registro con este identificador")


@app.get("/_test/errors/auth")
async def _trigger_auth():
    raise AuthenticationError("Credenciales invalidas o ausentes")


@app.get("/_test/errors/forbidden")
async def _trigger_forbidden():
    raise AuthorizationError("No tiene permisos para realizar esta accion")


@app.get("/_test/errors/domain")
async def _trigger_domain():
    raise DomainError("Error generico de regla de negocio")


# --- Tests de Health Check ---


def test_health_check_returns_200_and_expected_fields(client):
    """AC-10, AC-15: GET /api/v1/health responde 200 con status, service y timestamp ISO-8601."""
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "online"
    assert data["service"] == "fashionstore-backend"
    assert "timestamp" in data

    # Validar que timestamp sea una fecha ISO-8601 valida
    parsed_date = datetime.fromisoformat(data["timestamp"])
    assert parsed_date is not None


def test_root_endpoint_returns_service_info(client):
    """Verifica que el endpoint raiz responde 200 con informacion del servicio."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "FashionStore API"
    assert data["health"] == "/api/v1/health"
    assert data["docs"] == "/docs"


# --- Tests de Exception Handlers (AC-9) ---


def test_not_found_error_handler(client):
    """AC-9: NotFoundError se traduce a 404 con formato {"detail": ..., "code": "NOT_FOUND"}."""
    response = client.get("/_test/errors/not-found")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Recurso solicitado no existe"
    assert data["code"] == "NOT_FOUND"


def test_conflict_error_handler(client):
    """AC-9: ConflictError se traduce a 409 con formato {"detail": ..., "code": "CONFLICT"}."""
    response = client.get("/_test/errors/conflict")

    assert response.status_code == 409
    data = response.json()
    assert data["detail"] == "Ya existe un registro con este identificador"
    assert data["code"] == "CONFLICT"


def test_authentication_error_handler(client):
    """AC-9: AuthenticationError se traduce a 401 con formato {"detail": ..., "code": "NOT_AUTHENTICATED"}."""
    response = client.get("/_test/errors/auth")

    assert response.status_code == 401
    data = response.json()
    assert data["detail"] == "Credenciales invalidas o ausentes"
    assert data["code"] == "NOT_AUTHENTICATED"


def test_authorization_error_handler(client):
    """AC-9: AuthorizationError se traduce a 403 con formato {"detail": ..., "code": "FORBIDDEN"}."""
    response = client.get("/_test/errors/forbidden")

    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "No tiene permisos para realizar esta accion"
    assert data["code"] == "FORBIDDEN"


def test_domain_error_base_handler(client):
    """AC-9: DomainError generico se traduce a 400 con formato {"detail": ..., "code": "DOMAIN_ERROR"}."""
    response = client.get("/_test/errors/domain")

    assert response.status_code == 400
    data = response.json()
    assert data["detail"] == "Error generico de regla de negocio"
    assert data["code"] == "DOMAIN_ERROR"
