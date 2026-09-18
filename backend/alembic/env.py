"""Entorno de Alembic para FashionStore.

Lee DATABASE_URL de core.config.Settings y configura la tabla de versiones
dentro del esquema fashionstore.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Sobreescribir la URL del .ini con la de Settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Metadata para autogenerate (None por ahora; apuntar a Base.metadata
# cuando se creen modelos ORM de dominio)
target_metadata = None


def run_migrations_offline() -> None:
    """Migraciones en modo offline (genera SQL sin conectar)."""
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


def run_migrations_online() -> None:
    """Migraciones en modo online (conecta al engine)."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema="fashionstore",
            include_schemas=True,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
