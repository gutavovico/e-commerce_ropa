"""Pruebas unitarias y de integración para CU36: Consultar Colecciones."""

from datetime import date, timedelta
from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from main import app
from modules.catalogo.cu36_colecciones.servicio import (
    ColeccionNoEncontradaError,
    ColeccionesService,
)
from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    ProveedorORM,
    TallaORM,
    TemporadaORM,
    VarianteProductoORM,
)


@pytest.fixture
def client():
    """Cliente HTTP de prueba para FastAPI."""
    return TestClient(app)


def crear_temporada_fixture(
    id_temporada: int = 1,
    nombre: str = "Primavera / Verano 2026",
    tipo: str = "primavera_verano",
    activa: bool = True,
    dias_inicio: int = -30,
    dias_fin: int = 60,
) -> TemporadaORM:
    """Crea una entidad TemporadaORM para pruebas."""
    hoy = date.today()
    return TemporadaORM(
        id_temporada=id_temporada,
        nombre=nombre,
        tipo=tipo,
        fecha_inicio=hoy + timedelta(days=dias_inicio),
        fecha_fin=hoy + timedelta(days=dias_fin),
        activa=activa,
    )


def crear_coleccion_fixture(
    id_coleccion: int = 1,
    id_temporada: int = 1,
    nombre: str = "Sastrería en Lana Virgen & Seda Natural",
    descripcion: str = "Cortes fluidos y armaduras arquitectónicas concebidas con tejidos de Biella y Lyon.",
    razon_social_proveedor: str = "Lanificio Cerruti 1881",
) -> ColeccionORM:
    """Crea una entidad ColeccionORM con proveedor y temporada vinculados."""
    proveedor = ProveedorORM(
        id_proveedor=id_coleccion,
        razon_social=razon_social_proveedor,
        activo=True,
    )
    col = ColeccionORM(
        id_coleccion=id_coleccion,
        id_temporada=id_temporada,
        id_proveedor=proveedor.id_proveedor,
        nombre=nombre,
        descripcion=descripcion,
    )
    col.proveedor = proveedor
    return col


def crear_producto_fixture(
    id_producto: int,
    id_coleccion: int,
    nombre: str,
    precio_base: Decimal,
    stock: int = 5,
) -> ProductoORM:
    """Crea un ProductoORM completo con categoría, variante e inventario."""
    categoria = CategoriaORM(id_categoria=1, nombre="Sastrería")
    talla = TallaORM(id_talla=1, codigo="38", orden=1)
    color = ColorORM(id_color=1, nombre="Camel Puro", codigo_hex="#C19A6B")

    variante = VarianteProductoORM(
        id_variante=id_producto * 10,
        id_producto=id_producto,
        id_talla=1,
        id_color=1,
        sku=f"SKU-COL-{id_producto}",
        precio_extra=Decimal("0.00"),
    )
    variante.talla = talla
    variante.color = color

    inventario = InventarioSucursalORM(
        id_inventario=id_producto * 100,
        id_variante=variante.id_variante,
        id_sucursal=1,
        cantidad_disponible=stock,
        cantidad_reservada=0,
        estado="disponible",
    )
    variante.inventarios = [inventario]

    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=1,
        id_coleccion=id_coleccion,
        nombre=nombre,
        descripcion=f"Descripción de {nombre}",
        precio_base=precio_base,
        imagen_url=f"https://example.com/{id_producto}.jpg",
        activo=True,
    )
    prod.categoria = categoria
    prod.variantes = [variante]
    return prod


# ==============================================================================
# TESTS DE ENDPOINTS HTTP
# ==============================================================================


def test_endpoint_colecciones_activas_retorna_200_con_temporada_vigente(client):
    """Verifica que GET /api/v1/colecciones/activas retorne la colección destacada y otras colecciones."""
    mock_db = MagicMock()
    temporada = crear_temporada_fixture(id_temporada=1, nombre="Primavera / Verano 2026")
    col1 = crear_coleccion_fixture(id_coleccion=1, id_temporada=1, nombre="Sastrería en Lana Virgen & Seda Natural")
    col2 = crear_coleccion_fixture(id_coleccion=2, id_temporada=1, nombre="Edición Milano: Punto & Lino")

    p1 = crear_producto_fixture(id_producto=101, id_coleccion=1, nombre="Vestido plisado en seda natural", precio_base=Decimal("890.00"))
    p2 = crear_producto_fixture(id_producto=102, id_coleccion=1, nombre="Blazer estructurado en lana virgen", precio_base=Decimal("740.00"))
    p3 = crear_producto_fixture(id_producto=103, id_coleccion=2, nombre="Chaqueta liviana de punto & lino", precio_base=Decimal("340.00"))

    col1.temporada = temporada
    col1.productos = [p1, p2]
    col2.temporada = temporada
    col2.productos = [p3]

    llamadas = 0

    def mock_execute(stmt):
        nonlocal llamadas
        llamadas += 1
        mock_result = MagicMock()
        # Primera llamada busca la temporada activa; subsiguientes buscan colecciones
        if llamadas == 1:
            mock_result.scalars.return_value.first.return_value = temporada
        else:
            mock_result.scalars.return_value.all.return_value = [col1, col2]
        return mock_result

    mock_db.execute.side_effect = mock_execute
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/colecciones/activas")
        assert response.status_code == 200
        data = response.json()

        assert data["temporada_activa_id"] == 1
        assert data["temporada_activa_nombre"] == "Primavera / Verano 2026"
        assert data["total_colecciones"] == 2

        # Verificar colección destacada
        destacada = data["coleccion_destacada"]
        assert destacada is not None
        assert destacada["es_destacada"] is True
        assert destacada["nombre"] == "Sastrería en Lana Virgen & Seda Natural"
        assert float(destacada["precio_desde"]) == 740.0
        assert destacada["total_prendas"] == 2
        assert len(destacada["piezas_clave"]) == 2

        # Verificar otras colecciones
        otras = data["otras_colecciones"]
        assert len(otras) == 1
        assert otras[0]["nombre"] == "Edición Milano: Punto & Lino"
        assert float(otras[0]["precio_desde"]) == 340.0
        assert otras[0]["taller_origen"] == "Molinos de Biella & Como"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_colecciones_activas_sin_temporadas_retorna_lista_vacia(client):
    """Verifica que si no hay temporadas configuradas retorne total_colecciones: 0."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.first.return_value = None

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/colecciones/activas")
        assert response.status_code == 200
        data = response.json()
        assert data["total_colecciones"] == 0
        assert data["coleccion_destacada"] is None
        assert data["otras_colecciones"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_prendas_de_coleccion_retorna_200_con_productos_activos(client):
    """Verifica que GET /api/v1/colecciones/{id}/productos devuelva las prendas de la colección."""
    mock_db = MagicMock()
    temporada = crear_temporada_fixture(id_temporada=1)
    col = crear_coleccion_fixture(id_coleccion=1, id_temporada=1, nombre="Sastrería en Lana Virgen & Seda Natural")
    p1 = crear_producto_fixture(id_producto=101, id_coleccion=1, nombre="Vestido plisado en seda natural", precio_base=Decimal("890.00"))
    p2 = crear_producto_fixture(id_producto=102, id_coleccion=1, nombre="Blazer estructurado en lana virgen", precio_base=Decimal("740.00"))

    col.temporada = temporada
    col.productos = [p1, p2]

    mock_db.execute.return_value.scalars.return_value.first.return_value = col
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/colecciones/1/productos")
        assert response.status_code == 200
        data = response.json()

        assert data["id_coleccion"] == 1
        assert data["nombre"] == "Sastrería en Lana Virgen & Seda Natural"
        assert data["total_prendas"] == 2
        assert len(data["productos"]) == 2

        prod_0 = data["productos"][0]
        assert prod_0["id_producto"] == 101
        assert prod_0["nombre"] == "Vestido plisado en seda natural"
        assert float(prod_0["precio_base"]) == 890.0
        assert prod_0["stock_total_disponible"] == 5
        assert prod_0["tiene_stock"] is True
        assert prod_0["badge_editorial"] == "COLECCIÓN 07"
        assert prod_0["subtitulo_textil"] == "SEDA LYON · ALTA COSTURA"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_prendas_de_coleccion_sin_productos_retorna_empty_state_proximo_lanzamiento(client):
    """Verifica que una colección sin prendas retorne mensaje de próximo lanzamiento."""
    mock_db = MagicMock()
    temporada = crear_temporada_fixture(id_temporada=2)
    col_vacia = crear_coleccion_fixture(id_coleccion=99, id_temporada=2, nombre="Cápsula Alta Joyería")
    col_vacia.temporada = temporada
    col_vacia.productos = []

    mock_db.execute.return_value.scalars.return_value.first.return_value = col_vacia
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/colecciones/99/productos")
        assert response.status_code == 200
        data = response.json()

        assert data["id_coleccion"] == 99
        assert data["total_prendas"] == 0
        assert data["productos"] == []
        assert "Próximo lanzamiento" in data["mensaje_empty_state"]
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_prendas_de_coleccion_inexistente_retorna_404(client):
    """Verifica que consultar una colección no existente retorne 404 Not Found."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.get("/api/v1/colecciones/9999/productos")
        assert response.status_code == 404
        data = response.json()
        assert "no encontrada" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# TESTS DE LÓGICA Y SERVICIO
# ==============================================================================


def test_servicio_derivar_metadatos_editoriales():
    """Verifica la derivación de badges y subtítulos textiles según el producto y colección."""
    # Metadatos de colección
    meta_milano = ColeccionesService._derivar_metadatos_coleccion("Edición Milano: Punto & Lino", None)
    assert meta_milano["taller"] == "Molinos de Biella & Como"
    assert meta_milano["edicion"] == "EDICIÓN SS24 MILANO"

    meta_alpaca = ColeccionesService._derivar_metadatos_coleccion("Abrigos en Alpaca & Lana", None)
    assert meta_alpaca["taller"] == "Alpaca Suri de los Andes"
    assert meta_alpaca["disponibilidad"] == "ÚLTIMAS UNIDADES"

    # Badges de producto
    p_vestido = ProductoORM(nombre="Vestido plisado seda")
    p_blazer = ProductoORM(nombre="Blazer estructurado lana")
    p_blusa = ProductoORM(nombre="Blusa satén fluido")
    p_pantalon = ProductoORM(nombre="Pantalón sastre tiro alto")

    assert ColeccionesService._derivar_badge_producto(p_vestido) == "COLECCIÓN 07"
    assert ColeccionesService._derivar_badge_producto(p_blazer) == "EN SERRANO"
    assert ColeccionesService._derivar_badge_producto(p_blusa) == "BÁSICO DE LUJO"
    assert ColeccionesService._derivar_badge_producto(p_pantalon) == "SASTRERÍA ATELIER"

    # Subtítulos de composición textil
    assert "SEDA LYON" in ColeccionesService._derivar_subtitulo_textil(p_vestido)
    assert "BIELLA 380G" in ColeccionesService._derivar_subtitulo_textil(p_blazer)
    assert "SATÉN 100%" in ColeccionesService._derivar_subtitulo_textil(p_blusa)
    assert "LANA FINA" in ColeccionesService._derivar_subtitulo_textil(p_pantalon)


def test_servicio_obtener_temporada_activa_fallback():
    """Verifica la resolución de temporada activa con fallback a la temporada activa más reciente."""
    mock_db = MagicMock()
    t_inactiva_pasada = crear_temporada_fixture(id_temporada=1, dias_inicio=-300, dias_fin=-200, activa=False)
    t_activa_reciente = crear_temporada_fixture(id_temporada=2, dias_inicio=-100, dias_fin=-10, activa=True)

    # 1. No hay coincidencia por fecha exacta
    mock_db.execute.return_value.scalars.return_value.first.side_effect = [
        None,               # Fallo por fecha_inicio <= hoy <= fecha_fin
        t_activa_reciente,  # Fallback a activa = True más reciente
    ]

    resultado = ColeccionesService.obtener_temporada_activa(mock_db)
    assert resultado is not None
    assert resultado.id_temporada == 2
