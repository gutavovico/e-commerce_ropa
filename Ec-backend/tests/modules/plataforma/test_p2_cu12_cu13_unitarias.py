"""Pruebas unitarias de la fundación multitenant (P2-CU13 · P2-CU12), sin base de datos.

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.4 y §A.5.
Las pruebas contra PostgreSQL real (RLS, FK compuestas, vistas) están en
`tests/integracion/test_multitenant.py`.
"""

from datetime import date
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core import tenant as modulo_tenant
from core.errors import AuthorizationError, ConflictError, NotFoundError
from core.security import create_access_token, decode_access_token
from core.tenant import (
    CLAVE_TENANT,
    CLAVE_TENANT_CABECERA,
    TenantInfo,
    aplicar_tenant_del_token,
    contexto,
    fijar_contexto,
    preparar_sesion,
)
from modules.plataforma.cu12_validar_suscripcion import servicio as modulo_cu12
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio
from modules.plataforma.servicio_tenants import TenantServicio, es_rol_sin_empresa

FASHION = TenantInfo(1, "fashionstore", "FASHION STORE", "activa")
OTRA = TenantInfo(2, "menshopping", "Menshopping", "activa")
SUSPENDIDA = TenantInfo(3, "cerrada", "Cerrada", "suspendida")


class SesionFalsa:
    """Doble mínimo de `Session`: `info` real y registro de las sentencias ejecutadas."""

    def __init__(self, en_transaccion=False):
        self.info = {}
        self.ejecutadas = []
        self._en_transaccion = en_transaccion

    def in_transaction(self):
        return self._en_transaccion

    def execute(self, sentencia, parametros=None):
        self.ejecutadas.append((str(sentencia), parametros))

    def rollback(self):
        pass


@pytest.fixture
def tenants(monkeypatch):
    catalogo = {t.codigo: t for t in (FASHION, OTRA, SUSPENDIDA)}
    monkeypatch.setattr(modulo_tenant, "buscar_tenant", lambda db, codigo: catalogo.get(codigo))
    return catalogo


# ---------------------------------------------------------------------------- P2-CU13 · contexto

def test_las_sesiones_simuladas_no_tienen_contexto():
    assert contexto(MagicMock()) is None
    fijar_contexto(MagicMock(), 1)  # no falla ni hace nada


def test_fijar_contexto_dentro_de_una_transaccion_lo_aplica_de_inmediato():
    db = SesionFalsa(en_transaccion=True)
    fijar_contexto(db, 7, id_usuario=14)
    assert db.info[CLAVE_TENANT] == 7
    assert db.ejecutadas and db.ejecutadas[-1][1] == {"t": "7", "u": "14", "p": ""}


def test_sin_cabecera_usa_la_empresa_por_defecto(tenants):
    db = SesionFalsa()
    preparar_sesion(db, None, "fashionstore")
    assert db.info[CLAVE_TENANT] == 1
    assert CLAVE_TENANT_CABECERA not in db.info


def test_cabecera_con_empresa_inexistente_404(tenants):
    with pytest.raises(NotFoundError) as error:
        preparar_sesion(SesionFalsa(), "no-existe", "fashionstore")
    assert error.value.code == "TENANT_NO_ENCONTRADO"


def test_cabecera_con_empresa_suspendida_403(tenants):
    with pytest.raises(AuthorizationError) as error:
        preparar_sesion(SesionFalsa(), "cerrada", "fashionstore")
    assert error.value.code == "TENANT_INACTIVO"


def test_empresa_por_defecto_inexistente_deja_la_sesion_sin_empresa(tenants):
    db = SesionFalsa()
    preparar_sesion(db, None, "no-existe")
    assert db.info[CLAVE_TENANT] is None  # F5: sin empresa la RLS no deja ver nada


def test_el_token_manda_sobre_la_empresa_por_defecto(tenants):
    db = SesionFalsa()
    preparar_sesion(db, None, "fashionstore")
    aplicar_tenant_del_token(db, 2, id_usuario=30)
    assert db.info[CLAVE_TENANT] == 2


def test_token_y_cabecera_de_empresas_distintas_403(tenants):
    db = SesionFalsa()
    preparar_sesion(db, "menshopping", "fashionstore")
    with pytest.raises(AuthorizationError) as error:
        aplicar_tenant_del_token(db, 1, id_usuario=14)
    assert error.value.code == "TENANT_NO_COINCIDE"


def test_cliente_sin_empresa_en_el_token_conserva_la_del_portal(tenants):
    db = SesionFalsa()
    preparar_sesion(db, "menshopping", "fashionstore")
    aplicar_tenant_del_token(db, None, id_usuario=2)
    assert db.info[CLAVE_TENANT] == 2


@pytest.mark.parametrize("rol, sin_empresa", [
    ("cliente", True), ("super_administrador", True),
    ("administrador", False), ("encargado_sucursal", False), ("cajero", False),
])
def test_roles_sin_empresa(rol, sin_empresa):
    assert es_rol_sin_empresa(rol) is sin_empresa


def test_un_token_antiguo_sin_empresa_es_rechazado(client):
    token = create_access_token({"sub": "14", "rol": "cajero"})  # sin id_tenant
    respuesta = client.get("/api/v1/perfil", headers={"Authorization": f"Bearer {token}"})
    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "TOKEN_INVALIDO"


def test_el_token_del_login_lleva_la_empresa():
    empleado = SimpleNamespace(rol="cajero", id_tenant=1, id_usuario=14)
    assert TenantServicio.empresa_del_token(MagicMock(), empleado) == 1
    token = create_access_token({"sub": "14", "id_tenant": TenantServicio.empresa_del_token(MagicMock(), empleado)})
    assert decode_access_token(token)["id_tenant"] == 1
    super_admin = SimpleNamespace(rol="super_administrador", id_tenant=None, id_usuario=1)
    assert TenantServicio.empresa_del_token(MagicMock(), super_admin) is None


# ---------------------------------------------------------------------------- P2-CU12

@pytest.fixture
def plan(monkeypatch):
    """Empresa 2 con plan Básico vigente; el estado se ajusta en cada prueba."""
    estado = SimpleNamespace(
        suscripcion=SimpleNamespace(id_plan=10),
        plan=SimpleNamespace(id_plan=10, nombre="Básico", max_sucursales_activas=2, max_empleados=None),
        funcionalidades={"productos", "ventas", "reservas", "operacion_offline", "reportes_convencionales"},
        sucursales=1, empleados=5,
    )
    repo = modulo_cu12.SuscripcionRepositorio
    monkeypatch.setattr(repo, "suscripcion_vigente", staticmethod(lambda db, t, hoy: estado.suscripcion))
    monkeypatch.setattr(repo, "plan", staticmethod(lambda db, i: estado.plan))
    monkeypatch.setattr(repo, "plan_incluye", staticmethod(lambda db, i, f: f in estado.funcionalidades))
    monkeypatch.setattr(repo, "planes_con", staticmethod(lambda db, f: ["Profesional"]))
    monkeypatch.setattr(modulo_cu12, "RECURSOS", {
        "sucursales": ("sucursales activas", "max_sucursales_activas", lambda db, t: estado.sucursales),
        "empleados": ("empleados", "max_empleados", lambda db, t: estado.empleados),
    })
    return estado


def _sesion_de(id_tenant):
    db = SesionFalsa()
    db.info[CLAVE_TENANT] = id_tenant
    return db


def test_cu12_operacion_permitida(plan):
    SuscripcionServicio.validar(_sesion_de(2), funcionalidad="ventas", recurso="sucursales")


def test_cu12_suscripcion_no_vigente_403(plan):
    plan.suscripcion = None
    with pytest.raises(AuthorizationError) as error:
        SuscripcionServicio.validar(_sesion_de(2), funcionalidad="reservas")
    assert error.value.code == "SUSCRIPCION_NO_VIGENTE"


def test_cu12_funcionalidad_no_incluida_indica_el_plan_que_la_tiene(plan):
    with pytest.raises(AuthorizationError) as error:
        SuscripcionServicio.validar(_sesion_de(2), funcionalidad="reportes_ia")
    assert error.value.code == "FUNCIONALIDAD_NO_INCLUIDA"
    assert "Profesional" in error.value.message


def test_cu12_limite_de_sucursales_alcanzado_409(plan):
    plan.sucursales = 2
    with pytest.raises(ConflictError) as error:
        SuscripcionServicio.validar(_sesion_de(2), recurso="sucursales")
    assert error.value.code == "LIMITE_PLAN_ALCANZADO"
    assert "2 sucursales activas" in error.value.message


def test_cu12_limite_nulo_significa_sin_limite(plan):
    plan.empleados = 10_000
    SuscripcionServicio.validar(_sesion_de(2), recurso="empleados")


def test_cu12_sin_empresa_403(plan):
    with pytest.raises(AuthorizationError) as error:
        SuscripcionServicio.validar(_sesion_de(None), funcionalidad="ventas")
    assert error.value.code == "TENANT_REQUERIDO"


def test_cu12_modo_plataforma_no_se_valida(plan):
    plan.suscripcion = None
    db = _sesion_de(None)
    db.info["modo_plataforma"] = True
    SuscripcionServicio.validar(db, funcionalidad="ventas")


def test_cu12_sesion_simulada_no_se_valida():
    SuscripcionServicio.validar(MagicMock(), funcionalidad="ventas")


def test_cu12_funcionalidad_desconocida_es_un_error_de_programacion():
    with pytest.raises(ValueError):
        SuscripcionServicio.validar(MagicMock(), funcionalidad="inventada")
