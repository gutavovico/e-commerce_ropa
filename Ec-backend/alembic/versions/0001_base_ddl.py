"""Base DDL - esquema completo de FashionStore

Reproduce fielmente el DDL de fashionstore.sql:
esquema, extensiones, 10 enums, 22 tablas, indices, 2 triggers, 3 vistas,
y datos semilla.

Revision ID: 0001
Revises: None
Create Date: 2026-09-18
"""

from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # 0. CONFIGURACION INICIAL
    # ------------------------------------------------------------------
    op.execute("CREATE SCHEMA IF NOT EXISTS fashionstore")
    op.execute("SET search_path TO fashionstore, public")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")
    op.execute("CREATE EXTENSION IF NOT EXISTS citext")
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")

    # ------------------------------------------------------------------
    # 1. TIPOS ENUMERADOS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TYPE fashionstore.rol_usuario AS ENUM (
            'cliente', 'administrador', 'encargado_sucursal', 'cajero', 'proveedor'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.estado_reserva AS ENUM (
            'pendiente', 'confirmada', 'en_atencion', 'atendida', 'cancelada', 'vencida'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.estado_prenda_stock AS ENUM (
            'disponible', 'reservada', 'vendida', 'agotada', 'proxima_ingreso', 'devuelta'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.tipo_movimiento_inv AS ENUM (
            'ingreso_proveedor', 'reserva', 'liberacion_reserva', 'venta',
            'devolucion', 'ajuste', 'transferencia_salida', 'transferencia_entrada'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.tipo_venta AS ENUM (
            'presencial', 'digital_web', 'digital_movil'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.estado_venta AS ENUM (
            'pendiente', 'pagada', 'anulada', 'devuelta'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.estado_pago AS ENUM (
            'pendiente', 'autorizado', 'confirmado', 'rechazado', 'reembolsado'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.metodo_pago AS ENUM (
            'efectivo', 'tarjeta_debito', 'tarjeta_credito', 'pasarela_digital', 'qr',
            'transferencia'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.canal_origen AS ENUM (
            'web', 'movil', 'sucursal'
        )
    """)
    op.execute("""
        CREATE TYPE fashionstore.tipo_temporada AS ENUM (
            'primavera_verano', 'otono_invierno', 'escolar', 'promocion_especial',
            'nueva_coleccion'
        )
    """)

    # ------------------------------------------------------------------
    # 2. UBICACIONES / SUCURSALES
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.ciudades (
            id_ciudad SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            pais VARCHAR(100) NOT NULL DEFAULT 'Bolivia',
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.sucursales (
            id_sucursal SERIAL PRIMARY KEY,
            id_ciudad INTEGER NOT NULL REFERENCES fashionstore.ciudades(id_ciudad),
            nombre VARCHAR(150) NOT NULL,
            direccion VARCHAR(255) NOT NULL,
            telefono VARCHAR(30),
            horario_apertura TIME NOT NULL DEFAULT '09:00',
            horario_cierre TIME NOT NULL DEFAULT '20:00',
            activa BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (id_ciudad, nombre)
        )
    """)

    # ------------------------------------------------------------------
    # 3. USUARIOS, ROLES, CLIENTES, EMPLEADOS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.usuarios (
            id_usuario BIGSERIAL PRIMARY KEY,
            email CITEXT NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            nombres VARCHAR(100) NOT NULL,
            apellidos VARCHAR(100) NOT NULL,
            telefono VARCHAR(30),
            rol fashionstore.rol_usuario NOT NULL DEFAULT 'cliente',
            id_sucursal INTEGER REFERENCES fashionstore.sucursales(id_sucursal),
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            fecha_registro TIMESTAMPTZ NOT NULL DEFAULT now(),
            ultimo_acceso TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX idx_usuarios_rol ON fashionstore.usuarios(rol)")
    op.execute("CREATE INDEX idx_usuarios_sucursal ON fashionstore.usuarios(id_sucursal)")

    op.execute("""
        CREATE TABLE fashionstore.clientes (
            id_cliente BIGINT PRIMARY KEY
                REFERENCES fashionstore.usuarios(id_usuario) ON DELETE CASCADE,
            fecha_nacimiento DATE,
            genero VARCHAR(20),
            talla_preferida VARCHAR(10),
            ciudad_preferida INTEGER REFERENCES fashionstore.ciudades(id_ciudad),
            acepta_marketing BOOLEAN NOT NULL DEFAULT TRUE
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.empleados (
            id_empleado BIGINT PRIMARY KEY
                REFERENCES fashionstore.usuarios(id_usuario) ON DELETE CASCADE,
            codigo_empleado VARCHAR(20) NOT NULL UNIQUE,
            fecha_contratacion DATE NOT NULL DEFAULT CURRENT_DATE,
            cargo VARCHAR(100)
        )
    """)

    # ------------------------------------------------------------------
    # 4. PROVEEDORES
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.proveedores (
            id_proveedor SERIAL PRIMARY KEY,
            id_usuario BIGINT REFERENCES fashionstore.usuarios(id_usuario),
            razon_social VARCHAR(200) NOT NULL,
            nit VARCHAR(30) UNIQUE,
            contacto_nombre VARCHAR(150),
            telefono VARCHAR(30),
            email CITEXT,
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # ------------------------------------------------------------------
    # 5. CATALOGO: TEMPORADAS, COLECCIONES, CATEGORIAS, TALLAS, COLORES
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.temporadas (
            id_temporada SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            tipo fashionstore.tipo_temporada NOT NULL,
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            activa BOOLEAN NOT NULL DEFAULT TRUE,
            CHECK (fecha_fin >= fecha_inicio)
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.colecciones (
            id_coleccion SERIAL PRIMARY KEY,
            id_temporada INTEGER NOT NULL
                REFERENCES fashionstore.temporadas(id_temporada),
            id_proveedor INTEGER REFERENCES fashionstore.proveedores(id_proveedor),
            nombre VARCHAR(150) NOT NULL,
            descripcion TEXT,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.categorias (
            id_categoria SERIAL PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL UNIQUE,
            id_categoria_padre INTEGER REFERENCES fashionstore.categorias(id_categoria)
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.tallas (
            id_talla SERIAL PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL UNIQUE,
            orden SMALLINT NOT NULL DEFAULT 0
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.colores (
            id_color SERIAL PRIMARY KEY,
            nombre VARCHAR(50) NOT NULL UNIQUE,
            codigo_hex CHAR(7)
        )
    """)

    # ------------------------------------------------------------------
    # 6. PRODUCTOS Y VARIANTES
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.productos (
            id_producto BIGSERIAL PRIMARY KEY,
            id_categoria INTEGER NOT NULL
                REFERENCES fashionstore.categorias(id_categoria),
            id_coleccion INTEGER REFERENCES fashionstore.colecciones(id_coleccion),
            id_proveedor INTEGER REFERENCES fashionstore.proveedores(id_proveedor),
            nombre VARCHAR(200) NOT NULL,
            descripcion TEXT,
            precio_base NUMERIC(10,2) NOT NULL CHECK (precio_base >= 0),
            imagen_url VARCHAR(500),
            modelo_ar_url VARCHAR(500),
            activo BOOLEAN NOT NULL DEFAULT TRUE,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX idx_productos_categoria ON fashionstore.productos(id_categoria)"
    )
    op.execute(
        "CREATE INDEX idx_productos_coleccion ON fashionstore.productos(id_coleccion)"
    )
    op.execute(
        "CREATE INDEX idx_productos_nombre_trgm ON fashionstore.productos "
        "USING gin (nombre gin_trgm_ops)"
    )

    op.execute("""
        CREATE TABLE fashionstore.variantes_producto (
            id_variante BIGSERIAL PRIMARY KEY,
            id_producto BIGINT NOT NULL
                REFERENCES fashionstore.productos(id_producto) ON DELETE CASCADE,
            id_talla INTEGER NOT NULL REFERENCES fashionstore.tallas(id_talla),
            id_color INTEGER NOT NULL REFERENCES fashionstore.colores(id_color),
            sku VARCHAR(50) NOT NULL UNIQUE,
            precio_extra NUMERIC(10,2) NOT NULL DEFAULT 0,
            UNIQUE (id_producto, id_talla, id_color)
        )
    """)

    # ------------------------------------------------------------------
    # 7. INVENTARIO POR SUCURSAL
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.inventario_sucursal (
            id_inventario BIGSERIAL PRIMARY KEY,
            id_variante BIGINT NOT NULL
                REFERENCES fashionstore.variantes_producto(id_variante),
            id_sucursal INTEGER NOT NULL
                REFERENCES fashionstore.sucursales(id_sucursal),
            id_temporada INTEGER NOT NULL
                REFERENCES fashionstore.temporadas(id_temporada),
            cantidad_disponible INTEGER NOT NULL DEFAULT 0
                CHECK (cantidad_disponible >= 0),
            cantidad_reservada INTEGER NOT NULL DEFAULT 0
                CHECK (cantidad_reservada >= 0),
            stock_minimo INTEGER NOT NULL DEFAULT 0,
            estado fashionstore.estado_prenda_stock NOT NULL DEFAULT 'disponible',
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (id_variante, id_sucursal, id_temporada)
        )
    """)
    op.execute(
        "CREATE INDEX idx_inventario_sucursal ON fashionstore.inventario_sucursal(id_sucursal)"
    )
    op.execute(
        "CREATE INDEX idx_inventario_variante ON fashionstore.inventario_sucursal(id_variante)"
    )
    op.execute(
        "CREATE INDEX idx_inventario_estado ON fashionstore.inventario_sucursal(estado)"
    )

    # Trigger: actualizar estado de inventario
    op.execute("""
        CREATE OR REPLACE FUNCTION fashionstore.fn_actualizar_estado_inventario()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.cantidad_disponible = 0 AND NEW.cantidad_reservada = 0 THEN
                NEW.estado := 'agotada';
            ELSIF NEW.cantidad_disponible = 0 AND NEW.cantidad_reservada > 0 THEN
                NEW.estado := 'reservada';
            ELSE
                NEW.estado := 'disponible';
            END IF;
            NEW.actualizado_en := now();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_inventario_estado
        BEFORE INSERT OR UPDATE OF cantidad_disponible, cantidad_reservada
        ON fashionstore.inventario_sucursal
        FOR EACH ROW EXECUTE FUNCTION fashionstore.fn_actualizar_estado_inventario()
    """)

    # ------------------------------------------------------------------
    # 8. MOVIMIENTOS DE INVENTARIO
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.movimientos_inventario (
            id_movimiento BIGSERIAL PRIMARY KEY,
            id_inventario BIGINT NOT NULL
                REFERENCES fashionstore.inventario_sucursal(id_inventario),
            tipo_movimiento fashionstore.tipo_movimiento_inv NOT NULL,
            cantidad INTEGER NOT NULL CHECK (cantidad <> 0),
            id_usuario_responsable BIGINT
                REFERENCES fashionstore.usuarios(id_usuario),
            referencia_documento VARCHAR(100),
            observacion TEXT,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX idx_mov_inv_inventario "
        "ON fashionstore.movimientos_inventario(id_inventario)"
    )
    op.execute(
        "CREATE INDEX idx_mov_inv_tipo "
        "ON fashionstore.movimientos_inventario(tipo_movimiento)"
    )

    # ------------------------------------------------------------------
    # 9. RESERVAS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.reservas (
            id_reserva BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT NOT NULL
                REFERENCES fashionstore.clientes(id_cliente),
            id_sucursal INTEGER NOT NULL
                REFERENCES fashionstore.sucursales(id_sucursal),
            fecha_hora_atencion TIMESTAMPTZ NOT NULL,
            estado fashionstore.estado_reserva NOT NULL DEFAULT 'pendiente',
            canal_origen fashionstore.canal_origen NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            atendido_por BIGINT REFERENCES fashionstore.empleados(id_empleado),
            atendido_en TIMESTAMPTZ,
            observacion TEXT
        )
    """)
    op.execute(
        "CREATE INDEX idx_reservas_cliente ON fashionstore.reservas(id_cliente)"
    )
    op.execute(
        "CREATE INDEX idx_reservas_sucursal "
        "ON fashionstore.reservas(id_sucursal, fecha_hora_atencion)"
    )
    op.execute(
        "CREATE INDEX idx_reservas_estado ON fashionstore.reservas(estado)"
    )

    op.execute("""
        CREATE TABLE fashionstore.reserva_detalle (
            id_reserva_detalle BIGSERIAL PRIMARY KEY,
            id_reserva BIGINT NOT NULL
                REFERENCES fashionstore.reservas(id_reserva) ON DELETE CASCADE,
            id_variante BIGINT NOT NULL
                REFERENCES fashionstore.variantes_producto(id_variante),
            cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0),
            UNIQUE (id_reserva, id_variante)
        )
    """)

    # ------------------------------------------------------------------
    # 10. VESTIDOR VIRTUAL
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.sesiones_vestidor_virtual (
            id_sesion_ar BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT NOT NULL
                REFERENCES fashionstore.clientes(id_cliente),
            id_producto BIGINT NOT NULL
                REFERENCES fashionstore.productos(id_producto),
            dispositivo VARCHAR(50),
            fecha_hora TIMESTAMPTZ NOT NULL DEFAULT now(),
            resultado_url VARCHAR(500),
            genero_interes BOOLEAN NOT NULL DEFAULT FALSE
        )
    """)
    op.execute(
        "CREATE INDEX idx_ar_cliente ON fashionstore.sesiones_vestidor_virtual(id_cliente)"
    )
    op.execute(
        "CREATE INDEX idx_ar_producto ON fashionstore.sesiones_vestidor_virtual(id_producto)"
    )

    # ------------------------------------------------------------------
    # 11. CARRITO DE COMPRAS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.carritos (
            id_carrito BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT NOT NULL
                REFERENCES fashionstore.clientes(id_cliente),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (id_cliente)
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.carrito_detalle (
            id_carrito_detalle BIGSERIAL PRIMARY KEY,
            id_carrito BIGINT NOT NULL
                REFERENCES fashionstore.carritos(id_carrito) ON DELETE CASCADE,
            id_variante BIGINT NOT NULL
                REFERENCES fashionstore.variantes_producto(id_variante),
            id_sucursal INTEGER NOT NULL
                REFERENCES fashionstore.sucursales(id_sucursal),
            cantidad INTEGER NOT NULL DEFAULT 1 CHECK (cantidad > 0),
            agregado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            UNIQUE (id_carrito, id_variante, id_sucursal)
        )
    """)

    # ------------------------------------------------------------------
    # 12. VENTAS, DETALLES Y PAGOS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.ventas (
            id_venta BIGSERIAL PRIMARY KEY,
            numero_comprobante VARCHAR(30) NOT NULL UNIQUE,
            id_cliente BIGINT REFERENCES fashionstore.clientes(id_cliente),
            id_sucursal INTEGER NOT NULL
                REFERENCES fashionstore.sucursales(id_sucursal),
            id_cajero BIGINT REFERENCES fashionstore.empleados(id_empleado),
            id_reserva BIGINT REFERENCES fashionstore.reservas(id_reserva),
            tipo_venta fashionstore.tipo_venta NOT NULL,
            estado fashionstore.estado_venta NOT NULL DEFAULT 'pendiente',
            subtotal NUMERIC(12,2) NOT NULL DEFAULT 0,
            descuento NUMERIC(12,2) NOT NULL DEFAULT 0,
            total NUMERIC(12,2) NOT NULL DEFAULT 0,
            fecha_venta TIMESTAMPTZ NOT NULL DEFAULT now(),
            CHECK (total >= 0)
        )
    """)
    op.execute(
        "CREATE INDEX idx_ventas_cliente ON fashionstore.ventas(id_cliente)"
    )
    op.execute(
        "CREATE INDEX idx_ventas_sucursal "
        "ON fashionstore.ventas(id_sucursal, fecha_venta)"
    )
    op.execute(
        "CREATE INDEX idx_ventas_tipo ON fashionstore.ventas(tipo_venta)"
    )
    op.execute(
        "CREATE INDEX idx_ventas_estado ON fashionstore.ventas(estado)"
    )

    op.execute("""
        CREATE TABLE fashionstore.venta_detalle (
            id_venta_detalle BIGSERIAL PRIMARY KEY,
            id_venta BIGINT NOT NULL
                REFERENCES fashionstore.ventas(id_venta) ON DELETE CASCADE,
            id_variante BIGINT NOT NULL
                REFERENCES fashionstore.variantes_producto(id_variante),
            cantidad INTEGER NOT NULL CHECK (cantidad > 0),
            precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0),
            subtotal_linea NUMERIC(12,2) GENERATED ALWAYS AS
                (cantidad * precio_unitario) STORED
        )
    """)
    op.execute(
        "CREATE INDEX idx_venta_detalle_venta ON fashionstore.venta_detalle(id_venta)"
    )

    op.execute("""
        CREATE TABLE fashionstore.pagos (
            id_pago BIGSERIAL PRIMARY KEY,
            id_venta BIGINT NOT NULL
                REFERENCES fashionstore.ventas(id_venta) ON DELETE CASCADE,
            metodo_pago fashionstore.metodo_pago NOT NULL,
            monto NUMERIC(12,2) NOT NULL CHECK (monto >= 0),
            estado fashionstore.estado_pago NOT NULL DEFAULT 'pendiente',
            referencia_pasarela VARCHAR(150),
            payload_respuesta JSONB,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
            confirmado_en TIMESTAMPTZ
        )
    """)
    op.execute("CREATE INDEX idx_pagos_venta ON fashionstore.pagos(id_venta)")
    op.execute("CREATE INDEX idx_pagos_estado ON fashionstore.pagos(estado)")

    # ------------------------------------------------------------------
    # 13. PROMOCIONES
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.promociones (
            id_promocion SERIAL PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            descripcion TEXT,
            porcentaje_descuento NUMERIC(5,2)
                CHECK (porcentaje_descuento BETWEEN 0 AND 100),
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            activa BOOLEAN NOT NULL DEFAULT TRUE,
            CHECK (fecha_fin >= fecha_inicio)
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.promocion_producto (
            id_promocion INTEGER NOT NULL
                REFERENCES fashionstore.promociones(id_promocion) ON DELETE CASCADE,
            id_producto BIGINT NOT NULL
                REFERENCES fashionstore.productos(id_producto) ON DELETE CASCADE,
            PRIMARY KEY (id_promocion, id_producto)
        )
    """)

    # ------------------------------------------------------------------
    # 14. INTELIGENCIA ARTIFICIAL Y CHATBOT
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE fashionstore.historial_navegacion (
            id_historial BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT NOT NULL
                REFERENCES fashionstore.clientes(id_cliente),
            id_producto BIGINT NOT NULL
                REFERENCES fashionstore.productos(id_producto),
            tipo_evento VARCHAR(30) NOT NULL DEFAULT 'vista',
            fecha_hora TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX idx_hist_nav_cliente "
        "ON fashionstore.historial_navegacion(id_cliente)"
    )
    op.execute(
        "CREATE INDEX idx_hist_nav_producto "
        "ON fashionstore.historial_navegacion(id_producto)"
    )

    op.execute("""
        CREATE TABLE fashionstore.recomendaciones_ia (
            id_recomendacion BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT NOT NULL
                REFERENCES fashionstore.clientes(id_cliente),
            id_producto BIGINT NOT NULL
                REFERENCES fashionstore.productos(id_producto),
            score_relevancia NUMERIC(5,4) NOT NULL
                CHECK (score_relevancia BETWEEN 0 AND 1),
            motivo VARCHAR(255),
            generado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute(
        "CREATE INDEX idx_recom_cliente "
        "ON fashionstore.recomendaciones_ia(id_cliente, score_relevancia DESC)"
    )

    op.execute("""
        CREATE TABLE fashionstore.interacciones_chatbot (
            id_interaccion BIGSERIAL PRIMARY KEY,
            id_cliente BIGINT REFERENCES fashionstore.clientes(id_cliente),
            mensaje_usuario TEXT NOT NULL,
            respuesta_ia TEXT,
            canal fashionstore.canal_origen NOT NULL,
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("""
        CREATE TABLE fashionstore.solicitudes_reporte_ia (
            id_solicitud BIGSERIAL PRIMARY KEY,
            id_usuario BIGINT NOT NULL
                REFERENCES fashionstore.usuarios(id_usuario),
            comando_voz_texto TEXT NOT NULL,
            tipo_reporte VARCHAR(100),
            resultado_url VARCHAR(500),
            creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # ------------------------------------------------------------------
    # 15. VISTAS
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE VIEW fashionstore.vw_inventario_consolidado AS
        SELECT
            s.id_sucursal,
            s.nombre AS sucursal,
            p.id_producto,
            p.nombre AS producto,
            t.codigo AS talla,
            c.nombre AS color,
            tp.nombre AS temporada,
            inv.cantidad_disponible,
            inv.cantidad_reservada,
            inv.estado
        FROM fashionstore.inventario_sucursal inv
        JOIN fashionstore.variantes_producto vp ON vp.id_variante = inv.id_variante
        JOIN fashionstore.productos p ON p.id_producto = vp.id_producto
        JOIN fashionstore.tallas t ON t.id_talla = vp.id_talla
        JOIN fashionstore.colores c ON c.id_color = vp.id_color
        JOIN fashionstore.sucursales s ON s.id_sucursal = inv.id_sucursal
        JOIN fashionstore.temporadas tp ON tp.id_temporada = inv.id_temporada
    """)
    op.execute("""
        CREATE OR REPLACE VIEW fashionstore.vw_ventas_por_sucursal AS
        SELECT
            v.id_sucursal,
            s.nombre AS sucursal,
            v.tipo_venta,
            DATE_TRUNC('day', v.fecha_venta)::date AS fecha,
            COUNT(*) AS cantidad_ventas,
            SUM(v.total) AS total_vendido
        FROM fashionstore.ventas v
        JOIN fashionstore.sucursales s ON s.id_sucursal = v.id_sucursal
        WHERE v.estado = 'pagada'
        GROUP BY v.id_sucursal, s.nombre, v.tipo_venta,
                 DATE_TRUNC('day', v.fecha_venta)
    """)
    op.execute("""
        CREATE OR REPLACE VIEW fashionstore.vw_reservas_pendientes AS
        SELECT
            r.id_reserva,
            r.id_sucursal,
            s.nombre AS sucursal,
            u.nombres || ' ' || u.apellidos AS cliente,
            r.fecha_hora_atencion,
            r.estado
        FROM fashionstore.reservas r
        JOIN fashionstore.sucursales s ON s.id_sucursal = r.id_sucursal
        JOIN fashionstore.usuarios u ON u.id_usuario = r.id_cliente
        WHERE r.estado IN ('pendiente', 'confirmada')
    """)

    # ------------------------------------------------------------------
    # 16. TRIGGER: DESCUENTO AUTOMATICO DE INVENTARIO TRAS VENTA
    # ------------------------------------------------------------------
    op.execute("""
        CREATE OR REPLACE FUNCTION fashionstore.fn_descontar_inventario_venta()
        RETURNS TRIGGER AS $$
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
        $$ LANGUAGE plpgsql
    """)
    op.execute("""
        CREATE TRIGGER trg_descontar_inventario
        AFTER INSERT ON fashionstore.venta_detalle
        FOR EACH ROW EXECUTE FUNCTION fashionstore.fn_descontar_inventario_venta()
    """)

    # ------------------------------------------------------------------
    # 17. DATOS SEMILLA MINIMOS
    # ------------------------------------------------------------------
    op.execute("""
        INSERT INTO fashionstore.ciudades (nombre) VALUES
        ('Santa Cruz de la Sierra'),
        ('La Paz'),
        ('Cochabamba')
    """)
    op.execute("""
        INSERT INTO fashionstore.tallas (codigo, orden) VALUES
        ('XS', 1), ('S', 2), ('M', 3), ('L', 4), ('XL', 5), ('XXL', 6)
    """)
    op.execute("""
        INSERT INTO fashionstore.colores (nombre, codigo_hex) VALUES
        ('Negro', '#000000'),
        ('Blanco', '#FFFFFF'),
        ('Azul', '#1E3A8A'),
        ('Rojo', '#B91C1C')
    """)
    op.execute("""
        INSERT INTO fashionstore.categorias (nombre) VALUES
        ('Camisas'), ('Pantalones'), ('Vestidos'), ('Chaquetas'), ('Accesorios')
    """)
    op.execute("""
        INSERT INTO fashionstore.temporadas (nombre, tipo, fecha_inicio, fecha_fin) VALUES
        ('Primavera-Verano 2026', 'primavera_verano', '2026-09-01', '2027-02-28'),
        ('Escolar 2026', 'escolar', '2026-01-15', '2026-03-01')
    """)


def downgrade() -> None:
    op.execute("SET search_path TO fashionstore, public")

    # Vistas
    op.execute("DROP VIEW IF EXISTS fashionstore.vw_reservas_pendientes")
    op.execute("DROP VIEW IF EXISTS fashionstore.vw_ventas_por_sucursal")
    op.execute("DROP VIEW IF EXISTS fashionstore.vw_inventario_consolidado")

    # Trigger de descuento de inventario
    op.execute(
        "DROP TRIGGER IF EXISTS trg_descontar_inventario "
        "ON fashionstore.venta_detalle"
    )
    op.execute("DROP FUNCTION IF EXISTS fashionstore.fn_descontar_inventario_venta()")

    # Trigger de estado de inventario
    op.execute(
        "DROP TRIGGER IF EXISTS trg_inventario_estado "
        "ON fashionstore.inventario_sucursal"
    )
    op.execute("DROP FUNCTION IF EXISTS fashionstore.fn_actualizar_estado_inventario()")

    # Tablas en orden inverso de dependencias
    op.execute("DROP TABLE IF EXISTS fashionstore.solicitudes_reporte_ia CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.interacciones_chatbot CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.recomendaciones_ia CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.historial_navegacion CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.promocion_producto CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.promociones CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.pagos CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.venta_detalle CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.ventas CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.carrito_detalle CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.carritos CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.sesiones_vestidor_virtual CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.reserva_detalle CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.reservas CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.movimientos_inventario CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.inventario_sucursal CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.variantes_producto CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.productos CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.colores CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.tallas CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.categorias CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.colecciones CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.temporadas CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.proveedores CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.empleados CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.clientes CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.usuarios CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.sucursales CASCADE")
    op.execute("DROP TABLE IF EXISTS fashionstore.ciudades CASCADE")

    # Enums
    op.execute("DROP TYPE IF EXISTS fashionstore.tipo_temporada")
    op.execute("DROP TYPE IF EXISTS fashionstore.canal_origen")
    op.execute("DROP TYPE IF EXISTS fashionstore.metodo_pago")
    op.execute("DROP TYPE IF EXISTS fashionstore.estado_pago")
    op.execute("DROP TYPE IF EXISTS fashionstore.estado_venta")
    op.execute("DROP TYPE IF EXISTS fashionstore.tipo_venta")
    op.execute("DROP TYPE IF EXISTS fashionstore.tipo_movimiento_inv")
    op.execute("DROP TYPE IF EXISTS fashionstore.estado_prenda_stock")
    op.execute("DROP TYPE IF EXISTS fashionstore.estado_reserva")
    op.execute("DROP TYPE IF EXISTS fashionstore.rol_usuario")

    # Esquema (las extensiones NO se eliminan: son compartidas a nivel de BD)
    op.execute("DROP SCHEMA IF EXISTS fashionstore CASCADE")
