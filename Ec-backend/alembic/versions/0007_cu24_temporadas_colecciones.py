"""Extension y normalizacion de las tablas fashionstore.temporadas y fashionstore.colecciones para CU24.

Revision ID: 0007
Revises: 0006
Create Date: 2026-09-21
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Normalizar fashionstore.temporadas: anio, estado_activo, marcas temporales y flexibilizar tipo
    op.execute("""
        DO $$
        BEGIN
            -- Normalizar activa -> estado_activo si existe activa
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'temporadas' AND column_name = 'activa'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'temporadas' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.temporadas RENAME COLUMN activa TO estado_activo;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'temporadas' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.temporadas ADD COLUMN estado_activo BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END $$;
    """)

    op.execute("""
        ALTER TABLE fashionstore.temporadas
        ADD COLUMN IF NOT EXISTS anio INTEGER NOT NULL DEFAULT EXTRACT(YEAR FROM CURRENT_DATE),
        ADD COLUMN IF NOT EXISTS creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now();
    """)

    # Permitir que tipo sea opcional o tenga default
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'temporadas' AND column_name = 'tipo'
            ) THEN
                ALTER TABLE fashionstore.temporadas ALTER COLUMN tipo DROP NOT NULL;
            END IF;
        END $$;
    """)

    # Constraints de temporadas
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'chk_temporadas_fechas_orden'
            ) THEN
                ALTER TABLE fashionstore.temporadas 
                    ADD CONSTRAINT chk_temporadas_fechas_orden CHECK (fecha_fin > fecha_inicio);
            END IF;

            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'chk_temporadas_anio_valido'
            ) THEN
                ALTER TABLE fashionstore.temporadas 
                    ADD CONSTRAINT chk_temporadas_anio_valido CHECK (anio >= 2020);
            END IF;
        END $$;

        CREATE UNIQUE INDEX IF NOT EXISTS uq_temporadas_nombre_lower 
            ON fashionstore.temporadas (LOWER(TRIM(nombre)));
        CREATE INDEX IF NOT EXISTS idx_temporadas_estado 
            ON fashionstore.temporadas (estado_activo);
        CREATE INDEX IF NOT EXISTS idx_temporadas_anio 
            ON fashionstore.temporadas (anio);
    """)

    # 2. Normalizar fashionstore.colecciones: estado_activo, actualizado_en e indices
    op.execute("""
        ALTER TABLE fashionstore.colecciones
        ADD COLUMN IF NOT EXISTS estado_activo BOOLEAN NOT NULL DEFAULT TRUE,
        ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now();

        CREATE UNIQUE INDEX IF NOT EXISTS uq_colecciones_temporada_nombre_lower 
            ON fashionstore.colecciones (id_temporada, LOWER(TRIM(nombre)));
        CREATE INDEX IF NOT EXISTS idx_colecciones_estado 
            ON fashionstore.colecciones (estado_activo);
        CREATE INDEX IF NOT EXISTS idx_colecciones_temporada 
            ON fashionstore.colecciones (id_temporada);
    """)


def downgrade() -> None:
    pass
