"""Pruebas de integración de la fundación multitenant contra PostgreSQL real (RNF11).

Specs: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.5 (decisión F18) y
`.specs/finalized/P2-CU02-CU01-acceso-por-empresa/spec.md` §A.6 (requiere la migración 0015).

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
    # Zona de Bolivia, como la aplicación (`core.tenant`): sin ella `current_date` es la fecha UTC y,
    # entre las 20:00 y las 24:00 de Bolivia, «ayer» todavía es hoy para la aplicación.
    c.execute(
        text("SELECT set_config('app.id_tenant', :t, true), set_config('app.id_usuario', :u, true), "
             "set_config('app.modo_plataforma', :p, true), set_config('TimeZone', 'America/La_Paz', true)"),
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
            preparar_sesion(sesion, request.headers.get(CABECERA_TENANT))
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

def test_sin_token_ni_cabecera_no_se_ve_ninguna_empresa(mundo):
    # P2-CU02: ya no hay empresa por defecto
    respuesta = mundo["cliente"].get("/api/v1/productos")
    assert respuesta.status_code == 200
    assert _total(respuesta) == 0


def test_el_portal_de_fashion_store_ve_su_catalogo(mundo):
    respuesta = mundo["cliente"].get("/api/v1/productos", headers={CABECERA_TENANT: "fashionstore"})
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


def test_login_de_empleado_solo_con_correo_y_contrasena(mundo):
    # P2-CU02 A1: la cuenta determina la empresa, aunque el login llegue desde otro portal
    respuesta = mundo["cliente"].post(
        "/api/v1/autenticacion/login",
        json={"email": "admin@empresa-b.com", "password": CLAVE_PRUEBA},
        headers={CABECERA_TENANT: "fashionstore"},
    )
    assert respuesta.status_code == 200, respuesta.text
    cuerpo = respuesta.json()
    assert cuerpo["tenant"] == {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "BOB"}
    assert cuerpo["empresas"] == []
    from core.security import decode_access_token
    assert decode_access_token(cuerpo["access_token"])["id_tenant"] == mundo["id_b"]


def test_login_de_empleado_con_suscripcion_vencida_403(mundo):
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    c.execute(text("UPDATE fashionstore.suscripciones SET fecha_inicio = current_date - 60, "
                   "fecha_vencimiento = current_date - 1 WHERE id_tenant = :t"), {"t": mundo["id_b"]})
    _contexto(c)
    respuesta = mundo["cliente"].post("/api/v1/autenticacion/login", json={
        "email": "admin@empresa-b.com", "password": CLAVE_PRUEBA,
    })
    assert respuesta.status_code == 403
    assert respuesta.json()["code"] == "SUSCRIPCION_NO_VIGENTE"


def test_login_con_correo_inexistente_401(mundo):
    respuesta = mundo["cliente"].post("/api/v1/autenticacion/login", json={
        "email": "nadie@empresa-b.com", "password": CLAVE_PRUEBA,
    })
    assert respuesta.status_code == 401
    assert respuesta.json()["code"] == "CREDENCIALES_INVALIDAS"


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


# --------------------------------------------------------------------------------- P2-CU02 (0015)

def test_cuenta_por_email_encuentra_empleados_de_cualquier_empresa_sin_contexto(mundo):
    c = mundo["conexion"]
    _contexto(c)
    resultado = c.execute(text("SELECT * FROM fashionstore.cuenta_por_email('ADMIN@empresa-b.com')"))
    assert list(resultado.keys()) == ["id_usuario", "id_tenant"]  # solo dos columnas (A11)
    assert resultado.all() == [(mundo["admin_b"], mundo["id_b"])]


def test_el_correo_es_unico_en_toda_la_plataforma(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=1)
    error = _falla(c, "INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo, id_tenant) "
                      "VALUES ('Admin@Empresa-B.com', 'x', 'Otro', 'Admin', 'cajero', true, 1)")
    assert error and "uq_usuarios_email" in error


def test_empresas_disponibles_excluye_las_suspendidas(mundo):
    c = mundo["conexion"]
    _contexto(c)
    codigos = lambda: {f[0] for f in c.execute(text("SELECT codigo FROM fashionstore.empresas_disponibles()"))}
    assert {"fashionstore", "pruebas-b"} <= codigos()
    _contexto(c, plataforma=True)
    c.execute(text("UPDATE fashionstore.tenants SET estado = 'suspendida' WHERE id_tenant = :t"), {"t": mundo["id_b"]})
    _contexto(c)
    assert "pruebas-b" not in codigos()


def test_codigo_de_empresa_reservado(mundo):
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    error = _falla(c, "INSERT INTO fashionstore.tenants (codigo, nombre) VALUES ('admin', 'Intrusa')")
    assert error and "chk_tenants_codigo_reservado" in error


def test_directorio_y_portal(mundo):
    cliente = mundo["cliente"]
    directorio = cliente.get("/api/v1/tenants")
    assert directorio.status_code == 200
    assert {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "BOB"} in directorio.json()
    assert cliente.get("/api/v1/tenants/pruebas-b").json() == {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "BOB"}
    assert cliente.get("/api/v1/tenants/no-existe").status_code == 404


def test_flujo_del_cliente_entre_dos_tiendas(mundo):
    cliente = mundo["cliente"]
    datos = {"email": "clienta.p2cu02@ejemplo.com", "password": CLAVE_PRUEBA, "nombres": "Clienta", "apellidos": "Prueba"}

    # Registro desde el portal de FASHION STORE: cuenta global registrada en esa tienda
    registro = cliente.post("/api/v1/autenticacion/registrarse", json=datos, headers={CABECERA_TENANT: "fashionstore"})
    assert registro.status_code == 201, registro.text
    from core.security import decode_access_token
    assert decode_access_token(registro.json()["token_acceso"])["id_tenant"] is None  # A10

    # Correo repetido → 409, también si es el de un empleado de otra empresa
    repetido = cliente.post("/api/v1/autenticacion/registrarse", json={**datos, "email": "admin@empresa-b.com"})
    assert repetido.status_code == 409

    login = cliente.post("/api/v1/autenticacion/login", json={"email": datos["email"], "password": CLAVE_PRUEBA})
    assert login.status_code == 200, login.text
    assert login.json()["tenant"] is None
    assert login.json()["empresas"] == [{"codigo": "fashionstore", "nombre": "FASHION STORE", "moneda": "BOB"}]
    auth = {"Authorization": "Bearer " + login.json()["access_token"]}

    # En la tienda B todavía no puede comprar
    carrito_b = cliente.get("/api/v1/carrito", headers={**auth, CABECERA_TENANT: "pruebas-b"})
    assert carrito_b.status_code == 403
    assert carrito_b.json()["code"] == "CLIENTE_NO_REGISTRADO"

    # «Registrarme en esta tienda» (idempotente)
    alta = cliente.post("/api/v1/mis-empresas", headers={**auth, CABECERA_TENANT: "pruebas-b"})
    assert alta.status_code == 201, alta.text
    assert alta.json() == {"empresa": {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "BOB"}, "registrado_ahora": True}
    otra_vez = cliente.post("/api/v1/mis-empresas", headers={**auth, CABECERA_TENANT: "pruebas-b"})
    assert otra_vez.status_code == 200
    assert otra_vez.json()["registrado_ahora"] is False

    mias = cliente.get("/api/v1/mis-empresas", headers=auth)
    assert {e["codigo"] for e in mias.json()} == {"fashionstore", "pruebas-b"}

    # Ya puede usar el carrito en B con el mismo token (cambio de tienda sin contraseña, CU02 A7)
    assert cliente.get("/api/v1/carrito", headers={**auth, CABECERA_TENANT: "pruebas-b"}).status_code == 200
    assert cliente.get("/api/v1/carrito", headers={**auth, CABECERA_TENANT: "fashionstore"}).status_code == 200


def test_registrarse_en_tienda_sin_cabecera_y_como_empleado(mundo):
    cliente = mundo["cliente"]
    sin_tienda = cliente.post("/api/v1/mis-empresas", headers=_token(2, "cliente", None))
    assert sin_tienda.status_code == 400
    assert sin_tienda.json()["code"] == "TENANT_REQUERIDO"
    empleado = cliente.post("/api/v1/mis-empresas", headers={**_token(14, "cajero", 1), CABECERA_TENANT: "fashionstore"})
    assert empleado.status_code == 403
    assert empleado.json()["code"] == "SOLO_CLIENTES"


def test_alta_de_empleado_queda_en_la_empresa_del_administrador(mundo):
    # A9 / CU20: la cuenta del empleado toma la empresa del administrador que la crea
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    sucursal_b = c.execute(text("SELECT min(id_sucursal) FROM fashionstore.sucursales")).scalar()
    _contexto(c)
    respuesta = mundo["cliente"].post(
        "/api/v1/admin/usuarios",
        headers=_token(mundo["admin_b"], "administrador", mundo["id_b"]),
        json={"email": "cajero.b@empresa-b.com", "password": CLAVE_PRUEBA, "nombres": "Cajero",
              "apellidos": "Prueba", "rol": "cajero", "id_sucursal": sucursal_b},
    )
    assert respuesta.status_code == 201, respuesta.text
    _contexto(c)
    empresa = c.execute(text("SELECT id_tenant FROM fashionstore.cuenta_por_email('cajero.b@empresa-b.com')")).scalar()
    assert empresa == mundo["id_b"]

    # El mismo correo, otra vez → 409
    repetido = mundo["cliente"].post(
        "/api/v1/admin/usuarios",
        headers=_token(mundo["admin_b"], "administrador", mundo["id_b"]),
        json={"email": "cajero.b@empresa-b.com", "password": CLAVE_PRUEBA, "nombres": "Otro",
              "apellidos": "Cajero", "rol": "cajero", "id_sucursal": sucursal_b},
    )
    assert repetido.status_code == 409


# --------------------------------------------------------------------------------- P2-CU03 · P2-CU04

def _sucursales(mundo, tenant):
    c = mundo["conexion"]
    _contexto(c, tenant=tenant)
    ids = [f[0] for f in c.execute(text("SELECT id_sucursal FROM fashionstore.sucursales ORDER BY id_sucursal"))]
    _contexto(c)
    return ids


def test_p2_cu03_b1_el_administrador_no_ve_ni_toca_cuentas_sin_empresa(mundo):
    """Defecto de fuga: la RLS de `usuarios` deja leer clientes y super administrador a cualquier empresa."""
    cliente, admin = mundo["cliente"], _token(mundo["admin_b"], "administrador", mundo["id_b"])
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    ajenos = [f[0] for f in c.execute(text(
        "SELECT id_usuario FROM fashionstore.usuarios WHERE id_tenant IS NULL ORDER BY id_usuario LIMIT 3"))]
    _contexto(c)
    assert ajenos, "La rama de pruebas debería tener clientes"

    listado = cliente.get("/api/v1/admin/usuarios?limite=100", headers=admin)
    assert listado.status_code == 200, listado.text
    assert {u["id_usuario"] for u in listado.json()["items"]} == {mundo["admin_b"]}
    assert listado.json()["total"] == 1
    assert cliente.get("/api/v1/admin/usuarios?rol=cliente", headers=admin).json()["total"] == 0

    for id_ajeno in ajenos:
        assert cliente.get(f"/api/v1/admin/usuarios/{id_ajeno}", headers=admin).status_code == 404
        reset = cliente.post(f"/api/v1/admin/usuarios/{id_ajeno}/reset-password", headers=admin,
                             json={"nuevo_password": "Intrusa2026!"})
        assert reset.status_code == 404
        assert cliente.patch(f"/api/v1/admin/usuarios/{id_ajeno}/estado", headers=admin,
                             json={"activo": False}).status_code == 404


def test_p2_cu03_b3_empleado_con_dos_sucursales(mundo):
    from modules.autenticacion_seguridad.modelos import UsuarioORM
    from modules.plataforma.servicio_sucursales_empleado import SucursalesEmpleadoServicio

    cliente, admin = mundo["cliente"], _token(mundo["admin_b"], "administrador", mundo["id_b"])
    b1, b2 = _sucursales(mundo, mundo["id_b"])
    ajena = _sucursales(mundo, 1)[0]

    # Una sucursal de otra empresa no existe para B (RLS)
    intruso = cliente.post("/api/v1/admin/usuarios", headers=admin, json={
        "email": "cajera.intrusa@empresa-b.com", "password": CLAVE_PRUEBA, "nombres": "Cajera", "apellidos": "Intrusa",
        "rol": "cajero", "sucursales_autorizadas": [b1, ajena], "id_sucursal_principal": b1})
    assert intruso.status_code == 422, intruso.text
    assert intruso.json()["code"] == "SUCURSAL_INEXISTENTE_O_INACTIVA"

    alta = cliente.post("/api/v1/admin/usuarios", headers=admin, json={
        "email": "cajera.dos@empresa-b.com", "password": CLAVE_PRUEBA, "nombres": "Cajera", "apellidos": "Dos",
        "rol": "cajero", "sucursales_autorizadas": [b1, b2], "id_sucursal_principal": b2})
    assert alta.status_code == 201, alta.text
    cuerpo = alta.json()
    assert cuerpo["id_sucursal"] == b2
    assert {(s["id_sucursal"], s["es_principal"]) for s in cuerpo["sucursales_autorizadas"]} == {(b1, False), (b2, True)}
    id_cajera = cuerpo["id_usuario"]

    # RN07 leído de `empleado_sucursal` con la sesión real
    sesion = _sesion_b(mundo)
    cajera = sesion.get(UsuarioORM, id_cajera)
    assert SucursalesEmpleadoServicio.autorizadas(cajera) == frozenset({b1, b2})
    assert not SucursalesEmpleadoServicio.autoriza(cajera, ajena)

    mias = cliente.get("/api/v1/mis-sucursales", headers=_token(id_cajera, "cajero", mundo["id_b"]))
    assert mias.status_code == 200, mias.text
    assert [(s["id_sucursal"], s["es_principal"]) for s in mias.json()] == [(b2, True), (b1, False)]

    # Editar: queda solo b1 (la principal pasa a ser la única)
    edicion = cliente.put(f"/api/v1/admin/usuarios/{id_cajera}", headers=admin, json={"sucursales_autorizadas": [b1]})
    assert edicion.status_code == 200, edicion.text
    assert edicion.json()["id_sucursal"] == b1
    assert [s["id_sucursal"] for s in edicion.json()["sucursales_autorizadas"]] == [b1]


def test_p2_cu04_b7_uso_del_plan(mundo):
    uso = mundo["cliente"].get("/api/v1/admin/sucursales/uso-plan",
                               headers=_token(mundo["admin_b"], "administrador", mundo["id_b"]))
    assert uso.status_code == 200, uso.text
    assert uso.json() == {"uso": 2, "limite": 2, "plan": "Básico"}


def test_p2_cu04_b8_el_limite_se_serializa_por_empresa(mundo, motor):
    """Mientras una operación de la empresa B valida su límite de sucursales, otra conexión no puede
    tomar el mismo bloqueo (esperaría), pero sí el de otra empresa o el de otro recurso."""
    from modules.plataforma.cu12_validar_suscripcion.repositorio import SuscripcionRepositorio

    sesion = _sesion_b(mundo)
    SuscripcionRepositorio.bloquear_recurso(sesion, mundo["id_b"], "sucursales")
    probar = "SELECT pg_try_advisory_xact_lock(hashtext(:clave), :t)"
    with motor.connect() as otra:
        with otra.begin():
            assert otra.execute(text(probar), {"clave": "fashionstore.limite.sucursales", "t": mundo["id_b"]}).scalar() is False
            assert otra.execute(text(probar), {"clave": "fashionstore.limite.sucursales", "t": 1}).scalar() is True
            assert otra.execute(text(probar), {"clave": "fashionstore.limite.empleados", "t": mundo["id_b"]}).scalar() is True


def test_p2_cu04_b6_ciudades_de_solo_lectura(mundo):
    admin = _token(mundo["admin_b"], "administrador", mundo["id_b"])
    assert mundo["cliente"].get("/api/v1/admin/ciudades", headers=admin).status_code == 200
    alta = mundo["cliente"].post("/api/v1/admin/ciudades", headers=admin, json={"nombre": "Ciudad Intrusa", "pais": "X"})
    assert alta.status_code == 405


# --------------------------------------------------------------------------------- P2-CU11

def test_p2_cu11_cada_empresa_configura_lo_suyo(mundo):
    cliente, admin_b = mundo["cliente"], _token(mundo["admin_b"], "administrador", mundo["id_b"])

    # La empresa B no tenía fila: se crea con los valores por defecto al leerla (C4)
    lectura = cliente.get("/api/v1/admin/configuracion", headers=admin_b)
    assert lectura.status_code == 200, lectura.text
    assert lectura.json()["horas_vencimiento_reserva"] == 24

    cambio = cliente.put("/api/v1/admin/configuracion", headers=admin_b, json={
        "moneda": "BOB", "zona_horaria": "America/La_Paz",
        "horas_vencimiento_reserva": 48, "dias_cambio_prenda": 30,
        "operacion_offline_habilitada": False, "dias_antiguedad_offline": 7})
    assert cambio.status_code == 200, cambio.text
    assert cambio.json()["horas_vencimiento_reserva"] == 48

    # FASHION STORE conserva los suyos (RLS)
    c = mundo["conexion"]
    _contexto(c, tenant=1)
    fs = c.execute(text("SELECT horas_vencimiento_reserva, operacion_offline_habilitada "
                        "FROM fashionstore.configuracion_tenant")).all()
    _contexto(c)
    assert fs == [(24, True)]


def test_p2_cu11_la_base_rechaza_valores_invalidos(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=1)
    error = _falla(c, "UPDATE fashionstore.configuracion_tenant SET horas_vencimiento_reserva = 0")
    _contexto(c)
    assert error and "chk_config_horas_reserva" in error


# --------------------------------------------------------------------------------- Fix P2-CU11 (0016)

CONFIG_BASE = {"zona_horaria": "America/La_Paz", "horas_vencimiento_reserva": 24, "dias_cambio_prenda": 15,
               "operacion_offline_habilitada": True, "dias_antiguedad_offline": 7}


def test_fix_cu11_la_sesion_trabaja_en_hora_de_bolivia(mundo):
    from core.tiempo import hoy

    sesion = _sesion_b(mundo)
    zona, fecha = sesion.execute(text("SELECT current_setting('TimeZone'), current_date")).one()
    assert zona == "America/La_Paz"
    assert fecha == hoy()


def test_fix_cu11_0016_monedas_y_zona(mundo):
    c = mundo["conexion"]
    _contexto(c, tenant=1)
    assert c.execute(text("SELECT moneda, zona_horaria FROM fashionstore.configuracion_tenant")).one() == (
        "BOB", "America/La_Paz")
    assert "chk_config_moneda" in (_falla(c, "UPDATE fashionstore.configuracion_tenant SET moneda = 'EUR'") or "")
    assert "chk_config_zona" in (
        _falla(c, "UPDATE fashionstore.configuracion_tenant SET zona_horaria = 'Europe/Madrid'") or "")
    _contexto(c)
    monedas = {f[0]: f[1] for f in c.execute(text("SELECT codigo, moneda FROM fashionstore.empresas_disponibles()"))}
    assert monedas["fashionstore"] == "BOB"


def test_fix_cu11_moneda_bloqueada_con_ventas_y_libre_sin_ellas(mundo):
    cliente = mundo["cliente"]

    # FASHION STORE tiene ventas: no puede cambiar de moneda (M3)
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    admin_fs = c.execute(text("SELECT id_usuario FROM fashionstore.usuarios WHERE id_tenant = 1 "
                              "AND rol = 'administrador' AND activo ORDER BY id_usuario LIMIT 1")).scalar()
    ventas_fs = c.execute(text("SELECT count(*) FROM fashionstore.ventas WHERE id_tenant = 1")).scalar()
    _contexto(c)
    assert admin_fs and ventas_fs, "La rama de pruebas debería tener un administrador y ventas de FASHION STORE"
    fs = _token(admin_fs, "administrador", 1)
    assert cliente.get("/api/v1/admin/configuracion", headers=fs).json()["moneda_bloqueada"] is True
    bloqueo = cliente.put("/api/v1/admin/configuracion", headers=fs, json={**CONFIG_BASE, "moneda": "USD"})
    assert bloqueo.status_code == 409, bloqueo.text
    assert bloqueo.json()["code"] == "MONEDA_CON_OPERACIONES"

    # La empresa B no tiene ventas: pasa a USD y el directorio y el login lo reflejan (M6)
    admin_b = _token(mundo["admin_b"], "administrador", mundo["id_b"])
    cambio = cliente.put("/api/v1/admin/configuracion", headers=admin_b, json={**CONFIG_BASE, "moneda": "USD"})
    assert cambio.status_code == 200, cambio.text
    assert {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "USD"} in cliente.get("/api/v1/tenants").json()
    login = cliente.post("/api/v1/autenticacion/login", json={"email": "admin@empresa-b.com", "password": CLAVE_PRUEBA})
    assert login.status_code == 200, login.text
    assert login.json()["tenant"]["moneda"] == "USD"


# --------------------------------------------------------------------------------- RF15 (Menshopping)

def test_rf15_carga_de_menshopping_aislada_de_fashion_store(mundo):
    """La carga completa dentro de la transacción de la rama de pruebas (se deshace al final)."""
    from datetime import date

    from argon2 import PasswordHasher

    from scripts import cargar_menshopping as carga

    c = mundo["conexion"]
    # Código y correos propios: la prueba no choca con el Menshopping ya cargado en la rama de pruebas
    datos = carga.cargar_datos()
    datos["empresa"].update(codigo="rf15-prueba", nombre="RF15 Prueba", correo_contacto="admin@rf15-prueba.com")
    for usuario in datos["usuarios"]:
        usuario["email"] = usuario["email"].replace("@menshopping.com", "@rf15-prueba.com")
    imagenes = carga.Imagenes(
        vestidor={p["codigo"]: f"/ar/{p['imagen_vestidor']}" for p in datos["prendas"]},
        catalogo={p["codigo"]: f"/ar/{p['imagen_vestidor']}" for p in datos["prendas"]},
    )
    resumen = carga.cargar(c, datos, PasswordHasher().hash(CLAVE_PRUEBA), imagenes, date(2026, 11, 9))
    t = resumen["id_tenant"]
    assert {k: v for k, v in resumen.items() if k != "id_tenant"} == {
        "sucursales": 2, "categorias": 4, "usuarios": 5,
        "productos": 4, "variantes": 8, "inventario": 16, "movimientos": 16,
    }

    _contexto(c, tenant=t)
    stock = dict(c.execute(text(
        "SELECT s.nombre, sum(i.cantidad_disponible) FROM fashionstore.inventario_sucursal i "
        "JOIN fashionstore.sucursales s ON s.id_sucursal = i.id_sucursal GROUP BY s.nombre")).all())
    assert stock == {"Menshopping Santa Cruz": 40, "Menshopping Beni": 16}  # 4 prendas × (5+5) y × (2+2)
    nombres_ms = {f[0] for f in c.execute(text("SELECT nombre FROM fashionstore.productos"))}
    assert nombres_ms == {p["nombre"] for p in datos["prendas"]}

    # FASHION STORE no ve nada de Menshopping, y al revés (RLS)
    _contexto(c, tenant=1)
    assert c.execute(text("SELECT count(*) FROM fashionstore.productos WHERE nombre = ANY(:n)"),
                     {"n": list(nombres_ms)}).scalar() == 0
    assert c.execute(text("SELECT count(*) FROM fashionstore.sucursales WHERE nombre LIKE 'Menshopping%'")).scalar() == 0
    _contexto(c)

    # El directorio la lista en BOB y su administrador entra con su empresa
    cliente = mundo["cliente"]
    assert {"codigo": "rf15-prueba", "nombre": "RF15 Prueba", "moneda": "BOB"} in cliente.get("/api/v1/tenants").json()
    login = cliente.post("/api/v1/autenticacion/login", json={"email": "admin@rf15-prueba.com", "password": CLAVE_PRUEBA})
    assert login.status_code == 200, login.text
    assert login.json()["tenant"] == {"codigo": "rf15-prueba", "nombre": "RF15 Prueba", "moneda": "BOB"}
    catalogo = cliente.get("/api/v1/productos?pagina=1", headers={CABECERA_TENANT: "rf15-prueba"})
    assert _total(catalogo) == 4

    # Una segunda carga se detiene sin tocar nada (R5)
    with pytest.raises(carga.CargaError, match="ya existe"):
        carga.cargar(c, datos, "x", imagenes, date(2026, 11, 9))


# --------------------------------------------------------------------------------- Tablas nuevas Parcial 2 (CU21–CU25, CU09–CU10)

def test_aislamiento_multitenant_tablas_nuevas_ia_ml_suscripcion(mundo):
    """Verifica que las tablas de CU21-CU25 y CU09-CU10 respetan RLS entre FASHION STORE y Empresa B."""
    c = mundo["conexion"]
    id_b = mundo["id_b"]

    # 1. solicitudes_reporte_ia
    _contexto(c, tenant=1)
    admin_fs = c.execute(text(
        "SELECT id_usuario FROM fashionstore.usuarios WHERE id_tenant = 1 AND rol = 'administrador' LIMIT 1"
    )).scalar()
    if admin_fs:
        c.execute(text(
            "INSERT INTO fashionstore.solicitudes_reporte_ia "
            "(id_tenant, id_usuario, comando_voz_texto, tipo_reporte, estado) "
            "VALUES (1, :u, 'ventas del mes', 'ventas_por_sucursal', 'completada')"
        ), {"u": admin_fs})
        assert c.execute(text("SELECT count(*) FROM fashionstore.solicitudes_reporte_ia")).scalar() >= 1

        _contexto(c, tenant=id_b)
        assert c.execute(text("SELECT count(*) FROM fashionstore.solicitudes_reporte_ia")).scalar() == 0

    # 2. datasets_ml, modelos_ml, predicciones_ml y segmentos_clientes_ml (CU23–CU25)
    tablas_ml_existen = c.execute(text(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'fashionstore' AND table_name = 'datasets_ml'"
    )).scalar() > 0

    if tablas_ml_existen:
        _contexto(c, tenant=1)
        # Columnas de la migración 0019 (las anteriores de esta prueba no existían en el esquema)
        id_ds = c.execute(text(
            "INSERT INTO fashionstore.datasets_ml (id_tenant, nombre, origen, cantidad_registros) "
            "VALUES (1, 'Demanda de prueba', 'sintetico', 10) RETURNING id_dataset"
        )).scalar()
        id_mod = c.execute(text(
            "INSERT INTO fashionstore.modelos_ml "
            "(id_tenant, id_dataset, nombre, tipo_modelo, algoritmo, origen_datos, estado, activo) "
            "VALUES (1, :ds, 'Modelo de prueba', 'supervisado', 'random_forest', 'sintetico', 'activo', true) "
            "RETURNING id_modelo"
        ), {"ds": id_ds}).scalar()
        c.execute(text(
            "INSERT INTO fashionstore.predicciones_ml "
            "(id_tenant, id_modelo, nombre_producto, nombre_sucursal, periodo) "
            "VALUES (1, :m, 'Producto', 'Sucursal', '2026-12')"
        ), {"m": id_mod})
        c.execute(text(
            "INSERT INTO fashionstore.segmentos_clientes_ml "
            "(id_tenant, id_modelo, codigo_grupo, nombre_grupo, descripcion) "
            "VALUES (1, :m, 'G1', 'Grupo 1', 'Grupo de prueba')"
        ), {"m": id_mod})

        assert c.execute(text("SELECT count(*) FROM fashionstore.datasets_ml")).scalar() >= 1
        assert c.execute(text("SELECT count(*) FROM fashionstore.modelos_ml")).scalar() >= 1
        assert c.execute(text("SELECT count(*) FROM fashionstore.predicciones_ml")).scalar() >= 1
        assert c.execute(text("SELECT count(*) FROM fashionstore.segmentos_clientes_ml")).scalar() >= 1

        _contexto(c, tenant=id_b)
        assert c.execute(text("SELECT count(*) FROM fashionstore.datasets_ml")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM fashionstore.modelos_ml")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM fashionstore.predicciones_ml")).scalar() == 0
        assert c.execute(text("SELECT count(*) FROM fashionstore.segmentos_clientes_ml")).scalar() == 0

        _contexto(c, plataforma=True)
        assert c.execute(text("SELECT count(*) FROM fashionstore.datasets_ml")).scalar() >= 1

    # 3. catalogo_reportes_ia (CU22): catálogo global visible por todos los tenants
    cat_existe = c.execute(text(
        "SELECT count(*) FROM information_schema.tables "
        "WHERE table_schema = 'fashionstore' AND table_name = 'catalogo_reportes_ia'"
    )).scalar() > 0

    if cat_existe:
        _contexto(c, tenant=id_b)
        total_cat = c.execute(text("SELECT count(*) FROM fashionstore.catalogo_reportes_ia WHERE activo = true")).scalar()
        assert total_cat >= 4

    # 4. historial_suscripcion (CU07/CU10)
    _contexto(c, tenant=1)
    susc_1 = c.execute(text("SELECT id_suscripcion FROM fashionstore.suscripciones WHERE id_tenant = 1 LIMIT 1")).scalar()
    if susc_1:
        c.execute(text(
            "INSERT INTO fashionstore.historial_suscripcion (id_tenant, id_suscripcion, evento, detalle) "
            "VALUES (1, :s, 'cambio_plan', '{\"motivo\": \"test\"}'::jsonb)"
        ), {"s": susc_1})
        assert c.execute(text("SELECT count(*) FROM fashionstore.historial_suscripcion WHERE id_tenant = 1")).scalar() >= 1

        _contexto(c, tenant=id_b)
        assert c.execute(text("SELECT count(*) FROM fashionstore.historial_suscripcion WHERE id_tenant = 1")).scalar() == 0



# --------------------------------------------------------------------------------- P2-CU14, CU15, CU19 y CU20 (0020)
# Spec: `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/plan.md` §9.

import threading
import uuid as _uuid
from datetime import datetime as _dt, timedelta as _td, timezone as _tz


def _catalogo_b(mundo, unidades=2):
    """Prenda, inventario y un cliente registrado en la empresa B (dentro de la transacción de la prueba)."""
    c = mundo["conexion"]
    t = mundo["id_b"]
    _contexto(c, plataforma=True)
    q = lambda sql, **p: c.execute(text(sql), p).scalar()
    s1, s2 = c.execute(text("SELECT id_sucursal FROM fashionstore.sucursales WHERE id_tenant = :t ORDER BY id_sucursal"),
                       {"t": t}).scalars().all()
    cat = q("INSERT INTO fashionstore.categorias (id_tenant, nombre) VALUES (:t, 'Camisas B') RETURNING id_categoria", t=t)
    temp = q("INSERT INTO fashionstore.temporadas (id_tenant, nombre, fecha_inicio, fecha_fin) "
             "VALUES (:t, 'Temporada sync', current_date, current_date + 90) RETURNING id_temporada", t=t)
    prod = q("INSERT INTO fashionstore.productos (id_tenant, id_categoria, nombre, precio_base) "
             "VALUES (:t, :c, 'Camisa B', 100) RETURNING id_producto", t=t, c=cat)
    var = q("INSERT INTO fashionstore.variantes_producto (id_tenant, id_producto, id_talla, id_color, sku) "
            "VALUES (:t, :p, (SELECT min(id_talla) FROM fashionstore.tallas), (SELECT min(id_color) FROM fashionstore.colores), "
            "'SYNC-B-1') RETURNING id_variante", t=t, p=prod)
    inv = q("INSERT INTO fashionstore.inventario_sucursal (id_tenant, id_variante, id_sucursal, id_temporada, cantidad_disponible) "
            "VALUES (:t, :v, :s, :temp, :n) RETURNING id_inventario", t=t, v=var, s=s1, temp=temp, n=unidades)
    cliente = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo) "
                "VALUES ('cliente.sync@ejemplo.com', :h, 'Cliente', 'Sync', 'cliente', true) RETURNING id_usuario",
                h=hash_password(CLAVE_PRUEBA))
    q("INSERT INTO fashionstore.clientes (id_cliente) VALUES (:c) RETURNING id_cliente", c=cliente)
    q("INSERT INTO fashionstore.cliente_tenant (id_tenant, id_cliente) VALUES (:t, :c) RETURNING id_cliente", t=t, c=cliente)
    sucursal_fs = q("SELECT min(id_sucursal) FROM fashionstore.sucursales WHERE id_tenant = 1")
    _contexto(c)
    return {"s1": s1, "s2": s2, "producto": prod, "variante": var, "inventario": inv, "cliente": cliente,
            "sucursal_fs": sucursal_fs,
            "auth": {**_token(cliente, "cliente", None), CABECERA_TENANT: "pruebas-b"}}


def _op_reserva(id_sucursal, id_variante, cantidad=1, provisional="PROV-AAAA-000001", **cambios):
    ahora = _dt.now(_tz.utc)
    op = {
        "uuid": str(_uuid.uuid4()), "tipo": "reserva", "id_sucursal": id_sucursal,
        "registrada_en": (ahora - _td(minutes=30)).isoformat(), "codigo_provisional": provisional,
        "datos": {"fecha_hora_atencion": (ahora + _td(hours=3)).isoformat(),
                  "items": [{"id_variante": id_variante, "cantidad": cantidad}]},
    }
    op.update(cambios)
    return op


def _fila(c, sql, **p):
    _contexto(c, plataforma=True)
    try:
        return c.execute(text(sql), p).one()
    finally:
        _contexto(c)


def test_p2_cu14_cu19_flujo_del_cliente_sin_conexion(mundo):
    d = _catalogo_b(mundo)
    api, c = mundo["cliente"], mundo["conexion"]
    disp = str(_uuid.uuid4())

    # CU14: alta (201) y reutilización (200, A1)
    alta = api.post("/api/v1/sin-conexion/dispositivos", json={"identificador": disp, "plataforma": "pwa"}, headers=d["auth"])
    assert alta.status_code == 201, alta.text
    assert alta.json()["codigo_corto"] == disp[:4].upper()
    assert alta.json()["horas_vencimiento_reserva"] == 24
    assert api.post("/api/v1/sin-conexion/dispositivos", json={"identificador": disp, "plataforma": "pwa"},
                    headers=d["auth"]).status_code == 200

    # CU14: el paquete trae solo lo de la empresa B (RLS)
    paquete = api.get(f"/api/v1/sin-conexion/catalogo?dispositivo={disp}", headers=d["auth"])
    assert paquete.status_code == 200, paquete.text
    cuerpo = paquete.json()
    assert [p["id_producto"] for p in cuerpo["productos"]] == [d["producto"]]
    assert {s["id_sucursal"] for s in cuerpo["sucursales"]} == {d["s1"], d["s2"]}
    assert {"id_variante": d["variante"], "id_sucursal": d["s1"], "cantidad_disponible": 2} in cuerpo["existencias"]
    assert cuerpo["productos"][0]["precio_base"] == "100.00"

    # El cliente no registrado en FASHION STORE no registra dispositivos allí
    ajeno = api.post("/api/v1/sin-conexion/dispositivos", json={"identificador": str(_uuid.uuid4()), "plataforma": "pwa"},
                     headers={**d["auth"], CABECERA_TENANT: "fashionstore"})
    assert ajeno.status_code == 403 and ajeno.json()["code"] == "CLIENTE_NO_REGISTRADO"

    # CU19: confirmada, sin stock (rechazada con aviso) y sucursal de otra empresa (PI-14)
    ops = [
        _op_reserva(d["s1"], d["variante"], 1, "PROV-AAAA-000001"),
        _op_reserva(d["s1"], d["variante"], 2, "PROV-AAAA-000002"),
        _op_reserva(d["sucursal_fs"], d["variante"], 1, "PROV-AAAA-000003"),
    ]
    lote = api.post("/api/v1/sin-conexion/sincronizar", json={"dispositivo": disp, "operaciones": ops}, headers=d["auth"])
    assert lote.status_code == 200, lote.text
    estados = [(r["estado"], r["motivo"]) for r in lote.json()["resultados"]]
    assert estados == [("confirmada", None), ("rechazada", "STOCK_INSUFICIENTE"), ("rechazada", "SUCURSAL_INACTIVA")]
    assert lote.json()["resultados"][0]["codigo_reserva"].startswith("RES-")

    # La reserva guarda su vencimiento (RN25: 24 h por defecto) y el código provisional
    horas, provisional = _fila(c, "SELECT extract(epoch FROM vence_en - creado_en) / 3600, codigo_provisional "
                                  "FROM fashionstore.reservas WHERE id_reserva = :r",
                               r=lote.json()["resultados"][0]["id_reserva"])
    assert (round(horas), provisional) == (24, "PROV-AAAA-000001")
    assert tuple(_fila(c, "SELECT cantidad_disponible, cantidad_reservada FROM fashionstore.inventario_sucursal "
                          "WHERE id_inventario = :i", i=d["inventario"])) == (1, 1)

    # Reenviar el lote no duplica nada (RN35)
    otra_vez = api.post("/api/v1/sin-conexion/sincronizar", json={"dispositivo": disp, "operaciones": ops}, headers=d["auth"])
    assert [r["repetida"] for r in otra_vez.json()["resultados"]] == [True, True, True]
    assert otra_vez.json()["resultados"][0]["codigo_reserva"] == lote.json()["resultados"][0]["codigo_reserva"]
    assert tuple(_fila(c, "SELECT cantidad_disponible, cantidad_reservada FROM fashionstore.inventario_sucursal "
                          "WHERE id_inventario = :i", i=d["inventario"])) == (1, 1)

    # Bandeja: un aviso por cada reserva rechazada
    bandeja = api.get("/api/v1/avisos", headers=d["auth"]).json()
    assert bandeja["no_leidos"] == 2 and {a["tipo"] for a in bandeja["avisos"]} == {"reserva_cancelada"}
    leido = api.post(f"/api/v1/avisos/{bandeja['avisos'][0]['id_aviso']}/leido", headers=d["auth"])
    assert leido.status_code == 200 and leido.json()["leido"] is True

    # Estado de las operaciones y registro de sincronización sin datos sensibles (RN43)
    assert len(api.get(f"/api/v1/sin-conexion/operaciones?dispositivo={disp}", headers=d["auth"]).json()) == 3
    tipos = _fila(c, "SELECT array_agg(tipo ORDER BY id_sync_log) FROM fashionstore.sync_log s "
                     "JOIN fashionstore.dispositivos d USING (id_tenant, id_dispositivo) WHERE d.identificador = :u", u=disp)[0]
    assert tipos == ["descarga", "sincronizacion", "sincronizacion"]


def test_p2_tablas_sin_conexion_aisladas_por_empresa(mundo):
    d = _catalogo_b(mundo)
    c = mundo["conexion"]
    _contexto(c, tenant=mundo["id_b"])
    c.execute(text("INSERT INTO fashionstore.dispositivos (identificador, id_cliente, plataforma, codigo_corto) "
                   "VALUES (gen_random_uuid(), :c, 'pwa', 'ABCD')"), {"c": d["cliente"]})
    c.execute(text("INSERT INTO fashionstore.avisos_cliente (id_cliente, tipo, titulo, mensaje) "
                   "VALUES (:c, 'reserva_cancelada', 't', 'm')"), {"c": d["cliente"]})
    for tabla in ("dispositivos", "avisos_cliente"):
        _contexto(c, tenant=mundo["id_b"])
        assert c.execute(text(f"SELECT count(*) FROM fashionstore.{tabla}")).scalar() == 1
        _contexto(c, tenant=1)
        assert c.execute(text(f"SELECT count(*) FROM fashionstore.{tabla} WHERE id_tenant = :t"), {"t": mundo["id_b"]}).scalar() == 0
        _contexto(c)
        assert c.execute(text(f"SELECT count(*) FROM fashionstore.{tabla}")).scalar() == 0

    # Escribir en otra empresa: lo impide la RLS; mezclar empresas: lo impiden las FK compuestas
    _contexto(c, tenant=1)
    error = _falla(c, "INSERT INTO fashionstore.avisos_cliente (id_tenant, id_cliente, tipo, titulo, mensaje) "
                      "VALUES (:t, :c, 'reserva_cancelada', 't', 'm')", t=mundo["id_b"], c=d["cliente"])
    assert error and "row-level security" in error
    _contexto(c, tenant=mundo["id_b"])
    disp = c.execute(text("SELECT id_dispositivo FROM fashionstore.dispositivos")).scalar()
    error = _falla(c, "INSERT INTO fashionstore.operaciones_sync (uuid_operacion, id_dispositivo, id_sucursal, tipo, estado, registrada_en) "
                      "VALUES (gen_random_uuid(), :d, :s, 'reserva', 'rechazada', now())", d=disp, s=d["sucursal_fs"])
    assert error and "fk_operaciones_sync_sucursal" in error
    _contexto(c)


def test_p2_cu19_cu20_compra_cobrada_sin_stock_se_reembolsa(mundo, monkeypatch):
    from integrations.stripe_service import ResultadoPasarela, StripeService
    from modules.sincronizacion.cu19_sincronizar import servicio as cu19
    from modules.sincronizacion.cu20_conflictos import servicio as cu20

    aprobado = ResultadoPasarela(aprobado=True, referencia="pi_sbx_sync", codigo_respuesta="succeeded", mensaje="ok")
    monkeypatch.setattr(cu19.PagoServicio, "verificar_cobro", staticmethod(lambda pago, pasarela=None: aprobado))
    monkeypatch.setattr(cu20, "StripeService", lambda: StripeService(api_key="", latencia_simulada_ms=0))

    d = _catalogo_b(mundo, unidades=0)
    api, c, t = mundo["cliente"], mundo["conexion"], mundo["id_b"]
    _contexto(c, plataforma=True)
    q = lambda sql, **p: c.execute(text(sql), p).scalar()
    # Compra móvil cuya retención venció (anulada) y que Stripe cobró: no queda stock para completarla
    venta = q("INSERT INTO fashionstore.ventas (id_tenant, id_cliente, id_sucursal, tipo_venta, numero_comprobante, estado, "
              "subtotal, total, fecha_venta) VALUES (:t, :c, :s, 'digital_movil', 'SYNC-B-0001', 'anulada', 100, 100, "
              "now() - interval '1 hour') RETURNING id_venta", t=t, c=d["cliente"], s=d["s1"])
    q("INSERT INTO fashionstore.venta_detalle (id_tenant, id_venta, id_variante, cantidad, precio_unitario, id_sucursal) "
      "VALUES (:t, :v, :var, 1, 100, :s) RETURNING id_venta_detalle", t=t, v=venta, var=d["variante"], s=d["s1"])
    pago = q("INSERT INTO fashionstore.pagos (id_tenant, id_venta, metodo_pago, monto, estado, referencia_pasarela) "
             "VALUES (:t, :v, 'tarjeta_credito', 100, 'pendiente', 'pi_sbx_sync') RETURNING id_pago", t=t, v=venta)
    # Encargado autorizado solo en la otra sucursal
    encargado = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo, id_tenant, id_sucursal) "
                  "VALUES ('encargado.sync@empresa-b.com', :h, 'Enc', 'B', 'encargado_sucursal', true, :t, :s) RETURNING id_usuario",
                  h=hash_password(CLAVE_PRUEBA), t=t, s=d["s2"])
    q("INSERT INTO fashionstore.empleados (id_empleado, id_tenant, codigo_empleado, cargo, fecha_contratacion) "
      "VALUES (:u, :t, 'EMP-B-SYNC', 'Encargado', current_date) RETURNING id_empleado", u=encargado, t=t)
    _contexto(c)

    disp = str(_uuid.uuid4())
    assert api.post("/api/v1/sin-conexion/dispositivos", json={"identificador": disp, "plataforma": "flutter"},
                    headers=d["auth"]).status_code == 201
    compra = {"uuid": str(_uuid.uuid4()), "tipo": "compra_interrumpida",
              "registrada_en": _dt.now(_tz.utc).isoformat(),
              "datos": {"id_venta": venta, "id_pago": pago, "client_secret": "no-debe-guardarse"}}
    lote = api.post("/api/v1/sin-conexion/sincronizar", json={"dispositivo": disp, "operaciones": [compra]}, headers=d["auth"])
    resultado = lote.json()["resultados"][0]
    assert (resultado["estado"], resultado["motivo"]) == ("en_conflicto", "STOCK_INSUFICIENTE"), lote.text
    id_conflicto = resultado["id_conflicto"]
    assert _fila(c, "SELECT estado FROM fashionstore.pagos WHERE id_pago = :p", p=pago)[0] == "confirmado"
    assert "client_secret" not in str(_fila(c, "SELECT datos FROM fashionstore.operaciones_sync WHERE id_venta = :v", v=venta)[0])
    assert tuple(_fila(c, "SELECT cantidad_disponible, cantidad_reservada FROM fashionstore.inventario_sucursal "
                          "WHERE id_inventario = :i", i=d["inventario"])) == (0, 0)

    admin = _token(mundo["admin_b"], "administrador", t)
    enc = _token(encargado, "encargado_sucursal", t)
    # A2: el encargado de la otra sucursal no lo ve; FASHION STORE tampoco (RLS)
    assert api.get("/api/v1/conflictos-sync", headers=enc).json() == []
    assert api.get(f"/api/v1/conflictos-sync/{id_conflicto}", headers=enc).status_code == 404
    _contexto(c, tenant=1)
    assert c.execute(text("SELECT count(*) FROM fashionstore.conflictos_sync WHERE id_conflicto = :i"), {"i": id_conflicto}).scalar() == 0
    _contexto(c)

    lista = api.get("/api/v1/conflictos-sync", headers=admin)
    assert [x["id_conflicto"] for x in lista.json()] == [id_conflicto]
    detalle = api.get(f"/api/v1/conflictos-sync/{id_conflicto}", headers=admin).json()
    assert detalle["detalle"]["esperado"] == 1 and detalle["detalle"]["encontrado"] == 0
    assert detalle["pago"]["monto"] == "100.00"
    assert api.get("/api/v1/conflictos-sync/resumen", headers=admin).json() == {"pendiente": 1, "reembolso_pendiente": 0}

    # Aceptar (y el segundo intento choca, A3)
    aceptado = api.post(f"/api/v1/conflictos-sync/{id_conflicto}/aceptar-reembolso", headers=admin)
    assert aceptado.status_code == 200, aceptado.text
    assert aceptado.json()["estado"] == "reembolso_pendiente"
    otra = api.post(f"/api/v1/conflictos-sync/{id_conflicto}/aceptar-reembolso", headers=admin)
    assert otra.status_code == 409 and otra.json()["code"] == "CONFLICTO_YA_RESUELTO"
    assert tuple(_fila(c, "SELECT cantidad_disponible, cantidad_reservada FROM fashionstore.inventario_sucursal "
                          "WHERE id_inventario = :i", i=d["inventario"])) == (0, 0)  # el inventario no se toca

    # Cierre: el encargado no puede; sin forzar solo el último día; forzado reembolsa
    assert api.post("/api/v1/conflictos-sync/procesar-cierre", json={"forzar": True}, headers=enc).status_code == 403
    if not api.get("/api/v1/conflictos-sync/cierre", headers=admin).json()["es_ultimo_dia_del_mes"]:
        sin_forzar = api.post("/api/v1/conflictos-sync/procesar-cierre", json={"forzar": False}, headers=admin)
        assert sin_forzar.status_code == 409 and sin_forzar.json()["code"] == "CIERRE_NO_DISPONIBLE"
    cierre = api.post("/api/v1/conflictos-sync/procesar-cierre", json={"forzar": True}, headers=admin)
    assert cierre.status_code == 200, cierre.text
    assert (cierre.json()["procesados"], cierre.json()["reembolsados"]) == (1, 1)
    assert _fila(c, "SELECT estado FROM fashionstore.pagos WHERE id_pago = :p", p=pago)[0] == "reembolsado"
    assert _fila(c, "SELECT estado FROM fashionstore.conflictos_sync WHERE id_conflicto = :i", i=id_conflicto)[0] == "resuelto"

    # El cliente ve los avisos y el nuevo estado de su operación
    assert {a["tipo"] for a in api.get("/api/v1/avisos", headers=d["auth"]).json()["avisos"]} == {
        "reembolso_aceptado", "reembolso_procesado"}
    operaciones = api.get(f"/api/v1/sin-conexion/operaciones?dispositivo={disp}", headers=d["auth"]).json()
    assert operaciones[0]["estado_conflicto"] == "resuelto"


# ----------------------------------------------------- concurrencia real (dos conexiones, datos confirmados)

@pytest.fixture
def empresa_confirmada(motor):
    """Empresa suspendida (no aparece en el directorio) con una unidad en stock, **confirmada** en la rama
    de pruebas para que dos conexiones la vean. Se borra entera al terminar."""
    limpiar_cache_tenants()
    sufijo = _uuid.uuid4().hex[:8]
    ids = {}
    with motor.connect() as c:
        with c.begin():
            _contexto(c, plataforma=True)
            q = lambda sql, **p: c.execute(text(sql), p).scalar()
            t = q("INSERT INTO fashionstore.tenants (codigo, nombre, estado) VALUES (:c, 'Concurrencia', 'suspendida') "
                  "RETURNING id_tenant", c=f"sync-{sufijo}")
            q("INSERT INTO fashionstore.suscripciones (id_tenant, id_plan, estado, fecha_inicio, fecha_vencimiento) "
              "VALUES (:t, (SELECT id_plan FROM fashionstore.planes WHERE nombre = 'Básico'), 'activa', current_date - 1, "
              "current_date + 30) RETURNING id_suscripcion", t=t)
            q("INSERT INTO fashionstore.configuracion_tenant (id_tenant) VALUES (:t) RETURNING id_tenant", t=t)
            s = q("INSERT INTO fashionstore.sucursales (id_tenant, nombre, direccion, id_ciudad) VALUES "
                  "(:t, 'Sucursal C', 'Calle de prueba 1', (SELECT min(id_ciudad) FROM fashionstore.ciudades)) RETURNING id_sucursal", t=t)
            cat = q("INSERT INTO fashionstore.categorias (id_tenant, nombre) VALUES (:t, 'Cat C') RETURNING id_categoria", t=t)
            temp = q("INSERT INTO fashionstore.temporadas (id_tenant, nombre, fecha_inicio, fecha_fin) "
                     "VALUES (:t, 'Temp C', current_date, current_date + 30) RETURNING id_temporada", t=t)
            prod = q("INSERT INTO fashionstore.productos (id_tenant, id_categoria, nombre, precio_base) "
                     "VALUES (:t, :c, 'Prenda C', 50) RETURNING id_producto", t=t, c=cat)
            var = q("INSERT INTO fashionstore.variantes_producto (id_tenant, id_producto, id_talla, id_color, sku) VALUES "
                    "(:t, :p, (SELECT min(id_talla) FROM fashionstore.tallas), (SELECT min(id_color) FROM fashionstore.colores), "
                    "'SYNC-C-1') RETURNING id_variante", t=t, p=prod)
            inv = q("INSERT INTO fashionstore.inventario_sucursal (id_tenant, id_variante, id_sucursal, id_temporada, "
                    "cantidad_disponible) VALUES (:t, :v, :s, :tp, 1) RETURNING id_inventario", t=t, v=var, s=s, tp=temp)
            cliente = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo) VALUES "
                        "(:e, :h, 'Cliente', 'Concurrente', 'cliente', true) RETURNING id_usuario",
                        e=f"concurrencia.{sufijo}@ejemplo.com", h=hash_password(CLAVE_PRUEBA))
            q("INSERT INTO fashionstore.clientes (id_cliente) VALUES (:c) RETURNING id_cliente", c=cliente)
            q("INSERT INTO fashionstore.cliente_tenant (id_tenant, id_cliente) VALUES (:t, :c) RETURNING id_cliente", t=t, c=cliente)
            disp = q("INSERT INTO fashionstore.dispositivos (id_tenant, identificador, id_cliente, plataforma, codigo_corto) "
                     "VALUES (:t, gen_random_uuid(), :c, 'pwa', 'CCCC') RETURNING id_dispositivo", t=t, c=cliente)
            ids = {"tenant": t, "sucursal": s, "variante": var, "inventario": inv, "cliente": cliente, "dispositivo": disp}
    try:
        yield ids
    finally:
        with motor.connect() as c:
            with c.begin():
                _contexto(c, plataforma=True)
                # Orden de las FK: lo que apunta a ventas, empleados o usuarios se borra antes (P2-CU18).
                for tabla in ("avisos_cliente", "conflictos_sync", "sync_log", "operaciones_sync", "dispositivos",
                              "cambio_prenda_detalle", "cambios_prenda",
                              "movimientos_inventario", "reserva_detalle", "reservas", "pagos", "venta_detalle",
                              "ventas", "inventario_sucursal",
                              "variantes_producto", "productos", "categorias", "temporadas", "bitacora",
                              "configuracion_tenant", "empleado_sucursal", "empleados", "usuarios",
                              "sucursales", "historial_suscripcion", "suscripciones",
                              "cliente_tenant"):
                    c.execute(text(f"DELETE FROM fashionstore.{tabla} WHERE id_tenant = :t"), {"t": ids["tenant"]})
                c.execute(text("DELETE FROM fashionstore.tenants WHERE id_tenant = :t"), {"t": ids["tenant"]})
                c.execute(text("DELETE FROM fashionstore.clientes WHERE id_cliente = :c"), {"c": ids["cliente"]})
                c.execute(text("DELETE FROM fashionstore.usuarios WHERE id_usuario = :c"), {"c": ids["cliente"]})
        limpiar_cache_tenants()


def _en_paralelo(motor, empresa, operaciones):
    """Procesa cada operación en su propia conexión, a la vez, con el servicio real de CU19."""
    from modules.autenticacion_seguridad.modelos import UsuarioORM
    from modules.sincronizacion.cu19_sincronizar.esquemas import OperacionIn
    from modules.sincronizacion.cu19_sincronizar.servicio import SincronizacionServicio

    barrera = threading.Barrier(len(operaciones))
    resultados = [None] * len(operaciones)

    def trabajar(i, op):
        sesion = Session(bind=motor)
        sesion.info.update({"id_tenant": empresa["tenant"], "id_usuario": empresa["cliente"], "modo_plataforma": False})
        try:
            usuario = sesion.get(UsuarioORM, empresa["cliente"])
            sesion.commit()
            barrera.wait(timeout=30)
            resultados[i] = SincronizacionServicio._procesar(
                sesion, usuario, empresa["dispositivo"], "web", OperacionIn(**op), None
            )
        except Exception as exc:  # noqa: BLE001 - se comprueba abajo
            resultados[i] = exc
        finally:
            sesion.close()

    hilos = [threading.Thread(target=trabajar, args=(i, op)) for i, op in enumerate(operaciones)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=120)
    for r in resultados:
        assert not isinstance(r, Exception), repr(r)
    return resultados


def _estado_stock(motor, empresa):
    with motor.connect() as c:
        with c.begin():
            _contexto(c, plataforma=True)
            stock = c.execute(text("SELECT cantidad_disponible, cantidad_reservada FROM fashionstore.inventario_sucursal "
                                   "WHERE id_inventario = :i"), {"i": empresa["inventario"]}).one()
            reservas = c.execute(text("SELECT count(*) FROM fashionstore.reservas WHERE id_tenant = :t"),
                                 {"t": empresa["tenant"]}).scalar()
            operaciones = c.execute(text("SELECT count(*) FROM fashionstore.operaciones_sync WHERE id_tenant = :t"),
                                    {"t": empresa["tenant"]}).scalar()
    return tuple(stock), reservas, operaciones


def test_p2_err04_dos_sincronizaciones_por_la_ultima_unidad(motor, empresa_confirmada):
    e = empresa_confirmada
    ops = [_op_reserva(e["sucursal"], e["variante"], 1, f"PROV-CCCC-00000{i}") for i in (1, 2)]
    resultados = _en_paralelo(motor, e, ops)
    assert sorted(r.estado for r in resultados) == ["confirmada", "rechazada"]
    assert next(r for r in resultados if r.estado == "rechazada").motivo == "STOCK_INSUFICIENTE"
    assert _estado_stock(motor, e) == ((0, 1), 1, 2)  # nunca negativo, una sola reserva


def test_p2_rn35_el_mismo_uuid_enviado_a_la_vez_se_aplica_una_vez(motor, empresa_confirmada):
    e = empresa_confirmada
    op = _op_reserva(e["sucursal"], e["variante"], 1, "PROV-CCCC-000009")
    resultados = _en_paralelo(motor, e, [op, dict(op)])
    assert {r.estado for r in resultados} == {"confirmada"}
    assert resultados[0].codigo_reserva == resultados[1].codigo_reserva
    assert sorted(r.repetida for r in resultados) == [False, True]
    assert _estado_stock(motor, e) == ((0, 1), 1, 1)


# --------------------------------------------------------------------------------- P2-CU18 (0021)
# Spec: `.specs/changes/P2-CU18-cambio-prenda/plan.md` §8.

def _venta_pagada_b(mundo, d, cupon=False):
    """Venta pagada en la empresa B (hace 2 días) de 2 unidades de la prenda del catálogo de prueba,
    y un cajero de B en la sucursal 1. Devuelve ids y la cabecera del cajero."""
    c, t = mundo["conexion"], mundo["id_b"]
    _contexto(c, plataforma=True)
    q = lambda sql, **p: c.execute(text(sql), p).scalar()
    otra = q("INSERT INTO fashionstore.variantes_producto (id_tenant, id_producto, id_talla, id_color, sku) VALUES "
             "(:t, :p, (SELECT max(id_talla) FROM fashionstore.tallas), (SELECT min(id_color) FROM fashionstore.colores), "
             "'SYNC-B-2') RETURNING id_variante", t=t, p=d["producto"])
    temp = q("SELECT id_temporada FROM fashionstore.inventario_sucursal WHERE id_inventario = :i", i=d["inventario"])
    inv_otra = q("INSERT INTO fashionstore.inventario_sucursal (id_tenant, id_variante, id_sucursal, id_temporada, "
                 "cantidad_disponible) VALUES (:t, :v, :s, :tp, 3) RETURNING id_inventario", t=t, v=otra, s=d["s1"], tp=temp)
    total = 180 if cupon else 200
    venta = q("INSERT INTO fashionstore.ventas (id_tenant, id_cliente, id_sucursal, tipo_venta, numero_comprobante, estado, "
              "subtotal, descuento, total, fecha_venta) VALUES (:t, :c, :s, 'presencial', 'B-CAMBIO-0001', 'pagada', 200, :desc, "
              ":tot, now() - interval '2 days') RETURNING id_venta",
              t=t, c=d["cliente"], s=d["s1"], desc=200 - total, tot=total)
    linea = q("INSERT INTO fashionstore.venta_detalle (id_tenant, id_venta, id_variante, cantidad, precio_unitario, id_sucursal) "
              "VALUES (:t, :v, :var, 2, 100, :s) RETURNING id_venta_detalle", t=t, v=venta, var=d["variante"], s=d["s1"])
    cajero = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo, id_tenant, id_sucursal) "
               "VALUES ('cajero.cambio@empresa-b.com', :h, 'Caja', 'B', 'cajero', true, :t, :s) RETURNING id_usuario",
               h=hash_password(CLAVE_PRUEBA), t=t, s=d["s1"])
    q("INSERT INTO fashionstore.empleados (id_empleado, id_tenant, codigo_empleado, cargo, fecha_contratacion) "
      "VALUES (:u, :t, 'EMP-B-CAJA', 'Cajero', current_date) RETURNING id_empleado", u=cajero, t=t)
    _contexto(c)
    return {"venta": venta, "linea": linea, "otra": otra, "inv_otra": inv_otra,
            "cajero": _token(cajero, "cajero", t)}


def test_p2_cu18_cambio_de_prenda_con_kardex_y_aislamiento(mundo):
    d = _catalogo_b(mundo, unidades=1)
    v = _venta_pagada_b(mundo, d, cupon=True)
    api, c = mundo["cliente"], mundo["conexion"]

    # AC-1: la venta con lo que queda por cambiar y lo pagado por unidad (cupón repartido: 100 × 180/200)
    venta = api.get("/api/v1/pos/cambios/venta?comprobante=b-cambio-0001", headers=v["cajero"])
    assert venta.status_code == 200, venta.text
    linea = venta.json()["lineas"][0]
    assert (linea["cambiables"], linea["valor_unitario"], venta.json()["dias_transcurridos"]) == (2, "90.00", 2)

    # AC-6/AC-7: devuelve 1 (vale 90) y se lleva la otra talla (100): paga 10 en efectivo con 20
    cuerpo = {"id_venta": v["venta"], "devueltas": [{"id_venta_detalle": v["linea"], "cantidad": 1}],
              "nuevas": [{"id_variante": v["otra"], "cantidad": 1}]}
    previo = api.post("/api/v1/pos/cambios/previsualizar", json=cuerpo, headers=v["cajero"])
    assert previo.json()["diferencia"] == "10.00", previo.text
    sin_cobro = api.post("/api/v1/pos/cambios", json=cuerpo, headers=v["cajero"])
    assert sin_cobro.status_code == 422 and sin_cobro.json()["code"] == "COBRO_REQUERIDO"
    hecho = api.post("/api/v1/pos/cambios", json={**cuerpo, "cobro": {"metodo_pago": "efectivo", "monto_recibido": "20"}},
                     headers=v["cajero"])
    assert hecho.status_code == 201, hecho.text
    comprobante = hecho.json()
    assert comprobante["numero_comprobante"].startswith("CAM-") and comprobante["numero_comprobante"].endswith("-00001")
    assert (comprobante["vuelto"], comprobante["comprobante_venta"]) == ("10.00", "B-CAMBIO-0001")

    # AC-8 (RN32): entra la devuelta y sale la nueva, con sus movimientos
    _contexto(c, plataforma=True)
    saldos = dict(c.execute(text("SELECT id_inventario, cantidad_disponible FROM fashionstore.inventario_sucursal "
                                 "WHERE id_inventario IN (:a, :b)"), {"a": d["inventario"], "b": v["inv_otra"]}).all())
    movimientos = sorted(c.execute(text("SELECT tipo_movimiento::text, cantidad FROM fashionstore.movimientos_inventario "
                                        "WHERE referencia_documento = :r"), {"r": f"CAMBIO-{comprobante['id_cambio']}"}).all())
    estado_venta = c.execute(text("SELECT estado::text FROM fashionstore.ventas WHERE id_venta = :v"), {"v": v["venta"]}).scalar()
    _contexto(c)
    assert (saldos[d["inventario"]], saldos[v["inv_otra"]]) == (2, 2)
    assert movimientos == [("devolucion", 1), ("venta_confirmada", -1)]
    assert estado_venta == "pagada"

    # AC-10/RN31: queda una unidad; pedir dos se rechaza
    otra_vez = api.post("/api/v1/pos/cambios/previsualizar",
                        json={**cuerpo, "devueltas": [{"id_venta_detalle": v["linea"], "cantidad": 2}]}, headers=v["cajero"])
    assert otra_vez.status_code == 409 and otra_vez.json()["code"] == "CANTIDAD_NO_CAMBIABLE"

    # AC-12: FASHION STORE no ve el cambio de B; un cajero de B no ve una venta de otra empresa
    _contexto(c, tenant=1)
    assert c.execute(text("SELECT count(*) FROM fashionstore.cambios_prenda WHERE id_cambio = :i"),
                     {"i": comprobante["id_cambio"]}).scalar() == 0
    ajena = c.execute(text("SELECT numero_comprobante FROM fashionstore.ventas WHERE estado = 'pagada' LIMIT 1")).scalar()
    _contexto(c)
    if ajena:
        r = api.get(f"/api/v1/pos/cambios/venta?comprobante={ajena}", headers=v["cajero"])
        assert r.status_code == 404 and r.json()["code"] == "VENTA_NO_ENCONTRADA"


def test_p2_cu18_plazo_vencido(mundo):
    d = _catalogo_b(mundo)
    v = _venta_pagada_b(mundo, d)
    c = mundo["conexion"]
    _contexto(c, plataforma=True)
    c.execute(text("UPDATE fashionstore.ventas SET fecha_venta = now() - interval '20 days' WHERE id_venta = :v"), {"v": v["venta"]})
    _contexto(c)
    r = mundo["cliente"].get("/api/v1/pos/cambios/venta?comprobante=B-CAMBIO-0001", headers=v["cajero"])
    assert r.status_code == 409 and r.json()["code"] == "PLAZO_DE_CAMBIO_VENCIDO"
    assert (r.json()["dias_transcurridos"], r.json()["plazo_dias"]) == (20, 15)


def test_p2_cu18_dos_cambios_a_la_vez_sobre_la_ultima_unidad(motor, empresa_confirmada):
    """AC-11: la línea vendida tiene 1 unidad; dos cajas la cambian a la vez → solo una puede."""
    from core.errors import DomainError
    from modules.autenticacion_seguridad.modelos import UsuarioORM
    from modules.compras_pagos.cu18_cambio_prenda.esquemas import CambioIn
    from modules.compras_pagos.cu18_cambio_prenda.servicio import CambioPrendaServicio

    e = empresa_confirmada
    with motor.connect() as c:
        with c.begin():
            _contexto(c, plataforma=True)
            q = lambda sql, **p: c.execute(text(sql), p).scalar()
            venta = q("INSERT INTO fashionstore.ventas (id_tenant, id_cliente, id_sucursal, tipo_venta, numero_comprobante, "
                      "estado, subtotal, total, fecha_venta) VALUES (:t, :c, :s, 'presencial', 'C-0001', 'pagada', 50, 50, now()) "
                      "RETURNING id_venta", t=e["tenant"], c=e["cliente"], s=e["sucursal"])
            linea = q("INSERT INTO fashionstore.venta_detalle (id_tenant, id_venta, id_variante, cantidad, precio_unitario, "
                      "id_sucursal) VALUES (:t, :v, :var, 1, 50, :s) RETURNING id_venta_detalle",
                      t=e["tenant"], v=venta, var=e["variante"], s=e["sucursal"])
            cajero = q("INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo, id_tenant, "
                       "id_sucursal) VALUES (:m, :h, 'Caja', 'C', 'cajero', true, :t, :s) RETURNING id_usuario",
                       m=f"caja.{e['tenant']}@ejemplo.com", h=hash_password(CLAVE_PRUEBA), t=e["tenant"], s=e["sucursal"])
            q("INSERT INTO fashionstore.empleados (id_empleado, id_tenant, codigo_empleado, cargo, fecha_contratacion) "
              "VALUES (:u, :t, 'EMP-C', 'Cajero', current_date) RETURNING id_empleado", u=cajero, t=e["tenant"])

    datos = CambioIn(id_venta=venta, devueltas=[{"id_venta_detalle": linea, "cantidad": 1}],
                     nuevas=[{"id_variante": e["variante"], "cantidad": 1}])
    barrera = threading.Barrier(2)
    resultados = [None, None]

    def trabajar(i):
        sesion = Session(bind=motor)
        sesion.info.update({"id_tenant": e["tenant"], "id_usuario": cajero, "modo_plataforma": False})
        try:
            usuario = sesion.get(UsuarioORM, cajero)
            sesion.commit()
            barrera.wait(timeout=30)
            resultados[i] = CambioPrendaServicio.registrar(sesion, usuario, datos).numero_comprobante
        except DomainError as exc:
            resultados[i] = exc.code
        finally:
            sesion.close()

    hilos = [threading.Thread(target=trabajar, args=(i,)) for i in (0, 1)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=120)

    assert sorted(resultados, key=str)[1] == "CANTIDAD_NO_CAMBIABLE", resultados
    assert str(sorted(resultados, key=str)[0]).startswith("CAM-")
    with motor.connect() as c:
        with c.begin():
            _contexto(c, plataforma=True)
            n = c.execute(text("SELECT count(*) FROM fashionstore.cambios_prenda WHERE id_tenant = :t"), {"t": e["tenant"]}).scalar()
            stock = c.execute(text("SELECT cantidad_disponible FROM fashionstore.inventario_sucursal WHERE id_inventario = :i"),
                              {"i": e["inventario"]}).scalar()
    assert (n, stock) == (1, 1)  # un solo cambio; la prenda entra y sale: el stock queda igual


# ---------------------------------------------------------------------------------------------
# RNF18 · Respaldo manual (`.specs/changes/P2-cierre-sesion-respaldos-push/`, parte B)
# ---------------------------------------------------------------------------------------------


NULO = "\\N"  # NULL en el formato de texto de COPY


def _respaldo(mundo, id_tenant=None):
    """Genera el respaldo con la sesión del super administrador (modo plataforma) y lo lee como el script."""
    from types import SimpleNamespace

    from core.tenant import fijar_contexto
    from modules.plataforma.rnf18_respaldos.servicio import RespaldosServicio
    from tests.modules.plataforma.test_rnf18_respaldos import restaurar

    sesion = Session(bind=mundo["conexion"], join_transaction_mode="create_savepoint")
    try:
        fijar_contexto(sesion, None, plataforma=True)
        respaldo = RespaldosServicio.generar(sesion, SimpleNamespace(id_usuario=None, email="super@pruebas"), id_tenant)
    finally:
        sesion.close()
    _contexto(mundo["conexion"], plataforma=True)
    filas = {}
    for bloque in restaurar.leer_respaldo(respaldo.contenido.decode()).bloques:
        tabla = bloque.tabla.split('"')[1]
        columnas = [c.strip('"') for c in bloque.columnas.split(", ")]
        filas[tabla] = [dict(zip(columnas, linea.split("\t"))) for linea in bloque.datos.decode().splitlines()]
    return filas


def _claves_foraneas(conexion):
    return conexion.execute(text(
        "SELECT cl.relname, cr.relname, "
        "  (SELECT array_agg(a.attname ORDER BY x.n) FROM unnest(k.conkey) WITH ORDINALITY x(c, n) "
        "     JOIN pg_attribute a ON a.attrelid = k.conrelid AND a.attnum = x.c), "
        "  (SELECT array_agg(a.attname ORDER BY x.n) FROM unnest(k.confkey) WITH ORDINALITY x(c, n) "
        "     JOIN pg_attribute a ON a.attrelid = k.confrelid AND a.attnum = x.c) "
        "FROM pg_constraint k JOIN pg_class cl ON cl.oid = k.conrelid JOIN pg_class cr ON cr.oid = k.confrelid "
        "JOIN pg_namespace n ON n.oid = cl.relnamespace WHERE k.contype = 'f' AND n.nspname = 'fashionstore'"
    )).all()


def test_rnf18_el_respaldo_de_una_empresa_no_lleva_filas_de_otra(mundo):
    id_b = mundo["id_b"]
    filas = _respaldo(mundo, id_b)
    assert [f["codigo"] for f in filas["tenants"]] == ["pruebas-b"]
    assert {f["email"] for f in filas["usuarios"] if f["id_tenant"] != NULO} == {"admin@empresa-b.com"}
    for tabla, lista in filas.items():
        ajenas = [f for f in lista if f.get("id_tenant") not in (None, NULO, str(id_b))]
        assert not ajenas, f"{tabla} lleva filas de otra empresa"
    assert len(filas["sucursales"]) == 2
    assert "codigos_recuperacion" not in filas

    # Y el de FASHION STORE no lleva nada de B
    otra = mundo["conexion"].execute(text("SELECT id_tenant FROM fashionstore.tenants WHERE codigo = 'fashionstore'")).scalar()
    assert otra, "la rama de pruebas debe tener FASHION STORE"
    de_fashion = _respaldo(mundo, otra)
    assert all(f.get("id_tenant") != str(id_b) for lista in de_fashion.values() for f in lista)


@pytest.mark.parametrize("codigo", ["pruebas-b", "fashionstore", "menshopping"])
def test_rnf18_el_respaldo_de_una_empresa_se_puede_restaurar_sin_claves_rotas(mundo, codigo):
    """Toda FK de una fila respaldada apunta a una fila que también está en el respaldo."""
    id_tenant = mundo["conexion"].execute(
        text("SELECT id_tenant FROM fashionstore.tenants WHERE codigo = :c"), {"c": codigo}
    ).scalar()
    assert id_tenant, f"falta la empresa {codigo} en la rama de pruebas"
    filas = _respaldo(mundo, id_tenant)
    rotas = []
    for hija, padre, columnas, referidas in _claves_foraneas(mundo["conexion"]):
        if hija not in filas or hija == padre:
            continue
        existentes = {tuple(f[c] for c in referidas) for f in filas.get(padre, [])}
        for fila in filas[hija]:
            clave = tuple(fila[c] for c in columnas)
            if NULO not in clave and clave not in existentes:
                rotas.append((hija, padre, clave))
    assert not rotas, rotas[:10]


def test_rnf18_el_respaldo_de_toda_la_plataforma_lleva_todas_las_empresas(mundo):
    filas = _respaldo(mundo)
    codigos = {f["codigo"] for f in filas["tenants"]}
    assert "pruebas-b" in codigos and len(codigos) >= 2
    assert "codigos_recuperacion" in filas


# ---------------------------------------------------------------------------------------------
# Panel del super administrador contra la base real (defectos del enum `rol_usuario` y de
# `ventas.estado` comparado como VARCHAR: las pruebas simuladas no los veían)
# ---------------------------------------------------------------------------------------------


def test_panel_del_super_administrador_responde_contra_la_base_real(mundo):
    conexion = mundo["conexion"]
    _contexto(conexion, plataforma=True)
    id_super = conexion.execute(text(
        "INSERT INTO fashionstore.usuarios (email, password_hash, nombres, apellidos, rol, activo) "
        "VALUES ('super-integracion@fashionstore-pruebas.com', :h, 'Super', 'Integración', 'super_administrador', true) "
        "RETURNING id_usuario"), {"h": hash_password(CLAVE_PRUEBA)}).scalar()
    _contexto(conexion)

    cliente = mundo["cliente"]
    login = cliente.post("/api/v1/autenticacion/login",
                         json={"email": "super-integracion@fashionstore-pruebas.com", "password": CLAVE_PRUEBA})
    assert login.status_code == 200, login.text
    assert login.json()["rol"] == "super_administrador"

    cabeceras = _token(id_super, "super_administrador", None)
    empresas = cliente.get("/api/v1/plataforma/empresas", headers=cabeceras)
    assert empresas.status_code == 200, empresas.text
    assert "pruebas-b" in {e["codigo"] for e in empresas.json()}
    assert cliente.get("/api/v1/plataforma/metricas", headers=cabeceras).status_code == 200

    respaldo = cliente.get(f"/api/v1/plataforma/respaldos?id_tenant={mundo['id_b']}", headers=cabeceras)
    assert respaldo.status_code == 200, respaldo.text
    assert respaldo.headers["content-disposition"].startswith('attachment; filename="respaldo-pruebas-b-')
