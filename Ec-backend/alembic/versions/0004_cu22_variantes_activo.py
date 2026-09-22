"""Agregar columnas activo y creado_en a variantes_producto para CU22

Revision ID: 0004
Revises: 0003
Create Date: 2026-09-20
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE fashionstore.variantes_producto 
        ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT TRUE;
    """)
    op.execute("""
        ALTER TABLE fashionstore.variantes_producto 
        ADD COLUMN IF NOT EXISTS creado_en TIMESTAMPTZ NOT NULL DEFAULT now();
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE fashionstore.variantes_producto 
        DROP COLUMN IF EXISTS creado_en;
    """)
    op.execute("""
        ALTER TABLE fashionstore.variantes_producto 
        DROP COLUMN IF EXISTS activo;
    """)
