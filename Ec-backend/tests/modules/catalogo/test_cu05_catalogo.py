"""Pruebas unitarias y de integración para CU05: Consultar Catálogo de Productos."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from main import app
from modules.catalogo.cu05_consultar_catalogo.servicio import CatalogoServicio
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
    """Cliente de pruebas para interactuar con la aplicación FastAPI."""
    return TestClient(app)


def crear_categoria_fixture(id_categoria: int = 1, nombre: str = "Sastrería & Trajes") -> CategoriaORM:
    """Crea una entidad CategoriaORM para pruebas."""
    return CategoriaORM(id_categoria=id_categoria, nombre=nombre)


def crear_producto_fixture(
    id_producto: int = 101,
    id_categoria: int = 1,
    nombre: str = "Traje sastre arquitectónico en lana fría",
    precio_base: Decimal = Decimal("890.00"),
    categoria: CategoriaORM = None,
    cantidad_stock: int = 10,
) -> ProductoORM:
    """Crea un producto ORM con variantes, tallas, colores e inventario."""
    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=id_categoria,
        nombre=nombre,
        descripcion="Prenda confeccionada en lana fría de Biella con corte estructurado.",
        precio_base=precio_base,
        imagen_url="https://images.unsplash.com/photo-1515886657613-9f3515b0c78f",
        activo=True,
    )
    prod.categoria = categoria or crear_categoria_fixture(id_categoria=id_categoria)

    # Variantes con tallas y colores
    talla_36 = TallaORM(id_talla=1, codigo="36", orden=1)
    talla_38 = TallaORM(id_talla=2, codigo="38", orden=2)
    color_negro = ColorORM(id_color=1, nombre="Negro Ébano", codigo_hex="#1A1A1A")

    v1 = VarianteProductoORM(
        id_variante=1001,
        id_producto=id_producto,
        id_talla=1,
        id_color=1,
        sku=f"FASH-{id_producto}-36-NEG",
        precio_extra=Decimal("0.00"),
    )
    v1.talla = talla_36
    v1.color = color_negro
    inv1 = InventarioSucursalORM(
        id_inventario=2001,
        id_variante=1001,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=cantidad_stock,
    )
    v1.inventarios = [inv1]

    v2 = VarianteProductoORM(
        id_variante=1002,
        id_producto=id_producto,
        id_talla=2,
        id_color=1,
        sku=f"FASH-{id_producto}-38-NEG",
        precio_extra=Decimal("0.00"),
    )
    v2.talla = talla_38
    v2.color = color_negro
    inv2 = InventarioSucursalORM(
        id_inventario=2002,
        id_variante=1002,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=max(0, cantidad_stock - 2),
    )
    v2.inventarios = [inv2]

    prod.variantes = [v1, v2]
    return prod


def mock_db_execute_side_effect(categorias_filas, promociones_filas=None):
    """Genera un side_effect para mock_db.execute que separa categorías y promociones."""
    if promociones_filas is None:
        promociones_filas = []

    cat_result = MagicMock()
    cat_result.all.return_value = categorias_filas

    promo_result = MagicMock()
    promo_result.all.return_value = promociones_filas

    invocaciones = {"count": 0}

    def _execute(stmt):
        invocaciones["count"] += 1
        if invocaciones["count"] == 1:
            return cat_result
        return promo_result

    return _execute


# =========================================================================
# PRUEBAS DEL ENDPOINT GET /api/v1/catalogo
# =========================================================================


def test_endpoint_catalogo_carga_inicial_200(client):
    """AC-1: Carga inicial del catálogo activo con paginación y resumen de categorías."""
    cat1 = crear_categoria_fixture(id_categoria=1, nombre="Sastrería & Trajes")
    cat2 = crear_categoria_fixture(id_categoria=2, nombre="Vestidos de Gala")
    p1 = crear_producto_fixture(id_producto=1, id_categoria=1, nombre="Blazer estructurado en lana", categoria=cat1)
    p2 = crear_producto_fixture(id_producto=2, id_categoria=2, nombre="Vestido midi en seda pura", categoria=cat2)

    mock_db = MagicMock()
    mock_db.execute.side_effect = mock_db_execute_side_effect(
        categorias_filas=[
            (1, "Sastrería & Trajes", 8),
            (2, "Vestidos de Gala", 6),
        ],
        promociones_filas=[],
    )
    mock_db.scalar.return_value = 2
    mock_db.scalars.return_value.all.return_value = [p1, p2]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/catalogo?pagina=1&limite=8")
        assert response.status_code == 200
        data = response.json()

        assert "resumen_categorias" in data
        assert len(data["resumen_categorias"]) == 2
        assert data["resumen_categorias"][0]["nombre"] == "Sastrería & Trajes"
        assert data["resumen_categorias"][0]["total_prendas"] == 8

        assert data["total_articulos"] == 2
        assert data["pagina_actual"] == 1
        assert data["limite"] == 8
        assert data["total_paginas"] == 1
        assert data["tiene_siguiente"] is False
        assert data["tiene_anterior"] is False

        assert len(data["items"]) == 2
        primer_item = data["items"][0]
        assert primer_item["id_producto"] == 1
        assert primer_item["nombre"] == "Blazer estructurado en lana"
        assert float(primer_item["precio_base"]) == 890.0
        assert primer_item["subtitulo_atelier"] == "SASTRERÍA ATELIER"
        assert primer_item["tallas_disponibles"] == ["36", "38"]
        assert len(primer_item["colores_disponibles"]) == 1
        assert primer_item["tiene_stock"] is True
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_catalogo_filtrado_por_categoria(client):
    """AC-2: Filtrado directo por chip de categoría."""
    cat2 = crear_categoria_fixture(id_categoria=2, nombre="Vestidos de Gala")
    p = crear_producto_fixture(id_producto=2, id_categoria=2, nombre="Vestido largo plisado", categoria=cat2)

    mock_db = MagicMock()
    mock_db.execute.side_effect = mock_db_execute_side_effect(
        categorias_filas=[
            (1, "Sastrería & Trajes", 8),
            (2, "Vestidos de Gala", 6),
        ],
        promociones_filas=[],
    )
    mock_db.scalar.return_value = 1
    mock_db.scalars.return_value.all.return_value = [p]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/catalogo?categoria_id=2")
        assert response.status_code == 200
        data = response.json()

        assert data["categoria_seleccionada_id"] == 2
        assert data["total_articulos"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["categoria_id"] == 2
        assert data["items"][0]["subtitulo_atelier"] == "ALTA COSTURA"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_catalogo_categoria_vacia_empty_state(client):
    """AC-3: Consulta de categoría vacía sin artículos registrados."""
    mock_db = MagicMock()
    mock_db.execute.side_effect = mock_db_execute_side_effect(
        categorias_filas=[
            (1, "Sastrería & Trajes", 5),
            (99, "Alta Costura Nupcial", 0),
        ],
        promociones_filas=[],
    )
    mock_db.scalar.return_value = 0
    mock_db.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/catalogo?categoria_id=99")
        assert response.status_code == 200
        data = response.json()

        assert data["categoria_seleccionada_id"] == 99
        assert data["total_articulos"] == 0
        assert data["total_paginas"] == 0
        assert data["items"] == []
        assert data["tiene_siguiente"] is False
        assert data["tiene_anterior"] is False
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_catalogo_paginacion_segunda_pagina(client):
    """AC-4: Navegación paginada hacia la página 2."""
    cat = crear_categoria_fixture(id_categoria=1, nombre="Sastrería")
    p3 = crear_producto_fixture(id_producto=3, id_categoria=1, nombre="Prenda página 2", categoria=cat)

    mock_db = MagicMock()
    mock_db.execute.side_effect = mock_db_execute_side_effect(
        categorias_filas=[(1, "Sastrería", 10)],
        promociones_filas=[],
    )
    mock_db.scalar.return_value = 10  # 10 productos en total
    mock_db.scalars.return_value.all.return_value = [p3]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        # Página 2 con límite de 4 artículos -> 3 páginas totales (4 + 4 + 2)
        response = client.get("/api/v1/catalogo?pagina=2&limite=4")
        assert response.status_code == 200
        data = response.json()

        assert data["pagina_actual"] == 2
        assert data["limite"] == 4
        assert data["total_paginas"] == 3
        assert data["tiene_anterior"] is True
        assert data["tiene_siguiente"] is True
        assert len(data["items"]) == 1
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_catalogo_con_promocion_activa(client):
    """AC-5: Verificación de endpoint aplicando promoción activa."""
    cat = crear_categoria_fixture(id_categoria=1, nombre="Vestidos")
    p = crear_producto_fixture(id_producto=10, id_categoria=1, nombre="Vestido con descuento", precio_base=Decimal("1000.00"), categoria=cat)

    mock_db = MagicMock()
    mock_db.execute.side_effect = mock_db_execute_side_effect(
        categorias_filas=[(1, "Vestidos", 1)],
        promociones_filas=[(10, Decimal("25.00"), "Descuento Gala")],
    )
    mock_db.scalar.return_value = 1
    mock_db.scalars.return_value.all.return_value = [p]

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/catalogo")
        assert response.status_code == 200
        data = response.json()

        item = data["items"][0]
        assert item["tiene_descuento"] is True
        assert item["porcentaje_descuento"] == 25
        assert float(item["precio_final"]) == 750.0
        assert item["etiqueta_badge"] == "-25% ATELIER"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_servicio_aplica_promocion_activa():
    """AC-6: Cálculo de descuento y badge cuando existe una promoción activa."""
    cat = crear_categoria_fixture(id_categoria=1, nombre="Vestidos")
    prod = crear_producto_fixture(
        id_producto=50,
        id_categoria=1,
        nombre="Vestido de noche en tafetán",
        precio_base=Decimal("1000.00"),
        categoria=cat,
    )

    # Simular información de promoción activa del 20%
    promo_info = (Decimal("20.00"), "Venta Privada Atelier")

    item_out = CatalogoServicio._mapear_producto(prod, promo_info)

    assert item_out.tiene_descuento is True
    assert item_out.porcentaje_descuento == 20
    assert item_out.precio_base == Decimal("1000.00")
    assert item_out.precio_final == Decimal("800.00")
    assert item_out.etiqueta_badge == "-20% ATELIER"


def test_servicio_marca_ultimas_unidades_si_stock_es_bajo():
    """AC-7: Si el stock total es <= 5 y > 0, asigna badge 'ÚLTIMAS UNIDADES'."""
    cat = crear_categoria_fixture(id_categoria=1, nombre="Blusas")
    prod = crear_producto_fixture(
        id_producto=55,
        id_categoria=1,
        nombre="Blusa en organza de seda",
        precio_base=Decimal("450.00"),
        categoria=cat,
        cantidad_stock=2,  # Stock bajo
    )

    item_out = CatalogoServicio._mapear_producto(prod, promo_info=None)

    assert item_out.tiene_stock is True
    assert item_out.etiqueta_badge == "ÚLTIMAS UNIDADES"
