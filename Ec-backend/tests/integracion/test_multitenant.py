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
    assert cuerpo["tenant"] == {"codigo": "pruebas-b", "nombre": "Empresa B"}
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
    assert {"codigo": "pruebas-b", "nombre": "Empresa B"} in directorio.json()
    assert cliente.get("/api/v1/tenants/pruebas-b").json() == {"codigo": "pruebas-b", "nombre": "Empresa B"}
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
    assert login.json()["empresas"] == [{"codigo": "fashionstore", "nombre": "FASHION STORE"}]
    auth = {"Authorization": "Bearer " + login.json()["access_token"]}

    # En la tienda B todavía no puede comprar
    carrito_b = cliente.get("/api/v1/carrito", headers={**auth, CABECERA_TENANT: "pruebas-b"})
    assert carrito_b.status_code == 403
    assert carrito_b.json()["code"] == "CLIENTE_NO_REGISTRADO"

    # «Registrarme en esta tienda» (idempotente)
    alta = cliente.post("/api/v1/mis-empresas", headers={**auth, CABECERA_TENANT: "pruebas-b"})
    assert alta.status_code == 201, alta.text
    assert alta.json() == {"empresa": {"codigo": "pruebas-b", "nombre": "Empresa B"}, "registrado_ahora": True}
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
