"""P2-CU13/CU12 · Fundación multitenant (1/3): empresas, planes, suscripciones y registro de clientes.

Spec: `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.1 (decisiones F9, F14 y F15).

Crea las tablas del modelo de empresa (tenant) y siembra la empresa 1, FASHION STORE, que recibe
todos los datos actuales en la migración 0013. Las tablas que pertenecen a una empresa toman
`id_tenant` del contexto de la transacción (`app.id_tenant`) cuando el INSERT no lo indica (F2).

Revision ID: 0012
Revises: 0011
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0012"
down_revision: Union[str, None] = "0011"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

#: Empresa de la transacción. Vacío o ausente → NULL, que una columna NOT NULL rechaza (F5).
CONTEXTO_TENANT = "NULLIF(current_setting('app.id_tenant', true), '')::bigint"


def upgrade() -> None:
    op.execute(f"""
        CREATE TABLE fashionstore.tenants (
            id_tenant        BIGSERIAL PRIMARY KEY,
            codigo           VARCHAR(60)  NOT NULL,
            nombre           VARCHAR(150) NOT NULL,
            correo_contacto  VARCHAR(255),
            telefono         VARCHAR(30),
            estado           VARCHAR(20)  NOT NULL DEFAULT 'activa',
            creado_en        TIMESTAMPTZ  NOT NULL DEFAULT now(),
            CONSTRAINT uq_tenants_codigo UNIQUE (codigo),
            -- RN03: 3 a 60 caracteres, minúsculas, números y guiones
            CONSTRAINT chk_tenants_codigo CHECK (codigo ~ '^[a-z0-9-]{{3,60}}$'),
            -- RN08
            CONSTRAINT chk_tenants_estado CHECK (estado IN ('activa', 'suspendida', 'baja'))
        );

        CREATE TABLE fashionstore.funcionalidades (
            codigo       VARCHAR(50)  PRIMARY KEY,
            nombre       VARCHAR(100) NOT NULL,
            descripcion  TEXT
        );

        CREATE TABLE fashionstore.planes (
            id_plan                 BIGSERIAL PRIMARY KEY,
            nombre                  VARCHAR(60)   NOT NULL,
            precio_mensual          NUMERIC(10,2) NOT NULL DEFAULT 0,
            max_sucursales_activas  INTEGER       NOT NULL,
            max_empleados           INTEGER,       -- NULL = sin límite (F14)
            activo                  BOOLEAN       NOT NULL DEFAULT true,
            creado_en               TIMESTAMPTZ   NOT NULL DEFAULT now(),
            CONSTRAINT uq_planes_nombre UNIQUE (nombre),
            CONSTRAINT chk_planes_precio CHECK (precio_mensual >= 0),
            CONSTRAINT chk_planes_max_sucursales CHECK (max_sucursales_activas > 0),
            CONSTRAINT chk_planes_max_empleados CHECK (max_empleados IS NULL OR max_empleados > 0)
        );

        CREATE TABLE fashionstore.plan_funcionalidades (
            id_plan               BIGINT      NOT NULL REFERENCES fashionstore.planes(id_plan) ON DELETE CASCADE,
            codigo_funcionalidad  VARCHAR(50) NOT NULL REFERENCES fashionstore.funcionalidades(codigo),
            PRIMARY KEY (id_plan, codigo_funcionalidad)
        );

        CREATE TABLE fashionstore.suscripciones (
            id_suscripcion     BIGSERIAL PRIMARY KEY,
            id_tenant          BIGINT      NOT NULL DEFAULT {CONTEXTO_TENANT}
                               REFERENCES fashionstore.tenants(id_tenant),
            id_plan            BIGINT      NOT NULL REFERENCES fashionstore.planes(id_plan),
            estado             VARCHAR(20) NOT NULL,
            fecha_inicio       DATE        NOT NULL,
            fecha_vencimiento  DATE        NOT NULL,
            creado_en          TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_suscripciones_tenant UNIQUE (id_tenant, id_suscripcion),
            CONSTRAINT chk_suscripciones_estado
                CHECK (estado IN ('prueba', 'activa', 'vencida', 'suspendida', 'cancelada')),
            -- RN13
            CONSTRAINT chk_suscripciones_fechas CHECK (fecha_vencimiento > fecha_inicio)
        );
        -- RN13: como máximo una suscripción vigente por empresa
        CREATE UNIQUE INDEX uq_suscripcion_vigente
            ON fashionstore.suscripciones (id_tenant) WHERE estado IN ('prueba', 'activa');

        CREATE TABLE fashionstore.historial_suscripcion (
            id_historial    BIGSERIAL PRIMARY KEY,
            id_tenant       BIGINT      NOT NULL DEFAULT {CONTEXTO_TENANT},
            id_suscripcion  BIGINT      NOT NULL,
            evento          VARCHAR(30) NOT NULL,
            detalle         JSONB,
            id_usuario      BIGINT REFERENCES fashionstore.usuarios(id_usuario) ON DELETE SET NULL,
            creado_en       TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT fk_historial_suscripcion_tenant FOREIGN KEY (id_tenant, id_suscripcion)
                REFERENCES fashionstore.suscripciones (id_tenant, id_suscripcion) ON DELETE CASCADE,
            -- RN17
            CONSTRAINT chk_historial_suscripcion_evento CHECK (evento IN (
                'alta', 'renovacion', 'cambio_plan', 'suspension', 'vencimiento', 'reactivacion', 'cancelacion'))
        );
        CREATE INDEX idx_historial_suscripcion_tenant ON fashionstore.historial_suscripcion (id_tenant, creado_en DESC);

        CREATE TABLE fashionstore.configuracion_tenant (
            id_tenant                     BIGINT PRIMARY KEY DEFAULT {CONTEXTO_TENANT}
                                          REFERENCES fashionstore.tenants(id_tenant) ON DELETE CASCADE,
            moneda                        CHAR(3)     NOT NULL DEFAULT 'EUR',
            zona_horaria                  VARCHAR(60) NOT NULL DEFAULT 'Europe/Madrid',
            horas_vencimiento_reserva     INTEGER     NOT NULL DEFAULT 24,   -- RN25
            dias_cambio_prenda            INTEGER     NOT NULL DEFAULT 15,   -- RN30
            operacion_offline_habilitada  BOOLEAN     NOT NULL DEFAULT true, -- RN33
            dias_antiguedad_offline       INTEGER     NOT NULL DEFAULT 7,    -- RN41
            actualizado_en                TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT chk_config_horas_reserva CHECK (horas_vencimiento_reserva > 0),
            CONSTRAINT chk_config_dias_cambio CHECK (dias_cambio_prenda >= 0),
            CONSTRAINT chk_config_dias_offline CHECK (dias_antiguedad_offline > 0)
        );

        -- F9: un cliente (cuenta global) se registra en cada empresa en la que compra
        CREATE TABLE fashionstore.cliente_tenant (
            id_tenant      BIGINT      NOT NULL DEFAULT {CONTEXTO_TENANT}
                           REFERENCES fashionstore.tenants(id_tenant),
            id_cliente     BIGINT      NOT NULL REFERENCES fashionstore.clientes(id_cliente) ON DELETE CASCADE,
            registrado_en  TIMESTAMPTZ NOT NULL DEFAULT now(),
            activo         BOOLEAN     NOT NULL DEFAULT true,
            PRIMARY KEY (id_tenant, id_cliente)
        );
        CREATE INDEX idx_cliente_tenant_cliente ON fashionstore.cliente_tenant (id_cliente);
    """)

    # ----- Datos iniciales -----------------------------------------------------------------
    op.execute("""
        INSERT INTO fashionstore.tenants (id_tenant, codigo, nombre, estado)
        VALUES (1, 'fashionstore', 'FASHION STORE', 'activa');
        SELECT setval(pg_get_serial_sequence('fashionstore.tenants', 'id_tenant'), 1, true);

        INSERT INTO fashionstore.funcionalidades (codigo, nombre) VALUES
            ('productos',               'Gestión de productos'),
            ('ventas',                  'Ventas'),
            ('reservas',                'Reservas'),
            ('operacion_offline',       'Operación sin conexión'),
            ('reportes_convencionales', 'Reportes convencionales'),
            ('reportes_ia',             'Reportes generativos con IA');

        -- F14: precio 0,00 y empleados sin límite hasta que el super administrador los fije (P2-CU06)
        INSERT INTO fashionstore.planes (nombre, precio_mensual, max_sucursales_activas, max_empleados)
        VALUES ('Básico', 0, 2, NULL), ('Profesional', 0, 10, NULL);

        INSERT INTO fashionstore.plan_funcionalidades (id_plan, codigo_funcionalidad)
        SELECT p.id_plan, f.codigo
          FROM fashionstore.planes p CROSS JOIN fashionstore.funcionalidades f
         WHERE p.nombre = 'Profesional'
            OR (p.nombre = 'Básico' AND f.codigo <> 'reportes_ia');

        -- F15: FASHION STORE en plan Profesional durante 12 meses
        INSERT INTO fashionstore.suscripciones (id_tenant, id_plan, estado, fecha_inicio, fecha_vencimiento)
        SELECT 1, id_plan, 'activa', DATE '2026-11-08', DATE '2027-11-08'
          FROM fashionstore.planes WHERE nombre = 'Profesional';

        INSERT INTO fashionstore.historial_suscripcion (id_tenant, id_suscripcion, evento, detalle)
        SELECT 1, id_suscripcion, 'alta',
               jsonb_build_object('plan', 'Profesional', 'origen', 'migracion_0012')
          FROM fashionstore.suscripciones WHERE id_tenant = 1;

        INSERT INTO fashionstore.configuracion_tenant (id_tenant) VALUES (1);

        -- F9: todas las fichas de cliente actuales (incluidas las de 3 empleados) quedan
        -- registradas en FASHION STORE para no romper sus ventas, reservas y carritos.
        INSERT INTO fashionstore.cliente_tenant (id_tenant, id_cliente)
        SELECT 1, id_cliente FROM fashionstore.clientes;
    """)


def downgrade() -> None:
    op.execute("""
        DROP TABLE IF EXISTS fashionstore.cliente_tenant;
        DROP TABLE IF EXISTS fashionstore.configuracion_tenant;
        DROP TABLE IF EXISTS fashionstore.historial_suscripcion;
        DROP TABLE IF EXISTS fashionstore.suscripciones;
        DROP TABLE IF EXISTS fashionstore.plan_funcionalidades;
        DROP TABLE IF EXISTS fashionstore.planes;
        DROP TABLE IF EXISTS fashionstore.funcionalidades;
        DROP TABLE IF EXISTS fashionstore.tenants;
    """)
