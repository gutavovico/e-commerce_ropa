"""Pruebas unitarias y de integración para CU33: Recuperar Acceso de Cuenta."""

from datetime import datetime, timedelta, timezone
import hashlib
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.email_service import email_service
from core.security import hash_password, verify_password
from main import app
from modules.autenticacion_seguridad.cu33_recuperar_acceso.esquemas import (
    RestablecerPasswordIn,
    RestablecerPasswordOut,
    SolicitarCodigoIn,
    SolicitarCodigoOut,
)
from modules.autenticacion_seguridad.modelos import CodigoRecuperacionORM, UsuarioORM

EMAIL_TEST = "ana.recuperacion@fashionstore.com"
PASS_ORIGINAL = "ClaveOriginal2026"
PASS_NUEVA = "ClaveNuevaSegura2026"


class MockSession:
    """Mock de sesión SQLAlchemy para aislar pruebas sin dependencias de red."""

    def __init__(self, usuarios=None, codigos=None):
        self.usuarios = usuarios or []
        self.codigos = codigos or []
        self._added = []

    def scalars(self, query):
        # Simular búsqueda de Usuario o CodigoRecuperacion
        query_str = str(query).lower()
        if "from fashionstore.usuarios" in query_str or "usuarios" in query_str:
            mock_result = MagicQuery(self.usuarios)
            return mock_result
        elif "from fashionstore.codigos_recuperacion" in query_str or "codigos" in query_str:
            # Filtrar por no usados si corresponde
            activos = [c for c in self.codigos if not c.usado]
            return MagicQuery(activos if activos else self.codigos)
        return MagicQuery([])

    def add(self, obj):
        if isinstance(obj, CodigoRecuperacionORM):
            if not hasattr(obj, "id_codigo") or obj.id_codigo is None:
                obj.id_codigo = len(self.codigos) + 1
            self.codigos.append(obj)
        self._added.append(obj)

    def commit(self):
        pass


class MagicQuery:
    def __init__(self, items):
        self.items = items

    def first(self):
        return self.items[0] if self.items else None

    def all(self):
        return list(self.items)


@pytest.fixture
def usuario_prueba():
    """Crea una instancia de UsuarioORM para pruebas."""
    return UsuarioORM(
        id_usuario=100,
        email=EMAIL_TEST,
        password_hash=hash_password(PASS_ORIGINAL),
        nombres="Ana",
        apellidos="Valenzuela",
        rol="cliente",
        activo=True,
    )


# --- 1. Pruebas Unitarias de Esquemas Pydantic ---


def test_esquema_solicitar_codigo_valido():
    """Valida que SolicitarCodigoIn acepte correos bien formados."""
    schema = SolicitarCodigoIn(email="test@fashionstore.com")
    assert schema.email == "test@fashionstore.com"


def test_esquema_solicitar_codigo_invalido():
    """Rechaza correos con formato inválido."""
    with pytest.raises(Exception):
        SolicitarCodigoIn(email="no-es-un-correo")


def test_esquema_restablecer_password_normaliza_espacio():
    """Valida que el código con formato '849 201' se normalice a '849201'."""
    schema = RestablecerPasswordIn(
        email="test@fashionstore.com",
        codigo="849 201",
        nueva_password="Password123",
        confirmar_password="Password123",
    )
    assert schema.codigo == "849201"


def test_esquema_restablecer_password_rechaza_no_coincidencia():
    """Rechaza cuando confirmar_password difiere de nueva_password."""
    with pytest.raises(ValueError, match="Las contraseñas no coinciden"):
        RestablecerPasswordIn(
            email="test@fashionstore.com",
            codigo="123456",
            nueva_password="Password123",
            confirmar_password="Password456",
        )


def test_esquema_restablecer_password_rechaza_debil():
    """Rechaza contraseñas de menos de 8 caracteres o sin combinación alfanumérica."""
    with pytest.raises(Exception, match=r"(al menos 8 caracteres|at least 8 characters)"):
        RestablecerPasswordIn(
            email="test@fashionstore.com",
            codigo="123456",
            nueva_password="corta",
            confirmar_password="corta",
        )

    with pytest.raises(ValueError, match="combinar al menos una letra y un número"):
        RestablecerPasswordIn(
            email="test@fashionstore.com",
            codigo="123456",
            nueva_password="sololetrassinnumero",
            confirmar_password="sololetrassinnumero",
        )


# --- 2. Pruebas de Integración de Endpoints con FastAPI TestClient ---


@pytest.mark.anyio
async def test_endpoint_solicitar_codigo_usuario_existente(usuario_prueba):
    """Solicita código para un usuario existente: 200 OK y correo enviado."""
    mock_db = MockSession(usuarios=[usuario_prueba])
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch.object(
        email_service, "enviar_codigo_recuperacion", new_callable=AsyncMock
    ) as mock_send:
        mock_send.return_value = True

        client = TestClient(app)
        res = client.post(
            "/api/v1/autenticacion/recuperar-password/solicitar",
            json={"email": EMAIL_TEST},
        )

        assert res.status_code == 200
        data = res.json()
        assert "código de verificación" in data["mensaje"]
        assert len(mock_db.codigos) == 1
        assert mock_db.codigos[0].id_usuario == usuario_prueba.id_usuario
        mock_send.assert_called_once()

    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_endpoint_solicitar_codigo_anti_enumeracion():
    """Usuario inexistente recibe 200 OK sin generar código ni enviar correo."""
    mock_db = MockSession(usuarios=[])
    app.dependency_overrides[get_db] = lambda: mock_db

    with patch.object(
        email_service, "enviar_codigo_recuperacion", new_callable=AsyncMock
    ) as mock_send:
        client = TestClient(app)
        res = client.post(
            "/api/v1/autenticacion/recuperar-password/solicitar",
            json={"email": "inexistente@fashionstore.com"},
        )

        assert res.status_code == 200
        data = res.json()
        assert "código de verificación" in data["mensaje"]
        assert len(mock_db.codigos) == 0
        mock_send.assert_not_called()

    app.dependency_overrides.clear()


def test_endpoint_restablecer_password_exito(usuario_prueba):
    """Restablece la contraseña exitosamente con OTP válido y actualiza el hash con Argon2id."""
    codigo_plano = "849201"
    codigo_hash = hashlib.sha256(codigo_plano.encode("utf-8")).hexdigest()
    codigo_orm = CodigoRecuperacionORM(
        id_codigo=1,
        id_usuario=usuario_prueba.id_usuario,
        codigo_hash=codigo_hash,
        expira_en=datetime.now(timezone.utc) + timedelta(minutes=15),
        usado=False,
        intentos_fallidos=0,
        creado_en=datetime.now(timezone.utc),
    )

    mock_db = MockSession(usuarios=[usuario_prueba], codigos=[codigo_orm])
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    res = client.post(
        "/api/v1/autenticacion/recuperar-password/restablecer",
        json={
            "email": EMAIL_TEST,
            "codigo": "849 201",
            "nueva_password": PASS_NUEVA,
            "confirmar_password": PASS_NUEVA,
        },
    )

    assert res.status_code == 200
    data = res.json()
    assert data["exito"] is True
    assert data["codigo_evento"] == "PASSWORD_RESTABLECIDA"
    assert codigo_orm.usado is True
    # Validar que la nueva contraseña funcione y la anterior ya no
    assert verify_password(PASS_NUEVA, usuario_prueba.password_hash) is True
    assert verify_password(PASS_ORIGINAL, usuario_prueba.password_hash) is False

    app.dependency_overrides.clear()


def test_endpoint_restablecer_password_codigo_incorrecto(usuario_prueba):
    """Rechaza código incorrecto e incrementa contador de intentos fallidos."""
    codigo_hash = hashlib.sha256("849201".encode("utf-8")).hexdigest()
    codigo_orm = CodigoRecuperacionORM(
        id_codigo=1,
        id_usuario=usuario_prueba.id_usuario,
        codigo_hash=codigo_hash,
        expira_en=datetime.now(timezone.utc) + timedelta(minutes=15),
        usado=False,
        intentos_fallidos=0,
        creado_en=datetime.now(timezone.utc),
    )

    mock_db = MockSession(usuarios=[usuario_prueba], codigos=[codigo_orm])
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    res = client.post(
        "/api/v1/autenticacion/recuperar-password/restablecer",
        json={
            "email": EMAIL_TEST,
            "codigo": "000000",
            "nueva_password": PASS_NUEVA,
            "confirmar_password": PASS_NUEVA,
        },
    )

    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "CODIGO_INVALIDO"
    assert codigo_orm.intentos_fallidos == 1
    assert codigo_orm.usado is False

    app.dependency_overrides.clear()


def test_endpoint_restablecer_password_limite_intentos_superado(usuario_prueba):
    """Invalida el código y rechaza la solicitud al superar los 5 intentos permitidos."""
    codigo_hash = hashlib.sha256("849201".encode("utf-8")).hexdigest()
    codigo_orm = CodigoRecuperacionORM(
        id_codigo=1,
        id_usuario=usuario_prueba.id_usuario,
        codigo_hash=codigo_hash,
        expira_en=datetime.now(timezone.utc) + timedelta(minutes=15),
        usado=False,
        intentos_fallidos=4,  # Al fallar llegará a 5
        creado_en=datetime.now(timezone.utc),
    )

    mock_db = MockSession(usuarios=[usuario_prueba], codigos=[codigo_orm])
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    res = client.post(
        "/api/v1/autenticacion/recuperar-password/restablecer",
        json={
            "email": EMAIL_TEST,
            "codigo": "999999",
            "nueva_password": PASS_NUEVA,
            "confirmar_password": PASS_NUEVA,
        },
    )

    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "INTENTOS_SUPERADOS"
    assert codigo_orm.usado is True

    app.dependency_overrides.clear()


def test_endpoint_restablecer_password_codigo_expirado(usuario_prueba):
    """Rechaza código cuya fecha de expiración haya pasado."""
    codigo_hash = hashlib.sha256("849201".encode("utf-8")).hexdigest()
    codigo_orm = CodigoRecuperacionORM(
        id_codigo=1,
        id_usuario=usuario_prueba.id_usuario,
        codigo_hash=codigo_hash,
        expira_en=datetime.now(timezone.utc) - timedelta(minutes=1),  # Expirado
        usado=False,
        intentos_fallidos=0,
        creado_en=datetime.now(timezone.utc) - timedelta(minutes=16),
    )

    mock_db = MockSession(usuarios=[usuario_prueba], codigos=[codigo_orm])
    app.dependency_overrides[get_db] = lambda: mock_db

    client = TestClient(app)
    res = client.post(
        "/api/v1/autenticacion/recuperar-password/restablecer",
        json={
            "email": EMAIL_TEST,
            "codigo": "849201",
            "nueva_password": PASS_NUEVA,
            "confirmar_password": PASS_NUEVA,
        },
    )

    assert res.status_code == 400
    data = res.json()
    assert data["code"] == "CODIGO_EXPIRADO"
    assert codigo_orm.usado is True

    app.dependency_overrides.clear()
