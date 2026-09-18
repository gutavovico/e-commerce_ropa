"""Engine de SQLAlchemy, fabrica de sesiones y dependencia get_db.

- pool_pre_ping=True: tolera desconexiones por inactividad de Neon/Docker (AC-5).
- search_path=fashionstore,public: resuelve tablas al esquema fashionstore sin
  cualificar, y public para que las extensiones (pgcrypto, citext, pg_trgm)
  sean visibles (AC-7).
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-c search_path=fashionstore,public"},
)

SessionLocal = sessionmaker(bind=engine)


def get_db() -> Generator[Session, None, None]:
    """Dependencia de FastAPI: provee una sesion por request y la cierra al finalizar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
