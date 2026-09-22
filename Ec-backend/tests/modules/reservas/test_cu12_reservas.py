"""Pruebas unitarias y de integración para CU12: Reservar Prendas en Boutique."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.security import create_access_token
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.modelos import (
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.reservas.modelos import ReservaORM


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con FastAPI."""
    return TestClient(app)


def crear_usuario_cliente_fixture(id_usuario: int = 10) -> UsuarioORM:
    """Crea una entidad UsuarioORM con rol cliente para pruebas autenticadas."""
    user = UsuarioORM(
        id_usuario=id_usuario,
        email="madame.dubois@fashionstore.com",
        rol="cliente",
        nombres="Madame",
        apellidos="Dubois",
        activo=True,
    )
    user.cliente = ClienteORM(
        id_cliente=id_usuario,
        talla_preferida="38",
        acepta_marketing=True,
    )
    return user


def crear_sucursal_fixture(id_sucursal: int = 1) -> SucursalORM:
    """Crea una sucursal física activa para pruebas."""
    return SucursalORM(
        id_sucursal=id_sucursal,
        id_ciudad=1,
        nombre="Flagship Serrano (Madrid)",
        direccion="Calle de Serrano 44, Salamanca",
        telefono="91 555 0123",
        horario_apertura="09:00",
        horario_cierre="20:00",
        activa=True,
    )


def test_crear_reserva_presencial_exitosa_201(client):
    """Verifica la creación atómica de una reserva en boutique con decremento de stock y auditoría."""
    usuario = crear_usuario_cliente_fixture(id_usuario=10)
    sucursal = crear_sucursal_fixture(id_sucursal=1)

    producto = ProductoORM(
        id_producto=1,
        id_categoria=1,
        nombre="Vestido Plisado en Seda Marfil Natural",
        precio_base=Decimal("890.00"),
        activo=True,
    )
    variante = VarianteProductoORM(
        id_variante=10,
        id_producto=1,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-VD9-38-MAR",
        precio_extra=Decimal("0.00"),
    )
    variante.producto = producto
    variante.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    variante.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")

    inventario = InventarioSucursalORM(
        id_inventario=100,
        id_variante=10,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=2,
        cantidad_reservada=0,
    )

    db_mock = MagicMock()
    # 1. obtener_sucursal_activa -> sucursal
    # 2. asegurar_cliente -> usuario.cliente
    # 3. obtener_variante_con_prenda -> variante
    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        sucursal,
        usuario.cliente,
        variante,
    ]
    # 4. obtener_inventario_para_reserva -> inventario.
    # Usa scalars().first() en vez de scalar_one_or_none() porque (id_variante, id_sucursal)
    # no es la clave única de inventario_sucursal: la temporada forma parte de ella.
    db_mock.execute.return_value.scalars.return_value.first.side_effect = [inventario]

    # Simular asignación de ID de reserva generada
    def simular_crear_reserva(reserva_obj):
        reserva_obj.id_reserva = 501
        reserva_obj.creado_en = datetime.now(timezone.utc)
        return reserva_obj

    db_mock.add.side_effect = lambda obj: None

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        fecha_cita = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "id_sucursal": 1,
            "fecha_hora_atencion": fecha_cita,
            "canal_origen": "web",
            "observacion": "Cita de prueba privada con champán",
            "items": [
                {"id_variante": 10, "cantidad": 1}
            ],
        }

        response = client.post("/api/v1/reservas", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "id_reserva" in data
        assert data["nombre_sucursal"] == "Flagship Serrano (Madrid)"
        assert data["estado"] == "pendiente"
        assert len(data["items"]) == 1
        assert data["items"][0]["sku"] == "ATEL-2025-VD9-38-MAR"
        assert len(data["cortesias_incluidas"]) >= 1

        # Verificar que cantidad disponible bajó de 2 a 1 y reservada subió de 0 a 1
        assert inventario.cantidad_disponible == 1
        assert inventario.cantidad_reservada == 1
        assert db_mock.commit.called
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_crear_reserva_conflicto_stock_insuficiente_409(client):
    """Verifica que si no hay stock en la boutique seleccionada, retorne 409 Conflict."""
    usuario = crear_usuario_cliente_fixture(id_usuario=10)
    sucursal = crear_sucursal_fixture(id_sucursal=1)

    producto = ProductoORM(id_producto=1, id_categoria=1, nombre="Vestido Plisado", precio_base=Decimal("890.00"), activo=True)
    variante = VarianteProductoORM(id_variante=10, id_producto=1, id_talla=2, id_color=1, sku="ATEL-VD9-38", precio_extra=Decimal("0.00"))
    variante.producto = producto
    variante.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    variante.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")

    # Inventario agotado (cantidad_disponible = 0)
    inventario_agotado = InventarioSucursalORM(
        id_inventario=100,
        id_variante=10,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=0,
        cantidad_reservada=2,
    )

    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        sucursal,
        usuario.cliente,
        variante,
    ]
    # Ninguna fila cubre la cantidad pedida, así que la primera consulta (filtrada por
    # cantidad_disponible >= cantidad) no devuelve nada y se cae al fallback informativo.
    db_mock.execute.return_value.scalars.return_value.first.side_effect = [
        None,
        inventario_agotado,
    ]

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        fecha_cita = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "id_sucursal": 1,
            "fecha_hora_atencion": fecha_cita,
            "canal_origen": "web",
            "items": [{"id_variante": 10, "cantidad": 1}],
        }
        response = client.post("/api/v1/reservas", json=payload)
        assert response.status_code == 409
        assert response.json()["code"] == "STOCK_INSUFICIENTE_RESERVA"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_crear_reserva_variante_duplicada_consolida_lineas_201(client):
    """Verifica que repetir la misma variante consolide cantidades en una sola línea.

    `reserva_detalle` tiene UNIQUE (id_reserva, id_variante): sin consolidar, el servicio
    descontaba el inventario dos veces e insertaba dos líneas idénticas, y el IntegrityError
    resultante escapaba del árbol de DomainError como un 500.
    """
    usuario = crear_usuario_cliente_fixture(id_usuario=10)
    sucursal = crear_sucursal_fixture(id_sucursal=1)

    producto = ProductoORM(
        id_producto=1,
        id_categoria=1,
        nombre="Vestido Plisado en Seda Marfil Natural",
        precio_base=Decimal("890.00"),
        activo=True,
    )
    variante = VarianteProductoORM(
        id_variante=10,
        id_producto=1,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-VD9-38-MAR",
        precio_extra=Decimal("0.00"),
    )
    variante.producto = producto
    variante.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    variante.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")

    inventario = InventarioSucursalORM(
        id_inventario=100,
        id_variante=10,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=5,
        cantidad_reservada=0,
    )

    db_mock = MagicMock()
    # La variante se resuelve una sola vez porque las líneas se agrupan antes del bucle.
    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        sucursal,
        usuario.cliente,
        variante,
    ]
    db_mock.execute.return_value.scalars.return_value.first.side_effect = [inventario]

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        fecha_cita = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "id_sucursal": 1,
            "fecha_hora_atencion": fecha_cita,
            "canal_origen": "web",
            "items": [
                {"id_variante": 10, "cantidad": 1},
                {"id_variante": 10, "cantidad": 2},
            ],
        }

        response = client.post("/api/v1/reservas", json=payload)
        assert response.status_code == 201
        data = response.json()
        # Una única línea con la cantidad sumada, no dos líneas que violen el UNIQUE.
        assert len(data["items"]) == 1
        assert data["items"][0]["cantidad"] == 3
        # El inventario se descuenta una sola vez por el total consolidado.
        assert inventario.cantidad_disponible == 2
        assert inventario.cantidad_reservada == 3
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_crear_reserva_variante_duplicada_excede_maximo_400(client):
    """Verifica que el tope de 5 unidades por variante se aplique sobre el total consolidado."""
    usuario = crear_usuario_cliente_fixture(id_usuario=10)
    sucursal = crear_sucursal_fixture(id_sucursal=1)

    producto = ProductoORM(
        id_producto=1,
        id_categoria=1,
        nombre="Vestido Plisado",
        precio_base=Decimal("890.00"),
        activo=True,
    )
    variante = VarianteProductoORM(
        id_variante=10, id_producto=1, id_talla=2, id_color=1, sku="ATEL-VD9-38", precio_extra=Decimal("0.00")
    )
    variante.producto = producto
    variante.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    variante.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")

    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        sucursal,
        usuario.cliente,
        variante,
    ]

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        fecha_cita = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
        payload = {
            "id_sucursal": 1,
            "fecha_hora_atencion": fecha_cita,
            "canal_origen": "web",
            # Cada línea respeta le=5, pero el total consolidado (8) no.
            "items": [
                {"id_variante": 10, "cantidad": 5},
                {"id_variante": 10, "cantidad": 3},
            ],
        }
        response = client.post("/api/v1/reservas", json=payload)
        assert response.status_code == 400
        assert response.json()["code"] == "CANTIDAD_MAXIMA_EXCEDIDA"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_obtener_inventario_para_reserva_con_varias_temporadas(client):
    """Verifica que el stock repartido en varias temporadas no rompa la reserva.

    La clave única de `inventario_sucursal` es (id_variante, id_sucursal, id_temporada). Filtrar
    solo por (variante, sucursal) con `scalar_one_or_none()` lanzaba `MultipleResultsFound` —un
    500— en cuanto existía stock de una segunda temporada en la misma boutique.
    """
    from modules.reservas.cu12_reservar_prendas.repositorio import ReservaRepositorio

    inventario_temporada_vigente = InventarioSucursalORM(
        id_inventario=101,
        id_variante=10,
        id_sucursal=1,
        id_temporada=2,
        cantidad_disponible=3,
        cantidad_reservada=0,
    )

    db_mock = MagicMock()
    db_mock.execute.return_value.scalars.return_value.first.return_value = (
        inventario_temporada_vigente
    )

    inventario = ReservaRepositorio.obtener_inventario_para_reserva(
        db_mock, id_variante=10, id_sucursal=1, cantidad=2
    )

    assert inventario is inventario_temporada_vigente
    # El repositorio no debe usar scalar_one_or_none() sobre un filtro que no es único.
    assert not db_mock.execute.return_value.scalar_one_or_none.called


def test_crear_reserva_fecha_pasada_400(client):
    """Verifica que solicitar una cita con fecha pasada retorne 400 Bad Request."""
    usuario = crear_usuario_cliente_fixture(id_usuario=10)
    sucursal = crear_sucursal_fixture(id_sucursal=1)

    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = sucursal

    app.dependency_overrides[get_db] = lambda: db_mock
    app.dependency_overrides[get_current_user] = lambda: usuario
    try:
        fecha_pasada = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        payload = {
            "id_sucursal": 1,
            "fecha_hora_atencion": fecha_pasada,
            "canal_origen": "web",
            "items": [{"id_variante": 10, "cantidad": 1}],
        }
        response = client.post("/api/v1/reservas", json=payload)
        assert response.status_code == 400
        assert response.json()["code"] == "FECHA_HORA_INVALIDA"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_current_user, None)


def test_crear_reserva_no_autenticado_401(client):
    """Verifica que un usuario anónimo sin token no pueda crear una reserva (HTTP 401)."""
    fecha_cita = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    payload = {
        "id_sucursal": 1,
        "fecha_hora_atencion": fecha_cita,
        "canal_origen": "web",
        "items": [{"id_variante": 10, "cantidad": 1}],
    }
    response = client.post("/api/v1/reservas", json=payload)
    assert response.status_code == 401


def test_listar_sucursales_activas_200(client):
    """Verifica que el endpoint GET /api/v1/sucursales/activas devuelva el directorio de boutiques."""
    db_mock = MagicMock()
    db_mock.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/sucursales/activas")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert data[0]["nombre"] == "Flagship Serrano (Madrid)"
    finally:
        app.dependency_overrides.pop(get_db, None)
