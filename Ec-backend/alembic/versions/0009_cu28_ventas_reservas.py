"""Marcador de revision para CU28: Consultar ventas y reservas.

CU28 no altera el esquema: la revision existe solo para dejar constancia en la cadena. Su ID
lleva sufijo `a` porque `0009` ya pertenece a `0009_checkout_ddl.py` (el ID duplicado rompia
`alembic history` y `alembic upgrade head`).

Revision ID: 0009a
Revises: 0009
Create Date: 2026-09-22
"""

from typing import Sequence, Union

revision: str = "0009a"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
