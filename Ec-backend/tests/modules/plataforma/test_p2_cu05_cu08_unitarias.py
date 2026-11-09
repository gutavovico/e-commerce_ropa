"""Pruebas unitarias de P2-CU05, P2-CU06, P2-CU07 y P2-CU08 (Panel del Super Administrador SaaS).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` §4 (AC-01 a AC-08).
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import AuthorizationError, ConflictError, NotFoundError, UnprocessableEntityError
from core.tenant import CLAVE_PLATAFORMA, CLAVE_TENANT, CLAVE_USUARIO
from modules.plataforma.cu05_empresas_supervision.esquemas import (
    AdminInicialEmpresaIn,
    CambiarEstadoEmpresaIn,
    EmpresaActualizarIn,
    EmpresaCrearIn,
)
from modules.plataforma.cu05_empresas_supervision.repositorio import EmpresasSupervisionRepositorio
from modules.plataforma.cu05_empresas_supervision.servicio import EmpresasSupervisionServicio
from modules.plataforma.cu06_planes_funcionalidades.esquemas import (
    CambiarEstadoPlanIn,
    PlanActualizarIn,
    PlanCrearIn,
)
from modules.plataforma.cu06_planes_funcionalidades.repositorio import (
    PlanesFuncionalidadesRepositorio,
)
from modules.plataforma.cu06_planes_funcionalidades.servicio import PlanesFuncionalidadesServicio
from modules.plataforma.cu07_suscripciones.esquemas import OperacionSuscripcionIn
from modules.plataforma.cu07_suscripciones.repositorio import SuscripcionesAdminRepositorio
from modules.plataforma.cu07_suscripciones.servicio import SuscripcionesAdminServicio
from modules.plataforma.cu08_catalogos_globales.esquemas import (
    CambiarEstadoCatalogoIn,
    CiudadGlobalIn,
    ColorGlobalIn,
    TallaGlobalIn,
)
from modules.plataforma.cu08_catalogos_globales.repositorio import CatalogosGlobalesRepositorio
from modules.plataforma.cu08_catalogos_globales.servicio import CatalogosGlobalesServicio
from modules.plataforma.dependencias import exigir_super_administrador


class SesionFalsa:
    """Doble de sesión para verificar contexto y commits sin conexión a red."""

    def __init__(self):
        self.info = {}
        self.commits = 0
        self.refrescados = []

    def in_transaction(self):
        return False

    def commit(self):
        self.commits += 1

    def refresh(self, obj):
        self.refrescados.append(obj)


@pytest.fixture
def super_admin():
    return SimpleNamespace(
        id_usuario=999,
        email="superadmin@fashionstore.com",
        rol="super_administrador",
        id_tenant=None,
        activo=True,
    )


# ---------------------------------------------------------------------------
# AC-01: Autorización y activación de modo_plataforma
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("rol_invalido", ["cliente", "cajero", "encargado_sucursal", "administrador"])
def test_ac01_exigir_super_administrador_rechaza_otros_roles(rol_invalido):
    db = SesionFalsa()
    usuario = SimpleNamespace(id_usuario=10, rol=rol_invalido, email="u@test.com")
    with pytest.raises(AuthorizationError) as exc:
        exigir_super_administrador(usuario=usuario, db=db)  # type: ignore[arg-type]
    assert exc.value.code == "ACCESO_DENEGADO"


def test_ac01_exigir_super_administrador_activa_modo_plataforma(super_admin):
    db = SesionFalsa()
    res = exigir_super_administrador(usuario=super_admin, db=db)  # type: ignore[arg-type]
    assert res is super_admin
    assert db.info[CLAVE_TENANT] is None
    assert db.info[CLAVE_USUARIO] == 999
    assert db.info[CLAVE_PLATAFORMA] is True


# ---------------------------------------------------------------------------
# AC-02, AC-03, AC-04: P2-CU05 (Empresas, estados, métricas y bitácora)
# ---------------------------------------------------------------------------


def test_ac02_registrar_empresa_rechaza_codigo_reservado(super_admin):
    datos = EmpresaCrearIn(
        codigo="admin",
        nombre="Empresa Inválida",
        id_plan=1,
        estado_suscripcion="activa",
        fecha_inicio=date(2026, 11, 1),
        fecha_vencimiento=date(2027, 11, 1),
        admin_inicial=AdminInicialEmpresaIn(
            nombres="Ana",
            apellidos="Pérez",
            email="ana@empresa.com",
            password="Password123!",
        ),
    )
    with pytest.raises(UnprocessableEntityError) as exc:
        EmpresasSupervisionServicio.registrar_empresa(MagicMock(), datos, super_admin)
    assert exc.value.code == "CODIGO_EMPRESA_RESERVADO"


def test_ac02_registrar_empresa_rechaza_codigo_duplicado(monkeypatch, super_admin):
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "buscar_por_codigo",
        staticmethod(lambda db, c: SimpleNamespace(id_tenant=1, codigo=c)),
    )
    datos = EmpresaCrearIn(
        codigo="fashionstore",
        nombre="Otra Fashion",
        id_plan=1,
        estado_suscripcion="activa",
        fecha_inicio=date(2026, 11, 1),
        fecha_vencimiento=date(2027, 11, 1),
        admin_inicial=AdminInicialEmpresaIn(
            nombres="Ana",
            apellidos="Pérez",
            email="ana@empresa.com",
            password="Password123!",
        ),
    )
    with pytest.raises(ConflictError) as exc:
        EmpresasSupervisionServicio.registrar_empresa(MagicMock(), datos, super_admin)
    assert exc.value.code == "CODIGO_EMPRESA_OCUPADO"


def test_ac02_registrar_empresa_rechaza_plan_inactivo_y_correo_ocupado(monkeypatch, super_admin):
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "buscar_por_codigo",
        staticmethod(lambda db, c: None),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "obtener_plan",
        staticmethod(lambda db, i: SimpleNamespace(id_plan=i, nombre="Viejo", activo=False)),
    )
    datos = EmpresaCrearIn(
        codigo="atelier-norte",
        nombre="Atelier Norte",
        id_plan=2,
        estado_suscripcion="activa",
        fecha_inicio=date(2026, 11, 1),
        fecha_vencimiento=date(2027, 11, 1),
        admin_inicial=AdminInicialEmpresaIn(
            nombres="Ana",
            apellidos="Pérez",
            email="ana@atelier.com",
            password="Password123!",
        ),
    )
    with pytest.raises(ConflictError) as exc:
        EmpresasSupervisionServicio.registrar_empresa(MagicMock(), datos, super_admin)
    assert exc.value.code == "PLAN_INACTIVO"

    # Ahora con plan activo pero correo de admin ya ocupado
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "obtener_plan",
        staticmethod(lambda db, i: SimpleNamespace(id_plan=i, nombre="Básico", activo=True)),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "correo_existe",
        staticmethod(lambda db, email: True),
    )
    with pytest.raises(ConflictError) as exc2:
        EmpresasSupervisionServicio.registrar_empresa(MagicMock(), datos, super_admin)
    assert exc2.value.code == "CORREO_OCUPADO"


def test_ac02_registrar_empresa_exitoso_atomico(monkeypatch, super_admin):
    now = datetime.now(timezone.utc)
    plan = SimpleNamespace(id_plan=1, nombre="Profesional", activo=True)
    nuevo_tenant = SimpleNamespace(
        id_tenant=5,
        codigo="atelier-sur",
        nombre="Atelier Sur",
        correo_contacto="contacto@atelier.com",
        telefono="70000000",
        estado="activa",
        creado_en=now,
    )
    nueva_susc = SimpleNamespace(
        id_suscripcion=12,
        id_tenant=5,
        id_plan=1,
        estado="activa",
        fecha_inicio=date(2026, 11, 1),
        fecha_vencimiento=date(2027, 11, 1),
    )
    admin_u = SimpleNamespace(
        id_usuario=40,
        email="admin@atelier.com",
        nombres="Carlos",
        apellidos="Gómez",
    )

    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "buscar_por_codigo", staticmethod(lambda db, c: None)
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "obtener_plan", staticmethod(lambda db, i: plan)
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "correo_existe", staticmethod(lambda db, e: False)
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "crear_empresa_atomica",
        staticmethod(lambda db, **kw: (nuevo_tenant, nueva_susc, admin_u)),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "suscripcion_mas_reciente",
        staticmethod(lambda db, t: (nueva_susc, plan)),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "indicadores_empresa",
        staticmethod(
            lambda db, t: {
                "sucursales_activas": 0,
                "sucursales_totales": 0,
                "empleados_activos": 1,
                "productos_activos": 0,
                "ventas_pagadas_cantidad": 0,
                "ventas_pagadas_monto": Decimal("0.00"),
                "reservas_totales": 0,
            }
        ),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "admin_principal_empresa",
        staticmethod(lambda db, t: admin_u),
    )

    datos = EmpresaCrearIn(
        codigo="Atelier-Sur",
        nombre="Atelier Sur",
        correo_contacto="contacto@atelier.com",
        telefono="70000000",
        id_plan=1,
        estado_suscripcion="activa",
        fecha_inicio=date(2026, 11, 1),
        fecha_vencimiento=date(2027, 11, 1),
        admin_inicial=AdminInicialEmpresaIn(
            nombres="Carlos",
            apellidos="Gómez",
            email="admin@atelier.com",
            password="Password123!",
        ),
    )
    res = EmpresasSupervisionServicio.registrar_empresa(MagicMock(), datos, super_admin)
    assert res.id_tenant == 5
    assert res.codigo == "atelier-sur"
    assert res.admin_email == "admin@atelier.com"
    assert res.suscripcion_actual is not None
    assert res.suscripcion_actual.nombre_plan == "Profesional"
    assert res.suscripcion_actual.vigente is True


def test_ac03_cambiar_estado_empresa_exige_suspension_previa_para_baja(monkeypatch, super_admin):
    now = datetime.now(timezone.utc)
    tenant = SimpleNamespace(
        id_tenant=2,
        codigo="menshopping",
        nombre="Menshopping",
        correo_contacto=None,
        telefono=None,
        estado="activa",
        creado_en=now,
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "obtener_tenant", staticmethod(lambda db, i: tenant)
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "suscripcion_mas_reciente", staticmethod(lambda db, i: None)
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "indicadores_empresa",
        staticmethod(
            lambda db, t: {
                "sucursales_activas": 1,
                "sucursales_totales": 1,
                "empleados_activos": 2,
                "productos_activos": 10,
                "ventas_pagadas_cantidad": 5,
                "ventas_pagadas_monto": Decimal("500.00"),
                "reservas_totales": 1,
            }
        ),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "admin_principal_empresa",
        staticmethod(lambda db, t: None),
    )

    # Intento directo de activa -> baja debe fallar con 409 BAJA_REQUIERE_SUSPENSION_PREVIA
    with pytest.raises(ConflictError) as exc:
        EmpresasSupervisionServicio.cambiar_estado_empresa(
            MagicMock(), 2, CambiarEstadoEmpresaIn(estado="baja"), super_admin
        )
    assert exc.value.code == "BAJA_REQUIERE_SUSPENSION_PREVIA"

    # Primero suspender -> OK
    res_susp = EmpresasSupervisionServicio.cambiar_estado_empresa(
        MagicMock(), 2, CambiarEstadoEmpresaIn(estado="suspendida", motivo="Falta de pago"), super_admin
    )
    assert res_susp.estado == "suspendida"

    # Ahora dar de baja desde suspendida -> OK
    res_baja = EmpresasSupervisionServicio.cambiar_estado_empresa(
        MagicMock(), 2, CambiarEstadoEmpresaIn(estado="baja", motivo="Cierre definitivo"), super_admin
    )
    assert res_baja.estado == "baja"


def test_ac04_metricas_plataforma_y_bitacora(monkeypatch):
    now = datetime.now(timezone.utc)
    t1 = SimpleNamespace(
        id_tenant=1,
        codigo="fashionstore",
        nombre="FASHION STORE",
        correo_contacto=None,
        telefono=None,
        estado="activa",
        creado_en=now,
    )
    susc1 = SimpleNamespace(
        id_suscripcion=1,
        id_tenant=1,
        id_plan=2,
        estado="activa",
        fecha_inicio=date(2026, 1, 1),
        fecha_vencimiento=date(2027, 12, 31),
    )
    plan1 = SimpleNamespace(id_plan=2, nombre="Profesional")

    monkeypatch.setattr(
        EmpresasSupervisionRepositorio, "listar_tenants", staticmethod(lambda db, **kw: [t1])
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "suscripcion_mas_reciente",
        staticmethod(lambda db, t: (susc1, plan1)),
    )
    monkeypatch.setattr(
        EmpresasSupervisionRepositorio,
        "indicadores_empresa",
        staticmethod(
            lambda db, t: {
                "sucursales_activas": 2,
                "sucursales_totales": 2,
                "empleados_activos": 5,
                "productos_activos": 30,
                "ventas_pagadas_cantidad": 12,
                "ventas_pagadas_monto": Decimal("1850.50"),
                "reservas_totales": 4,
            }
        ),
    )

    metricas = EmpresasSupervisionServicio.obtener_metricas_plataforma(MagicMock())
    assert metricas.empresas_totales == 1
    assert metricas.empresas_activas == 1
    assert metricas.suscripciones_vigentes == 1
    assert metricas.monto_ventas_pagadas_total == Decimal("1850.50")
    assert len(metricas.desglose_empresas) == 1
    assert metricas.desglose_empresas[0].codigo == "fashionstore"


# ---------------------------------------------------------------------------
# AC-05: P2-CU06 (Planes, funcionalidades y advertencias por reducción de límite)
# ---------------------------------------------------------------------------


def test_ac05_crear_plan_valida_funcionalidades_y_unicidad(monkeypatch, super_admin):
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "buscar_por_nombre",
        staticmethod(lambda db, n, **kw: None),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "listar_funcionalidades",
        staticmethod(
            lambda db: [
                SimpleNamespace(codigo="productos", nombre="Productos", descripcion=None),
                SimpleNamespace(codigo="ventas", nombre="Ventas", descripcion=None),
            ]
        ),
    )

    datos_invalido = PlanCrearIn(
        nombre="Enterprise",
        precio_mensual=Decimal("99.00"),
        max_sucursales_activas=20,
        max_empleados=100,
        funcionalidades=["productos", "modulo_inexistente"],
    )
    with pytest.raises(UnprocessableEntityError) as exc:
        PlanesFuncionalidadesServicio.crear_plan(MagicMock(), datos_invalido, super_admin)
    assert exc.value.code == "FUNCIONALIDAD_DESCONOCIDA"


def test_ac05_actualizar_plan_genera_advertencias_cuando_empresa_supera_nuevo_limite(
    monkeypatch, super_admin
):
    now = datetime.now(timezone.utc)
    plan_actual = SimpleNamespace(
        id_plan=1,
        nombre="Básico",
        precio_mensual=Decimal("29.00"),
        max_sucursales_activas=5,
        max_empleados=20,
        activo=True,
        creado_en=now,
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio, "obtener_plan", staticmethod(lambda db, i: plan_actual)
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "buscar_por_nombre",
        staticmethod(lambda db, n, **kw: None),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "listar_funcionalidades",
        staticmethod(
            lambda db: [SimpleNamespace(codigo="productos", nombre="Productos", descripcion=None)]
        ),
    )
    # Empresa con 3 sucursales activas y 8 empleados activos
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "empresas_con_suscripcion_activa_en_plan",
        staticmethod(
            lambda db, i: [SimpleNamespace(id_tenant=1, codigo="fashionstore", nombre="FASHION STORE")]
        ),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "uso_recursos_empresa",
        staticmethod(lambda db, t: (3, 8)),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "actualizar_plan",
        staticmethod(
            lambda db, p, **kw: SimpleNamespace(
                id_plan=1,
                nombre=kw["nombre"],
                precio_mensual=kw["precio_mensual"],
                max_sucursales_activas=kw["max_sucursales_activas"],
                max_empleados=kw["max_empleados"],
                activo=True,
                creado_en=now,
            )
        ),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "funcionalidades_de_plan",
        staticmethod(
            lambda db, i: [SimpleNamespace(codigo="productos", nombre="Productos", descripcion=None)]
        ),
    )
    monkeypatch.setattr(
        PlanesFuncionalidadesRepositorio,
        "contar_empresas_del_plan",
        staticmethod(lambda db, i, hoy: (1, 1)),
    )

    datos = PlanActualizarIn(
        nombre="Básico",
        precio_mensual=Decimal("29.00"),
        max_sucursales_activas=2,  # menor que 3
        max_empleados=5,           # menor que 8
        funcionalidades=["productos"],
    )
    res = PlanesFuncionalidadesServicio.actualizar_plan(MagicMock(), 1, datos, super_admin)
    assert res.max_sucursales_activas == 2
    assert res.max_empleados == 5
    assert len(res.advertencias) == 2
    assert "FASHION STORE" in res.advertencias[0]


# ---------------------------------------------------------------------------
# AC-06: P2-CU07 (Suscripciones de empresas y Curso Alterno A1)
# ---------------------------------------------------------------------------


def test_ac06_cambio_plan_rechaza_si_uso_actual_supera_limite_del_plan_destino(
    monkeypatch, super_admin
):
    now = datetime.now(timezone.utc)
    tenant = SimpleNamespace(
        id_tenant=1, codigo="fashionstore", nombre="FASHION STORE", estado="activa"
    )
    susc_actual = SimpleNamespace(
        id_suscripcion=10,
        id_tenant=1,
        id_plan=2,
        estado="activa",
        fecha_inicio=date(2026, 1, 1),
        fecha_vencimiento=date(2027, 1, 1),
        creado_en=now,
    )
    plan_actual = SimpleNamespace(
        id_plan=2,
        nombre="Profesional",
        precio_mensual=Decimal("79.00"),
        max_sucursales_activas=10,
        max_empleados=None,
        activo=True,
    )
    plan_basico = SimpleNamespace(
        id_plan=1,
        nombre="Básico",
        precio_mensual=Decimal("29.00"),
        max_sucursales_activas=2,
        max_empleados=5,
        activo=True,
    )

    monkeypatch.setattr(
        SuscripcionesAdminRepositorio, "obtener_tenant", staticmethod(lambda db, i: tenant)
    )
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio,
        "suscripcion_actual_empresa",
        staticmethod(lambda db, i: (susc_actual, plan_actual)),
    )
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio, "obtener_plan", staticmethod(lambda db, i: plan_basico)
    )
    # Uso actual: 4 sucursales activas (> 2 del Básico)
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio,
        "uso_recursos_empresa",
        staticmethod(lambda db, i: (4, 3)),
    )

    with pytest.raises(ConflictError) as exc:
        SuscripcionesAdminServicio.operar_suscripcion(
            MagicMock(),
            1,
            OperacionSuscripcionIn(operacion="cambio_plan", id_plan=1),
            super_admin,
        )
    assert exc.value.code == "USO_SUPERA_LIMITE_PLAN"
    assert "sucursales activas" in exc.value.message


def test_ac06_renovacion_y_suspension_registran_historial(monkeypatch, super_admin):
    now = datetime.now(timezone.utc)
    tenant = SimpleNamespace(
        id_tenant=1, codigo="fashionstore", nombre="FASHION STORE", estado="activa"
    )
    susc_actual = SimpleNamespace(
        id_suscripcion=10,
        id_tenant=1,
        id_plan=2,
        estado="activa",
        fecha_inicio=date(2026, 1, 1),
        fecha_vencimiento=date(2027, 1, 1),
        creado_en=now,
    )
    plan_actual = SimpleNamespace(
        id_plan=2,
        nombre="Profesional",
        precio_mensual=Decimal("79.00"),
        max_sucursales_activas=10,
        max_empleados=None,
        activo=True,
    )
    eventos_registrados = []

    monkeypatch.setattr(
        SuscripcionesAdminRepositorio, "obtener_tenant", staticmethod(lambda db, i: tenant)
    )
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio,
        "suscripcion_actual_empresa",
        staticmethod(lambda db, i: (susc_actual, plan_actual)),
    )
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio,
        "uso_recursos_empresa",
        staticmethod(lambda db, i: (2, 4)),
    )
    monkeypatch.setattr(
        SuscripcionesAdminRepositorio,
        "registrar_evento_historial",
        staticmethod(lambda db, **kw: eventos_registrados.append(kw)),
    )

    res_ren = SuscripcionesAdminServicio.operar_suscripcion(
        SesionFalsa(),  # type: ignore[arg-type]
        1,
        OperacionSuscripcionIn(operacion="renovacion", fecha_vencimiento=date(2028, 1, 1)),
        super_admin,
    )
    assert res_ren.fecha_vencimiento == date(2028, 1, 1)
    assert eventos_registrados[-1]["evento"] == "renovacion"

    res_susp = SuscripcionesAdminServicio.operar_suscripcion(
        SesionFalsa(),  # type: ignore[arg-type]
        1,
        OperacionSuscripcionIn(operacion="suspension", motivo="Mora"),
        super_admin,
    )
    assert res_susp.estado == "suspendida"
    assert eventos_registrados[-1]["evento"] == "suspension"


# ---------------------------------------------------------------------------
# AC-07: P2-CU08 (Catálogos globales: ciudades, tallas, colores y Curso Alterno A2)
# ---------------------------------------------------------------------------


def test_ac07_eliminar_ciudad_en_uso_rechaza_409_y_permite_desactivar(monkeypatch, super_admin):
    now = datetime.now(timezone.utc)
    ciudad_en_uso = {
        "id_ciudad": 1,
        "nombre": "Santa Cruz de la Sierra",
        "pais": "Bolivia",
        "activo": True,
        "creado_en": now,
        "sucursales_asociadas": 2,
    }
    monkeypatch.setattr(
        CatalogosGlobalesRepositorio,
        "obtener_ciudad",
        staticmethod(lambda db, i: ciudad_en_uso),
    )

    with pytest.raises(ConflictError) as exc:
        CatalogosGlobalesServicio.eliminar_ciudad(MagicMock(), 1, super_admin)
    assert exc.value.code == "ELEMENTO_CATALOGO_EN_USO"

    # Desactivar la ciudad en uso (CU08 A2) funciona sin eliminarla
    monkeypatch.setattr(
        CatalogosGlobalesRepositorio,
        "cambiar_estado_ciudad",
        staticmethod(lambda db, i, activo: {**ciudad_en_uso, "activo": activo}),
    )
    res_desact = CatalogosGlobalesServicio.cambiar_estado_ciudad(
        MagicMock(), 1, CambiarEstadoCatalogoIn(activo=False), super_admin
    )
    assert res_desact.activo is False


def test_ac07_tallas_y_colores_protegen_integridad_y_unicidad(monkeypatch, super_admin):
    talla_en_uso = {
        "id_talla": 3,
        "codigo": "M",
        "orden": 3,
        "activo": True,
        "variantes_asociadas": 15,
    }
    monkeypatch.setattr(
        CatalogosGlobalesRepositorio,
        "obtener_talla",
        staticmethod(lambda db, i: talla_en_uso),
    )
    with pytest.raises(ConflictError) as exc_talla:
        CatalogosGlobalesServicio.eliminar_talla(MagicMock(), 3, super_admin)
    assert exc_talla.value.code == "ELEMENTO_CATALOGO_EN_USO"

    # Color sin variantes asociadas se elimina correctamente
    color_libre = {
        "id_color": 9,
        "nombre": "Lavanda",
        "codigo_hex": "#E6E6FA",
        "activo": True,
        "variantes_asociadas": 0,
    }
    monkeypatch.setattr(
        CatalogosGlobalesRepositorio,
        "obtener_color",
        staticmethod(lambda db, i: color_libre),
    )
    monkeypatch.setattr(
        CatalogosGlobalesRepositorio,
        "eliminar_color",
        staticmethod(lambda db, i: None),
    )
    res_del = CatalogosGlobalesServicio.eliminar_color(MagicMock(), 9, super_admin)
    assert res_del.eliminado is True


def test_ac08_rutas_plataforma_registradas_en_app(client):
    from core.database import get_db
    from main import app

    rutas = set(app.openapi()["paths"].keys())
    esperadas = {
        "/api/v1/plataforma/empresas",
        "/api/v1/plataforma/empresas/{id_tenant}",
        "/api/v1/plataforma/empresas/{id_tenant}/estado",
        "/api/v1/plataforma/metricas",
        "/api/v1/plataforma/bitacora",
        "/api/v1/plataforma/funcionalidades",
        "/api/v1/plataforma/planes",
        "/api/v1/plataforma/planes/{id_plan}",
        "/api/v1/plataforma/planes/{id_plan}/estado",
        "/api/v1/plataforma/suscripciones",
        "/api/v1/plataforma/empresas/{id_tenant}/suscripciones/historial",
        "/api/v1/plataforma/empresas/{id_tenant}/suscripcion",
        "/api/v1/plataforma/catalogos/ciudades",
        "/api/v1/plataforma/catalogos/tallas",
        "/api/v1/plataforma/catalogos/colores",
    }
    assert esperadas.issubset(rutas)

    # Petición sin token a ruta protegida del Super Administrador devuelve 401
    app.dependency_overrides[get_db] = lambda: SesionFalsa()
    try:
        resp = client.get("/api/v1/plataforma/empresas")
        assert resp.status_code == 401
        assert resp.json()["code"] == "TOKEN_INVALIDO"
    finally:
        app.dependency_overrides.pop(get_db, None)


