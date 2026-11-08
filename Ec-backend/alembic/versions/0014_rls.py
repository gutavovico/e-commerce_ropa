"""P2-CU13 · Fundación multitenant (3/3): Row Level Security, vistas, rol y permisos.

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.3 (decisiones F5, F6, F7,
F12, F13 y F16).

Contexto que fija el backend en cada transacción (`set_config(..., true)`):
  - `app.id_tenant`        → empresa de la petición.
  - `app.modo_plataforma`  → 'on' solo para el super administrador y la localización del webhook.
  - `app.id_usuario`       → usuario de la petición (el cliente lista sus empresas en `cliente_tenant`).

Sin contexto, las políticas no dejan ver ni escribir nada (F5). El dueño de las tablas
(`neondb_owner`) tiene BYPASSRLS: las migraciones y los scripts de mantenimiento no se ven afectados.
La aplicación se conecta con `fashionstore_app` (NOBYPASSRLS), creado a mano en Neon (F13).

Revision ID: 0014
Revises: 0013
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0014"
down_revision: Union[str, None] = "0013"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
ROL_APP = "fashionstore_app"

TENANT = "NULLIF(current_setting('app.id_tenant', true), '')::bigint"
USUARIO = "NULLIF(current_setting('app.id_usuario', true), '')::bigint"
PLATAFORMA = "(current_setting('app.modo_plataforma', true) = 'on')"

#: Tablas con aislamiento estándar: solo las filas de la empresa del contexto.
TABLAS_AISLADAS = [
    "sucursales", "empleados", "proveedores", "temporadas", "colecciones", "categorias", "productos",
    "variantes_producto", "inventario_sucursal", "movimientos_inventario", "reservas", "reserva_detalle",
    "carritos", "carrito_detalle", "ventas", "venta_detalle", "pagos", "promociones", "promocion_producto",
    "historial_navegacion", "recomendaciones_ia", "interacciones_chatbot", "sesiones_vestidor_virtual",
    "solicitudes_reporte_ia", "empleado_sucursal", "suscripciones", "historial_suscripcion",
    "configuracion_tenant",
]

#: Políticas especiales: tabla → (USING, WITH CHECK)
POLITICAS_ESPECIALES = {
    # F7: los empleados de la empresa y los usuarios sin empresa (clientes y super administradores)
    "usuarios": (
        f"id_tenant IS NULL OR id_tenant = {TENANT} OR {PLATAFORMA}",
        f"id_tenant IS NULL OR id_tenant = {TENANT} OR {PLATAFORMA}",
    ),
    # Eventos de la empresa; los de plataforma (sin empresa) solo se leen en modo plataforma,
    # pero cualquiera puede registrarlos (p. ej. un login fallido antes de conocer la empresa).
    "bitacora": (
        f"id_tenant = {TENANT} OR {PLATAFORMA}",
        f"id_tenant IS NULL OR id_tenant = {TENANT} OR {PLATAFORMA}",
    ),
    # El cliente ve todas las empresas en las que está registrado (pantalla de selección, P2-CU02)
    "cliente_tenant": (
        f"id_tenant = {TENANT} OR id_cliente = {USUARIO} OR {PLATAFORMA}",
        f"id_tenant = {TENANT} OR {PLATAFORMA}",
    ),
}

VISTAS = ["vw_inventario_consolidado", "vw_ventas_por_sucursal", "vw_reservas_pendientes"]


def upgrade() -> None:
    sql: list[str] = []
    estandar = f"id_tenant = {TENANT} OR {PLATAFORMA}"
    for tabla in TABLAS_AISLADAS:
        sql += [
            f"ALTER TABLE {S}.{tabla} ENABLE ROW LEVEL SECURITY",
            f"CREATE POLICY aislamiento_tenant ON {S}.{tabla} USING ({estandar}) WITH CHECK ({estandar})",
        ]
    for tabla, (usando, comprobando) in POLITICAS_ESPECIALES.items():
        sql += [
            f"ALTER TABLE {S}.{tabla} ENABLE ROW LEVEL SECURITY",
            f"CREATE POLICY aislamiento_tenant ON {S}.{tabla} USING ({usando}) WITH CHECK ({comprobando})",
        ]

    # F12: las vistas se ejecutan con los permisos de quien consulta, así respetan la RLS
    sql += [f"ALTER VIEW {S}.{vista} SET (security_invoker = true)" for vista in VISTAS]

    # F16: rol del dueño de la plataforma. `proveedor` se conserva en el enum (no se puede quitar).
    sql.append(f"ALTER TYPE {S}.rol_usuario ADD VALUE IF NOT EXISTS 'super_administrador'")

    # F13: permisos del rol de la aplicación, solo si ya existe en esta rama de Neon
    sql.append(f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROL_APP}') THEN
                GRANT USAGE ON SCHEMA {S} TO {ROL_APP};
                GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA {S} TO {ROL_APP};
                REVOKE ALL ON {S}.alembic_version FROM {ROL_APP};
                GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA {S} TO {ROL_APP};
                GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA {S} TO {ROL_APP};
                ALTER DEFAULT PRIVILEGES IN SCHEMA {S}
                    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {ROL_APP};
                ALTER DEFAULT PRIVILEGES IN SCHEMA {S}
                    GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {ROL_APP};
            END IF;
        END
        $$;
    """)

    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql: list[str] = [f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROL_APP}') THEN
                ALTER DEFAULT PRIVILEGES IN SCHEMA {S}
                    REVOKE USAGE, SELECT, UPDATE ON SEQUENCES FROM {ROL_APP};
                ALTER DEFAULT PRIVILEGES IN SCHEMA {S}
                    REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM {ROL_APP};
                REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA {S} FROM {ROL_APP};
                REVOKE ALL ON ALL SEQUENCES IN SCHEMA {S} FROM {ROL_APP};
                REVOKE ALL ON ALL TABLES IN SCHEMA {S} FROM {ROL_APP};
                REVOKE USAGE ON SCHEMA {S} FROM {ROL_APP};
            END IF;
        END
        $$;
    """]
    sql += [f"ALTER VIEW {S}.{vista} RESET (security_invoker)" for vista in VISTAS]
    for tabla in TABLAS_AISLADAS + list(POLITICAS_ESPECIALES):
        sql += [
            f"DROP POLICY IF EXISTS aislamiento_tenant ON {S}.{tabla}",
            f"ALTER TABLE {S}.{tabla} DISABLE ROW LEVEL SECURITY",
        ]
    # El valor 'super_administrador' del enum se conserva: PostgreSQL no permite quitarlo.
    for sentencia in sql:
        op.execute(sentencia)
