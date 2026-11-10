"""P2-Cierre · Token push para dispositivos móviles (RF37).

Spec: `P2-cierre-sesion-respaldos-push` (Parte C).
- Añade columna opcional `token_push VARCHAR(255)` a la tabla `fashionstore.dispositivos`.

Revision ID: 0022
Revises: 0021
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"


def upgrade() -> None:
    op.execute(f"""
        ALTER TABLE {S}.dispositivos
        ADD COLUMN IF NOT EXISTS token_push VARCHAR(255);
    """)


def downgrade() -> None:
    op.execute(f"""
        ALTER TABLE {S}.dispositivos
        DROP COLUMN IF EXISTS token_push;
    """)

