"""Creacion de tabla fashionstore.codigos_recuperacion (CU33)

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-19
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS fashionstore.codigos_recuperacion (
            id_codigo BIGSERIAL PRIMARY KEY,
            id_usuario BIGINT NOT NULL REFERENCES fashionstore.usuarios(id_usuario) ON DELETE CASCADE,
            codigo_hash VARCHAR(64) NOT NULL,
            expira_en TIMESTAMPTZ NOT NULL,
            usado BOOLEAN NOT NULL DEFAULT FALSE,
            intentos_fallidos INTEGER NOT NULL DEFAULT 0,
            ip_solicitante VARCHAR(45),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_fashionstore_codigos_recuperacion_id_usuario
        ON fashionstore.codigos_recuperacion (id_usuario)
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_fashionstore_codigos_recuperacion_codigo_hash
        ON fashionstore.codigos_recuperacion (codigo_hash)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fashionstore.codigos_recuperacion CASCADE")
