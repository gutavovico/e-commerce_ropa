"""Pruebas unitarias y de integración para CU06: Buscar y Filtrar Productos."""

from decimal import Decimal
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from main import app
from modules.catalogo.cu06_buscar_filtrar.esquemas import (
    CatalogoBuscarIn,
    FiltrosDetalleIn,
    ProductoPaginadoOut,
    VarianteResumenOut,
)
from modules.catalogo.cu06_buscar_filtrar.servicio import (
    FiltroInvalidoError,
    ServicioBuscarFiltro,
)
from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    TallaORM,
    TemporadaORM,
    VarianteProductoORM,
)


@pytest.fixture
def client():
    """Cliente HTTP de prueba para la aplicación FastAPI."""
    return TestClient(app)


def crear_producto_fixture(
    id_producto: int,
    nombre: str,
    precio: Decimal,
    categoria_nombre: str = "Vestidos",
    coleccion_nombre: str = "Alta Costura",
    temporada_nombre: str = "Otoño / Invierno 2024",
    talla_codigo: str = "38",
    color_nombre: str = "Marfil",
    color_hex: str = "#FCFBF8",
    cantidad_stock: int = 10,
) -> ProductoORM:
    """Crea una instancia ORM de Producto con sus relaciones pobladas para pruebas."""
    cat = CategoriaORM(id_categoria=1, nombre=categoria_nombre)
    temp = TemporadaORM(
        id_temporada=1,
        nombre=temporada_nombre,
        tipo="otono_invierno",
        activa=True,
    )
    col = ColeccionORM(
        id_coleccion=1,
        id_temporada=1,
        nombre=coleccion_nombre,
    )
    col.temporada = temp

    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=1,
        id_coleccion=1,
        nombre=nombre,
        descripcion=f"Descripción de {nombre}",
        precio_base=precio,
        imagen_url=f"https://fashionstore.com/img/{id_producto}.jpg",
        activo=True,
    )
    prod.categoria = cat
    prod.coleccion = col

    talla = TallaORM(id_talla=1, codigo=talla_codigo, orden=10)
    color = ColorORM(id_color=1, nombre=color_nombre, codigo_hex=color_hex)

    var = VarianteProductoORM(
        id_variante=100 + id_producto,
        id_producto=id_producto,
        id_talla=1,
        id_color=1,
        sku=f"SKU-{id_producto}",
        precio_extra=Decimal("0.00"),
    )
    var.talla = talla
    var.color = color

    inv = InventarioSucursalORM(
        id_inventario=200 + id_producto,
        id_variante=var.id_variante,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=cantidad_stock,
        cantidad_reservada=0,
        estado="disponible",
    )
    var.inventarios = [inv]
    prod.variantes = [var]

    return prod


# ============================================================================
# 1. PRUEBAS DE ESQUEMAS PYDANTIC
# ============================================================================


def test_esquema_filtros_detalle_in_valido():
    """Valida la instanciación correcta de filtros anidados."""
    filtros = FiltrosDetalleIn(
        id_categoria=1,
        id_talla=3,
        id_color=2,
        precio_min=Decimal("50.00"),
        precio_max=Decimal("300.00"),
    )
    assert filtros.id_categoria == 1
    assert filtros.precio_min == Decimal("50.00")
    assert filtros.precio_max == Decimal("300.00")


def test_esquema_filtros_detalle_in_precio_min_mayor_que_max_falla():
    """Verifica que precio_min > precio_max dispare ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        FiltrosDetalleIn(
            precio_min=Decimal("500.00"),
            precio_max=Decimal("200.00"),
        )
    assert "precio_max no puede ser menor que precio_min" in str(exc_info.value)


def test_esquema_catalogo_buscar_in_defaults():
    """Verifica los valores por defecto del esquema POST."""
    payload = CatalogoBuscarIn()
    assert payload.termino_busqueda == ""
    assert payload.filtros is None
    assert payload.pagina == 1
    assert payload.limite == 12


def test_esquema_variante_resumen_out():
    """Valida construcción de VarianteResumenOut."""
    var = VarianteResumenOut(
        id_variante=1,
        sku="VES-38-MAR",
        talla="38",
        id_talla=2,
        color="Marfil",
        id_color=3,
        codigo_hex="#FCFBF8",
        precio_extra=Decimal("15.00"),
        disponible=True,
        cantidad_disponible=5,
    )
    assert var.sku == "VES-38-MAR"
    assert var.disponible is True
    assert var.cantidad_disponible == 5


# ============================================================================
# 2. PRUEBAS DEL SERVICIO (ServicioBuscarFiltro)
# ============================================================================


def test_servicio_derivar_badge_editorial():
    """Verifica la asignación correcta de badges de alta costura según la colección."""
    p_limitada = crear_producto_fixture(1, "Vestido", Decimal("890"), coleccion_nombre="Edición Limitada")
    assert ServicioBuscarFiltro._derivar_badge_editorial(p_limitada) == "ED. LIMITADA 12/50"

    p_serrano = crear_producto_fixture(2, "Blazer", Decimal("740"), coleccion_nombre="Sastrería Serrano")
    assert ServicioBuscarFiltro._derivar_badge_editorial(p_serrano) == "EN SERRANO"

    p_seda = crear_producto_fixture(3, "Blusa", Decimal("310"), coleccion_nombre="Seda Natural")
    assert ServicioBuscarFiltro._derivar_badge_editorial(p_seda) == "SEDA PURA"

    p_lana = crear_producto_fixture(4, "Pantalón", Decimal("420"), coleccion_nombre="Lana Fría")
    assert ServicioBuscarFiltro._derivar_badge_editorial(p_lana) == "LANA & SEDA"


def test_servicio_derivar_subtitulo_atelier():
    """Verifica la derivación de la línea atelier en mayúsculas."""
    p_atelier = crear_producto_fixture(1, "Blazer", Decimal("740"), coleccion_nombre="Sastrería Atelier")
    assert ServicioBuscarFiltro._derivar_subtitulo_atelier(p_atelier) == "SASTRERÍA ATELIER"

    p_esenciales = crear_producto_fixture(2, "Blusa", Decimal("310"), coleccion_nombre="Esenciales Minimalistas")
    assert ServicioBuscarFiltro._derivar_subtitulo_atelier(p_esenciales) == "BÁSICOS DE LUJO"


def test_servicio_mapear_a_item_out():
    """Valida la transformación íntegra de ProductoORM a ProductoItemOut enriquecido."""
    prod_orm = crear_producto_fixture(
        id_producto=42,
        nombre="Vestido plisado seda",
        precio=Decimal("890.00"),
        categoria_nombre="Vestidos",
        coleccion_nombre="Alta Costura",
        talla_codigo="38",
        color_nombre="Marfil",
    )
    item_out = ServicioBuscarFiltro.mapear_a_item_out(prod_orm)

    assert item_out.id_producto == 42
    assert item_out.nombre == "Vestido plisado seda"
    assert item_out.precio_base == Decimal("890.00")
    assert item_out.categoria == "Vestidos"
    assert item_out.coleccion == "Alta Costura"
    assert item_out.talla_sugerida == "Talla 38"
    assert item_out.color_sugerido == "Marfil"
    assert len(item_out.variantes) == 1
    assert item_out.variantes[0].disponible is True


def test_servicio_precio_invalido_lanza_error():
    """Lanza FiltroInvalidoError si precio_min > precio_max."""
    mock_session = MagicMock()
    with pytest.raises(FiltroInvalidoError) as exc_info:
        ServicioBuscarFiltro.buscar_productos(
            session=mock_session,
            precio_min=Decimal("800.00"),
            precio_max=Decimal("200.00"),
        )
    assert "precio_max no puede ser menor que precio_min" in str(exc_info.value)


def test_servicio_buscar_productos_con_mock_session():
    """Valida la ejecución de la consulta dinámica y cálculo de paginación con mock session."""
    prod1 = crear_producto_fixture(1, "Vestido plisado seda", Decimal("890.00"))
    prod2 = crear_producto_fixture(2, "Blazer estructurado", Decimal("740.00"))

    mock_session = MagicMock()
    mock_session.scalar.return_value = 2  # Total registros
    mock_scalars_mock = MagicMock()
    mock_scalars_mock.all.return_value = [prod1, prod2]
    mock_session.scalars.return_value = mock_scalars_mock

    resultado = ServicioBuscarFiltro.buscar_productos(
        session=mock_session,
        q="vestido",
        precio_min=Decimal("100.00"),
        precio_max=Decimal("1000.00"),
        pagina=1,
        limite=12,
    )

    assert isinstance(resultado, ProductoPaginadoOut)
    assert resultado.paginacion.total_registros == 2
    assert len(resultado.items) == 2
    assert resultado.paginacion.total_paginas == 1
    assert resultado.paginacion.tiene_siguiente is False
    assert resultado.paginacion.tiene_anterior is False
    assert resultado.filtros_aplicados["q"] == "vestido"


def test_servicio_buscar_sin_coincidencias():
    """Valida respuesta vacía cuando el conteo total es 0."""
    mock_session = MagicMock()
    mock_session.scalar.return_value = 0
    mock_scalars_mock = MagicMock()
    mock_scalars_mock.all.return_value = []
    mock_session.scalars.return_value = mock_scalars_mock

    resultado = ServicioBuscarFiltro.buscar_productos(
        session=mock_session,
        q="prenda_inexistente",
    )

    assert resultado.paginacion.total_registros == 0
    assert len(resultado.items) == 0
    assert resultado.paginacion.total_paginas == 0


def test_servicio_obtener_filtros_disponibles_mock():
    """Valida que obtener_filtros_disponibles mapee adecuadamente las dimensiones."""
    mock_session = MagicMock()

    temp1 = TemporadaORM(id_temporada=1, nombre="Otoño / Invierno 2024", tipo="otono_invierno", activa=True)
    talla1 = TallaORM(id_talla=1, codigo="38", orden=10)
    color1 = ColorORM(id_color=1, nombre="Marfil", codigo_hex="#FCFBF8")

    # Scalars devuelve temporadas, tallas y colores
    def mock_scalars(query):
        q_str = str(query).lower()
        if "temporadas" in q_str:
            m = MagicMock()
            m.all.return_value = [temp1]
            return m
        elif "tallas" in q_str:
            m = MagicMock()
            m.all.return_value = [talla1]
            return m
        elif "colores" in q_str:
            m = MagicMock()
            m.all.return_value = [color1]
            return m
        m = MagicMock()
        m.all.return_value = []
        return m

    mock_session.scalars.side_effect = mock_scalars

    # Execute devuelve colecciones, categorias y min/max precio
    call_count = {"val": 0}

    def mock_execute(query):
        q_str = str(query).lower()
        m = MagicMock()
        if "colecciones" in q_str:
            m.all.return_value = [(1, "Sastrería Atelier", 12)]
            return m
        elif "categorias" in q_str:
            m.all.return_value = [(1, "Vestidos", 5)]
            return m
        elif "coalesce" in q_str or "min" in q_str:
            m.one.return_value = (Decimal("310.00"), Decimal("890.00"))
            return m
        m.all.return_value = []
        return m

    mock_session.execute.side_effect = mock_execute

    filtros = ServicioBuscarFiltro.obtener_filtros_disponibles(session=mock_session)

    assert len(filtros.temporadas) == 1
    assert filtros.temporadas[0].nombre == "Otoño / Invierno 2024"
    assert len(filtros.colecciones) == 1
    assert filtros.colecciones[0].nombre == "Sastrería Atelier"
    assert filtros.colecciones[0].conteo == 12
    assert len(filtros.tallas) == 1
    assert filtros.tallas[0].codigo == "38"
    assert len(filtros.colores) == 1
    assert filtros.colores[0].nombre == "Marfil"
    assert filtros.precio_min_global == Decimal("310.00")
    assert filtros.precio_max_global == Decimal("890.00")


# ============================================================================
# 3. PRUEBAS DE ENDPOINTS HTTP (API REST)
# ============================================================================


def test_endpoint_get_productos_200_ok():
    """GET /api/v1/productos devuelve respuesta paginada con 200 OK."""
    prod = crear_producto_fixture(1, "Vestido plisado seda", Decimal("890.00"))

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/productos")
            assert response.status_code == 200
            data = response.json()
            assert "items" in data
            assert "paginacion" in data
            assert data["paginacion"]["total_registros"] == 1
            assert data["items"][0]["nombre"] == "Vestido plisado seda"
            assert data["items"][0]["badge_editorial"] == "ED. LIMITADA 12/50"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_get_productos_con_filtros_combinados():
    """GET /api/v1/productos con múltiples query params filtra con éxito."""
    prod = crear_producto_fixture(2, "Blazer estructurado", Decimal("740.00"), coleccion_nombre="Sastrería Serrano")

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/productos?q=blazer&talla=40&color=Camel")
            assert response.status_code == 200
            data = response.json()
            assert data["paginacion"]["total_registros"] == 1
            primer_item = data["items"][0]
            assert "blazer" in primer_item["nombre"].lower()
            assert primer_item["badge_editorial"] == "EN SERRANO"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_get_productos_precio_invalido_422():
    """GET /api/v1/productos con precio_min > precio_max retorna 422."""
    with TestClient(app) as client:
        response = client.get("/api/v1/productos?precio_min=1000&precio_max=200")
        assert response.status_code == 422
        assert "no puede ser menor" in response.json()["detail"]


def test_endpoint_get_filtros_disponibles_200_ok():
    """GET /api/v1/catalogo/filtros-disponibles devuelve las dimensiones del catálogo."""
    mock_db = MagicMock()

    temp = TemporadaORM(id_temporada=1, nombre="Otoño / Invierno 2024", tipo="otono_invierno", activa=True)
    talla = TallaORM(id_talla=1, codigo="38", orden=10)
    color = ColorORM(id_color=1, nombre="Marfil", codigo_hex="#FCFBF8")

    def mock_scalars(query):
        q_str = str(query).lower()
        m = MagicMock()
        if "temporadas" in q_str:
            m.all.return_value = [temp]
        elif "tallas" in q_str:
            m.all.return_value = [talla]
        elif "colores" in q_str:
            m.all.return_value = [color]
        else:
            m.all.return_value = []
        return m

    def mock_execute(query):
        q_str = str(query).lower()
        m = MagicMock()
        if "colecciones" in q_str:
            m.all.return_value = [(1, "Sastrería Atelier", 12)]
        elif "categorias" in q_str:
            m.all.return_value = [(1, "Vestidos", 5)]
        elif "coalesce" in q_str or "min" in q_str:
            m.one.return_value = (Decimal("300.00"), Decimal("1200.00"))
        else:
            m.all.return_value = []
        return m

    mock_db.scalars.side_effect = mock_scalars
    mock_db.execute.side_effect = mock_execute

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/catalogo/filtros-disponibles")
            assert response.status_code == 200
            data = response.json()
            assert "temporadas" in data
            assert "colecciones" in data
            assert "categorias" in data
            assert "tallas" in data
            assert "colores" in data
            assert float(data["precio_min_global"]) == 300.0
            assert float(data["precio_max_global"]) == 1200.0
    finally:
        app.dependency_overrides.clear()


def test_endpoint_post_catalogo_buscar_compatibilidad_si2():
    """POST /api/v1/catalogo/buscar es compatible con la especificación de SI2-Parcial1.md."""
    prod = crear_producto_fixture(42, "Camisa Casual Oxford", Decimal("150.00"), categoria_nombre="Camisas")

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        with TestClient(app) as client:
            payload = {
                "termino_busqueda": "camisa",
                "filtros": {
                    "id_categoria": 1,
                    "precio_min": 50.0,
                    "precio_max": 300.0,
                },
                "pagina": 1,
                "limite": 10,
            }
            response = client.post("/api/v1/catalogo/buscar", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["total_resultados"] == 1
            assert len(data["productos"]) == 1
            prod_out = data["productos"][0]
            assert prod_out["id_producto"] == 42
            assert prod_out["nombre"] == "Camisa Casual Oxford"
            assert prod_out["precio_base"] == 150.0
            assert "variantes_coincidentes" in prod_out
    finally:
        app.dependency_overrides.clear()


def test_busqueda_flexible_insensible_mayusculas_y_por_categoria_coleccion():
    """Búsqueda flexible insensible a mayúsculas/minúsculas por nombre, colección y categoría."""
    prod = crear_producto_fixture(
        77, "Blusa satén 22mm", Decimal("310.00"),
        categoria_nombre="Camisas",
        coleccion_nombre="Seda Natural Pura"
    )

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    # Prueba con mayúsculas completas (e.g. 'SEDA NATURAL' o 'BLUSA')
    res = ServicioBuscarFiltro.buscar_productos(mock_db, q="SEDA NATURAL PURA")
    assert res.paginacion.total_registros == 1
    assert len(res.items) == 1
    assert res.items[0].nombre == "Blusa satén 22mm"

    # Prueba de normalización de término en filtros aplicados
    assert res.filtros_aplicados["q"] == "SEDA NATURAL PURA"


def test_endpoint_get_productos_sin_filtros_opcionales():
    """GET /api/v1/productos sin parámetros devuelve 200 OK con filtros opcionales."""
    prod = crear_producto_fixture(1, "Vestido plisado seda", Decimal("890.00"))

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        with TestClient(app) as client:
            resp = client.get("/api/v1/productos")
            assert resp.status_code == 200
            data = resp.json()
            assert data["paginacion"]["total_registros"] == 1
            assert len(data["items"]) == 1
            # Comprobar que no hay filtros restrictivos forzados
            assert "talla" not in data["filtros_aplicados"]
            assert "color" not in data["filtros_aplicados"]
            assert "precio_min" not in data["filtros_aplicados"]
    finally:
        app.dependency_overrides.clear()


def test_normalizacion_y_expansion_terminos_palabras_sueltas():
    """Verifica que la normalización y expansión morfológica cubra singular/plural y sinónimos."""
    from modules.catalogo.cu06_buscar_filtrar.servicio import (
        _expandir_termino,
        _normalizar_texto,
    )

    # Normalización
    assert _normalizar_texto("Pantalón") == "pantalon"
    assert _normalizar_texto("Ébano") == "ebano"
    assert _normalizar_texto("Vestidos") == "vestidos"

    # Expansión de vestidos -> incluye vestido y vestidos
    vars_vestido = _expandir_termino("vestidos")
    assert "vestido" in vars_vestido
    assert "vestidos" in vars_vestido

    # Expansión de pantalon -> incluye pantalon, pantalón, pantalones
    vars_pantalon = _expandir_termino("pantalon")
    assert "pantalon" in vars_pantalon
    assert "pantalón" in vars_pantalon
    assert "pantalones" in vars_pantalon

    # Expansión de chaquetas -> incluye blazer y trench
    vars_chaqueta = _expandir_termino("chaqueta")
    assert "chaquetas" in vars_chaqueta
    assert "blazer" in vars_chaqueta

    # Expansión de rojo -> incluye carmín
    vars_rojo = _expandir_termino("rojo")
    assert "carmin" in vars_rojo or "carmín" in vars_rojo


def test_busqueda_palabras_sueltas_multiples_criterios():
    """Verifica que términos como 'vestido rojo' o 'vestidos' generen condiciones válidas."""
    prod = crear_producto_fixture(
        1, "Vestido plisado seda", Decimal("890.00"),
        categoria_nombre="Vestidos",
        color_nombre="Rojo Carmín",
        color_hex="#991B1B"
    )

    mock_db = MagicMock()
    mock_db.scalar.return_value = 1
    m_scalars = MagicMock()
    m_scalars.all.return_value = [prod]
    mock_db.scalars.return_value = m_scalars

    # Búsqueda por plural 'vestidos'
    res_plural = ServicioBuscarFiltro.buscar_productos(mock_db, q="vestidos")
    assert len(res_plural.items) == 1
    assert res_plural.items[0].nombre == "Vestido plisado seda"

    # Búsqueda por palabras sueltas compuestas 'vestido rojo'
    res_compuesto = ServicioBuscarFiltro.buscar_productos(mock_db, q="vestido rojo")
    assert len(res_compuesto.items) == 1
    assert res_compuesto.items[0].color_sugerido == "Rojo Carmín"


