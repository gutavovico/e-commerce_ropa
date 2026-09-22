"""Creacion de la tabla fashionstore.bitacora para CU30 Consultar bitacora.

Revision ID: 0011
Revises: 0010
Create Date: 2026-09-22
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS fashionstore.bitacora (
            id_bitacora BIGSERIAL PRIMARY KEY,
            id_usuario INTEGER REFERENCES fashionstore.usuarios(id_usuario) ON DELETE SET NULL,
            usuario_nombre VARCHAR(255),
            accion VARCHAR(100) NOT NULL,
            tabla_modulo VARCHAR(100) NOT NULL,
            direccion_ip VARCHAR(45),
            severidad VARCHAR(20) NOT NULL DEFAULT 'INFO',
            payload_anterior JSONB,
            payload_nuevo JSONB,
            creado_en TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        );

        CREATE INDEX IF NOT EXISTS idx_bitacora_creado_en ON fashionstore.bitacora (creado_en DESC);
        CREATE INDEX IF NOT EXISTS idx_bitacora_severidad ON fashionstore.bitacora (severidad);
        CREATE INDEX IF NOT EXISTS idx_bitacora_modulo ON fashionstore.bitacora (tabla_modulo);
        CREATE INDEX IF NOT EXISTS idx_bitacora_usuario ON fashionstore.bitacora (id_usuario);
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS fashionstore.bitacora CASCADE;
    """)
