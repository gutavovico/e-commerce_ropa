"""Marcador de revision para CU29: Visualizar indicadores empresariales.

CU29 no altera el esquema: la revision existe solo para dejar constancia en la cadena. Su ID
lleva sufijo `a` porque `0010` ya pertenece a `0010_seed_promociones.py` (el ID duplicado rompia
`alembic history` y `alembic upgrade head`).

Revision ID: 0010a
Revises: 0010
Create Date: 2026-09-22
"""

from typing import Sequence, Union

revision: str = "0010a"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
