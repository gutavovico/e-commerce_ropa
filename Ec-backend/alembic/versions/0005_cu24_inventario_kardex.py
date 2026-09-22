"""Agregar columnas stock_alerta a inventario_sucursal, saldo_anterior y saldo_nuevo a movimientos_inventario, y valores de enum tipo_movimiento_inv

Revision ID: 0005
Revises: 0004
Create Date: 2026-09-21
"""
from typing import Sequence, Union
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Nuevos valores en tipo_movimiento_inv enum
    # En PostgreSQL, ALTER TYPE ... ADD VALUE no puede ejecutarse dentro de un bloque transaccional en algunas versiones
    # sin embargo, autocommit_block() o sentencias individuales funcionan.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE fashionstore.tipo_movimiento_inv ADD VALUE IF NOT EXISTS 'ajuste_positivo'")
        op.execute("ALTER TYPE fashionstore.tipo_movimiento_inv ADD VALUE IF NOT EXISTS 'ajuste_negativo'")
        op.execute("ALTER TYPE fashionstore.tipo_movimiento_inv ADD VALUE IF NOT EXISTS 'venta_confirmada'")
        op.execute("ALTER TYPE fashionstore.tipo_movimiento_inv ADD VALUE IF NOT EXISTS 'cancelacion_pedido'")

    # 2. Agregar stock_alerta a inventario_sucursal
    op.execute("""
        ALTER TABLE fashionstore.inventario_sucursal
        ADD COLUMN IF NOT EXISTS stock_alerta INTEGER NOT NULL DEFAULT 5;
    """)

    # 3. Agregar saldo_anterior y saldo_nuevo a movimientos_inventario
    op.execute("""
        ALTER TABLE fashionstore.movimientos_inventario
        ADD COLUMN IF NOT EXISTS saldo_anterior INTEGER NOT NULL DEFAULT 0;
    """)
    op.execute("""
        ALTER TABLE fashionstore.movimientos_inventario
        ADD COLUMN IF NOT EXISTS saldo_nuevo INTEGER NOT NULL DEFAULT 0;
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE fashionstore.movimientos_inventario
        DROP COLUMN IF EXISTS saldo_nuevo;
    """)
    op.execute("""
        ALTER TABLE fashionstore.movimientos_inventario
        DROP COLUMN IF EXISTS saldo_anterior;
    """)
    op.execute("""
        ALTER TABLE fashionstore.inventario_sucursal
        DROP COLUMN IF EXISTS stock_alerta;
    """)
