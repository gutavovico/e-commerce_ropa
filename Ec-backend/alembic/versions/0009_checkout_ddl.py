"""DDL aditivo para CU11/CU15: trazabilidad por linea, datos de entrega y comprobantes

Cambios aprobados en `.specs/changes/change-carrito-checkout.md` (secciones 1.1, 1.2 y 1.3):

1. `venta_detalle.id_sucursal` — conserva desde que boutique se expide cada prenda. El carrito
   ya lo registra por linea (`carrito_detalle.id_sucursal`), pero al convertirlo en venta ese
   dato se perdia porque `ventas.id_sucursal` es una unica sucursal de cabecera.
2. Campos de entrega y cupon en `ventas` — `tipo_entrega`, `id_sucursal_retiro`,
   `direccion_envio` e `id_promocion`. Sin ellos la orden no es reproducible y CU16 no sabria
   a donde despachar ni que promocion se aplico.
3. `seq_comprobante_venta` — secuencia para `numero_comprobante`. Calcularlo con `MAX(...)+1`
   es una condicion de carrera clasica.
4. Reemplazo de `fn_descontar_inventario_venta` — el trigger descontaba `cantidad_disponible`
   en el `INSERT` de `venta_detalle`, sin consultar `ventas.estado` y resolviendo el inventario
   por la sucursal de la *cabecera*. Con un carrito multi-sucursal lanzaba `RAISE EXCEPTION` y
   abortaba el checkout completo. La retencion de stock pasa a `CheckoutServicio`, de forma
   transaccional y con auditoria en `movimientos_inventario`, replicando el patron de CU12.

ADVERTENCIA SOBRE LA CADENA DE MIGRACIONES
------------------------------------------
La base desplegada declara `alembic_version = '0008'`, pero este repositorio solo contiene los
archivos `0001`, `0002` y `0003`: las revisiones 0004 a 0008 no estan versionadas aqui. Por eso
`alembic upgrade head` NO puede resolver esta cadena y esta revision se aplico ejecutando su DDL
de forma directa e idempotente contra PostgreSQL, actualizando despues `alembic_version` a '0009'.

Este archivo es el registro reversible y auditable del cambio. Reconciliar la cadena completa de
migraciones con el esquema real sigue siendo deuda abierta (ver `CHANGELOG.md`, seccion
"Deuda Tecnica Registrada"); es una decision de esquema pendiente de autorizacion.

Revision ID: 0009
Revises: 0008
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0009"
down_revision: Union[str, None] = "0008"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Trazabilidad de la sucursal de expedicion por linea de venta
    # ------------------------------------------------------------------
    op.execute("""
        ALTER TABLE fashionstore.venta_detalle
        ADD COLUMN IF NOT EXISTS id_sucursal INTEGER
            REFERENCES fashionstore.sucursales(id_sucursal);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_venta_detalle_id_sucursal
        ON fashionstore.venta_detalle (id_sucursal);
    """)

    # ------------------------------------------------------------------
    # 2. Datos de entrega y promocion aplicada en la cabecera de la venta
    # ------------------------------------------------------------------
    op.execute("""
        ALTER TABLE fashionstore.ventas
        ADD COLUMN IF NOT EXISTS tipo_entrega VARCHAR(20) NOT NULL DEFAULT 'domicilio',
        ADD COLUMN IF NOT EXISTS id_sucursal_retiro INTEGER
            REFERENCES fashionstore.sucursales(id_sucursal),
        ADD COLUMN IF NOT EXISTS direccion_envio TEXT,
        ADD COLUMN IF NOT EXISTS id_promocion INTEGER
            REFERENCES fashionstore.promociones(id_promocion);
    """)

    # Solo dos modalidades de entrega son validas; se fija en la base para que ningun
    # camino de escritura pueda introducir un valor fuera de contrato.
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint
                WHERE conname = 'ck_ventas_tipo_entrega'
            ) THEN
                ALTER TABLE fashionstore.ventas
                ADD CONSTRAINT ck_ventas_tipo_entrega
                CHECK (tipo_entrega IN ('domicilio', 'recogida_boutique'));
            END IF;
        END $$;
    """)

    # ------------------------------------------------------------------
    # 3. Secuencia para numero_comprobante (unicidad bajo concurrencia)
    # ------------------------------------------------------------------
    op.execute("CREATE SEQUENCE IF NOT EXISTS fashionstore.seq_comprobante_venta START 1;")

    # ------------------------------------------------------------------
    # 4. Neutralizacion del descuento automatico de inventario
    # ------------------------------------------------------------------
    # La funcion se conserva (otros flujos podrian referenciarla) pero deja de mutar stock.
    # El trigger se elimina: `CheckoutServicio` es ahora el unico responsable del movimiento,
    # dentro de la misma transaccion y registrando el usuario responsable.
    op.execute("DROP TRIGGER IF EXISTS trg_descontar_inventario ON fashionstore.venta_detalle;")
    op.execute("""
        CREATE OR REPLACE FUNCTION fashionstore.fn_descontar_inventario_venta()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        BEGIN
            -- Neutralizada el 2026-09-22 (ver .specs/changes/change-carrito-checkout.md, 1.1).
            -- El descuento de inventario lo realiza CheckoutServicio de forma transaccional:
            -- valida suficiencia, respeta la sucursal de cada linea, filtra por temporada
            -- vigente y registra el usuario responsable en movimientos_inventario.
            RETURN NEW;
        END;
        $function$;
    """)


def downgrade() -> None:
    # Restaura el trigger original tal y como estaba en la base antes de esta revision.
    op.execute("""
        CREATE OR REPLACE FUNCTION fashionstore.fn_descontar_inventario_venta()
        RETURNS trigger
        LANGUAGE plpgsql
        AS $function$
        DECLARE
            v_id_inventario BIGINT;
        BEGIN
            SELECT inv.id_inventario INTO v_id_inventario
            FROM fashionstore.inventario_sucursal inv
            JOIN fashionstore.ventas v ON v.id_venta = NEW.id_venta
            WHERE inv.id_variante = NEW.id_variante
              AND inv.id_sucursal = v.id_sucursal
            LIMIT 1;

            IF v_id_inventario IS NULL THEN
                RAISE EXCEPTION
                    'No existe inventario para la variante % en la sucursal de la venta %',
                    NEW.id_variante, NEW.id_venta;
            END IF;

            UPDATE fashionstore.inventario_sucursal
            SET cantidad_disponible = cantidad_disponible - NEW.cantidad
            WHERE id_inventario = v_id_inventario;

            INSERT INTO fashionstore.movimientos_inventario (
                id_inventario, tipo_movimiento, cantidad, referencia_documento
            )
            VALUES (
                v_id_inventario, 'venta', -NEW.cantidad,
                'VENTA-' || NEW.id_venta
            );

            RETURN NEW;
        END;
        $function$;
    """)
    op.execute("""
        CREATE TRIGGER trg_descontar_inventario
        AFTER INSERT ON fashionstore.venta_detalle
        FOR EACH ROW EXECUTE FUNCTION fashionstore.fn_descontar_inventario_venta();
    """)

    op.execute("DROP SEQUENCE IF EXISTS fashionstore.seq_comprobante_venta;")

    op.execute("""
        ALTER TABLE fashionstore.ventas
        DROP CONSTRAINT IF EXISTS ck_ventas_tipo_entrega;
    """)
    op.execute("""
        ALTER TABLE fashionstore.ventas
        DROP COLUMN IF EXISTS id_promocion,
        DROP COLUMN IF EXISTS direccion_envio,
        DROP COLUMN IF EXISTS id_sucursal_retiro,
        DROP COLUMN IF EXISTS tipo_entrega;
    """)

    op.execute("DROP INDEX IF EXISTS fashionstore.ix_venta_detalle_id_sucursal;")
    op.execute("ALTER TABLE fashionstore.venta_detalle DROP COLUMN IF EXISTS id_sucursal;")
