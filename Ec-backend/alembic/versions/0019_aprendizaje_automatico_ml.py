"""P2-CU23, P2-CU24 y P2-CU25 · Aprendizaje automático (datasets, modelos supervisados/no supervisados, predicciones y segmentos de clientes).

Spec: `.specs/changes/P2-CU23-CU25-aprendizaje-ml/spec.md` (RF34, RF35, RN49, RN50, RN51).

- Crea `fashionstore.datasets_ml`, `fashionstore.modelos_ml`, `fashionstore.predicciones_ml` y `fashionstore.segmentos_clientes_ml`
  con aislamiento por empresa (`id_tenant` + políticas Row Level Security) y montos monetarios en Bolivianos (`Bs. / BOB`).

Revision ID: 0019
Revises: 0018
Create Date: 2026-11-09
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0019"
down_revision: Union[str, None] = "0018"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"

TABLAS_ML = (
    "datasets_ml",
    "modelos_ml",
    "predicciones_ml",
    "segmentos_clientes_ml",
)


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {S}.datasets_ml (
            id_dataset              BIGSERIAL PRIMARY KEY,
            id_tenant               INTEGER NOT NULL DEFAULT NULLIF(current_setting('app.id_tenant', true), '')::integer
                                    REFERENCES {S}.tenants(id_tenant) ON DELETE CASCADE,
            nombre                  VARCHAR(140) NOT NULL,
            origen                  VARCHAR(20) NOT NULL CHECK (origen IN ('sintetico', 'real', 'mixto')),
            cantidad_registros      INTEGER NOT NULL DEFAULT 0,
            variables_seleccionadas JSONB NOT NULL DEFAULT '[]'::jsonb,
            parametros_generacion   JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            resumen_preprocesamiento JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            muestra_datos           JSONB NOT NULL DEFAULT '[]'::jsonb,
            creado_por              BIGINT REFERENCES {S}.usuarios(id_usuario) ON DELETE SET NULL,
            creado_en               TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {S}.modelos_ml (
            id_modelo               BIGSERIAL PRIMARY KEY,
            id_tenant               INTEGER NOT NULL DEFAULT NULLIF(current_setting('app.id_tenant', true), '')::integer
                                    REFERENCES {S}.tenants(id_tenant) ON DELETE CASCADE,
            id_dataset              BIGINT NOT NULL REFERENCES {S}.datasets_ml(id_dataset) ON DELETE CASCADE,
            nombre                  VARCHAR(140) NOT NULL,
            tipo_modelo             VARCHAR(25) NOT NULL CHECK (tipo_modelo IN ('supervisado', 'no_supervisado')),
            algoritmo               VARCHAR(80) NOT NULL,
            variable_objetivo       VARCHAR(80),
            variables_entrada       JSONB NOT NULL DEFAULT '[]'::jsonb,
            origen_datos            VARCHAR(20) NOT NULL CHECK (origen_datos IN ('sintetico', 'real', 'mixto')),
            estado                  VARCHAR(25) NOT NULL DEFAULT 'evaluado'
                                    CHECK (estado IN ('entrenando', 'evaluado', 'activo', 'archivado', 'fallido')),
            activo                  BOOLEAN NOT NULL DEFAULT false,
            motivo_error            TEXT,
            metricas_entrenamiento  JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            metricas_validacion     JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            metricas_prueba         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            creado_por              BIGINT REFERENCES {S}.usuarios(id_usuario) ON DELETE SET NULL,
            creado_en               TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en          TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {S}.predicciones_ml (
            id_prediccion           BIGSERIAL PRIMARY KEY,
            id_tenant               INTEGER NOT NULL DEFAULT NULLIF(current_setting('app.id_tenant', true), '')::integer
                                    REFERENCES {S}.tenants(id_tenant) ON DELETE CASCADE,
            id_modelo               BIGINT NOT NULL REFERENCES {S}.modelos_ml(id_modelo) ON DELETE CASCADE,
            id_producto             BIGINT,
            nombre_producto         VARCHAR(150) NOT NULL,
            id_sucursal             BIGINT,
            nombre_sucursal         VARCHAR(120) NOT NULL,
            periodo                 VARCHAR(40) NOT NULL,
            demanda_esperada        INTEGER NOT NULL DEFAULT 0,
            ingresos_esperados_bob  NUMERIC(14, 2) NOT NULL DEFAULT 0.00,
            probabilidad            NUMERIC(5, 4) NOT NULL DEFAULT 0.5000
                                    CHECK (probabilidad >= 0.0000 AND probabilidad <= 1.0000),
            nivel_confianza         VARCHAR(25) NOT NULL DEFAULT 'ALTA',
            creado_en               TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {S}.segmentos_clientes_ml (
            id_segmento             BIGSERIAL PRIMARY KEY,
            id_tenant               INTEGER NOT NULL DEFAULT NULLIF(current_setting('app.id_tenant', true), '')::integer
                                    REFERENCES {S}.tenants(id_tenant) ON DELETE CASCADE,
            id_modelo               BIGINT NOT NULL REFERENCES {S}.modelos_ml(id_modelo) ON DELETE CASCADE,
            codigo_grupo            VARCHAR(40) NOT NULL,
            nombre_grupo            VARCHAR(120) NOT NULL,
            descripcion             TEXT NOT NULL,
            cantidad_clientes       INTEGER NOT NULL DEFAULT 0,
            caracteristicas         JSONB NOT NULL DEFAULT '{{}}'::jsonb,
            clientes_muestra        JSONB NOT NULL DEFAULT '[]'::jsonb,
            creado_en               TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    for tabla in TABLAS_ML:
        op.execute(f"CREATE INDEX IF NOT EXISTS ix_{tabla}_id_tenant ON {S}.{tabla} (id_tenant)")
        op.execute(f"ALTER TABLE {S}.{tabla} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {S}.{tabla} FORCE ROW LEVEL SECURITY")
        op.execute(f"DROP POLICY IF EXISTS aislamiento_tenant_{tabla} ON {S}.{tabla}")
        op.execute(
            f"""
            CREATE POLICY aislamiento_tenant_{tabla} ON {S}.{tabla}
                USING (
                    current_setting('app.modo_plataforma', true) = 'on'
                    OR id_tenant = NULLIF(current_setting('app.id_tenant', true), '')::integer
                )
                WITH CHECK (
                    current_setting('app.modo_plataforma', true) = 'on'
                    OR id_tenant = NULLIF(current_setting('app.id_tenant', true), '')::integer
                )
            """
        )

    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashionstore_app') THEN
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON {S}.datasets_ml, {S}.modelos_ml, {S}.predicciones_ml, {S}.segmentos_clientes_ml TO fashionstore_app';
                EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE {S}.datasets_ml_id_dataset_seq, {S}.modelos_ml_id_modelo_seq, {S}.predicciones_ml_id_prediccion_seq, {S}.segmentos_clientes_ml_id_segmento_seq TO fashionstore_app';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(f"DROP TABLE IF EXISTS {S}.segmentos_clientes_ml")
    op.execute(f"DROP TABLE IF EXISTS {S}.predicciones_ml")
    op.execute(f"DROP TABLE IF EXISTS {S}.modelos_ml")
    op.execute(f"DROP TABLE IF EXISTS {S}.datasets_ml")

