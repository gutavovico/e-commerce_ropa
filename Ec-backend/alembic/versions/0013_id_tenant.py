"""P2-CU13 · Fundación multitenant (2/3): `id_tenant` en las tablas de negocio.

Spec: `.specs/changes/P2-CU13-CU12-fundacion-multitenant/spec.md` §A.2 (decisiones F1, F2, F8, F9,
F10 y F11).

- Todas las filas actuales pasan a la empresa 1 (FASHION STORE).
- `id_tenant` toma por defecto la empresa del contexto de la transacción (F2).
- Las claves únicas de negocio pasan a ser por empresa (RN05, RN20, RN28).
- Las claves foráneas entre tablas de empresa pasan a ser compuestas `(id_tenant, fk)`, de modo que
  la base de datos impide relacionar filas de empresas distintas (RNF02). Las que apuntan a un
  cliente pasan a apuntar a `cliente_tenant`: un cliente solo opera donde está registrado (F9).
- Crea `empleado_sucursal` (sucursales autorizadas, RN07) a partir de `usuarios.id_sucursal` (F10).

Las definiciones originales de las claves están copiadas del esquema de Neon (2026-11-08) para que
el downgrade las restaure tal cual.

Revision ID: 0013
Revises: 0012
Create Date: 2026-11-08
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0013"
down_revision: Union[str, None] = "0012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

S = "fashionstore"
CONTEXTO_TENANT = "NULLIF(current_setting('app.id_tenant', true), '')::bigint"
ROLES_SIN_EMPRESA = "('cliente', 'super_administrador')"

#: Tablas de negocio de una sola empresa → su clave primaria (None si es compuesta y nadie la referencia).
TABLAS_TENANT = {
    "sucursales": "id_sucursal",
    "empleados": "id_empleado",
    "proveedores": "id_proveedor",
    "temporadas": "id_temporada",
    "colecciones": "id_coleccion",
    "categorias": "id_categoria",
    "productos": "id_producto",
    "variantes_producto": "id_variante",
    "inventario_sucursal": "id_inventario",
    "movimientos_inventario": "id_movimiento",
    "reservas": "id_reserva",
    "reserva_detalle": "id_reserva_detalle",
    "carritos": "id_carrito",
    "carrito_detalle": "id_carrito_detalle",
    "ventas": "id_venta",
    "venta_detalle": "id_venta_detalle",
    "pagos": "id_pago",
    "promociones": "id_promocion",
    "promocion_producto": None,
    "historial_navegacion": "id_historial",
    "recomendaciones_ia": "id_recomendacion",
    "interacciones_chatbot": "id_interaccion",
    "sesiones_vestidor_virtual": "id_sesion_ar",
    "solicitudes_reporte_ia": "id_solicitud",
}

#: Claves foráneas que pasan a ser compuestas:
#: (tabla, constraint original, columna, tabla referida, columna referida, ON DELETE, definición original)
FKS_COMPUESTAS = [
    ("usuarios", "usuarios_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("colecciones", "colecciones_id_proveedor_fkey", "id_proveedor", "proveedores", "id_proveedor", "",
     "FOREIGN KEY (id_proveedor) REFERENCES fashionstore.proveedores(id_proveedor)"),
    ("colecciones", "colecciones_id_temporada_fkey", "id_temporada", "temporadas", "id_temporada", "",
     "FOREIGN KEY (id_temporada) REFERENCES fashionstore.temporadas(id_temporada)"),
    ("categorias", "categorias_id_categoria_padre_fkey", "id_categoria_padre", "categorias", "id_categoria", "",
     "FOREIGN KEY (id_categoria_padre) REFERENCES fashionstore.categorias(id_categoria)"),
    ("productos", "productos_id_categoria_fkey", "id_categoria", "categorias", "id_categoria", "",
     "FOREIGN KEY (id_categoria) REFERENCES fashionstore.categorias(id_categoria)"),
    ("productos", "productos_id_coleccion_fkey", "id_coleccion", "colecciones", "id_coleccion", "",
     "FOREIGN KEY (id_coleccion) REFERENCES fashionstore.colecciones(id_coleccion)"),
    ("productos", "productos_id_proveedor_fkey", "id_proveedor", "proveedores", "id_proveedor", "",
     "FOREIGN KEY (id_proveedor) REFERENCES fashionstore.proveedores(id_proveedor)"),
    ("variantes_producto", "variantes_producto_id_producto_fkey", "id_producto", "productos", "id_producto", "CASCADE",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON DELETE CASCADE"),
    ("inventario_sucursal", "inventario_sucursal_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("inventario_sucursal", "inventario_sucursal_id_temporada_fkey", "id_temporada", "temporadas", "id_temporada", "",
     "FOREIGN KEY (id_temporada) REFERENCES fashionstore.temporadas(id_temporada)"),
    ("inventario_sucursal", "inventario_sucursal_id_variante_fkey", "id_variante", "variantes_producto", "id_variante", "",
     "FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante)"),
    ("movimientos_inventario", "movimientos_inventario_id_inventario_fkey", "id_inventario", "inventario_sucursal", "id_inventario", "",
     "FOREIGN KEY (id_inventario) REFERENCES fashionstore.inventario_sucursal(id_inventario)"),
    ("reservas", "reservas_atendido_por_fkey", "atendido_por", "empleados", "id_empleado", "",
     "FOREIGN KEY (atendido_por) REFERENCES fashionstore.empleados(id_empleado)"),
    ("reservas", "reservas_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("reservas", "reservas_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("reserva_detalle", "reserva_detalle_id_reserva_fkey", "id_reserva", "reservas", "id_reserva", "CASCADE",
     "FOREIGN KEY (id_reserva) REFERENCES fashionstore.reservas(id_reserva) ON DELETE CASCADE"),
    ("reserva_detalle", "reserva_detalle_id_variante_fkey", "id_variante", "variantes_producto", "id_variante", "",
     "FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante)"),
    ("sesiones_vestidor_virtual", "sesiones_vestidor_virtual_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("sesiones_vestidor_virtual", "sesiones_vestidor_virtual_id_producto_fkey", "id_producto", "productos", "id_producto", "",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto)"),
    ("carritos", "carritos_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("carrito_detalle", "carrito_detalle_id_carrito_fkey", "id_carrito", "carritos", "id_carrito", "CASCADE",
     "FOREIGN KEY (id_carrito) REFERENCES fashionstore.carritos(id_carrito) ON DELETE CASCADE"),
    ("carrito_detalle", "carrito_detalle_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("carrito_detalle", "carrito_detalle_id_variante_fkey", "id_variante", "variantes_producto", "id_variante", "",
     "FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante)"),
    ("ventas", "ventas_id_cajero_fkey", "id_cajero", "empleados", "id_empleado", "",
     "FOREIGN KEY (id_cajero) REFERENCES fashionstore.empleados(id_empleado)"),
    ("ventas", "ventas_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("ventas", "ventas_id_promocion_fkey", "id_promocion", "promociones", "id_promocion", "",
     "FOREIGN KEY (id_promocion) REFERENCES fashionstore.promociones(id_promocion)"),
    ("ventas", "ventas_id_reserva_fkey", "id_reserva", "reservas", "id_reserva", "",
     "FOREIGN KEY (id_reserva) REFERENCES fashionstore.reservas(id_reserva)"),
    ("ventas", "ventas_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("ventas", "ventas_id_sucursal_retiro_fkey", "id_sucursal_retiro", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal_retiro) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("venta_detalle", "venta_detalle_id_sucursal_fkey", "id_sucursal", "sucursales", "id_sucursal", "",
     "FOREIGN KEY (id_sucursal) REFERENCES fashionstore.sucursales(id_sucursal)"),
    ("venta_detalle", "venta_detalle_id_variante_fkey", "id_variante", "variantes_producto", "id_variante", "",
     "FOREIGN KEY (id_variante) REFERENCES fashionstore.variantes_producto(id_variante)"),
    ("venta_detalle", "venta_detalle_id_venta_fkey", "id_venta", "ventas", "id_venta", "CASCADE",
     "FOREIGN KEY (id_venta) REFERENCES fashionstore.ventas(id_venta) ON DELETE CASCADE"),
    ("pagos", "pagos_id_venta_fkey", "id_venta", "ventas", "id_venta", "CASCADE",
     "FOREIGN KEY (id_venta) REFERENCES fashionstore.ventas(id_venta) ON DELETE CASCADE"),
    ("promociones", "promociones_id_categoria_fkey", "id_categoria", "categorias", "id_categoria", "SET NULL (id_categoria)",
     "FOREIGN KEY (id_categoria) REFERENCES fashionstore.categorias(id_categoria) ON DELETE SET NULL"),
    ("promociones", "promociones_id_producto_fkey", "id_producto", "productos", "id_producto", "SET NULL (id_producto)",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON DELETE SET NULL"),
    ("promocion_producto", "promocion_producto_id_producto_fkey", "id_producto", "productos", "id_producto", "CASCADE",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto) ON DELETE CASCADE"),
    ("promocion_producto", "promocion_producto_id_promocion_fkey", "id_promocion", "promociones", "id_promocion", "CASCADE",
     "FOREIGN KEY (id_promocion) REFERENCES fashionstore.promociones(id_promocion) ON DELETE CASCADE"),
    ("historial_navegacion", "historial_navegacion_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("historial_navegacion", "historial_navegacion_id_producto_fkey", "id_producto", "productos", "id_producto", "",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto)"),
    ("recomendaciones_ia", "recomendaciones_ia_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
    ("recomendaciones_ia", "recomendaciones_ia_id_producto_fkey", "id_producto", "productos", "id_producto", "",
     "FOREIGN KEY (id_producto) REFERENCES fashionstore.productos(id_producto)"),
    ("interacciones_chatbot", "interacciones_chatbot_id_cliente_fkey", "id_cliente", "cliente_tenant", "id_cliente", "",
     "FOREIGN KEY (id_cliente) REFERENCES fashionstore.clientes(id_cliente)"),
]

#: Claves únicas globales que pasan a ser por empresa: (tabla, nombre original, definición original, definición nueva)
#: `None` como definición original indica un índice único (no una constraint).
UNICAS = [
    ("categorias", "categorias_nombre_key", "UNIQUE (nombre)",
     "CONSTRAINT categorias_tenant_nombre_key UNIQUE (id_tenant, nombre)"),
    ("empleados", "empleados_codigo_empleado_key", "UNIQUE (codigo_empleado)",
     "CONSTRAINT empleados_tenant_codigo_key UNIQUE (id_tenant, codigo_empleado)"),
    ("proveedores", "proveedores_nit_key", "UNIQUE (nit_rut)",
     "CONSTRAINT proveedores_tenant_nit_key UNIQUE (id_tenant, nit_rut)"),
    ("sucursales", "sucursales_id_ciudad_nombre_key", "UNIQUE (id_ciudad, nombre)",
     "CONSTRAINT sucursales_tenant_ciudad_nombre_key UNIQUE (id_tenant, id_ciudad, nombre)"),
    ("variantes_producto", "variantes_producto_sku_key", "UNIQUE (sku)",
     "CONSTRAINT variantes_producto_tenant_sku_key UNIQUE (id_tenant, sku)"),
    ("ventas", "ventas_numero_comprobante_key", "UNIQUE (numero_comprobante)",
     "CONSTRAINT ventas_tenant_comprobante_key UNIQUE (id_tenant, numero_comprobante)"),
    ("carritos", "carritos_id_cliente_key", "UNIQUE (id_cliente)",
     "CONSTRAINT carritos_tenant_cliente_key UNIQUE (id_tenant, id_cliente)"),
]

#: Índices únicos que pasan a ser por empresa: (nombre, definición original, nombre nuevo, definición nueva)
INDICES_UNICOS = [
    ("uq_proveedores_nit_rut",
     "CREATE UNIQUE INDEX uq_proveedores_nit_rut ON fashionstore.proveedores USING btree (nit_rut)",
     None, None),  # duplicaba proveedores_nit_key; la nueva constraint por empresa lo cubre
    ("uq_proveedores_razon_social",
     "CREATE UNIQUE INDEX uq_proveedores_razon_social ON fashionstore.proveedores USING btree (lower((razon_social)::text))",
     "uq_proveedores_tenant_razon_social",
     "CREATE UNIQUE INDEX uq_proveedores_tenant_razon_social ON fashionstore.proveedores (id_tenant, lower((razon_social)::text))"),
    ("uq_promociones_codigo_cupon_lower",
     "CREATE UNIQUE INDEX uq_promociones_codigo_cupon_lower ON fashionstore.promociones USING btree (lower(TRIM(BOTH FROM codigo_cupon))) WHERE (codigo_cupon IS NOT NULL)",
     "uq_promociones_tenant_cupon",
     "CREATE UNIQUE INDEX uq_promociones_tenant_cupon ON fashionstore.promociones (id_tenant, lower(TRIM(BOTH FROM codigo_cupon))) WHERE (codigo_cupon IS NOT NULL)"),
    ("uq_temporadas_nombre_lower",
     "CREATE UNIQUE INDEX uq_temporadas_nombre_lower ON fashionstore.temporadas USING btree (lower(TRIM(BOTH FROM nombre)))",
     "uq_temporadas_tenant_nombre",
     "CREATE UNIQUE INDEX uq_temporadas_tenant_nombre ON fashionstore.temporadas (id_tenant, lower(TRIM(BOTH FROM nombre)))"),
]


def _nombre_fk(tabla: str, columna: str) -> str:
    return f"fk_{tabla}_{columna}_tenant"


def upgrade() -> None:
    sql: list[str] = []

    # 1. id_tenant en las tablas de una sola empresa ------------------------------------------
    for tabla, pk in TABLAS_TENANT.items():
        sql += [
            f"ALTER TABLE {S}.{tabla} ADD COLUMN id_tenant BIGINT",
            f"UPDATE {S}.{tabla} SET id_tenant = 1",
            f"ALTER TABLE {S}.{tabla} ALTER COLUMN id_tenant SET NOT NULL",
            f"ALTER TABLE {S}.{tabla} ALTER COLUMN id_tenant SET DEFAULT {CONTEXTO_TENANT}",
            f"ALTER TABLE {S}.{tabla} ADD CONSTRAINT fk_{tabla}_tenant "
            f"FOREIGN KEY (id_tenant) REFERENCES {S}.tenants(id_tenant)",
        ]
        if pk:
            # Destino de las FK compuestas y, a la vez, índice por empresa (RNF09)
            sql.append(f"ALTER TABLE {S}.{tabla} ADD CONSTRAINT uq_{tabla}_tenant_pk UNIQUE (id_tenant, {pk})")
        else:
            sql.append(f"CREATE INDEX idx_{tabla}_tenant ON {S}.{tabla} (id_tenant)")

    # usuarios: empresa solo para los empleados (F1). Sin DEFAULT: los clientes y el super
    # administrador se crean sin empresa aunque la petición tenga una en su contexto.
    sql += [
        f"ALTER TABLE {S}.usuarios ADD COLUMN id_tenant BIGINT REFERENCES {S}.tenants(id_tenant)",
        f"UPDATE {S}.usuarios SET id_tenant = 1 WHERE rol::text NOT IN {ROLES_SIN_EMPRESA}",
        f"ALTER TABLE {S}.usuarios ADD CONSTRAINT chk_usuarios_tenant_segun_rol CHECK ("
        f"(rol::text IN {ROLES_SIN_EMPRESA} AND id_tenant IS NULL) OR "
        f"(rol::text NOT IN {ROLES_SIN_EMPRESA} AND id_tenant IS NOT NULL))",
        f"ALTER TABLE {S}.usuarios ADD CONSTRAINT uq_usuarios_tenant_pk UNIQUE (id_tenant, id_usuario)",
        # El empleado y su usuario son de la misma empresa
        f"ALTER TABLE {S}.empleados ADD CONSTRAINT fk_empleados_usuario_tenant "
        f"FOREIGN KEY (id_tenant, id_empleado) REFERENCES {S}.usuarios (id_tenant, id_usuario)",
    ]

    # bitacora: eventos de plataforma sin empresa; los actuales son de FASHION STORE
    sql += [
        f"ALTER TABLE {S}.bitacora ADD COLUMN id_tenant BIGINT REFERENCES {S}.tenants(id_tenant)",
        f"UPDATE {S}.bitacora SET id_tenant = 1",
        f"ALTER TABLE {S}.bitacora ALTER COLUMN id_tenant SET DEFAULT {CONTEXTO_TENANT}",
        f"CREATE INDEX idx_bitacora_tenant ON {S}.bitacora (id_tenant, creado_en DESC)",
    ]

    # 2. Claves únicas por empresa ------------------------------------------------------------
    for tabla, nombre, _original, nueva in UNICAS:
        sql += [f"ALTER TABLE {S}.{tabla} DROP CONSTRAINT {nombre}", f"ALTER TABLE {S}.{tabla} ADD {nueva}"]
    for nombre, _original, _nuevo_nombre, nueva in INDICES_UNICOS:
        sql.append(f"DROP INDEX {S}.{nombre}")
        if nueva:
            sql.append(nueva)

    # RN05 (F8): correo de empleado único por empresa; de cliente y super administrador, global
    sql += [
        f"ALTER TABLE {S}.usuarios DROP CONSTRAINT usuarios_email_key",
        f"CREATE UNIQUE INDEX uq_usuarios_email_empresa ON {S}.usuarios (id_tenant, lower(email::text)) "
        f"WHERE id_tenant IS NOT NULL",
        f"CREATE UNIQUE INDEX uq_usuarios_email_global ON {S}.usuarios (lower(email::text)) WHERE id_tenant IS NULL",
    ]

    # 3. Claves foráneas compuestas (F9, F11) ------------------------------------------------
    for tabla, original, col, ref, ref_col, al_borrar, _def in FKS_COMPUESTAS:
        accion = f" ON DELETE {al_borrar}" if al_borrar else ""
        sql += [
            f"ALTER TABLE {S}.{tabla} DROP CONSTRAINT {original}",
            f"ALTER TABLE {S}.{tabla} ADD CONSTRAINT {_nombre_fk(tabla, col)} "
            f"FOREIGN KEY (id_tenant, {col}) REFERENCES {S}.{ref} (id_tenant, {ref_col}){accion}",
        ]

    # 4. Sucursales autorizadas por empleado (RN07, F10) -------------------------------------
    sql += [
        f"""CREATE TABLE {S}.empleado_sucursal (
                id_tenant     BIGINT  NOT NULL DEFAULT {CONTEXTO_TENANT} REFERENCES {S}.tenants(id_tenant),
                id_empleado   BIGINT  NOT NULL,
                id_sucursal   INTEGER NOT NULL,
                es_principal  BOOLEAN NOT NULL DEFAULT false,
                PRIMARY KEY (id_empleado, id_sucursal),
                CONSTRAINT fk_empleado_sucursal_empleado FOREIGN KEY (id_tenant, id_empleado)
                    REFERENCES {S}.empleados (id_tenant, id_empleado) ON DELETE CASCADE,
                CONSTRAINT fk_empleado_sucursal_sucursal FOREIGN KEY (id_tenant, id_sucursal)
                    REFERENCES {S}.sucursales (id_tenant, id_sucursal) ON DELETE CASCADE
            )""",
        f"CREATE UNIQUE INDEX uq_empleado_sucursal_principal ON {S}.empleado_sucursal (id_empleado) WHERE es_principal",
        f"CREATE INDEX idx_empleado_sucursal_tenant ON {S}.empleado_sucursal (id_tenant, id_sucursal)",
        f"""INSERT INTO {S}.empleado_sucursal (id_tenant, id_empleado, id_sucursal, es_principal)
            SELECT u.id_tenant, e.id_empleado, u.id_sucursal, true
              FROM {S}.empleados e JOIN {S}.usuarios u ON u.id_usuario = e.id_empleado
             WHERE u.id_sucursal IS NOT NULL""",
    ]

    for sentencia in sql:
        op.execute(sentencia)


def downgrade() -> None:
    sql: list[str] = [f"DROP TABLE IF EXISTS {S}.empleado_sucursal"]

    # 3. Restaurar las claves foráneas originales
    for tabla, original, col, _ref, _ref_col, _al_borrar, definicion in FKS_COMPUESTAS:
        sql += [
            f"ALTER TABLE {S}.{tabla} DROP CONSTRAINT {_nombre_fk(tabla, col)}",
            f"ALTER TABLE {S}.{tabla} ADD CONSTRAINT {original} {definicion}",
        ]

    # 2. Restaurar las claves únicas originales
    sql += [
        f"DROP INDEX {S}.uq_usuarios_email_empresa",
        f"DROP INDEX {S}.uq_usuarios_email_global",
        f"ALTER TABLE {S}.usuarios ADD CONSTRAINT usuarios_email_key UNIQUE (email)",
    ]
    for nombre, original, nuevo_nombre, _nueva in INDICES_UNICOS:
        if nuevo_nombre:
            sql.append(f"DROP INDEX {S}.{nuevo_nombre}")
        sql.append(original)
    for tabla, nombre, original, nueva in UNICAS:
        nombre_nuevo = nueva.split()[1]
        sql += [
            f"ALTER TABLE {S}.{tabla} DROP CONSTRAINT {nombre_nuevo}",
            f"ALTER TABLE {S}.{tabla} ADD CONSTRAINT {nombre} {original}",
        ]

    # 1. Quitar id_tenant (arrastra sus índices, FK y CHECK)
    sql += [
        f"ALTER TABLE {S}.empleados DROP CONSTRAINT fk_empleados_usuario_tenant",
        f"ALTER TABLE {S}.bitacora DROP COLUMN id_tenant",
    ]
    for tabla in TABLAS_TENANT:
        sql.append(f"ALTER TABLE {S}.{tabla} DROP COLUMN id_tenant")
    sql.append(f"ALTER TABLE {S}.usuarios DROP COLUMN id_tenant")

    for sentencia in sql:
        op.execute(sentencia)
