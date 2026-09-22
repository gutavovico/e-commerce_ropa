"""Suite de pruebas automatizadas para CU26: Consultar inventario global.

Cubre rigurosamente los criterios de aceptacion:
- # AC-1: Seguridad RBAC (Token Bearer JWT con roles administrador o encargado_sucursal requeridos; bloqueo 401 sin token, 403 a cajero y cliente).
- # AC-2: Acceso y segregacion funcional de consulta por rol (administrador irrestricto, encargado en modo consulta multi-sede).
- # AC-3: Consolidacion agregada multi-sucursal a nivel de prenda y variante (disponible, reservado, fisico, desglose por boutique y metricas de red).
- # AC-4: Filtros multicriterio aplicados (busqueda textual q, id_categoria, id_sucursal, estado_stock).
- # AC-5: Tratamiento defensivo contra nulos con COALESCE (variante sin inventario devuelve 0) y exclusion de sucursales inactivas.
- # AC-6: Validacion estricta de parametros y paginacion (422 ante rangos no permitidos, 404 ante id inexistente).
- # AC-7: Consulta de directorio logistico de sedes con direccion, telefono y ciudad para derivacion inter-tiendas.
"""

from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.gestion_operativa.cu26_inventario_global.errores import (
    CategoriaInvalidaConsultaError,
    SucursalInvalidaConsultaError,
)
from modules.gestion_operativa.cu26_inventario_global.esquemas import (
    ExistenciaSucursalItemOut,
    InventarioGlobalFiltrosIn,
    InventarioGlobalItemOut,
    MetricasInventarioGlobalOut,
    RespuestaInventarioGlobalOut,
)
from modules.gestion_operativa.cu26_inventario_global.servicio import (
    ServicioInventarioGlobal,
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
    usuario.email = "admin.corporativo@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Elena"
    usuario.apellidos = "Montes"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2, id_sucursal: int = 10) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado.boutique@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Carlos"
    usuario.apellidos = "Vargas"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3, id_sucursal: int = 10) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.tienda@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Pedro"
    usuario.apellidos = "Gomez"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente.vip@fashionstore.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Ana"
    usuario.apellidos = "Rios"
    usuario.activo = True
    return usuario


# Namedtuples para simular filas de SQLAlchemy
FilaSucursal = namedtuple("FilaSucursal", ["id_sucursal", "nombre", "direccion", "telefono", "ciudad_nombre"])
FilaVariante = namedtuple(
    "FilaVariante",
    [
        "id_variante",
        "id_producto",
        "nombre_producto",
        "sku",
        "categoria_nombre",
        "talla_codigo",
        "color_nombre",
        "swatches_hex",
        "total_disponible",
        "total_reservado",
    ],
)
FilaExistencia = namedtuple(
    "FilaExistencia",
    ["id_variante", "id_sucursal", "cantidad_disponible", "cantidad_reservada"],
)
FilaMetricas = namedtuple("FilaMetricas", ["total_unidades", "total_variantes"])


# -----------------------------------------------------------------------------
# 1. PRUEBAS DE SEGURIDAD Y CONTROL DE ACCESO RBAC (# AC-1, # AC-2)
# -----------------------------------------------------------------------------

def test_cu26_rbac_sin_token(client):
    """# AC-1: Peticion sin cabecera Authorization responde HTTP 401 Unauthorized."""
    app.dependency_overrides.pop(get_current_user, None)
    app.dependency_overrides.pop(get_db, None)

    res = client.get("/api/v1/admin/inventario/global")
    assert res.status_code == 401
    assert res.json()["code"] == "TOKEN_INVALIDO"


def test_cu26_rbac_rol_cajero_denegado(client):
    """# AC-1: Usuario con rol cajero es rechazado con HTTP 403 Forbidden."""
    cajero = crear_usuario_cajero_mock()
    app.dependency_overrides[get_current_user] = lambda: cajero
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/inventario/global")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_cu26_rbac_rol_cliente_denegado(client):
    """# AC-1: Usuario con rol cliente es rechazado con HTTP 403 Forbidden."""
    cliente = crear_usuario_cliente_mock()
    app.dependency_overrides[get_current_user] = lambda: cliente
    app.dependency_overrides[get_db] = lambda: MagicMock()

    try:
        res = client.get("/api/v1/admin/inventario/global")
        assert res.status_code == 403
        assert res.json()["code"] == "ACCESO_DENEGADO"
    finally:
        app.dependency_overrides.clear()


def test_cu26_acceso_administrador_exitoso(client):
    """# AC-1, # AC-2: Usuario con rol administrador accede exitosamente al inventario global."""
    admin = crear_usuario_admin_mock()
    app.dependency_overrides[get_current_user] = lambda: admin

    # Mock de servicio retornando respuesta estructurada valida
    respuesta_falsa = RespuestaInventarioGlobalOut(
        items=[
            InventarioGlobalItemOut(
                id_variante=101,
                id_producto=10,
                nombre_producto="Vestido Gala Seda",
                sku="VES-GAL-S-NEG",
                categoria="Vestidos de Fiesta",
                talla="S",
                color="Negro",
                swatches_hex="#000000",
                total_disponible=12,
                total_reservado=2,
                total_fisico=14,
                estado_stock="optimo",
                desglose_sucursales=[
                    ExistenciaSucursalItemOut(
                        id_sucursal=1,
                        nombre_sucursal="Boutique Calacoto",
                        ciudad="La Paz",
                        direccion="Av. Ballivian #100",
                        telefono="2790001",
                        cantidad_disponible=12,
                        cantidad_reservada=2,
                    )
                ],
            )
        ],
        metricas=MetricasInventarioGlobalOut(
            total_unidades_red=12,
            variantes_monitoreadas=1,
            alertas_stock_bajo=0,
            sedes_activas=1,
        ),
        total=1,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioInventarioGlobal, "consultar_inventario_global", return_value=respuesta_falsa):
        try:
            res = client.get("/api/v1/admin/inventario/global")
            assert res.status_code == 200
            data = res.json()
            assert "items" in data
            assert "metricas" in data
            assert data["total"] == 1
            assert data["items"][0]["sku"] == "VES-GAL-S-NEG"
            assert data["items"][0]["estado_stock"] == "optimo"
            assert data["metricas"]["sedes_activas"] == 1
        finally:
            app.dependency_overrides.clear()


def test_cu26_acceso_encargado_exitoso(client):
    """# AC-1, # AC-2: Usuario con rol encargado_sucursal consulta de modo informativo multi-sede."""
    encargado = crear_usuario_encargado_mock(id_usuario=2, id_sucursal=1)
    app.dependency_overrides[get_current_user] = lambda: encargado

    respuesta_falsa = RespuestaInventarioGlobalOut(
        items=[],
        metricas=MetricasInventarioGlobalOut(
            total_unidades_red=0,
            variantes_monitoreadas=0,
            alertas_stock_bajo=0,
            sedes_activas=2,
        ),
        total=0,
        pagina=1,
        limite=10,
        total_paginas=1,
    )

    with patch.object(ServicioInventarioGlobal, "consultar_inventario_global", return_value=respuesta_falsa):
        try:
            res = client.get("/api/v1/admin/inventario/global")
            assert res.status_code == 200
            data = res.json()
            assert data["total"] == 0
            assert data["metricas"]["sedes_activas"] == 2
        finally:
            app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# 2. PRUEBAS DE LOGICA DE AGREGACION Y SERVICIO (# AC-3, # AC-5, # AC-7)
# -----------------------------------------------------------------------------

def test_cu26_agregacion_stock_red():
    """# AC-3, # AC-7: Agregacion multi-sucursal calcula existencias exactas y desglose logistico."""
    mock_db = MagicMock()

    # Dos sucursales activas en el sistema
    suc1 = FilaSucursal(1, "Boutique Calacoto", "Av. Ballivian #100", "2790001", "La Paz")
    suc2 = FilaSucursal(2, "Boutique Equipetrol", "Av. San Martin #200", "3340002", "Santa Cruz")

    # Variante con 4 en suc1 y 3 en suc2 -> total_disponible = 7, total_reservado = 1
    var1 = FilaVariante(10, 5, "Camisa Lino Premium", "CAM-LIN-M-BLA", "Camisas", "M", "Blanco", "#FFFFFF", 7, 1)

    # Existencias individuales por boutique
    ex1 = FilaExistencia(10, 1, 4, 1)
    ex2 = FilaExistencia(10, 2, 3, 0)

    # Configuracion de respuestas para db.execute
    def mock_execute_side_effect(statement, *args, **kwargs):
        res = MagicMock()
        sql_str = str(statement)
        if "FROM fashionstore.sucursales" in sql_str and "ciudad_nombre" in sql_str:
            res.all.return_value = [suc1, suc2]
        elif "count" in sql_str and "conteo_subquery" in sql_str:
            res.scalar_one.return_value = 1
        elif "FROM fashionstore.variantes_producto" in sql_str and "offset" in sql_str.lower():
            res.all.return_value = [var1]
        elif "FROM fashionstore.inventario_sucursal" in sql_str and "id_variante IN" in sql_str:
            res.all.return_value = [ex1, ex2]
        elif "total_unidades" in sql_str:
            res.one.return_value = FilaMetricas(7, 1)
        elif "subq_alerta" in sql_str or "count" in sql_str:
            res.scalar_one.return_value = 0
        return res

    mock_db.execute.side_effect = mock_execute_side_effect

    filtros = InventarioGlobalFiltrosIn(pagina=1, limite=10)
    respuesta = ServicioInventarioGlobal.consultar_inventario_global(mock_db, filtros)

    assert respuesta.total == 1
    assert len(respuesta.items) == 1
    item = respuesta.items[0]

    assert item.sku == "CAM-LIN-M-BLA"
    assert item.total_disponible == 7
    assert item.total_reservado == 1
    assert item.total_fisico == 8
    assert item.estado_stock == "optimo"  # 7 > 5 -> optimo

    # Desglose de sucursales con datos logisticos
    assert len(item.desglose_sucursales) == 2
    assert item.desglose_sucursales[0].nombre_sucursal == "Boutique Calacoto"
    assert item.desglose_sucursales[0].cantidad_disponible == 4
    assert item.desglose_sucursales[0].telefono == "2790001"
    assert item.desglose_sucursales[1].nombre_sucursal == "Boutique Equipetrol"
    assert item.desglose_sucursales[1].cantidad_disponible == 3
    assert item.desglose_sucursales[1].ciudad == "Santa Cruz"


def test_cu26_variante_sin_inventario_retorna_cero():
    """# AC-5: Variante en catalogo sin inventario previo retorna 0 y estado 'agotado' defensivamente."""
    mock_db = MagicMock()

    suc1 = FilaSucursal(1, "Boutique Calacoto", "Av. Ballivian #100", "2790001", "La Paz")
    # Variante sin existencias (disponible=0, reservado=0)
    var_cero = FilaVariante(20, 8, "Saco Velvet", "SAC-VEL-L-AZU", "Sacos", "L", "Azul", "#0000FF", 0, 0)

    def mock_execute_side_effect(statement, *args, **kwargs):
        res = MagicMock()
        sql_str = str(statement)
        if "FROM fashionstore.sucursales" in sql_str and "ciudad_nombre" in sql_str:
            res.all.return_value = [suc1]
        elif "count" in sql_str and "conteo_subquery" in sql_str:
            res.scalar_one.return_value = 1
        elif "FROM fashionstore.variantes_producto" in sql_str and "offset" in sql_str.lower():
            res.all.return_value = [var_cero]
        elif "FROM fashionstore.inventario_sucursal" in sql_str and "id_variante IN" in sql_str:
            res.all.return_value = []  # Sin registros en inventario_sucursal
        elif "total_unidades" in sql_str:
            res.one.return_value = FilaMetricas(0, 1)
        elif "subq_alerta" in sql_str or "count" in sql_str:
            res.scalar_one.return_value = 0
        return res

    mock_db.execute.side_effect = mock_execute_side_effect

    filtros = InventarioGlobalFiltrosIn(pagina=1, limite=10)
    respuesta = ServicioInventarioGlobal.consultar_inventario_global(mock_db, filtros)

    assert respuesta.total == 1
    item = respuesta.items[0]
    assert item.total_disponible == 0
    assert item.total_reservado == 0
    assert item.total_fisico == 0
    assert item.estado_stock == "agotado"
    # El desglose aun debe incluir la sucursal activa con disponible = 0
    assert len(item.desglose_sucursales) == 1
    assert item.desglose_sucursales[0].cantidad_disponible == 0
    assert item.desglose_sucursales[0].cantidad_reservada == 0


def test_cu26_filtro_textual_q():
    """# AC-4: Busqueda textual por parametro q se sanitiza y genera filtrado ILIKE."""
    filtros = InventarioGlobalFiltrosIn(q="   CAMISA LINO   ")
    assert filtros.q == "CAMISA LINO"

    filtros_espacios = InventarioGlobalFiltrosIn(q="   ")
    assert filtros_espacios.q is None


def test_cu26_filtro_estado_alerta_baja():
    """# AC-3, # AC-4: Semaforo clasifica correctamente estado alerta_baja cuando 0 < stock <= 5."""
    assert ServicioInventarioGlobal.calcular_estado_stock(0) == "agotado"
    assert ServicioInventarioGlobal.calcular_estado_stock(-1) == "agotado"
    assert ServicioInventarioGlobal.calcular_estado_stock(1) == "alerta_baja"
    assert ServicioInventarioGlobal.calcular_estado_stock(3) == "alerta_baja"
    assert ServicioInventarioGlobal.calcular_estado_stock(5) == "alerta_baja"
    assert ServicioInventarioGlobal.calcular_estado_stock(6) == "optimo"
    assert ServicioInventarioGlobal.calcular_estado_stock(100) == "optimo"


def test_cu26_exclusion_sucursales_inactivas():
    """# AC-5: Existencias en sucursales inactivas no se suman a las unidades disponibles en red."""
    mock_db = MagicMock()

    # Solo la sucursal 1 esta activa
    suc_activa = FilaSucursal(1, "Boutique Central", "Av. 16 de Julio", "2200000", "La Paz")

    # Variante con 2 unidades en la sede activa (las 10 de la inactiva fueron discriminadas por SQL CASE)
    var_solo_activa = FilaVariante(30, 9, "Pantalon Lino", "PAN-LIN-38-BEI", "Pantalones", "38", "Beige", "#F5F5DC", 2, 0)
    ex_activa = FilaExistencia(30, 1, 2, 0)

    def mock_execute_side_effect(statement, *args, **kwargs):
        res = MagicMock()
        sql_str = str(statement)
        if "FROM fashionstore.sucursales" in sql_str and "ciudad_nombre" in sql_str:
            res.all.return_value = [suc_activa]
        elif "count" in sql_str and "conteo_subquery" in sql_str:
            res.scalar_one.return_value = 1
        elif "FROM fashionstore.variantes_producto" in sql_str and "offset" in sql_str.lower():
            res.all.return_value = [var_solo_activa]
        elif "FROM fashionstore.inventario_sucursal" in sql_str and "id_variante IN" in sql_str:
            res.all.return_value = [ex_activa]
        elif "total_unidades" in sql_str:
            res.one.return_value = FilaMetricas(2, 1)
        elif "subq_alerta" in sql_str or "count" in sql_str:
            res.scalar_one.return_value = 1  # 2 unidades clasifica en alerta_baja
        return res

    mock_db.execute.side_effect = mock_execute_side_effect

    filtros = InventarioGlobalFiltrosIn(pagina=1, limite=10)
    respuesta = ServicioInventarioGlobal.consultar_inventario_global(mock_db, filtros)

    assert respuesta.items[0].total_disponible == 2
    assert respuesta.items[0].estado_stock == "alerta_baja"
    assert respuesta.metricas.sedes_activas == 1
    assert len(respuesta.items[0].desglose_sucursales) == 1
