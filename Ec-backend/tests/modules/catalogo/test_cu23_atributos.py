"""Pruebas unitarias y de integracion para CU23: Gestionar Categorias, Tallas y Colores.

Cubre estrictamente los criterios de aceptacion de la especificacion EARS:
- # AC-1: Seguridad RBAC (JWT con rol 'administrador' requerido en endpoints /admin/*).
- # AC-2: Creacion de categoria taxonomica con normalizacion y relacion jerarquica (HTTP 201).
- # AC-3: Rechazo de categoria duplicada (HTTP 409, CATEGORIA_DUPLICADA).
- # AC-4: Prevencion de referencias circulares en categorias (HTTP 422, REFERENCIA_CIRCULAR_NO_PERMITIDA).
- # AC-5: Proteccion de integridad en eliminacion de categoria con dependencias (HTTP 409, CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS).
- # AC-6: Creacion y secuenciacion comercial de tallas (HTTP 201, orden >= 0).
- # AC-7: Unicidad y validacion de codigo de talla (HTTP 409 / 422).
- # AC-8: Proteccion de integridad en eliminacion de talla en uso (HTTP 409, TALLA_EN_USO_EN_VARIANTES).
- # AC-9: Creacion de color textil con formato #HEX (HTTP 201).
- # AC-10: Unicidad y validacion regex de color #HEX (HTTP 409 / 422).
- # AC-11: Proteccion de integridad en eliminacion de color en uso (HTTP 409, COLOR_EN_USO_EN_VARIANTES).
- # AC-12: Consultas publicas y administrativas enriquecidas con metricas de uso.
"""

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
from modules.gestion_operativa.cu23_categorias_tallas_colores.errores import (
    CategoriaConDependenciasError,
    CategoriaDuplicadaError,
    CategoriaNoEncontradaError,
    ColorDuplicadoError,
    ColorEnUsoError,
    ColorNoEncontradoError,
    ReferenciaCircularError,
    TallaDuplicadaError,
    TallaEnUsoError,
    TallaNoEncontradaError,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.esquemas import (
    CategoriaActualizarIn,
    CategoriaAdminOut,
    CategoriaCrearIn,
    CategoriaOut,
    ColorActualizarIn,
    ColorAdminOut,
    ColorCrearIn,
    ColorOut,
    TallaActualizarIn,
    TallaAdminOut,
    TallaCrearIn,
    TallaOut,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.modelos import (
    CategoriaORM,
    ColorORM,
    TallaORM,
)
from modules.gestion_operativa.cu23_categorias_tallas_colores.servicio import (
    ServicioGestionAtributos,
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
# 1. PRUEBAS DE ESQUEMAS PYDANTIC (VALIDACION DE INVARIANTES)
# =============================================================================


def test_esquema_categoria_normalizacion_espacios():
    """AC-2: Normalizacion de espacios perimetrales e interiores en categorias."""
    dto = CategoriaCrearIn(nombre="   Vestidos   de   Gala   ")
    assert dto.nombre == "Vestidos de Gala"
    assert dto.id_categoria_padre is None


def test_esquema_categoria_nombre_muy_corto():
    """AC-2: Validacion de longitud minima para categorias."""
    with pytest.raises(ValidationError):
        CategoriaCrearIn(nombre=" X ")


def test_esquema_talla_normalizacion_mayusculas():
    """AC-6: Normalizacion automatica de codigos de talla a mayusculas."""
    dto = TallaCrearIn(codigo="  xl  ", orden=5)
    assert dto.codigo == "XL"
    assert dto.orden == 5


def test_esquema_talla_orden_invalido():
    """AC-7: El orden de talla debe ser un entero no negativo."""
    with pytest.raises(ValidationError):
        TallaCrearIn(codigo="M", orden=-1)


def test_esquema_color_hex_valido_y_normalizado():
    """AC-9: Formato #HEX valido normalizado a mayusculas."""
    dto = ColorCrearIn(nombre="  Azul   Cobalto  ", codigo_hex="  #1e40af  ")
    assert dto.nombre == "Azul Cobalto"
    assert dto.codigo_hex == "#1E40AF"


def test_esquema_color_hex_invalido():
    """AC-10: Rechazo de formatos hexadecimales invalidos."""
    casos_invalidos = ["#FFF", "123456", "#GGGGGG", "#12345", "#1234567"]
    for hex_invalido in casos_invalidos:
        with pytest.raises(ValidationError):
            ColorCrearIn(nombre="Rojo Test", codigo_hex=hex_invalido)


# =============================================================================
# 2. PRUEBAS DE EXCEPCIONES DE DOMINIO Y JERARQUIA
# =============================================================================


def test_jerarquia_excepciones_dominio():
    """AC-3, AC-4, AC-5: Verificacion de jerarquia y codigos tipados."""
    err_circ = ReferenciaCircularError(id_categoria=2, id_padre=2)
    assert isinstance(err_circ, UnprocessableEntityError)
    assert err_circ.code == "REFERENCIA_CIRCULAR_NO_PERMITIDA"

    err_dup = CategoriaDuplicadaError(nombre="Blusas")
    assert isinstance(err_dup, ConflictError)
    assert err_dup.code == "CATEGORIA_DUPLICADA"

    err_dep = CategoriaConDependenciasError(motivo="Posee subcategorias dependientes.")
    assert isinstance(err_dep, ConflictError)
    assert err_dep.code == "CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS"

    err_talla_uso = TallaEnUsoError(total_variantes=3)
    assert isinstance(err_talla_uso, ConflictError)
    assert err_talla_uso.code == "TALLA_EN_USO_EN_VARIANTES"

    err_color_uso = ColorEnUsoError(total_variantes=4)
    assert isinstance(err_color_uso, ConflictError)
    assert err_color_uso.code == "COLOR_EN_USO_EN_VARIANTES"


# =============================================================================
# 3. PRUEBAS DE SERVICIO: DETECCION DE CICLOS Y REGLAS DE INTEGRIDAD
# =============================================================================


def test_servicio_categoria_deteccion_ciclo_directo():
    """AC-4: Rechazo inmediato cuando una categoria se asigna a si misma como padre."""
    db_mock = MagicMock()
    servicio = ServicioGestionAtributos(db_mock)

    with pytest.raises(ReferenciaCircularError) as exc_info:
        servicio._verificar_ciclo_jerarquico(id_categoria=5, nuevo_id_padre=5)
    assert exc_info.value.code == "REFERENCIA_CIRCULAR_NO_PERMITIDA"


def test_servicio_categoria_deteccion_ciclo_indirecto():
    """AC-4: Deteccion de ciclo jerarquico ascendente A -> B -> C -> A."""
    db_mock = MagicMock()

    # Arbol: Cat 1 (padre de 2), Cat 2 (padre de 3), se intenta poner Cat 3 como padre de Cat 1
    cat3 = MagicMock(id_categoria=3, id_categoria_padre=2)
    cat2 = MagicMock(id_categoria=2, id_categoria_padre=1)
    cat1 = MagicMock(id_categoria=1, id_categoria_padre=None)

    def mock_get(model, id_val):
        if id_val == 3:
            return cat3
        if id_val == 2:
            return cat2
        if id_val == 1:
            return cat1
        return None

    db_mock.get.side_effect = mock_get

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(ReferenciaCircularError) as exc_info:
        servicio._verificar_ciclo_jerarquico(id_categoria=1, nuevo_id_padre=3)
    assert exc_info.value.code == "REFERENCIA_CIRCULAR_NO_PERMITIDA"


def test_servicio_categoria_crear_duplicada_lanza_409():
    """AC-3: Rechazo de categoria duplicada en servicio."""
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = MagicMock(id_categoria=1, nombre="Vestidos")

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(CategoriaDuplicadaError) as exc_info:
        servicio.crear_categoria(CategoriaCrearIn(nombre="vestidos"))
    assert exc_info.value.code == "CATEGORIA_DUPLICADA"


def test_servicio_categoria_eliminar_bloqueada_por_subcategorias():
    """AC-5: Bloqueo de eliminacion de categoria con subcategorias hijas."""
    db_mock = MagicMock()
    cat_mock = MagicMock(id_categoria=10, nombre="Prendas Superiores")
    db_mock.get.return_value = cat_mock
    # Subcategorias count = 2
    db_mock.execute.return_value.scalar.return_value = 2

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(CategoriaConDependenciasError) as exc_info:
        servicio.eliminar_categoria(id_categoria=10)
    assert exc_info.value.code == "CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS"


def test_servicio_categoria_eliminar_bloqueada_por_productos():
    """AC-5: Bloqueo de eliminacion de categoria con productos asociados."""
    db_mock = MagicMock()
    cat_mock = MagicMock(id_categoria=10, nombre="Prendas Superiores")
    db_mock.get.return_value = cat_mock
    # Primer count (hijas) = 0, segundo count (productos) = 5
    db_mock.execute.return_value.scalar.side_effect = [0, 5]

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(CategoriaConDependenciasError) as exc_info:
        servicio.eliminar_categoria(id_categoria=10)
    assert exc_info.value.code == "CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS"


def test_servicio_talla_eliminar_bloqueada_por_variantes():
    """AC-8: Bloqueo de eliminacion de talla asignada a variantes."""
    db_mock = MagicMock()
    talla_mock = MagicMock(id_talla=3, codigo="M", orden=2)
    db_mock.get.return_value = talla_mock
    db_mock.execute.return_value.scalar.return_value = 8

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(TallaEnUsoError) as exc_info:
        servicio.eliminar_talla(id_talla=3)
    assert exc_info.value.code == "TALLA_EN_USO_EN_VARIANTES"


def test_servicio_color_eliminar_bloqueada_por_variantes():
    """AC-11: Bloqueo de eliminacion de color asignado a variantes."""
    db_mock = MagicMock()
    color_mock = MagicMock(id_color=4, nombre="Negro Ebano", codigo_hex="#000000")
    db_mock.get.return_value = color_mock
    db_mock.execute.return_value.scalar.return_value = 12

    servicio = ServicioGestionAtributos(db_mock)
    with pytest.raises(ColorEnUsoError) as exc_info:
        servicio.eliminar_color(id_color=4)
    assert exc_info.value.code == "COLOR_EN_USO_EN_VARIANTES"


# =============================================================================
# 4. PRUEBAS HTTP Y CONTROL DE ACCESO RBAC (AC-1)
# =============================================================================


def test_endpoints_admin_sin_token_401(client):
    """AC-1: Endpoints administrativos exigen token Bearer (HTTP 401)."""
    rutas = [
        "/api/v1/admin/categorias",
        "/api/v1/admin/tallas",
        "/api/v1/admin/colores",
    ]
    for ruta in rutas:
        resp = client.get(ruta)
        assert resp.status_code == 401
        assert resp.json()["code"] == "TOKEN_INVALIDO"


def test_endpoints_admin_con_rol_cliente_403(client):
    """AC-1: Endpoints administrativos rechazan rol 'cliente' (HTTP 403)."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cliente_mock()
    try:
        token_cliente = create_access_token({"sub": "2", "rol": "cliente"})
        headers = {"Authorization": f"Bearer {token_cliente}"}
        for ruta in ["/api/v1/admin/categorias", "/api/v1/admin/tallas", "/api/v1/admin/colores"]:
            resp = client.get(ruta, headers=headers)
            assert resp.status_code == 403
            assert resp.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# =============================================================================
# 5. PRUEBAS DE ENDPOINTS PUBLICOS (AC-12)
# =============================================================================


def test_endpoints_publicos_categorias_tallas_colores_200(client):
    """AC-12: Endpoints publicos de lectura accesibles sin autenticacion."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalars.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        for ruta in ["/api/v1/categorias", "/api/v1/tallas", "/api/v1/colores"]:
            resp = client.get(ruta)
            assert resp.status_code == 200
            assert isinstance(resp.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)


# =============================================================================
# 6. PRUEBAS DE OPERACIONES ADMINISTRATIVAS (HTTP INTEGRATION)
# =============================================================================


def test_endpoint_admin_crear_categoria_exito_201(client):
    """AC-2: Creacion exitosa de categoria con rol administrador (HTTP 201)."""
    mock_db = MagicMock()
    # No duplicado
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    def mock_refresh(inst):
        inst.id_categoria = 99

    mock_db.refresh.side_effect = mock_refresh

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"nombre": "Vestidos Midi", "id_categoria_padre": None}
        resp = client.post(
            "/api/v1/admin/categorias",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["id_categoria"] == 99
        assert data["nombre"] == "Vestidos Midi"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_categoria_duplicada_409(client):
    """AC-3: Conflicto 409 al registrar categoria con nombre existente."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock(id_categoria=1, nombre="Vestidos")

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"nombre": "vestidos", "id_categoria_padre": None}
        resp = client.post(
            "/api/v1/admin/categorias",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "CATEGORIA_DUPLICADA"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_actualizar_categoria_referencia_circular_422(client):
    """AC-4: Respuesta 422 ante intento de referencia circular."""
    mock_db = MagicMock()
    cat_existente = MagicMock(id_categoria=7, nombre="Pantalones", id_categoria_padre=None)
    mock_db.get.return_value = cat_existente

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        # Intento de asignarse a si misma como padre
        payload = {"id_categoria_padre": 7}
        resp = client.put(
            "/api/v1/admin/categorias/7",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 422
        assert resp.json()["code"] == "REFERENCIA_CIRCULAR_NO_PERMITIDA"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_eliminar_categoria_con_dependencias_409(client):
    """AC-5: Conflicto 409 al intentar eliminar categoria con productos asociados."""
    mock_db = MagicMock()
    cat_existente = MagicMock(id_categoria=5, nombre="Prendas")
    mock_db.get.return_value = cat_existente
    # Primer count = 0 subcategorias, segundo count = 3 productos
    mock_db.execute.return_value.scalar.side_effect = [0, 3]

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/categorias/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_eliminar_categoria_exito_204(client):
    """AC-5: Eliminacion exitosa (HTTP 204) cuando no existen dependencias."""
    mock_db = MagicMock()
    cat_existente = MagicMock(id_categoria=5, nombre="Prendas Vacias")
    mock_db.get.return_value = cat_existente
    # Cero subcategorias, cero productos
    mock_db.execute.return_value.scalar.side_effect = [0, 0]

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/categorias/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 204
        assert mock_db.delete.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_talla_exito_201(client):
    """AC-6: Creacion de talla con orden secuencial (HTTP 201)."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    def mock_refresh(inst):
        inst.id_talla = 12

    mock_db.refresh.side_effect = mock_refresh

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"codigo": "xxl", "orden": 6}
        resp = client.post(
            "/api/v1/admin/tallas",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["codigo"] == "XXL"
        assert data["orden"] == 6
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_talla_duplicada_409(client):
    """AC-7: Conflicto 409 al registrar codigo de talla duplicado."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock(id_talla=1, codigo="S")

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"codigo": "S", "orden": 1}
        resp = client.post(
            "/api/v1/admin/tallas",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "TALLA_DUPLICADA"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_eliminar_talla_en_uso_409(client):
    """AC-8: Conflicto 409 al eliminar talla en uso en variantes."""
    mock_db = MagicMock()
    mock_db.get.return_value = MagicMock(id_talla=2, codigo="M")
    mock_db.execute.return_value.scalar.return_value = 15

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/tallas/2",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "TALLA_EN_USO_EN_VARIANTES"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_color_exito_201(client):
    """AC-9: Creacion exitosa de color textil con codigo #HEX (HTTP 201)."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    def mock_refresh(inst):
        inst.id_color = 33

    mock_db.refresh.side_effect = mock_refresh

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"nombre": "Verde Oliva", "codigo_hex": "#556B2F"}
        resp = client.post(
            "/api/v1/admin/colores",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["nombre"] == "Verde Oliva"
        assert data["codigo_hex"] == "#556B2F"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_color_hex_invalido_422(client):
    """AC-10: Pydantic rechaza codigo hex invalido con HTTP 422."""
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"nombre": "Color Malo", "codigo_hex": "no-es-hex"}
        resp = client.post(
            "/api/v1/admin/colores",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_color_duplicado_409(client):
    """AC-10: Conflicto 409 al registrar nombre de color existente."""
    mock_db = MagicMock()
    mock_db.execute.return_value.scalar_one_or_none.return_value = MagicMock(id_color=1, nombre="Rojo")

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {"nombre": "rojo", "codigo_hex": "#FF0000"}
        resp = client.post(
            "/api/v1/admin/colores",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "COLOR_DUPLICADO"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_eliminar_color_en_uso_409(client):
    """AC-11: Conflicto 409 al eliminar color en uso en variantes."""
    mock_db = MagicMock()
    mock_db.get.return_value = MagicMock(id_color=5, nombre="Azul")
    mock_db.execute.return_value.scalar.return_value = 20

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/colores/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 409
        assert resp.json()["code"] == "COLOR_EN_USO_EN_VARIANTES"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_eliminar_color_exito_204(client):
    """AC-11: Eliminacion exitosa de color textil libre de dependencias (HTTP 204)."""
    mock_db = MagicMock()
    mock_db.get.return_value = MagicMock(id_color=5, nombre="Azul Libre")
    mock_db.execute.return_value.scalar.return_value = 0

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        resp = client.delete(
            "/api/v1/admin/colores/5",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert resp.status_code == 204
        assert mock_db.delete.called
        assert mock_db.commit.called
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
