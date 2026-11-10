"""P2-CU18 · Registrar cambio de prenda.

Spec: `.specs/changes/P2-CU18-cambio-prenda/plan.md` §4.

- `cambios_prenda`: el cambio como documento propio asociado a la venta original (que sigue `pagada`),
  con su comprobante `CAM-AAAA-NNNNN` único por empresa, los valores devuelto y nuevo, la diferencia y
  cómo se cobró o devolvió.
- `cambio_prenda_detalle`: prendas devueltas (con la línea de la venta) y nuevas.

Tablas de empresa: `id_tenant` con el valor por defecto del contexto, `UNIQUE (id_tenant, pk)`, FK
compuestas y política `aislamiento_tenant`. No toca tablas existentes: el código desplegado sigue
funcionando entre la migración y el push (defecto 55).

Revision ID: 0021
Revises: 0020
Create Date: 2026-11-10
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0021"
down_revision: Union[str, None] = "0020"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
ROL_APP = "fashionstore_app"
TENANT = "NULLIF(current_setting('app.id_tenant', true), '')::bigint"
PLATAFORMA = "(current_setting('app.modo_plataforma', true) = 'on')"

TABLAS = {
    "cambios_prenda": "cambios_prenda_id_cambio_seq",
    "cambio_prenda_detalle": "cambio_prenda_detalle_id_cambio_detalle_seq",
}


def upgrade() -> None:
    op.execute(f"""
        CREATE TABLE {S}.cambios_prenda (
            id_cambio           BIGSERIAL PRIMARY KEY,
            id_tenant           BIGINT        NOT NULL DEFAULT {TENANT}
                                CONSTRAINT fk_cambios_prenda_tenant REFERENCES {S}.tenants(id_tenant),
            numero_comprobante  VARCHAR(30)   NOT NULL,
            id_venta            BIGINT        NOT NULL,
            id_sucursal         INTEGER       NOT NULL,
            id_usuario          BIGINT        NOT NULL,
            creado_en           TIMESTAMPTZ   NOT NULL DEFAULT now(),
            valor_devuelto      NUMERIC(12,2) NOT NULL,
            valor_nuevo         NUMERIC(12,2) NOT NULL,
            diferencia          NUMERIC(12,2) NOT NULL,
            metodo_pago         VARCHAR(20),
            monto_recibido      NUMERIC(12,2),
            vuelto              NUMERIC(12,2),
            referencia          VARCHAR(150),
            CONSTRAINT uq_cambios_prenda_tenant_pk UNIQUE (id_tenant, id_cambio),
            CONSTRAINT uq_cambios_prenda_comprobante UNIQUE (id_tenant, numero_comprobante),
            CONSTRAINT chk_cambios_prenda_valores CHECK (
                valor_devuelto >= 0 AND valor_nuevo >= 0 AND diferencia = valor_nuevo - valor_devuelto),
            CONSTRAINT chk_cambios_prenda_metodo CHECK (metodo_pago IS NULL OR metodo_pago IN
                ('efectivo', 'tarjeta_debito', 'tarjeta_credito', 'qr', 'transferencia')),
            CONSTRAINT fk_cambios_prenda_venta FOREIGN KEY (id_tenant, id_venta)
                REFERENCES {S}.ventas (id_tenant, id_venta),
            CONSTRAINT fk_cambios_prenda_sucursal FOREIGN KEY (id_tenant, id_sucursal)
                REFERENCES {S}.sucursales (id_tenant, id_sucursal),
            CONSTRAINT fk_cambios_prenda_usuario FOREIGN KEY (id_tenant, id_usuario)
                REFERENCES {S}.usuarios (id_tenant, id_usuario)
        )
    """)
    op.execute(f"CREATE INDEX idx_cambios_prenda_venta ON {S}.cambios_prenda (id_tenant, id_venta)")
    op.execute(f"CREATE INDEX idx_cambios_prenda_sucursal ON {S}.cambios_prenda (id_tenant, id_sucursal, creado_en)")

    op.execute(f"""
        CREATE TABLE {S}.cambio_prenda_detalle (
            id_cambio_detalle   BIGSERIAL PRIMARY KEY,
            id_tenant           BIGINT        NOT NULL DEFAULT {TENANT}
                                CONSTRAINT fk_cambio_prenda_detalle_tenant REFERENCES {S}.tenants(id_tenant),
            id_cambio           BIGINT        NOT NULL,
            tipo                VARCHAR(10)   NOT NULL,
            id_venta_detalle    BIGINT,
            id_variante         BIGINT        NOT NULL,
            cantidad            INTEGER       NOT NULL,
            precio_unitario     NUMERIC(12,2) NOT NULL,
            subtotal            NUMERIC(12,2) NOT NULL,
            CONSTRAINT uq_cambio_prenda_detalle_tenant_pk UNIQUE (id_tenant, id_cambio_detalle),
            CONSTRAINT chk_cambio_prenda_detalle_tipo CHECK (tipo IN ('devuelta', 'nueva')),
            CONSTRAINT chk_cambio_prenda_detalle_linea CHECK ((tipo = 'devuelta') = (id_venta_detalle IS NOT NULL)),
            CONSTRAINT chk_cambio_prenda_detalle_cantidad CHECK (cantidad > 0 AND precio_unitario >= 0),
            CONSTRAINT fk_cambio_prenda_detalle_cambio FOREIGN KEY (id_tenant, id_cambio)
                REFERENCES {S}.cambios_prenda (id_tenant, id_cambio) ON DELETE CASCADE,
            CONSTRAINT fk_cambio_prenda_detalle_linea FOREIGN KEY (id_tenant, id_venta_detalle)
                REFERENCES {S}.venta_detalle (id_tenant, id_venta_detalle),
            CONSTRAINT fk_cambio_prenda_detalle_variante FOREIGN KEY (id_tenant, id_variante)
                REFERENCES {S}.variantes_producto (id_tenant, id_variante)
        )
    """)
    op.execute(f"CREATE INDEX idx_cambio_prenda_detalle_linea ON {S}.cambio_prenda_detalle (id_tenant, id_venta_detalle)")

    estandar = f"id_tenant = {TENANT} OR {PLATAFORMA}"
    for tabla in TABLAS:
        op.execute(f"ALTER TABLE {S}.{tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"CREATE POLICY aislamiento_tenant ON {S}.{tabla} USING ({estandar}) WITH CHECK ({estandar})")

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
    op.execute(f"DROP TABLE IF EXISTS {S}.cambio_prenda_detalle")
    op.execute(f"DROP TABLE IF EXISTS {S}.cambios_prenda")
