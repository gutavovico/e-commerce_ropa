"""Pruebas unitarias y de integración para CU18: Recibir Recomendaciones Personalizadas."""

from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_optional_current_user
from integrations.gemini_service import GeminiService, gemini_service
from main import app
from modules.autenticacion_seguridad.modelos import ClienteORM, UsuarioORM
from modules.catalogo.cu18_recomendaciones.esquemas import (
    ProductoRecomendadoItemOut,
    RecomendacionesPersonalizadasOut,
)
from modules.catalogo.cu18_recomendaciones.servicio import (
    MENSAJE_EMPTY_STATE_OFICIAL,
    RecomendacionesService,
)
from modules.catalogo.modelos import (
    CategoriaORM,
    ColeccionORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    RecomendacionIAORM,
    SucursalORM,
    TallaORM,
    VarianteProductoORM,
    VentaDetalleORM,
    VentaORM,
)


@pytest.fixture
def client():
    """Cliente HTTP de prueba para FastAPI."""
    return TestClient(app)


def crear_cliente_fixture(id_usuario: int = 101, nombres: str = "Ana", apellidos: str = "Valenzuela") -> UsuarioORM:
    """Crea una entidad UsuarioORM con perfil de cliente."""
    cliente = ClienteORM(
        id_cliente=id_usuario,
        talla_preferida="38",
        acepta_marketing=True,
    )
    usuario = UsuarioORM(
        id_usuario=id_usuario,
        email="ana.valenzuela@example.com",
        password_hash="argon2id$mockhash",
        nombres=nombres,
        apellidos=apellidos,
        rol="cliente",
        activo=True,
        cliente=cliente,
    )
    return usuario


def crear_producto_con_stock(
    id_producto: int,
    nombre: str,
    id_categoria: int,
    categoria_nombre: str,
    precio: Decimal,
    stock: int = 5,
    activo: bool = True,
    id_coleccion: int = 1,
    coleccion_nombre: str = "Haute Couture",
) -> ProductoORM:
    """Crea un ProductoORM con variantes e inventario asociado."""
    cat = CategoriaORM(id_categoria=id_categoria, nombre=categoria_nombre)
    col = ColeccionORM(id_coleccion=id_coleccion, id_temporada=1, nombre=coleccion_nombre)

    prod = ProductoORM(
        id_producto=id_producto,
        id_categoria=id_categoria,
        id_coleccion=id_coleccion,
        nombre=nombre,
        descripcion=f"Descripción de {nombre}",
        precio_base=precio,
        imagen_url=f"https://fashionstore.com/img/{id_producto}.jpg",
        activo=activo,
        categoria=cat,
        coleccion=col,
    )

    talla = TallaORM(id_talla=1, codigo="38", orden=1)
    color = ColorORM(id_color=1, nombre="Marfil Puro", codigo_hex="#FCFBF8")

    variante = VarianteProductoORM(
        id_variante=id_producto * 10,
        id_producto=id_producto,
        id_talla=1,
        id_color=1,
        sku=f"SKU-{id_producto}-MARFIL-38",
        precio_extra=Decimal("0.00"),
        talla=talla,
        color=color,
        producto=prod,
    )

    inv = InventarioSucursalORM(
        id_inventario=id_producto * 100,
        id_variante=variante.id_variante,
        id_sucursal=1,
        id_temporada=1,
        cantidad_disponible=stock,
        cantidad_reservada=0,
        stock_minimo=1,
        estado="disponible",
        variante=variante,
    )

    variante.inventarios = [inv]
    prod.variantes = [variante]
    return prod


# ============================================================================
# 1. PRUEBAS DEL MOTOR DE EXPLICABILIDAD (GEMINI + FALLBACK DETERMINISTA)
# ============================================================================

def test_gemini_service_fallback_determinista_seda():
    """AC-1: El generador fallback retorna motivo estilístico de seda para vestidos."""
    service = GeminiService(api_key="")
    motivo = service.generar_motivo_recomendacion(
        categoria_principal="Vestidos de Gala en Seda",
        sucursal_nombre="Flagship Serrano (Madrid)",
    )
    assert "seda" in motivo.lower() or "sastrería" in motivo.lower()
    assert "Flagship Serrano (Madrid)" in motivo


def test_gemini_service_fallback_determinista_blazer():
    """AC-2: El generador fallback retorna motivo de sastrería y lana para blazers."""
    service = GeminiService(api_key="")
    motivo = service.generar_motivo_recomendacion(
        categoria_principal="Blazers y Chaquetas",
        sucursal_nombre="Boutique Saint-Honoré (París)",
    )
    assert "sastrería" in motivo.lower() or "lana" in motivo.lower()
    assert "Boutique Saint-Honoré (París)" in motivo


def test_gemini_service_con_error_conmuta_a_fallback():
    """AC-3: Si la API de Gemini falla, conmuta silenciosamente al fallback sin lanzar excepción."""
    service = GeminiService(api_key="clave_invalida_de_prueba")
    with patch("urllib.request.urlopen", side_effect=Exception("Timeout simulado")):
        motivo = service.generar_motivo_recomendacion(
            categoria_principal="Abrigos",
            sucursal_nombre="Flagship Serrano (Madrid)",
        )
        assert motivo is not None
        assert "abrigo" in motivo.lower() or "paño noble" in motivo.lower()


# ============================================================================
# 2. PRUEBAS DEL SERVICIO DE RECOMENDACIONES (LÓGICA DE NEGOCIO Y DOMINIO)
# ============================================================================

def test_recomendaciones_visitante_anonimo_retorna_empty_state():
    """AC-4: Si el visitante no está autenticado (None), responde empty state oficial sin inventar productos."""
    mock_db = MagicMock()
    service = RecomendacionesService(mock_db)

    resultado = service.obtener_recomendaciones_personalizadas(usuario=None)

    assert resultado.tiene_historial is False
    assert resultado.total_recomendados == 0
    assert len(resultado.items) == 0
    assert resultado.mensaje_empty_state == MENSAJE_EMPTY_STATE_OFICIAL
    assert resultado.motivo_general is None


def test_recomendaciones_cliente_nuevo_sin_compras_retorna_empty_state():
    """AC-5: Si el cliente está autenticado pero no tiene compras pagadas previas, retorna empty state."""
    mock_db = MagicMock()
    # Simular que la consulta a ventas_pagadas retorna lista vacía
    mock_query = MagicMock()
    mock_query.unique.return_value.scalars.return_value.all.return_value = []
    mock_db.execute.return_value = mock_query

    usuario = crear_cliente_fixture(101)
    service = RecomendacionesService(mock_db)

    resultado = service.obtener_recomendaciones_personalizadas(usuario=usuario)

    assert resultado.tiene_historial is False
    assert resultado.total_recomendados == 0
    assert len(resultado.items) == 0
    assert resultado.mensaje_empty_state == MENSAJE_EMPTY_STATE_OFICIAL


def test_recomendaciones_cliente_con_compras_recomienda_afines_con_stock():
    """AC-6: Si el cliente compró prendas de sastrería, recomienda productos afines activos en stock,

    excluyendo los productos ya adquiridos.
    """
    usuario = crear_cliente_fixture(101)

    # 1. Prenda comprada previamente (ID 1: Vestido plisado)
    prenda_comprada = crear_producto_con_stock(
        id_producto=1,
        nombre="Vestido plisado en seda natural",
        id_categoria=10,
        categoria_nombre="Vestidos",
        precio=Decimal("890.00"),
        stock=5,
    )

    sucursal = SucursalORM(id_sucursal=1, id_ciudad=1, nombre="Flagship Serrano (Madrid)", direccion="Serrano 48")
    venta_pagada = VentaORM(
        id_venta=5001,
        numero_comprobante="TK-001",
        id_cliente=101,
        id_sucursal=1,
        tipo_venta="presencial",
        estado="pagada",
        total=Decimal("890.00"),
        fecha_venta=datetime.now(timezone.utc),
        sucursal=sucursal,
    )
    detalle = VentaDetalleORM(
        id_venta_detalle=9001,
        id_venta=5001,
        id_variante=10,
        cantidad=1,
        precio_unitario=Decimal("890.00"),
        variante=prenda_comprada.variantes[0],
        venta=venta_pagada,
    )
    venta_pagada.detalles = [detalle]

    # 2. Candidatos en catálogo:
    # - Prenda afín en stock (ID 2: Blazer estructurado) -> Debe ser recomendada
    prenda_afin_stock = crear_producto_con_stock(
        id_producto=2,
        nombre="Blazer estructurado en lana virgen",
        id_categoria=10,  # Misma categoría de preferencia
        categoria_nombre="Vestidos y Sastrería",
        precio=Decimal("740.00"),
        stock=8,
    )
    # - Prenda sin stock (ID 3) -> Debe ser descartada
    prenda_sin_stock = crear_producto_con_stock(
        id_producto=3,
        nombre="Pantalón sastre agotado",
        id_categoria=10,
        categoria_nombre="Vestidos y Sastrería",
        precio=Decimal("450.00"),
        stock=0,
    )
    # - Prenda inactiva (ID 4) -> Debe ser descartada
    prenda_inactiva = crear_producto_con_stock(
        id_producto=4,
        nombre="Falda descatalogada",
        id_categoria=10,
        categoria_nombre="Vestidos y Sastrería",
        precio=Decimal("320.00"),
        stock=4,
        activo=False,
    )

    mock_db = MagicMock()
    # Primera ejecución: ventas_pagadas
    mock_res_ventas = MagicMock()
    mock_res_ventas.unique.return_value.scalars.return_value.all.return_value = [venta_pagada]

    # Segunda ejecución: productos candidatos
    mock_res_prods = MagicMock()
    mock_res_prods.unique.return_value.scalars.return_value.all.return_value = [
        prenda_afin_stock,
        prenda_sin_stock,
    ]

    mock_db.execute.side_effect = [mock_res_ventas, mock_res_prods]

    service = RecomendacionesService(mock_db)
    resultado = service.obtener_recomendaciones_personalizadas(usuario=usuario, limite=6)

    assert resultado.tiene_historial is True
    assert resultado.total_recomendados == 1
    assert len(resultado.items) == 1

    item = resultado.items[0]
    assert item.id_producto == 2
    assert item.nombre == "Blazer estructurado en lana virgen"
    assert item.stock_total_disponible == 8
    assert item.badge_editorial is not None
    assert resultado.motivo_general is not None
    assert "Flagship Serrano (Madrid)" in resultado.boutique_referencia


# ============================================================================
# 3. PRUEBAS DE LOS ENDPOINTS HTTP REST (ROUTER FASTAPI)
# ============================================================================

def test_endpoint_recomendaciones_sin_token_retorna_200_con_empty_state(client):
    """AC-7: GET /api/v1/catalogo/recomendaciones/personalizadas sin token responde 200 con empty state."""
    # Inyectar get_db para simular sin base de datos real
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_optional_current_user] = lambda: None

    try:
        response = client.get("/api/v1/catalogo/recomendaciones/personalizadas")
        assert response.status_code == 200
        data = response.json()
        assert data["tiene_historial"] is False
        assert data["total_recomendados"] == 0
        assert data["items"] == []
        assert data["mensaje_empty_state"] == MENSAJE_EMPTY_STATE_OFICIAL
    finally:
        app.dependency_overrides.clear()


def test_endpoint_recomendaciones_alias_sin_token_retorna_200(client):
    """AC-8: GET /api/v1/recomendaciones/personalizadas responde igualmente 200 con empty state."""
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_optional_current_user] = lambda: None

    try:
        response = client.get("/api/v1/recomendaciones/personalizadas")
        assert response.status_code == 200
        data = response.json()
        assert data["tiene_historial"] is False
    finally:
        app.dependency_overrides.clear()


def test_endpoint_recomendaciones_con_cliente_autenticado(client):
    """AC-9: GET /api/v1/catalogo/recomendaciones/personalizadas con cliente autenticado devuelve prendas afines."""
    usuario = crear_cliente_fixture(202)

    prenda_sugerida = crear_producto_con_stock(
        id_producto=10,
        nombre="Blusa de satén fluido marfil",
        id_categoria=5,
        categoria_nombre="Blusas",
        precio=Decimal("310.00"),
        stock=12,
    )

    sucursal = SucursalORM(id_sucursal=1, id_ciudad=1, nombre="Boutique Serrano (Madrid)", direccion="Serrano 48")
    venta = VentaORM(
        id_venta=701,
        numero_comprobante="TK-701",
        id_cliente=202,
        id_sucursal=1,
        tipo_venta="digital_web",
        estado="pagada",
        total=Decimal("310.00"),
        fecha_venta=datetime.now(timezone.utc),
        sucursal=sucursal,
    )
    prenda_comprada_previa = crear_producto_con_stock(
        id_producto=9,
        nombre="Top de seda previo",
        id_categoria=5,
        categoria_nombre="Blusas",
        precio=Decimal("280.00"),
        stock=3,
    )
    detalle = VentaDetalleORM(
        id_venta_detalle=1001,
        id_venta=701,
        id_variante=90,
        cantidad=1,
        precio_unitario=Decimal("280.00"),
        variante=prenda_comprada_previa.variantes[0],
        venta=venta,
    )
    venta.detalles = [detalle]

    mock_db = MagicMock()
    mock_res_ventas = MagicMock()
    mock_res_ventas.unique.return_value.scalars.return_value.all.return_value = [venta]

    mock_res_prods = MagicMock()
    mock_res_prods.unique.return_value.scalars.return_value.all.return_value = [prenda_sugerida]

    mock_db.execute.side_effect = [mock_res_ventas, mock_res_prods]

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_optional_current_user] = lambda: usuario

    try:
        response = client.get("/api/v1/catalogo/recomendaciones/personalizadas?limite=3")
        assert response.status_code == 200
        data = response.json()

        assert data["tiene_historial"] is True
        assert data["total_recomendados"] == 1
        assert len(data["items"]) == 1
        item = data["items"][0]
        assert item["id_producto"] == 10
        assert item["nombre"] == "Blusa de satén fluido marfil"
        assert item["precio_base"] == "310.00"
        assert item["stock_total_disponible"] == 12
        assert item["score_relevancia"] >= 0.8
        assert data["motivo_general"] is not None
    finally:
        app.dependency_overrides.clear()


def test_endpoint_recomendaciones_limite_invalido_devuelve_422(client):
    """AC-10: Parámetros fuera de rango (limite=0 o limite=50) son validados por Pydantic con HTTP 422."""
    response = client.get("/api/v1/catalogo/recomendaciones/personalizadas?limite=0")
    assert response.status_code == 422

    response2 = client.get("/api/v1/catalogo/recomendaciones/personalizadas?limite=50")
    assert response2.status_code == 422
