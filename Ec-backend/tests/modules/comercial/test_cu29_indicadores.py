"""Suite de pruebas automatizadas para CU29: Visualizar indicadores empresariales.
Nomenclatura oficial: Visualizar indicadores empresariales

Cubre los criterios de aceptacion esenciales:
- # AC-1: Autenticacion obligatoria con JWT (HTTP 401).
- # AC-2: Control de acceso RBAC (HTTP 403 para cajero y cliente).
- # AC-3: Segregacion territorial obligatoria para encargado de sucursal.
- # AC-4: Restriccion estricta de comparativa de sucursales a administradores (HTTP 403 para encargados).
- # AC-5 y # AC-6: Validacion defensiva de filtros temporales y rangos cronologicos (HTTP 422).
- # AC-7 a # AC-12: Calculo de resumen ejecutivo, serie temporal, ranking top productos, distribucion y comparativa.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.comercial.cu29_indicadores.errores import (
    AccesoComparativaDenegadoError,
    IndicadoresError,
    RangoTemporalInvalidoError,
    SucursalNoAutorizadaError,
)
from modules.comercial.cu29_indicadores.esquemas import (
    CanalDistribucionOut,
    CategoriaDistribucionOut,
    ComparativaSucursalesOut,
    DashboardIndicadoresCompletoOut,
    DistribucionVentasOut,
    IndicadoresFiltrosIn,
    ItemRankingProductoOut,
    PuntoSerieTemporalOut,
    RankingProductosOut,
    ResumenEjecutivoOut,
    SerieTemporalIngresosOut,
    SucursalDesempenoOut,
)
from modules.comercial.cu29_indicadores.servicio import (
    ServicioIndicadoresEmpresariales,
)


# -----------------------------------------------------------------------------
# FIXTURES Y GENERADORES DE MOCKS
# -----------------------------------------------------------------------------


@pytest.fixture
def client():
    """Cliente HTTP de pruebas para endpoints FastAPI."""
    return TestClient(app)


def crear_usuario_admin_mock(id_usuario: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "director.ejecutivo@fashionstore.com"
    usuario.rol = "administrador"
    usuario.id_sucursal = None
    usuario.nombres = "Director"
    usuario.apellidos = "Ejecutivo"
    usuario.activo = True
    return usuario


def crear_usuario_encargado_mock(id_usuario: int = 2, id_sucursal: int = 1) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "encargado.central@fashionstore.com"
    usuario.rol = "encargado_sucursal"
    usuario.id_sucursal = id_sucursal
    usuario.nombres = "Encargado"
    usuario.apellidos = "Central"
    usuario.activo = True
    return usuario


def crear_usuario_cajero_mock(id_usuario: int = 3) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cajero.tienda@fashionstore.com"
    usuario.rol = "cajero"
    usuario.id_sucursal = 1
    usuario.nombres = "Cajero"
    usuario.apellidos = "PuntoDeVenta"
    usuario.activo = True
    return usuario


def crear_usuario_cliente_mock(id_usuario: int = 4) -> UsuarioORM:
    usuario = MagicMock(spec=UsuarioORM)
    usuario.id_usuario = id_usuario
    usuario.email = "cliente.fashion@gmail.com"
    usuario.rol = "cliente"
    usuario.id_sucursal = None
    usuario.nombres = "Cliente"
    usuario.apellidos = "Frecuente"
    usuario.activo = True
    return usuario


def fabricar_resumen_mock() -> ResumenEjecutivoOut:
    return ResumenEjecutivoOut(
        periodo_inicio=date(2026, 9, 1),
        periodo_fin=date(2026, 9, 30),
        ingresos_totales=Decimal("45000.00"),
        variacion_porcentual=Decimal("12.50"),
        total_transacciones=150,
        variacion_porcentual_transacciones=Decimal("8.00"),
        margen_estimado=Decimal("42.50"),
        ticket_promedio=Decimal("300.00"),
        variacion_porcentual_ticket=Decimal("4.17"),
        unidades_vendidas=320,
        variacion_porcentual_unidades=Decimal("10.20"),
    )


def fabricar_serie_temporal_mock() -> SerieTemporalIngresosOut:
    return SerieTemporalIngresosOut(
        agrupacion="diaria",
        puntos=[
            PuntoSerieTemporalOut(
                etiqueta_tiempo="2026-09-01",
                fecha_inicio=date(2026, 9, 1),
                monto_ingresos=Decimal("1500.00"),
                cantidad_ordenes=5,
            ),
            PuntoSerieTemporalOut(
                etiqueta_tiempo="2026-09-02",
                fecha_inicio=date(2026, 9, 2),
                monto_ingresos=Decimal("2200.00"),
                cantidad_ordenes=8,
            ),
        ],
    )


def fabricar_top_productos_mock() -> RankingProductosOut:
    return RankingProductosOut(
        limite=5,
        productos=[
            ItemRankingProductoOut(
                id_producto=10,
                nombre_producto="Vestido Seda Silk Noir",
                sku_referencia="VSN-S-BLK",
                categoria_nombre="Vestidos de Gala",
                unidades_vendidas=25,
                monto_total_generado=Decimal("31250.00"),
                porcentaje_contribucion=Decimal("69.44"),
            )
        ],
    )


def fabricar_distribucion_mock() -> DistribucionVentasOut:
    return DistribucionVentasOut(
        por_categoria=[
            CategoriaDistribucionOut(
                id_categoria=1,
                nombre_categoria="Vestidos de Gala",
                monto_facturado=Decimal("31250.00"),
                unidades_vendidas=25,
                porcentaje_participacion=Decimal("69.44"),
            )
        ],
        por_canal=[
            CanalDistribucionOut(
                canal_codigo="boutique_fisica",
                canal_nombre="Boutique Fisica",
                monto_facturado=Decimal("25000.00"),
                total_ordenes=80,
                porcentaje_participacion=Decimal("55.56"),
            ),
            CanalDistribucionOut(
                canal_codigo="tienda_web",
                canal_nombre="Tienda Web",
                monto_facturado=Decimal("20000.00"),
                total_ordenes=70,
                porcentaje_participacion=Decimal("44.44"),
            ),
        ],
    )


def fabricar_comparativa_mock() -> ComparativaSucursalesOut:
    return ComparativaSucursalesOut(
        sucursales=[
            SucursalDesempenoOut(
                id_sucursal=1,
                nombre_sucursal="Boutique Central",
                ciudad="La Paz",
                monto_facturado=Decimal("25000.00"),
                total_ventas=80,
                ticket_promedio=Decimal("312.50"),
                porcentaje_red=Decimal("55.56"),
            )
        ]
    )


# -----------------------------------------------------------------------------
# PRUEBAS DE SEGURIDAD, RBAC Y AUTENTICACION (# AC-1, # AC-2, # AC-4)
# -----------------------------------------------------------------------------


def test_cu29_sin_token_rechaza_401(client):
    """Peticiones no autenticadas son rechazadas con HTTP 401."""
    resp = client.get("/api/v1/admin/indicadores/resumen")
    assert resp.status_code == 401


def test_cu29_rol_cajero_rechaza_403(client):
    """Rol cajero no posee permisos para consultar indicadores analiticos (HTTP 403)."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cajero_mock()
    try:
        resp = client.get("/api/v1/admin/indicadores/resumen")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cu29_rol_cliente_rechaza_403(client):
    """Rol cliente no posee permisos para consultar indicadores analiticos (HTTP 403)."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_cliente_mock()
    try:
        resp = client.get("/api/v1/admin/indicadores/resumen")
        assert resp.status_code == 403
    finally:
        app.dependency_overrides.clear()


def test_cu29_encargado_bloqueado_en_comparativa_sucursales_403(client):
    """Encargado de sucursal es bloqueado de consultar comparativas entre sedes (HTTP 403)."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_encargado_mock(id_sucursal=1)
    try:
        resp = client.get("/api/v1/admin/indicadores/comparativa-sucursales")
        assert resp.status_code == 403
        data = resp.json()
        assert data.get("code") == "ACCESO_COMPARATIVA_DENEGADO"
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# PRUEBAS DE VALIDACION DE ESQUEMAS Y PARAMETROS (# AC-5, # AC-6)
# -----------------------------------------------------------------------------


def test_cu29_esquema_fechas_inversas_rechaza_validation_error():
    """Filtros con fecha_desde > fecha_hasta en periodo personalizado lanzan error."""
    with pytest.raises(ValidationError):
        IndicadoresFiltrosIn(
            periodo="personalizado",
            fecha_desde=date(2026, 9, 30),
            fecha_hasta=date(2026, 9, 1),
        )


def test_cu29_esquema_periodo_personalizado_sin_fechas_rechaza_error():
    """Periodo personalizado sin fechas lanza error de validacion."""
    with pytest.raises(ValidationError):
        IndicadoresFiltrosIn(
            periodo="personalizado",
            fecha_desde=None,
            fecha_hasta=None,
        )


def test_cu29_router_fechas_invertidas_retorna_422(client):
    """Endpoint con fechas invertidas en periodo personalizado retorna HTTP 422."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    try:
        resp = client.get(
            "/api/v1/admin/indicadores/resumen",
            params={
                "periodo": "personalizado",
                "fecha_desde": "2026-09-30",
                "fecha_hasta": "2026-09-01",
            },
        )
        assert resp.status_code == 422
    finally:
        app.dependency_overrides.clear()


# -----------------------------------------------------------------------------
# PRUEBAS DEL SERVICIO ANALITICO (# AC-3, # AC-7 a # AC-12)
# -----------------------------------------------------------------------------


def test_cu29_servicio_segregacion_encargado_fuerza_sucursal():
    """Servicio fuerza la sucursal del usuario encargado independientemente de parametros."""
    servicio = ServicioIndicadoresEmpresariales()
    encargado = crear_usuario_encargado_mock(id_usuario=2, id_sucursal=3)

    alcance = servicio.resolver_alcance_sucursal(encargado, id_sucursal_solicitado=99)
    assert alcance == 3


def test_cu29_servicio_segregacion_admin_permite_global_o_especifica():
    """Servicio permite a administradores consultar globalmente o por sede especifica."""
    servicio = ServicioIndicadoresEmpresariales()
    admin = crear_usuario_admin_mock()

    alcance_global = servicio.resolver_alcance_sucursal(admin, id_sucursal_solicitado=None)
    assert alcance_global is None

    alcance_especifico = servicio.resolver_alcance_sucursal(admin, id_sucursal_solicitado=2)
    assert alcance_especifico == 2


def test_cu29_servicio_calculo_defensivo_variaciones():
    """Calculo defensivo de variaciones porcentuales sin division por cero."""
    servicio = ServicioIndicadoresEmpresariales()

    # Crecimiento regular
    var1 = servicio._calcular_variacion(Decimal("120.00"), Decimal("100.00"))
    assert var1 == Decimal("20.00")

    # Caida regular
    var2 = servicio._calcular_variacion(Decimal("80.00"), Decimal("100.00"))
    assert var2 == Decimal("-20.00")

    # Anterior en cero con actual positivo
    var3 = servicio._calcular_variacion(Decimal("50.00"), Decimal("0.00"))
    assert var3 == Decimal("100.00")

    # Ambos en cero
    var4 = servicio._calcular_variacion(Decimal("0.00"), Decimal("0.00"))
    assert var4 == Decimal("0.00")


def test_cu29_servicio_resolucion_intervalos():
    """Resolucion correcta de intervalos temporales predeterminados y personalizados."""
    servicio = ServicioIndicadoresEmpresariales()

    # 7 dias
    f_7d = IndicadoresFiltrosIn(periodo="7d")
    ini, fin, ini_ant, fin_ant, agrup = servicio.resolver_intervalos_tiempo(f_7d)
    assert agrup == "diaria"
    assert (fin - ini).days == 7
    assert (fin_ant - ini_ant).days == 7

    # Personalizado corto
    f_custom = IndicadoresFiltrosIn(
        periodo="personalizado",
        fecha_desde=date(2026, 9, 1),
        fecha_hasta=date(2026, 9, 10),
    )
    ini_c, fin_c, _, _, agrup_c = servicio.resolver_intervalos_tiempo(f_custom)
    assert agrup_c == "diaria"
    assert ini_c.date() == date(2026, 9, 1)
    assert fin_c.date() == date(2026, 9, 10)


# -----------------------------------------------------------------------------
# PRUEBAS DE ENDPOINTS REST (# AC-7 a # AC-13)
# -----------------------------------------------------------------------------


def test_cu29_router_obtener_dashboard_consolidado_admin_200(client):
    """Admin obtiene el dashboard consolidado completo incluyendo comparativa."""
    mock_dashboard = DashboardIndicadoresCompletoOut(
        resumen=fabricar_resumen_mock(),
        serie_temporal=fabricar_serie_temporal_mock(),
        top_productos=fabricar_top_productos_mock(),
        distribucion=fabricar_distribucion_mock(),
        comparativa_sucursales=fabricar_comparativa_mock(),
    )

    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_dashboard_consolidado",
        return_value=mock_dashboard,
    ):
        resp = client.get("/api/v1/admin/indicadores/dashboard?periodo=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert "resumen" in data
        assert "serie_temporal" in data
        assert "top_productos" in data
        assert "distribucion" in data
        assert "comparativa_sucursales" in data
        assert float(data["resumen"]["ingresos_totales"]) == 45000.0


def test_cu29_router_obtener_resumen_ejecutivo_200(client):
    """Endpoint de resumen retorna datos financieros y operacionales."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_resumen_ejecutivo",
        return_value=fabricar_resumen_mock(),
    ):
        resp = client.get("/api/v1/admin/indicadores/resumen?periodo=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert float(data["ingresos_totales"]) == 45000.0
        assert data["total_transacciones"] == 150
        assert float(data["ticket_promedio"]) == 300.0


def test_cu29_router_obtener_serie_temporal_200(client):
    """Endpoint de serie temporal retorna puntos ordenados."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_serie_temporal",
        return_value=fabricar_serie_temporal_mock(),
    ):
        resp = client.get("/api/v1/admin/indicadores/serie-temporal?periodo=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert data["agrupacion"] == "diaria"
        assert len(data["puntos"]) == 2


def test_cu29_router_obtener_top_productos_200(client):
    """Endpoint de top productos retorna lista de prendas con contribucion."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_top_productos",
        return_value=fabricar_top_productos_mock(),
    ):
        resp = client.get("/api/v1/admin/indicadores/top-productos?periodo=30d&limite=5")
        assert resp.status_code == 200
        data = resp.json()
        assert data["limite"] == 5
        assert len(data["productos"]) == 1
        assert data["productos"][0]["nombre_producto"] == "Vestido Seda Silk Noir"


def test_cu29_router_obtener_distribucion_ventas_200(client):
    """Endpoint de distribucion retorna desgloses por categoria y por canal."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_distribucion_ventas",
        return_value=fabricar_distribucion_mock(),
    ):
        resp = client.get("/api/v1/admin/indicadores/distribucion?periodo=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert "por_categoria" in data
        assert "por_canal" in data
        assert len(data["por_canal"]) == 2


def test_cu29_router_obtener_comparativa_sucursales_admin_200(client):
    """Admin consulta exitosamente la comparativa de sucursales."""
    app.dependency_overrides[get_current_user] = lambda: crear_usuario_admin_mock()
    app.dependency_overrides[get_db] = lambda: MagicMock()

    with patch.object(
        ServicioIndicadoresEmpresariales,
        "obtener_comparativa_sucursales",
        return_value=fabricar_comparativa_mock(),
    ):
        resp = client.get("/api/v1/admin/indicadores/comparativa-sucursales?periodo=30d")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sucursales"]) == 1
        assert data["sucursales"][0]["nombre_sucursal"] == "Boutique Central"
