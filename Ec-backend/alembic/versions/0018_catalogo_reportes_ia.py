"""P2-CU22 y P2-CU21 · Catálogo de reportes permitidos y trazabilidad de solicitudes de reportes con IA.

Spec: `.specs/changes/P2-CU22-CU21-reportes-ia/spec.md` (RF32, RF33, RN44–RN48).

- Crea la tabla global `fashionstore.catalogo_reportes_ia` y siembra de forma idempotente 4 reportes
  permitidos iniciales (`ventas_por_sucursal`, `top_productos_vendidos`, `inventario_por_sucursal`,
  `reservas_por_estado_sucursal`).
- Amplía `fashionstore.solicitudes_reporte_ia` con `estado`, `interpretacion`, `formato_visualizacion`,
  `mensaje_estado` y `exportaciones`.

Revision ID: 0018
Revises: 0017
Create Date: 2026-11-09
"""

import json
from typing import Sequence, Union

from alembic import op

revision: str = "0018"
down_revision: Union[str, None] = "0017"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"

REPORTES_SEMILLA = [
    {
        "codigo": "ventas_por_sucursal",
        "nombre": "Ventas e ingresos por sucursal y período",
        "descripcion": "Consolidado de órdenes pagadas, unidades e ingresos en Bolivianos (Bs. / BOB) agrupado por sucursal.",
        "vista_origen": "vw_ventas_por_sucursal",
        "metricas": [
            {
                "codigo": "cantidad_ventas",
                "etiqueta": "Órdenes Pagadas",
                "expresion": "COUNT(v.id_venta)",
                "es_monetaria": False,
            },
            {
                "codigo": "ingresos_totales",
                "etiqueta": "Ingresos Totales (Bs.)",
                "expresion": "COALESCE(SUM(v.total), 0)",
                "es_monetaria": True,
            },
            {
                "codigo": "ticket_promedio",
                "etiqueta": "Ticket Promedio (Bs.)",
                "expresion": "COALESCE(AVG(v.total), 0)",
                "es_monetaria": True,
            },
        ],
        "dimensiones": [
            {
                "codigo": "sucursal",
                "etiqueta": "Sucursal",
                "expresion": "s.nombre",
            }
        ],
        "filtros_permitidos": ["fecha_inicio", "fecha_fin", "id_sucursal", "moneda"],
        "tipos_grafico": ["tabla", "barras", "torta", "linea"],
        "ejemplos_consulta": [
            "Ventas de este mes agrupadas por sucursal en bolivianos",
            "Ingresos por sucursal de los últimos 30 días en gráfico de barras",
        ],
    },
    {
        "codigo": "top_productos_vendidos",
        "nombre": "Ranking de productos más vendidos",
        "descripcion": "Top de prendas con mayor volumen de unidades vendidas y facturación en Bolivianos (Bs. / BOB).",
        "vista_origen": "ranking_productos",
        "metricas": [
            {
                "codigo": "unidades_vendidas",
                "etiqueta": "Unidades Vendidas",
                "expresion": "COALESCE(SUM(vd.cantidad), 0)",
                "es_monetaria": False,
            },
            {
                "codigo": "ingresos_producto",
                "etiqueta": "Ingresos Generados (Bs.)",
                "expresion": "COALESCE(SUM(vd.cantidad * vd.precio_unitario), 0)",
                "es_monetaria": True,
            },
        ],
        "dimensiones": [
            {
                "codigo": "producto",
                "etiqueta": "Prenda",
                "expresion": "p.nombre",
            },
            {
                "codigo": "categoria",
                "etiqueta": "Categoría",
                "expresion": "c.nombre",
            },
        ],
        "filtros_permitidos": [
            "fecha_inicio",
            "fecha_fin",
            "id_sucursal",
            "id_categoria",
            "id_producto",
            "moneda",
        ],
        "tipos_grafico": ["tabla", "barras", "torta"],
        "ejemplos_consulta": [
            "Top 10 productos más vendidos este mes",
            "Prendas con mayores ingresos en bolivianos en gráfico de torta",
        ],
    },
    {
        "codigo": "inventario_por_sucursal",
        "nombre": "Existencias y valorización de inventario por sucursal",
        "descripcion": "Stock disponible, unidades reservadas y valorización de existencias en Bolivianos (Bs. / BOB) por boutique.",
        "vista_origen": "vw_inventario_consolidado",
        "metricas": [
            {
                "codigo": "stock_disponible",
                "etiqueta": "Unidades Disponibles",
                "expresion": "COALESCE(SUM(inv.cantidad_disponible), 0)",
                "es_monetaria": False,
            },
            {
                "codigo": "stock_reservado",
                "etiqueta": "Unidades Reservadas",
                "expresion": "COALESCE(SUM(inv.cantidad_reservada), 0)",
                "es_monetaria": False,
            },
            {
                "codigo": "valor_inventario",
                "etiqueta": "Valor Inventario (Bs.)",
                "expresion": "COALESCE(SUM(inv.cantidad_disponible * p.precio_venta), 0)",
                "es_monetaria": True,
            },
        ],
        "dimensiones": [
            {
                "codigo": "sucursal",
                "etiqueta": "Sucursal",
                "expresion": "s.nombre",
            },
            {
                "codigo": "categoria",
                "etiqueta": "Categoría",
                "expresion": "c.nombre",
            },
        ],
        "filtros_permitidos": ["id_sucursal", "id_categoria", "id_producto", "moneda"],
        "tipos_grafico": ["tabla", "barras", "torta"],
        "ejemplos_consulta": [
            "Inventario disponible y valorizado por sucursal",
            "Existencias actuales de prendas agrupadas por sucursal",
        ],
    },
    {
        "codigo": "reservas_por_estado_sucursal",
        "nombre": "Estado de reservas omnicanal por sucursal",
        "descripcion": "Distribución de reservas por estado operativo y sucursal de atención.",
        "vista_origen": "vw_reservas_pendientes",
        "metricas": [
            {
                "codigo": "total_reservas",
                "etiqueta": "Cantidad de Reservas",
                "expresion": "COUNT(r.id_reserva)",
                "es_monetaria": False,
            },
            {
                "codigo": "prendas_reservadas",
                "etiqueta": "Prendas Reservadas",
                "expresion": "COALESCE(SUM(rd.cantidad), 0)",
                "es_monetaria": False,
            },
        ],
        "dimensiones": [
            {
                "codigo": "sucursal",
                "etiqueta": "Sucursal",
                "expresion": "s.nombre",
            },
            {
                "codigo": "estado",
                "etiqueta": "Estado de Reserva",
                "expresion": "r.estado::text",
            },
        ],
        "filtros_permitidos": ["fecha_inicio", "fecha_fin", "id_sucursal"],
        "tipos_grafico": ["tabla", "barras", "torta", "linea"],
        "ejemplos_consulta": [
            "Reservas del mes agrupadas por sucursal y estado",
            "Cantidad de reservas pendientes por sucursal",
        ],
    },
]


def upgrade() -> None:
    op.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {S}.catalogo_reportes_ia (
            id_reporte_catalogo BIGSERIAL PRIMARY KEY,
            codigo              VARCHAR(60) NOT NULL UNIQUE,
            nombre              VARCHAR(120) NOT NULL,
            descripcion         TEXT,
            vista_origen        VARCHAR(80) NOT NULL,
            metricas            JSONB NOT NULL DEFAULT '[]'::jsonb,
            dimensiones         JSONB NOT NULL DEFAULT '[]'::jsonb,
            filtros_permitidos  JSONB NOT NULL DEFAULT '[]'::jsonb,
            tipos_grafico       JSONB NOT NULL DEFAULT '["tabla","barras"]'::jsonb,
            ejemplos_consulta   JSONB NOT NULL DEFAULT '[]'::jsonb,
            activo              BOOLEAN NOT NULL DEFAULT true,
            creado_en           TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
        )
        """
    )

    for rep in REPORTES_SEMILLA:
        metricas_json = json.dumps(rep["metricas"], ensure_ascii=False).replace("'", "''")
        dim_json = json.dumps(rep["dimensiones"], ensure_ascii=False).replace("'", "''")
        filtros_json = json.dumps(rep["filtros_permitidos"], ensure_ascii=False).replace("'", "''")
        graficos_json = json.dumps(rep["tipos_grafico"], ensure_ascii=False).replace("'", "''")
        ejemplos_json = json.dumps(rep["ejemplos_consulta"], ensure_ascii=False).replace("'", "''")
        nombre = rep["nombre"].replace("'", "''")
        desc = rep["descripcion"].replace("'", "''")
        op.execute(
            f"""
            INSERT INTO {S}.catalogo_reportes_ia (
                codigo, nombre, descripcion, vista_origen,
                metricas, dimensiones, filtros_permitidos, tipos_grafico, ejemplos_consulta, activo
            )
            VALUES (
                '{rep["codigo"]}', '{nombre}', '{desc}', '{rep["vista_origen"]}',
                '{metricas_json}'::jsonb, '{dim_json}'::jsonb, '{filtros_json}'::jsonb,
                '{graficos_json}'::jsonb, '{ejemplos_json}'::jsonb, true
            )
            ON CONFLICT (codigo) DO NOTHING
            """
        )

    op.execute(
        f"ALTER TABLE {S}.solicitudes_reporte_ia ADD COLUMN IF NOT EXISTS estado VARCHAR(30) NOT NULL DEFAULT 'completada'"
    )
    op.execute(
        f"ALTER TABLE {S}.solicitudes_reporte_ia ADD COLUMN IF NOT EXISTS interpretacion JSONB"
    )
    op.execute(
        f"ALTER TABLE {S}.solicitudes_reporte_ia ADD COLUMN IF NOT EXISTS formato_visualizacion VARCHAR(20) NOT NULL DEFAULT 'ambos'"
    )
    op.execute(
        f"ALTER TABLE {S}.solicitudes_reporte_ia ADD COLUMN IF NOT EXISTS mensaje_estado TEXT"
    )
    op.execute(
        f"ALTER TABLE {S}.solicitudes_reporte_ia ADD COLUMN IF NOT EXISTS exportaciones JSONB NOT NULL DEFAULT '[]'::jsonb"
    )

    op.execute(
        f"""
        DO $$
        BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'fashionstore_app') THEN
                EXECUTE 'GRANT SELECT, INSERT, UPDATE, DELETE ON {S}.catalogo_reportes_ia TO fashionstore_app';
                EXECUTE 'GRANT USAGE, SELECT ON SEQUENCE {S}.catalogo_reportes_ia_id_reporte_catalogo_seq TO fashionstore_app';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.execute(f"ALTER TABLE {S}.solicitudes_reporte_ia DROP COLUMN IF EXISTS exportaciones")
    op.execute(f"ALTER TABLE {S}.solicitudes_reporte_ia DROP COLUMN IF EXISTS mensaje_estado")
    op.execute(f"ALTER TABLE {S}.solicitudes_reporte_ia DROP COLUMN IF EXISTS formato_visualizacion")
    op.execute(f"ALTER TABLE {S}.solicitudes_reporte_ia DROP COLUMN IF EXISTS interpretacion")
    op.execute(f"ALTER TABLE {S}.solicitudes_reporte_ia DROP COLUMN IF EXISTS estado")
    op.execute(f"DROP TABLE IF EXISTS {S}.catalogo_reportes_ia")

