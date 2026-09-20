"""Pruebas unitarias y de integración para CU03: Cerrar Sesión (Logout)."""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.security import create_access_token
from core.token_blacklist import TokenBlacklistService, token_blacklist
from main import app
from modules.autenticacion_seguridad.cu03_cerrar_sesion.esquemas import LogoutOut
from modules.autenticacion_seguridad.cu03_cerrar_sesion.servicio import ServicioLogout
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM


@pytest.fixture(autouse=True)
def limpiar_blacklist():
    """Reinicia la lista negra de tokens antes y después de cada prueba."""
    token_blacklist.reiniciar()
    yield
    token_blacklist.reiniciar()


# --- 1. Pruebas Unitarias del Servicio TokenBlacklistService ---


def test_blacklist_revocar_y_verificar():
    """Comprueba que un token revocado sea detectado inmediatamente."""
    blacklist = TokenBlacklistService()
    token = "test_token_secreto_alta_costura"

    assert not blacklist.esta_revocado(token)
    blacklist.revocar_token(token)
    assert blacklist.esta_revocado(token)


def test_blacklist_limpieza_expirados():
    """Verifica que un token cuya expiración ya ocurrió no se considere revocado."""
    blacklist = TokenBlacklistService()
    token = "test_token_expirado"
    pasado = datetime.now(timezone.utc).timestamp() - 100.0

    blacklist.revocar_token(token, exp_timestamp=pasado)
    assert not blacklist.esta_revocado(token)


# --- 2. Pruebas Unitarias de Esquema Pydantic y Servicio ---


def test_esquema_logout_out_defaults():
    """Verifica los valores por defecto del esquema LogoutOut."""
    esquema = LogoutOut()
    assert esquema.mensaje == "Sesión finalizada exitosamente."
    assert esquema.revocado is True
    assert esquema.codigo == "SESION_FINALIZADA"


def test_servicio_logout_revoca_token():
    """Verifica que ServicioLogout.cerrar_sesion revoque el token en la blacklist."""
    usuario = UsuarioORM(
        id_usuario=999,
        email="cliente.test@atelier.com",
        nombres="Elena",
        apellidos="Rostova",
        rol="cliente",
        activo=True,
    )
    token = create_access_token({"sub": "999"})

    assert not token_blacklist.esta_revocado(token)
    res = ServicioLogout.cerrar_sesion(token=token, usuario=usuario)

    assert res.revocado is True
    assert "cliente.test@atelier.com" in res.mensaje
    assert token_blacklist.esta_revocado(token)


# --- 3. Pruebas de Integración HTTP con TestClient ---


def _mock_usuario():
    cliente = ClienteORM(
        id_cliente=1001,
        fecha_nacimiento=None,
        genero="femenino",
        talla_preferida="M",
        ciudad_preferida=None,
        acepta_marketing=True,
    )
    usuario = UsuarioORM(
        id_usuario=1001,
        email="madame.logout@fashionstore.com",
        password_hash="hash_mock",
        nombres="Madame",
        apellidos="Logout",
        telefono="+34 600 000 000",
        rol="cliente",
        activo=True,
        fecha_registro=datetime(2022, 1, 1, tzinfo=timezone.utc),
    )
    usuario.cliente = cliente
    return usuario


def test_logout_exitoso_revoca_token_en_servidor():
    """Flujo completo de logout:

    1. Token válido accede a endpoints protegidos.
    2. POST /api/v1/autenticacion/logout responde 200 OK y revoca el token.
    3. Intento posterior de consumir la API con el mismo token es rechazado con 401 TOKEN_REVOCADO.
    """
    client = TestClient(app)
    usuario = _mock_usuario()
    token = create_access_token({"sub": "1001"})

    # Sobrescribir get_db para resolver el usuario mockeado
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = usuario
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # 1. Petición POST a /logout con token válido
        headers = {"Authorization": f"Bearer {token}"}
        resp = client.post("/api/v1/autenticacion/logout", headers=headers)

        assert resp.status_code == 200
        data = resp.json()
        assert data["revocado"] is True
        assert data["codigo"] == "SESION_FINALIZADA"
        assert "madame.logout@fashionstore.com" in data["mensaje"]

        # 2. Reintento inmediato con el mismo token debe ser rechazado
        resp_reintento = client.post("/api/v1/autenticacion/logout", headers=headers)
        assert resp_reintento.status_code == 401
        data_error = resp_reintento.json()
        assert data_error["code"] == "TOKEN_REVOCADO"

        # 3. Intento de acceder al perfil con el token revocado también debe ser rechazado
        resp_perfil = client.get("/api/v1/perfil", headers=headers)
        assert resp_perfil.status_code == 401
        assert resp_perfil.json()["code"] == "TOKEN_REVOCADO"

    finally:
        app.dependency_overrides.clear()


def test_logout_sin_token_retorna_401():
    """Llamar a logout sin cabecera Authorization responde 401 TOKEN_INVALIDO."""
    client = TestClient(app)
    resp = client.post("/api/v1/autenticacion/logout")

    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_INVALIDO"


def test_logout_con_token_invalido_retorna_401():
    """Llamar a logout con token malformado responde 401 TOKEN_INVALIDO."""
    client = TestClient(app)
    headers = {"Authorization": "Bearer token_falso_o_corrupto_123"}
    resp = client.post("/api/v1/autenticacion/logout", headers=headers)

    assert resp.status_code == 401
    assert resp.json()["code"] == "TOKEN_INVALIDO"
