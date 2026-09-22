"""Configuracion de fixtures para pytest.

AC-14: Fixture de TestClient (httpx) que usa la aplicacion FastAPI
sin necesidad de conexion a base de datos.
"""

import os
import pytest
from fastapi.testclient import TestClient

# Variables de entorno minimas requeridas por Settings (AC-2, AC-17)
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://fashionstore_user:fashionstore_pass@localhost:5432/fashionstore_db",
)
os.environ.setdefault(
    "JWT_SECRET",
    "test-secret-key-for-bootstrap-tests-only-min-32-chars-long",
)

from main import app


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con la aplicacion FastAPI."""
    return TestClient(app)
