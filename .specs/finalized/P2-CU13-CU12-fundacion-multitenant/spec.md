# Especificación Técnica: Fundación Multitenant (P2-CU13 Aislar datos por empresa · P2-CU12 Validar suscripción y límites del plan)

**ID del cambio:** `P2-CU13-CU12-fundacion-multitenant`
**Fuente:** `SI2-Parcial2.md` (corregido el 2026-11-08): CU12, CU13, RF13, RF14, RNF02, RNF09, RNF16, RN01–RN18, RN51
**Numeración:** casos de uso del Parcial 2 con prefijo `P2-` (decisión D7). No se renombra ningún módulo existente.
**Nivel SDD:** **3 (alto riesgo)**: migraciones que alteran todas las tablas de negocio con datos de producción, seguridad por filas y cambios en la autenticación.
**Bloques:** **solo backend y base de datos.** Web y móvil no cambian en este ciclo (ver §1.3).
**Estado:** 🟢 Aprobada el 2026-11-08, implementada y en producción. Spec permanente: `.specs/modules/plataforma/P2-CU13-CU12-fundacion-multitenant.md`.
**Fecha:** 2026-11-08

---

## 0. Hallazgos (verificados contra Neon y el código el 2026-11-08)

### 0.1 Base de datos
- PostgreSQL **18.6** en Neon. Admite `security_invoker` en vistas y RLS completa.
- **31 tablas** de negocio en `fashionstore`, ninguna con `id_tenant` ni RLS.
- La aplicación se conecta como `neondb_owner`: **dueño de las tablas y con `BYPASSRLS`**. Con ese rol, ninguna política de RLS tendría efecto.
- Las 3 vistas (`vw_inventario_consolidado`, `vw_ventas_por_sucursal`, `vw_reservas_pendientes`) se ejecutan con los permisos de su dueño. Si no se marcan como `security_invoker`, **se saltarían la RLS**.
- Neon usa PgBouncer en modo transacción: vale `set_config(..., true)` (equivale a `SET LOCAL`), pero un `SET` de sesión se perdería o contaminaría otras peticiones.
- **Datos actuales:** 4 sucursales, 10 usuarios (6 clientes, 2 administradores, 1 encargado, 1 cajero), 21 productos, 52 variantes, 49 ventas, 11 reservas.
- **9 filas en `clientes`:** 6 son clientes y 3 son empleados (los administradores 8 y 9 y el cajero 14), con ficha de cliente heredada del registro.
- **Claves únicas que hoy son globales y deben pasar a ser por empresa** (RN20, RN28): `categorias.nombre`, `empleados.codigo_empleado`, `proveedores.nit_rut` y su razón social, `sucursales (id_ciudad, nombre)`, `variantes_producto.sku`, `ventas.numero_comprobante`, `promociones` (código de cupón), `temporadas` (nombre), `carritos.id_cliente` y `usuarios.email` (RN05).
- El enum `rol_usuario` vale `{cliente, administrador, encargado_sucursal, cajero, proveedor}`: falta `super_administrador`. No hay usuarios con rol `proveedor`.

### 0.2 Código
- `get_db()` entrega una sesión sin contexto de empresa. `get_current_user()` decodifica el JWT (`sub`, `email`, `rol`) y lee `usuarios`.
- El JWT no lleva empresa.
- El webhook de Stripe (`POST /pagos/webhook`) no tiene token: localiza el pago por su referencia. Los 9 pagos con Stripe que existen se crearon sin `id_tenant` en sus metadatos.
- `usuarios.id_sucursal` es la sucursal única del empleado. La usan el POS, CU24, CU28, CU29 y los guards.

---

## 1. Alcance

### 1.1 Qué entrega este cambio
1. **Modelo de empresa (tenant):** tablas nuevas de empresas, planes, funcionalidades, suscripciones con su historial, configuración por empresa, registro de clientes por empresa y sucursales autorizadas por empleado.
2. **`id_tenant` en todas las tablas de negocio**, con los datos actuales asignados a la empresa **FASHION STORE** (código `fashionstore`).
3. **Aislamiento en tres niveles (P2-CU13, RNF02):**
   - el backend fija la empresa de cada petición;
   - las claves foráneas compuestas impiden relacionar filas de empresas distintas;
   - la RLS de PostgreSQL filtra todo lo que lee o escribe la sesión.
4. **Validación de suscripción y límites (P2-CU12):** servicio y dependencia reutilizables, conectados a las operaciones existentes que el plan restringe.
5. **Rol de base de datos para la aplicación** sin `BYPASSRLS` (decisión D-G aprobada).
6. **Pruebas de aislamiento contra PostgreSQL real** (RNF11).

### 1.2 Fuera de alcance (cada uno tendrá su spec)
- **Pantallas y flujos de P2-CU02:** login con código de empresa obligatorio, pantalla de selección de empresa en el móvil y portal web por ruta `/{codigo}`. Este cambio solo deja el **contrato de backend** preparado y un modo de transición (§1.3).
- Gestión de empresas, planes, suscripciones y catálogos globales (P2-CU05 a P2-CU08), consulta y cambio de plan (P2-CU09, P2-CU10), parámetros (P2-CU11) y usuario super administrador.
- Inventario sin temporada (RN21), totales calculados por la base de datos (RN26) y vencimiento de reservas a 24 h (RN25).
- Empresa de prueba Menshopping (RF15), operación sin conexión, conflictos, cambios de prenda, reportes con IA, aprendizaje automático, notificaciones push y respaldos.

### 1.3 Modo de transición: web y móvil siguen funcionando sin cambios
Hasta que se implemente P2-CU02, los clientes web y móvil no envían empresa. Para no romperlos:
- **Empleados:** si el login llega sin `codigo_empresa`, se usa la empresa por defecto `fashionstore`.
- **Clientes:** el token se emite con la empresa por defecto, si el cliente está registrado en ella.
- **Visitantes sin token:** usan la empresa por defecto.

La empresa por defecto se fija en la variable `TENANT_POR_DEFECTO` (valor `fashionstore`). **P2-CU02 la elimina.** Mientras exista, la segunda empresa solo es accesible enviando su código.

---

## 2. Decisiones

### 2.1 Ya tomadas (2026-11-08)
| # | Decisión |
| :--- | :--- |
| D1 | El cliente tiene una cuenta única en la plataforma y se registra en cada empresa. Navega en una a la vez. |
| D2–3 | Nombres estándar: tabla `tenants`, columna `id_tenant`. |
| D3 | Los datos actuales pasan a la empresa FASHION STORE con plan Profesional. |
| D4 | Límite de empleados por plan, configurable por el super administrador. |
| D-G | La aplicación se conecta con un rol sin `BYPASSRLS`. |

### 2.2 Propuestas de esta spec (requieren aprobación)
| # | Pregunta | Recomendación |
| :--- | :--- | :--- |
| **F1** | Qué tablas llevan `id_tenant` | Todas las de negocio (§3.2). Son globales: `ciudades`, `tallas`, `colores` (RN19), `clientes` (D1), `codigos_recuperacion`, `planes`, `funcionalidades`, `plan_funcionalidades` y `tenants`. `usuarios` lleva `id_tenant` **nulo** para clientes y super administradores. `bitacora` lo lleva nulo para eventos de plataforma. |
| **F2** | Cómo se rellena `id_tenant` al insertar | Con un **valor por defecto en la base de datos** tomado del contexto de la transacción: `DEFAULT NULLIF(current_setting('app.id_tenant', true), '')::bigint`. Los servicios existentes no tienen que tocar cada `INSERT`, y la RLS rechaza cualquier valor que no coincida. |
| **F3** | Cómo llega la empresa a la base de datos | Un *listener* `after_begin` de SQLAlchemy ejecuta `set_config('app.id_tenant', …, true)` **al inicio de cada transacción**, con el valor guardado en `session.info`. Así se mantiene aunque un servicio haga varios `commit` en la misma petición, y es compatible con PgBouncer. |
| **F4** | Fuente de la empresa en cada petición | 1) la del token (empleados y clientes); 2) si no hay token, la cabecera `X-Tenant: <codigo>`; 3) si no hay ninguna, `TENANT_POR_DEFECTO` (transición). Si el token y la cabecera no coinciden, **403 `TENANT_NO_COINCIDE`**. |
| **F5** | Si falta el contexto | **Se cierra:** la RLS no devuelve filas y rechaza escrituras. Nunca hay un «ver todo» por omisión. |
| **F6** | Super administrador y procesos sin token | Un segundo valor de contexto, `app.modo_plataforma = 'on'`, que las políticas aceptan para ver todas las empresas. Solo lo activan: el super administrador en los endpoints de plataforma (P2-CU05 a P2-CU08) y el webhook de Stripe para **localizar** el pago. Después de localizarlo, el webhook fija la empresa del pago y desactiva el modo plataforma. Los pagos nuevos guardan `id_tenant` en los metadatos del `PaymentIntent`. |
| **F7** | `usuarios` y el login | Política de `usuarios`: visibles los de la empresa del contexto **y** los que no tienen empresa (clientes y super administradores). Login: se busca primero la empresa por su código (`tenants` no lleva RLS) y después el usuario dentro de ese contexto. |
| **F8** | Correo único (RN05) | Dos índices únicos parciales: `(id_tenant, lower(email)) WHERE id_tenant IS NOT NULL` para empleados y `(lower(email)) WHERE id_tenant IS NULL` para clientes y super administradores. |
| **F9** | Clientes registrados por empresa | Tabla `cliente_tenant (id_tenant, id_cliente, registrado_en, activo)`. Las tablas que referencian a un cliente usan una **clave foránea compuesta** hacia ella: un cliente no puede reservar ni comprar en una empresa en la que no está registrado. Se registran en FASHION STORE las 9 filas actuales de `clientes`, incluidas las 3 de empleados, para no romper ventas ni reservas existentes. |
| **F10** | Sucursales del empleado (RN07) | Tabla `empleado_sucursal (id_tenant, id_empleado, id_sucursal, es_principal)`, rellenada desde `usuarios.id_sucursal`. **`usuarios.id_sucursal` se mantiene como sucursal principal**: el código actual sigue funcionando y P2-CU03 ampliará el uso. |
| **F11** | Claves foráneas compuestas (RNF02) | Cada tabla padre de empresa gana `UNIQUE (id_tenant, <pk>)`, y las FK entre tablas de empresa pasan a `(id_tenant, fk) → (id_tenant, pk)`. Las FK hacia tablas globales (ciudades, tallas, colores, usuarios) siguen siendo simples. |
| **F12** | Vistas | `ALTER VIEW … SET (security_invoker = on)` en las 3 vistas, para que respeten la RLS. |
| **F13** | Rol de la aplicación | Rol `fashionstore_app` (LOGIN, `NOBYPASSRLS`, sin ser dueño de las tablas) con `SELECT/INSERT/UPDATE/DELETE` sobre las tablas y uso de secuencias. **Las migraciones siguen ejecutándose como `neondb_owner`** con una variable nueva, `DATABASE_URL_MIGRACIONES`, que usan `alembic/env.py` y el `preDeployCommand` de Render. La contraseña del rol la creas tú en la consola de Neon: nunca pasa por el chat ni por el repo. |
| **F14** | Planes iniciales | **Básico:** 2 sucursales, sin reportes con IA. **Profesional:** 10 sucursales, con reportes con IA. Límite de empleados **nulo, es decir sin límite**, hasta que el super administrador lo fije en P2-CU06. Precio de referencia: Básico 0,00 y Profesional 0,00 hasta P2-CU06. Funcionalidades: `productos`, `ventas`, `reservas`, `operacion_offline`, `reportes_convencionales`, `reportes_ia`. |
| **F15** | Suscripción de FASHION STORE | Profesional, `activa`, desde el 2026-11-08 hasta el **2027-11-08** (12 meses). |
| **F16** | Enum de roles | Se añade `super_administrador`. **`proveedor` se mantiene en el enum** (PostgreSQL no permite borrar valores de un enum sin recrearlo), pero queda prohibido asignarlo (RN06). |
| **F17** | Dónde se conecta P2-CU12 ahora | Al crear o activar una sucursal (límite de sucursales, CU21 actual), al crear un empleado (límite de empleados, CU20 actual), al reservar (`reservas`), al hacer checkout o una venta en caja (`ventas`) y en los reportes por voz (`reportes_convencionales`). Los reportes con IA (`reportes_ia`) se conectan en P2-CU21. |
| **F18** | Dónde se prueba el aislamiento | En una **rama de Neon** dedicada (`pruebas-multitenant`), con su URL en `Ec-backend/.env` como `DATABASE_URL_PRUEBAS`. La creas tú en la consola de Neon; es gratis. Las pruebas se saltan si la variable no existe, igual que `tests/test_esquema_bd.py`. |
| **F19** | Cómo se aplica en producción | 1) crear una rama de respaldo de Neon (`respaldo-pre-0012`); 2) aplicar y probar la migración en la rama `pruebas-multitenant`; 3) solo con tu confirmación, aplicarla en la rama principal; 4) cambiar `DATABASE_URL` de Render y de `.env` al rol `fashionstore_app`. |
| **F20** | Constitución de las skills | Delta en `.agents/skills/fashionstore-backend-sdd/SKILL.md`: el principio 0 (moda femenina) pasa a valer solo para FASHION STORE, y el principio 6 suma el rol `super_administrador` y las sucursales autorizadas. |

---

## A. Especificación técnica

### A.1 Tablas nuevas (migración `0012`)

```sql
tenants (
  id_tenant      BIGSERIAL PRIMARY KEY,
  codigo         CITEXT NOT NULL UNIQUE CHECK (codigo ~ '^[a-z0-9-]{3,60}$'),   -- RN03
  nombre         VARCHAR(150) NOT NULL,
  correo_contacto CITEXT, telefono VARCHAR(30),
  estado         VARCHAR(20) NOT NULL DEFAULT 'activa'
                 CHECK (estado IN ('activa','suspendida','baja')),               -- RN08
  creado_en      TIMESTAMPTZ NOT NULL DEFAULT now()
)
funcionalidades (codigo VARCHAR(50) PRIMARY KEY, nombre VARCHAR(100) NOT NULL)
planes (
  id_plan BIGSERIAL PRIMARY KEY, nombre VARCHAR(60) NOT NULL UNIQUE,
  precio_mensual NUMERIC(10,2) NOT NULL DEFAULT 0 CHECK (precio_mensual >= 0),
  max_sucursales_activas INT NOT NULL CHECK (max_sucursales_activas > 0),
  max_empleados INT NULL CHECK (max_empleados > 0),                              -- NULL = sin límite
  activo BOOLEAN NOT NULL DEFAULT true
)
plan_funcionalidades (id_plan → planes, codigo_funcionalidad → funcionalidades, PK (id_plan, codigo_funcionalidad))
suscripciones (
  id_suscripcion BIGSERIAL PRIMARY KEY, id_tenant → tenants, id_plan → planes,
  estado VARCHAR(20) NOT NULL CHECK (estado IN ('prueba','activa','vencida','suspendida','cancelada')),
  fecha_inicio DATE NOT NULL, fecha_vencimiento DATE NOT NULL CHECK (fecha_vencimiento > fecha_inicio),  -- RN13
  creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
)
-- RN13: como máximo una vigente por empresa
CREATE UNIQUE INDEX uq_suscripcion_vigente ON suscripciones (id_tenant) WHERE estado IN ('prueba','activa');
historial_suscripcion (id_historial, id_tenant, id_suscripcion, evento, detalle JSONB, id_usuario, creado_en)  -- RN17
configuracion_tenant (
  id_tenant PRIMARY KEY → tenants,
  moneda CHAR(3) NOT NULL DEFAULT 'EUR', zona_horaria VARCHAR(60) NOT NULL DEFAULT 'Europe/Madrid',
  horas_vencimiento_reserva INT NOT NULL DEFAULT 24 CHECK (> 0),
  dias_cambio_prenda INT NOT NULL DEFAULT 15 CHECK (>= 0),
  operacion_offline_habilitada BOOLEAN NOT NULL DEFAULT true,
  dias_antiguedad_offline INT NOT NULL DEFAULT 7 CHECK (> 0)
)
cliente_tenant (id_tenant → tenants, id_cliente → clientes, registrado_en, activo, PK (id_tenant, id_cliente))
empleado_sucursal (id_tenant, id_empleado, id_sucursal, es_principal BOOLEAN,
                   PK (id_empleado, id_sucursal),
                   UNIQUE (id_empleado) WHERE es_principal)                       -- una principal por empleado
```

**Datos iniciales:** la empresa 1 `fashionstore` («FASHION STORE», activa), las 6 funcionalidades, los planes Básico y Profesional (F14), la suscripción de FASHION STORE (F15), su configuración por defecto, `cliente_tenant` con las 9 fichas de cliente y `empleado_sucursal` con el cajero 14 y el encargado 13.

### A.2 Tablas modificadas (migración `0013`)

**Con `id_tenant BIGINT NOT NULL`**, rellenado con 1 en las filas actuales, valor por defecto del contexto (F2), índice, `UNIQUE (id_tenant, <pk>)` y RLS:

`sucursales`, `empleados`, `proveedores`, `temporadas`, `colecciones`, `categorias`, `productos`, `variantes_producto`, `inventario_sucursal`, `movimientos_inventario`, `reservas`, `reserva_detalle`, `carritos`, `carrito_detalle`, `ventas`, `venta_detalle`, `pagos`, `promociones`, `promocion_producto`, `historial_navegacion`, `recomendaciones_ia`, `interacciones_chatbot`, `sesiones_vestidor_virtual`, `solicitudes_reporte_ia`.

**Con `id_tenant` nulo:** `usuarios` (empleados con valor; clientes y super administradores sin él) y `bitacora` (eventos de plataforma sin valor).

**Claves únicas que pasan a ser por empresa:** las de §0.1, añadiendo `id_tenant` como primera columna. Los correos de `usuarios` usan los índices parciales de F8.

### A.3 Políticas (migración `0014`)

```sql
-- Contexto (F3, F6)
--   app.id_tenant        → empresa de la transacción
--   app.modo_plataforma  → 'on' solo para el super administrador y la localización del webhook
--   app.id_usuario       → usuario de la petición (para cliente_tenant)

ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;
CREATE POLICY aislamiento_tenant ON <t>
  USING      (id_tenant = NULLIF(current_setting('app.id_tenant', true), '')::bigint
              OR current_setting('app.modo_plataforma', true) = 'on')
  WITH CHECK (id_tenant = NULLIF(current_setting('app.id_tenant', true), '')::bigint
              OR current_setting('app.modo_plataforma', true) = 'on');

-- usuarios: además, los que no tienen empresa (clientes y super administradores)
-- bitacora: además, los eventos sin empresa, visibles y escribibles solo en modo plataforma
-- cliente_tenant: además, las filas del propio cliente (app.id_usuario) para listar sus empresas
-- suscripciones, historial_suscripcion, configuracion_tenant: aislamiento normal
-- tenants, planes, funcionalidades, plan_funcionalidades: sin RLS; la escritura solo la permite el backend en modo plataforma

ALTER VIEW vw_inventario_consolidado SET (security_invoker = on);   -- y las otras dos
GRANT … TO fashionstore_app;   -- solo si el rol existe (F13)
```

### A.4 Backend

**`core/tenant.py` (nuevo):**
- `fijar_contexto(db, id_tenant, *, id_usuario=None, plataforma=False)`: guarda el contexto en `session.info`.
- Un listener `after_begin` aplica `set_config(..., true)` en cada transacción.
- Una dependencia global `resolver_tenant(request, db)` aplica F4 a la cabecera `X-Tenant` o a `TENANT_POR_DEFECTO` y valida que la empresa exista y esté activa (`404 TENANT_NO_ENCONTRADO`, `403 TENANT_INACTIVO`).

**`core/deps.py`:**
- `get_current_user` lee `id_tenant` del token **antes** de consultar `usuarios`, y fija el contexto.
- Un token sin `id_tenant` (los emitidos antes de esta migración) responde **401 `TOKEN_INVALIDO`**: el usuario vuelve a iniciar sesión, y los clientes ya gestionan ese caso.
- Si el token y la cabecera no coinciden: 403 `TENANT_NO_COINCIDE` (F4).

**JWT:** pasa a `{sub, email, rol, id_tenant}`, con `id_tenant` nulo para el super administrador.

**Login (transición, §1.3):**
- El cuerpo admite `codigo_empresa` opcional.
- **Empleado:** se busca dentro de la empresa indicada o, si no hay código, de `TENANT_POR_DEFECTO`.
- **Cliente:** el token se emite con la empresa por defecto si el cliente está registrado en ella. Si no, se emite sin empresa y solo puede ver la lista de empresas (P2-CU02).
- La respuesta añade `tenant: {codigo, nombre}`. Es un cambio **compatible**: solo añade campos.

**`modules/plataforma/` (nuevo paquete, en este cambio solo P2-CU12):**
- **Servicio** `SuscripcionServicio.validar(db, id_tenant, *, funcionalidad=None, recurso=None)`. Comprueba que la suscripción esté vigente (estado `prueba` o `activa` y dentro de sus fechas) y que el plan incluya la funcionalidad. Para un recurso con límite compara el uso con el máximo. Errores:
  - `403 SUSCRIPCION_NO_VIGENTE`
  - `403 FUNCIONALIDAD_NO_INCLUIDA`, que indica qué plan la incluye
  - `409 LIMITE_PLAN_ALCANZADO`, con `{limite, uso}`
- **Dependencia** `requiere_funcionalidad("ventas")` para los routers, y llamada directa al servicio para los límites (F17).
- Si el usuario es super administrador, la validación no se aplica (CU12 A4).
- **Una vigencia vencida se detecta al consultar.** No hay proceso programado: si `fecha_vencimiento < hoy`, la suscripción se trata como vencida.

**Webhook de Stripe (F6):**
- Localiza el pago en modo plataforma y fija después la empresa del pago.
- `crear_intento` guarda `metadata.id_tenant`.

**Modelos ORM:**
- Atributo `id_tenant` mapeado con `FetchedValue()` (lo rellena la base de datos).
- Modelos nuevos para las tablas de §A.1.
- `tests/test_esquema_bd.py` vuelve a comparar contra Neon tras la migración.

### A.5 Criterios de aceptación (Gherkin)

```gherkin
Característica: P2-CU13 — Aislar datos por empresa

  Antecedentes:
    Dadas las empresas "fashionstore" y "pruebas-b", cada una con un producto, una sucursal y un empleado

  Escenario: Cada empresa solo ve lo suyo
    Cuando el administrador de "pruebas-b" consulta los productos
    Entonces solo recibe el producto de "pruebas-b"

  Escenario: Recurso de otra empresa responde como inexistente (CU13 A2)
    Cuando el administrador de "pruebas-b" pide la venta 33 de "fashionstore"
    Entonces recibe 404 sin revelar que existe
    Y el intento queda en la bitácora de "pruebas-b"

  Escenario: La base de datos impide mezclar empresas aunque el backend falle
    Dada una sesión con el contexto de "pruebas-b"
    Cuando se intenta insertar una línea de venta de "pruebas-b" con una variante de "fashionstore"
    Entonces PostgreSQL rechaza la escritura (RLS o clave foránea compuesta)

  Escenario: Sin contexto no se ve nada (F5)
    Dada una conexión con el rol fashionstore_app sin app.id_tenant
    Cuando consulta productos
    Entonces obtiene 0 filas

  Escenario: Las vistas respetan la RLS
    Cuando "pruebas-b" consulta vw_ventas_por_sucursal
    Entonces no aparece ninguna sucursal de "fashionstore"

  Escenario: Token y cabecera no coinciden
    Cuando un empleado de "fashionstore" envía X-Tenant: pruebas-b
    Entonces recibe 403 TENANT_NO_COINCIDE

  Escenario: Token antiguo sin empresa
    Cuando se usa un token emitido antes de la migración
    Entonces recibe 401 y debe iniciar sesión de nuevo

  Escenario: Transición sin cambios en web y móvil (§1.3)
    Cuando un visitante consulta el catálogo sin token ni cabecera
    Entonces recibe el catálogo de "fashionstore"

Característica: P2-CU12 — Validar suscripción y límites

  Escenario: Límite de sucursales del plan Básico
    Dada "pruebas-b" con plan Básico y 2 sucursales activas
    Cuando su administrador activa una tercera
    Entonces recibe 409 LIMITE_PLAN_ALCANZADO con límite 2 y uso 2

  Escenario: Suscripción vencida bloquea operaciones restringidas
    Dada "pruebas-b" con la suscripción vencida ayer
    Cuando un cliente intenta reservar
    Entonces recibe 403 SUSCRIPCION_NO_VIGENTE

  Escenario: Límite de empleados nulo significa sin límite
    Dado el plan Profesional con max_empleados nulo
    Cuando el administrador crea un empleado más
    Entonces se crea

  Escenario: Los datos actuales siguen funcionando
    Dado FASHION STORE con plan Profesional vigente y 4 sucursales activas
    Cuando se ejecuta la suite actual del backend
    Entonces sigue en verde
```

### A.6 Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| La migración falla a medias sobre producción | Cada migración se ejecuta en una sola transacción. Antes: rama de respaldo de Neon y ensayo en la rama de pruebas (F19). Todas tienen `downgrade`. |
| Una consulta que antes funcionaba devuelve vacío por falta de contexto (F5) | La dependencia global fija el contexto en todas las peticiones; prueba de humo de todos los GET con el rol nuevo; el modo de transición cubre a los clientes actuales. |
| Un `commit` intermedio pierde el contexto | El listener `after_begin` lo reaplica en cada transacción (F3). Hay una prueba con dos commits en la misma petición. |
| Procesos sin petición HTTP (scripts, webhook) | Los scripts de mantenimiento usan `DATABASE_URL_MIGRACIONES` (dueño). El webhook usa el modo plataforma solo para localizar (F6). |
| Los tests actuales simulan la base de datos y no ven la RLS | Pruebas nuevas contra la rama de Neon (F18). La suite simulada sigue siendo la red rápida. |
| Cambiar `DATABASE_URL` en Render deja la app sin permisos | Los `GRANT` se prueban en la rama de pruebas con el rol nuevo antes de tocar Render. |
| Los usuarios pierden la sesión (tokens sin `id_tenant`) | Es aceptable y se avisa. Basta volver a iniciar sesión. |

---

## B. Deltas de implementación (bloque 2, 2026-11-08)

Cambios respecto a lo especificado, descubiertos al implementar y probar contra la rama de pruebas:

| # | Delta | Motivo |
| :--- | :--- | :--- |
| Δ1 | **CU20 rechaza convertir un cliente en empleado o al revés** (409 `CAMBIO_ROL_NO_PERMITIDO`). Los cambios entre roles de empleado siguen permitidos. | La cuenta de cliente es global y la de empleado es de una empresa (RN04, RN05); además, la FK compuesta `empleados (id_tenant, id_empleado) → usuarios` impide cambiar la empresa del usuario. |
| Δ2 | **Carrito y reserva exigen que el cliente esté registrado en la empresa** (403 `CLIENTE_NO_REGISTRADO`, decisión D-B). Un **empleado** que usa el carrito en su propia empresa queda registrado como cliente de ella. | Sin esta comprobación, la FK compuesta hacia `cliente_tenant` devolvía un 500. La prueba de humo lo detectó con el encargado 13, que antes podía comprar en su tienda: se conserva ese comportamiento. |
| Δ3 | `requiere_funcionalidad` resuelve el token por su cuenta y **no valida si no hay usuario** (el endpoint responde 401). | FastAPI resuelve las `dependencies` del decorador antes que los parámetros del endpoint: sin esto validaba con la empresa de la cabecera y respondía 403 en vez de 401. |
| Δ4 | `LIMITE_PLAN_ALCANZADO` informa el límite y el uso **en el mensaje**, no en campos aparte. | El formato de error del proyecto es `{detail, code}`; ampliarlo no aporta en este ciclo. |
| Δ5 | El registro de bitácora autónomo ya no relee el evento tras el commit. | Con RLS, un evento sin empresa no se puede releer fuera del modo plataforma. |
| Δ6 | `Settings` declara `DATABASE_URL_MIGRACIONES`, `DATABASE_URL_PRUEBAS`, `DATABASE_URL_PRUEBAS_APP` y `TENANT_POR_DEFECTO`. | Sin declararlas, el backend local no arrancaba (`pydantic-settings` rechaza variables desconocidas del `.env`). |
| Δ7 | `tests/test_esquema_bd.py` compara el ORM con `DATABASE_URL_PRUEBAS` si existe. | Mientras producción sigue en `0011`, la base que debe coincidir con el ORM es la rama migrada. |
