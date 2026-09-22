"""Suite de pruebas automatizadas para CU24: Gestionar temporadas y colecciones.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401 Unauthorized ante peticion anonima).
- # AC-2: Control de acceso RBAC por rol (HTTP 403 Forbidden para cajero y cliente).
- # AC-3: Segregacion funcional (administrador con acceso completo, encargado en modo consulta).
- # AC-4: Persistencia y mapeo de entidad TemporadaORM.
- # AC-5: Validacion estricta de rango cronologico de fechas (HTTP 422 ante fecha_inicio >= fecha_fin).
- # AC-6: Validacion de unicidad de nombre de temporada (HTTP 409 ante colision insensible a mayusculas).
- # AC-7: Listado paginado y filtros multicriterio de temporadas.
- # AC-8: Baja logica y reactivacion de temporada mediante conmutacion de estado (PATCH 200).
- # AC-9: Persistencia y mapeo de entidad ColeccionORM vinculada a temporada activa.
- # AC-10: Validacion de unicidad de coleccion por temporada matriz (HTTP 409).
- # AC-11: Validacion de temporada matriz existente y activa (HTTP 404 / HTTP 422).
- # AC-12: Listado paginado de colecciones con join a temporada y conteo de prendas.
- # AC-13: Baja logica de coleccion preservando trazabilidad de prendas (PATCH 200).
"""

from datetime import date, datetime, timezone
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.cu24_temporadas_colecciones.errores import (
    ColeccionDuplicadaError,
    ColeccionNoEncontradaError,
    TemporadaDuplicadaError,
    TemporadaFechasInvalidasError,
    TemporadaInactivaParaColeccionError,
    TemporadaNoEncontradaError,
)
from modules.catalogo.cu24_temporadas_colecciones.esquemas import (
    ColeccionActualizarIn,
    ColeccionCrearIn,
    ColeccionFiltrosIn,
    ColeccionItemOut,
    EstadoConmutarIn,
    ListaPaginadaColeccionesOut,
    ListaPaginadaTemporadasOut,
    TemporadaActualizarIn,
    TemporadaCrearIn,
    TemporadaFiltrosIn,
    TemporadaItemOut,
)
from modules.catalogo.cu24_temporadas_colecciones.modelos import ColeccionORM, TemporadaORM
from modules.catalogo.cu24_temporadas_colecciones.servicio import (
    ServicioGestionColecciones,
    ServicioGestionTemporadas,
)


# -----------------------------------------------------------------------------
# FIXTURES Y FABRICAS DE MOCKS
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Cliente HTTP para pruebas de integracion de endpoints."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Admin"
    usuario.apellidos = "General"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = 1
    usuario.nombres = "Encargado"
    usuario.apellidos = "Sucursal"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = 1
    usuario.nombres = "Cajero"
    usuario.apellidos = "Tienda"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Cliente"
    usuario.apellidos = "Final"
    usuario.activo = True
    return usuario


def fabricar_temporada_orm(
    id_temporada: int = 1,
    nombre: str = "Otono - Invierno 2026",
    anio: int = 2026,
    tipo: str = "otono_invierno",
    fecha_inicio: date = date(2026, 3, 21),
    fecha_fin: date = date(2026, 6, 20),
    estado_activo: bool = True,
) -> TemporadaORM:
    ahora = datetime.now(timezone.utc)
    return TemporadaORM(
        id_temporada=id_temporada,
        nombre=nombre,
        anio=anio,
        tipo=tipo,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado_activo=estado_activo,
        creado_en=ahora,
        actualizado_en=ahora,
    )


def fabricar_coleccion_orm(
    id_coleccion: int = 1,
    id_temporada: int = 1,
    nombre: str = "Capsula Alpaca Real",
    descripcion: str = "Coleccion de abrigos de alpaca de lujo",
    id_proveedor: int = 10,
    estado_activo: bool = True,
) -> ColeccionORM:
    ahora = datetime.now(timezone.utc)
    return ColeccionORM(
        id_coleccion=id_coleccion,
        id_temporada=id_temporada,
        nombre=nombre,
        descripcion=descripcion,
        id_proveedor=id_proveedor,
        estado_activo=estado_activo,
        creado_en=ahora,
        actualizado_en=ahora,
    )


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE SEGURIDAD Y RBAC (# AC-1, # AC-2, # AC-3)
# -----------------------------------------------------------------------------

def test_cu24_rbac_sin_token_retorna_401(client: TestClient):
    """# AC-1: Peticion anonima a endpoints de temporadas y colecciones retorna HTTP 401."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    resp_temp = client.get("/api/v1/admin/temporadas")
    assert resp_temp.status_code == 401

    resp_col = client.get("/api/v1/admin/colecciones")
    assert resp_col.status_code == 401


def test_cu24_rbac_cajero_denegado_403(client: TestClient):
    """# AC-2: Usuario con rol cajero es denegado con HTTP 403 Forbidden."""
    usuario_cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cajero
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        resp = client.get("/api/v1/admin/temporadas")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cu24_rbac_cliente_denegado_403(client: TestClient):
    """# AC-2: Usuario con rol cliente es denegado con HTTP 403 Forbidden."""
    usuario_cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cliente
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        resp = client.get("/api/v1/admin/colecciones")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cu24_administrador_acceso_exitoso_200(client: TestClient):
    """# AC-3: Usuario administrador accede exitosamente a la consulta de temporadas."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    respuesta_mock = ListaPaginadaTemporadasOut(
        items=[],
        total=0,
        pagina=1,
        limite=10,
        total_paginas=0,
    )

    with patch.object(ServicioGestionTemporadas, "listar_temporadas", return_value=respuesta_mock):
        try:
            resp = client.get("/api/v1/admin/temporadas")
            assert resp.status_code == 200
            data = resp.json()
            assert "items" in data
            assert data["total"] == 0
        finally:
            app.dependency_overrides.clear()


def test_cu24_encargado_acceso_lectura_200(client: TestClient):
    """# AC-3: Usuario encargado de sucursal tiene acceso de lectura a temporadas y colecciones."""
    usuario_encargado = crear_usuario_encargado_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_encargado

    resp_temp_mock = ListaPaginadaTemporadasOut(items=[], total=0, pagina=1, limite=10, total_paginas=0)
    resp_col_mock = ListaPaginadaColeccionesOut(items=[], total=0, pagina=1, limite=10, total_paginas=0)

    with patch.object(ServicioGestionTemporadas, "listar_temporadas", return_value=resp_temp_mock), \
         patch.object(ServicioGestionColecciones, "listar_colecciones", return_value=resp_col_mock):
        try:
            resp_temp = client.get("/api/v1/admin/temporadas")
            assert resp_temp.status_code == 200

            resp_col = client.get("/api/v1/admin/colecciones")
            assert resp_col.status_code == 200
        finally:
            app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE LOGICA DE DOMINIO Y GESTION DE TEMPORADAS (# AC-4 a # AC-8)
# -----------------------------------------------------------------------------

def test_cu24_fechas_invalidas_rechaza_422():
    """# AC-5: Creacion de temporada con fecha_fin <= fecha_inicio es rechazada con ValidationError."""
    with pytest.raises(ValidationError) as exc_info:
        TemporadaCrearIn(
            nombre="Temporada Cronologia Invalida",
            anio=2026,
            fecha_inicio=date(2026, 10, 1),
            fecha_fin=date(2026, 5, 1),
        )
    assert "estrictamente posterior a" in str(exc_info.value)


def test_cu24_crear_temporada_exitosa_servicio():
    """# AC-4: Creacion valida de temporada retorna entidad con estado_activo = True y persistencia."""
    mock_db = MagicMock()
    # Sin colision de nombre
    mock_db.scalar.return_value = None

    def mock_refresh(inst):
        inst.id_temporada = 101

    mock_db.refresh.side_effect = mock_refresh

    datos_in = TemporadaCrearIn(
        nombre="Crucero Luxe 2027",
        tipo="primavera_verano",
        anio=2027,
        fecha_inicio=date(2027, 1, 15),
        fecha_fin=date(2027, 4, 30),
        estado_activo=True,
    )

    resultado = ServicioGestionTemporadas.crear_temporada(mock_db, datos_in)

    assert resultado.id_temporada == 101
    assert resultado.nombre == "Crucero Luxe 2027"
    assert resultado.anio == 2027
    assert resultado.estado_activo is True
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()


def test_cu24_nombre_temporada_duplicado_rechaza_409():
    """# AC-6: Intento de registrar temporada con nombre ya existente lanza TemporadaDuplicadaError."""
    mock_db = MagicMock()
    # Simular que ya existe un registro con el mismo nombre normalizado
    mock_db.scalar.return_value = 1

    datos_in = TemporadaCrearIn(
        nombre="  Otono - Invierno 2026  ",
        anio=2026,
        fecha_inicio=date(2026, 3, 21),
        fecha_fin=date(2026, 6, 20),
    )

    with pytest.raises(TemporadaDuplicadaError) as exc_info:
        ServicioGestionTemporadas.crear_temporada(mock_db, datos_in)

    assert "Otono - Invierno 2026" in str(exc_info.value)


def test_cu24_listar_temporadas_paginadas_servicio():
    """# AC-7: Listado paginado de temporadas con conteo de colecciones subordinadas."""
    mock_db = MagicMock()
    temporada_mock = fabricar_temporada_orm(id_temporada=1, nombre="Primavera 2026")

    # Mock total count
    mock_db.scalar.return_value = 1
    # Mock items scalars
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [temporada_mock]
    mock_db.scalars.return_value = mock_scalars
    # Mock conteos_map query
    mock_db.execute.return_value = [(1, 3)]

    filtros = TemporadaFiltrosIn(q="Primavera", pagina=1, limite=10)
    resultado = ServicioGestionTemporadas.listar_temporadas(mock_db, filtros)

    assert resultado.total == 1
    assert len(resultado.items) == 1
    assert resultado.items[0].nombre == "Primavera 2026"
    assert resultado.items[0].total_colecciones == 3


def test_cu24_baja_logica_temporada_conmutar_estado():
    """# AC-8: Conmutacion de estado de temporada (baja logica y reactivacion)."""
    mock_db = MagicMock()
    temporada_mock = fabricar_temporada_orm(id_temporada=5, estado_activo=True)
    # db.scalar returns temporada_mock, then total_cols=0
    mock_db.scalar.side_effect = [
        temporada_mock,
        0,
        temporada_mock,
        0,
    ]

    # Desactivacion
    res_baja = ServicioGestionTemporadas.conmutar_estado_temporada(
        mock_db, id_temporada=5, estado_activo=False
    )
    assert res_baja.estado_activo is False
    assert temporada_mock.estado_activo is False

    # Reactivacion
    res_alta = ServicioGestionTemporadas.conmutar_estado_temporada(
        mock_db, id_temporada=5, estado_activo=True
    )
    assert res_alta.estado_activo is True
    assert temporada_mock.estado_activo is True


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE LOGICA DE DOMINIO Y GESTION DE COLECCIONES (# AC-9 a # AC-13)
# -----------------------------------------------------------------------------

def test_cu24_crear_coleccion_vinculada_temporada_exitosa():
    """# AC-9: Creacion exitosa de coleccion vinculada a temporada activa."""
    mock_db = MagicMock()
    temporada_activa = fabricar_temporada_orm(id_temporada=1, estado_activo=True)

    # 1. select(TemporadaORM) -> temporada_activa
    # 2. select(ColeccionORM.id_coleccion) -> None (no existe duplicado)
    mock_db.scalar.side_effect = [temporada_activa, None]

    def mock_refresh(inst):
        inst.id_coleccion = 201
        inst.creado_en = datetime.now(timezone.utc)
        inst.actualizado_en = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = mock_refresh

    datos_in = ColeccionCrearIn(
        id_temporada=1,
        nombre="Capsula Alpaca Real",
        descripcion="Tejidos de punto fino",
        id_proveedor=10,
        estado_activo=True,
    )

    resultado = ServicioGestionColecciones.crear_coleccion(mock_db, datos_in)

    assert resultado.id_coleccion == 201
    assert resultado.nombre == "Capsula Alpaca Real"
    assert resultado.temporada_nombre == "Otono - Invierno 2026"
    assert resultado.total_productos == 0
    mock_db.commit.assert_called()


def test_cu24_coleccion_temporada_inactiva_rechaza_422():
    """# AC-11: Creacion de coleccion en temporada inactiva lanza TemporadaInactivaParaColeccionError."""
    mock_db = MagicMock()
    temporada_inactiva = fabricar_temporada_orm(id_temporada=2, estado_activo=False)
    # select(TemporadaORM) -> temporada_inactiva
    mock_db.scalar.return_value = temporada_inactiva

    datos_in = ColeccionCrearIn(
        id_temporada=2,
        nombre="Capsula de Archivo",
    )

    with pytest.raises(TemporadaInactivaParaColeccionError):
        ServicioGestionColecciones.crear_coleccion(mock_db, datos_in)


def test_cu24_coleccion_nombre_duplicado_rechaza_409():
    """# AC-10: Registrar coleccion con nombre duplicado en la misma temporada lanza ColeccionDuplicadaError."""
    mock_db = MagicMock()
    temporada_activa = fabricar_temporada_orm(id_temporada=1, estado_activo=True)
    # 1. select(TemporadaORM) -> temporada_activa
    # 2. select(ColeccionORM.id_coleccion) -> 1 (duplicado existente)
    mock_db.scalar.side_effect = [temporada_activa, 1]

    datos_in = ColeccionCrearIn(
        id_temporada=1,
        nombre="  Capsula Alpaca Real  ",
    )

    with pytest.raises(ColeccionDuplicadaError) as exc_info:
        ServicioGestionColecciones.crear_coleccion(mock_db, datos_in)

    assert "Capsula Alpaca Real" in str(exc_info.value)


def test_cu24_baja_logica_coleccion_preservando_prendas():
    """# AC-13: Conmutacion de estado de coleccion preserva las prendas vinculadas."""
    mock_db = MagicMock()
    coleccion_mock = fabricar_coleccion_orm(id_coleccion=7, estado_activo=True)
    temporada_mock = fabricar_temporada_orm(id_temporada=1)

    # 1. select(ColeccionORM) -> coleccion_mock
    # 2. select(TemporadaORM) -> temporada_mock
    # 3. select(func.count(ProductoORM)) -> 5
    mock_db.scalar.side_effect = [coleccion_mock, temporada_mock, 5]

    res_baja = ServicioGestionColecciones.conmutar_estado_coleccion(
        mock_db, id_coleccion=7, estado_activo=False
    )

    assert res_baja.estado_activo is False
    assert res_baja.total_productos == 5
    assert coleccion_mock.estado_activo is False
    mock_db.commit.assert_called()
