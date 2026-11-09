"""P2-CU05/CU08 · Super Administrador SaaS y catálogos globales (`activo` en ciudades, tallas, colores).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` (decisiones S1 y S2).

- S1 (P2-CU08 A2): agrega `activo BOOLEAN NOT NULL DEFAULT true` a las tablas globales
  `fashionstore.ciudades`, `fashionstore.tallas` y `fashionstore.colores` para permitir
  desactivar elementos en uso sin eliminarlos.
- S2 (P2-CU05): siembra de forma idempotente la cuenta inicial de `super_administrador`
  (`superadmin@fashionstore.com`, `id_tenant = NULL`).

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
SUPERADMIN_EMAIL = "superadmin@fashionstore.com"
# Hash Argon2id de 'SuperAdmin2026!'
SUPERADMIN_HASH = (
    "$argon2id$v=19$m=65536,t=3,p=4$T0mFmRwFJE+UzB649JKv7w$"
    "ShZrzE6NeWfxn4/kU1gcGiW18exJZdolHghIAHzdw+I"
)


def upgrade() -> None:
    sql = [
        # S1: columna activo en catálogos globales (P2-CU08 A2)
        f"ALTER TABLE {S}.ciudades ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        f"ALTER TABLE {S}.tallas ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        f"ALTER TABLE {S}.colores ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true",
        # S2: cuenta inicial de super_administrador (id_tenant IS NULL según chk_usuarios_tenant_segun_rol)
        f"""
        INSERT INTO {S}.usuarios (
            email, password_hash, nombres, apellidos, rol, id_tenant, id_sucursal, activo
        )
        SELECT
            '{SUPERADMIN_EMAIL}',
            '{SUPERADMIN_HASH}',
            'Super',
            'Administrador',
            'super_administrador'::{S}.rol_usuario,
            NULL,
            NULL,
            true
        WHERE NOT EXISTS (
            SELECT 1 FROM {S}.usuarios WHERE lower(email::text) = lower('{SUPERADMIN_EMAIL}')
        )
        """,
    ]
    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql = [
        f"DELETE FROM {S}.usuarios WHERE lower(email::text) = lower('{SUPERADMIN_EMAIL}') "
        f"AND rol::text = 'super_administrador'",
        f"ALTER TABLE {S}.colores DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.tallas DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.ciudades DROP COLUMN IF EXISTS activo",
    ]
    for sentencia in sql:
        op.execute(sentencia)

