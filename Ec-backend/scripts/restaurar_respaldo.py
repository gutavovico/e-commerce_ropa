"""Restaura un respaldo manual de datos (RNF18, decisión H3) en una rama de Neon que NO sea producción.

Spec: `.specs/changes/P2-cierre-sesion-respaldos-push/` (parte B).

- Solo archivos `.sql` generados desde «Respaldos» del panel del super administrador (bloques
  `COPY … FROM stdin`). Los respaldos automáticos cifrados (`.dump.gpg`) se restauran con la acción
  «restaurar» del flujo `.github/workflows/respaldo.yml`.
- Destino: la URL de `DATABASE_URL_RESTAURACION` (rol dueño de la rama nueva). Se niega si su endpoint
  es el de `DATABASE_URL` o `DATABASE_URL_MIGRACIONES` (producción) (AC-B8).
- El destino debe estar en la revisión de Alembic de la cabecera y tener vacías las tablas del
  respaldo: crea la rama, aplica `alembic upgrade <revisión>` y después este script.
- Una sola transacción: si algo falla, no queda nada a medias. Pide escribir el endpoint para confirmar.

Uso (desde Ec-backend/):
    ./.venv/Scripts/python.exe scripts/restaurar_respaldo.py respaldo-menshopping-20261110-0436.sql
"""

from __future__ import annotations

import argparse
import os
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

RAIZ_BACKEND = Path(__file__).resolve().parent.parent
VARIABLES_DE_PRODUCCION = ("DATABASE_URL", "DATABASE_URL_MIGRACIONES")
# Solo nombres simples entre comillas: lo que va dentro de la sentencia SQL no puede traer otra cosa.
_COPY = re.compile(r'^COPY (fashionstore\."[a-z_0-9]+") \(("[a-z_0-9]+"(?:, "[a-z_0-9]+")*)\) FROM stdin;$')
_SETVAL = re.compile(
    r"""^SELECT setval\(pg_get_serial_sequence\('fashionstore\."[a-z_0-9]+"', '[a-z_0-9]+'\), """
    r"""COALESCE\(\(SELECT max\("[a-z_0-9]+"\) FROM fashionstore\."[a-z_0-9]+"\), 0\) \+ 1, false\);$"""
)


@dataclass
class Bloque:
    tabla: str
    columnas: str
    datos: bytes


@dataclass
class Respaldo:
    revision: str | None
    bloques: list[Bloque] = field(default_factory=list)
    secuencias: list[str] = field(default_factory=list)


def leer_respaldo(texto: str) -> Respaldo:
    """Separa la cabecera, los bloques `COPY` y los `setval` del archivo."""
    revision = None
    respaldo = Respaldo(revision=None)
    lineas = texto.split("\n")
    i = 0
    while i < len(lineas):
        linea = lineas[i]
        if linea.startswith("-- Revisión de Alembic:"):
            revision = linea.split(":", 1)[1].strip()
        coincidencia = _COPY.match(linea)
        if linea.startswith("COPY ") and not coincidencia:
            raise ValueError(f"Línea COPY no reconocida: {linea[:120]}")
        if coincidencia:
            datos: list[str] = []
            i += 1
            while i < len(lineas) and lineas[i] != "\\.":
                datos.append(lineas[i])
                i += 1
            if i >= len(lineas):
                raise ValueError(f"Bloque COPY sin terminar: {coincidencia.group(1)}")
            contenido = ("\n".join(datos) + "\n") if datos else ""
            respaldo.bloques.append(Bloque(coincidencia.group(1), coincidencia.group(2), contenido.encode()))
        elif _SETVAL.match(linea):
            respaldo.secuencias.append(linea)
        i += 1
    respaldo.revision = revision
    return respaldo


def endpoint(url: str) -> str:
    """Identificador del endpoint de Neon (`ep-…`), igual con o sin `-pooler`."""
    host = urlsplit(url.replace("postgresql+psycopg://", "postgresql://")).hostname or ""
    return host.split(".")[0].removesuffix("-pooler")


def verificar_destino(url_destino: str, entorno: dict[str, str]) -> None:
    """AC-B8: nunca sobre la rama principal (producción)."""
    destino = endpoint(url_destino)
    if not destino:
        raise SystemExit("La URL de destino no es válida.")
    for nombre in VARIABLES_DE_PRODUCCION:
        url = entorno.get(nombre, "")
        if url and endpoint(url) == destino:
            raise SystemExit(f"Rechazado: el destino es el mismo endpoint que {nombre} (producción).")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("archivo", type=Path)
    args = parser.parse_args()

    from dotenv import dotenv_values

    entorno = {**dotenv_values(RAIZ_BACKEND / ".env"), **os.environ}
    url = entorno.get("DATABASE_URL_RESTAURACION") or ""
    if not url:
        raise SystemExit("Falta DATABASE_URL_RESTAURACION (rol dueño de la rama nueva de Neon).")
    verificar_destino(url, entorno)

    respaldo = leer_respaldo(args.archivo.read_text(encoding="utf-8"))
    print(f"Respaldo: {len(respaldo.bloques)} tablas · revisión {respaldo.revision}")

    import psycopg

    with psycopg.connect(url.replace("postgresql+psycopg://", "postgresql://")) as conexion:
        tabla_version = conexion.execute(
            "SELECT COALESCE(to_regclass('fashionstore.alembic_version'), to_regclass('public.alembic_version'))::text"
        ).fetchone()[0]
        version = conexion.execute(f"SELECT version_num FROM {tabla_version}").fetchone() if tabla_version else None
        if not version or version[0] != respaldo.revision:
            raise SystemExit(
                f"El destino está en {version[0] if version else 'ninguna revisión'} y el respaldo es de "
                f"{respaldo.revision}: aplica `alembic upgrade {respaldo.revision}` en la rama antes."
            )
        ocupadas = [
            b.tabla for b in respaldo.bloques if conexion.execute(f"SELECT EXISTS (SELECT 1 FROM {b.tabla})").fetchone()[0]
        ]
        if ocupadas:
            raise SystemExit(f"El destino ya tiene datos en {', '.join(ocupadas)}: usa una rama nueva y vacía.")

        confirmacion = input(f"Se restaurará en el endpoint {endpoint(url)}. Escríbelo para confirmar: ")
        if confirmacion.strip() != endpoint(url):
            raise SystemExit("Cancelado.")

        with conexion.transaction():
            with conexion.cursor() as cursor:
                for bloque in respaldo.bloques:
                    with cursor.copy(f"COPY {bloque.tabla} ({bloque.columnas}) FROM STDIN") as copia:
                        copia.write(bloque.datos)
                for sentencia in respaldo.secuencias:
                    cursor.execute(sentencia)
    print("Restauración completa.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
