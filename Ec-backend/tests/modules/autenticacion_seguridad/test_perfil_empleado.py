"""Perfil del empleado (fix: `/admin/perfil` usaba el perfil del cliente y daba 403).

Lo que depende de PostgreSQL (empresa y sucursales reales con RLS) está en
`tests/integracion/test_multitenant.py` §perfil del empleado.
"""

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from core.database import get_db
from core.deps import get_current_user
from core.security import hash_password, verify_password
from main import app
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

URL = "/api/v1/mi-perfil-empleado"
CLAVE = "ClaveActual2026"


def empleado(rol="cajero", id_sucursal=3):
    usuario = UsuarioORM(
        id_usuario=9, email="cajero@menshopping.com", nombres="Cajero", apellidos="Santa Cruz",
        telefono=None, rol=rol, id_sucursal=id_sucursal, id_tenant=2, activo=True,
        password_hash=hash_password(CLAVE),
    )
    return usuario


@pytest.fixture
def cliente(monkeypatch):
    eventos = []
    monkeypatch.setattr(
        ServicioBitacoraAuditoria, "registrar_evento_seguro", classmethod(lambda cls, **kw: eventos.append(kw))
    )
    app.dependency_overrides[get_db] = lambda: MagicMock()
    yield TestClient(app), eventos
    app.dependency_overrides.clear()


def _como(usuario):
    app.dependency_overrides[get_current_user] = lambda: usuario


@pytest.mark.parametrize("rol", ["administrador", "encargado_sucursal", "cajero"])
def test_los_empleados_ven_su_perfil(cliente, rol):
    http, _ = cliente
    _como(empleado(rol, None if rol == "administrador" else 3))
    respuesta = http.get(URL)
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["rol"] == rol and cuerpo["email"] == "cajero@menshopping.com"
    assert cuerpo["todas_las_sucursales"] is (rol == "administrador")
    if rol != "administrador":
        assert cuerpo["sucursales"] == [{"id_sucursal": 3, "nombre": None, "es_principal": True}]


@pytest.mark.parametrize("rol", ["cliente", "super_administrador"])
def test_clientes_y_super_administrador_no(cliente, rol):
    http, _ = cliente
    _como(empleado(rol, None))
    assert http.get(URL).status_code == 403


def test_actualiza_solo_lo_que_cambia_y_lo_registra(cliente):
    http, eventos = cliente
    usuario = empleado()
    _como(usuario)
    respuesta = http.patch(URL, json={"nombres": "  Carla ", "telefono": "+591 70000000"})
    assert respuesta.status_code == 200, respuesta.text
    assert usuario.nombres == "Carla" and usuario.telefono == "+591 70000000"
    assert [e["accion"] for e in eventos] == ["PERFIL_EMPLEADO_MODIFICADO"]
    assert eventos[0]["payload_nuevo"] == {"nombres": "Carla", "telefono": "+591 70000000"}


def test_cambiar_contrasena(cliente):
    http, eventos = cliente
    usuario = empleado()
    _como(usuario)
    respuesta = http.post(f"{URL}/contrasena", json={"contrasena_actual": CLAVE, "contrasena_nueva": "NuevaClave2027"})
    assert respuesta.status_code == 204, respuesta.text
    assert verify_password("NuevaClave2027", usuario.password_hash)
    assert [e["accion"] for e in eventos] == ["CONTRASENA_CAMBIADA"]
    assert "NuevaClave2027" not in str(eventos) and CLAVE not in str(eventos)


@pytest.mark.parametrize("cuerpo, estado, codigo", [
    ({"contrasena_actual": "Incorrecta1", "contrasena_nueva": "NuevaClave2027"}, 400, "CONTRASENA_ACTUAL_INCORRECTA"),
    ({"contrasena_actual": CLAVE, "contrasena_nueva": CLAVE}, 400, "CONTRASENA_REPETIDA"),
    ({"contrasena_actual": CLAVE, "contrasena_nueva": "debil"}, 422, None),
])
def test_cambiar_contrasena_rechazos(cliente, cuerpo, estado, codigo):
    http, eventos = cliente
    usuario = empleado()
    anterior = usuario.password_hash
    _como(usuario)
    respuesta = http.post(f"{URL}/contrasena", json=cuerpo)
    assert respuesta.status_code == estado
    if codigo:
        assert respuesta.json()["code"] == codigo
    assert usuario.password_hash == anterior and eventos == []
