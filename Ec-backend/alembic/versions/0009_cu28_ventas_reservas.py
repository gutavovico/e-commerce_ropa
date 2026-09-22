"""Marcador de revision para CU28: Consultar ventas y reservas.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-22
"""

from typing import Sequence, Union

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
