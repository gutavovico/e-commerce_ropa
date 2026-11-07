"""Pruebas unitarias y de integración para CU19: Consultar Asistente Inteligente."""

from datetime import datetime, time, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user, get_optional_current_user
from integrations.gemini_service import gemini_service
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.cu19_asistente_chatbot.esquemas import (
    MensajeChatbotIn,
    RespuestaChatbotOut,
)
from modules.catalogo.cu19_asistente_chatbot.modelos import InteraccionChatbotORM
from modules.catalogo.cu19_asistente_chatbot.servicio import ServicioAsistenteChatbot
from modules.catalogo.modelos import (
    CategoriaORM,
    InventarioSucursalORM,
    ProductoORM,
    VarianteProductoORM,
)
from modules.gestion_operativa.modelos import SucursalORM


@pytest.fixture
def client():
    """Cliente HTTP para pruebas contra FastAPI."""
    return TestClient(app)


def _crear_usuario_fixture(id_usuario: int = 5) -> UsuarioORM:
    """Crea una entidad UsuarioORM simulada."""
    cliente = ClienteORM(
        id_cliente=id_usuario,
        talla_preferida="M",
        acepta_marketing=True,
    )
    return UsuarioORM(
        id_usuario=id_usuario,
        email="madame.perfil@fashionstore.com",
        password_hash="argon2id$mockhash",
        nombres="Claire Victoria",
        apellidos="Dubois",
        rol="cliente",
        activo=True,
        cliente=cliente,
    )


def _crear_datos_prueba():
    """Genera entidades ORM de prueba en memoria."""
    cat = CategoriaORM(id_categoria=1, nombre="Vestidos de Gala")
    prod = ProductoORM(
        id_producto=10,
        id_categoria=1,
        nombre="Vestido Plisado Seda Noir",
        descripcion="Vestido de noche confeccionado en satén y seda.",
        precio_base=Decimal("1250.00"),
        imagen_url="https://fashionstore.com/vestido.jpg",
        activo=True,
    )
    prod.categoria = cat
    suc = SucursalORM(
        id_sucursal=1,
        nombre="Atelier Serrano - Madrid",
        direccion="Calle Serrano 48",
        horario_apertura=time(9, 0),
        horario_cierre=time(20, 0),
        activa=True,
    )
    var = VarianteProductoORM(
        id_variante=101,
        id_producto=10,
        id_talla=1,
        id_color=1,
        sku="FS-VES-010-M-NEG",
        activo=True,
        producto=prod,
    )
    inv = InventarioSucursalORM(
        id_inventario=201,
        id_variante=101,
        id_sucursal=1,
        cantidad_disponible=5,
        cantidad_reservada=0,
        sucursal=suc,
        variante=var,
    )
    var.inventarios = [inv]
    prod.variantes = [var]

    return prod, suc


class MockSession:
    """Sesión SQLAlchemy simulada para tests unitarios."""

    def __init__(self, productos=None, sucursales=None, interacciones=None):
        self.productos = productos or []
        self.sucursales = sucursales or []
        self.interacciones = interacciones or []
        self._next_id = 100

    def add(self, obj):
        if isinstance(obj, InteraccionChatbotORM):
            if not obj.id_interaccion:
                obj.id_interaccion = self._next_id
                self._next_id += 1
            if not obj.creado_en:
                obj.creado_en = datetime.now(timezone.utc)
            self.interacciones.append(obj)

    def commit(self):
        pass

    def refresh(self, obj):
        pass

    def execute(self, stmt):
        stmt_str = str(stmt).lower()
        mock_result = MagicMock()

        if "interacciones_chatbot" in stmt_str:
            mock_result.scalars.return_value.all.return_value = list(self.interacciones)
            return mock_result

        if "sucursales" in stmt_str:
            mock_result.scalars.return_value.all.return_value = list(self.sucursales)
            return mock_result

        if "productos" in stmt_str:
            unique_mock = MagicMock()
            unique_mock.scalars.return_value.all.return_value = list(self.productos)
            mock_result.unique.return_value = unique_mock
            return mock_result

        mock_result.scalars.return_value.all.return_value = []
        mock_result.unique.return_value.scalars.return_value.all.return_value = []
        return mock_result


# --- TESTS ---


def test_chat_asistente_anonimo_fallback(client):
    """Verifica que un visitante no autenticado reciba asesoría con fallback determinista."""
    prod, suc = _crear_datos_prueba()
    db_mock = MockSession(productos=[prod], sucursales=[suc])

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_optional_current_user] = lambda: None

    try:
        with patch.object(gemini_service, "generar_respuesta_chat", return_value=None):
            resp = client.post(
                "/api/v1/asistente/chat",
                json={
                    "mensaje": "¿Tienen vestidos de gala para una fiesta?",
                    "canal": "web",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["id_interaccion"] > 0
        assert "Vestido" in data["respuesta"] or "alta costura" in data["respuesta"]
        assert len(data["productos_sugeridos"]) >= 1
        assert data["productos_sugeridos"][0]["id_producto"] == 10
        assert data["productos_sugeridos"][0]["nombre"] == "Vestido Plisado Seda Noir"
        assert len(data["sugerencias_rapidas"]) > 0

        # Verificar persistencia en MockSession
        assert len(db_mock.interacciones) == 1
        assert db_mock.interacciones[0].id_cliente is None
        assert db_mock.interacciones[0].canal == "web"
    finally:
        app.dependency_overrides.clear()


def test_chat_asistente_autenticado_con_gemini(client):
    """Verifica respuesta exitosa integrando respuesta generada por Gemini y cliente autenticado."""
    prod, suc = _crear_datos_prueba()
    db_mock = MockSession(productos=[prod], sucursales=[suc])
    usuario = _crear_usuario_fixture(id_usuario=8)

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_optional_current_user] = lambda: usuario

    gemini_reply = "Estimada Claire, nuestro Vestido Plisado Seda Noir es la opción perfecta para su evento."

    try:
        with patch.object(gemini_service, "generar_respuesta_chat", return_value=gemini_reply):
            resp = client.post(
                "/api/v1/asistente/chat",
                json={
                    "mensaje": "¿Qué vestido me recomiendan para una gala benéfica?",
                    "canal": "movil",
                    "id_sucursal_preferida": 1,
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["respuesta"] == gemini_reply
        assert len(data["productos_sugeridos"]) == 1
        assert data["productos_sugeridos"][0]["precio"] == "1250.00"

        # Verificar cliente asociado
        assert len(db_mock.interacciones) == 1
        assert db_mock.interacciones[0].id_cliente == 8
        assert db_mock.interacciones[0].canal == "movil"
    finally:
        app.dependency_overrides.clear()


def test_chat_consulta_horario_y_sucursal(client):
    """Verifica que la consulta sobre horarios y tiendas retorne los datos de la sucursal."""
    prod, suc = _crear_datos_prueba()
    db_mock = MockSession(productos=[prod], sucursales=[suc])

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_optional_current_user] = lambda: None

    try:
        with patch.object(gemini_service, "generar_respuesta_chat", return_value=None):
            resp = client.post(
                "/api/v1/asistente/chat",
                json={
                    "mensaje": "¿Cuál es el horario y dirección de la boutique en Madrid?",
                    "canal": "web",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert "Atelier Serrano" in data["respuesta"] or "09:00" in data["respuesta"]
        assert len(data["sucursales_sugeridas"]) == 1
        assert data["sucursales_sugeridas"][0]["id_sucursal"] == 1
        assert data["sucursales_sugeridas"][0]["direccion"] == "Calle Serrano 48"
        assert data["sucursales_sugeridas"][0]["horario"] == "09:00 - 20:00"
    finally:
        app.dependency_overrides.clear()


def test_chat_validacion_mensaje_muy_corto(client):
    """Valida que un mensaje con menos de 2 caracteres sea rechazado con HTTP 422."""
    app.dependency_overrides[get_optional_current_user] = lambda: None
    try:
        resp = client.post(
            "/api/v1/asistente/chat",
            json={"mensaje": "a", "canal": "web"},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_historial_asistente_autenticado(client):
    """Verifica que el cliente autenticado pueda recuperar su historial de conversación."""
    interaccion_previa = InteraccionChatbotORM(
        id_interaccion=45,
        id_cliente=5,
        mensaje_usuario="¿Tienen blazers negros?",
        respuesta_ia="Sí, disponemos del Blazer Sastrería Lana Virgen.",
        canal="web",
        creado_en=datetime(2026, 11, 7, 6, 0, tzinfo=timezone.utc),
    )
    db_mock = MockSession(interacciones=[interaccion_previa])
    usuario = _crear_usuario_fixture(id_usuario=5)

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario

    try:
        resp = client.get("/api/v1/asistente/historial?limite=10")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["id_interaccion"] == 45
        assert data[0]["mensaje_usuario"] == "¿Tienen blazers negros?"
        assert data[0]["canal"] == "web"
    finally:
        app.dependency_overrides.clear()


def test_historial_asistente_sin_token_retorna_401(client):
    """Verifica que invocar /asistente/historial sin token Bearer retorne 401 Unauthorized."""
    resp = client.get("/api/v1/asistente/historial")
    assert resp.status_code == 401


def test_chat_asistente_canal_invalido(client):
    """Valida que un canal desconocido sea rechazado con HTTP 422."""
    app.dependency_overrides[get_optional_current_user] = lambda: None
    try:
        resp = client.post(
            "/api/v1/asistente/chat",
            json={"mensaje": "¿Tienen vestidos?", "canal": "canal_desconocido"},
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


def test_chat_saludo_y_probador_fallback(client):
    """Verifica respuestas específicas del fallback para saludos y dudas del vestidor virtual."""
    prod, suc = _crear_datos_prueba()
    db_mock = MockSession(productos=[prod], sucursales=[suc])

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_optional_current_user] = lambda: None

    try:
        with patch.object(gemini_service, "generar_respuesta_chat", return_value=None):
            # Saludo
            resp_saludo = client.post(
                "/api/v1/asistente/chat",
                json={"mensaje": "Hola, buenas tardes", "canal": "web"},
            )
            assert resp_saludo.status_code == 200
            assert "Bienvenido a Fashion Store" in resp_saludo.json()["respuesta"]

            # Vestidor Virtual / Reserva
            resp_ar = client.post(
                "/api/v1/asistente/chat",
                json={"mensaje": "¿Cómo puedo usar el probador o vestidor virtual?", "canal": "movil"},
            )
            assert resp_ar.status_code == 200
            assert "Vestidor Virtual" in resp_ar.json()["respuesta"] or "reserva" in resp_ar.json()["respuesta"]
    finally:
        app.dependency_overrides.clear()
