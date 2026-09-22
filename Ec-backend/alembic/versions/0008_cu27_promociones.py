"""Extension y normalizacion de la tabla fashionstore.promociones para CU27.

Revision ID: 0008
Revises: 0007
Create Date: 2026-09-21
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Normalizar columna activa -> estado_activo
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'promociones' AND column_name = 'activa'
            ) AND NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'promociones' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.promociones RENAME COLUMN activa TO estado_activo;
            ELSIF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'fashionstore' AND table_name = 'promociones' AND column_name = 'estado_activo'
            ) THEN
                ALTER TABLE fashionstore.promociones ADD COLUMN estado_activo BOOLEAN NOT NULL DEFAULT TRUE;
            END IF;
        END $$;
    """)

    # 2. Agregar columnas faltantes
    op.execute("""
        ALTER TABLE fashionstore.promociones
        ADD COLUMN IF NOT EXISTS codigo_cupon VARCHAR(50),
        ADD COLUMN IF NOT EXISTS tipo_descuento VARCHAR(20) NOT NULL DEFAULT 'porcentaje',
        ADD COLUMN IF NOT EXISTS valor_descuento NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
        ADD COLUMN IF NOT EXISTS tope_descuento NUMERIC(10, 2),
        ADD COLUMN IF NOT EXISTS limite_usos INTEGER,
        ADD COLUMN IF NOT EXISTS usos_actuales INTEGER NOT NULL DEFAULT 0,
        ADD COLUMN IF NOT EXISTS alcance VARCHAR(20) NOT NULL DEFAULT 'global',
        ADD COLUMN IF NOT EXISTS id_categoria INTEGER REFERENCES fashionstore.categorias(id_categoria) ON DELETE SET NULL,
        ADD COLUMN IF NOT EXISTS id_producto BIGINT REFERENCES fashionstore.productos(id_producto) ON DELETE SET NULL,
        ADD COLUMN IF NOT EXISTS creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now();
    """)

    # 3. Convertir fecha_inicio y fecha_fin a TIMESTAMPTZ
    op.execute("""
        ALTER TABLE fashionstore.promociones 
        ALTER COLUMN fecha_inicio TYPE TIMESTAMPTZ USING fecha_inicio::TIMESTAMPTZ,
        ALTER COLUMN fecha_fin TYPE TIMESTAMPTZ USING fecha_fin::TIMESTAMPTZ;
    """)

    # 4. Ajustar porcentaje_descuento heredado hacia valor_descuento si existiera
    op.execute("""
        UPDATE fashionstore.promociones
        SET valor_descuento = COALESCE(porcentaje_descuento, 0.00)
        WHERE valor_descuento = 0.00 AND porcentaje_descuento IS NOT NULL;
    """)

    # 5. Eliminar constraints anonimos previos de fechas si existen
    op.execute("""
        DO $$
        DECLARE
            c_name text;
        BEGIN
            FOR c_name IN (
                SELECT conname 
                FROM pg_constraint 
                WHERE conrelid = 'fashionstore.promociones'::regclass 
                AND contype = 'c'
            ) LOOP
                EXECUTE 'ALTER TABLE fashionstore.promociones DROP CONSTRAINT IF EXISTS ' || quote_ident(c_name);
            END LOOP;
        END $$;
    """)

    # 6. Agregar constraints nombrados y validados
    op.execute("""
        ALTER TABLE fashionstore.promociones
        ADD CONSTRAINT chk_promociones_fechas_orden CHECK (fecha_fin > fecha_inicio),
        ADD CONSTRAINT chk_promociones_tipo_descuento CHECK (tipo_descuento IN ('porcentaje', 'monto_fijo')),
        ADD CONSTRAINT chk_promociones_valor_positivo CHECK (valor_descuento > 0),
        ADD CONSTRAINT chk_promociones_porcentaje_tope CHECK (
            tipo_descuento != 'porcentaje' OR (valor_descuento >= 1.00 AND valor_descuento <= 100.00)
        ),
        ADD CONSTRAINT chk_promociones_tope_positivo CHECK (tope_descuento IS NULL OR tope_descuento >= 0),
        ADD CONSTRAINT chk_promociones_usos_no_negativos CHECK (usos_actuales >= 0),
        ADD CONSTRAINT chk_promociones_limite_positivo CHECK (limite_usos IS NULL OR limite_usos > 0),
        ADD CONSTRAINT chk_promociones_alcance_tipo CHECK (alcance IN ('global', 'categoria', 'producto'));
    """)

    # 7. Indice unico para codigo_cupon insensible a mayusculas
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_promociones_codigo_cupon_lower 
        ON fashionstore.promociones (LOWER(TRIM(codigo_cupon))) 
        WHERE codigo_cupon IS NOT NULL;
    """)

    # 8. Indices auxiliares de optimizacion
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_promociones_fechas_vigencia 
        ON fashionstore.promociones (fecha_inicio, fecha_fin, estado_activo);

        CREATE INDEX IF NOT EXISTS ix_promociones_alcance 
        ON fashionstore.promociones (alcance, id_categoria, id_producto);
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS fashionstore.ix_promociones_alcance;")
    op.execute("DROP INDEX IF EXISTS fashionstore.ix_promociones_fechas_vigencia;")
    op.execute("DROP INDEX IF EXISTS fashionstore.uq_promociones_codigo_cupon_lower;")
    op.execute("""
        ALTER TABLE fashionstore.promociones
        DROP CONSTRAINT IF EXISTS chk_promociones_alcance_tipo,
        DROP CONSTRAINT IF EXISTS chk_promociones_limite_positivo,
        DROP CONSTRAINT IF EXISTS chk_promociones_usos_no_negativos,
        DROP CONSTRAINT IF EXISTS chk_promociones_tope_positivo,
        DROP CONSTRAINT IF EXISTS chk_promociones_porcentaje_tope,
        DROP CONSTRAINT IF EXISTS chk_promociones_valor_positivo,
        DROP CONSTRAINT IF EXISTS chk_promociones_tipo_descuento,
        DROP CONSTRAINT IF EXISTS chk_promociones_fechas_orden;
    """)
    op.execute("""
        ALTER TABLE fashionstore.promociones
        DROP COLUMN IF EXISTS actualizado_en,
        DROP COLUMN IF EXISTS creado_en,
        DROP COLUMN IF EXISTS id_producto,
        DROP COLUMN IF EXISTS id_categoria,
        DROP COLUMN IF EXISTS alcance,
        DROP COLUMN IF EXISTS usos_actuales,
        DROP COLUMN IF EXISTS limite_usos,
        DROP COLUMN IF EXISTS tope_descuento,
        DROP COLUMN IF EXISTS valor_descuento,
        DROP COLUMN IF EXISTS tipo_descuento,
        DROP COLUMN IF EXISTS codigo_cupon;
    """)
