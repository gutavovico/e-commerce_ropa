"""P2-CU14, CU15, CU19 y CU20 · Operación sin conexión.

Spec: `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/plan.md` §4.

- Crea `dispositivos`, `operaciones_sync`, `conflictos_sync`, `sync_log` y `avisos_cliente`, todas de
  empresa: `id_tenant` con el valor por defecto del contexto, `UNIQUE (id_tenant, pk)`, FK compuestas
  hacia otras tablas de empresa y política `aislamiento_tenant`.
- `reservas.vence_en` (RN25: creación + horas de la empresa). Las reservas existentes reciben
  `creado_en + 24 h` (valor por defecto de RN25) y la columna pasa a `NOT NULL`.
- `reservas.codigo_provisional` (RN34: `PROV-<dispositivo>-<correlativo>` de una reserva sin conexión).

Estados y tipos como `VARCHAR` con `CHECK`, no `ENUM`: un `ENUM` no admite quitar valores en el
`downgrade`.

Revision ID: 0020
Revises: 0019
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
ROL_APP = "fashionstore_app"
TENANT = "NULLIF(current_setting('app.id_tenant', true), '')::bigint"
PLATAFORMA = "(current_setting('app.modo_plataforma', true) = 'on')"

#: Tabla → secuencia de su clave primaria (para los permisos del rol de la aplicación).
TABLAS = {
    "dispositivos": "dispositivos_id_dispositivo_seq",
    "operaciones_sync": "operaciones_sync_id_operacion_sync_seq",
    "conflictos_sync": "conflictos_sync_id_conflicto_seq",
    "sync_log": "sync_log_id_sync_log_seq",
    "avisos_cliente": "avisos_cliente_id_aviso_seq",
}


def _tenant(nombre: str) -> str:
    return (
        f"id_tenant BIGINT NOT NULL DEFAULT {TENANT} "
        f"CONSTRAINT fk_{nombre}_tenant REFERENCES {S}.tenants(id_tenant)"
    )


def upgrade() -> None:
    op.execute(f"""
        CREATE TABLE {S}.dispositivos (
            id_dispositivo            BIGSERIAL PRIMARY KEY,
            {_tenant("dispositivos")},
            identificador             UUID        NOT NULL,
            id_cliente                BIGINT      NOT NULL,
            plataforma                VARCHAR(10) NOT NULL,
            codigo_corto              CHAR(4)     NOT NULL,
            registrado_en             TIMESTAMPTZ NOT NULL DEFAULT now(),
            ultima_descarga_en        TIMESTAMPTZ,
            ultima_sincronizacion_en  TIMESTAMPTZ,
            CONSTRAINT uq_dispositivos_tenant_pk UNIQUE (id_tenant, id_dispositivo),
            CONSTRAINT uq_dispositivos_identificador UNIQUE (id_tenant, identificador),
            CONSTRAINT chk_dispositivos_plataforma CHECK (plataforma IN ('pwa', 'flutter')),
            CONSTRAINT fk_dispositivos_cliente FOREIGN KEY (id_tenant, id_cliente)
                REFERENCES {S}.cliente_tenant (id_tenant, id_cliente)
        )
    """)

    op.execute(f"""
        CREATE TABLE {S}.operaciones_sync (
            id_operacion_sync   BIGSERIAL PRIMARY KEY,
            {_tenant("operaciones_sync")},
            uuid_operacion      UUID        NOT NULL,
            id_dispositivo      BIGINT      NOT NULL,
            id_sucursal         INTEGER,
            tipo                VARCHAR(25) NOT NULL,
            estado              VARCHAR(15) NOT NULL,
            codigo_provisional  VARCHAR(24),
            registrada_en       TIMESTAMPTZ NOT NULL,
            recibida_en         TIMESTAMPTZ NOT NULL DEFAULT now(),
            datos               JSONB       NOT NULL DEFAULT '{{}}'::jsonb,
            resultado           JSONB       NOT NULL DEFAULT '{{}}'::jsonb,
            motivo              VARCHAR(40),
            id_reserva          BIGINT,
            id_venta            BIGINT,
            CONSTRAINT uq_operaciones_sync_tenant_pk UNIQUE (id_tenant, id_operacion_sync),
            CONSTRAINT uq_operaciones_sync_uuid UNIQUE (id_tenant, uuid_operacion),
            CONSTRAINT chk_operaciones_sync_tipo CHECK (tipo IN ('reserva', 'compra_interrumpida')),
            CONSTRAINT chk_operaciones_sync_estado CHECK (estado IN ('confirmada', 'rechazada', 'en_conflicto')),
            CONSTRAINT fk_operaciones_sync_dispositivo FOREIGN KEY (id_tenant, id_dispositivo)
                REFERENCES {S}.dispositivos (id_tenant, id_dispositivo) ON DELETE CASCADE,
            CONSTRAINT fk_operaciones_sync_sucursal FOREIGN KEY (id_tenant, id_sucursal)
                REFERENCES {S}.sucursales (id_tenant, id_sucursal),
            CONSTRAINT fk_operaciones_sync_reserva FOREIGN KEY (id_tenant, id_reserva)
                REFERENCES {S}.reservas (id_tenant, id_reserva),
            CONSTRAINT fk_operaciones_sync_venta FOREIGN KEY (id_tenant, id_venta)
                REFERENCES {S}.ventas (id_tenant, id_venta)
        )
    """)
    op.execute(f"CREATE INDEX idx_operaciones_sync_dispositivo ON {S}.operaciones_sync (id_tenant, id_dispositivo)")

    op.execute(f"""
        CREATE TABLE {S}.conflictos_sync (
            id_conflicto          BIGSERIAL PRIMARY KEY,
            {_tenant("conflictos_sync")},
            id_operacion_sync     BIGINT      NOT NULL,
            id_venta              BIGINT      NOT NULL,
            id_pago               BIGINT      NOT NULL,
            id_sucursal           INTEGER     NOT NULL,
            tipo                  VARCHAR(30) NOT NULL,
            detalle               JSONB       NOT NULL DEFAULT '{{}}'::jsonb,
            estado                VARCHAR(25) NOT NULL DEFAULT 'pendiente',
            creado_en             TIMESTAMPTZ NOT NULL DEFAULT now(),
            aceptado_por          BIGINT,
            aceptado_en           TIMESTAMPTZ,
            resuelto_en           TIMESTAMPTZ,
            referencia_reembolso  VARCHAR(150),
            intentos_reembolso    INTEGER     NOT NULL DEFAULT 0,
            ultimo_error          TEXT,
            CONSTRAINT uq_conflictos_sync_tenant_pk UNIQUE (id_tenant, id_conflicto),
            CONSTRAINT uq_conflictos_sync_operacion UNIQUE (id_tenant, id_operacion_sync),
            -- Un solo conflicto (y un solo reembolso) por compra
            CONSTRAINT uq_conflictos_sync_venta UNIQUE (id_tenant, id_venta),
            CONSTRAINT chk_conflictos_sync_tipo CHECK (tipo IN (
                'stock_insuficiente', 'precio_modificado', 'producto_inactivo',
                'sucursal_inactiva', 'suscripcion_no_vigente', 'antiguedad_excedida')),
            CONSTRAINT chk_conflictos_sync_estado CHECK (estado IN ('pendiente', 'reembolso_pendiente', 'resuelto')),
            CONSTRAINT fk_conflictos_sync_operacion FOREIGN KEY (id_tenant, id_operacion_sync)
                REFERENCES {S}.operaciones_sync (id_tenant, id_operacion_sync),
            CONSTRAINT fk_conflictos_sync_venta FOREIGN KEY (id_tenant, id_venta)
                REFERENCES {S}.ventas (id_tenant, id_venta),
            CONSTRAINT fk_conflictos_sync_pago FOREIGN KEY (id_tenant, id_pago)
                REFERENCES {S}.pagos (id_tenant, id_pago),
            CONSTRAINT fk_conflictos_sync_sucursal FOREIGN KEY (id_tenant, id_sucursal)
                REFERENCES {S}.sucursales (id_tenant, id_sucursal),
            CONSTRAINT fk_conflictos_sync_aceptado_por FOREIGN KEY (id_tenant, aceptado_por)
                REFERENCES {S}.usuarios (id_tenant, id_usuario)
        )
    """)
    op.execute(f"CREATE INDEX idx_conflictos_sync_estado ON {S}.conflictos_sync (id_tenant, estado)")

    op.execute(f"""
        CREATE TABLE {S}.sync_log (
            id_sync_log     BIGSERIAL PRIMARY KEY,
            {_tenant("sync_log")},
            id_dispositivo  BIGINT      NOT NULL,
            tipo            VARCHAR(15) NOT NULL,
            iniciado_en     TIMESTAMPTZ NOT NULL DEFAULT now(),
            finalizado_en   TIMESTAMPTZ,
            resultado       VARCHAR(10) NOT NULL,
            enviadas        INTEGER     NOT NULL DEFAULT 0,
            confirmadas     INTEGER     NOT NULL DEFAULT 0,
            rechazadas      INTEGER     NOT NULL DEFAULT 0,
            en_conflicto    INTEGER     NOT NULL DEFAULT 0,
            mensaje         VARCHAR(500),
            CONSTRAINT uq_sync_log_tenant_pk UNIQUE (id_tenant, id_sync_log),
            CONSTRAINT chk_sync_log_tipo CHECK (tipo IN ('descarga', 'sincronizacion')),
            CONSTRAINT chk_sync_log_resultado CHECK (resultado IN ('ok', 'parcial', 'error')),
            CONSTRAINT fk_sync_log_dispositivo FOREIGN KEY (id_tenant, id_dispositivo)
                REFERENCES {S}.dispositivos (id_tenant, id_dispositivo) ON DELETE CASCADE
        )
    """)
    op.execute(f"CREATE INDEX idx_sync_log_dispositivo ON {S}.sync_log (id_tenant, id_dispositivo)")

    op.execute(f"""
        CREATE TABLE {S}.avisos_cliente (
            id_aviso    BIGSERIAL PRIMARY KEY,
            {_tenant("avisos_cliente")},
            id_cliente  BIGINT       NOT NULL,
            tipo        VARCHAR(25)  NOT NULL,
            titulo      VARCHAR(120) NOT NULL,
            mensaje     VARCHAR(500) NOT NULL,
            id_reserva  BIGINT,
            id_venta    BIGINT,
            creado_en   TIMESTAMPTZ  NOT NULL DEFAULT now(),
            leido_en    TIMESTAMPTZ,
            CONSTRAINT uq_avisos_cliente_tenant_pk UNIQUE (id_tenant, id_aviso),
            CONSTRAINT chk_avisos_cliente_tipo CHECK (tipo IN (
                'reserva_cancelada', 'reembolso_aceptado', 'reembolso_procesado')),
            CONSTRAINT fk_avisos_cliente_cliente FOREIGN KEY (id_tenant, id_cliente)
                REFERENCES {S}.cliente_tenant (id_tenant, id_cliente),
            CONSTRAINT fk_avisos_cliente_venta FOREIGN KEY (id_tenant, id_venta)
                REFERENCES {S}.ventas (id_tenant, id_venta)
        )
    """)
    op.execute(f"CREATE INDEX idx_avisos_cliente_bandeja ON {S}.avisos_cliente (id_tenant, id_cliente, leido_en)")

    # RN25: vencimiento guardado en la reserva (CU11 C7: el valor que rige al crearla)
    op.execute(f"ALTER TABLE {S}.reservas ADD COLUMN vence_en TIMESTAMPTZ")
    op.execute(f"UPDATE {S}.reservas SET vence_en = creado_en + interval '24 hours'")
    op.execute(f"ALTER TABLE {S}.reservas ALTER COLUMN vence_en SET NOT NULL")
    # Mientras el código anterior siga desplegado (la migración se aplica antes del push, defecto 55),
    # sus reservas no indican `vence_en`: sin este valor por defecto fallarían por el NOT NULL. El
    # código nuevo lo fija siempre con las horas de la empresa (RN25).
    op.execute(f"ALTER TABLE {S}.reservas ALTER COLUMN vence_en SET DEFAULT (now() + interval '24 hours')")
    op.execute(f"ALTER TABLE {S}.reservas ADD COLUMN codigo_provisional VARCHAR(24)")

    estandar = f"id_tenant = {TENANT} OR {PLATAFORMA}"
    for tabla in TABLAS:
        op.execute(f"ALTER TABLE {S}.{tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(
            f"CREATE POLICY aislamiento_tenant ON {S}.{tabla} USING ({estandar}) WITH CHECK ({estandar})"
        )

    tablas = ", ".join(f"{S}.{t}" for t in TABLAS)
    secuencias = ", ".join(f"{S}.{s}" for s in TABLAS.values())
    op.execute(f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROL_APP}') THEN
                GRANT SELECT, INSERT, UPDATE, DELETE ON {tablas} TO {ROL_APP};
                GRANT USAGE, SELECT, UPDATE ON SEQUENCE {secuencias} TO {ROL_APP};
            END IF;
        END $$;
    """)


def downgrade() -> None:
    op.execute(f"ALTER TABLE {S}.reservas DROP COLUMN IF EXISTS codigo_provisional")
    op.execute(f"ALTER TABLE {S}.reservas DROP COLUMN IF EXISTS vence_en")
    for tabla in ("avisos_cliente", "sync_log", "conflictos_sync", "operaciones_sync", "dispositivos"):
        op.execute(f"DROP TABLE IF EXISTS {S}.{tabla}")
