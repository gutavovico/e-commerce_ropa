"""Pruebas de integración de la fundación multitenant contra PostgreSQL real (RNF11).

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.5 (decisión F18).

Se ejecutan en la rama de Neon `pruebas-multitenant` conectando con el rol de la aplicación
(`fashionstore_app`, sin BYPASSRLS), que es lo que hace cumplir la seguridad por filas. Requieren en
`Ec-backend/.env` la variable `DATABASE_URL_PRUEBAS_APP`; sin ella se saltan.

Todo ocurre dentro de una transacción que se deshace al final: la rama no queda modificada.
La segunda empresa (`pruebas-b`) y sus datos se crean dentro de esa transacción.
"""

from pathlib import Path

import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from core.database import get_db
from core.security import create_access_token, hash_password
from core.tenant import CABECERA_TENANT, limpiar_cache_tenants, preparar_sesion
from main import app
from modules.plataforma.cu12_validar_suscripcion.servicio import SuscripcionServicio


def _leer_env(clave: str):
    archivo = Path(__file__).resolve().parents[2] / ".env"
    if not archivo.is_file():
        return None
    for linea in archivo.read_text(encoding="utf-8").splitlines():
        if linea.strip().startswith(f"{clave}="):
            return linea.split("=", 1)[1].strip().strip("\"'") or None
    return None


URL_APP = _leer_env("DATABASE_URL_PRUEBAS_APP")
pytestmark = pytest.mark.skipif(
    not URL_APP, reason="Sin DATABASE_URL_PRUEBAS_APP: se omiten las pruebas de aislamiento contra Neon."
)

CLAVE_PRUEBA = "ClavePrueba123!"


# --------------------------------------------------------------------------------- infraestructura

@pytest.fixture(scope="module")
def motor():
    url = URL_APP.replace("postgresql://", "postgresql+psycopg://", 1) if URL_APP.startswith("postgresql://") else URL_APP
    eng = create_engine(url, pool_pre_ping=True)
    yield eng
    eng.dispose()


def _contexto(c, tenant=None, usuario=None, plataforma=False):
    c.execute(
        text("SELECT set_config('app.id_tenant', :t, true), set_config('app.id_usuario', :u, true), "
             "set_config('app.modo_plataforma', :p, true)"),
        {"t": str(tenant) if tenant else "", "u": str(usuario) if usuario else "", "p": "on" if plataforma else ""},
    )


@pytest.fixture
def mundo(motor):
    """Conexión con una transacción exterior que se deshace al final, y una empresa B con datos."""
    limpiar_cache_tenants()
    conexion = motor.connect()
    exterior = conexion.begin()
    _contexto(conexion, plataforma=True)
    q = lambda sql, **p: conexion.execute(text(sql), p).scalar()

    id_b = q("INSERT INTO fashionstore.tenants (codigo, nombre) VALUES ('pruebas-b', 'Empresa B') RETURNING id_tenant")
    basico = q("SELECT id_plan FROM fashionstore.planes WHERE nombre = 'Básico'")
    q("INSERT INTO fashionstore.suscripciones (id_tenant, id_plan, estado, fecha_inicio, fecha_vencimiento) "
      "VALUES (:t, :p, 'activa', current_date - 1, current_date + 30) RETURNING id_suscripcion", t=id_b, p=basico)
    ciudad = q("SELECT min(id_ciudad) FROM fashionstore.ciudades")
    for nombre in ("Sucursal B1", "Sucursal B2"):
        q("INSERT INTO fashionstore.sucursales (id_tenant, nombre, direccion, id_ciudad) "
          "VALUES (:t, :n, 'Calle de prueba 123', :c) RETURNING id_sucursal", t=id_b, n=nombre, c=ciudad)
    # Administrador de B, con contraseña conocida (para probar el login)
    admin_b = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo, id_tenant) "
                "VALUES ('admin@empresa-b.com', :h, 'Admin', 'B', 'administrador', true, :t) RETURNING id_usuario",
                h=hash_password(CLAVE_PRUEBA), t=id_b)
    q("INSERT INTO fashionstore.empleados (id_empleado, id_tenant, codigo_empleado, cargo, fecha_contratacion) "
      "VALUES (:u, :t, 'EMP-B-1', 'Administrador', current_date) RETURNING id_empleado", u=admin_b, t=id_b)
    _contexto(conexion)  # vuelve a «sin contexto» antes de las pruebas

    def get_db_prueba(request: Request):
        sesion = Session(bind=conexion, join_transaction_mode="create_savepoint")
        try:
            preparar_sesion(sesion, request.headers.get(CABECERA_TENANT), "fashionstore")
            yield sesion
        finally:
            sesion.close()

    app.dependency_overrides[get_db] = get_db_prueba
    try:
        yield {"conexion": conexion, "id_b": id_b, "admin_b": admin_b, "cliente": TestClient(app)}
    finally:
        app.dependency_overrides.clear()
        exterior.rollback()
        conexion.close()
        limpiar_cache_tenants()


def _falla(conexion, sql, **parametros):
    sp = conexion.begin_nested()
    try:
        conexion.execute(text(sql), parametros)
        sp.rollback()
        return None
    except DBAPIError as exc:
        sp.rollback()
        return str(exc.orig).splitlines()[0]


def _token(sub, rol, id_tenant):
    return {"Authorization": "Bearer " + create_access_token({"sub": str(sub), "rol": rol, "id_tenant": id_tenant})}


def _total(respuesta):
    """`total_registros` de una respuesta paginada (ProductoPaginadoOut), esté donde esté."""
    def buscar(nodo):
        if isinstance(nodo, dict):
            if "total_registros" in nodo:
                return nodo["total_registros"]
            for valor in nodo.values():
                encontrado = buscar(valor)
                if encontrado is not None:
                    return encontrado
        return None

    total = buscar(respuesta.json())
    assert total is not None, f"La respuesta no trae total_registros: {respuesta.text[:200]}"
    return total


# --------------------------------------------------------------------------------- base de datos (§A.5)

def test_sin_contexto_no_se_ve_ni_se_escribe_nada(mundo):
    c = mundo["conexion"]
    _contexto(c)
    assert c.execute(text("SELECT count(*) FROM fashionstore.productos")).scalar() == 0
    error = _falla(c, "INSERT INTO fashionstore.categorias (nombre) VALUES ('x-sin-contexto')")
    assert error and "row-level security" in error


def test_cada_empresa_solo_ve_lo_suyo_incluidas_las_vistas(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    assert c.execute(text("SELECT count(*) FROM fashionstore.productos")).scalar() == 0
    assert c.execute(text("SELECT count(*) FROM fashionstore.vw_ventas_por_sucursal")).scalar() == 0
    assert c.execute(text("SELECT count(*) FROM fashionstore.sucursales")).scalar() == 2
    _contexto(c, tenant=1)
    assert c.execute(text("SELECT count(*) FROM fashionstore.productos")).scalar() > 0
    assert c.execute(text("SELECT count(*) FROM fashionstore.sucursales WHERE nombre LIKE 'Sucursal B%'")).scalar() == 0


def test_la_base_impide_mezclar_empresas(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    error = _falla(c, "INSERT INTO fashionstore.categorias (nombre, id_tenant) VALUES ('Intrusa', 1)")
    assert error and "row-level security" in error
    temporada = c.execute(text(
        "INSERT INTO fashionstore.temporadas (nombre, fecha_inicio, fecha_fin) "
        "VALUES ('Temporada B', current_date, current_date + 90) RETURNING id_temporada")).scalar()
    sucursal = c.execute(text("SELECT min(id_sucursal) FROM fashionstore.sucursales")).scalar()
    variante_de_la_empresa_1 = 137
    error = _falla(c, "INSERT INTO fashionstore.inventario_sucursal (id_variante, id_sucursal, id_temporada, "
                      "cantidad_disponible, cantidad_reservada) VALUES (:v, :s, :t, 1, 0)",
                   v=variante_de_la_empresa_1, s=sucursal, t=temporada)
    assert error and "fk_inventario_sucursal_id_variante_tenant" in error


def test_nombres_unicos_por_empresa_y_valor_por_defecto_del_contexto(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    c.execute(text("INSERT INTO fashionstore.categorias (nombre) VALUES ('Pantalones')"))  # también existe en la 1
    assert c.execute(text("SELECT id_tenant FROM fashionstore.categorias WHERE nombre='Pantalones'")).scalar() == mundo["id_b"]
    error = _falla(c, "INSERT INTO fashionstore.categorias (nombre) VALUES ('Pantalones')")
    assert error and "categorias_tenant_nombre_key" in error


def test_un_cliente_solo_opera_donde_esta_registrado(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    error = _falla(c, "INSERT INTO fashionstore.carritos (id_cliente) VALUES (2)")  # cliente 2: solo en la empresa 1
    assert error and "fk_carritos_id_cliente_tenant" in error


# --------------------------------------------------------------------------------- API (§A.5)

def test_transicion_sin_token_ni_cabecera_ve_fashion_store(mundo):
    respuesta = mundo["cliente"].get("/api/v1/productos")
    assert respuesta.status_code == 200
    assert _total(respuesta) > 0


def test_la_cabecera_x_tenant_cambia_de_empresa(mundo):
    respuesta = mundo["cliente"].get("/api/v1/productos", headers={CABECERA_TENANT: "pruebas-b"})
    assert respuesta.status_code == 200
    assert _total(respuesta) == 0


def test_cabecera_de_empresa_inexistente_404(mundo):
    respuesta = mundo["cliente"].get("/api/v1/productos", headers={CABECERA_TENANT: "no-existe"})
    assert respuesta.status_code == 404
    assert respuesta.json()["code"] == "TENANT_NO_ENCONTRADO"


def test_token_y_cabecera_de_empresas_distintas_403(mundo):
    cabeceras = {**_token(14, "cajero", 1), CABECERA_TENANT: "pruebas-b"}
    respuesta = mundo["cliente"].get("/api/v1/pos/ventas", headers=cabeceras)
    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "TENANT_NO_COINCIDE"


def test_recurso_de_otra_empresa_responde_404(mundo):
    respuesta = mundo["cliente"].get("/api/v1/admin/sucursales/1", headers=_token(mundo["admin_b"], "administrador", mundo["id_b"]))
    assert respuesta.status_code == 404


def test_login_con_codigo_de_empresa(mundo):
    respuesta = mundo["cliente"].post("/api/v1/autenticacion/login", json={
        "email": "admin@empresa-b.com", "password": CLAVE_PRUEBA, "codigo_empresa": "pruebas-b",
    })
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["tenant"] == {"codigo": "pruebas-b", "nombre": "Empresa B"}
    from core.security import decode_access_token
    assert decode_access_token(cuerpo["access_token"])["id_tenant"] == mundo["id_b"]


def test_login_sin_codigo_no_encuentra_empleados_de_otra_empresa(mundo):
    respuesta = mundo["cliente"].post("/api/v1/autenticacion/login", json={
        "email": "admin@empresa-b.com", "password": CLAVE_PRUEBA,
    })
    assert respuesta.status_code == 401  # la empresa por defecto es fashionstore


# --------------------------------------------------------------------------------- P2-CU12

def _sesion_b(mundo):
    sesion = Session(bind=mundo["conexion"], join_transaction_mode="create_savepoint")
    sesion.info.update({"id_tenant": mundo["id_b"], "id_usuario": None, "modo_plataforma": False})
    return sesion


def test_cu12_limite_de_sucursales_del_plan_basico_por_la_api(mundo):
    respuesta = mundo["cliente"].post(
        "/api/v1/admin/sucursales",
        headers=_token(mundo["admin_b"], "administrador", mundo["id_b"]),
        json={"id_ciudad": 1, "nombre": "Sucursal B3", "direccion": "Calle de prueba 456"},
    )
    assert respuesta.status_code == 409, respuesta.text
    assert respuesta.json()["code"] == "LIMITE_PLAN_ALCANZADO"


def test_cu12_basico_no_incluye_reportes_con_ia(mundo):
    with pytest.raises(Exception) as error:
        SuscripcionServicio.validar(_sesion_b(mundo), funcionalidad="reportes_ia")
    assert getattr(error.value, "code", None) == "FUNCIONALIDAD_NO_INCLUIDA"


def test_cu12_suscripcion_vencida(mundo):
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    c.execute(text("UPDATE fashionstore.suscripciones SET fecha_inicio = current_date - 60, "
                   "fecha_vencimiento = current_date - 1 WHERE id_tenant = :t"), {"t": mundo["id_b"]})
    _contexto(c)
    with pytest.raises(Exception) as error:
        SuscripcionServicio.validar(_sesion_b(mundo), funcionalidad="reservas")
    assert getattr(error.value, "code", None) == "SUSCRIPCION_NO_VIGENTE"


def test_cu12_fashion_store_profesional_vigente(mundo):
    sesion = Session(bind=mundo["conexion"], join_transaction_mode="create_savepoint")
    sesion.info.update({"id_tenant": 1, "id_usuario": None, "modo_plataforma": False})
    SuscripcionServicio.validar(sesion, funcionalidad="reportes_ia", recurso="sucursales")


# --------------------------------------------------------------------------------- registro de clientes (D-B)

def test_un_cliente_no_registrado_en_la_empresa_no_puede_comprar(mundo):
    # El cliente 2 solo está registrado en FASHION STORE; su token apunta a la empresa B.
    respuesta = mundo["cliente"].get("/api/v1/carrito", headers=_token(2, "cliente", mundo["id_b"]))
    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "CLIENTE_NO_REGISTRADO"


def test_un_empleado_puede_usar_el_carrito_en_su_propia_empresa(mundo):
    # El encargado 13 no tenía ficha de cliente: se crea y se registra en su empresa (comportamiento previo).
    respuesta = mundo["cliente"].get("/api/v1/carrito", headers=_token(13, "encargado_sucursal", 1))
    assert respuesta.status_code == 200, respuesta.text
