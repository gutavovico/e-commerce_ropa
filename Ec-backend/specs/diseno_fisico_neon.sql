-- ============================================================================
-- SCRIPT DDL FÍSICO COMPLETO EXTRAÍDO DIRECTAMENTE DE NEON POSTGRESQL
-- ESQUEMA: fashionstore
-- ============================================================================

CREATE SCHEMA IF NOT EXISTS fashionstore;
SET search_path TO fashionstore, public;

-- ----------------------------------------------------------------------------
-- 1. EXTENSIONES
-- ----------------------------------------------------------------------------
CREATE EXTENSION IF NOT EXISTS pgcrypto WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS citext WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS pg_trgm WITH SCHEMA public;
CREATE EXTENSION IF NOT EXISTS unaccent WITH SCHEMA public;

-- ----------------------------------------------------------------------------
-- 2. TIPOS ENUMERADOS (ENUMS)
-- ----------------------------------------------------------------------------
CREATE TYPE fashionstore.canal_origen AS ENUM ('web', 'movil', 'sucursal');
CREATE TYPE fashionstore.estado_pago AS ENUM ('pendiente', 'autorizado', 'confirmado', 'rechazado', 'reembolsado');
CREATE TYPE fashionstore.estado_prenda_stock AS ENUM ('disponible', 'reservada', 'vendida', 'agotada', 'proxima_ingreso', 'devuelta');
CREATE TYPE fashionstore.estado_reserva AS ENUM ('pendiente', 'confirmada', 'en_atencion', 'atendida', 'cancelada', 'vencida');
CREATE TYPE fashionstore.estado_venta AS ENUM ('pendiente', 'pagada', 'anulada', 'devuelta');
CREATE TYPE fashionstore.metodo_pago AS ENUM ('efectivo', 'tarjeta_debito', 'tarjeta_credito', 'pasarela_digital', 'qr', 'transferencia');
CREATE TYPE fashionstore.rol_usuario AS ENUM ('cliente', 'administrador', 'encargado_sucursal', 'cajero', 'proveedor');
CREATE TYPE fashionstore.tipo_movimiento_inv AS ENUM ('ingreso_proveedor', 'reserva', 'liberacion_reserva', 'venta', 'devolucion', 'ajuste', 'transferencia_salida', 'transferencia_entrada', 'ajuste_positivo', 'ajuste_negativo', 'venta_confirmada', 'cancelacion_pedido');
CREATE TYPE fashionstore.tipo_temporada AS ENUM ('primavera_verano', 'otono_invierno', 'escolar', 'promocion_especial', 'nueva_coleccion');
CREATE TYPE fashionstore.tipo_venta AS ENUM ('presencial', 'digital_web', 'digital_movil');

-- ----------------------------------------------------------------------------
-- 3. TABLAS FÍSICAS
-- ----------------------------------------------------------------------------
CREATE TABLE fashionstore.bitacora (
    id_bitacora                  BIGSERIAL,
    id_usuario                   INTEGER,
    usuario_nombre               VARCHAR(255),
    accion                       VARCHAR(100)             NOT NULL,
    tabla_modulo                 VARCHAR(100)             NOT NULL,
    direccion_ip                 VARCHAR(45),
    severidad                    VARCHAR(20)              NOT NULL DEFAULT 'INFO'::character varying,
    payload_anterior             JSONB,
    payload_nuevo                JSONB,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_bitacora PRIMARY KEY (id_bitacora)
);

CREATE TABLE fashionstore.carrito_detalle (
    id_carrito_detalle           BIGSERIAL,
    id_carrito                   BIGINT                   NOT NULL,
    id_variante                  BIGINT                   NOT NULL,
    id_sucursal                  INTEGER                  NOT NULL,
    cantidad                     INTEGER                  NOT NULL DEFAULT 1,
    agregado_en                  TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_carrito_detalle PRIMARY KEY (id_carrito_detalle),
    CONSTRAINT carrito_detalle_id_carrito_id_variante_id_sucursal_key UNIQUE (id_carrito, id_variante, id_sucursal),
    CONSTRAINT carrito_detalle_cantidad_check CHECK ((cantidad > 0))
);

CREATE TABLE fashionstore.carritos (
    id_carrito                   BIGSERIAL,
    id_cliente                   BIGINT                   NOT NULL,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    actualizado_en               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_carritos PRIMARY KEY (id_carrito),
    CONSTRAINT carritos_id_cliente_key UNIQUE (id_cliente)
);

CREATE TABLE fashionstore.categorias (
    id_categoria                 SERIAL,
    nombre                       VARCHAR(100)             NOT NULL,
    id_categoria_padre           INTEGER,
    CONSTRAINT pk_categorias PRIMARY KEY (id_categoria),
    CONSTRAINT categorias_nombre_key UNIQUE (nombre)
);

CREATE TABLE fashionstore.ciudades (
    id_ciudad                    SERIAL,
    nombre                       VARCHAR(100)             NOT NULL,
    pais                         VARCHAR(100)             NOT NULL DEFAULT 'Bolivia'::character varying,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_ciudades PRIMARY KEY (id_ciudad),
    CONSTRAINT ciudades_nombre_key UNIQUE (nombre)
);

CREATE TABLE fashionstore.clientes (
    id_cliente                   BIGINT                   NOT NULL,
    fecha_nacimiento             DATE,
    genero                       VARCHAR(20),
    talla_preferida              VARCHAR(10),
    ciudad_preferida             INTEGER,
    acepta_marketing             BOOLEAN                  NOT NULL DEFAULT true,
    CONSTRAINT pk_clientes PRIMARY KEY (id_cliente)
);

CREATE TABLE fashionstore.codigos_recuperacion (
    id_codigo                    BIGSERIAL,
    id_usuario                   BIGINT                   NOT NULL,
    codigo_hash                  VARCHAR(64)              NOT NULL,
    expira_en                    TIMESTAMPTZ              NOT NULL,
    usado                        BOOLEAN                  NOT NULL DEFAULT false,
    intentos_fallidos            INTEGER                  NOT NULL DEFAULT 0,
    ip_solicitante               VARCHAR(45),
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_codigos_recuperacion PRIMARY KEY (id_codigo)
);

CREATE TABLE fashionstore.colecciones (
    id_coleccion                 SERIAL,
    id_temporada                 INTEGER                  NOT NULL,
    id_proveedor                 INTEGER,
    nombre                       VARCHAR(150)             NOT NULL,
    descripcion                  TEXT,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    estado_activo                BOOLEAN                  NOT NULL DEFAULT true,
    actualizado_en               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_colecciones PRIMARY KEY (id_coleccion)
);

CREATE TABLE fashionstore.colores (
    id_color                     SERIAL,
    nombre                       VARCHAR(50)              NOT NULL,
    codigo_hex                   CHAR(7),
    CONSTRAINT pk_colores PRIMARY KEY (id_color),
    CONSTRAINT colores_nombre_key UNIQUE (nombre)
);

CREATE TABLE fashionstore.empleados (
    id_empleado                  BIGINT                   NOT NULL,
    codigo_empleado              VARCHAR(20)              NOT NULL,
    fecha_contratacion           DATE                     NOT NULL DEFAULT CURRENT_DATE,
    cargo                        VARCHAR(100),
    CONSTRAINT pk_empleados PRIMARY KEY (id_empleado),
    CONSTRAINT empleados_codigo_empleado_key UNIQUE (codigo_empleado)
);

CREATE TABLE fashionstore.historial_navegacion (
    id_historial                 BIGSERIAL,
    id_cliente                   BIGINT                   NOT NULL,
    id_producto                  BIGINT                   NOT NULL,
    tipo_evento                  VARCHAR(30)              NOT NULL DEFAULT 'vista'::character varying,
    fecha_hora                   TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_historial_navegacion PRIMARY KEY (id_historial)
);

CREATE TABLE fashionstore.interacciones_chatbot (
    id_interaccion               BIGSERIAL,
    id_cliente                   BIGINT,
    mensaje_usuario              TEXT                     NOT NULL,
    respuesta_ia                 TEXT,
    canal                        fashionstore.canal_origen NOT NULL,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_interacciones_chatbot PRIMARY KEY (id_interaccion)
);

CREATE TABLE fashionstore.inventario_sucursal (
    id_inventario                BIGSERIAL,
    id_variante                  BIGINT                   NOT NULL,
    id_sucursal                  INTEGER                  NOT NULL,
    id_temporada                 INTEGER                  NOT NULL,
    cantidad_disponible          INTEGER                  NOT NULL DEFAULT 0,
    cantidad_reservada           INTEGER                  NOT NULL DEFAULT 0,
    stock_minimo                 INTEGER                  NOT NULL DEFAULT 0,
    estado                       fashionstore.estado_prenda_stock NOT NULL DEFAULT 'disponible'::estado_prenda_stock,
    actualizado_en               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    stock_alerta                 INTEGER                  NOT NULL DEFAULT 5,
    CONSTRAINT pk_inventario_sucursal PRIMARY KEY (id_inventario),
    CONSTRAINT inventario_sucursal_id_variante_id_sucursal_id_temporada_key UNIQUE (id_variante, id_sucursal, id_temporada),
    CONSTRAINT inventario_sucursal_cantidad_disponible_check CHECK ((cantidad_disponible >= 0)),
    CONSTRAINT inventario_sucursal_cantidad_reservada_check CHECK ((cantidad_reservada >= 0))
);

CREATE TABLE fashionstore.movimientos_inventario (
    id_movimiento                BIGSERIAL,
    id_inventario                BIGINT                   NOT NULL,
    tipo_movimiento              fashionstore.tipo_movimiento_inv NOT NULL,
    cantidad                     INTEGER                  NOT NULL,
    id_usuario_responsable       BIGINT,
    referencia_documento         VARCHAR(100),
    observacion                  TEXT,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    saldo_anterior               INTEGER                  NOT NULL DEFAULT 0,
    saldo_nuevo                  INTEGER                  NOT NULL DEFAULT 0,
    CONSTRAINT pk_movimientos_inventario PRIMARY KEY (id_movimiento),
    CONSTRAINT movimientos_inventario_cantidad_check CHECK ((cantidad <> 0))
);

CREATE TABLE fashionstore.pagos (
    id_pago                      BIGSERIAL,
    id_venta                     BIGINT                   NOT NULL,
    metodo_pago                  fashionstore.metodo_pago NOT NULL,
    monto                        NUMERIC(12,2)            NOT NULL,
    estado                       fashionstore.estado_pago NOT NULL DEFAULT 'pendiente'::estado_pago,
    referencia_pasarela          VARCHAR(150),
    payload_respuesta            JSONB,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    confirmado_en                TIMESTAMPTZ,
    CONSTRAINT pk_pagos PRIMARY KEY (id_pago),
    CONSTRAINT pagos_monto_check CHECK ((monto >= (0)::numeric))
);

CREATE TABLE fashionstore.productos (
    id_producto                  BIGSERIAL,
    id_categoria                 INTEGER                  NOT NULL,
    id_coleccion                 INTEGER,
    id_proveedor                 INTEGER,
    nombre                       VARCHAR(200)             NOT NULL,
    descripcion                  TEXT,
    precio_base                  NUMERIC(10,2)            NOT NULL,
    imagen_url                   VARCHAR(500),
    modelo_ar_url                VARCHAR(500),
    activo                       BOOLEAN                  NOT NULL DEFAULT true,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_productos PRIMARY KEY (id_producto),
    CONSTRAINT productos_precio_base_check CHECK ((precio_base >= (0)::numeric))
);

CREATE TABLE fashionstore.promocion_producto (
    id_promocion                 INTEGER                  NOT NULL,
    id_producto                  BIGINT                   NOT NULL,
    CONSTRAINT pk_promocion_producto PRIMARY KEY (id_promocion, id_producto)
);

CREATE TABLE fashionstore.promociones (
    id_promocion                 SERIAL,
    nombre                       VARCHAR(150)             NOT NULL,
    descripcion                  TEXT,
    porcentaje_descuento         NUMERIC(5,2),
    fecha_inicio                 TIMESTAMPTZ              NOT NULL,
    fecha_fin                    TIMESTAMPTZ              NOT NULL,
    estado_activo                BOOLEAN                  NOT NULL DEFAULT true,
    codigo_cupon                 VARCHAR(50),
    tipo_descuento               VARCHAR(20)              NOT NULL DEFAULT 'porcentaje'::character varying,
    valor_descuento              NUMERIC(10,2)            NOT NULL DEFAULT 0.00,
    tope_descuento               NUMERIC(10,2),
    limite_usos                  INTEGER,
    usos_actuales                INTEGER                  NOT NULL DEFAULT 0,
    alcance                      VARCHAR(20)              NOT NULL DEFAULT 'global'::character varying,
    id_categoria                 INTEGER,
    id_producto                  BIGINT,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    actualizado_en               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_promociones PRIMARY KEY (id_promocion),
    CONSTRAINT chk_promociones_alcance_tipo CHECK (((alcance)::text = ANY ((ARRAY['global'::character varying, 'categoria'::character varying, 'producto'::character varying])::text[]))),
    CONSTRAINT chk_promociones_fechas_orden CHECK ((fecha_fin > fecha_inicio)),
    CONSTRAINT chk_promociones_limite_positivo CHECK (((limite_usos IS NULL) OR (limite_usos > 0))),
    CONSTRAINT chk_promociones_porcentaje_tope CHECK ((((tipo_descuento)::text <> 'porcentaje'::text) OR ((valor_descuento >= 1.00) AND (valor_descuento <= 100.00)))),
    CONSTRAINT chk_promociones_tipo_descuento CHECK (((tipo_descuento)::text = ANY ((ARRAY['porcentaje'::character varying, 'monto_fijo'::character varying])::text[]))),
    CONSTRAINT chk_promociones_tope_positivo CHECK (((tope_descuento IS NULL) OR (tope_descuento >= (0)::numeric))),
    CONSTRAINT chk_promociones_usos_no_negativos CHECK ((usos_actuales >= 0)),
    CONSTRAINT chk_promociones_valor_positivo CHECK ((valor_descuento > (0)::numeric))
);

CREATE TABLE fashionstore.proveedores (
    id_proveedor                 SERIAL,
    id_usuario                   BIGINT,
    razon_social                 VARCHAR(200)             NOT NULL,
    nit_rut                      VARCHAR(30),
    contacto_nombre              VARCHAR(150),
    telefono                     VARCHAR(30),
    email                        fashionstore.citext,
    estado_activo                BOOLEAN                  NOT NULL DEFAULT true,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    direccion                    VARCHAR(255)             DEFAULT 'Direccion no registrada'::character varying,
    ciudad                       VARCHAR(80)              DEFAULT 'La Paz'::character varying,
    rubro                        VARCHAR(80)              DEFAULT 'Confeccion Textil'::character varying,
    actualizado_en               TIMESTAMPTZ              DEFAULT now(),
    CONSTRAINT pk_proveedores PRIMARY KEY (id_proveedor),
    CONSTRAINT proveedores_nit_key UNIQUE (nit_rut)
);

CREATE TABLE fashionstore.recomendaciones_ia (
    id_recomendacion             BIGSERIAL,
    id_cliente                   BIGINT                   NOT NULL,
    id_producto                  BIGINT                   NOT NULL,
    score_relevancia             NUMERIC(5,4)             NOT NULL,
    motivo                       VARCHAR(255),
    generado_en                  TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_recomendaciones_ia PRIMARY KEY (id_recomendacion),
    CONSTRAINT recomendaciones_ia_score_relevancia_check CHECK (((score_relevancia >= (0)::numeric) AND (score_relevancia <= (1)::numeric)))
);

CREATE TABLE fashionstore.reserva_detalle (
    id_reserva_detalle           BIGSERIAL,
    id_reserva                   BIGINT                   NOT NULL,
    id_variante                  BIGINT                   NOT NULL,
    cantidad                     INTEGER                  NOT NULL DEFAULT 1,
    CONSTRAINT pk_reserva_detalle PRIMARY KEY (id_reserva_detalle),
    CONSTRAINT reserva_detalle_id_reserva_id_variante_key UNIQUE (id_reserva, id_variante),
    CONSTRAINT reserva_detalle_cantidad_check CHECK ((cantidad > 0))
);

CREATE TABLE fashionstore.reservas (
    id_reserva                   BIGSERIAL,
    id_cliente                   BIGINT                   NOT NULL,
    id_sucursal                  INTEGER                  NOT NULL,
    fecha_hora_atencion          TIMESTAMPTZ              NOT NULL,
    estado                       fashionstore.estado_reserva NOT NULL DEFAULT 'pendiente'::estado_reserva,
    canal_origen                 fashionstore.canal_origen NOT NULL,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    atendido_por                 BIGINT,
    atendido_en                  TIMESTAMPTZ,
    observacion                  TEXT,
    CONSTRAINT pk_reservas PRIMARY KEY (id_reserva)
);

CREATE TABLE fashionstore.sesiones_vestidor_virtual (
    id_sesion_ar                 BIGSERIAL,
    id_cliente                   BIGINT                   NOT NULL,
    id_producto                  BIGINT                   NOT NULL,
    dispositivo                  VARCHAR(50),
    fecha_hora                   TIMESTAMPTZ              NOT NULL DEFAULT now(),
    resultado_url                VARCHAR(500),
    genero_interes               BOOLEAN                  NOT NULL DEFAULT false,
    CONSTRAINT pk_sesiones_vestidor_virtual PRIMARY KEY (id_sesion_ar)
);

CREATE TABLE fashionstore.solicitudes_reporte_ia (
    id_solicitud                 BIGSERIAL,
    id_usuario                   BIGINT                   NOT NULL,
    comando_voz_texto            TEXT                     NOT NULL,
    tipo_reporte                 VARCHAR(100),
    resultado_url                VARCHAR(500),
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_solicitudes_reporte_ia PRIMARY KEY (id_solicitud)
);

CREATE TABLE fashionstore.sucursales (
    id_sucursal                  SERIAL,
    id_ciudad                    INTEGER                  NOT NULL,
    nombre                       VARCHAR(150)             NOT NULL,
    direccion                    VARCHAR(255)             NOT NULL,
    telefono                     VARCHAR(30),
    horario_apertura             TIME WITHOUT TIME ZONE   NOT NULL DEFAULT '09:00:00'::time without time zone,
    horario_cierre               TIME WITHOUT TIME ZONE   NOT NULL DEFAULT '20:00:00'::time without time zone,
    activa                       BOOLEAN                  NOT NULL DEFAULT true,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_sucursales PRIMARY KEY (id_sucursal),
    CONSTRAINT sucursales_id_ciudad_nombre_key UNIQUE (id_ciudad, nombre)
);

CREATE TABLE fashionstore.tallas (
    id_talla                     SERIAL,
    codigo                       VARCHAR(10)              NOT NULL,
    orden                        SMALLINT                 NOT NULL DEFAULT 0,
    CONSTRAINT pk_tallas PRIMARY KEY (id_talla),
    CONSTRAINT tallas_codigo_key UNIQUE (codigo)
);

CREATE TABLE fashionstore.temporadas (
    id_temporada                 SERIAL,
    nombre                       VARCHAR(100)             NOT NULL,
    tipo                         fashionstore.tipo_temporada,
    fecha_inicio                 DATE                     NOT NULL,
    fecha_fin                    DATE                     NOT NULL,
    estado_activo                BOOLEAN                  NOT NULL DEFAULT true,
    anio                         INTEGER                  NOT NULL DEFAULT EXTRACT(year FROM CURRENT_DATE),
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    actualizado_en               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_temporadas PRIMARY KEY (id_temporada),
    CONSTRAINT chk_temporadas_anio_valido CHECK ((anio >= 2020)),
    CONSTRAINT chk_temporadas_fechas_orden CHECK ((fecha_fin > fecha_inicio)),
    CONSTRAINT temporadas_check CHECK ((fecha_fin >= fecha_inicio))
);

CREATE TABLE fashionstore.usuarios (
    id_usuario                   BIGSERIAL,
    email                        fashionstore.citext      NOT NULL,
    password_hash                VARCHAR(255)             NOT NULL,
    nombres                      VARCHAR(100)             NOT NULL,
    apellidos                    VARCHAR(100)             NOT NULL,
    telefono                     VARCHAR(30),
    rol                          fashionstore.rol_usuario NOT NULL DEFAULT 'cliente'::rol_usuario,
    id_sucursal                  INTEGER,
    activo                       BOOLEAN                  NOT NULL DEFAULT true,
    fecha_registro               TIMESTAMPTZ              NOT NULL DEFAULT now(),
    ultimo_acceso                TIMESTAMPTZ,
    CONSTRAINT pk_usuarios PRIMARY KEY (id_usuario),
    CONSTRAINT usuarios_email_key UNIQUE (email)
);

CREATE TABLE fashionstore.variantes_producto (
    id_variante                  BIGSERIAL,
    id_producto                  BIGINT                   NOT NULL,
    id_talla                     INTEGER                  NOT NULL,
    id_color                     INTEGER                  NOT NULL,
    sku                          VARCHAR(50)              NOT NULL,
    precio_extra                 NUMERIC(10,2)            NOT NULL DEFAULT 0,
    activo                       BOOLEAN                  NOT NULL DEFAULT true,
    creado_en                    TIMESTAMPTZ              NOT NULL DEFAULT now(),
    CONSTRAINT pk_variantes_producto PRIMARY KEY (id_variante),
    CONSTRAINT variantes_producto_id_producto_id_talla_id_color_key UNIQUE (id_producto, id_talla, id_color),
    CONSTRAINT variantes_producto_sku_key UNIQUE (sku)
);

CREATE TABLE fashionstore.venta_detalle (
    id_venta_detalle             BIGSERIAL,
    id_venta                     BIGINT                   NOT NULL,
    id_variante                  BIGINT                   NOT NULL,
    cantidad                     INTEGER                  NOT NULL,
    precio_unitario              NUMERIC(10,2)            NOT NULL,
    subtotal_linea               NUMERIC(12,2),
    id_sucursal                  INTEGER,
    CONSTRAINT pk_venta_detalle PRIMARY KEY (id_venta_detalle),
    CONSTRAINT venta_detalle_cantidad_check CHECK ((cantidad > 0)),
    CONSTRAINT venta_detalle_precio_unitario_check CHECK ((precio_unitario >= (0)::numeric))
);

CREATE TABLE fashionstore.ventas (
    id_venta                     BIGSERIAL,
    numero_comprobante           VARCHAR(30)              NOT NULL,
    id_cliente                   BIGINT,
    id_sucursal                  INTEGER                  NOT NULL,
    id_cajero                    BIGINT,
    id_reserva                   BIGINT,
    tipo_venta                   fashionstore.tipo_venta  NOT NULL,
    estado                       fashionstore.estado_venta NOT NULL DEFAULT 'pendiente'::estado_venta,
    subtotal                     NUMERIC(12,2)            NOT NULL DEFAULT 0,
    descuento                    NUMERIC(12,2)            NOT NULL DEFAULT 0,
    total                        NUMERIC(12,2)            NOT NULL DEFAULT 0,
    fecha_venta                  TIMESTAMPTZ              NOT NULL DEFAULT now(),
    tipo_entrega                 VARCHAR(20)              NOT NULL DEFAULT 'domicilio'::character varying,
    id_sucursal_retiro           INTEGER,
    direccion_envio              TEXT,
    id_promocion                 INTEGER,
    CONSTRAINT pk_ventas PRIMARY KEY (id_venta),
    CONSTRAINT ventas_numero_comprobante_key UNIQUE (numero_comprobante),
    CONSTRAINT ck_ventas_tipo_entrega CHECK (((tipo_entrega)::text = ANY ((ARRAY['domicilio'::character varying, 'recogida_boutique'::character varying])::text[]))),
    CONSTRAINT ventas_total_check CHECK ((total >= (0)::numeric))
);

-- ----------------------------------------------------------------------------
-- 4. RESTRICCIONES DE INTEGRIDAD REFERENCIAL (FOREIGN KEYS)
-- ----------------------------------------------------------------------------
ALTER TABLE fashionstore.bitacora ADD CONSTRAINT bitacora_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE fashionstore.carrito_detalle ADD CONSTRAINT carrito_detalle_id_carrito_fkey FOREIGN KEY (id_carrito) REFERENCES fashionstore.carritos(id_carrito) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.carrito_detalle ADD CONSTRAINT carrito_detalle_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.carrito_detalle ADD CONSTRAINT carrito_detalle_id_variante_fkey FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.carritos ADD CONSTRAINT carritos_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.categorias ADD CONSTRAINT categorias_id_categoria_padre_fkey FOREIGN KEY (id_categoria_padre) REFERENCES fashionstore.categorias(id_categoria) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.clientes ADD CONSTRAINT clientes_ciudad_preferida_fkey FOREIGN KEY (ciudad_preferida) REFERENCES fashionstore.ciudades(id_ciudad) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.clientes ADD CONSTRAINT clientes_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.codigos_recuperacion ADD CONSTRAINT fk_codigos_recuperacion_usuario FOREIGN KEY (id_usuario) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.colecciones ADD CONSTRAINT colecciones_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES fashionstore.proveedores(id_proveedor) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.colecciones ADD CONSTRAINT colecciones_id_temporada_fkey FOREIGN KEY (id_temporada) REFERENCES fashionstore.temporadas(id_temporada) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.empleados ADD CONSTRAINT empleados_id_empleado_fkey FOREIGN KEY (id_empleado) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.historial_navegacion ADD CONSTRAINT historial_navegacion_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.historial_navegacion ADD CONSTRAINT historial_navegacion_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.interacciones_chatbot ADD CONSTRAINT interacciones_chatbot_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.inventario_sucursal ADD CONSTRAINT inventario_sucursal_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.inventario_sucursal ADD CONSTRAINT inventario_sucursal_id_temporada_fkey FOREIGN KEY (id_temporada) REFERENCES fashionstore.temporadas(id_temporada) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.inventario_sucursal ADD CONSTRAINT inventario_sucursal_id_variante_fkey FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.movimientos_inventario ADD CONSTRAINT movimientos_inventario_id_inventario_fkey FOREIGN KEY (id_inventario) REFERENCES fashionstore.inventario_sucursal(id_inventario) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.movimientos_inventario ADD CONSTRAINT movimientos_inventario_id_usuario_responsable_fkey FOREIGN KEY (id_usuario_responsable) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.pagos ADD CONSTRAINT pagos_id_venta_fkey FOREIGN KEY (id_venta) REFERENCES fashionstore.ventas(id_venta) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.productos ADD CONSTRAINT productos_id_categoria_fkey FOREIGN KEY (id_categoria) REFERENCES fashionstore.categorias(id_categoria) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.productos ADD CONSTRAINT productos_id_coleccion_fkey FOREIGN KEY (id_coleccion) REFERENCES fashionstore.colecciones(id_coleccion) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.productos ADD CONSTRAINT productos_id_proveedor_fkey FOREIGN KEY (id_proveedor) REFERENCES fashionstore.proveedores(id_proveedor) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.promocion_producto ADD CONSTRAINT promocion_producto_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.promocion_producto ADD CONSTRAINT promocion_producto_id_promocion_fkey FOREIGN KEY (id_promocion) REFERENCES fashionstore.promociones(id_promocion) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.promociones ADD CONSTRAINT fk_promociones_categoria FOREIGN KEY (id_categoria) REFERENCES fashionstore.categorias(id_categoria) ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE fashionstore.promociones ADD CONSTRAINT fk_promociones_producto FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE SET NULL;
ALTER TABLE fashionstore.proveedores ADD CONSTRAINT proveedores_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.recomendaciones_ia ADD CONSTRAINT recomendaciones_ia_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.recomendaciones_ia ADD CONSTRAINT recomendaciones_ia_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.reserva_detalle ADD CONSTRAINT reserva_detalle_id_reserva_fkey FOREIGN KEY (id_reserva) REFERENCES fashionstore.reservas(id_reserva) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.reserva_detalle ADD CONSTRAINT reserva_detalle_id_variante_fkey FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.reservas ADD CONSTRAINT reservas_atendido_por_fkey FOREIGN KEY (atendido_por) REFERENCES fashionstore.empleados(id_empleado) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.reservas ADD CONSTRAINT reservas_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.reservas ADD CONSTRAINT reservas_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.sesiones_vestidor_virtual ADD CONSTRAINT sesiones_vestidor_virtual_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.sesiones_vestidor_virtual ADD CONSTRAINT sesiones_vestidor_virtual_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.solicitudes_reporte_ia ADD CONSTRAINT solicitudes_reporte_ia_id_usuario_fkey FOREIGN KEY (id_usuario) REFERENCES fashionstore.usuarios(id_usuario) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.sucursales ADD CONSTRAINT sucursales_id_ciudad_fkey FOREIGN KEY (id_ciudad) REFERENCES fashionstore.ciudades(id_ciudad) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.usuarios ADD CONSTRAINT usuarios_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.variantes_producto ADD CONSTRAINT variantes_producto_id_color_fkey FOREIGN KEY (id_color) REFERENCES fashionstore.colores(id_color) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.variantes_producto ADD CONSTRAINT variantes_producto_id_producto_fkey FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.variantes_producto ADD CONSTRAINT variantes_producto_id_talla_fkey FOREIGN KEY (id_talla) REFERENCES fashionstore.tallas(id_talla) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.venta_detalle ADD CONSTRAINT venta_detalle_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.venta_detalle ADD CONSTRAINT venta_detalle_id_variante_fkey FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.venta_detalle ADD CONSTRAINT venta_detalle_id_venta_fkey FOREIGN KEY (id_venta) REFERENCES fashionstore.ventas(id_venta) ON UPDATE NO ACTION ON DELETE CASCADE;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT fk_ventas_id_promocion FOREIGN KEY (id_promocion) REFERENCES fashionstore.promociones(id_promocion) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT fk_ventas_sucursal_retiro FOREIGN KEY (id_sucursal_retiro) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT ventas_id_cajero_fkey FOREIGN KEY (id_cajero) REFERENCES fashionstore.empleados(id_empleado) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT ventas_id_cliente_fkey FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT ventas_id_reserva_fkey FOREIGN KEY (id_reserva) REFERENCES fashionstore.reservas(id_reserva) ON UPDATE NO ACTION ON DELETE NO ACTION;
ALTER TABLE fashionstore.ventas ADD CONSTRAINT ventas_id_sucursal_fkey FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal) ON UPDATE NO ACTION ON DELETE NO ACTION;

-- ----------------------------------------------------------------------------
-- 5. ÍNDICES
-- ----------------------------------------------------------------------------
CREATE INDEX idx_bitacora_creado_en ON fashionstore.bitacora USING btree (creado_en DESC);
CREATE INDEX idx_bitacora_modulo ON fashionstore.bitacora USING btree (tabla_modulo);
CREATE INDEX idx_bitacora_severidad ON fashionstore.bitacora USING btree (severidad);
CREATE INDEX idx_bitacora_usuario ON fashionstore.bitacora USING btree (id_usuario);
CREATE INDEX ix_fashionstore_codigos_recuperacion_codigo_hash ON fashionstore.codigos_recuperacion USING btree (codigo_hash);
CREATE INDEX ix_fashionstore_codigos_recuperacion_id_usuario ON fashionstore.codigos_recuperacion USING btree (id_usuario);
CREATE INDEX idx_colecciones_estado ON fashionstore.colecciones USING btree (estado_activo);
CREATE INDEX idx_colecciones_temporada ON fashionstore.colecciones USING btree (id_temporada);
CREATE UNIQUE INDEX uq_colecciones_temporada_nombre_lower ON fashionstore.colecciones USING btree (id_temporada, lower(TRIM(BOTH FROM nombre)));
CREATE INDEX idx_hist_nav_cliente ON fashionstore.historial_navegacion USING btree (id_cliente);
CREATE INDEX idx_hist_nav_producto ON fashionstore.historial_navegacion USING btree (id_producto);
CREATE INDEX idx_inventario_estado ON fashionstore.inventario_sucursal USING btree (estado);
CREATE INDEX idx_inventario_sucursal ON fashionstore.inventario_sucursal USING btree (id_sucursal);
CREATE INDEX idx_inventario_variante ON fashionstore.inventario_sucursal USING btree (id_variante);
CREATE INDEX idx_mov_inv_inventario ON fashionstore.movimientos_inventario USING btree (id_inventario);
CREATE INDEX idx_mov_inv_tipo ON fashionstore.movimientos_inventario USING btree (tipo_movimiento);
CREATE INDEX idx_pagos_estado ON fashionstore.pagos USING btree (estado);
CREATE INDEX idx_pagos_venta ON fashionstore.pagos USING btree (id_venta);
CREATE INDEX idx_productos_categoria ON fashionstore.productos USING btree (id_categoria);
CREATE INDEX idx_productos_coleccion ON fashionstore.productos USING btree (id_coleccion);
CREATE INDEX idx_productos_nombre_trgm ON fashionstore.productos USING gin (nombre gin_trgm_ops);
CREATE INDEX ix_promociones_alcance ON fashionstore.promociones USING btree (alcance, id_categoria, id_producto);
CREATE INDEX ix_promociones_fechas_vigencia ON fashionstore.promociones USING btree (fecha_inicio, fecha_fin, estado_activo);
CREATE UNIQUE INDEX uq_promociones_codigo_cupon_lower ON fashionstore.promociones USING btree (lower(TRIM(BOTH FROM codigo_cupon))) WHERE (codigo_cupon IS NOT NULL);
CREATE INDEX idx_proveedores_estado ON fashionstore.proveedores USING btree (estado_activo);
CREATE INDEX idx_proveedores_rubro ON fashionstore.proveedores USING btree (rubro);
CREATE UNIQUE INDEX uq_proveedores_nit_rut ON fashionstore.proveedores USING btree (nit_rut);
CREATE UNIQUE INDEX uq_proveedores_razon_social ON fashionstore.proveedores USING btree (lower((razon_social)::text));
CREATE INDEX idx_recom_cliente ON fashionstore.recomendaciones_ia USING btree (id_cliente, score_relevancia DESC);
CREATE INDEX idx_reservas_cliente ON fashionstore.reservas USING btree (id_cliente);
CREATE INDEX idx_reservas_estado ON fashionstore.reservas USING btree (estado);
CREATE INDEX idx_reservas_sucursal ON fashionstore.reservas USING btree (id_sucursal, fecha_hora_atencion);
CREATE INDEX idx_ar_cliente ON fashionstore.sesiones_vestidor_virtual USING btree (id_cliente);
CREATE INDEX idx_ar_producto ON fashionstore.sesiones_vestidor_virtual USING btree (id_producto);
CREATE INDEX idx_temporadas_anio ON fashionstore.temporadas USING btree (anio);
CREATE INDEX idx_temporadas_estado ON fashionstore.temporadas USING btree (estado_activo);
CREATE UNIQUE INDEX uq_temporadas_nombre_lower ON fashionstore.temporadas USING btree (lower(TRIM(BOTH FROM nombre)));
CREATE INDEX idx_usuarios_rol ON fashionstore.usuarios USING btree (rol);
CREATE INDEX idx_usuarios_sucursal ON fashionstore.usuarios USING btree (id_sucursal);
CREATE INDEX idx_venta_detalle_venta ON fashionstore.venta_detalle USING btree (id_venta);
CREATE INDEX ix_venta_detalle_id_sucursal ON fashionstore.venta_detalle USING btree (id_sucursal);
CREATE INDEX idx_ventas_cliente ON fashionstore.ventas USING btree (id_cliente);
CREATE INDEX idx_ventas_estado ON fashionstore.ventas USING btree (estado);
CREATE INDEX idx_ventas_sucursal ON fashionstore.ventas USING btree (id_sucursal, fecha_venta);
CREATE INDEX idx_ventas_tipo ON fashionstore.ventas USING btree (tipo_venta);

-- ----------------------------------------------------------------------------
-- 6. TRIGGERS Y FUNCIONES
-- ----------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION fashionstore.fn_actualizar_estado_inventario()
RETURNS trigger AS $$
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
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_inventario_estado
BEFORE INSERT OR UPDATE ON fashionstore.inventario_sucursal
FOR EACH ROW
EXECUTE FUNCTION fashionstore.fn_actualizar_estado_inventario();

-- ----------------------------------------------------------------------------
-- 7. VISTAS
-- ----------------------------------------------------------------------------
CREATE OR REPLACE VIEW fashionstore.vw_inventario_consolidado AS
 SELECT s.id_sucursal,
    s.nombre AS sucursal,
    p.id_producto,
    p.nombre AS producto,
    t.codigo AS talla,
    c.nombre AS color,
    tp.nombre AS temporada,
    inv.cantidad_disponible,
    inv.cantidad_reservada,
    inv.estado
   FROM ((((((fashionstore.inventario_sucursal inv
     JOIN fashionstore.variantes_producto vp ON ((vp.id_variante = inv.id_variante)))
     JOIN fashionstore.productos p ON ((p.id_producto = vp.id_producto)))
     JOIN fashionstore.tallas t ON ((t.id_talla = vp.id_talla)))
     JOIN fashionstore.colores c ON ((c.id_color = vp.id_color)))
     JOIN fashionstore.sucursales s ON ((s.id_sucursal = inv.id_sucursal)))
     JOIN fashionstore.temporadas tp ON ((tp.id_temporada = inv.id_temporada)));

CREATE OR REPLACE VIEW fashionstore.vw_reservas_pendientes AS
 SELECT r.id_reserva,
    r.id_sucursal,
    s.nombre AS sucursal,
    (((u.nombres)::text || ' '::text) || (u.apellidos)::text) AS cliente,
    r.fecha_hora_atencion,
    r.estado
   FROM ((fashionstore.reservas r
     JOIN fashionstore.sucursales s ON ((s.id_sucursal = r.id_sucursal)))
     JOIN fashionstore.usuarios u ON ((u.id_usuario = r.id_cliente)))
  WHERE (r.estado = ANY (ARRAY['pendiente'::fashionstore.estado_reserva, 'confirmada'::fashionstore.estado_reserva]));

CREATE OR REPLACE VIEW fashionstore.vw_ventas_por_sucursal AS
 SELECT v.id_sucursal,
    s.nombre AS sucursal,
    v.tipo_venta,
    (date_trunc('day'::text, v.fecha_venta))::date AS fecha,
    count(*) AS cantidad_ventas,
    sum(v.total) AS total_vendido
   FROM (fashionstore.ventas v
     JOIN fashionstore.sucursales s ON ((s.id_sucursal = v.id_sucursal)))
  WHERE (v.estado = 'pagada'::fashionstore.estado_venta)
  GROUP BY v.id_sucursal, s.nombre, v.tipo_venta, (date_trunc('day'::text, v.fecha_venta));
