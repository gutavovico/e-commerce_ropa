# Especificación Técnica: Panel del Super Administrador SaaS (P2-CU05 · P2-CU06 · P2-CU07 · P2-CU08)

**ID del cambio:** `P2-CU05-CU08-superadmin`
**Fuente:** `SI2-Parcial2.md` (CU05, CU06, CU07, CU08, RF01, RF02, RF07, RF09, RF10, RNF16, RNF17, RN01–RN05, RN08, RN11–RN14, RN17, RN19, RN51; PF-10 a PF-14) y `Repartición.md`.
**Depende de:** `P2-CU13-CU12-fundacion-multitenant` (migraciones `0012`–`0014`) y `P2-CU02-CU01-acceso-por-empresa` (migración `0015`).
**Nivel SDD:** **3 (alto riesgo)**: alta transaccional de empresas e inquilinos, gobierno de planes/suscripciones en modo plataforma (`app.modo_plataforma = 'on'`) y catálogos globales compartidos.
**Bloques:** Backend → Web (cada uno con su puerta de aprobación). No aplica a Móvil.
**Estado:** 🟡 Pendiente de aprobación (Gate 0).
**Fecha:** 2026-11-09

---

## 0. Hallazgos en el repositorio y esquema actual

1. **Tablas SaaS ya creadas (`0012`–`0015`):**
   - `fashionstore.tenants`: `id_tenant`, `codigo` (`^[a-z0-9-]{3,60}$` y no reservado en `0015`), `nombre`, `correo_contacto`, `telefono`, `estado` (`'activa' | 'suspendida' | 'baja'`), `creado_en`. Sin RLS.
   - `fashionstore.funcionalidades`: `codigo` (PK), `nombre`, `descripcion`. Sembradas las 6 funcionalidades (`productos`, `ventas`, `reservas`, `operacion_offline`, `reportes_convencionales`, `reportes_ia`).
   - `fashionstore.planes`: `id_plan`, `nombre` (UNIQUE), `precio_mensual` (`>= 0`), `max_sucursales_activas` (`> 0`), `max_empleados` (`NULL` o `> 0`), `activo`, `creado_en`.
   - `fashionstore.plan_funcionalidades`: `(id_plan, codigo_funcionalidad)`.
   - `fashionstore.suscripciones`: `id_suscripcion`, `id_tenant`, `id_plan`, `estado` (`'prueba' | 'activa' | 'vencida' | 'suspendida' | 'cancelada'`), `fecha_inicio`, `fecha_vencimiento` (`> fecha_inicio`). Índice único parcial `uq_suscripcion_vigente ON suscripciones (id_tenant) WHERE estado IN ('prueba', 'activa')`. Con RLS (`aislamiento_tenant`).
   - `fashionstore.historial_suscripcion`: `id_historial`, `id_tenant`, `id_suscripcion`, `evento` (`'alta' | 'renovacion' | 'cambio_plan' | 'suspension' | 'vencimiento' | 'reactivacion' | 'cancelacion'`), `detalle` (JSONB), `id_usuario`, `creado_en`. Con RLS.
   - `fashionstore.configuracion_tenant`: `id_tenant` (PK), `moneda`, `zona_horaria`, `horas_vencimiento_reserva`, `dias_cambio_prenda`, `operacion_offline_habilitada`, `dias_antiguedad_offline`, `actualizado_en`. Con RLS.
2. **Modo plataforma (`core/tenant.py`):**
   - `fijar_contexto(db, None, id_usuario=usuario.id_usuario, plataforma=True)` activa `app.modo_plataforma = 'on'` en la transacción actual y en cualquier transacción subsiguiente de la sesión.
   - Todas las políticas RLS de `0014_rls.py` incluyen `OR (current_setting('app.modo_plataforma', true) = 'on')`.
   - Por tanto, no se requiere modificar ningún archivo de `app/core/` (propiedad de Gustavo según `Repartición.md`).
3. **Catálogos globales (`ciudades`, `tallas`, `colores`):**
   - Son tablas globales sin `id_tenant` ni RLS (`0012`–`0014`).
   - Actualmente no tienen columna `activo` en PostgreSQL (`ciudades` tiene `id_ciudad, nombre, pais, creado_en`; `tallas` tiene `id_talla, codigo, orden`; `colores` tiene `id_color, nombre, codigo_hex`).
   - El flujo alternativo **CU08 A2** pide: *«Desactivar un elemento que ya usan productos, sucursales o ventas: el sistema lo desactiva sin borrarlo, para conservar el historial»*, y **CU08 A3**: *«Eliminar un elemento en uso: el sistema lo rechaza»*.
4. **Cuenta de Super Administrador:**
   - El enum `rol_usuario` ya incluye `'super_administrador'` (`0014`) y `chk_usuarios_tenant_segun_rol` exige `id_tenant IS NULL` para ese rol (`0013`).
   - En `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/paginas/login.component.ts` hay un comentario explícito: *«El super administrador aún no tiene pantalla (P2-CU05): va al directorio»*.

---

## 1. Alcance y Decisiones Propuestas

### 1.1 Qué entrega este bloque
1. **P2-CU05 — Gestionar empresas y supervisar la plataforma:**
   - Listado de empresas con métricas operativas (sucursales activas, empleados activos) y suscripción actual.
   - Alta atómica de empresa con su administrador inicial (`usuarios` + `empleados`), `configuracion_tenant` por defecto, `suscripciones` inicial e `historial_suscripcion` (`'alta'`).
   - Cambio de estado de empresa (`'activa'`, `'suspendida'`, `'baja'`) y actualización de datos de contacto, invalidando la caché de tenants (`limpiar_cache_tenants()`).
   - Consulta de la bitácora global de toda la plataforma filtrable por empresa (`id_tenant`), usuario, módulo, severidad y fechas.
2. **P2-CU06 — Gestionar planes y funcionalidades:**
   - Consulta de funcionalidades del sistema y listado de planes con sus límites, funcionalidades y número de empresas suscritas.
   - Creación y edición de planes (`nombre`, `precio_mensual`, `max_sucursales_activas`, `max_empleados`, `activo`, `funcionalidades`).
   - Advertencia con confirmación (`409 REDUCCION_SUPERA_USO_ACTUAL` si `confirmar_reduccion=false`) cuando se reduce un límite por debajo del uso actual de empresas suscritas (CU06 A1).
   - Rechazo (`409 PLAN_CON_EMPRESAS_SUSCRITAS`) al intentar desactivar un plan con suscripciones vigentes (CU06 A2).
3. **P2-CU07 — Gestionar suscripciones de empresas:**
   - Vista consolidada de suscripciones por empresa y su estado efectivo (`'prueba'`, `'activa'`, `'vencida'`, `'suspendida'`, `'cancelada'`).
   - Asignación de plan con fechas de inicio y vencimiento a una empresa sin suscripción vigente (si tenía una suscripción cuya `fecha_vencimiento < hoy`, se marca previamente como `'vencida'`).
   - Suspensión, reactivación y cancelación de suscripciones, registrando cada transición en `historial_suscripcion` y en `bitacora`.
   - Consulta del historial de suscripción por empresa.
4. **P2-CU08 — Gestionar catálogos globales:**
   - Administración centralizada por el super administrador de `ciudades`, `tallas` y `colores` bajo `/api/v1/plataforma/catalogos/...`: listar, crear, editar, activar/desactivar (CU08 A2) y eliminar cuando no tiene referencias en ninguna empresa (CU08 A3).
5. **Frontend Web (`/admin/plataforma`):**
   - Panel exclusivo del `super_administrador` con navegación por secciones (Empresas, Planes, Suscripciones, Catálogos Globales y Bitácora de Plataforma).
   - Redirección automática al iniciar sesión con rol `super_administrador` hacia `/admin/plataforma`.

### 1.2 Decisiones propuestas para aprobación (Gate 0)

| ID | Tema | Propuesta | Motivo |
| :--- | :--- | :--- | :--- |
| **S1** | Desactivación en catálogos globales (CU08 A2) | Añadir `activo BOOLEAN NOT NULL DEFAULT true` a `ciudades`, `tallas` y `colores` mediante una migración `0016_superadmin_catalogos` (acordando el número con Gustavo antes de crearla, según `Repartición.md` regla #1). | Las tres tablas no tienen columna `activo` hoy, y CU08 A2 exige poder desactivar un elemento en uso sin borrarlo. `DEFAULT true` es 100 % compatible con las consultas actuales de todas las empresas. |
| **S2** | Cuenta inicial de `super_administrador` | En la misma migración `0016` (o script semilla idempotente), sembrar una cuenta `super_administrador` (`admin@plataforma.fashionstore.com` o el correo que indique el usuario) si aún no existe ningún usuario con `rol = 'super_administrador'`. | Permite probar de inmediato el login de plataforma y el panel `/admin/plataforma` en pruebas y producción. |
| **S3** | Frontera con `gestion_operativa/` (regla #7) | Todos los endpoints nuevos del super administrador viven en `app/modules/plataforma/` bajo el prefijo `/api/v1/plataforma/...` y se registran en `app/main.py` por adición. No se modifican los archivos de `gestion_operativa/` ni de `app/core/`. | Respeta estrictamente la división de carpetas de `Repartición.md` para evitar conflictos de merge con el trabajo de Gustavo en `CU04`. |
| **S4** | Suscripción inicial en alta de empresa (CU05 paso 4 y 6) | `POST /api/v1/plataforma/empresas` recibe `id_plan`, `estado_suscripcion` (`'activa'` o `'prueba'`, por defecto `'activa'`) y opcionalmente `fecha_inicio` (por defecto hoy UTC) y `fecha_vencimiento` (por defecto `fecha_inicio + 30 días`). | Cumple CU05 paso 6 («crea la empresa, su administrador, sus parámetros por defecto y su suscripción») en una sola transacción y deja a la empresa lista para operar. |

---

## 2. Diseño Técnico — Backend (`Ec-backend/app/modules/plataforma/`)

### 2.1 Estructura de archivos
```
app/modules/plataforma/
├── modelos.py                           # Se amplía si se añade `activo` o helpers; dueño: Tony
├── dependencias.py                      # exigir_super_administrador (fija modo_plataforma = True)
├── router.py                            # Router agregador /api/v1/plataforma
├── cu05_empresas_supervision/
│   ├── esquemas.py
│   ├── repositorio.py
│   ├── servicio.py
│   └── router.py
├── cu06_planes_funcionalidades/
│   ├── esquemas.py
│   ├── repositorio.py
│   ├── servicio.py
│   └── router.py
├── cu07_suscripciones/
│   ├── esquemas.py
│   ├── repositorio.py
│   ├── servicio.py
│   └── router.py
└── cu08_catalogos_globales/
    ├── esquemas.py
    ├── repositorio.py
    ├── servicio.py
    └── router.py
```

### 2.2 Dependencia de autorización y modo plataforma (`dependencias.py`)
- `exigir_super_administrador(usuario: UsuarioORM = Depends(get_current_user), db: Session = Depends(get_db)) -> UsuarioORM`:
  1. Comprueba `str(usuario.rol) == "super_administrador"`; si no, lanza `AuthorizationError("Acceso restringido al super administrador de la plataforma.", code="ACCESO_DENEGADO")` (HTTP 403).
  2. Llama a `fijar_contexto(db, None, id_usuario=usuario.id_usuario, plataforma=True)` para activar `app.modo_plataforma = 'on'` y dejar `app.id_tenant = ''` (los eventos de bitácora que registre el super administrador quedan con `id_tenant = NULL`, es decir, eventos de plataforma según RN51).

### 2.3 Contratos de API (`/api/v1/plataforma/...`)

#### CU05 — Empresas y Supervisión
| Método y Ruta | Descripción | Códigos HTTP |
| :--- | :--- | :--- |
| `GET /api/v1/plataforma/empresas` | Lista empresas con su estado, datos de contacto, suscripción actual, sucursales activas y empleados activos. Filtros opcionales: `estado`, `q`. | `200 OK`, `403` |
| `POST /api/v1/plataforma/empresas` | Crea empresa + administrador inicial + configuración por defecto + suscripción inicial + historial + bitácora. | `201 Created`, `400/422` (código reservado/formato), `404` (plan no existe), `409` (`CODIGO_EMPRESA_DUPLICADO`, `USUARIO_YA_EXISTE`) |
| `PATCH /api/v1/plataforma/empresas/{id_tenant}` | Actualiza `nombre`, `correo_contacto`, `telefono` de la empresa. | `200 OK`, `404` |
| `PATCH /api/v1/plataforma/empresas/{id_tenant}/estado` | Cambia `estado` a `'activa'`, `'suspendida'` o `'baja'`. Limpia caché de tenants y registra en bitácora. | `200 OK`, `400`, `404` |
| `GET /api/v1/plataforma/bitacora` | Lista paginada de eventos de `bitacora` de toda la plataforma con métricas, incluyendo `id_tenant` y `tenant_nombre`. Filtros: `id_tenant`, `id_usuario`, `fecha_inicio`, `fecha_fin`, `severidad`, `tabla_modulo`, `accion`, `q`, `pagina`, `limite`. | `200 OK`, `403` |
| `GET /api/v1/plataforma/bitacora/{id_bitacora}` | Detalle de un evento de bitácora (incluye `payload_anterior` y `payload_nuevo`). | `200 OK`, `404` |

**Detalle transaccional de `POST /api/v1/plataforma/empresas`:**
1. Validar `codigo` contra `^[a-z0-9-]{3,60}$` y que no esté en `CODIGOS_RESERVADOS`. Comprobar que no exista en `tenants` (`409 CODIGO_EMPRESA_DUPLICADO`).
2. Comprobar que el correo del administrador inicial no exista en `usuarios` mediante `correo_ocupado(db, email)` (`409 USUARIO_YA_EXISTE`).
3. Comprobar que el plan (`id_plan`) exista y esté `activo` (`404 PLAN_NO_ENCONTRADO` / `409 PLAN_INACTIVO`), y que `fecha_vencimiento > fecha_inicio`.
4. Insertar `TenantORM` (`flush()` para obtener `id_tenant`).
5. Insertar `UsuarioORM` con `id_tenant = tenant.id_tenant`, `rol = "administrador"`, `activo = True`, y crear su fila en `fashionstore.empleados (id_tenant, id_empleado, codigo_empleado, cargo)` con `id_tenant` explícito.
6. Insertar `ConfiguracionTenantORM(id_tenant=tenant.id_tenant)`.
7. Insertar `SuscripcionORM(id_tenant=tenant.id_tenant, id_plan=..., estado=..., fecha_inicio=..., fecha_vencimiento=...)` (`flush()`) e `HistorialSuscripcionORM(id_tenant=tenant.id_tenant, id_suscripcion=..., evento="alta", id_usuario=superadmin.id_usuario, detalle={"plan": plan.nombre, "origen": "alta_empresa"})`.
8. Registrar en `bitacora` y hacer `commit()`. Llamar a `limpiar_cache_tenants()`.

#### CU06 — Planes y Funcionalidades
| Método y Ruta | Descripción | Códigos HTTP |
| :--- | :--- | :--- |
| `GET /api/v1/plataforma/funcionalidades` | Lista las funcionalidades disponibles en la plataforma. | `200 OK` |
| `GET /api/v1/plataforma/planes` | Lista todos los planes con sus límites, precio, estado `activo`, lista de códigos de funcionalidades y `empresas_suscritas`. | `200 OK` |
| `POST /api/v1/plataforma/planes` | Crea un nuevo plan con sus límites y `funcionalidades`. | `201 Created`, `400/422`, `409 PLAN_NOMBRE_DUPLICADO` |
| `PUT /api/v1/plataforma/planes/{id_plan}` | Actualiza un plan (`nombre`, `precio_mensual`, `max_sucursales_activas`, `max_empleados`, `activo`, `funcionalidades`, `confirmar_reduccion: bool = False`). | `200 OK`, `404`, `409 PLAN_NOMBRE_DUPLICADO`, `409 REDUCCION_SUPERA_USO_ACTUAL`, `409 PLAN_CON_EMPRESAS_SUSCRITAS` |

#### CU07 — Suscripciones de Empresas
| Método y Ruta | Descripción | Códigos HTTP |
| :--- | :--- | :--- |
| `GET /api/v1/plataforma/suscripciones` | Lista cada empresa con su suscripción actual (o última), estado efectivo (`'vencida'` si `fecha_vencimiento < hoy`), días restantes y uso de límites. | `200 OK` |
| `POST /api/v1/plataforma/suscripciones` | Asigna un plan a una empresa (`id_tenant`, `id_plan`, `estado` `'activa' \| 'prueba'`, `fecha_inicio`, `fecha_vencimiento`). | `201 Created`, `400 FECHAS_INVALIDAS`, `404`, `409 SUSCRIPCION_VIGENTE_EXISTENTE` |
| `PATCH /api/v1/plataforma/suscripciones/{id_suscripcion}/estado` | Cambia el estado de una suscripción (`'suspendida'`, `'activa'`, `'cancelada'`) o actualiza su plan/vigencia, registrando en `historial_suscripcion` y `bitacora`. | `200 OK`, `400`, `404`, `409` |
| `GET /api/v1/plataforma/empresas/{id_tenant}/historial-suscripcion` | Lista el historial de eventos de suscripción de la empresa ordenados por `creado_en DESC`. | `200 OK`, `404` |

#### CU08 — Catálogos Globales (Ciudades, Tallas, Colores)
| Método y Ruta | Descripción | Códigos HTTP |
| :--- | :--- | :--- |
| `GET /api/v1/plataforma/catalogos/ciudades` | Lista ciudades globales con `activo` y conteo global de sucursales/clientes en todas las empresas. | `200 OK` |
| `POST /api/v1/plataforma/catalogos/ciudades` | Crea una ciudad global (`nombre`, `pais`). | `201 Created`, `409 CIUDAD_DUPLICADA` |
| `PUT /api/v1/plataforma/catalogos/ciudades/{id_ciudad}` | Edita `nombre`, `pais` o `activo`. | `200 OK`, `404`, `409 CIUDAD_DUPLICADA` |
| `PATCH /api/v1/plataforma/catalogos/ciudades/{id_ciudad}/estado` | Activa o desactiva la ciudad sin borrarla (CU08 A2). | `200 OK`, `404` |
| `DELETE /api/v1/plataforma/catalogos/ciudades/{id_ciudad}` | Elimina la ciudad solo si no tiene sucursales ni clientes asociados en ninguna empresa (CU08 A3). | `200 OK`, `404`, `409 ELEMENTO_EN_USO` |
| `GET /api/v1/plataforma/catalogos/tallas` | Lista tallas globales con `activo` y total de variantes en la plataforma. | `200 OK` |
| `POST /api/v1/plataforma/catalogos/tallas` | Crea una talla (`codigo`, `orden`). | `201 Created`, `409 TALLA_DUPLICADA` |
| `PUT /api/v1/plataforma/catalogos/tallas/{id_talla}` | Edita `codigo`, `orden` o `activo`. | `200 OK`, `404`, `409 TALLA_DUPLICADA` |
| `PATCH /api/v1/plataforma/catalogos/tallas/{id_talla}/estado` | Activa o desactiva la talla sin borrarla (CU08 A2). | `200 OK`, `404` |
| `DELETE /api/v1/plataforma/catalogos/tallas/{id_talla}` | Elimina la talla si ninguna variante la usa (CU08 A3). | `200 OK`, `404`, `409 ELEMENTO_EN_USO` |
| `GET /api/v1/plataforma/catalogos/colores` | Lista colores globales con `activo` y total de variantes en la plataforma. | `200 OK` |
| `POST /api/v1/plataforma/catalogos/colores` | Crea un color (`nombre`, `codigo_hex`). | `201 Created`, `409 COLOR_DUPLICADO` |
| `PUT /api/v1/plataforma/catalogos/colores/{id_color}` | Edita `nombre`, `codigo_hex` o `activo`. | `200 OK`, `404`, `409 COLOR_DUPLICADO` |
| `PATCH /api/v1/plataforma/catalogos/colores/{id_color}/estado` | Activa o desactiva el color sin borrarlo (CU08 A2). | `200 OK`, `404` |
| `DELETE /api/v1/plataforma/catalogos/colores/{id_color}` | Elimina el color si ninguna variante lo usa (CU08 A3). | `200 OK`, `404`, `409 ELEMENTO_EN_USO` |

---

## 3. Diseño Técnico — Frontend Web (`Ec-frontend/`)

### 3.1 Estructura de archivos
```
src/app/modules/plataforma/superadmin/
├── modelos/
│   └── superadmin.model.ts
├── servicios/
│   ├── superadmin.service.ts
│   └── superadmin.service.spec.ts
└── paginas/
    ├── superadmin-panel.component.ts
    ├── superadmin-panel.component.html
    ├── superadmin-panel.component.scss
    └── superadmin-panel.component.spec.ts
```

### 3.2 Rutas y Navegación
- En `app.routes.ts` (por adición, antes de las redirecciones y de `:codigo`):
  ```ts
  {
    path: 'admin/plataforma',
    canActivate: [authGuard, roleGuard(['super_administrador'])],
    loadComponent: () =>
      import('./modules/plataforma/superadmin/paginas/superadmin-panel.component').then(
        (m) => m.SuperadminPanelComponent
      ),
    title: 'FashionStore | Panel de Plataforma SaaS',
  },
  ```
- En `login.component.ts` (`irAlDestino`): si `rol === 'super_administrador'`, navegar a `['/admin/plataforma']`.
- En `tenant.guard.ts` (`destinoEmpleado` o manejo de sesión): si un `super_administrador` entra a `/admin`, redirigir o mostrar enlace a `/admin/plataforma`.
- Todos los componentes cumplen: `standalone: true`, `ChangeDetectionStrategy.OnPush`, Signals (`signal`, `computed`), `inject()`, `@if`/`@for` y tokens Base-2 (`space-1` a `space-7`, paleta `slate`/`camel`).

---

## 4. Criterios de Aceptación (Trazabilidad AC → Tests)

- **AC-01 (CU05 - Alta de empresa):** Cuando el super administrador registra una empresa con código válido, correo de administrador único y plan activo, el sistema crea `tenants`, `usuarios` (`rol='administrador'`), `empleados`, `configuracion_tenant`, `suscripciones` e `historial_suscripcion` (`'alta'`) y devuelve `201`.
- **AC-02 (CU05 A1/A4 - Validaciones en alta):** Si el código está repetido, tiene formato inválido o es reservado (`admin`, `login`…), o si el correo del administrador ya existe en la plataforma, el sistema rechaza la operación (`409` / `400`) sin dejar registros parciales.
- **AC-03 (CU05 A2/A3 - Suspensión y reactivación):** Al cambiar el estado de una empresa a `'suspendida'` o `'baja'`, se limpia la caché y sus empleados/clientes ya no pueden operar en ella (`403 TENANT_INACTIVO`); al reactivarla (`'activa'`), recuperan el acceso.
- **AC-04 (CU05 paso 8 - Bitácora global):** El super administrador consulta `/api/v1/plataforma/bitacora` viendo eventos de todas las empresas y de plataforma (`id_tenant = NULL`), con filtro por `id_tenant`, usuario y fechas.
- **AC-05 (CU06 - Crear y editar planes):** El super administrador crea y edita planes y sus funcionalidades; `SuscripcionServicio.validar` (CU12) aplica los nuevos límites y funcionalidades de inmediato sin tocar código.
- **AC-06 (CU06 A1/A2 - Salvaguardas de planes):** Reducir un límite por debajo del uso actual de empresas suscritas sin `confirmar_reduccion=True` devuelve `409 REDUCCION_SUPERA_USO_ACTUAL` indicando cuántas empresas quedan por encima; desactivar un plan con empresas suscritas devuelve `409 PLAN_CON_EMPRESAS_SUSCRITAS`.
- **AC-07 (CU07 - Asignación y ciclo de vida de suscripciones):** Asignar una suscripción a una empresa que ya tiene una vigente devuelve `409 SUSCRIPCION_VIGENTE_EXISTENTE`; suspender, reactivar o cancelar actualiza `suscripciones.estado` y añade la fila correspondiente en `historial_suscripcion`.
- **AC-08 (CU08 - Catálogos globales):** El super administrador crea, edita y desactiva (`activo=False`) ciudades, tallas y colores; intentar eliminar un elemento en uso devuelve `409 ELEMENTO_EN_USO`; cualquier rol distinto de `super_administrador` recibe `403 ACCESO_DENEGADO`.

