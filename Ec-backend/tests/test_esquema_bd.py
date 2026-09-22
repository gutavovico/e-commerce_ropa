"""Guardia de deriva de esquema: contrasta el ORM contra la base de datos real.

Motivación (2026-09-22): la suite completa estaba en verde mientras `GET /api/v1/catalogo`,
`/api/v1/colecciones/activas` y los filtros de búsqueda respondían 500 en ejecución. La causa era
que `TemporadaORM`, `PromocionORM` y `ProveedorORM` mapeaban columnas (`activa`, `activo`, `nit`)
que no existen en PostgreSQL, donde se llaman `estado_activo` y `nit_rut`.

Ningún test lo detectaba porque todos mockean la sesión de base de datos, y la migración
`alembic/versions/0001_base_ddl.py` tampoco servía de contraste: declara los nombres antiguos y
NO refleja el esquema realmente desplegado. Este módulo es el único punto donde el ORM se compara
con la base de datos de verdad.

Se omite automáticamente cuando no hay una `DATABASE_URL` real configurada en `Ec-backend/.env`,
para no romper CI ni el desarrollo sin conexión.
"""

import importlib
import pathlib

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

RAIZ_BACKEND = pathlib.Path(__file__).resolve().parents[1]
ARCHIVO_ENV = RAIZ_BACKEND / ".env"
ESQUEMA = "fashionstore"


def _leer_database_url() -> str | None:
    """Lee DATABASE_URL directamente del archivo .env.

    No se usa `os.environ` a propósito: `tests/conftest.py` define un valor de marcador
    apuntando a un localhost inexistente, que enmascararía la ausencia de configuración real.
    """
    if not ARCHIVO_ENV.is_file():
        return None

    for linea in ARCHIVO_ENV.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if linea.startswith("DATABASE_URL="):
            valor = linea.split("=", 1)[1].strip().strip("\"'")
            return valor or None
    return None


DATABASE_URL = _leer_database_url()

pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="Sin DATABASE_URL real en Ec-backend/.env; se omite la verificación de esquema.",
)


def _cargar_todos_los_modelos():
    """Importa cada `modelos.py` del proyecto para poblar `Base.metadata`."""
    from core.database import Base

    for ruta in (RAIZ_BACKEND / "app" / "modules").rglob("modelos.py"):
        modulo = ".".join(ruta.relative_to(RAIZ_BACKEND / "app").with_suffix("").parts)
        importlib.import_module(modulo)

    return Base


@pytest.fixture(scope="module")
def columnas_reales() -> dict[str, set[str]]:
    """Mapa {tabla: {columnas}} leído de `information_schema` de la base de datos real."""
    try:
        motor = create_engine(DATABASE_URL)
        with motor.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT table_name, column_name FROM information_schema.columns "
                    "WHERE table_schema = :esquema"
                ),
                {"esquema": ESQUEMA},
            ).fetchall()
    except SQLAlchemyError as exc:
        pytest.skip(f"No se pudo conectar a la base de datos para verificar el esquema: {exc}")

    mapa: dict[str, set[str]] = {}
    for tabla, columna in filas:
        mapa.setdefault(tabla, set()).add(columna)

    if not mapa:
        pytest.skip(f"El esquema '{ESQUEMA}' no contiene tablas en la base de datos configurada.")

    return mapa


def test_todas_las_tablas_del_orm_existen_en_la_base_de_datos(columnas_reales):
    """Cada `__tablename__` mapeado debe existir en el esquema `fashionstore`."""
    base = _cargar_todos_los_modelos()

    ausentes = sorted(
        tabla.name for tabla in base.metadata.tables.values() if tabla.name not in columnas_reales
    )

    assert not ausentes, (
        "Hay modelos ORM cuyas tablas no existen en la base de datos: "
        f"{ausentes}. Revisa el nombre en `__tablename__` o el estado de las migraciones."
    )


def test_ninguna_columna_del_orm_falta_en_la_base_de_datos(columnas_reales):
    """Ninguna columna mapeada puede faltar en la tabla real.

    Es exactamente el fallo que rompió catálogo, búsqueda y colecciones: SQLAlchemy emitía
    `SELECT temporadas.activa` contra una tabla cuya columna se llama `estado_activo`, y
    PostgreSQL respondía `UndefinedColumn`, que llegaba al cliente como un HTTP 500.
    """
    base = _cargar_todos_los_modelos()

    desajustes: dict[str, dict[str, list[str]]] = {}
    for tabla in base.metadata.tables.values():
        if tabla.name not in columnas_reales:
            continue  # Cubierto por el test de tablas ausentes.

        mapeadas = {columna.name for columna in tabla.columns}
        faltantes = mapeadas - columnas_reales[tabla.name]
        if faltantes:
            desajustes[tabla.name] = {
                "inexistentes_en_bd": sorted(faltantes),
                "disponibles_sin_mapear": sorted(columnas_reales[tabla.name] - mapeadas),
            }

    assert not desajustes, (
        "El ORM mapea columnas que no existen en la base de datos. Usa el nombre real como primer "
        "argumento de `mapped_column(\"nombre_real\", ...)` para conservar el atributo de dominio:\n"
        f"{desajustes}"
    )
