"""Semilla de catalogo de alta costura para CU06 y capturas de diseno

Revision ID: 0003
Revises: 0002
Create Date: 2026-09-20
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Sucursales de prueba para inventario
    op.execute("""
        INSERT INTO fashionstore.sucursales (id_ciudad, nombre, direccion, telefono)
        VALUES 
            (1, 'Atelier Serrano - Madrid', 'Calle Serrano 48', '+34 91 555 1234'),
            (1, 'Boutique Central - Santa Cruz', 'Av. San Martín 100', '+591 3 333 4444')
        ON CONFLICT (id_ciudad, nombre) DO NOTHING;
    """)

    # 2. Temporadas de Alta Costura
    op.execute("""
        INSERT INTO fashionstore.temporadas (nombre, tipo, fecha_inicio, fecha_fin, activa)
        VALUES
            ('Otoño / Invierno 2024', 'otono_invierno', '2024-03-01', '2024-08-31', TRUE),
            ('Primavera / Verano 2025', 'primavera_verano', '2025-09-01', '2026-02-28', TRUE),
            ('Cápsula Edición Limitada', 'nueva_coleccion', '2026-01-01', '2026-12-31', TRUE)
        ON CONFLICT DO NOTHING;
    """)

    # 3. Colecciones de Alta Costura
    op.execute("""
        DO $$
        DECLARE
            tid INTEGER;
        BEGIN
            SELECT id_temporada INTO tid FROM fashionstore.temporadas WHERE nombre = 'Otoño / Invierno 2024' LIMIT 1;
            IF tid IS NULL THEN
                SELECT id_temporada INTO tid FROM fashionstore.temporadas LIMIT 1;
            END IF;

            INSERT INTO fashionstore.colecciones (id_temporada, nombre, descripcion)
            VALUES
                (tid, 'Sastrería Atelier', 'Prendas de sastrería artesanal confeccionadas con cortes arquitectónicos y tejidos nobles.'),
                (tid, 'Esenciales Minimalistas', 'Piezas sobrias de corte atemporal, versátiles y concebidas para el fondo de armario de lujo.'),
                (tid, 'Alta Costura', 'Creaciones exclusivas de patronaje complejo, sedas puras y terminaciones a mano.'),
                (tid, 'Seda Natural Pura', 'Línea fluida en satén de seda pura de 22mm con caída etérea y brillo sutil.')
            ON CONFLICT DO NOTHING;
        END $$;
    """)

    # 4. Tallas Numéricas Atelier
    op.execute("""
        INSERT INTO fashionstore.tallas (codigo, orden)
        VALUES
            ('36', 10),
            ('38', 11),
            ('40', 12),
            ('42', 13),
            ('44', 14),
            ('Única', 15)
        ON CONFLICT (codigo) DO NOTHING;
    """)

    # 5. Colores Atelier y de Colección Femenina
    op.execute("""
        INSERT INTO fashionstore.colores (nombre, codigo_hex)
        VALUES
            ('Marfil', '#FCFBF8'),
            ('Camel', '#C2A688'),
            ('Ébano', '#1A1A1A'),
            ('Champagne', '#E8DFCF'),
            ('Blanco Puro', '#FFFFFF'),
            ('Beige Arena', '#D8C4B6'),
            ('Borgoña', '#5E1924'),
            ('Terracota', '#B85D3B'),
            ('Azul Marino', '#1C2A39'),
            ('Verde Oliva', '#4B5842'),
            ('Esmeralda', '#1B4D3E'),
            ('Rosa Palo', '#E8C5C8'),
            ('Malva', '#A594A6'),
            ('Rojo Carmín', '#991B1B'),
            ('Gris Perla', '#C5C6C7'),
            ('Ocre', '#C68B29')
        ON CONFLICT (nombre) DO NOTHING;
    """)

    # 6. Prendas Fieles a las Capturas de Referencia
    op.execute("""
        DO $$
        DECLARE
            cat_vestidos INT;
            cat_chaquetas INT;
            cat_camisas INT;
            cat_pantalones INT;
            col_atelier INT;
            col_esenciales INT;
            col_altacostura INT;
            col_seda INT;
            
            p1_id BIGINT;
            p2_id BIGINT;
            p3_id BIGINT;
            p4_id BIGINT;

            t36 INT; t38 INT; t40 INT; t42 INT; t_unica INT;
            c_marfil INT; c_camel INT; c_ebano INT; c_champagne INT; c_rojo INT;
            
            suc1 INT;
            temp1 INT;
        BEGIN
            SELECT id_categoria INTO cat_vestidos FROM fashionstore.categorias WHERE nombre = 'Vestidos' LIMIT 1;
            SELECT id_categoria INTO cat_chaquetas FROM fashionstore.categorias WHERE nombre = 'Chaquetas' LIMIT 1;
            SELECT id_categoria INTO cat_camisas FROM fashionstore.categorias WHERE nombre = 'Camisas' LIMIT 1;
            SELECT id_categoria INTO cat_pantalones FROM fashionstore.categorias WHERE nombre = 'Pantalones' LIMIT 1;

            SELECT id_coleccion INTO col_altacostura FROM fashionstore.colecciones WHERE nombre = 'Alta Costura' LIMIT 1;
            SELECT id_coleccion INTO col_atelier FROM fashionstore.colecciones WHERE nombre = 'Sastrería Atelier' LIMIT 1;
            SELECT id_coleccion INTO col_esenciales FROM fashionstore.colecciones WHERE nombre = 'Esenciales Minimalistas' LIMIT 1;
            SELECT id_coleccion INTO col_seda FROM fashionstore.colecciones WHERE nombre = 'Seda Natural Pura' LIMIT 1;

            SELECT id_talla INTO t36 FROM fashionstore.tallas WHERE codigo = '36' LIMIT 1;
            SELECT id_talla INTO t38 FROM fashionstore.tallas WHERE codigo = '38' LIMIT 1;
            SELECT id_talla INTO t40 FROM fashionstore.tallas WHERE codigo = '40' LIMIT 1;
            SELECT id_talla INTO t42 FROM fashionstore.tallas WHERE codigo = '42' LIMIT 1;
            SELECT id_talla INTO t_unica FROM fashionstore.tallas WHERE codigo = 'Única' LIMIT 1;

            SELECT id_color INTO c_marfil FROM fashionstore.colores WHERE nombre = 'Marfil' LIMIT 1;
            SELECT id_color INTO c_camel FROM fashionstore.colores WHERE nombre = 'Camel' LIMIT 1;
            SELECT id_color INTO c_ebano FROM fashionstore.colores WHERE nombre = 'Ébano' LIMIT 1;
            SELECT id_color INTO c_champagne FROM fashionstore.colores WHERE nombre = 'Champagne' LIMIT 1;
            SELECT id_color INTO c_rojo FROM fashionstore.colores WHERE nombre = 'Rojo Carmín' LIMIT 1;
            IF c_rojo IS NULL THEN
                SELECT id_color INTO c_rojo FROM fashionstore.colores WHERE nombre = 'Rojo' LIMIT 1;
            END IF;
            IF c_rojo IS NULL THEN c_rojo := c_marfil; END IF;

            SELECT id_sucursal INTO suc1 FROM fashionstore.sucursales LIMIT 1;
            SELECT id_temporada INTO temp1 FROM fashionstore.temporadas WHERE nombre = 'Otoño / Invierno 2024' LIMIT 1;
            IF temp1 IS NULL THEN SELECT id_temporada INTO temp1 FROM fashionstore.temporadas LIMIT 1; END IF;

            -- 1. Vestido plisado seda (Rojo Carmín)
            INSERT INTO fashionstore.productos (id_categoria, id_coleccion, nombre, descripcion, precio_base, imagen_url, activo)
            VALUES (
                cat_vestidos, col_altacostura, 'Vestido plisado seda',
                'Vestido de alta costura largo plisado confeccionado en pura seda rojo carmín con caída etérea y espalda descubierta.',
                890.00, 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop&q=80', TRUE
            )
            RETURNING id_producto INTO p1_id;

            -- Variantes Vestido
            INSERT INTO fashionstore.variantes_producto (id_producto, id_talla, id_color, sku, precio_extra)
            VALUES 
                (p1_id, t38, c_rojo, 'VES-PLI-38-ROJ', 0.00),
                (p1_id, t36, c_rojo, 'VES-PLI-36-ROJ', 0.00),
                (p1_id, t40, c_rojo, 'VES-PLI-40-ROJ', 0.00)
            ON CONFLICT DO NOTHING;

            -- 2. Blazer estructurado / Blazer lana virgen
            INSERT INTO fashionstore.productos (id_categoria, id_coleccion, nombre, descripcion, precio_base, imagen_url, activo)
            VALUES (
                cat_chaquetas, col_atelier, 'Blazer estructurado',
                'Blazer sastre confeccionado en fina lana virgen estructurada, hombreras definidas y cierre cruzado de botones en cuerno natural.',
                740.00, 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?w=800&auto=format&fit=crop&q=80', TRUE
            )
            RETURNING id_producto INTO p2_id;

            -- Variantes Blazer
            INSERT INTO fashionstore.variantes_producto (id_producto, id_talla, id_color, sku, precio_extra)
            VALUES 
                (p2_id, t40, c_camel, 'BLA-EST-40-CAM', 0.00),
                (p2_id, t38, c_camel, 'BLA-EST-38-CAM', 0.00),
                (p2_id, t42, c_camel, 'BLA-EST-42-CAM', 0.00)
            ON CONFLICT DO NOTHING;

            -- 3. Blusa satén 22mm (Moda Femenina Atelier)
            INSERT INTO fashionstore.productos (id_categoria, id_coleccion, nombre, descripcion, precio_base, imagen_url, activo)
            VALUES (
                cat_camisas, col_seda, 'Blusa satén 22mm',
                'Blusa de corte asimétrico en satén de seda natural de 22mm, cuello drapeado y mangas con puño extendido en tono champagne.',
                310.00, 'https://images.unsplash.com/photo-1564257631407-4deb1f99d992?w=800&auto=format&fit=crop&q=80', TRUE
            )
            RETURNING id_producto INTO p3_id;

            -- Variantes Blusa
            INSERT INTO fashionstore.variantes_producto (id_producto, id_talla, id_color, sku, precio_extra)
            VALUES 
                (p3_id, t38, c_champagne, 'BLU-SAT-38-CHA', 0.00),
                (p3_id, t36, c_champagne, 'BLU-SAT-36-CHA', 0.00),
                (p3_id, t40, c_champagne, 'BLU-SAT-40-CHA', 0.00)
            ON CONFLICT DO NOTHING;

            -- 4. Pantalón tiro alto
            INSERT INTO fashionstore.productos (id_categoria, id_coleccion, nombre, descripcion, precio_base, imagen_url, activo)
            VALUES (
                cat_pantalones, col_atelier, 'Pantalón tiro alto',
                'Pantalón sastre de corte amplio y pinzas frontales profundas, confeccionado en mezcla de lana fría y seda en tono ébano profundo.',
                420.00, 'https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&auto=format&fit=crop&q=80', TRUE
            )
            RETURNING id_producto INTO p4_id;

            -- Variantes Pantalon
            INSERT INTO fashionstore.variantes_producto (id_producto, id_talla, id_color, sku, precio_extra)
            VALUES 
                (p4_id, t38, c_ebano, 'PAN-TIR-38-EBA', 0.00),
                (p4_id, t40, c_ebano, 'PAN-TIR-40-EBA', 0.00),
                (p4_id, t42, c_ebano, 'PAN-TIR-42-EBA', 0.00)
            ON CONFLICT DO NOTHING;

            -- 7. Inventario para cada variante en la sucursal activa
            IF suc1 IS NOT NULL AND temp1 IS NOT NULL THEN
                INSERT INTO fashionstore.inventario_sucursal (id_variante, id_sucursal, id_temporada, cantidad_disponible, cantidad_reservada)
                SELECT id_variante, suc1, temp1, 15, 0
                FROM fashionstore.variantes_producto
                WHERE id_producto IN (p1_id, p2_id, p3_id, p4_id)
                ON CONFLICT DO NOTHING;
            END IF;

        END $$;
    """)


def downgrade() -> None:
    op.execute("""
        DELETE FROM fashionstore.productos 
        WHERE nombre IN ('Vestido plisado seda', 'Blazer estructurado', 'Blusa satén 22mm', 'Pantalón tiro alto');
    """)
