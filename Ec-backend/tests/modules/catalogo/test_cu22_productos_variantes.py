"""Pruebas unitarias y de integracion para CU22: Gestionar Prendas, Productos y Variantes (SKUs).

Verifica estrictamente los criterios de aceptacion de la especificacion EARS:
- # AC-1: Seguridad RBAC (JWT con rol 'administrador' requerido en endpoints /admin/*).
- # AC-2: Creacion de prenda base con normalizacion y precio mayor a cero (HTTP 201).
- # AC-3: Rechazo de producto duplicado o denominacion invalida (HTTP 409 / 422).
- # AC-4: Validacion de categoria existente (HTTP 422, CATEGORIA_INEXISTENTE).
- # AC-5: Generacion y alta de matriz cartesiana de variantes con SKU corporativo (HTTP 201).
- # AC-6: Prevencion de colision de SKU o combinacion duplicada (HTTP 409).
- # AC-7: Sobreescritura opcional de precio por variante (precio_final = base + extra).
- # AC-8: Actualizacion editorial de producto y validacion de nombres contra terceros (HTTP 200).
- # AC-9: Bloqueo de eliminacion fisica por dependencias de inventario/ventas/reservas (HTTP 409).
- # AC-10: Baja logica y desactivacion de producto (HTTP 200, activo = False).
- # AC-11: Consultas publicas y administrativas enriquecidas con metricas.
"""

from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from core.errors import ConflictError, NotFoundError, UnprocessableEntityError
from core.security import create_access_token
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import (
    CategoriaORM,
    ColorORM,
    InventarioSucursalORM,
    ProductoORM,
    TallaORM,
    VarianteProductoORM,
)
from modules.gestion_operativa.cu22_prendas_productos.errores import (
    CategoriaInexistenteError,
    ProductoConDependenciasError,
    ProductoDuplicadoError,
    ProductoNoEncontradoError,
    SkuDuplicadoError,
    VarianteConDependenciasError,
    VarianteDuplicadaError,
    VarianteNoEncontradaError,
)
from modules.gestion_operativa.cu22_prendas_productos.esquemas import (
    MatrizGenerarIn,
    ProductoActualizarIn,
    ProductoCrearIn,
    ProductoEstadoIn,
    ProductoResumenOut,
    VarianteActualizarIn,
    VarianteItemIn,
    VarianteOut,
)
from modules.gestion_operativa.cu22_prendas_productos.servicio import (
    ServicioGestionProductos,
    ServicioGestionVariantes,
)
from modules.gestion_operativa.cu22_prendas_productos.utilidades import (
    generar_sku_corporativo,
    slugify_text,
)


# =============================================================================
# FIXTURES Y UTILIDADES
# =============================================================================


@pytest.fixture
def client():
    """Cliente HTTP para pruebas de endpoints."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    """Crea un mock de usuario con rol administrador."""
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin@fashionstore.com"
    usuario.rol = "administrador"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 2) -> UsuarioORM:
    """Crea un mock de usuario con rol cliente."""
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente@fashionstore.com"
    usuario.rol = "cliente"
    usuario.activo = True
    return usuario


# =============================================================================
# 1. PRUEBAS DE UTILIDADES Y GENERADOR DE SKUs
# =============================================================================


def test_slugify_text_purga_acentos_y_especiales():
    """Verifica la normalizacion determinista a mayusculas sin acentos ni diacriticos."""
    assert slugify_text("Pantalón Lino Atelier") == "PANTALON-LINO-AT"
    assert slugify_text("  Vestido Plisado Seda  ") == "VESTIDO-PLISADO"
    assert slugify_text("Chaqueta / Blazer & Seda!") == "CHAQUETA-BLAZER"
    assert slugify_text("") == ""


def test_generador_sku_corporativo_formato_canonico():
    """AC-5: Verifica el patron canonico FS-[PROD]-[TALLA]-[COLOR] acotado a 50 chars."""
    sku = generar_sku_corporativo(
        nombre_producto="Vestido Plisado Seda",
        codigo_talla="38",
        nombre_color="Marfil Natural",
    )
    assert sku.startswith("FS-")
    assert "VESTIDO-PLISADO" in sku
    assert "-38-" in sku
    assert "MARFIL-NA" in sku
    assert len(sku) <= 50
    # No contiene acentos ni caracteres raros
    assert all(c.isalnum() or c == "-" for c in sku)


def test_generador_sku_corporativo_fallbacks():
    """Verifica comportamiento seguro ante campos atipicos o vacios."""
    sku = generar_sku_corporativo(
        nombre_producto="!!!",
        codigo_talla="",
        nombre_color="",
        id_producto=42,
    )
    assert sku == "FS-PROD42-STD-UNI"


# =============================================================================
# 2. PRUEBAS DE ESQUEMAS PYDANTIC (VALIDACIONES DE INVARIANTES)
# =============================================================================


def test_esquema_producto_crear_normaliza_espacios_y_valida_precio_base():
    """AC-2: Normalizacion de nombre y validacion de precio_base > 0."""
    payload = ProductoCrearIn(
        nombre="   Blazer   Cruzado   Lana   ",
        id_categoria=1,
        precio_base=Decimal("250.00"),
        descripcion="Tejido artesanal",
    )
    assert payload.nombre == "Blazer Cruzado Lana"
    assert payload.precio_base == Decimal("250.00")
    assert payload.activo is True

    # Precio invalido (cero o negativo)
    with pytest.raises(ValidationError):
        ProductoCrearIn(
            nombre="Blazer Invalido",
            id_categoria=1,
            precio_base=Decimal("0.00"),
        )

    # Nombre menor a 3 caracteres
    with pytest.raises(ValidationError):
        ProductoCrearIn(
            nombre="AB",
            id_categoria=1,
            precio_base=Decimal("100.00"),
        )


def test_esquema_matriz_generar_in_valida_listas_no_vacias():
    """AC-5: La matriz requiere al menos una talla y un color."""
    matriz = MatrizGenerarIn(
        ids_tallas=[1, 2],
        ids_colores=[10, 11],
        precio_extra_defecto=Decimal("15.00"),
    )
    assert len(matriz.ids_tallas) == 2
    assert matriz.precio_extra_defecto == Decimal("15.00")

    with pytest.raises(ValidationError):
        MatrizGenerarIn(ids_tallas=[], ids_colores=[1])

    with pytest.raises(ValidationError):
        MatrizGenerarIn(ids_tallas=[1], ids_colores=[])


# =============================================================================
# 3. PRUEBAS DE EXCEPCIONES DE DOMINIO
# =============================================================================


def test_jerarquia_excepciones_dominio():
    """AC-3, AC-4, AC-6, AC-9: Excepciones tipadas con codigos correctos."""
    assert issubclass(ProductoDuplicadoError, ConflictError)
    assert issubclass(CategoriaInexistenteError, UnprocessableEntityError)
    assert issubclass(SkuDuplicadoError, ConflictError)
    assert issubclass(VarianteDuplicadaError, ConflictError)
    assert issubclass(ProductoConDependenciasError, ConflictError)
    assert issubclass(VarianteConDependenciasError, ConflictError)
    assert issubclass(ProductoNoEncontradoError, NotFoundError)
    assert issubclass(VarianteNoEncontradaError, NotFoundError)

    err = ProductoDuplicadoError()
    assert err.code == "PRODUCTO_DUPLICADO"

    err_dep = ProductoConDependenciasError()
    assert err_dep.code == "PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS"


# =============================================================================
# 4. PRUEBAS DE SERVICIO: SERVICIO_GESTION_PRODUCTOS
# =============================================================================


def test_servicio_crear_producto_exitoso():
    """AC-2: Creacion de producto en base de datos con categoria valida."""
    mock_db = MagicMock()
    # No hay producto con mismo nombre
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    # Categoria existe
    cat = CategoriaORM(id_categoria=5, nombre="Trajes")
    mock_db.get.return_value = cat

    payload = ProductoCrearIn(
        nombre="Traje Sastre Dos Piezas",
        id_categoria=5,
        precio_base=Decimal("450.00"),
        descripcion="Confeccion sastrera lana virgen",
    )

    resultado = ServicioGestionProductos.crear_producto(mock_db, payload)
    assert resultado.nombre == "Traje Sastre Dos Piezas"
    assert resultado.precio_base == Decimal("450.00")
    assert mock_db.add.called
    assert mock_db.commit.called


def test_servicio_crear_producto_nombre_duplicado_409():
    """AC-3: Rechazo con ProductoDuplicadoError ante colision de nombre."""
    mock_db = MagicMock()
    # Existe producto con el mismo nombre
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()

    payload = ProductoCrearIn(
        nombre="Vestido Plisado Seda",
        id_categoria=1,
        precio_base=Decimal("300.00"),
    )

    with pytest.raises(ProductoDuplicadoError):
        ServicioGestionProductos.crear_producto(mock_db, payload)


def test_servicio_crear_producto_categoria_inexistente_422():
    """AC-4: Rechazo con CategoriaInexistenteError si id_categoria no existe."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    # Categoria no existe
    mock_db.get.return_value = None

    payload = ProductoCrearIn(
        nombre="Prenda Sin Categoria",
        id_categoria=999,
        precio_base=Decimal("120.00"),
    )

    with pytest.raises(CategoriaInexistenteError):
        ServicioGestionProductos.crear_producto(mock_db, payload)


def test_servicio_actualizar_producto_colision_nombre_tercero():
    """AC-8: Rechazo al actualizar si otro producto ya posee el nuevo nombre."""
    mock_db = MagicMock()
    prod_existente = MagicMock(id_producto=10, nombre="Nombre Antiguo")
    mock_db.get.return_value = prod_existente
    # Colision con id_producto 15
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock(id_producto=15)

    payload = ProductoActualizarIn(nombre="Nombre Ocupado")
    with pytest.raises(ProductoDuplicadoError):
        ServicioGestionProductos.actualizar_producto(mock_db, 10, payload)


def test_servicio_eliminar_producto_bloqueado_por_dependencias():
    """AC-9: Bloqueo de eliminacion fisica ante dependencias operativas."""
    mock_db = MagicMock()
    prod = MagicMock(id_producto=7)
    mock_db.get.return_value = prod
    var = MagicMock(id_variante=20)
    mock_db.scalars.return_value.all.return_value = [var]
    # Inventario con stock > 0
    mock_db.execute.return_value.scalar.return_value = 5

    with pytest.raises(ProductoConDependenciasError):
        ServicioGestionProductos.eliminar_producto(mock_db, 7)


def test_servicio_eliminar_producto_exitoso_sin_dependencias():
    """AC-9: Eliminacion fisica autorizada cuando no existen dependencias."""
    mock_db = MagicMock()
    prod = MagicMock(id_producto=7)
    mock_db.get.return_value = prod
    # Cero variantes
    mock_db.scalars.return_value.all.return_value = []

    ServicioGestionProductos.eliminar_producto(mock_db, 7)
    assert mock_db.delete.called
    assert mock_db.commit.called


def test_servicio_cambiar_estado_producto_baja_logica():
    """AC-10: Desactivacion comercial conmutando activo = False."""
    mock_db = MagicMock()
    prod = MagicMock(id_producto=12, id_categoria=1, activo=True, categoria=None, coleccion=None, precio_base=Decimal("100"))
    mock_db.get.return_value = prod
    mock_db.execute.return_value.scalar.return_value = 0

    res = ServicioGestionProductos.cambiar_estado_producto(mock_db, 12, activo=False)
    assert prod.activo is False
    assert mock_db.commit.called


# =============================================================================
# 5. PRUEBAS DE SERVICIO: SERVICIO_GESTION_VARIANTES (MATRIZ CARTESIANA)
# =============================================================================


def test_servicio_generar_matriz_variantes_cartesiana_exito():
    """AC-5, AC-7: Computo de 2 tallas x 2 colores = 4 variantes con SKU y recargo."""
    mock_db = MagicMock()
    prod = ProductoORM(id_producto=10, nombre="Vestido Plisado", precio_base=Decimal("300.00"))
    mock_db.get.return_value = prod

    tallas = [TallaORM(id_talla=1, codigo="S"), TallaORM(id_talla=2, codigo="M")]
    colores = [
        ColorORM(id_color=10, nombre="Negro", codigo_hex="#000000"),
        ColorORM(id_color=11, nombre="Beige", codigo_hex="#F5F5DC"),
    ]

    # Retorno de scalars para tallas y colores
    m_scalars = MagicMock()
    m_scalars.all.side_effect = [tallas, colores]
    mock_db.scalars.return_value = m_scalars

    # Sin tuplas existentes
    mock_db.execute.return_value.all.return_value = []
    # Sin colision de SKU
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    payload = MatrizGenerarIn(
        ids_tallas=[1, 2],
        ids_colores=[10, 11],
        precio_extra_defecto=Decimal("25.00"),
    )

    variantes = ServicioGestionVariantes.generar_matriz_variantes(mock_db, 10, payload)
    assert len(variantes) == 4
    assert mock_db.add_all.called
    assert mock_db.commit.called

    # Verificar que el precio_final sea precio_base (300) + precio_extra (25) = 325
    for v in variantes:
        assert v.precio_extra == Decimal("25.00")
        assert v.precio_final == Decimal("325.00")
        assert v.sku.startswith("FS-VESTIDO-PLISADO-")


def test_servicio_generar_matriz_variante_duplicada_409():
    """AC-6: Conflicto si alguna tupla de la matriz ya existe en la base de datos."""
    mock_db = MagicMock()
    prod = ProductoORM(id_producto=10, nombre="Falda Midi", precio_base=Decimal("150.00"))
    mock_db.get.return_value = prod

    tallas = [TallaORM(id_talla=1, codigo="S")]
    colores = [ColorORM(id_color=10, nombre="Negro", codigo_hex="#000000")]

    m_scalars = MagicMock()
    m_scalars.all.side_effect = [tallas, colores]
    mock_db.scalars.return_value = m_scalars

    # Tupla (1, 10) ya existente
    mock_db.execute.return_value.all.return_value = [(1, 10)]

    payload = MatrizGenerarIn(ids_tallas=[1], ids_colores=[10])
    with pytest.raises(VarianteDuplicadaError):
        ServicioGestionVariantes.generar_matriz_variantes(mock_db, 10, payload)


# =============================================================================
# 6. PRUEBAS DE INTEGRACION: ENDPOINTS Y CONTROL DE ACCESO RBAC
# =============================================================================


def test_endpoint_admin_productos_rbac_requiere_token_401(client):
    """AC-1: Rechazo HTTP 401 si no se proporciona token de autorizacion."""
    resp = client.get("/api/v1/admin/productos")
    assert resp.status_code == 401


def test_endpoint_admin_productos_rbac_rol_cliente_denegado_403(client):
    """AC-1: Rechazo HTTP 403 si el usuario autenticado tiene rol 'cliente'."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cliente_mock()
    try:
        token_cliente = create_access_token({"sub": "2", "rol": "cliente"})
        resp = client.get(
            "/api/v1/admin/productos",
            headers={"Authorization": f"Bearer {token_cliente}"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_crear_producto_exito_201(client):
    """AC-2: Alta exitosa de prenda por usuario administrador retornando HTTP 201."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None
    mock_db.get.return_value = CategoriaORM(id_categoria=2, nombre="Blazers")

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {
            "nombre": "Blazer Esmoquin Terciopelo",
            "id_categoria": 2,
            "precio_base": 380.0,
            "descripcion": "Acabado saten solapas",
            "activo": True,
        }
        resp = client.post(
            "/api/v1/admin/productos",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Blazer Esmoquin Terciopelo"
        assert float(data["precio_base"]) == 380.0
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_crear_producto_duplicado_409(client):
    """AC-3: Conflicto HTTP 409 ante intento de alta con nombre ya existente."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock()

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {
            "nombre": "Blazer Esmoquin Terciopelo",
            "id_categoria": 2,
            "precio_base": 380.0,
        }
        resp = client.post(
            "/api/v1/admin/productos",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "PRODUCTO_DUPLICADO"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_eliminar_producto_con_dependencias_409(client):
    """AC-9: Respuesta 409 al intentar eliminar prenda con inventario o dependencias."""
    mock_db = MagicMock()
    prod = MagicMock(id_producto=5)
    mock_db.get.return_value = prod
    var = MagicMock(id_variante=100)
    mock_db.scalars.return_value.all.return_value = [var]
    # Inventario registrado > 0
    mock_db.execute.return_value.scalar.return_value = 8

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/productos/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS"
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_eliminar_producto_exito_204(client):
    """AC-9: Eliminacion fisica exitosa (HTTP 204) cuando no tiene dependencias."""
    mock_db = MagicMock()
    prod = MagicMock(id_producto=5)
    mock_db.get.return_value = prod
    mock_db.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/productos/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 204
        assert mock_db.delete.called
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_matriz_variantes_crear_201(client):
    """AC-5: Generacion por lote de matriz de variantes retornando HTTP 201."""
    mock_db = MagicMock()
    prod = ProductoORM(id_producto=3, id_categoria=1, nombre="Camisa Sastrera", precio_base=Decimal("180.00"))
    mock_db.get.return_value = prod

    tallas = [TallaORM(id_talla=1, codigo="38")]
    colores = [ColorORM(id_color=2, nombre="Blanco", codigo_hex="#FFFFFF")]
    m_scalars = MagicMock()
    m_scalars.all.side_effect = [tallas, colores]
    mock_db.scalars.return_value = m_scalars
    mock_db.execute.return_value.all.return_value = []
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {
            "ids_tallas": [1],
            "ids_colores": [2],
            "precio_extra_defecto": 10.0,
        }
        resp = client.post(
            "/api/v1/admin/productos/3/variantes/matriz",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert len(data) == 1
        assert data[0]["talla_codigo"] == "38"
        assert data[0]["color_nombre"] == "Blanco"
        assert float(data[0]["precio_final"]) == 190.0
    finally:
        app.dependency_overrides.clear()


def test_endpoint_publico_obtener_producto_ficha_tecnica(client):
    """AC-11: Consulta publica de ficha tecnica de producto activo con variantes."""
    prod = ProductoORM(
        id_producto=9,
        id_categoria=1,
        nombre="Vestido Gala Seda",
        precio_base=Decimal("750.00"),
        activo=True,
        categoria=CategoriaORM(id_categoria=1, nombre="Vestidos"),
        coleccion=None,
    )
    # Variante activa
    talla = TallaORM(id_talla=1, codigo="40", orden=1)
    color = ColorORM(id_color=3, nombre="Azul Noche", codigo_hex="#0A1128")
    var = VarianteProductoORM(
        id_variante=50,
        id_producto=9,
        id_talla=1,
        id_color=3,
        sku="FS-VESTIDO-GALA-40-AZUL",
        precio_extra=Decimal("50.00"),
        activo=True,
        talla=talla,
        color=color,
    )
    var.inventarios = []
    prod.variantes = [var]

    mock_db = MagicMock()
    mock_db.get.return_value = prod
    mock_db.execute.return_value.scalar.return_value = 4  # stock
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [prod, None]
    mock_db.execute.return_value.scalars.return_value.all.return_value = []

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        resp = client.get("/api/v1/productos/9")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id_producto"] == 9
        assert data["nombre"] == "Vestido Gala Seda"
        assert len(data["variantes"]) == 1
        assert data["variantes"][0]["sku"] == "FS-VESTIDO-GALA-40-AZUL"
        assert float(data["variantes"][0]["precio_final"]) == 800.0
    finally:
        app.dependency_overrides.clear()


# =============================================================================
# PRUEBAS DE CARGA DE IMAGENES LOCALES (FILE UPLOAD)
# =============================================================================


def test_endpoint_admin_upload_imagen_png_exitoso(client):
    """Subida exitosa de archivo PNG simulado con rol administrador retornando HTTP 201."""
    from pathlib import Path

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        contenido_png = b"\x89PNG\r\n\x1a\n" + b"simulated-png-bytes"
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"archivo": ("prenda_test.png", contenido_png, "image/png")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert "url" in data
        assert data["url"].startswith("/static/uploads/productos/prod_")
        assert data["url"].endswith(".png")

        # Verificar existencia fisica y limpiar
        ruta_archivo = Path(__file__).resolve().parents[4] / data["url"].lstrip("/")
        if ruta_archivo.exists():
            ruta_archivo.unlink()
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_upload_imagen_jpg_exitoso(client):
    """Subida exitosa de archivo JPEG simulado retornando extension .jpg."""
    from pathlib import Path

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        contenido_jpg = b"\xff\xd8\xff\xe0" + b"simulated-jpeg-bytes"
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"archivo": ("foto_modelo.jpg", contenido_jpg, "image/jpeg")},
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["url"].startswith("/static/uploads/productos/prod_")
        assert data["url"].endswith(".jpg")

        ruta_archivo = Path(__file__).resolve().parents[4] / data["url"].lstrip("/")
        if ruta_archivo.exists():
            ruta_archivo.unlink()
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_upload_imagen_formato_no_admitido_400(client):
    """Rechazo con HTTP 400 ante formatos no permitidos (ej. texto plano o PDF)."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"archivo": ("documento.txt", b"contenido no valido", "text/plain")},
        )
        assert resp.status_code == 400
        assert "Formato de imagen no admitido" in resp.json()["detail"]
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_upload_imagen_archivo_vacio_400(client):
    """Rechazo con HTTP 400 ante archivos de 0 bytes."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"archivo": ("vacio.png", b"", "image/png")},
        )
        assert resp.status_code == 400
        assert "vacio" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_upload_imagen_tamano_excedido_400(client):
    """Rechazo con HTTP 400 ante archivos superiores a 5 MB."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        # 5 MB + 1 byte
        contenido_pesado = b"X" * (5 * 1024 * 1024 + 1)
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_admin}"},
            files={"archivo": ("pesado.webp", contenido_pesado, "image/webp")},
        )
        assert resp.status_code == 400
        assert "limite maximo" in resp.json()["detail"].lower()
    finally:
        app.dependency_overrides.clear()


def test_endpoint_admin_upload_imagen_sin_permisos_403(client):
    """Rechazo con HTTP 403 si el usuario autenticado no posee rol administrador."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cliente_mock()
    try:
        token_cliente = create_access_token({"sub": "2", "rol": "cliente"})
        resp = client.post(
            "/api/v1/admin/productos/upload-imagen",
            headers={"Authorization": f"Bearer {token_cliente}"},
            files={"archivo": ("foto.png", b"bytes", "image/png")},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()
