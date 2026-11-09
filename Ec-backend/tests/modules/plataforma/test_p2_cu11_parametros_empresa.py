"""Pruebas unitarias de P2-CU11 · Parámetros de la empresa, sin base de datos.

Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §5. El comportamiento con RLS y los CHECK
de la base está en `tests/integracion/test_multitenant.py`.
"""

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.cu11_parametros_empresa import servicio as srv
from modules.plataforma.cu11_parametros_empresa.repositorio import ParametrosEmpresaRepositorio
from modules.plataforma.modelos import ConfiguracionTenantORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

URL = "/api/v1/admin/configuracion"
VALIDOS = {
    "horas_vencimiento_reserva": 24,
    "dias_cambio_prenda": 15,
    "operacion_offline_habilitada": True,
    "dias_antiguedad_offline": 7,
}


def fila_por_defecto() -> ConfiguracionTenantORM:
    return ConfiguracionTenantORM(
        id_tenant=1, moneda="EUR", zona_horaria="Europe/Madrid", horas_vencimiento_reserva=24,
        dias_cambio_prenda=15, operacion_offline_habilitada=True, dias_antiguedad_offline=7,
        actualizado_en=datetime(2026, 11, 8, tzinfo=timezone.utc),
    )


def usuario(rol: str) -> UsuarioORM:
    u = MagicMock(spec=UsuarioORM)
    u.id_usuario, u.rol, u.activo = 1, rol, True
    u.nombres, u.apellidos, u.email = "Ana", "Admin", "ana@tienda.com"
    return u


@pytest.fixture
def entorno(monkeypatch):
    """Empresa 1 en el contexto, una fila en «la base» y la bitácora capturada."""
    estado = {"fila": fila_por_defecto(), "creadas": 0, "eventos": []}
    monkeypatch.setattr(srv, "tenant_actual", lambda db: 1)
    monkeypatch.setattr(srv.SuscripcionServicio, "validar", staticmethod(lambda db, **kw: None))

    def leer(db, id_tenant, bloquear=False):
        return estado["fila"]

    def crear_si_falta(db):
        estado["creadas"] += 1
        estado["fila"] = fila_por_defecto()

    monkeypatch.setattr(ParametrosEmpresaRepositorio, "leer", staticmethod(leer))
    monkeypatch.setattr(ParametrosEmpresaRepositorio, "crear_si_falta", staticmethod(crear_si_falta))
    monkeypatch.setattr(
        ServicioBitacoraAuditoria, "registrar_evento_seguro",
        classmethod(lambda cls, **kw: estado["eventos"].append(kw)),
    )
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: usuario("administrador")
    yield estado
    app.dependency_overrides.clear()


@pytest.fixture
def cliente():
    return TestClient(app)


def test_lee_los_parametros(entorno, cliente):
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200
    assert respuesta.json() == {
        "moneda": "EUR", "zona_horaria": "Europe/Madrid", "horas_vencimiento_reserva": 24,
        "dias_cambio_prenda": 15, "operacion_offline_habilitada": True, "dias_antiguedad_offline": 7,
        "actualizado_en": "2026-11-08T00:00:00Z",
    }


def test_c4_crea_la_fila_que_falta(entorno, cliente):
    entorno["fila"] = None
    respuesta = cliente.get(URL)
    assert respuesta.status_code == 200
    assert entorno["creadas"] == 1
    assert respuesta.json()["horas_vencimiento_reserva"] == 24


def test_guarda_y_registra_solo_lo_que_cambio(entorno, cliente):
    respuesta = cliente.put(URL, json={**VALIDOS, "horas_vencimiento_reserva": 48, "operacion_offline_habilitada": False})
    assert respuesta.status_code == 200
    assert respuesta.json()["horas_vencimiento_reserva"] == 48
    assert respuesta.json()["operacion_offline_habilitada"] is False
    assert len(entorno["eventos"]) == 1
    evento = entorno["eventos"][0]
    assert evento["accion"] == "CONFIGURACION_MODIFICADA"
    assert evento["payload_anterior"] == {"horas_vencimiento_reserva": 24, "operacion_offline_habilitada": True}
    assert evento["payload_nuevo"] == {"horas_vencimiento_reserva": 48, "operacion_offline_habilitada": False}
    assert evento["id_usuario"] == 1


def test_sin_cambios_no_escribe_bitacora(entorno, cliente):
    assert cliente.put(URL, json=VALIDOS).status_code == 200
    assert entorno["eventos"] == []


@pytest.mark.parametrize("campo, valor", [
    ("horas_vencimiento_reserva", 0),
    ("horas_vencimiento_reserva", 169),
    ("dias_cambio_prenda", -1),
    ("dias_cambio_prenda", 91),
    ("dias_antiguedad_offline", 0),
    ("dias_antiguedad_offline", 31),
])
def test_c3_fuera_de_rango_no_se_guarda(entorno, cliente, campo, valor):
    respuesta = cliente.put(URL, json={**VALIDOS, campo: valor})
    assert respuesta.status_code == 422
    assert getattr(entorno["fila"], campo) == VALIDOS[campo]
    assert entorno["eventos"] == []


def test_c2_moneda_y_zona_no_se_cambian(entorno, cliente):
    respuesta = cliente.put(URL, json={**VALIDOS, "moneda": "USD", "zona_horaria": "America/La_Paz"})
    assert respuesta.status_code == 200
    assert respuesta.json()["moneda"] == "EUR"
    assert respuesta.json()["zona_horaria"] == "Europe/Madrid"


@pytest.mark.parametrize("rol", ["encargado_sucursal", "cajero", "cliente"])
def test_c8_solo_el_administrador(entorno, cliente, rol):
    app.dependency_overrides[get_current_user] = lambda: usuario(rol)
    assert cliente.get(URL).status_code == 403
    assert cliente.put(URL, json=VALIDOS).status_code == 403


def test_c8_guardar_exige_suscripcion_vigente(entorno, cliente, monkeypatch):
    from core.errors import AuthorizationError

    def vencida(db, **kw):
        raise AuthorizationError("La suscripción no está vigente.", code="SUSCRIPCION_NO_VIGENTE")

    monkeypatch.setattr(srv.SuscripcionServicio, "validar", staticmethod(vencida))
    respuesta = cliente.put(URL, json={**VALIDOS, "dias_cambio_prenda": 30})
    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SUSCRIPCION_NO_VIGENTE"
    assert entorno["fila"].dias_cambio_prenda == 15


def test_vigentes_para_otros_paquetes(entorno):
    parametros = srv.ParametrosEmpresaServicio.vigentes(MagicMock())
    assert parametros.horas_vencimiento_reserva == 24
    assert parametros.dias_cambio_prenda == 15
    with pytest.raises(Exception):
        parametros.dias_cambio_prenda = 1  # inmutable


def test_sin_empresa_en_el_contexto(monkeypatch):
    monkeypatch.setattr(srv, "tenant_actual", lambda db: None)
    with pytest.raises(Exception) as error:
        srv.ParametrosEmpresaServicio.vigentes(MagicMock())
    assert getattr(error.value, "code", None) == "TENANT_REQUERIDO"
