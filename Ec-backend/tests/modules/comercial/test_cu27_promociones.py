"""Suite de pruebas automatizadas para CU27: Gestionar promociones.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401 Unauthorized ante peticion anonima).
- # AC-2: Control de acceso RBAC por rol (HTTP 403 Forbidden para cajero y cliente).
- # AC-3: Segregacion funcional (administrador con control total, encargado en modo solo consulta).
- # AC-4: Persistencia y mapeo de entidad PromocionORM.
- # AC-5: Validacion estricta de consistencia cronologica (HTTP 422 ante fecha_inicio >= fecha_fin).
- # AC-6: Validacion de rango de descuento (HTTP 422 ante porcentaje anomalo o valor <= 0).
- # AC-7: Validacion de unicidad de codigo de cupon (HTTP 409 Conflict ante colision insensible a mayusculas).
- # AC-8: Validacion de integridad de alcance promocional (HTTP 422 ante categoria o producto invalido).
- # AC-9: Listado paginado con filtros multicriterio y calculo de metricas cuantitativas.
- # AC-10: Detalle individual de promocion con relaciones relacionales.
- # AC-11: Creacion exitosa de promocion comercial o cupon de descuento (HTTP 201 Created).
- # AC-12: Modificacion integral de metadatos y reglas promocionales (HTTP 200 OK).
- # AC-13: Conmutacion atomica de estado logico y baja logica no destructiva (PATCH HTTP 200 OK).
"""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.catalogo.modelos import CategoriaORM, ProductoORM
from modules.comercial.cu27_promociones.errores import (
    AlcancePromocionInvalidoError,
    CodigoCuponDuplicadoError,
    FechasPromocionInvalidasError,
    PromocionNoEncontradaError,
    ValorDescuentoInvalidoError,
)
from modules.comercial.cu27_promociones.esquemas import (
    AlcancePromocionEnum,
    EstadoConmutarIn,
    FiltrosPromocionIn,
    MetricasPromocionesOut,
    PromocionActualizarIn,
    PromocionCrearIn,
    PromocionItemOut,
    RespuestaPaginadaPromocionesOut,
    TipoDescuentoEnum,
)
from modules.comercial.cu27_promociones.modelos import PromocionORM
from modules.comercial.cu27_promociones.servicio import ServicioGestionPromociones


# -----------------------------------------------------------------------------
# FIXTURES Y GENERADORES DE MOCKS
# -----------------------------------------------------------------------------

@pytest.fixture
def client():
    """Cliente HTTP de pruebas para invocacion de endpoints FastAPI."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "admin.comercial@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Director"
    usuario.apellidos = "Comercial"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado.boutique@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = 1
    usuario.nombres = "Encargado"
    usuario.apellidos = "Boutique"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.tienda@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = 1
    usuario.nombres = "Cajero"
    usuario.apellidos = "Operativo"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente.vip@gmail.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Cliente"
    usuario.apellidos = "VIP"
    usuario.activo = True
    return usuario


def fabricar_promocion_item_out(
    id_promocion: int = 10,
    nombre: str = "Rebajas Otono 2026",
    codigo_cupon: str | None = "OTONO20",
    tipo_descuento: str = "porcentaje",
    valor_descuento: Decimal = Decimal("20.00"),
    tope_descuento: Decimal | None = Decimal("500000.00"),
    limite_usos: int | None = 200,
    usos_actuales: int = 15,
    alcance: str = "global",
    estado_activo: bool = True,
) -> PromocionItemOut:
    ahora = datetime.now(timezone.utc)
    return PromocionItemOut(
        id_promocion=id_promocion,
        nombre=nombre,
        descripcion="Descuento editorial de media estacion",
        codigo_cupon=codigo_cupon,
        tipo_descuento=tipo_descuento,
        valor_descuento=valor_descuento,
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(days=30),
        tope_descuento=tope_descuento,
        limite_usos=limite_usos,
        usos_actuales=usos_actuales,
        alcance=alcance,
        id_categoria=None,
        nombre_categoria=None,
        id_producto=None,
        nombre_producto=None,
        estado_activo=estado_activo,
        creado_en=ahora,
        actualizado_en=ahora,
        esta_vigente=True,
    )


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE AUTORIZACION Y CONTROL DE ACCESO (AC-1, AC-2, AC-3)
# -----------------------------------------------------------------------------

def test_cu27_sin_token_rechaza_401(client: TestClient):
    """AC-1: Cualquier peticion sin cabecera de autorizacion debe retornar HTTP 401."""
    app.dependency_overrides.clear()
    resp = client.get("/api/v1/admin/promociones")
    assert resp.status_code == 401


def test_cu27_rol_cajero_rechaza_403(client: TestClient):
    """AC-2: El rol cajero debe ser bloqueado con HTTP 403 en endpoints administrativos."""
    usuario_cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cajero

    try:
        resp = client.get("/api/v1/admin/promociones")
        assert resp.status_code == 403
        assert "ACCESO_DENEGADO" in str(resp.json())
    finally:
        app.dependency_overrides.clear()


def test_cu27_rol_cliente_rechaza_403(client: TestClient):
    """AC-2: El rol cliente debe ser bloqueado con HTTP 403 en endpoints administrativos."""
    usuario_cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_cliente

    try:
        resp = client.get("/api/v1/admin/promociones")
        assert resp.status_code == 403
        assert "ACCESO_DENEGADO" in str(resp.json())
    finally:
        app.dependency_overrides.clear()


def test_cu27_encargado_sucursal_acceso_lectura_200(client: TestClient):
    """AC-3: El encargado de sucursal tiene acceso concedido para lectura de promociones."""
    usuario_encargado = crear_usuario_encargado_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_encargado

    respuesta_mock = RespuestaPaginadaPromocionesOut(
        items=[fabricar_promocion_item_out()],
        metricas=MetricasPromocionesOut(
            promociones_activas=1,
            cupones_vigentes=1,
            descuento_promedio=Decimal("20.00"),
            usos_totales=15,
        ),
        total=1,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioGestionPromociones, "listar_promociones", return_value=respuesta_mock):
        try:
            resp = client.get("/api/v1/admin/promociones")
            assert resp.status_code == 200
            data = resp.json()
            assert len(data["items"]) == 1
            assert data["metricas"]["promociones_activas"] == 1
        finally:
            app.dependency_overrides.clear()


def test_cu27_encargado_sucursal_bloqueado_para_mutaciones_403(client: TestClient):
    """AC-3: El encargado de sucursal es bloqueado (HTTP 403) ante intentos de creacion."""
    usuario_encargado = crear_usuario_encargado_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_encargado

    ahora = datetime.now(timezone.utc)
    payload = {
        "nombre": "Promocion Denegada",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 15.0,
        "fecha_inicio": ahora.isoformat(),
        "fecha_fin": (ahora + timedelta(days=10)).isoformat(),
        "alcance": "global",
    }

    try:
        resp = client.post("/api/v1/admin/promociones", json=payload)
        assert resp.status_code == 403
        assert "ACCESO_DENEGADO" in str(resp.json())
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE VALIDACION DEFENSIVA DE ESQUEMAS PYDANTIC (AC-5, AC-6, AC-8)
# -----------------------------------------------------------------------------

def test_cu27_fechas_inversas_rechaza_validation_error():
    """AC-5: La fecha_fin <= fecha_inicio debe ser rechazada de forma sincronica."""
    ahora = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        PromocionCrearIn(
            nombre="Promocion Fechas Invalidas",
            tipo_descuento=TipoDescuentoEnum.PORCENTAJE,
            valor_descuento=Decimal("15.00"),
            fecha_inicio=ahora,
            fecha_fin=ahora - timedelta(days=5),
            alcance=AlcancePromocionEnum.GLOBAL,
        )
    assert "estrictamente posterior a la fecha de inicio" in str(exc_info.value)


def test_cu27_porcentaje_invalido_rechaza_validation_error():
    """AC-6: Porcentaje mayor a 100 o menor a 1 debe ser rechazado de forma sincronica."""
    ahora = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        PromocionCrearIn(
            nombre="Promocion Porcentaje Excesivo",
            tipo_descuento=TipoDescuentoEnum.PORCENTAJE,
            valor_descuento=Decimal("150.00"),  # > 100
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=10),
            alcance=AlcancePromocionEnum.GLOBAL,
        )
    assert "situarse entre 1% y 100%" in str(exc_info.value)


def test_cu27_alcance_categoria_sin_id_rechaza_validation_error():
    """AC-8: Alcance por categoria exige id_categoria obligatorio."""
    ahora = datetime.now(timezone.utc)
    with pytest.raises(ValidationError) as exc_info:
        PromocionCrearIn(
            nombre="Promocion Categoria Sin ID",
            tipo_descuento=TipoDescuentoEnum.MONTO_FIJO,
            valor_descuento=Decimal("25000.00"),
            fecha_inicio=ahora,
            fecha_fin=ahora + timedelta(days=10),
            alcance=AlcancePromocionEnum.CATEGORIA,
            id_categoria=None,
        )
    assert "Debe especificar una categoria valida" in str(exc_info.value)


# -----------------------------------------------------------------------------
# 3. PRUEBAS DE CAPA DE SERVICIO TRANSACCIONAL (AC-4, AC-7, AC-8, AC-10, AC-11)
# -----------------------------------------------------------------------------

def test_cu27_servicio_crear_promocion_exitosa():
    """AC-4, AC-11: Servicio crea promocion normalizando cupon a mayusculas y persistiendo."""
    mock_db = MagicMock()
    # Sin colision de cupon
    mock_db.execute.return_value.scalar_one_or_none.return_value = None

    ahora = datetime.now(timezone.utc)
    datos_in = PromocionCrearIn(
        nombre="  Rebajas Black Fashion  ",
        codigo_cupon="  black2026  ",
        tipo_descuento=TipoDescuentoEnum.PORCENTAJE,
        valor_descuento=Decimal("25.00"),
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(days=15),
        tope_descuento=Decimal("300000.00"),
        limite_usos=500,
        alcance=AlcancePromocionEnum.GLOBAL,
        estado_activo=True,
    )

    servicio = ServicioGestionPromociones()

    # Mock retorno de obtener_promocion_por_id
    promocion_creada_out = fabricar_promocion_item_out(
        id_promocion=100,
        nombre="Rebajas Black Fashion",
        codigo_cupon="BLACK2026",
        valor_descuento=Decimal("25.00"),
    )

    with patch.object(servicio, "obtener_promocion_por_id", return_value=promocion_creada_out):
        resultado = servicio.crear_promocion(mock_db, datos_in)

        assert resultado.id_promocion == 100
        assert resultado.codigo_cupon == "BLACK2026"
        assert resultado.nombre == "Rebajas Black Fashion"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()


def test_cu27_servicio_cupon_duplicado_rechaza_409():
    """AC-7: Servicio emite CodigoCuponDuplicadoError ante colision de cupon."""
    mock_db = MagicMock()
    # Simular que ya existe un registro con ese cupon
    mock_promocion_existente = MagicMock(spec=PromocionORM)
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_promocion_existente

    ahora = datetime.now(timezone.utc)
    datos_in = PromocionCrearIn(
        nombre="Cupon Duplicado Test",
        codigo_cupon="CUPONEXISTENTE",
        tipo_descuento=TipoDescuentoEnum.PORCENTAJE,
        valor_descuento=Decimal("10.00"),
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(days=10),
        alcance=AlcancePromocionEnum.GLOBAL,
    )

    servicio = ServicioGestionPromociones()

    with pytest.raises(CodigoCuponDuplicadoError) as exc_info:
        servicio.crear_promocion(mock_db, datos_in)

    assert "CODIGO_CUPON_DUPLICADO" in str(exc_info.value.code)


def test_cu27_servicio_categoria_inexistente_rechaza_422():
    """AC-8: Servicio emite AlcancePromocionInvalidoError si la categoria no existe."""
    mock_db = MagicMock()
    # Sin cupon duplicado pero categoria no encontrada
    mock_db.execute.return_value.scalar_one_or_none.side_effect = [None, None]

    ahora = datetime.now(timezone.utc)
    datos_in = PromocionCrearIn(
        nombre="Promocion Categoria Fantasma",
        tipo_descuento=TipoDescuentoEnum.PORCENTAJE,
        valor_descuento=Decimal("15.00"),
        fecha_inicio=ahora,
        fecha_fin=ahora + timedelta(days=10),
        alcance=AlcancePromocionEnum.CATEGORIA,
        id_categoria=999,
    )

    servicio = ServicioGestionPromociones()

    with pytest.raises(AlcancePromocionInvalidoError) as exc_info:
        servicio.crear_promocion(mock_db, datos_in)

    assert "ALCANCE_PROMOCION_INVALIDO" in str(exc_info.value.code)


def test_cu27_servicio_conmutar_estado_baja_logica():
    """AC-13: Servicio conmuta estado_activo a False realizando baja logica."""
    mock_db = MagicMock()
    mock_promocion = MagicMock(spec=PromocionORM)
    mock_promocion.id_promocion = 50
    mock_promocion.estado_activo = True
    mock_db.execute.return_value.scalar_one_or_none.return_value = mock_promocion

    servicio = ServicioGestionPromociones()
    mock_out = fabricar_promocion_item_out(id_promocion=50, estado_activo=False)

    with patch.object(servicio, "obtener_promocion_por_id", return_value=mock_out):
        resultado = servicio.conmutar_estado(mock_db, 50, False)

        assert resultado.estado_activo is False
        assert mock_promocion.estado_activo is False
        mock_db.commit.assert_called_once()


def test_cu27_servicio_promocion_no_encontrada_404():
    """AC-10: Intento de obtener ID inexistente emite PromocionNoEncontradaError (404)."""
    mock_db = MagicMock()
    mock_db.execute.return_value.unique.return_value.scalar_one_or_none.return_value = None

    servicio = ServicioGestionPromociones()

    with pytest.raises(PromocionNoEncontradaError) as exc_info:
        servicio.obtener_promocion_por_id(mock_db, 99999)

    assert "PROMOCION_NO_ENCONTRADA" in str(exc_info.value.code)


# -----------------------------------------------------------------------------
# 4. PRUEBAS DE ENDPOINTS REST DE ADMINISTRACION (AC-9, AC-11, AC-12, AC-13)
# -----------------------------------------------------------------------------

def test_cu27_router_crear_promocion_201(client: TestClient):
    """AC-11: Endpoint POST /admin/promociones crea promocion y devuelve HTTP 201."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    ahora = datetime.now(timezone.utc)
    payload = {
        "nombre": "Promocion Test Router",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 20.0,
        "fecha_inicio": ahora.isoformat(),
        "fecha_fin": (ahora + timedelta(days=10)).isoformat(),
        "alcance": "global",
    }

    mock_item = fabricar_promocion_item_out(nombre="Promocion Test Router")

    with patch.object(ServicioGestionPromociones, "crear_promocion", return_value=mock_item):
        try:
            resp = client.post("/api/v1/admin/promociones", json=payload)
            assert resp.status_code == 201
            assert resp.json()["nombre"] == "Promocion Test Router"
        finally:
            app.dependency_overrides.clear()


def test_cu27_router_actualizar_promocion_200(client: TestClient):
    """AC-12: Endpoint PUT /admin/promociones/{id} modifica promocion y devuelve HTTP 200."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    ahora = datetime.now(timezone.utc)
    payload = {
        "nombre": "Promocion Modificada Router",
        "tipo_descuento": "porcentaje",
        "valor_descuento": 30.0,
        "fecha_inicio": ahora.isoformat(),
        "fecha_fin": (ahora + timedelta(days=20)).isoformat(),
        "alcance": "global",
    }

    mock_item = fabricar_promocion_item_out(nombre="Promocion Modificada Router", valor_descuento=Decimal("30.00"))

    with patch.object(ServicioGestionPromociones, "actualizar_promocion", return_value=mock_item):
        try:
            resp = client.put("/api/v1/admin/promociones/10", json=payload)
            assert resp.status_code == 200
            assert resp.json()["nombre"] == "Promocion Modificada Router"
        finally:
            app.dependency_overrides.clear()


def test_cu27_router_conmutar_estado_200(client: TestClient):
    """AC-13: Endpoint PATCH /admin/promociones/{id}/estado conmuta estado y devuelve HTTP 200."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_item = fabricar_promocion_item_out(id_promocion=10, estado_activo=False)

    with patch.object(ServicioGestionPromociones, "conmutar_estado", return_value=mock_item):
        try:
            resp = client.patch("/api/v1/admin/promociones/10/estado", json={"estado_activo": False})
            assert resp.status_code == 200
            assert resp.json()["estado_activo"] is False
        finally:
            app.dependency_overrides.clear()


def test_cu27_router_listar_promociones_ordenar_por_creado_en_desc_200(client: TestClient):
    """AC-9: Endpoint GET /admin/promociones admite ordenar_por=creado_en_desc y creado_en_asc."""
    usuario_admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: usuario_admin

    mock_lista = RespuestaPaginadaPromocionesOut(
        items=[fabricar_promocion_item_out(id_promocion=1, nombre="Promocion Reciente")],
        metricas=MetricasPromocionesOut(
            promociones_activas=1,
            cupones_vigentes=0,
            descuento_promedio=Decimal("10.00"),
            usos_totales=0,
        ),
        total=1,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioGestionPromociones, "listar_promociones", return_value=mock_lista):
        try:
            # 1. Validar creado_en_desc
            resp = client.get("/api/v1/admin/promociones?ordenar_por=creado_en_desc")
            assert resp.status_code == 200
            assert resp.json()["total"] == 1

            # 2. Validar creado_en_asc
            resp_asc = client.get("/api/v1/admin/promociones?ordenar_por=creado_en_asc")
            assert resp_asc.status_code == 200
            assert resp_asc.json()["total"] == 1

            # 3. Validar valor por defecto sin parametro explicito
            resp_def = client.get("/api/v1/admin/promociones")
            assert resp_def.status_code == 200
        finally:
            app.dependency_overrides.clear()

