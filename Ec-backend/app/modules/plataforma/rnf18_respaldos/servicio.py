"""RNF18 · Respaldo manual de la base, de toda la plataforma o de una empresa (decisión H2).

Genera un archivo SQL de **datos** (bloques `COPY … FROM stdin`) en memoria: nunca toca el disco del
servidor (AC-B7). Se restaura sobre un esquema creado con `alembic upgrade <revisión>`, la que va en
la cabecera, con `scripts/restaurar_respaldo.py` (H3). El respaldo completo con esquema es el
automático (`.github/workflows/respaldo.yml`).

La sesión llega en modo plataforma (`exigir_super_administrador`): la RLS deja leer todas las
empresas, así que el alcance de una empresa lo fija el filtro de cada tabla.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from psycopg import sql
from sqlalchemy.orm import Session

from core.errors import NotFoundError
from core.tiempo import ahora_local
from core.tenant import buscar_tenant_por_id
from modules.autenticacion_seguridad.modelos import UsuarioORM
from modules.plataforma.rnf18_respaldos.repositorio import ESQUEMA, RespaldosRepositorio
from modules.seguridad.cu30_bitacora.servicio import ServicioBitacoraAuditoria

#: Tablas que no viajan en el respaldo de una empresa: códigos de recuperación de contraseña
#: (temporales y sensibles, de todas las cuentas).
EXCLUIDAS_POR_EMPRESA = frozenset({"codigos_recuperacion"})


@dataclass(frozen=True)
class Respaldo:
    nombre_archivo: str
    contenido: bytes
    tablas: int
    filas: int


def orden_por_dependencias(tablas: list[str], dependencias: list[tuple[str, str]]) -> list[str]:
    """Orden topológico: cada tabla después de las tablas a las que apunta. Empates por nombre.

    Raises:
        ValueError: si las FK forman un ciclo (hoy no hay ninguno).
    """
    pendientes = {t: {d for (o, d) in dependencias if o == t and d in tablas} for t in tablas}
    orden: list[str] = []
    while pendientes:
        listas = sorted(t for t, deps in pendientes.items() if not deps)
        if not listas:
            raise ValueError(f"Las claves foráneas forman un ciclo: {sorted(pendientes)}")
        for t in listas:
            orden.append(t)
            del pendientes[t]
        for deps in pendientes.values():
            deps.difference_update(listas)
    return orden


def filtro_empresa(tabla: str, columnas: list[str], id_tenant: int) -> Optional[sql.Composable]:
    """Filas de la tabla que pertenecen al respaldo de una empresa (AC-B4).

    - Tablas de empresa (con `id_tenant`): solo las suyas.
    - `usuarios`: sus empleados, sus clientes registrados y el super administrador (aparece en el
      historial de suscripción y en la bitácora de la empresa). Nunca empleados de otra empresa.
    - `clientes`: los registrados en la empresa (`cliente_tenant`).
    - Catálogos globales (ciudades, tallas, colores, planes…): completos; no son de ninguna empresa.
    """
    empresa = sql.Literal(int(id_tenant))
    clientes_de_la_empresa = sql.SQL(
        "SELECT ct.id_cliente FROM {ct} ct WHERE ct.id_tenant = {e}"
    ).format(ct=sql.Identifier(ESQUEMA, "cliente_tenant"), e=empresa)
    if tabla == "usuarios":
        return sql.SQL(
            "id_tenant = {e} OR (id_tenant IS NULL AND (id_usuario IN ({c}) OR rol = 'super_administrador'))"
        ).format(e=empresa, c=clientes_de_la_empresa)
    if tabla == "clientes":
        return sql.SQL("id_cliente IN ({c})").format(c=clientes_de_la_empresa)
    if "id_tenant" in columnas:
        return sql.SQL("id_tenant = {e}").format(e=empresa)
    return None


def revision_alembic() -> str:
    """Cabeza de la cadena de migraciones del código desplegado (el rol de la app no lee `alembic_version`)."""
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory

        raiz = Path(__file__).resolve().parents[4]
        configuracion = Config(str(raiz / "alembic.ini"))
        configuracion.set_main_option("script_location", str(raiz / "alembic"))
        return ScriptDirectory.from_config(configuracion).get_current_head() or "desconocida"
    except Exception:  # noqa: BLE001 - la cabecera no debe impedir el respaldo
        return "desconocida"


class RespaldosServicio:
    @staticmethod
    def generar(
        db: Session,
        usuario: UsuarioORM,
        id_tenant: Optional[int] = None,
        direccion_ip: Optional[str] = None,
    ) -> Respaldo:
        codigo = "plataforma"
        if id_tenant is not None:
            tenant = buscar_tenant_por_id(db, id_tenant)
            if tenant is None:
                raise NotFoundError("La empresa no existe.", code="EMPRESA_NO_ENCONTRADA")
            codigo = tenant.codigo

        tablas = RespaldosRepositorio.tablas(db)
        columnas = RespaldosRepositorio.columnas(db)
        orden = orden_por_dependencias(tablas, RespaldosRepositorio.dependencias(db))
        if id_tenant is not None:
            orden = [t for t in orden if t not in EXCLUIDAS_POR_EMPRESA]

        momento = ahora_local()
        partes: list[bytes] = [
            (
                f"-- FashionStore · respaldo de datos (RNF18)\n"
                f"-- Alcance: {'empresa ' + codigo + f' (id_tenant {id_tenant})' if id_tenant else 'toda la plataforma'}\n"
                f"-- Generado: {momento.isoformat()} por {usuario.email}\n"
                f"-- Revisión de Alembic: {revision_alembic()}\n"
                f"-- Restaurar sobre un esquema vacío de esa revisión con scripts/restaurar_respaldo.py.\n"
                f"SET client_encoding = 'UTF8';\n"
                f"BEGIN;\n\n"
            ).encode()
        ]
        filas_totales = 0
        for tabla in orden:
            cols = columnas.get(tabla, [])
            if not cols:
                continue
            filtro = filtro_empresa(tabla, cols, id_tenant) if id_tenant is not None else None
            datos = RespaldosRepositorio.copiar(db, tabla, cols, filtro)
            filas_totales += datos.count(b"\n")
            lista = ", ".join(f'"{c}"' for c in cols)
            partes.append(f'COPY {ESQUEMA}."{tabla}" ({lista}) FROM stdin;\n'.encode())
            partes.append(datos)
            partes.append(b"\\.\n\n")

        # Las secuencias continúan desde el mayor id restaurado.
        for tabla, columna in RespaldosRepositorio.columnas_con_secuencia(db):
            if tabla in orden:
                partes.append(
                    (
                        f"SELECT setval(pg_get_serial_sequence('{ESQUEMA}.\"{tabla}\"', '{columna}'), "
                        f'COALESCE((SELECT max("{columna}") FROM {ESQUEMA}."{tabla}"), 0) + 1, false);\n'
                    ).encode()
                )
        partes.append(b"\nCOMMIT;\n")

        ServicioBitacoraAuditoria.registrar_evento_seguro(
            id_usuario=usuario.id_usuario,
            usuario_nombre=usuario.email,
            accion="RESPALDO_MANUAL",
            tabla_modulo="plataforma.respaldos",
            direccion_ip=direccion_ip,
            severidad="WARN",
            payload_nuevo={"alcance": codigo, "id_tenant": id_tenant, "tablas": len(orden), "filas": filas_totales},
            db=db,
        )
        db.commit()

        return Respaldo(
            nombre_archivo=f"respaldo-{codigo}-{momento.strftime('%Y%m%d-%H%M')}.sql",
            contenido=b"".join(partes),
            tablas=len(orden),
            filas=filas_totales,
        )
