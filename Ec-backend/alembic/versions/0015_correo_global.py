"""P2-CU02 · Acceso por empresa: correo único global, búsqueda de cuentas y empresas disponibles.

Spec: `.specs/changes/P2-CU02-CU01-acceso-por-empresa/spec.md` §A.1 (decisiones A2, A11, A12 y A13).

- RN05: el correo es único en toda la plataforma (el login ya no lleva código de empresa).
- `cuenta_por_email`: el login, la recuperación de acceso y la comprobación de correos repetidos
  necesitan encontrar una cuenta antes de conocer su empresa, y la RLS de `usuarios` oculta a los
  empleados de otras empresas. La función (SECURITY DEFINER) devuelve solo `id_usuario` e `id_tenant`.
- `empresas_disponibles`: código y nombre de las empresas activas con suscripción vigente, para el
  directorio de la web y la lista de tiendas del cliente (`suscripciones` tiene RLS).
- Códigos de empresa reservados: el portal `/{codigo}` comparte espacio de rutas con la web.

Revision ID: 0015
Revises: 0014
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0015"
down_revision: Union[str, None] = "0014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
ROL_APP = "fashionstore_app"

#: A13: rutas fijas de la web que no pueden ser el código de una empresa.
CODIGOS_RESERVADOS = (
    "admin", "login", "registro", "recuperar-acceso", "recuperar-password", "iniciar-sesion",
    "api", "ar", "static", "assets", "mis-tiendas", "pago", "plataforma",
)


def upgrade() -> None:
    # Precondición: sin correos repetidos (si los hay, se aborta sin cambios)
    op.execute(f"""
        DO $$
        DECLARE repetidos text;
        BEGIN
            SELECT string_agg(correo, ', ') INTO repetidos FROM (
                SELECT lower(email::text) AS correo FROM {S}.usuarios
                 GROUP BY 1 HAVING count(*) > 1
            ) r;
            IF repetidos IS NOT NULL THEN
                RAISE EXCEPTION 'P2-CU02: hay correos repetidos en usuarios (%). Resuélvalos antes de migrar.', repetidos;
            END IF;
        END
        $$;
    """)

    reservados = ", ".join(f"'{c}'" for c in CODIGOS_RESERVADOS)
    sql = [
        # A2 / RN05
        f"DROP INDEX {S}.uq_usuarios_email_empresa",
        f"DROP INDEX {S}.uq_usuarios_email_global",
        f"CREATE UNIQUE INDEX uq_usuarios_email ON {S}.usuarios (lower(email::text))",

        # A11
        f"""
        CREATE FUNCTION {S}.cuenta_por_email(p_email text)
        RETURNS TABLE (id_usuario bigint, id_tenant bigint)
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = {S}, pg_temp
        AS $$
            SELECT u.id_usuario::bigint, u.id_tenant::bigint
              FROM {S}.usuarios u
             WHERE lower(u.email::text) = lower(trim(p_email))
        $$
        """,

        # A12
        f"""
        CREATE FUNCTION {S}.empresas_disponibles()
        RETURNS TABLE (id_tenant bigint, codigo text, nombre text)
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = {S}, pg_temp
        AS $$
            SELECT t.id_tenant, t.codigo::text, t.nombre::text
              FROM {S}.tenants t
             WHERE t.estado = 'activa'
               AND EXISTS (
                   SELECT 1 FROM {S}.suscripciones s
                    WHERE s.id_tenant = t.id_tenant
                      AND s.estado IN ('prueba', 'activa')
                      AND s.fecha_inicio <= current_date
                      AND s.fecha_vencimiento >= current_date)
             ORDER BY t.nombre
        $$
        """,
        f"REVOKE ALL ON FUNCTION {S}.cuenta_por_email(text) FROM PUBLIC",
        f"REVOKE ALL ON FUNCTION {S}.empresas_disponibles() FROM PUBLIC",
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROL_APP}') THEN
                GRANT EXECUTE ON FUNCTION {S}.cuenta_por_email(text) TO {ROL_APP};
                GRANT EXECUTE ON FUNCTION {S}.empresas_disponibles() TO {ROL_APP};
            END IF;
        END
        $$
        """,

        # A13
        f"ALTER TABLE {S}.tenants ADD CONSTRAINT chk_tenants_codigo_reservado "
        f"CHECK (codigo NOT IN ({reservados}))",
    ]
    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql = [
        f"ALTER TABLE {S}.tenants DROP CONSTRAINT IF EXISTS chk_tenants_codigo_reservado",
        f"DROP FUNCTION IF EXISTS {S}.empresas_disponibles()",
        f"DROP FUNCTION IF EXISTS {S}.cuenta_por_email(text)",
        f"DROP INDEX IF EXISTS {S}.uq_usuarios_email",
        f"CREATE UNIQUE INDEX uq_usuarios_email_empresa ON {S}.usuarios (id_tenant, lower(email::text)) "
        f"WHERE id_tenant IS NOT NULL",
        f"CREATE UNIQUE INDEX uq_usuarios_email_global ON {S}.usuarios (lower(email::text)) WHERE id_tenant IS NULL",
    ]
    for sentencia in sql:
        op.execute(sentencia)
