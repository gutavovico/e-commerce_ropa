# Especificación Técnica: Acceso por empresa (P2-CU02 Iniciar sesión · P2-CU01 Registrarse)

**ID del cambio:** `P2-CU02-CU01-acceso-por-empresa`
**Fuente:** `SI2-Parcial2.md` CU01, CU02, RN03–RN06, RN08, PF-01 a PF-09; decisiones del usuario del 2026-11-08 (§2), que **modifican** el documento (§1.4).
**Depende de:** `P2-CU13-CU12-fundacion-multitenant` (en producción, Alembic `0014`).
**Nivel SDD:** **3 (alto riesgo)**: autenticación, unicidad de correos con datos de producción y retirada del modo de transición (`TENANT_POR_DEFECTO`).
**Bloques:** Backend → Web → Mobile, cada uno con su gate.
**Estado:** 🟢 Aprobada el 2026-11-08 (A1–A16). Backend y web aprobados; móvil completo, pendiente de aprobación. Por decisión del usuario, se publica todo junto tras el bloque móvil.
**Fecha:** 2026-11-08

---

## 0. Hallazgos (código y esquema al 2026-11-08)

### 0.1 Backend
- `LoginIn.codigo_empresa` es opcional. Sin él, el login busca primero una cuenta sin empresa (cliente o super administrador) y luego un empleado de la empresa de la sesión, que hoy es `TENANT_POR_DEFECTO = fashionstore` (`cu02_iniciar_sesion/servicio.py::_buscar_usuario`).
- El token del cliente lleva `id_tenant` = la empresa de la sesión si está registrado en ella (`TenantServicio.empresa_del_token`).
- **Unicidad de correo (0013):** `uq_usuarios_email_empresa (id_tenant, email)` para empleados y `uq_usuarios_email_global (email) WHERE id_tenant IS NULL` para clientes y super administradores. Un mismo correo puede existir en varias empresas.
- **La RLS de `usuarios`** solo deja ver las cuentas sin empresa y los empleados de la empresa del contexto. Antes de saber quién inicia sesión no hay empresa, así que un empleado **no se puede encontrar por su correo** sin el modo de transición. Lo mismo afecta a la recuperación de acceso (`cu33`, busca por correo) y a la comprobación de correo repetido del registro (`cu01`) y del alta de empleados (`cu20`).
- `suscripciones` tiene RLS estándar: no se puede saber si otra empresa tiene suscripción vigente sin modo plataforma.
- `cu20` ya asigna a cada empleado nuevo la empresa del administrador que lo crea (`TenantServicio.empresa_para_rol` → empresa de la sesión, que es la del token del administrador). **Lo pedido para empleados ya funciona**; falta la prueba.
- `cliente_tenant` ya permite al cliente ver todas sus empresas (`id_cliente = app.id_usuario`).
- `tenants.codigo` admite cualquier `^[a-z0-9-]{3,60}$`, incluidos `admin` o `login`, que chocarían con rutas de la web.

### 0.2 Web
- Las rutas del cliente están en la raíz (`/inicio`, `/catalogo`, `/bolsa`, `/productos/:id`…); `''` es la landing de FASHION STORE. No hay noción de empresa.
- `authInterceptor` solo añade `Authorization`. Ninguna petición envía `X-Tenant`.
- «FASHION STORE» aparece escrito en 52 lugares de `src/app`.

### 0.3 Móvil
- La app arranca en `PantallaLogin` y, tras el login, abre `PantallaPrincipalHub`. No hay registro de empresa.
- Hay 17 datasources, cada uno con su propio `http`. Ninguno envía `X-Tenant`.
- «FASHION STORE» aparece en 17 lugares de `lib/`.

### 0.4 No verificado
- **Si hay correos repetidos en `usuarios`** en producción y en la rama de pruebas (el clasificador bloqueó la consulta). Es la condición de la migración `0015`: ver T-0-02.

---

## 1. Alcance

### 1.1 Qué entrega
1. **Login solo con correo y contraseña** para todos los roles. La cuenta determina la empresa del empleado.
2. **Correo único en toda la plataforma** (migración `0015`).
3. **Portal web por empresa** en `/{codigo}`, con su login, registro y recuperación de acceso.
4. **«Registrarme en esta tienda»** (solo web): un cliente con cuenta se registra en la empresa del portal sin crear otra contraseña.
5. **Directorio de empresas** en la raíz `/` de la web y sección «Mis tiendas» para el cliente con sesión.
6. **Pantalla de selección de empresa** en el móvil, entre el login y `PantallaPrincipalHub`, con «Cambiar de tienda» en Perfil.
7. **Retirada del modo de transición:** se elimina `TENANT_POR_DEFECTO`. Toda petición de datos de negocio indica su empresa (`X-Tenant` o token de empleado).
8. **Nombre de la empresa en la cabecera** del portal web y del hub móvil, en lugar de «FASHION STORE» fijo.

### 1.2 Fuera de alcance
- Usuario super administrador y su panel (P2-CU05 a P2-CU08). El login lo admite (token sin empresa), pero tras iniciar sesión no tiene pantalla. Su enrutamiento se define en P2-CU05.
- Contenido propio de cada empresa en la landing (imágenes de portada, textos de campaña, colores). La landing de FASHION STORE es contenido femenino de esa empresa. El contenido por empresa llega con la empresa de prueba Menshopping (RF15).
- Subdominios por empresa (decisión 2: ruta `/{codigo}`).
- Sesión sin conexión (CU02 A6) y notificaciones push: bloques de operación sin conexión y de RF37.

### 1.3 Compatibilidad
- Las apps móviles instaladas antes de este cambio **dejan de ver datos** cuando se despliega el backend, porque no envían empresa. Hay que instalar el APK nuevo.
- La web se despliega con el mismo push (Vercel) y no tiene ventana de incompatibilidad.
- Los tokens de cliente emitidos antes del despliegue llevan `id_tenant`. Siguen siendo válidos: el backend usa esa empresa si la petición no indica otra (§A.4).

### 1.4 Cambios en `SI2-Parcial2.md` (se aplican al aprobar esta spec)
| Elemento | Hoy | Pasa a |
| :--- | :--- | :--- |
| RN03 | El código de empresa sirve para iniciar sesión | Identifica el portal de la empresa (`/{codigo}`); no se pide en el login. No puede coincidir con una ruta reservada de la web. |
| RN05 | Correo único por empresa para empleados | Correo único en toda la plataforma, para todos los roles |
| CU01 | Registro en el portal; en móvil «eligiéndola» | En la web, desde el portal de la empresa. En el móvil, la cuenta se crea sin empresa y se registra en una desde la web. Nuevo flujo «Registrarme en esta tienda». |
| CU02 | Empleados con código de empresa; A3 «solicita el código» | Todos con correo y contraseña; se elimina A3; A4 sin código |
| CU12 (precondición) | «la empresa se identifica por su código» en el login | «la empresa es la de la cuenta del empleado» |
| PF-04, PF-05, PF-06, PF-09 | Login con código y correos repetidos entre empresas | Login sin código; correo repetido rechazado en toda la plataforma |

---

## 2. Decisiones aprobadas (2026-11-08)

| ID | Decisión |
| :--- | :--- |
| A1 | Login con correo y contraseña, sin código de empresa, para todos los roles. |
| A2 | **Correo único en toda la plataforma.** Una persona que sea empleada de una empresa y clienta de otra necesita dos correos. |
| A3 | Portal web por ruta: `/{codigo}` (p. ej. `/menshopping`). |
| A4 | La raíz `/` de la web es un directorio de las empresas disponibles. |
| A5 | Los empleados inician sesión en el `/login` general y van a su panel. Si un empleado con sesión abre el portal de otra empresa, se le lleva al suyo. |
| A6 | Cliente del móvil sin empresas: estado vacío «Regístrate en una tienda desde la web». |
| A7 | El registro de cuentas nuevas se mantiene en el móvil; la cuenta queda sin empresa hasta registrarse en una desde la web. |
| A8 | El registro en una empresa («Registrarme en esta tienda») es exclusivo de la web. |
| A9 | Los empleados reciben la empresa del administrador que crea su cuenta (ya implementado). |

### 2.1 Decisiones técnicas propuestas (se aprueban con la spec)
| ID | Propuesta | Motivo |
| :--- | :--- | :--- |
| A10 | **El token del cliente no lleva empresa** (`id_tenant: null`). La empresa viaja en cada petición con `X-Tenant`: en la web la pone la URL y en el móvil la empresa elegida. | Cambiar de tienda no exige un token nuevo ni la contraseña (CU02 A7). El aislamiento no se debilita: la RLS filtra por la cabecera y `exigir_cliente_en_tenant` impide comprar o reservar donde no está registrado. |
| A11 | **Búsqueda de la cuenta por correo con una función `SECURITY DEFINER`** (`fashionstore.cuenta_por_email`) que devuelve solo `id_usuario` e `id_tenant`. El servicio fija después el contexto de esa empresa y lee la fila completa bajo RLS. | Alternativa descartada: activar el modo plataforma durante el login, que abre todas las tablas a la sesión. La función expone dos columnas y nada más. |
| A12 | **Empresas disponibles con otra función `SECURITY DEFINER`** (`fashionstore.empresas_disponibles`): `codigo` y `nombre` de las empresas activas con suscripción vigente. | Lo necesitan el directorio y «Mis tiendas», y `suscripciones` tiene RLS. |
| A13 | **Códigos reservados**: `tenants.codigo` no puede ser `admin`, `login`, `registro`, `recuperar-acceso`, `recuperar-password`, `iniciar-sesion`, `api`, `ar`, `static`, `assets`, `mis-tiendas`, `pago` ni `plataforma`. CHECK en `0015`. | El portal `/{codigo}` comparte espacio de rutas con las páginas fijas. |
| A14 | **Rutas antiguas del cliente** (`/inicio`, `/catalogo`, `/bolsa`, `/productos/:id`, …) redirigen al directorio `/`. | No se fija ninguna empresa en el código de la web; los enlaces viejos no dan 404. |
| A15 | El login responde también `empresas`: la lista de tiendas del cliente (vacía para empleados). El móvil la usa para la pantalla de selección sin otra llamada. | Ahorra una petición en el arranque. `GET /mis-empresas` existe igualmente para refrescarla. |
| A16 | La pantalla de selección del móvil se muestra **siempre**, aunque haya una sola tienda. | Es lo que pidió el usuario; omitirla con una sola tienda es un cambio de una línea si se decide después. |

---

## A. Backend

### A.1 Migración `0015_correo_global` (`down_revision = "0014"`)
1. **Precondición** (aborta con mensaje claro si falla): no hay dos filas de `usuarios` con el mismo `lower(email)`.
2. Elimina `uq_usuarios_email_empresa` y `uq_usuarios_email_global`; crea `uq_usuarios_email UNIQUE (lower(email))`.
3. `fashionstore.cuenta_por_email(p_email text) RETURNS TABLE (id_usuario bigint, id_tenant bigint)`:
   `LANGUAGE sql STABLE SECURITY DEFINER SET search_path = fashionstore, pg_temp`. Busca `lower(email) = lower(p_email)`.
4. `fashionstore.empresas_disponibles() RETURNS TABLE (id_tenant bigint, codigo text, nombre text)`: empresas `activa` con una suscripción `prueba`/`activa` cuya `fecha_vencimiento >= current_date`. Mismo `SECURITY DEFINER` y `search_path`.
5. `REVOKE ALL ... FROM PUBLIC` y `GRANT EXECUTE` de las dos funciones a `fashionstore_app` (si el rol existe).
6. CHECK `chk_tenants_codigo_reservado` (A13).
7. `downgrade`: restaura los dos índices parciales, elimina el índice global, las funciones y el CHECK.

### A.2 Contratos

| Método y ruta | Auth | Cambio |
| :--- | :--- | :--- |
| `POST /api/v1/autenticacion/login` | Pública | Sin `codigo_empresa` (si llega, se ignora). Respuesta: `tenant` (empresa del empleado; `null` para cliente y super administrador) y `empresas: [{codigo, nombre}]` (A15). |
| `POST /api/v1/autenticacion/registrarse` | Pública | Con `X-Tenant`: crea la cuenta y la registra en esa empresa (la empresa debe estar disponible). Sin `X-Tenant`: crea la cuenta sin empresa (móvil, A7). Token sin empresa (A10). 409 `USUARIO_YA_EXISTE` si el correo existe en cualquier rol. |
| `GET /api/v1/tenants` | Pública | **Nuevo.** Directorio: `[{codigo, nombre}]` de `empresas_disponibles()`. |
| `GET /api/v1/tenants/{codigo}` | Pública | **Nuevo.** Datos del portal `{codigo, nombre}`. 404 `TENANT_NO_ENCONTRADO`; 403 `TENANT_INACTIVO` si está suspendida, dada de baja o sin suscripción vigente. |
| `GET /api/v1/mis-empresas` | Cliente | **Nuevo.** Empresas del cliente que están disponibles. |
| `POST /api/v1/mis-empresas` | Cliente + `X-Tenant` | **Nuevo.** «Registrarme en esta tienda». Idempotente: 201 al registrar, 200 si ya lo estaba. 403 `TENANT_INACTIVO`; 400 `TENANT_REQUERIDO` sin cabecera; 403 `SOLO_CLIENTES` para empleados. |
| Recuperar acceso (`cu33`) | Pública | Sin cambio de contrato; busca la cuenta con `cuenta_por_email`. |

### A.3 Login (`cu02`)
1. `cuenta_por_email(email)`. Si no hay cuenta → 401 `CREDENCIALES_INVALIDAS` (mismo mensaje que hoy; se registra en la bitácora).
2. Fija el contexto: la empresa de la cuenta (empleado) o ninguna (cliente o super administrador), con `id_usuario`. Lee la fila bajo RLS.
3. Contraseña y cuenta activa, como hoy.
4. **Empleado:** empresa activa (`TENANT_INACTIVO`) y suscripción vigente (`SuscripcionServicio.validar` sin funcionalidad → `SUSCRIPCION_NO_VIGENTE`). El mensaje pide contactar al administrador de la empresa (CU02 A2).
5. Token: `id_tenant` = empresa del empleado; `null` para cliente y super administrador (A10).

### A.4 Contexto de empresa (`core/tenant.py`, `database.py`)
- `preparar_sesion(db, cabecera)` sin empresa por defecto: sin cabecera, la sesión queda sin empresa.
- `aplicar_tenant_del_token`:
  - **Empleado:** manda su empresa. Una cabecera distinta → 403 `TENANT_NO_COINCIDE`, como hoy.
  - **Cliente:** manda la cabecera. Un token antiguo de cliente con `id_tenant` y sin cabecera conserva esa empresa (§1.3); con cabecera, gana la cabecera.
- Se elimina `TENANT_POR_DEFECTO` de `config.py`, `database.py`, `tenant.py` y las pruebas.
- `buscar_tenant` sigue sin RLS (`tenants` no la tiene). La comprobación «disponible» (activa y con suscripción vigente) usa `empresas_disponibles()`.

### A.5 Registro (`cu01`), alta de empleados (`cu20`) y recuperación (`cu33`)
- **Correo repetido:** se comprueba con `cuenta_por_email` en los tres. El índice único global es la red de seguridad: su `IntegrityError` se traduce a 409.
- **`cu20`:** sin cambios de lógica. Prueba nueva: un empleado creado por el administrador de la empresa 1 queda con `id_tenant = 1`; un correo que ya es de un cliente → 409.
- **`cu33`:** localiza la cuenta con la función y fija el contexto de su empresa antes de leer o actualizar.

### A.6 Pruebas
- **Unitarias:** login de empleado, cliente y super administrador sin código; token de cliente sin empresa; empleado con empresa suspendida o sin suscripción; registro con y sin `X-Tenant`; `POST /mis-empresas` idempotente y 403 para empleados; `TENANT_NO_COINCIDE` solo para empleados; token antiguo de cliente con empresa.
- **Integración (rama `pruebas-multitenant`, rol `fashionstore_app`):**
  - `cuenta_por_email` encuentra a un empleado de la empresa 2 sin contexto y no devuelve más columnas que las dos.
  - El índice global rechaza un correo repetido entre empresas.
  - `empresas_disponibles` excluye las empresas suspendidas o sin suscripción vigente.
  - Sin `X-Tenant` y sin token de empleado, `GET /productos` devuelve una lista vacía.
  - El CHECK rechaza un código reservado.
  - El flujo completo del cliente: registro en la empresa 1 → `GET /mis-empresas` → `POST /mis-empresas` en la empresa 2 → carrito en la 2 → la 1 no ve ese carrito.

---

## B. Web

### B.1 Rutas (`app.routes.ts`)
Orden obligatorio (lo vigila `app.routes.spec.ts`):
1. `''` (`pathMatch: 'full'`) → **`DirectorioEmpresasComponent`**: lista de `GET /tenants` y, con sesión de cliente, la sección «Mis tiendas» (`GET /mis-empresas`) arriba.
2. Rutas fijas: `login`, `iniciar-sesion`, `recuperar-acceso`, `recuperar-password`, `admin/**` (sin cambios).
3. Redirecciones de las rutas antiguas del cliente a `/` (A14).
4. **`:codigo`** con `tenantGuard` y `TenantLayout` como padre. Sus hijos son las rutas actuales del cliente, con la misma estructura de raíces y hojas:
   - raíces bajo `MainLayoutComponent`: `inicio`, `buscar`, `catalogo`, `perfil`;
   - hojas al nivel de `:codigo`: `colecciones`, `colecciones/:id`, `bolsa`, `pago/:idVenta`, `reservas`, `productos/:id`, `catalogo/:id`, `mi-cuenta`;
   - `''` del portal → landing de la empresa;
   - `login`, `registro` y `recuperar-acceso` del portal.
5. `**` al final.

La navegación Hub-and-Spoke no cambia: las cuatro raíces siguen siendo las únicas con barra principal, ahora bajo `/{codigo}`.

### B.2 Servicios
- **`TenantService`** (nuevo, `core/tenant/`): signal `tenantActual` `{codigo, nombre} | null`, `cargar(codigo)` contra `GET /tenants/{codigo}`, y el directorio.
- **`tenantGuard`:**
  - empresa inexistente → `/` con aviso «La tienda no existe»;
  - empresa no disponible → página «Esta tienda no está disponible»;
  - empleado con sesión en otra empresa → `/admin` (A5).
- **`authInterceptor`:** añade `X-Tenant` con `tenantActual().codigo` **solo** a las peticiones hechas dentro del portal. El panel `/admin` no lo envía (manda el token).
- **`LoginService`:**
  - guarda `tenant` y `empresas` de la respuesta;
  - enlaces internos del portal con prefijo `/{codigo}` mediante un helper `rutaPortal(...)`;
  - las navegaciones de los componentes del cliente usan ese helper.

### B.3 Login, registro y «Registrarme en esta tienda»
- **`/login` (general):** empleados → su panel (como hoy: cajero `/admin/pos`, administrador `/admin`, encargado su panel). Un cliente → `/` con «Mis tiendas».
- **`/{codigo}/login`:** un cliente registrado → `/{codigo}/inicio`. Si no está registrado, entra igual y ve el aviso «Registrarme en esta tienda». Un empleado → su panel.
- **`/{codigo}/registro`:** crea la cuenta y la registra en la empresa (CU01). Un 409 `USUARIO_YA_EXISTE` ofrece «Iniciar sesión» (CU01 A1) y «Recuperar acceso» (A2).
- **Aviso «Registrarme en esta tienda»** (componente `RegistroEnTiendaComponent`):
  - aparece en el portal para un cliente con sesión que no está en `empresas`;
  - lo abre también cualquier 403 `CLIENTE_NO_REGISTRADO` (bolsa, reserva, compra);
  - al confirmar, `POST /mis-empresas`; después actualiza `empresas` y repite la acción interrumpida si la había.
- **Cabecera y pie del portal:** muestran `tenantActual().nombre`. En el panel `/admin`, el nombre de la empresa del token.

### B.4 Pruebas web
- `app.routes.spec.ts`: el orden de §B.1; `:codigo` después de las rutas fijas y antes de `**`.
- `tenantGuard`: empresa inexistente, no disponible y empleado de otra empresa.
- `authInterceptor`: `X-Tenant` dentro del portal y no en `/admin`.
- Login: destinos por rol y por portal.
- `RegistroEnTiendaComponent`: con un 403 `CLIENTE_NO_REGISTRADO` literal del backend.

---

## C. Móvil

### C.1 Flujo
`PantallaLogin` → (cliente) **`PantallaSeleccionEmpresa`** → `PantallaPrincipalHub`; (empleado) → `PantallaPrincipalHub`.

- **`PantallaSeleccionEmpresa`** (nueva, `autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/`):
  - lista `empresas` del login (refrescable con `GET /mis-empresas`);
  - estado vacío A6 «Regístrate en una tienda desde la web»;
  - no es una raíz Hub-and-Spoke: no tiene barra de navegación.
- **«Cambiar de tienda»** en Perfil: vuelve a la selección sin cerrar sesión (CU02 A7).
- **Registro (A7):** sin `X-Tenant`. Tras crear la cuenta lleva a la selección, que mostrará el estado vacío.

### C.2 Empresa en las peticiones
- **`EmpresaActual`** (nuevo, `lib/src/core/`): singleton con la empresa elegida (`codigo`, `nombre`) y `cabeceras()`, que devuelve `{'X-Tenant': codigo}` si hay empresa.
- Los 17 datasources añaden `...EmpresaActual.instancia.cabeceras()` a sus cabeceras. Se propagan igual que el JWT, sin tocar los constructores de las pantallas.
- Cerrar sesión limpia `EmpresaActual`.
- El nombre de la cabecera del hub sale de `EmpresaActual`.
- Un 403 `CLIENTE_NO_REGISTRADO` muestra «Regístrate en esta tienda desde la web».

### C.3 DTO y pruebas
- `LoginResponse.fromJson` con `tenant` y `empresas`, probado con un **payload literal** copiado del backend.
- `EmpresaActual.cabeceras()`.
- `PantallaSeleccionEmpresa` con lista y vacía.
- `dart analyze` sin incidencias.

---

## D. Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| Hay correos repetidos y `0015` falla | Precondición explícita (T-0-02); la migración aborta sin cambios y se decide qué cuenta conservar antes de reintentar. |
| Una función `SECURITY DEFINER` mal escrita expone datos | Devuelve dos columnas, `search_path` fijo, `REVOKE ... FROM PUBLIC`; prueba de integración que lo verifica. |
| Desplegar el backend sin la web rompe el portal | Backend y web van en el mismo push. Orden: `0015` a mano → push → APK. |
| Un componente de la web navega a una ruta antigua sin prefijo | La redirección A14 lo lleva al directorio en vez de a un 404, y las pruebas de navegación cubren los destinos. |
| Una app móvil antigua sin `X-Tenant` muestra listas vacías | Aviso en §1.3; se distribuye el APK nuevo. |

---

## E. Deltas de la implementación (bloque 1)

- **Δ1 · Ruta del registro:** es `POST /api/v1/autenticacion/registrarse` (la ruta existente); §A.2 decía `/registro`.
- **Δ2 · Bitácora sin empresa:** el login de un cliente fuera de un portal deja la sesión sin empresa y su
  evento se guarda con `id_tenant` nulo. El `INSERT … RETURNING` del ORM fallaba porque la política de
  `bitacora` no deja leer esa fila, y el fallo (capturado como «no bloqueante») dejaba la sesión inservible
  → 500 en el login. `registrar_evento_seguro` inserta ahora sin `RETURNING` y, en la sesión del caso de
  uso, dentro de un punto de guardado: un fallo de auditoría ya no puede tumbar la operación. Detectado por
  la prueba de integración del flujo del cliente, antes de llegar a producción.
- **Δ3 · Correo único:** `cuentas.correo_ocupado()` (paquete `autenticacion_seguridad`) centraliza la
  comprobación para CU01 y CU20; con sesiones simuladas usa la consulta ORM.
- **Δ5 · Tienda no disponible (web):** en lugar de una página propia, `tenantGuard` lleva al directorio
  `/` con un aviso (`?aviso=tienda-inexistente` o `tienda-no-disponible`).
- **Δ6 · Acción interrumpida:** tras «Registrarme en esta tienda» no se repite automáticamente la operación
  que devolvió `CLIENTE_NO_REGISTRADO`; el aviso confirma el registro y el cliente la vuelve a pulsar.
- **Δ7 · `/registro` general:** redirige al directorio. El registro de cuentas en la web se hace siempre
  desde el portal de una tienda (CU01).
- **Δ8 · Asistente (CU19):** el widget solo se muestra dentro de un portal; fuera no hay catálogo.
- **Δ9 · Marca:** `<app-marca-tienda />` sustituye a «FASHION STORE» escrito en 30 plantillas (portal,
  panel y comprobantes) y `TituloTiendaStrategy` lo sustituye en los títulos. Fuera de un portal y sin
  empleado se muestra el nombre de la plataforma («FashionStore»).
- **Δ10 · Defecto previo corregido:** con sesión abierta, el login enviaba al encargado de sucursal a
  `/inicio` en vez de a `/admin`; ahora usa el mismo destino por rol que el guard (`destinoEmpleado`).
- **Δ11 · Enlaces del cliente:** pipe `rutaPortal` en las plantillas y `TenantService.ruta()` en las
  navegaciones (18 componentes y servicios), en lugar de un helper por componente.
- **Δ12 · Página en blanco al arrancar (NG0200):** `TituloTiendaStrategy` inyectaba `TenantService`, que
  inyecta el `Router`, que necesita la estrategia de títulos → dependencia circular y la aplicación no
  arrancaba. Las pruebas no lo veían porque ninguna usaba `appConfig`. La estrategia obtiene ahora el
  servicio con el `Injector` al actualizar el título; `app.config.spec.ts` arranca con la configuración real
  para que no vuelva a pasar. Detectado por el usuario en `ng serve`.
- **Δ13 · Cabecera `X-Tenant` en el móvil:** en lugar de editar las cabeceras de los 17 datasources, todos
  usan por defecto `ClienteHttpApi` (`lib/src/core/cliente_http_api.dart`), un `http.BaseClient` que añade
  la tienda de `EmpresaActual` a las rutas `/api/...` (equivale al interceptor de la web). Las pruebas
  siguen inyectando su propio cliente.
- **Δ14 · Registro en el móvil:** al crear la cuenta se vuelve al login (comportamiento previo); tras iniciar
  sesión, la selección muestra el estado vacío A6.
- **Δ15 · `CLIENTE_NO_REGISTRADO` en el móvil:** sin tratamiento propio. La selección solo ofrece tiendas
  en las que el cliente ya está registrado; si aun así ocurre, se muestra el mensaje del backend.
- **Δ16 · Defecto previo corregido:** `main.dart` pasaba al login dos callbacks y ambos abrían el hub
  (dos `pushAndRemoveUntil` seguidos). Ahora solo se usa `alCompletarLoginConUsuario`.
- **Δ17 · Empleados en el móvil:** `EmpresaActual` toma la empresa de su cuenta (`tenant` del login), así la
  marca de la pantalla de reportes por voz y de sucursales muestra su empresa.
- **Δ4 · Empresas del token de empleado:** el login valida, además de la empresa activa, la suscripción
  vigente con `SuscripcionServicio.validar(db, id_tenant=…)` (CU02 A2).
