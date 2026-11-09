"""Perfil del empleado contra la rama de pruebas (RLS real, rol fashionstore_app).

Reutiliza la infraestructura de `test_multitenant.py`: empresa B con su administrador, dentro de una
transacción que se deshace al final.
"""

import pytest
from sqlalchemy import text

from tests.integracion.test_multitenant import (  # noqa: F401 (fixtures)
    CLAVE_PRUEBA,
    URL_APP,
    _contexto,
    _token,
    motor,
    mundo,
)

pytestmark = pytest.mark.skipif(not URL_APP, reason="Sin DATABASE_URL_PRUEBAS_APP.")


def test_el_administrador_ve_su_empresa_y_cambia_su_contrasena(mundo):
    cliente, admin = mundo["cliente"], _token(mundo["admin_b"], "administrador", mundo["id_b"])

    perfil = cliente.get("/api/v1/mi-perfil-empleado", headers=admin)
    assert perfil.status_code == 200, perfil.text
    cuerpo = perfil.json()
    assert cuerpo["email"] == "admin@empresa-b.com"
    assert cuerpo["empresa"] == {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "BOB"}
    assert cuerpo["todas_las_sucursales"] is True

    # El perfil del cliente sigue cerrado a los empleados
    assert cliente.get("/api/v1/perfil", headers=admin).status_code == 403

    cambio = cliente.post("/api/v1/mi-perfil-empleado/contrasena", headers=admin,
                          json={"contrasena_actual": CLAVE_PRUEBA, "contrasena_nueva": "OtraClave2027"})
    assert cambio.status_code == 204, cambio.text
    nuevo_login = cliente.post("/api/v1/autenticacion/login",
                               json={"email": "admin@empresa-b.com", "password": "OtraClave2027"})
    assert nuevo_login.status_code == 200, nuevo_login.text


def test_el_cajero_ve_sus_sucursales_autorizadas(mundo):
    cliente, admin = mundo["cliente"], _token(mundo["admin_b"], "administrador", mundo["id_b"])
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    b1, b2 = [f[0] for f in c.execute(text("SELECT id_sucursal FROM fashionstore.sucursales ORDER BY id_sucursal"))]
    _contexto(c)
    alta = cliente.post("/api/v1/admin/usuarios", headers=admin, json={
        "email": "cajera.perfil@empresa-b.com", "password": CLAVE_PRUEBA, "nombres": "Cajera", "apellidos": "Perfil",
        "rol": "cajero", "sucursales_autorizadas": [b1, b2], "id_sucursal_principal": b2})
    assert alta.status_code == 201, alta.text

    perfil = cliente.get("/api/v1/mi-perfil-empleado",
                         headers=_token(alta.json()["id_usuario"], "cajero", mundo["id_b"]))
    assert perfil.status_code == 200, perfil.text
    assert perfil.json()["todas_las_sucursales"] is False
    assert [(s["id_sucursal"], s["es_principal"]) for s in perfil.json()["sucursales"]] == [(b2, True), (b1, False)]
    assert all(s["nombre"] for s in perfil.json()["sucursales"])
