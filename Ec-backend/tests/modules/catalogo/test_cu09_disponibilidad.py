"""Pruebas unitarias y de integración para CU09: Consultar Disponibilidad por Sucursal."""

from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from main import app
from modules.catalogo.modelos import (
    CiudadORM,
    InventarioSucursalORM,
    ProductoORM,
    SucursalORM,
    TallaORM,
    ColorORM,
    VarianteProductoORM,
)


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con FastAPI."""
    return TestClient(app)


def crear_producto_con_inventario_fixture(id_producto: int = 1) -> ProductoORM:
    """Crea una prenda con variante e inventario en sucursales."""
    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=1,
        nombre="Vestido Plisado Seda Marfil",
        precio_base=Decimal("890.00"),
        activo=True,
    )
    v1 = VarianteProductoORM(
        id_variante=10,
        id_producto=id_producto,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-VD9-38",
        precio_extra=Decimal("0.00"),
    )
    v1.talla = TallaORM(id_talla=2, codigo="38", orden=2)
    v1.color = ColorORM(id_color=1, nombre="Seda Marfil", codigo_hex="#F5F2EB")
    prod.variantes = [v1]
    return prod


def test_consultar_disponibilidad_exitosa_200(client):
    """Verifica que el endpoint GET /productos/{id}/disponibilidad retorne sucursales y existencias."""
    producto = crear_producto_con_inventario_fixture(id_producto=1)
    madrid = CiudadORM(id_ciudad=1, nombre="Madrid", pais="España")
    paris = CiudadORM(id_ciudad=2, nombre="París", pais="Francia")

    sucursal_madrid = SucursalORM(
        id_sucursal=1,
        id_ciudad=1,
        nombre="Flagship Serrano (Madrid)",
        direccion="Calle de Serrano 44, Salamanca",
        telefono="91 555 0123",
        horario_apertura="09:00",
        horario_cierre="20:00",
        activa=True,
    )
    sucursal_madrid.ciudad = madrid

    sucursal_paris = SucursalORM(
        id_sucursal=2,
        id_ciudad=2,
        nombre="Boutique Saint-Honoré (París)",
        direccion="228 Rue du Faubourg Saint-Honoré",
        telefono="+33 1 42 68 0000",
        horario_apertura="09:00",
        horario_cierre="20:00",
        activa=True,
    )
    sucursal_paris.ciudad = paris

    inv1 = InventarioSucursalORM(
        id_inventario=1,
        id_variante=10,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=2,
        cantidad_reservada=0,
    )
    inv2 = InventarioSucursalORM(
        id_inventario=2,
        id_variante=10,
        id_sucursal=2,
        id_temporada=1,
        cantidad_disponible=1,
        cantidad_reservada=0,
    )

    db_mock = MagicMock()
    # 1. obtener_producto_con_variantes -> producto
    # 2. obtener_sucursales_activas -> [sucursal_madrid, sucursal_paris]
    # 3. obtener_inventario_variante -> [inv1, inv2]
    db_mock.execute.return_value.scalar_one_or_none.return_value = producto
    db_mock.execute.return_value.scalars.return_value.all.side_effect = [
        [sucursal_madrid, sucursal_paris],
        [inv1, inv2],
    ]

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/productos/1/disponibilidad?id_variante=10")
        assert response.status_code == 200
        data = response.json()
        assert data["id_producto"] == 1
        assert data["id_variante"] == 10
        assert len(data["sucursales"]) == 2
        assert data["sucursales"][0]["nombre"] == "Flagship Serrano (Madrid)"
        assert data["sucursales"][0]["cantidad_disponible"] == 2
        assert data["sucursales"][0]["permite_reserva_directa"] is True
        assert data["total_disponible_global"] == 3
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_consultar_disponibilidad_producto_inexistente_404(client):
    """Verifica error 404 al consultar disponibilidad de un producto no existente."""
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/productos/99999/disponibilidad")
        assert response.status_code == 404
        assert response.json()["code"] == "PRODUCTO_NO_ENCONTRADO"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_consultar_disponibilidad_variante_invalida_404(client):
    """Verifica error 404 al consultar disponibilidad de una variante ajena a la prenda."""
    producto = crear_producto_con_inventario_fixture(id_producto=1)

    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = producto

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/productos/1/disponibilidad?id_variante=999")
        assert response.status_code == 404
        assert response.json()["code"] == "VARIANTE_NO_ENCONTRADA"
    finally:
        app.dependency_overrides.pop(get_db, None)
