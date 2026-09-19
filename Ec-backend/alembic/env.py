"""Entorno de Alembic para FashionStore.

Lee DATABASE_URL desde app.core.config.Settings y utiliza el metadata
de SQLAlchemy para detectar los modelos ORM del proyecto.

Las tablas y la tabla de versiones de Alembic utilizan el esquema
fashionstore.
"""

import sys
from pathlib import Path
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool, text

# ============================================================================
# PATH DEL PROYECTO
# ============================================================================

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR / "app"))
sys.path.insert(0, str(BASE_DIR))


# ============================================================================
# CONFIGURACIÓN DE LA APLICACIÓN
# ============================================================================

from core.config import settings
from core.database import Base


# ============================================================================
# IMPORTACIÓN Y AUTO-DESCUBRIMIENTO DE MODELOS ORM
# ============================================================================
# Auto-descubrimiento dinámico de todos los submódulos de modelos dentro
# de 'modules' para que SQLAlchemy registre automáticamente todas las tablas
# en Base.metadata sin requerir importaciones manuales para cada CU nuevo.

import importlib
import pkgutil
import modules

for _, module_name, _ in pkgutil.walk_packages(modules.__path__, prefix="modules."):
    if "modelos" in module_name:
        try:
            importlib.import_module(module_name)
        except Exception:
            pass


config = context.config


# ============================================================================
# LOGGING
# ============================================================================

if config.config_file_name is not None:
    fileConfig(config.config_file_name)


# ============================================================================
# URL DE BASE DE DATOS
# ============================================================================

raw_db_url = str(settings.DATABASE_URL)

if raw_db_url.startswith("postgresql://"):
    database_url = raw_db_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )
else:
    database_url = raw_db_url

config.set_main_option(
    "sqlalchemy.url",
    database_url,
)


# ============================================================================
# METADATA
# ============================================================================

target_metadata = Base.metadata


# ============================================================================
# MIGRACIONES OFFLINE
# ============================================================================

def run_migrations_offline() -> None:
    """Ejecuta migraciones en modo offline."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema="fashionstore",
        include_schemas=True,
    )

    with context.begin_transaction():
        context.run_migrations()


# ============================================================================
# MIGRACIONES ONLINE
# ============================================================================

def run_migrations_online() -> None:
    """Ejecuta migraciones conectándose a PostgreSQL/Neon."""

    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:

        # Crear el schema si todavía no existe.
        connection.execute(
            text("CREATE SCHEMA IF NOT EXISTS fashionstore")
        )
        connection.commit()

        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="fashionstore",
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


# ============================================================================
# EJECUCIÓN
# ============================================================================

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()