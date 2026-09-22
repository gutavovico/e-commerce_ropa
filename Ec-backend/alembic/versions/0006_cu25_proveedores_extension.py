"""Extension y normalizacion de la tabla fashionstore.proveedores para CU25.

Revision ID: 0006
Revises: 0005
Create Date: 2026-09-21
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Normalizar columna nit -> nit_rut
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'nit'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'nit_rut'
            ) THEN
                ALTER TABLE fashionstore.proveedores RENAME COLUMN nit TO nit_rut;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'nit_rut'
            ) THEN
                ALTER TABLE fashionstore.proveedores ADD COLUMN nit_rut VARCHAR(30);
            END IF;
        END $$;
    """)

    # 2. Normalizar columna activo -> estado_activo
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'activo'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.proveedores RENAME COLUMN activo TO estado_activo;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'proveedores' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.proveedores ADD COLUMN estado_activo BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END $$;
    """)

    # 3. Anadir columnas complementarias de domicilio, rubro y marca temporal
    op.execute("""
        ALTER TABLE fashionstore.proveedores
        ADD COLUMN IF NOT EXISTS direccion VARCHAR(255) DEFAULT 'Direccion no registrada',
        ADD COLUMN IF NOT EXISTS ciudad VARCHAR(80) DEFAULT 'La Paz',
        ADD COLUMN IF NOT EXISTS rubro VARCHAR(80) DEFAULT 'Confeccion Textil',
        ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ DEFAULT now();
    """)

    # 4. Indices de unicidad y busqueda
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_proveedores_nit_rut ON fashionstore.proveedores (nit_rut);
        CREATE UNIQUE INDEX IF NOT EXISTS uq_proveedores_razon_social ON fashionstore.proveedores (LOWER(razon_social));
        CREATE INDEX IF NOT EXISTS idx_proveedores_estado ON fashionstore.proveedores (estado_activo);
        CREATE INDEX IF NOT EXISTS idx_proveedores_rubro ON fashionstore.proveedores (rubro);
    """)


def downgrade() -> None:
    pass
