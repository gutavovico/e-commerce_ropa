"""Fix de P2-CU11 · Moneda y zona horaria de Bolivia.

Spec: `.specs/finalized/P2-CU11-fix-moneda-zona-bolivia/spec.md` §2 (decisiones M1, M2, M4 y M6).

- M1: monedas admitidas BOB y USD; por defecto BOB.
- M2: todas las empresas pasan a BOB y `America/La_Paz` **sin convertir importes** (decisión del
  usuario: 120 € pasan a Bs 120).
- M4: la zona horaria solo puede ser `America/La_Paz`.
- M6: `empresas_disponibles()` devuelve también la moneda, para el directorio y la lista de tiendas
  del cliente (la RLS de `configuracion_tenant` impide leer la de otra empresa).

Revision ID: 0016
Revises: 0015
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0016"
down_revision: Union[str, None] = "0015"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
ROL_APP = "fashionstore_app"
ZONA = "America/La_Paz"


def _permisos_funcion() -> list[str]:
    return [
        f"REVOKE ALL ON FUNCTION {S}.empresas_disponibles() FROM PUBLIC",
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROL_APP}') THEN
                GRANT EXECUTE ON FUNCTION {S}.empresas_disponibles() TO {ROL_APP};
            END IF;
        END
        $$
        """,
    ]


def _funcion(con_moneda: bool) -> str:
    columnas = "id_tenant bigint, codigo text, nombre text" + (", moneda text" if con_moneda else "")
    seleccion = "t.id_tenant, t.codigo::text, t.nombre::text" + (
        ", COALESCE(c.moneda, 'BOB')::text" if con_moneda else ""
    )
    union = f"LEFT JOIN {S}.configuracion_tenant c ON c.id_tenant = t.id_tenant" if con_moneda else ""
    return f"""
        CREATE FUNCTION {S}.empresas_disponibles()
        RETURNS TABLE ({columnas})
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = {S}, pg_temp
        AS $$
            SELECT {seleccion}
              FROM {S}.tenants t
              {union}
             WHERE t.estado = 'activa'
               AND EXISTS (
                   SELECT 1 FROM {S}.suscripciones s
                    WHERE s.id_tenant = t.id_tenant
                      AND s.estado IN ('prueba', 'activa')
                      AND s.fecha_inicio <= current_date
                      AND s.fecha_vencimiento >= current_date)
             ORDER BY t.nombre
        $$
        """


def upgrade() -> None:
    sql = [
        # M1 / M4: valores por defecto de las empresas nuevas
        f"ALTER TABLE {S}.configuracion_tenant ALTER COLUMN moneda SET DEFAULT 'BOB', "
        f"ALTER COLUMN zona_horaria SET DEFAULT '{ZONA}'",
        # M2: todas las empresas, sin convertir importes
        f"UPDATE {S}.configuracion_tenant SET moneda = 'BOB', zona_horaria = '{ZONA}'",
        f"ALTER TABLE {S}.configuracion_tenant ADD CONSTRAINT chk_config_moneda CHECK (moneda IN ('BOB', 'USD'))",
        f"ALTER TABLE {S}.configuracion_tenant ADD CONSTRAINT chk_config_zona CHECK (zona_horaria = '{ZONA}')",
        # M6
        f"DROP FUNCTION {S}.empresas_disponibles()",
        _funcion(con_moneda=True),
        *_permisos_funcion(),
    ]
    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql = [
        f"DROP FUNCTION IF EXISTS {S}.empresas_disponibles()",
        _funcion(con_moneda=False),
        *_permisos_funcion(),
        f"ALTER TABLE {S}.configuracion_tenant DROP CONSTRAINT IF EXISTS chk_config_zona",
        f"ALTER TABLE {S}.configuracion_tenant DROP CONSTRAINT IF EXISTS chk_config_moneda",
        f"UPDATE {S}.configuracion_tenant SET moneda = 'EUR', zona_horaria = 'Europe/Madrid'",
        f"ALTER TABLE {S}.configuracion_tenant ALTER COLUMN moneda SET DEFAULT 'EUR', "
        f"ALTER COLUMN zona_horaria SET DEFAULT 'Europe/Madrid'",
    ]
    for sentencia in sql:
        op.execute(sentencia)
