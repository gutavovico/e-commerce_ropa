"""Semilla de promociones y bonos atelier para CU15

La tabla `fashionstore.promociones` estaba vacia, de modo que el campo
"CODIGO DE INVITACION O BONO ATELIER" de la pantalla de Bolsa de Compra no tenia nada contra lo
que validar y el descuento nunca podia demostrarse.

Se siembran dos promociones reales:

1. `MAISON-2025` — bono de bienvenida de alcance global, 10 % con tope de 200 EUR y 500 usos.
2. Membresia Prive — promocion por porcentaje ligada a productos concretos a traves de
   `promocion_producto`, que es el mecanismo que ya consume CU05 para pintar el precio tachado.
   Se asocia a las prendas mas representativas del catalogo sembrado.

Todos los importes son inserciones de datos: esta revision no altera el esquema.

Revision ID: 0010
Revises: 0009
Create Date: 2026-09-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0010"
down_revision: Union[str, None] = "0009"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 1. Bono de invitacion global (cupon canjeable en el checkout)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO fashionstore.promociones (
            nombre, descripcion, porcentaje_descuento,
            fecha_inicio, fecha_fin, estado_activo,
            codigo_cupon, tipo_descuento, valor_descuento, tope_descuento,
            limite_usos, usos_actuales, alcance
        )
        SELECT
            'Bono Atelier de Bienvenida',
            'Invitacion de cortesia para clientes de la maison. 10 % sobre el importe de la orden.',
            10.00,
            now() - INTERVAL '1 day',
            now() + INTERVAL '365 days',
            TRUE,
            'MAISON-2025',
            'porcentaje',
            10.00,
            200.00,
            500,
            0,
            'global'
        WHERE NOT EXISTS (
            SELECT 1 FROM fashionstore.promociones WHERE codigo_cupon = 'MAISON-2025'
        );
    """)

    # ------------------------------------------------------------------
    # 2. Membresia Prive: descuento por producto (precio tachado en catalogo)
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO fashionstore.promociones (
            nombre, descripcion, porcentaje_descuento,
            fecha_inicio, fecha_fin, estado_activo,
            tipo_descuento, valor_descuento, usos_actuales, alcance
        )
        SELECT
            'Membresia Prive',
            'Beneficio exclusivo de la membresia Prive sobre piezas seleccionadas de alta costura.',
            15.00,
            now() - INTERVAL '1 day',
            now() + INTERVAL '365 days',
            TRUE,
            'porcentaje',
            15.00,
            0,
            'producto'
        WHERE NOT EXISTS (
            SELECT 1 FROM fashionstore.promociones WHERE nombre = 'Membresia Prive'
        );
    """)

    # Asociar la membresia a las 3 prendas activas mas costosas del catalogo real.
    # Se resuelve por consulta y no por identificadores fijos: sembrar ids inventados
    # romperia la regla de dominio "cero datos inventados".
    op.execute("""
        INSERT INTO fashionstore.promocion_producto (id_promocion, id_producto)
        SELECT p.id_promocion, prod.id_producto
        FROM fashionstore.promociones p
        CROSS JOIN LATERAL (
            SELECT id_producto
            FROM fashionstore.productos
            WHERE activo = TRUE
            ORDER BY precio_base DESC
            LIMIT 3
        ) prod
        WHERE p.nombre = 'Membresia Prive'
        ON CONFLICT DO NOTHING;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM fashionstore.promocion_producto
        WHERE id_promocion IN (
            SELECT id_promocion FROM fashionstore.promociones
            WHERE nombre = 'Membresia Prive'
        );
    """)
    op.execute("""
        DELETE FROM fashionstore.promociones
        WHERE codigo_cupon = 'MAISON-2025' OR nombre = 'Membresia Prive';
    """)
