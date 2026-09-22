"""Pruebas unitarias y de integracion para CU21: Gestionar Sucursales y Ciudades.

Cubre estrictamente los criterios de aceptacion:
- # AC-1: Seguridad RBAC (JWT con rol administrador requerido).
- # AC-2: Creacion de ciudad normalizada en UTC.
- # AC-3: Rechazo de ciudad duplicada (409 Conflict).
- # AC-4: Creacion de sucursal con invariantes y unicidad.
- # AC-5: Rechazo de horarios inconsistentes (422 Unprocessable Entity).
- # AC-6: Proteccion de integridad en baja de ciudad con dependencias activas (409 Conflict).
- # AC-7: Baja logica y restriccion de integridad en desactivacion de sucursal (409 Conflict).
- # AC-8: Consulta publica de sucursales activas.
- # AC-9: Consulta administrativa consolidada y metricas de sede.
"""

from datetime import datetime, time, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from core.errors import AuthenticationError, AuthorizationError, ConflictError
from core.security import create_access_token
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.cu21_sucursales_ciudades.errores import (
    CiudadConDependenciasError,
    CiudadDuplicadaError,
    CiudadNoEncontradaError,
    HorarioSucursalInvalidoError,
    SucursalConOperacionesPendientesError,
    SucursalDuplicadaError,
    SucursalNoEncontradaError,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.esquemas import (
    CiudadActualizarIn,
    CiudadCrearIn,
    CiudadOut,
    SucursalActualizarIn,
    SucursalAdminOut,
    SucursalCrearIn,
    SucursalEstadoIn,
    SucursalPublicaOut,
)
from modules.gestion_operativa.cu21_sucursales_ciudades.servicio import (
    ServicioGestionSucursal,
)
from modules.gestion_operativa.modelos import CiudadORM, SucursalORM


# -----------------------------------------------------------------------------
# FIXTURES Y UTILIDADES
# -----------------------------------------------------------------------------


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


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE ESQUEMAS PYDANTIC (VALIDACION DE INVARIANTES)
# -----------------------------------------------------------------------------


def test_esquema_ciudad_crear_valido():
    # AC-2: Creacion de ciudad valida con normalizacion de espacios
    datos = CiudadCrearIn(nombre="  Santa Cruz de la Sierra  ", pais="Bolivia")
    assert datos.nombre == "Santa Cruz de la Sierra"
    assert datos.pais == "Bolivia"


def test_esquema_ciudad_crear_nombre_muy_corto():
    # AC-2: Nombre menor a 2 caracteres debe fallar
    with pytest.raises(ValidationError):
        CiudadCrearIn(nombre="A", pais="Bolivia")


def test_esquema_sucursal_crear_valido():
    # AC-4: Sucursal valida con horarios coherentes
    datos = SucursalCrearIn(
        id_ciudad=1,
        nombre="Boutique Serrano Central",
        direccion="Av. San Martin #123, Equipetrol",
        telefono="+591 3 3344556",
        horario_apertura=time(9, 30),
        horario_cierre=time(20, 0),
    )
    assert datos.id_ciudad == 1
    assert datos.nombre == "Boutique Serrano Central"
    assert datos.horario_cierre > datos.horario_apertura


def test_esquema_sucursal_crear_horario_invalido():
    # AC-5: Rechazo si horario_cierre <= horario_apertura
    with pytest.raises(ValidationError) as exc_info:
        SucursalCrearIn(
            id_ciudad=1,
            nombre="Boutique Invalida",
            direccion="Calle Falsa 123",
            horario_apertura=time(20, 0),
            horario_cierre=time(9, 0),
        )
    assert "El horario de cierre debe ser cronologicamente posterior" in str(exc_info.value)


def test_esquema_sucursal_actualizar_horarios_inconsistentes():
    # AC-5: Rechazo en actualizacion si los horarios son contradictorios
    with pytest.raises(ValidationError):
        SucursalActualizarIn(
            horario_apertura=time(19, 0),
            horario_cierre=time(18, 0),
        )


# -----------------------------------------------------------------------------
# 2. PRUEBAS UNITARIAS DE SERVICIO (LOGICA DE DOMINIO E INVARIANTES)
# -----------------------------------------------------------------------------


def test_servicio_crear_ciudad_exitosa():
    # AC-2: El sistema debera registrar la ciudad y responder con datos normalizados
    db_mock = MagicMock()
    db_mock.execute.return_value.scalar_one_or_none.return_value = None

    def simular_refresh(instancia):
        instancia.id_ciudad = 10
        instancia.creado_en = datetime.now(timezone.utc)

    db_mock.refresh.side_effect = simular_refresh

    servicio = ServicioGestionSucursal(db_mock)
    salida = servicio.crear_ciudad(CiudadCrearIn(nombre="Cochabamba", pais="Bolivia"))

    assert salida.id_ciudad == 10
    assert salida.nombre == "Cochabamba"
    assert salida.total_sucursales == 0
    assert db_mock.commit.called


def test_servicio_crear_ciudad_duplicada():
    # AC-3: Si el nombre ya existe, rechazar con CiudadDuplicadaError (409)
    db_mock = MagicMock()
    ciudad_existente = CiudadORM(id_ciudad=1, nombre="La Paz", pais="Bolivia")
    db_mock.execute.return_value.scalar_one_or_none.return_value = ciudad_existente

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(CiudadDuplicadaError) as exc_info:
        servicio.crear_ciudad(CiudadCrearIn(nombre="la paz", pais="Bolivia"))

    assert exc_info.value.code == "CIUDAD_DUPLICADA"


def test_servicio_crear_sucursal_ciudad_no_existe():
    # AC-4: Si la ciudad no existe, lanzar CiudadNoEncontradaError (404)
    db_mock = MagicMock()
    db_mock.get.return_value = None

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(CiudadNoEncontradaError):
        servicio.crear_sucursal(
            SucursalCrearIn(
                id_ciudad=999,
                nombre="Boutique 999",
                direccion="Av. Principal 123",
                horario_apertura=time(9, 0),
                horario_cierre=time(20, 0),
            )
        )


def test_servicio_crear_sucursal_duplicada_en_ciudad():
    # AC-4: Unicidad (id_ciudad, nombre)
    db_mock = MagicMock()
    db_mock.get.return_value = CiudadORM(id_ciudad=1, nombre="Santa Cruz")
    db_mock.execute.return_value.scalar_one_or_none.return_value = SucursalORM(
        id_sucursal=1, id_ciudad=1, nombre="Atelier Central"
    )

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(SucursalDuplicadaError) as exc_info:
        servicio.crear_sucursal(
            SucursalCrearIn(
                id_ciudad=1,
                nombre="atelier central",
                direccion="Calle Ayacucho 45",
                horario_apertura=time(9, 0),
                horario_cierre=time(20, 0),
            )
        )
    assert exc_info.value.code == "SUCURSAL_DUPLICADA"


def test_servicio_eliminar_ciudad_con_sucursales_asociadas():
    # AC-6: Bloqueo de eliminacion si tiene sucursales activas (409 Conflict)
    db_mock = MagicMock()
    db_mock.get.return_value = CiudadORM(id_ciudad=1, nombre="Santa Cruz")
    # Conteo de sucursales = 2
    db_mock.execute.return_value.scalar.return_value = 2

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(CiudadConDependenciasError) as exc_info:
        servicio.eliminar_ciudad(id_ciudad=1)

    assert exc_info.value.code == "CIUDAD_CON_DEPENDENCIAS_ACTIVAS"
    assert "2 sucursal(es) asociada(s)" in exc_info.value.message


def test_servicio_desactivar_sucursal_con_reservas_activas():
    # AC-7: Bloqueo de desactivacion si mantiene reservas pendientes
    db_mock = MagicMock()
    sucursal = SucursalORM(
        id_sucursal=5,
        id_ciudad=1,
        nombre="Boutique Equipetrol",
        direccion="Av. San Martin",
        activa=True,
    )
    db_mock.get.return_value = sucursal

    # Simular reservas activas = 3
    db_mock.execute.return_value.scalar.return_value = 3

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(SucursalConOperacionesPendientesError) as exc_info:
        servicio.cambiar_estado_sucursal(id_sucursal=5, activa=False)

    assert exc_info.value.code == "SUCURSAL_CON_OPERACIONES_PENDIENTES"
    assert "reserva(s) pendiente(s)" in exc_info.value.message


def test_servicio_desactivar_sucursal_con_stock_disponible():
    # AC-7: Bloqueo de desactivacion si mantiene stock > 0
    db_mock = MagicMock()
    sucursal = SucursalORM(
        id_sucursal=6,
        id_ciudad=1,
        nombre="Boutique Monotributo",
        direccion="Av. Las Americas",
        activa=True,
    )
    db_mock.get.return_value = sucursal

    # Primer query (reservas = 0), segundo query (stock = 45)
    db_mock.execute.return_value.scalar.side_effect = [0, 45]

    servicio = ServicioGestionSucursal(db_mock)
    with pytest.raises(SucursalConOperacionesPendientesError) as exc_info:
        servicio.cambiar_estado_sucursal(id_sucursal=6, activa=False)

    assert exc_info.value.code == "SUCURSAL_CON_OPERACIONES_PENDIENTES"
    assert "45 prendas con inventario disponible" in exc_info.value.message


def test_servicio_desactivar_sucursal_limpia_exitoso():
    # AC-7: Desactivacion exitosa si no tiene reservas ni stock
    db_mock = MagicMock()
    sucursal = SucursalORM(
        id_sucursal=7,
        id_ciudad=1,
        nombre="Boutique Temporal",
        direccion="Av. Busch",
        horario_apertura=time(9, 0),
        horario_cierre=time(19, 0),
        activa=True,
        creado_en=datetime.now(timezone.utc),
    )
    ciudad = CiudadORM(id_ciudad=1, nombre="Santa Cruz")

    def mock_get(orm_cls, ident):
        if orm_cls == SucursalORM:
            return sucursal
        return ciudad

    db_mock.get.side_effect = mock_get
    # Reservas = 0, stock = 0, empleados = 0, stock_disp = 0, reservas_activas = 0
    db_mock.execute.return_value.scalar.return_value = 0

    servicio = ServicioGestionSucursal(db_mock)
    resultado = servicio.cambiar_estado_sucursal(id_sucursal=7, activa=False)

    assert resultado.activa is False
    assert sucursal.activa is False
    assert db_mock.commit.called


def test_servicio_listar_sucursales_publicas():
    # AC-8: Lista publica de sucursales activas
    db_mock = MagicMock()
    suc = SucursalORM(
        id_sucursal=1,
        id_ciudad=1,
        nombre="Boutique Atelier Central",
        direccion="Av. San Martin #123",
        telefono="+591 3 3344556",
        horario_apertura=time(10, 0),
        horario_cierre=time(21, 0),
        activa=True,
    )
    db_mock.execute.return_value.all.return_value = [(suc, "Santa Cruz de la Sierra")]

    servicio = ServicioGestionSucursal(db_mock)
    salida = servicio.listar_sucursales_publicas(id_ciudad=1)

    assert len(salida) == 1
    assert salida[0].nombre == "Boutique Atelier Central"
    assert salida[0].ciudad_nombre == "Santa Cruz de la Sierra"
    assert salida[0].horario_apertura == "10:00"
    assert salida[0].horario_cierre == "21:00"


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE INTEGRACION HTTP (ROUTER, AUTENTICACION Y RBAC)
# -----------------------------------------------------------------------------


def test_endpoint_publico_sucursales(client):
    # AC-8: Endpoint publico accesible sin token
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/sucursales")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_ciudades_sin_token_401(client):
    # AC-1: Acceso a /api/v1/admin/ciudades sin token devuelve 401
    app.dependency_overrides.pop(get_current_user, None)
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.get("/api/v1/admin/ciudades")
        assert response.status_code == 401
        assert response.json()["code"] == "TOKEN_INVALIDO"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_ciudades_con_rol_cliente_403(client):
    # AC-1: Acceso con rol cliente devuelve 403 Forbidden
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cliente_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_cliente = create_access_token({"sub": "2", "rol": "cliente"})
        response = client.get(
            "/api/v1/admin/ciudades",
            headers={"Authorization": f"Bearer {token_cliente}"},
        )
        assert response.status_code == 403
        assert response.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_ciudades_con_rol_admin_200(client):
    # AC-1: Acceso con rol administrador exitoso
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        response = client.get(
            "/api/v1/admin/ciudades",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_crear_sucursal_horarios_invalidos_422(client):
    # AC-5: Peticion con horario de cierre <= apertura retorna 422
    mock_db = MagicMock()
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        payload = {
            "id_ciudad": 1,
            "nombre": "Sucursal Horario Roto",
            "direccion": "Calle Invalida 100",
            "horario_apertura": "20:00",
            "horario_cierre": "08:00",
        }
        response = client.post(
            "/api/v1/admin/sucursales",
            headers={"Authorization": f"Bearer {token_admin}"},
            json=payload,
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)


def test_endpoint_admin_listar_sucursales_enriquecidas_200(client):
    # AC-9: Consulta administrativa con estadisticas de sede
    mock_db = MagicMock()
    mock_db.execute.return_value.all.return_value = []
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        token_admin = create_access_token({"sub": "1", "rol": "administrador"})
        response = client.get(
            "/api/v1/admin/sucursales",
            headers={"Authorization": f"Bearer {token_admin}"},
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_db, None)
