"""Pruebas unitarias y de integración para CU10: Utilizar Vestidor Virtual (Dos Motores).

Verifica:
- POST /api/v1/vestidor/token: autenticación requerida (401), sin cuerpo en la petición,
  entrega de token efímero de conexión (200 OK) y fallback por servicio Decart caído/sin créditos (503).
- POST /api/v1/vestidor/sesion: persistencia de sesión AR (201 Created) con motor 'local' o 'ia',
  validación de modelo_ar_url existente en la prenda (422), rechazo si no existe producto (404),
  y validación de esquemas (motor inválido, duración negativa).
- PATCH /api/v1/vestidor/sesion/{id}: actualización de interés comercial y captura fotográfica.
"""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.errors import ServiceUnavailableError
from integrations.decart_service import DecartService
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.cu10_vestidor_virtual.esquemas import (
    SesionVestidorCrearIn,
    TokenVestidorDecartOut,
)
from modules.catalogo.cu10_vestidor_virtual.modelos import SesionVestidorORM
from modules.catalogo.cu10_vestidor_virtual.servicio import ServicioProcesarAR
from modules.catalogo.modelos import ProductoORM


@pytest.fixture
def client():
    """Cliente de pruebas HTTP contra la app de FastAPI."""
    return TestClient(app)


def _crear_usuario_cliente_fixture(id_usuario: int = 10, id_cliente: int = 10) -> UsuarioORM:
    """Crea una entidad UsuarioORM con perfil de cliente."""
    cliente = ClienteORM(
        id_cliente=id_cliente,
        talla_preferida="38",
        acepta_marketing=True,
    )
    usuario = UsuarioORM(
        id_usuario=id_usuario,
        email="elena.de.troya@fashionstore.com",
        password_hash="argon2id$mockhash",
        nombres="Elena",
        apellidos="Vasilyeva",
        rol="cliente",
        activo=True,
        cliente=cliente,
    )
    return usuario


def _crear_producto_fixture(
    id_producto: int = 42,
    nombre: str = "Vestido Escultural de Noche en Seda",
    modelo_ar_url: str | None = "https://fashionstore.com/ar/vestido_seda_2d.png",
) -> ProductoORM:
    """Crea una entidad ProductoORM simulada."""
    return ProductoORM(
        id_producto=id_producto,
        id_categoria=1,
        id_coleccion=1,
        nombre=nombre,
        descripcion="Vestido exclusivo con corte sirena.",
        precio_base=Decimal("1200.00"),
        modelo_ar_url=modelo_ar_url,
        activo=True,
    )


# ==============================================================================
# 1. PRUEBAS DE ENDPOINT: POST /api/v1/vestidor/token (Prueba 3b)
# ==============================================================================


def test_obtener_token_decart_sin_autenticacion(client):
    """AC-1: El endpoint debe rechazar peticiones sin token Bearer JWT con 401."""
    app.dependency_overrides.clear()
    response = client.post("/api/v1/vestidor/token")
    assert response.status_code == 401
    data = response.json()
    assert data["code"] == "TOKEN_INVALIDO" or "detail" in data


def test_obtener_token_decart_exitoso_sin_cuerpo(client):
    """AC-2: Cliente autenticado obtiene token efímero de conexión sin enviar cuerpo en la petición (200 OK)."""
    usuario = _crear_usuario_cliente_fixture()
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    # Mock del cliente DecartService
    with patch(
        "modules.catalogo.cu10_vestidor_virtual.servicio.decart_service.generar_token_cliente"
    ) as mock_decart:
        mock_decart.return_value = {
            "token": "decart_client_token_9938bfa7c144a",
            "expira_en_segundos": 60,
            "servicio": "decart_lucy_vton_720p",
        }

        # Petición POST sin cuerpo (cuerpo vacío)
        response = client.post("/api/v1/vestidor/token")

        assert response.status_code == 200
        data = response.json()
        assert data["token"] == "decart_client_token_9938bfa7c144a"
        assert data["expira_en_segundos"] == 60
        assert data["servicio"] == "decart_lucy_vton_720p"

    app.dependency_overrides.clear()


@pytest.mark.parametrize(
    ("url", "restringir_esperado"),
    [
        ("/api/v1/vestidor/token", True),
        ("/api/v1/vestidor/token?canal=web", True),
        ("/api/v1/vestidor/token?canal=movil", False),
    ],
)
def test_obtener_token_decart_propaga_canal(client, url, restringir_esperado):
    """El canal móvil pide el token sin restricción de origen (WebView con Origin null)."""
    app.dependency_overrides[get_current_user] = lambda: _crear_usuario_cliente_fixture()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch(
        "modules.catalogo.cu10_vestidor_virtual.servicio.decart_service.generar_token_cliente"
    ) as mock_decart:
        mock_decart.return_value = {"token": "tok", "expira_en_segundos": 60, "servicio": "decart_lucy_vton_720p"}

        response = client.post(url)

        assert response.status_code == 200
        mock_decart.assert_called_once_with(restringir_origenes=restringir_esperado)

    app.dependency_overrides.clear()


def test_obtener_token_decart_canal_desconocido_422(client):
    app.dependency_overrides[get_current_user] = lambda: _crear_usuario_cliente_fixture()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    response = client.post("/api/v1/vestidor/token?canal=tv")

    assert response.status_code == 422
    app.dependency_overrides.clear()


def test_obtener_token_decart_servicio_no_disponible_503(client):
    """AC-3: Si Decart falla, no tiene saldo o no está configurado, retorna 503 para activar fallback."""
    usuario = _crear_usuario_cliente_fixture()
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch(
        "modules.catalogo.cu10_vestidor_virtual.servicio.decart_service.generar_token_cliente"
    ) as mock_decart:
        mock_decart.side_effect = ServiceUnavailableError(
            "El servicio externo Decart no está disponible o carece de saldo de créditos.",
            code="DECART_NO_DISPONIBLE",
        )

        response = client.post("/api/v1/vestidor/token")

        assert response.status_code == 503
        data = response.json()
        assert data["code"] == "DECART_NO_DISPONIBLE"
        assert "no está disponible" in data["detail"]

    app.dependency_overrides.clear()


# ==============================================================================
# 2. PRUEBAS DE ENDPOINT: POST /api/v1/vestidor/sesion (Prueba 3)
# ==============================================================================


def test_registrar_sesion_motor_local_exitoso(client):
    """AC-4: Registra sesión de vestidor con Motor 1 (Local) y duración activa (201 Created)."""
    usuario = _crear_usuario_cliente_fixture(id_cliente=10)
    producto = _crear_producto_fixture(id_producto=42, modelo_ar_url="https://fashionstore.com/ar/42.png")
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch.object(ServicioProcesarAR, "_obtener_id_cliente_valido", return_value=10):
        with patch("modules.catalogo.cu10_vestidor_virtual.servicio.VestidorRepositorio") as MockRepo:
            repo_inst = MockRepo.return_value
            repo_inst.obtener_producto.return_value = producto

            sesion_creada = SesionVestidorORM(
                id_sesion_ar=845,
                id_cliente=10,
                id_producto=42,
                dispositivo="android",
                motor="local",
                duracion_segundos=45,
                fecha_hora=datetime(2026, 9, 13, 16, 44, 28, tzinfo=timezone.utc),
                resultado_url="https://fashionstore.com/renders/ar_capture_845.jpg",
                genero_interes=True,
            )
            repo_inst.crear_sesion.return_value = sesion_creada

            payload = {
                "id_producto": 42,
                "dispositivo": "android",
                "motor": "local",
                "duracion_segundos": 45,
                "resultado_url": "https://fashionstore.com/renders/ar_capture_845.jpg",
                "genero_interes": True,
            }

            response = client.post("/api/v1/vestidor/sesion", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["id_sesion_ar"] == 845
            assert data["id_cliente"] == 10
            assert data["id_producto"] == 42
            assert data["motor"] == "local"
            assert data["duracion_segundos"] == 45
            assert data["genero_interes"] is True

    app.dependency_overrides.clear()


def test_registrar_sesion_motor_ia_exitoso(client):
    """AC-5: Registra sesión de vestidor con Motor 2 (IA Decart) respetando límite comercial (201 Created)."""
    usuario = _crear_usuario_cliente_fixture(id_cliente=10)
    producto = _crear_producto_fixture(id_producto=42, modelo_ar_url="https://fashionstore.com/ar/42.png")
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch.object(ServicioProcesarAR, "_obtener_id_cliente_valido", return_value=10):
        with patch("modules.catalogo.cu10_vestidor_virtual.servicio.VestidorRepositorio") as MockRepo:
            repo_inst = MockRepo.return_value
            repo_inst.obtener_producto.return_value = producto

            sesion_creada = SesionVestidorORM(
                id_sesion_ar=846,
                id_cliente=10,
                id_producto=42,
                dispositivo="app_flutter",
                motor="ia",
                duracion_segundos=60,
                fecha_hora=datetime.now(timezone.utc),
                resultado_url=None,
                genero_interes=False,
            )
            repo_inst.crear_sesion.return_value = sesion_creada

            payload = {
                "id_producto": 42,
                "dispositivo": "app_flutter",
                "motor": "ia",
                "duracion_segundos": 60,
                "genero_interes": False,
            }

            response = client.post("/api/v1/vestidor/sesion", json=payload)

            assert response.status_code == 201
            data = response.json()
            assert data["motor"] == "ia"
            assert data["duracion_segundos"] == 60

    app.dependency_overrides.clear()


def test_registrar_sesion_producto_sin_modelo_ar_422(client):
    """AC-6: Si la prenda no tiene modelo_ar_url configurado, retorna 422 Unprocessable Entity."""
    usuario = _crear_usuario_cliente_fixture()
    producto_sin_ar = _crear_producto_fixture(id_producto=99, modelo_ar_url=None)
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch.object(ServicioProcesarAR, "_obtener_id_cliente_valido", return_value=10):
        with patch("modules.catalogo.cu10_vestidor_virtual.servicio.VestidorRepositorio") as MockRepo:
            repo_inst = MockRepo.return_value
            repo_inst.obtener_producto.return_value = producto_sin_ar

            payload = {
                "id_producto": 99,
                "motor": "local",
            }

            response = client.post("/api/v1/vestidor/sesion", json=payload)

            assert response.status_code == 422
            data = response.json()
            assert data["code"] == "SIN_MODELO_AR"

    app.dependency_overrides.clear()


def test_registrar_sesion_producto_inexistente_404(client):
    """AC-7: Si el id_producto no existe en la base de datos, retorna 404 Not Found."""
    usuario = _crear_usuario_cliente_fixture()
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    with patch.object(ServicioProcesarAR, "_obtener_id_cliente_valido", return_value=10):
        with patch("modules.catalogo.cu10_vestidor_virtual.servicio.VestidorRepositorio") as MockRepo:
            repo_inst = MockRepo.return_value
            repo_inst.obtener_producto.return_value = None

            payload = {
                "id_producto": 9999,
                "motor": "local",
            }

            response = client.post("/api/v1/vestidor/sesion", json=payload)

            assert response.status_code == 404
            data = response.json()
            assert data["code"] == "PRODUCTO_NO_ENCONTRADO"

    app.dependency_overrides.clear()


def test_registrar_sesion_motor_invalido_422(client):
    """AC-8: Validación de Pydantic para valores de motor fuera de ('local', 'ia')."""
    usuario = _crear_usuario_cliente_fixture()
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "id_producto": 42,
        "motor": "motor_invalido",
    }

    response = client.post("/api/v1/vestidor/sesion", json=payload)
    assert response.status_code == 422

    app.dependency_overrides.clear()


def test_registrar_sesion_duracion_negativa_422(client):
    """AC-9: Validación de Pydantic para duración negativa."""
    usuario = _crear_usuario_cliente_fixture()
    db_mock = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: usuario
    app.dependency_overrides[get_db] = lambda: db_mock

    payload = {
        "id_producto": 42,
        "motor": "local",
        "duracion_segundos": -5,
    }

    response = client.post("/api/v1/vestidor/sesion", json=payload)
    assert response.status_code == 422

    app.dependency_overrides.clear()


# ==============================================================================
# 3. PRUEBAS DE INTEGRACIÓN CON DECART SERVICE
# ==============================================================================


def test_decart_service_sin_api_key_lanza_503():
    """AC-10: DecartService sin API key lanza ServiceUnavailableError."""
    service = DecartService(api_key="")
    with pytest.raises(ServiceUnavailableError) as exc_info:
        service.generar_token_cliente()
    assert exc_info.value.code == "DECART_NO_DISPONIBLE"


def test_decart_service_clave_mock_genera_token_exitoso():
    """AC-11: DecartService con clave mock o test genera token simulado determinista."""
    service = DecartService(api_key="mock_key_test_123")
    resultado = service.generar_token_cliente()
    assert resultado["token"].startswith("decart_client_token_")
    assert resultado["expira_en_segundos"] == 60
    assert resultado["servicio"] == "decart_lucy_vton_720p"


def test_decart_service_timeout_tolera_arranque_en_frio(monkeypatch):
    """La emisión real del token espera al menos 10 s: el primer token midió 4,55 s y el límite
    anterior de 4 s lo convertía en un falso DECART_TIMEOUT (503) y en fallback al Motor 1."""
    import json as _json

    import integrations.decart_service as modulo_decart

    capturado = {}

    class RespuestaFalsa:
        status = 200

        def read(self):
            return _json.dumps({"apiKey": "ek_prueba", "expiresAt": "2099-01-01T00:00:00Z"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def urlopen_falso(req, timeout):
        capturado["timeout"] = timeout
        return RespuestaFalsa()

    monkeypatch.setattr(modulo_decart.urllib.request, "urlopen", urlopen_falso)

    resultado = DecartService(api_key="clave_real_simulada").generar_token_cliente()

    assert resultado["token"] == "ek_prueba"
    assert capturado["timeout"] >= 10


@pytest.mark.parametrize(("restringir", "incluye_origenes"), [(True, True), (False, False)])
def test_decart_service_restriccion_de_origen_segun_canal(monkeypatch, restringir, incluye_origenes):
    """Web: el token lleva allowedOrigins. Móvil: se omite, pero conserva modelo, vida y duración."""
    import json as _json

    import integrations.decart_service as modulo_decart

    enviado = {}

    class RespuestaFalsa:
        status = 200

        def read(self):
            return _json.dumps({"apiKey": "ek_prueba"}).encode()

        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

    def urlopen_falso(req, timeout):
        enviado.update(_json.loads(req.data))
        return RespuestaFalsa()

    monkeypatch.setattr(modulo_decart.urllib.request, "urlopen", urlopen_falso)

    DecartService(api_key="clave_real_simulada").generar_token_cliente(restringir_origenes=restringir)

    assert ("allowedOrigins" in enviado) is incluye_origenes
    assert enviado["allowedModels"] == ["lucy-vton-3.6"]
    assert enviado["expiresIn"] == 60
    assert enviado["constraints"] == {"realtime": {"maxSessionDuration": 60}}

