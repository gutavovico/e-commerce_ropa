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
def esquema_real() -> dict[str, dict[str, str]]:
    """Mapa {tabla: {columna: tipo}} leído de `information_schema` de la base de datos real."""
    try:
        motor = create_engine(DATABASE_URL)
        with motor.connect() as conexion:
            filas = conexion.execute(
                text(
                    "SELECT table_name, column_name, data_type FROM information_schema.columns "
                    "WHERE table_schema = :esquema"
                ),
                {"esquema": ESQUEMA},
            ).fetchall()
    except SQLAlchemyError as exc:
        pytest.skip(f"No se pudo conectar a la base de datos para verificar el esquema: {exc}")

    mapa: dict[str, dict[str, str]] = {}
    for tabla, columna, tipo in filas:
        mapa.setdefault(tabla, {})[columna] = tipo

    if not mapa:
        pytest.skip(f"El esquema '{ESQUEMA}' no contiene tablas en la base de datos configurada.")

    return mapa


@pytest.fixture(scope="module")
def columnas_reales(esquema_real) -> dict[str, set[str]]:
    """Vista simplificada {tabla: {columnas}} del esquema real."""
    return {tabla: set(columnas) for tabla, columnas in esquema_real.items()}


# Familias de tipos que se consideran equivalentes entre el ORM y PostgreSQL. Se comparan
# familias y no nombres exactos porque `VARCHAR(50)`, `character varying` y `TEXT` son
# intercambiables para el ORM, mientras que DATE frente a TIMESTAMPTZ no lo son.
FAMILIAS_TIPO = {
    "fecha": {"date"},
    "instante": {"timestamp with time zone", "timestamp without time zone"},
    "numero_exacto": {"numeric"},
    "entero": {"integer", "bigint", "smallint"},
    "texto": {"character varying", "text", "character", "citext"},
    "booleano": {"boolean"},
    "json": {"json", "jsonb"},
}


def _familia(tipo_sql: str) -> str | None:
    """Clasifica un tipo de PostgreSQL en su familia, o None si no está catalogado."""
    tipo = tipo_sql.lower()
    for familia, tipos in FAMILIAS_TIPO.items():
        if tipo in tipos:
            return familia
    return None


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


def test_los_tipos_del_orm_son_compatibles_con_la_base_de_datos(esquema_real):
    """Ningún atributo puede declarar una familia de tipo distinta a la de su columna real.

    El 2026-09-22 `PromocionORM.fecha_inicio` se declaraba `Date` mientras PostgreSQL la define
    como TIMESTAMPTZ. SQLAlchemy devolvía entonces un `datetime` donde el código esperaba un
    `date`, y la validación de cupones reventaba con «can't compare datetime.datetime to
    datetime.date». La comprobación de nombres no lo detectaba: la columna existía.

    Se comparan familias, no nombres exactos: VARCHAR y TEXT son intercambiables para el ORM,
    pero DATE y TIMESTAMPTZ no lo son.
    """
    base = _cargar_todos_los_modelos()

    incompatibles: dict[str, dict[str, str]] = {}
    for tabla in base.metadata.tables.values():
        columnas_bd = esquema_real.get(tabla.name)
        if not columnas_bd:
            continue

        for columna in tabla.columns:
            tipo_bd = columnas_bd.get(columna.name)
            if tipo_bd is None:
                continue  # Cubierto por el test de columnas ausentes.

            familia_bd = _familia(tipo_bd)
            try:
                familia_orm = _familia(columna.type.compile(dialect=_dialecto()))
            except Exception:  # noqa: BLE001 - tipos exóticos (ENUM, ARRAY) quedan fuera
                continue

            # Solo se exige coincidencia cuando ambas familias están catalogadas.
            if familia_bd and familia_orm and familia_bd != familia_orm:
                incompatibles[f"{tabla.name}.{columna.name}"] = {
                    "declarado_en_orm": str(columna.type),
                    "real_en_postgresql": tipo_bd,
                }

    assert not incompatibles, (
        "El ORM declara tipos incompatibles con la base de datos. Ajusta el tipo del "
        "`mapped_column` al real para que SQLAlchemy devuelva el objeto Python esperado:\n"
        f"{incompatibles}"
    )


def _dialecto():
    """Dialecto de PostgreSQL usado para compilar los tipos declarados en el ORM."""
    from sqlalchemy.dialects import postgresql

    return postgresql.dialect()
