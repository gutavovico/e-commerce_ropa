"""Carga de la empresa de prueba Menshopping (RF15).

Spec: `.specs/changes/P2-RF15-menshopping/spec.md` (decisiones R1–R7).

- Datos en `scripts/datos/menshopping.json` (R1); contraseñas nunca en el repo: se leen de
  `MENSHOPPING_CLAVE_INICIAL` o se piden sin mostrarlas (R2).
- Exige los PNG del vestidor en `Ec-frontend/public/ar/` antes de cargar nada (R3).
- Una sola transacción, todo o nada (R4). Se conecta como dueño de la base: `DATABASE_URL_PRUEBAS`
  con `--db pruebas` o `DATABASE_URL_MIGRACIONES` por defecto (producción).
- Sin `--aplicar` hace la carga completa y la **deshace** al final, para comprobar que funcionaría
  (R5). Si `menshopping` o alguno de sus correos ya existen, se detiene sin tocar nada.

Uso (desde Ec-backend/):
    ./.venv/Scripts/python.exe scripts/cargar_menshopping.py --db pruebas            # comprobar
    ./.venv/Scripts/python.exe scripts/cargar_menshopping.py --db pruebas --aplicar  # ensayo
    ./.venv/Scripts/python.exe scripts/cargar_menshopping.py --aplicar               # producción

No importa `core.config`: las URL se leen de `Ec-backend/.env` con python-dotenv, para no depender
de que el `.env` local solo tenga variables declaradas en `Settings`.
"""

from __future__ import annotations

import argparse
import getpass
import json
import os
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
RAIZ_REPO = RAIZ_BACKEND.parent
ARCHIVO_DATOS = RAIZ_BACKEND / "scripts" / "datos" / "menshopping.json"
CARPETA_AR = RAIZ_REPO / "Ec-frontend" / "public" / "ar"
ZONA_BOLIVIA = "America/La_Paz"

ROLES_EMPLEADO = {"administrador": "Administrador", "encargado_sucursal": "Encargado de Sucursal", "cajero": "Cajero"}


class CargaError(Exception):
    """La carga no puede continuar; no se ha escrito nada."""


# ---------------------------------------------------------------------------------- validación

def reparto(unidades: int, variantes: int) -> list[int]:
    """RF15: unidades repartidas por igual entre las variantes con división entera (5 → 2 + 2)."""
    if variantes <= 0:
        raise CargaError("Cada prenda necesita al menos una variante.")
    return [unidades // variantes] * variantes


def validar_clave(clave: str) -> None:
    """Misma política que CU20 (`validar_complejidad_password`)."""
    if (len(clave) < 8 or not re.search(r"[A-Z]", clave) or not re.search(r"[a-z]", clave)
            or not re.search(r"\d", clave)):
        raise CargaError("La contraseña inicial necesita 8 caracteres o más, una mayúscula, una minúscula y un dígito.")


def cargar_datos(ruta: Path = ARCHIVO_DATOS) -> dict[str, Any]:
    datos = json.loads(ruta.read_text(encoding="utf-8"))
    claves_sucursal = {s["codigo"] for s in datos["sucursales"]}
    if len(datos["sucursales"]) != 2:
        raise CargaError("Menshopping tiene exactamente 2 sucursales (RF15).")
    if len(datos["prendas"]) != 4 or len({p["categoria"] for p in datos["prendas"]}) != 4:
        raise CargaError("Menshopping tiene 4 categorías con una prenda cada una (RF15).")
    if len(datos["tallas"]) != 2:
        raise CargaError("Cada prenda tiene 2 variantes (RF15).")
    for prenda in datos["prendas"]:
        if Decimal(prenda["precio"]) <= 0:
            raise CargaError(f"Precio inválido en «{prenda['nombre']}».")
    for usuario in datos["usuarios"]:
        if usuario["rol"] not in ROLES_EMPLEADO:
            raise CargaError(f"Rol no admitido: {usuario['rol']}.")
        if usuario["rol"] != "administrador" and usuario["sucursal"] not in claves_sucursal:
            raise CargaError(f"{usuario['email']} necesita una sucursal de Menshopping.")
    if sum(1 for u in datos["usuarios"] if u["rol"] == "administrador") != 1:
        raise CargaError("Menshopping necesita exactamente un administrador.")
    return datos


@dataclass
class Imagenes:
    """URL de cada prenda: el PNG del vestidor y, si existe, la foto de catálogo (R3)."""

    vestidor: dict[str, str] = field(default_factory=dict)
    catalogo: dict[str, str] = field(default_factory=dict)


def verificar_imagenes(datos: dict[str, Any], carpeta: Path = CARPETA_AR) -> Imagenes:
    faltan = [p["imagen_vestidor"] for p in datos["prendas"] if not (carpeta / p["imagen_vestidor"]).is_file()]
    if faltan:
        raise CargaError(
            f"Faltan los PNG del vestidor en {carpeta}: {', '.join(faltan)}. No se ha cargado nada."
        )
    imagenes = Imagenes()
    for p in datos["prendas"]:
        imagenes.vestidor[p["codigo"]] = f"/ar/{p['imagen_vestidor']}"
        catalogo = p.get("imagen_catalogo")
        imagenes.catalogo[p["codigo"]] = (
            f"/ar/{catalogo}" if catalogo and (carpeta / catalogo).is_file() else f"/ar/{p['imagen_vestidor']}"
        )
    return imagenes


# ---------------------------------------------------------------------------------- carga

def _uno(conexion, sql: str, **parametros):
    from sqlalchemy import text

    return conexion.execute(text(sql), parametros).scalar()


def cargar(conexion, datos: dict[str, Any], hash_clave: str, imagenes: Imagenes, hoy: date) -> dict[str, int]:
    """Inserta Menshopping en la transacción abierta de `conexion`. No confirma ni deshace.

    Escribe `id_tenant` en cada fila de forma explícita (FK compuestas) y fija el contexto
    `app.id_tenant` por si algún valor por defecto lo necesita.
    """
    from sqlalchemy import text

    S = "fashionstore"
    empresa = datos["empresa"]
    q = lambda sql, **p: _uno(conexion, sql, **p)  # noqa: E731

    conexion.execute(text("SELECT set_config('app.modo_plataforma', 'on', true)"))

    # 0. Condiciones: ni la empresa ni sus correos existen (R5)
    if q(f"SELECT 1 FROM {S}.tenants WHERE codigo = :c", c=empresa["codigo"]):
        raise CargaError(f"La empresa «{empresa['codigo']}» ya existe: la carga no se repite.")
    for usuario in datos["usuarios"]:
        if q(f"SELECT 1 FROM {S}.usuarios WHERE lower(email::text) = lower(:e)", e=usuario["email"]):
            raise CargaError(f"El correo {usuario['email']} ya existe en la plataforma (RN05).")

    # 1. Catálogos globales: ciudades nuevas, tallas, colores y plan
    for ciudad in datos["ciudades_nuevas"]:
        if not q(f"SELECT 1 FROM {S}.ciudades WHERE lower(nombre) = lower(:n)", n=ciudad["nombre"]):
            q(f"INSERT INTO {S}.ciudades (nombre, pais) VALUES (:n, :p) RETURNING id_ciudad",
              n=ciudad["nombre"], p=ciudad["pais"])
    ciudades = {s["ciudad"]: q(f"SELECT id_ciudad FROM {S}.ciudades WHERE lower(nombre) = lower(:n)", n=s["ciudad"])
                for s in datos["sucursales"]}
    tallas = {t: q(f"SELECT id_talla FROM {S}.tallas WHERE codigo = :c", c=t) for t in datos["tallas"]}
    colores = {p["color"]: q(f"SELECT id_color FROM {S}.colores WHERE nombre = :n ORDER BY id_color LIMIT 1",
                             n=p["color"]) for p in datos["prendas"]}
    id_plan = q(f"SELECT id_plan FROM {S}.planes WHERE nombre = :n", n=empresa["plan"])
    faltan = [k for k, v in {**ciudades, **tallas, **colores, "plan": id_plan}.items() if v is None]
    if faltan:
        raise CargaError(f"No existen en los catálogos globales: {', '.join(map(str, faltan))}.")

    # 2. Empresa, suscripción y configuración
    t = q(f"INSERT INTO {S}.tenants (codigo, nombre, correo_contacto, telefono, estado) "
          f"VALUES (:c, :n, :m, :tel, 'activa') RETURNING id_tenant",
          c=empresa["codigo"], n=empresa["nombre"], m=empresa.get("correo_contacto"), tel=empresa.get("telefono"))
    conexion.execute(text("SELECT set_config('app.id_tenant', :t, true)"), {"t": str(t)})
    vence = hoy + timedelta(days=365)
    id_suscripcion = q(f"INSERT INTO {S}.suscripciones (id_tenant, id_plan, estado, fecha_inicio, fecha_vencimiento) "
                       f"VALUES (:t, :p, 'activa', :i, :v) RETURNING id_suscripcion",
                       t=t, p=id_plan, i=hoy, v=vence)
    q(f"INSERT INTO {S}.historial_suscripcion (id_tenant, id_suscripcion, evento, detalle) "
      f"VALUES (:t, :s, 'alta', CAST(:d AS jsonb)) RETURNING id_historial",
      t=t, s=id_suscripcion, d=json.dumps({"plan": empresa["plan"], "origen": "carga RF15"}))
    q(f"INSERT INTO {S}.configuracion_tenant (id_tenant, moneda, zona_horaria) VALUES (:t, 'BOB', :z) "
      f"RETURNING id_tenant", t=t, z=ZONA_BOLIVIA)

    # 3. Sucursales, categorías y temporada
    sucursales = {}
    for s in datos["sucursales"]:
        sucursales[s["codigo"]] = q(
            f"INSERT INTO {S}.sucursales (id_tenant, id_ciudad, nombre, direccion, telefono, "
            f"horario_apertura, horario_cierre, activa) VALUES (:t, :c, :n, :d, :tel, '09:00', '20:00', true) "
            f"RETURNING id_sucursal",
            t=t, c=ciudades[s["ciudad"]], n=s["nombre"], d=s["direccion"], tel=s.get("telefono"))
    categorias = {}
    for p in datos["prendas"]:
        categorias[p["categoria"]] = q(
            f"INSERT INTO {S}.categorias (id_tenant, nombre) VALUES (:t, :n) RETURNING id_categoria",
            t=t, n=p["categoria"])
    temporada = datos["temporada"]
    id_temporada = q(
        f"INSERT INTO {S}.temporadas (id_tenant, nombre, tipo, fecha_inicio, fecha_fin, estado_activo, anio) "
        f"VALUES (:t, :n, CAST(:tipo AS {S}.tipo_temporada), :i, :f, true, :a) RETURNING id_temporada",
        t=t, n=temporada["nombre"], tipo=temporada["tipo"], i=hoy, f=vence, a=hoy.year)

    # 4. Usuarios, fichas de empleado y sucursales autorizadas (RN07)
    usuarios = {}
    for u in datos["usuarios"]:
        principal = sucursales.get(u["sucursal"]) if u["sucursal"] else None
        id_usuario = q(
            f"INSERT INTO {S}.usuarios (email, password_hash, nombres, apellidos, rol, id_tenant, id_sucursal, activo) "
            f"VALUES (lower(:e), :h, :n, :a, CAST(:r AS {S}.rol_usuario), :t, :s, true) RETURNING id_usuario",
            e=u["email"], h=hash_clave, n=u["nombres"], a=u["apellidos"], r=u["rol"], t=t, s=principal)
        q(f"INSERT INTO {S}.empleados (id_empleado, id_tenant, codigo_empleado, cargo, fecha_contratacion) "
          f"VALUES (:u, :t, :c, :cargo, :f) RETURNING id_empleado",
          u=id_usuario, t=t, c=f"MSH-{id_usuario}", cargo=ROLES_EMPLEADO[u["rol"]], f=hoy)
        if principal:
            q(f"INSERT INTO {S}.empleado_sucursal (id_tenant, id_empleado, id_sucursal, es_principal) "
              f"VALUES (:t, :u, :s, true) RETURNING id_empleado", t=t, u=id_usuario, s=principal)
        usuarios[u["email"]] = id_usuario
    admin = next(usuarios[u["email"]] for u in datos["usuarios"] if u["rol"] == "administrador")

    # 5. Prendas, variantes e inventario con su movimiento
    resumen = {"productos": 0, "variantes": 0, "inventario": 0, "movimientos": 0}
    for p in datos["prendas"]:
        id_producto = q(
            f"INSERT INTO {S}.productos (id_tenant, id_categoria, nombre, descripcion, precio_base, "
            f"imagen_url, modelo_ar_url, activo) VALUES (:t, :c, :n, :d, :pr, :img, :ar, true) RETURNING id_producto",
            t=t, c=categorias[p["categoria"]], n=p["nombre"], d=p["descripcion"], pr=Decimal(p["precio"]),
            img=imagenes.catalogo[p["codigo"]], ar=imagenes.vestidor[p["codigo"]])
        resumen["productos"] += 1
        for talla in datos["tallas"]:
            id_variante = q(
                f"INSERT INTO {S}.variantes_producto (id_tenant, id_producto, id_talla, id_color, sku, precio_extra, activo) "
                f"VALUES (:t, :p, :ta, :co, :sku, 0, true) RETURNING id_variante",
                t=t, p=id_producto, ta=tallas[talla], co=colores[p["color"]], sku=f"{p['sku']}-{talla}")
            resumen["variantes"] += 1
            for s in datos["sucursales"]:
                cantidad = reparto(s["unidades_por_prenda"], len(datos["tallas"]))[0]
                id_inventario = q(
                    f"INSERT INTO {S}.inventario_sucursal (id_tenant, id_variante, id_sucursal, id_temporada, "
                    f"cantidad_disponible, cantidad_reservada, stock_minimo, stock_alerta, estado) "
                    f"VALUES (:t, :v, :s, :tem, :c, 0, 0, 1, 'disponible') RETURNING id_inventario",
                    t=t, v=id_variante, s=sucursales[s["codigo"]], tem=id_temporada, c=cantidad)
                q(f"INSERT INTO {S}.movimientos_inventario (id_tenant, id_inventario, tipo_movimiento, cantidad, "
                  f"id_usuario_responsable, referencia_documento, observacion, saldo_anterior, saldo_nuevo) "
                  f"VALUES (:t, :i, 'ingreso_proveedor', :c, :u, 'CARGA-RF15', "
                  f"'Stock inicial de la empresa de prueba Menshopping', 0, :c) RETURNING id_movimiento",
                  t=t, i=id_inventario, c=cantidad, u=admin)
                resumen["inventario"] += 1
                resumen["movimientos"] += 1

    return {"id_tenant": t, "sucursales": len(sucursales), "categorias": len(categorias),
            "usuarios": len(usuarios), **resumen}


# ---------------------------------------------------------------------------------- ejecución

def _url(destino: str) -> str:
    from dotenv import dotenv_values

    valores = {**dotenv_values(RAIZ_BACKEND / ".env"), **os.environ}
    variable_url = "DATABASE_URL_PRUEBAS" if destino == "pruebas" else "DATABASE_URL_MIGRACIONES"
    url = valores.get(variable_url)
    if not url:
        raise CargaError(f"Falta {variable_url} en Ec-backend/.env (dueño de la base: la carga escribe catálogos globales).")
    return url.replace("postgresql://", "postgresql+psycopg://", 1) if url.startswith("postgresql://") else url


def _clave(aplicar: bool) -> str:
    clave = os.environ.get("MENSHOPPING_CLAVE_INICIAL")
    if not clave and aplicar:
        clave = getpass.getpass("Contraseña inicial de las 5 cuentas de Menshopping (no se muestra): ")
        if clave != getpass.getpass("Repítela: "):
            raise CargaError("Las contraseñas no coinciden.")
    if not clave:
        return "Comprobacion1"  # solo para la comprobación sin --aplicar, que se deshace
    validar_clave(clave)
    return clave


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga de la empresa de prueba Menshopping (RF15).")
    parser.add_argument("--db", choices=["pruebas", "produccion"], default="produccion")
    parser.add_argument("--aplicar", action="store_true", help="Confirma la carga (sin él, se deshace al final).")
    args = parser.parse_args()

    from argon2 import PasswordHasher  # mismos parámetros que core.security
    from sqlalchemy import create_engine

    try:
        datos = cargar_datos()
        imagenes = verificar_imagenes(datos)
        hash_clave = PasswordHasher().hash(_clave(args.aplicar))
        motor = create_engine(_url(args.db))
        with motor.connect() as conexion:
            transaccion = conexion.begin()
            try:
                hoy = datetime.now(ZoneInfo(ZONA_BOLIVIA)).date()  # fecha de Bolivia (core/tiempo.py)
                resumen = cargar(conexion, datos, hash_clave, imagenes, hoy)
            except Exception:
                transaccion.rollback()
                raise
            if args.aplicar:
                transaccion.commit()
            else:
                transaccion.rollback()
    except CargaError as error:
        print(f"No se cargó nada: {error}", file=sys.stderr)
        return 1

    estado = "CARGADA" if args.aplicar else "COMPROBADA (deshecha; añade --aplicar para cargarla)"
    print(f"Menshopping {estado} en {args.db}:")
    for clave, valor in resumen.items():
        print(f"  {clave}: {valor}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
