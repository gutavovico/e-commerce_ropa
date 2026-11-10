"""RNF18 · Lectura del esquema y volcado `COPY` para el respaldo manual.

Solo lee: catálogo de PostgreSQL (`information_schema`, `pg_constraint`) y `COPY (SELECT …) TO STDOUT`.
Los nombres de tabla y columna salen del catálogo y se citan con `psycopg.sql.Identifier`.
"""

from typing import Optional

from psycopg import sql
from sqlalchemy import text
from sqlalchemy.orm import Session

ESQUEMA = "fashionstore"


class RespaldosRepositorio:
    @staticmethod
    def tablas(db: Session) -> list[str]:
        return list(
            db.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = :e AND table_type = 'BASE TABLE' ORDER BY table_name"
                ),
                {"e": ESQUEMA},
            ).scalars()
        )

    @staticmethod
    def dependencias(db: Session) -> list[tuple[str, str]]:
        """Pares (tabla, tabla a la que apunta) de las FK del esquema, sin autorreferencias."""
        filas = db.execute(
            text(
                "SELECT DISTINCT cl.relname, cr.relname FROM pg_constraint k "
                "JOIN pg_class cl ON cl.oid = k.conrelid JOIN pg_class cr ON cr.oid = k.confrelid "
                "JOIN pg_namespace n ON n.oid = cl.relnamespace "
                "WHERE k.contype = 'f' AND n.nspname = :e AND cl.oid <> cr.oid"
            ),
            {"e": ESQUEMA},
        ).all()
        return [(a, b) for a, b in filas]

    @staticmethod
    def columnas(db: Session) -> dict[str, list[str]]:
        """Columnas de cada tabla en su orden, sin las generadas (`COPY FROM` no las admite)."""
        filas = db.execute(
            text(
                "SELECT table_name, column_name FROM information_schema.columns "
                "WHERE table_schema = :e AND is_generated = 'NEVER' ORDER BY table_name, ordinal_position"
            ),
            {"e": ESQUEMA},
        ).all()
        resultado: dict[str, list[str]] = {}
        for tabla, columna in filas:
            resultado.setdefault(tabla, []).append(columna)
        return resultado

    @staticmethod
    def columnas_con_secuencia(db: Session) -> list[tuple[str, str]]:
        return [
            (t, c)
            for t, c in db.execute(
                text(
                    "SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = :e AND column_default LIKE 'nextval(%' ORDER BY table_name"
                ),
                {"e": ESQUEMA},
            ).all()
        ]

    @staticmethod
    def copiar(db: Session, tabla: str, columnas: list[str], filtro: Optional[sql.Composable]) -> bytes:
        """Filas de la tabla en formato texto de `COPY`, con la RLS de la sesión."""
        consulta = sql.SQL("SELECT {cols} FROM {tabla}").format(
            cols=sql.SQL(", ").join(sql.Identifier(c) for c in columnas),
            tabla=sql.Identifier(ESQUEMA, tabla),
        )
        if filtro is not None:
            consulta = sql.SQL("{} WHERE {}").format(consulta, filtro)
        conexion = db.connection().connection.driver_connection
        partes: list[bytes] = []
        with conexion.cursor() as cursor:
            with cursor.copy(sql.SQL("COPY ({}) TO STDOUT").format(consulta)) as copia:
                for bloque in copia:
                    partes.append(bytes(bloque))
        return b"".join(partes)
