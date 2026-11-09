"""P2-CU08 · Catálogos globales (`activo` en ciudades, tallas y colores).

Spec: `.specs/changes/P2-CU05-CU08-superadmin/spec.md` (decisión S1).

- S1 (P2-CU08 A2): agrega `activo BOOLEAN NOT NULL DEFAULT true` a las tablas globales
  `fashionstore.ciudades`, `fashionstore.tallas` y `fashionstore.colores` para permitir
  desactivar elementos en uso sin eliminarlos.
- Nota de seguridad (S2): las migraciones en un repositorio público NUNCA siembran
  cuentas de `super_administrador` ni hashes de contraseñas fijos. El alta o rotación
  de credenciales de `super_administrador` se realiza fuera de banda mediante
  `Ec-backend/scripts/crear_superadmin.py` leyendo secretos del entorno o de `getpass`.

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
    ]
    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql = [
        f"ALTER TABLE {S}.colores DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.tallas DROP COLUMN IF EXISTS activo",
        f"ALTER TABLE {S}.ciudades DROP COLUMN IF EXISTS activo",
    ]
    for sentencia in sql:
        op.execute(sentencia)
