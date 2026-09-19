"""Engine de SQLAlchemy, fábrica de sesiones y dependencia get_db.

- pool_pre_ping=True: tolera desconexiones por inactividad de Neon.
- search_path=fashionstore,public: utiliza el esquema fashionstore
  y mantiene public disponible para extensiones PostgreSQL.
"""

from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from core.config import settings


class Base(DeclarativeBase):
    """Clase base declarativa de SQLAlchemy 2.0 para los modelos."""
    pass

# ============================================================================
# CONEXIÓN A POSTGRESQL / NEON
# ============================================================================

raw_db_url = str(settings.DATABASE_URL)

# Fuerza el uso de Psycopg 3 cuando la URL viene como postgres:// o postgresql://
if raw_db_url.startswith("postgres://"):
    database_url = raw_db_url.replace(
        "postgres://",
        "postgresql+psycopg://",
        1,
    )
elif raw_db_url.startswith("postgresql://"):
    database_url = raw_db_url.replace(
        "postgresql://",
        "postgresql+psycopg://",
        1,
    )
else:
    database_url = raw_db_url


# Neon con connection pooling (-pooler) no admite 'search_path' en connect_args (startup packet).
# Se conecta sin connect_args de inicio y se establece via evento post-conexión.
engine = create_engine(
    database_url,
    pool_pre_ping=True,
)


@event.listens_for(engine, "connect")
def configure_search_path(dbapi_connection, connection_record):
    """Establece el search_path de forma compatible con PgBouncer/Neon Pooler."""
    with dbapi_connection.cursor() as cursor:
        cursor.execute("SET search_path TO fashionstore, public")


# ============================================================================
# SESIONES
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# ============================================================================
# DEPENDENCIA DE FASTAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """Provee una sesión por request y la cierra al finalizar."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()