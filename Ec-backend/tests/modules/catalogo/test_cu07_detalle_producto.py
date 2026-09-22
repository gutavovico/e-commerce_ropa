"""Pruebas unitarias y de integración para CU07: Detalle de Producto y CU08: Variantes."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from main import app
from modules.catalogo.cu07_detalle_producto.servicio import ProductoDetalleServicio
from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    PromocionORM,
    PromocionProductoORM,
    TallaORM,
    VarianteProductoORM,
)


@pytest.fixture
def client():
    """Cliente de pruebas para interactuar con FastAPI."""
    return TestClient(app)


def crear_producto_completo_fixture(
    id_producto: int = 1,
    nombre: str = "Vestido Plisado en Seda Marfil Natural",
    precio_base: Decimal = Decimal("890.00"),
    con_promocion: bool = True,
) -> ProductoORM:
    """Crea una prenda ORM completa con variantes, tallas, colores e inventario."""
    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=1,
        id_coleccion=1,
        nombre=nombre,
        descripcion="Vestido de noche elaborado en seda pura con técnica de plisado al vapor.",
        precio_base=precio_base,
        imagen_url="https://images.unsplash.com/photo-1515372039744-b8f02a3ae446",
        modelo_ar_url=None,
        activo=True,
    )
    prod.categoria = CategoriaORM(id_categoria=1, nombre="Vestidos de Gala")
    prod.coleccion = ColeccionORM(id_coleccion=1, id_temporada=1, nombre="Atelier Privé 2026")

    # Variantes (Tallas 36, 38, 40 y Colores Seda Marfil, Negro)
    talla_36 = TallaORM(id_talla=1, codigo="36", orden=1)
    talla_38 = TallaORM(id_talla=2, codigo="38", orden=2)
    talla_40 = TallaORM(id_talla=3, codigo="40", orden=3)

    color_marfil = ColorORM(id_color=1, nombre="Seda Marfil / Champagne", codigo_hex="#F5F2EB")
    color_negro = ColorORM(id_color=2, nombre="Obsidian Negro", codigo_hex="#1E1E1E")

    v1 = VarianteProductoORM(
        id_variante=10,
        id_producto=id_producto,
        id_talla=2,
        id_color=1,
        sku="ATEL-2025-VD9-38-MAR",
        precio_extra=Decimal("0.00"),
    )
    v1.talla = talla_38
    v1.color = color_marfil
    v1.inventarios = [
        InventarioSucursalORM(
            id_inventario=1,
            id_variante=10,
            id_sucursal=1,
            id_temporada=1,
            cantidad_disponible=2,
            cantidad_reservada=1,
        )
    ]

    v2 = VarianteProductoORM(
        id_variante=11,
        id_producto=id_producto,
        id_talla=1,
        id_color=1,
        sku="ATEL-2025-VD9-36-MAR",
        precio_extra=Decimal("0.00"),
    )
    v2.talla = talla_36
    v2.color = color_marfil
    v2.inventarios = [
        InventarioSucursalORM(
            id_inventario=2,
            id_variante=11,
            id_sucursal=1,
            id_temporada=1,
            cantidad_disponible=3,
            cantidad_reservada=0,
        )
    ]

    prod.variantes = [v1, v2]
    return prod


def test_consultar_detalle_producto_servicio_exitoso():
    """Valida que el servicio devuelva la ficha técnica completa con galería, variantes y precios."""
    db_mock = MagicMock()
    producto_fixture = crear_producto_completo_fixture(id_producto=1)

    # Simular promocion activa de 15% de descuento
    promocion_fixture = PromocionORM(
        id_promocion=1,
        nombre="Beneficio Atelier Privé",
        porcentaje_descuento=Decimal("15.00"),
        fecha_inicio=date.today() - timedelta(days=5),
        fecha_fin=date.today() + timedelta(days=10),
        activa=True,
    )

    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        producto_fixture,   # obtener_producto_con_variantes
        promocion_fixture,  # obtener_promocion_activa
    ]
    db_mock.execute.return_value.scalars.return_value.all.return_value = []

    res = ProductoDetalleServicio.consultar_detalle_producto(db_mock, id_producto=1)

    assert res.id_producto == 1
    assert res.nombre == "Vestido Plisado en Seda Marfil Natural"
    assert res.precio_base == Decimal("890.00")
    assert res.tiene_descuento is True
    assert res.porcentaje_descuento == 15
    assert res.precio_final < Decimal("890.00")
    assert "Atelier Pay" in res.cuotas_info
    assert len(res.galeria) == 4
    assert res.composicion.cuerpo_principal == "100% Seda Natural 22 Momme"
    assert len(res.variantes) == 2
    assert res.variantes[0].talla_codigo in ("36", "38")
    assert res.variantes[0].sku == "ATEL-2025-VD9-38-MAR"


def test_consultar_detalle_producto_endpoint_200(client):
    """Prueba el endpoint GET /api/v1/productos/{id_producto} con respuesta 200 OK."""
    producto_fixture = crear_producto_completo_fixture(id_producto=1)

    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.side_effect = [
        producto_fixture,
        None,  # sin promocion
    ]
    db_mock.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/productos/1")
        assert response.status_code == 200
        data = response.json()
        assert data["id_producto"] == 1
        assert data["nombre"] == "Vestido Plisado en Seda Marfil Natural"
        assert "galeria" in data
        assert len(data["galeria"]) == 4
        assert data["composicion"]["tecnica_textil"] == "Plisado artesanal al vapor de Lyon"
        assert "tallas_disponibles" in data
        assert "colores_disponibles" in data
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_consultar_detalle_producto_inexistente_404(client):
    """Verifica que solicitar un producto inexistente devuelva 404 Not Found."""
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_db] = lambda: db_mock
    try:
        response = client.get("/api/v1/productos/99999")
        assert response.status_code == 404
        assert response.json()["code"] == "PRODUCTO_NO_ENCONTRADO"
    finally:
        app.dependency_overrides.pop(get_db, None)
