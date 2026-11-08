"""Pruebas unitarias de P2-CU02 · Acceso por empresa, sin base de datos.

Spec: `.specs/changes/P2-CU02-CU01-acceso-por-empresa/spec.md` §A.6. El comportamiento contra
PostgreSQL (funciones de 0015, RLS y flujo completo del cliente) está en
`tests/integracion/test_multitenant.py`.
"""

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from core.errors import AuthorizationError, DomainError
from core.tenant import CLAVE_TENANT, CLAVE_TENANT_CABECERA, TenantInfo
from modules.autenticacion_seguridad.cu02_iniciar_sesion.esquemas import LoginIn, LoginOut
from modules.plataforma import servicio_tenants
from modules.plataforma.servicio_tenants import TenantServicio

FASHION = TenantInfo(1, "fashionstore", "FASHION STORE", "activa")
OTRA = TenantInfo(2, "menshopping", "Menshopping", "activa")


class SesionFalsa:
    def __init__(self, cabecera=None):
        self.info = {CLAVE_TENANT: cabecera, CLAVE_TENANT_CABECERA: cabecera}
        self.agregados = []

    def in_transaction(self):
        return False

    def execute(self, *_a, **_k):
        return SimpleNamespace(scalar_one_or_none=lambda: None)

    def add(self, objeto):
        self.agregados.append(objeto)

    def flush(self):
        pass


@pytest.fixture
def disponibles(monkeypatch):
    monkeypatch.setattr(servicio_tenants, "empresas_disponibles", lambda db: [FASHION, OTRA])


def test_el_login_ya_no_pide_codigo_de_empresa():
    datos = LoginIn(email="a@b.com", password="x", codigo_empresa="fashionstore")  # se ignora
    assert not hasattr(datos, "codigo_empresa")
    assert LoginOut(access_token="t", id_usuario=1, email="a@b.com", nombres="A", apellidos="B",
                    rol="cliente").empresas == []


@pytest.mark.parametrize("rol, id_tenant, esperado", [
    ("cliente", None, None), ("super_administrador", None, None), ("cajero", 3, 3), ("administrador", 1, 1),
])
def test_el_token_del_cliente_no_lleva_empresa(rol, id_tenant, esperado):
    usuario = SimpleNamespace(rol=rol, id_tenant=id_tenant, id_usuario=7)
    assert TenantServicio.empresa_del_token(MagicMock(), usuario) == esperado


def test_empresas_del_cliente_vacia_para_empleados():
    assert TenantServicio.empresas_del_cliente(SesionFalsa(), SimpleNamespace(rol="cajero", id_usuario=1)) == []


def test_empresa_del_portal_disponible(disponibles):
    assert TenantServicio.empresa_del_portal(SesionFalsa(cabecera=2)) == 2
    assert TenantServicio.empresa_del_portal(SesionFalsa()) is None


def test_empresa_del_portal_no_disponible_403(disponibles):
    with pytest.raises(AuthorizationError) as error:
        TenantServicio.empresa_del_portal(SesionFalsa(cabecera=9))
    assert error.value.code == "TENANT_INACTIVO"


def test_registrarse_en_tienda(disponibles):
    db = SesionFalsa(cabecera=2)
    assert TenantServicio.registrar_en_tienda(db, SimpleNamespace(rol="cliente", id_usuario=5)) is True
    assert db.agregados[0].id_tenant == 2 and db.agregados[0].id_cliente == 5


def test_registrarse_en_tienda_solo_clientes(disponibles):
    with pytest.raises(AuthorizationError) as error:
        TenantServicio.registrar_en_tienda(SesionFalsa(cabecera=2), SimpleNamespace(rol="cajero", id_usuario=14))
    assert error.value.code == "SOLO_CLIENTES"


def test_registrarse_en_tienda_sin_tienda_400(disponibles):
    with pytest.raises(DomainError) as error:
        TenantServicio.registrar_en_tienda(SesionFalsa(), SimpleNamespace(rol="cliente", id_usuario=5))
    assert error.value.code == "TENANT_REQUERIDO"
