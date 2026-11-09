"""P2-CU08 y P2-CU10 · Catálogos globales (`activo` en ciudades, tallas y colores) e índice único de referencias de pago en `historial_suscripcion`.

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` (decisión S1) y `.specs/changes/P2-CU09-CU10-suscripcion-stripe/spec.md`.

- S1 (P2-CU08 A2): agrega `activo BOOLEAN NOT NULL DEFAULT true` a las tablas globales
  `fashionstore.ciudades`, `fashionstore.tallas` y `fashionstore.colores` para permitir
  desactivar elementos en uso sin eliminarlos.
- S2 (P2-CU05): las migraciones en un repositorio público NUNCA siembran cuentas de
  `super_administrador` ni hashes fijos; se aprovisionan fuera de banda con
  `Ec-backend/scripts/crear_superadmin.py`.
- P2-CU10: crea el índice único parcial `uq_historial_suscripcion_referencia_pago` sobre
  `fashionstore.historial_suscripcion ((detalle->>'referencia_pago'))` para impedir a nivel
  de base de datos la reutilización de un `PaymentIntent` en cambios de plan o renovaciones.

Revision ID: 0017
Revises: 0016
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0017"
down_revision: Union[str, None] = "0016"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"


def upgrade() -> None:
    sql = [
        # S1: columna activo en catálogos globales (P2-CU08 A2)
        f"ALTER TABLE {S}.ciudades ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        f"ALTER TABLE {S}.tallas ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        f"ALTER TABLE {S}.colores ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        # P2-CU10: índice único parcial para impedir reutilizar una referencia de pago en historial_suscripcion
        f"""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_historial_suscripcion_referencia_pago
            ON {S}.historial_suscripcion ((detalle->>'referencia_pago'))
            WHERE detalle->>'referencia_pago' IS NOT NULL
        """,
    ]
    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql = [
        f"DROP INDEX IF EXISTS {S}.uq_historial_suscripcion_referencia_pago",
        f"ALTER TABLE {S}.colores DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.tallas DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.ciudades DROP COLUMN IF EXISTS activo",
    ]
    for sentencia in sql:
        op.execute(sentencia)
