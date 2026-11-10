# Especificación Técnica: Operación sin conexión — P2-CU14, CU15, CU19 y CU20 (+ adaptación web de CU16/CU17)

**ID del cambio:** `P2-CU14-CU15-CU19-CU20-sin-conexion`
**Fuente:** `SI2-Parcial2.md` §2.1.2.3, CU14, CU15, CU16, CU17, CU19, CU20, RF16–RF19, RF25, RF26,
RNF03, RNF15, RN21, RN25, RN33–RN43; decisiones del usuario del 2026-11-09:
- avisos al cliente en una **bandeja dentro de la app**, sin Firebase;
- reembolsos del cierre de mes lanzados por un **botón del administrador**;
- la **caja en el móvil** (CU16/CU17 Flutter) va en un cambio aparte, antes de CU18.

**Depende de:** `P2-CU13-CU12-fundacion-multitenant`, `P2-CU11-parametros-empresa` (parámetros
sin conexión y de reserva) y de que **`0017`–`0019` (Tony) estén aplicadas en producción** antes
de aplicar `0020`.
**Nivel SDD:** **3 (riesgo alto)**: migración, inventario, dinero (reembolsos) y tres stacks.
**Bloques:** Backend → Web (PWA + CU20) → Móvil (SQLite). Cada bloque se aprueba antes del
siguiente.
**Responsable:** Gustavo (`reparticion.md`, bloque 3).
**Estado:** 🟡 Pendiente de aprobación.
**Fecha:** 2026-11-09

---

## 0. Hallazgos (rama de pruebas y código, al 2026-11-09)

| Necesita | Hoy |
| :--- | :--- |
| Tablas `dispositivos`, `operaciones_sync`, `conflictos_sync` y `sync_log` (nota del §5 de `SI2-Parcial2.md`) | **No existen.** |
| PWA (service worker, manifiesto, IndexedDB) | **No existe.** La web no funciona sin conexión. |
| SQLite, conectividad y UUID en el móvil | **No existen** (`pubspec.yaml` no tiene `sqflite`, `connectivity_plus` ni `uuid`). |
| Reserva de varias prendas en línea (CU15) | **Existe** (`POST /api/v1/reservas`, web y móvil), con `reserva_detalle` y movimientos de inventario. |
| Vencimiento de la reserva por parámetro (RN25, CU11 C1/C7) | **No.** `reservas` no tiene `vence_en`; una reserva vence 2 h después de la cita (D1-A del Parcial 1) y `horas_vencimiento_reserva` no se usa. |
| Compra interrumpida | El servidor crea la venta `pendiente` y retiene el stock 25 min **antes** de cobrar; el pago se confirma con `POST /pagos/{id}/confirmar` o el webhook. Si se corta la red tras el cobro, la venta queda pendiente y la retención caduca. |
| Reembolsos con Stripe | `StripeService` no tiene reembolso. |
| Avisos al cliente | No hay tabla ni pantalla. |

---

## 1. Decisiones

| ID | Decisión |
| :--- | :--- |
| **S1** | **Qué se hace sin conexión (RN33):** el cliente consulta el catálogo descargado y registra **reservas**; en el **móvil** se conserva además la **compra interrumpida**. La caja (CU16/CU17) y los cambios (CU18) exigen conexión. Si la empresa tiene `operacion_offline_habilitada = false`, el dispositivo se registra pero la app no deja reservar sin conexión (CU14 A5); lo ya pendiente se sigue sincronizando (CU11 A2). |
| **S2** | **Dispositivo:** la app genera un UUID la primera vez y lo conserva; el servidor lo registra **por empresa** (`dispositivos` es de empresa, con RLS) asociado al cliente y a su plataforma (`pwa`/`flutter`). Volver a registrarlo lo reutiliza (CU14 A1). El código corto del dispositivo son los 4 primeros caracteres hexadecimales del UUID en mayúsculas. |
| **S3** | **Código provisional (RN34):** `PROV-<código corto>-<correlativo de 6 dígitos>`, con el correlativo local del dispositivo. Al confirmarse, la reserva recibe su código definitivo de siempre (`RES-…`) y conserva el provisional en `reservas.codigo_provisional`. |
| **S4** | **Descarga del catálogo (CU14):** un paquete completo de la empresa: productos activos con variantes y precios, categorías, tallas, colores, promociones vigentes, sucursales activas y existencias por sucursal, con `generado_en`. Con `modo=indispensable` (A3) omite descripciones, promociones y colecciones. La app solo reemplaza lo guardado si la descarga termina (A2). Cada descarga deja `sync_log` y `dispositivos.ultima_descarga_en`. |
| **S5** | **Sincronización (CU19):** un lote de operaciones, `POST /sin-conexion/sincronizar`. Cada operación se procesa en su **propio punto de guardado**: una que falla no tumba las demás. Estados en el servidor: `confirmada`, `rechazada` o `en_conflicto`; `registrada_localmente` y `enviada` solo existen en el dispositivo (RN36). |
| **S6** | **Idempotencia (RN35):** `UNIQUE (id_tenant, uuid_operacion)`. Si el UUID ya existe, el servidor devuelve el **resultado guardado** sin volver a ejecutar nada (A2). Dos envíos simultáneos del mismo UUID: el segundo espera al primero por la clave única y devuelve su resultado. |
| **S7** | **Validación al sincronizar (RN39, RN41)**, en este orden: suscripción vigente y plan con reservas (CU12); antigüedad ≤ `dias_antiguedad_offline` contada desde `registrada_en` del dispositivo (con margen de 5 min de reloj); sucursal activa; productos y variantes activos; stock con `SELECT … FOR UPDATE` (ERR-04: nunca negativo). |
| **S8** | **Resultado de una reserva:** todo bien → se crea con el flujo de CU15 y queda `confirmada`. **Sin stock → la reserva no se crea, la operación queda `rechazada` con motivo `STOCK_INSUFICIENTE` y el cliente recibe un aviso** (CU15 A2, RN40: «se cancela»; no hay nada que reembolsar, así que **no** es un conflicto de CU20). Cualquier otra regla incumplida → `rechazada` con su motivo (A4). |
| **S9** | **Resultado de una compra interrumpida (móvil):** la operación lleva `id_venta` e `id_pago` (nunca datos de tarjeta). El servidor verifica el PaymentIntent con Stripe (**RN38: el cobro no basta**) y reutiliza la confirmación de pago existente. Si la venta ya se confirmó (webhook o un envío anterior) → `confirmada` con el resultado anterior. Si la retención caducó, vuelve a tomar stock con `FOR UPDATE`; si ya no hay, o falla otra regla de S7, → **`en_conflicto`** y se crea un conflicto de CU20 con reembolso pendiente. **Una compra cobrada nunca queda `rechazada`**: el dinero se devuelve por CU20. Un PaymentIntent no aprobado → `rechazada` (no hubo cobro). |
| **S10** | **Conflictos (CU20, RN40):** tipos `stock_insuficiente`, `precio_modificado`, `producto_inactivo`, `sucursal_inactiva` y `suscripcion_no_vigente`, con el dato que no coincide (esperado y encontrado). Estados: `pendiente` → (aceptar reembolso) `reembolso_pendiente` → (cierre de mes) `resuelto`. Al aceptar: la venta pasa a `anulada`, **el inventario no se toca** (la compra nunca se confirmó) y el cliente recibe el aviso «Recibirá su reembolso al finalizar el mes o en 15 días hábiles». Si dos usuarios aceptan a la vez, el segundo recibe 409 `CONFLICTO_YA_RESUELTO` (A3). |
| **S11** | **Cierre de mes (decisión del usuario):** botón «Procesar reembolsos del cierre» en `/admin/conflictos`, solo para el **administrador**. Se habilita el **último día del mes** (hora de Bolivia). Fuera de ese día, el administrador puede forzarlo con una confirmación explícita («cierre anticipado de prueba»), que queda en la bitácora como tal. Reembolsa con Stripe (`refunds`, simulador sin clave) cada conflicto `reembolso_pendiente`. El pago pasa a `reembolsado` y el conflicto a `resuelto`; si Stripe falla, el conflicto sigue pendiente con el motivo y el número de intento (A1). El cliente ve el nuevo estado en su dispositivo al sincronizar. |
| **S12** | **Quién ve los conflictos:** administrador, todos los de su empresa; encargado, solo los de sus sucursales autorizadas (`SucursalesEmpleadoServicio`, A2). El cajero, ninguno. Aviso dentro de la web (A4): contador de conflictos pendientes en la tarjeta del panel. |
| **S13** | **Avisos al cliente (decisión del usuario):** tabla `avisos_cliente` por empresa. La app los descarga al sincronizar y al abrirse, y los muestra en una bandeja con contador (Perfil). Sin Firebase: no llegan con la app cerrada. Tipos: `reserva_cancelada`, `reembolso_aceptado` y `reembolso_procesado`. |
| **S14** | **Registro de sincronización (RN43):** `sync_log` guarda dispositivo, tipo (`descarga`/`sincronizacion`), inicio, fin, resultado, conteos y un mensaje. `operaciones_sync.datos` guarda la operación **saneada**: sin tokens, contraseñas, `client_secret` ni datos de tarjeta. |
| **S15** | **CU15 en línea:** cada reserva guarda **`vence_en = creado_en + horas_vencimiento_reserva`**, con el valor vigente al crearla (CU11 C7, RN25). Sustituye la regla del Parcial 1 (cita + 2 h). Al vencer pasa a `vencida` y libera sus unidades, de forma perezosa al consultarla, como hoy. Las reservas ya existentes se rellenan con `creado_en + 24 h` y, si ya vencieron, siguen sus reglas de siempre hasta su atención o cancelación. Sin stock en línea (A3): 409 con las sucursales que sí tienen las unidades. Plan sin reservas o suscripción vencida (A4): 403 `FUNCIONALIDAD_NO_INCLUIDA` o `SUSCRIPCION_NO_VIGENTE`. |
| **S16** | **CU16/CU17 web:** la caja muestra «Sin conexión» y deshabilita registrar y cobrar mientras `navigator.onLine` sea falso (A4 de ambos). El servidor no cambia. |
| **S17** | **Dependencias nuevas** (*Ask First* de las constituciones):<ul><li>web: `@angular/service-worker` (misma versión que Angular) e `idb` (envoltorio de IndexedDB, ~1 KB);</li><li>móvil: `sqflite`, `path_provider`, `connectivity_plus` y `uuid`.</li></ul> |
| **S18** | **La PWA no cachea la API:** el service worker guarda solo la aplicación y sus recursos (RF16). Los datos sin conexión salen de IndexedDB, que escribe la propia app. Así no se sirven nunca respuestas de otra empresa o de otra sesión. |

---

## 2. Base de datos — migración `0020_sin_conexion` (`down_revision = "0019"`)

Todas son tablas de empresa: `id_tenant NOT NULL` con el valor por defecto del contexto,
`UNIQUE (id_tenant, pk)`, FK compuestas y la política `aislamiento_tenant`.

| Tabla | Columnas principales |
| :--- | :--- |
| `dispositivos` | `id_dispositivo`, `identificador UUID`, `id_cliente` (→ `cliente_tenant`), `plataforma` (`pwa`/`flutter`), `codigo_corto CHAR(4)`, `registrado_en`, `ultima_descarga_en`, `ultima_sincronizacion_en`. `UNIQUE (id_tenant, identificador)`. |
| `operaciones_sync` | `id_operacion_sync`, `uuid_operacion UUID`, `id_dispositivo`, `id_sucursal`, `tipo` (`reserva`/`compra_interrumpida`), `estado` (`confirmada`/`rechazada`/`en_conflicto`), `codigo_provisional`, `registrada_en` (reloj del dispositivo), `recibida_en`, `datos JSONB` (saneados), `resultado JSONB`, `motivo`, `id_reserva`, `id_venta`. `UNIQUE (id_tenant, uuid_operacion)`. |
| `conflictos_sync` | `id_conflicto`, `id_operacion_sync`, `id_venta`, `id_pago`, `id_sucursal`, `tipo`, `detalle JSONB`, `estado` (`pendiente`/`reembolso_pendiente`/`resuelto`), `aceptado_por`, `aceptado_en`, `resuelto_en`, `referencia_reembolso`, `intentos_reembolso`, `ultimo_error`. |
| `sync_log` | `id_sync_log`, `id_dispositivo`, `tipo` (`descarga`/`sincronizacion`), `iniciado_en`, `finalizado_en`, `resultado` (`ok`/`parcial`/`error`), `enviadas`, `confirmadas`, `rechazadas`, `en_conflicto`, `mensaje`. |
| `avisos_cliente` | `id_aviso`, `id_cliente` (→ `cliente_tenant`), `tipo`, `titulo`, `mensaje`, `id_reserva`, `id_venta`, `creado_en`, `leido_en`. |
| `reservas` (cambio) | `vence_en TIMESTAMPTZ` (relleno `creado_en + 24 h`, después `NOT NULL`) y `codigo_provisional VARCHAR(24)`. |

Los estados y tipos van como `VARCHAR` con `CHECK`, no como nuevos `ENUM` de PostgreSQL. Un
`ENUM` no admite quitar valores en un `downgrade`.

---

## 3. Contratos (prefijo `/api/v1`)

| Método y ruta | Quién | Comportamiento |
| :--- | :--- | :--- |
| `POST /sin-conexion/dispositivos` | Cliente (cabecera `X-Tenant`) | Registra o reutiliza el dispositivo `{identificador, plataforma}`. Devuelve `codigo_corto`, `operacion_offline_habilitada`, `dias_antiguedad_offline` y `ultima_descarga_en`. |
| `GET /sin-conexion/catalogo?dispositivo=&modo=completo\|indispensable` | Cliente | Paquete de S4 con `generado_en`; registra la descarga. |
| `POST /sin-conexion/sincronizar` | Cliente | `{dispositivo, operaciones: [{uuid, tipo, id_sucursal, registrada_en, codigo_provisional, datos}]}` → un resultado por operación: `{uuid, estado, motivo?, codigo_reserva?, id_venta?, id_conflicto?}`. Máx. 50 operaciones por lote. |
| `GET /sin-conexion/operaciones?dispositivo=` | Cliente | Estado actual de las operaciones del dispositivo (para ver la resolución de CU20). |
| `GET /avisos` · `POST /avisos/{id}/leido` | Cliente | Bandeja de S13. |
| `GET /conflictos-sync?estado=` · `GET /conflictos-sync/{id}` | Administrador, encargado | Lista y detalle de S10 y S12: compra, pago y dato que no coincide. |
| `GET /conflictos-sync/resumen` | Administrador, encargado | Pendientes por estado, para el contador del panel. |
| `POST /conflictos-sync/{id}/aceptar-reembolso` | Administrador, encargado | S10. 409 `CONFLICTO_YA_RESUELTO`. |
| `POST /conflictos-sync/procesar-cierre` | Administrador | S11. `{forzar: bool}`. Fuera del último día sin `forzar` → 409 `CIERRE_NO_DISPONIBLE`. Devuelve los conflictos procesados, reembolsados y fallidos. |
| `POST /reservas` (cambio) | Cliente | S15: `vence_en`; 409 `STOCK_INSUFICIENTE` con `alternativas`. |

Bitácora: `DISPOSITIVO_REGISTRADO`, `SINCRONIZACION`, `CONFLICTO_REGISTRADO`,
`REEMBOLSO_ACEPTADO`, `CIERRE_REEMBOLSOS` (con `forzado`) y `REEMBOLSO_FALLIDO`.

---

## 4. Web (PWA y CU20)

- **PWA (RF16):** `@angular/service-worker` con `ngsw-config.json` (solo la app y sus recursos,
  S18), manifiesto con los iconos de la marca e instalación. Hay que comprobar que `vercel.json`
  sirve `ngsw-worker.js` y `ngsw.json` sin reescribirlos a `index.html`.
- **IndexedDB:** catálogo por empresa, operaciones pendientes, correlativo local y fecha de la
  última descarga. Las claves llevan el código de la empresa: una tienda no ve lo de otra en el
  mismo navegador. Al cerrar sesión se borra el catálogo, pero **nunca las operaciones
  pendientes** (RNF03, RN37).
- **Estado sin conexión (RNF15):** banda fija en el portal con «Sin conexión», el número de
  pendientes y «Datos del dd/mm/aaaa hh:mm» (RN42).
- **Catálogo, búsqueda y detalle** leen de IndexedDB cuando no hay red. Lo que exige servidor
  (vestidor, asistente, carrito y pago) se muestra deshabilitado con su motivo.
- **Reservar sin conexión:** el mismo formulario guarda la reserva con su código `PROV-…` y el
  estado «registrada localmente».
- **Sincronización:** hoja `/{codigo}/sincronizacion` con las operaciones y su estado y el botón
  «Sincronizar». Se lanza sola al volver la red y al entrar en la tienda. Reintentos con espera
  creciente (A1). Si la sesión expiró, pide iniciar sesión y conserva todo (A5).
- **Bandeja de avisos** en Perfil, con contador.
- **CU20:** `/admin/conflictos` (`roleGuard`: administrador y encargado), con lista, detalle,
  aceptar reembolso y el botón de cierre (solo el administrador, S11). Tarjeta en el panel con el
  contador de pendientes.
- **CU16/CU17:** S16 en `/admin/pos`.

## 5. Móvil (SQLite)

- **SQLite** (`sqflite`): las mismas tablas locales que IndexedDB, más las compras interrumpidas.
  Toda escritura local va en una transacción. La base sobrevive a reinicios (RNF03).
- **Conectividad** (`connectivity_plus`) y comprobación real contra `/health` antes de sincronizar.
- **Catálogo, búsqueda y detalle** leen de SQLite sin red, con el mismo aviso de datos
  desactualizados.
- **Reservar sin conexión** desde el detalle de producto, con código `PROV-…`.
- **Compra interrumpida:** si `POST /pagos/{id}/confirmar` falla por la red **después** de que
  Stripe confirmó el cobro, la app guarda `{id_venta, id_pago}` como operación pendiente y lo
  dice: «Tu pago se registró; confirmaremos la compra al recuperar la conexión».
- **Pantalla «Sincronización»** (hoja con `BackButton`) y **bandeja de avisos** en Perfil.
- **Todo datasource nuevo usa `ClienteHttpApi()`** (cabecera `X-Tenant`).

## 6. Pruebas

- **Unitarias del backend:**
  - idempotencia (mismo UUID, mismo resultado, sin duplicados);
  - cada regla de S7;
  - reserva sin stock (rechazada con aviso, sin conflicto);
  - compra interrumpida confirmada, ya confirmada, en conflicto y no aprobada;
  - aceptar reembolso (venta anulada, inventario intacto, aviso);
  - cierre: fuera de fecha, forzado, Stripe fallido;
  - visibilidad del encargado;
  - `vence_en` con el parámetro vigente;
  - saneado de `datos`.
- **Integración** (`pruebas-multitenant`):
  - aislamiento de las 5 tablas nuevas entre empresas;
  - dos sincronizaciones concurrentes de la última unidad: una confirma y la otra no deja stock negativo (ERR-04, PI-13);
  - el mismo UUID enviado dos veces a la vez;
  - un dispositivo de una empresa que envía una sucursal de otra (PI-14).
- **Web:**
  - la cola de IndexedDB sobrevive a recargar;
  - reintento tras un fallo;
  - código `PROV`;
  - lectura del catálogo sin red;
  - guardas de `/admin/conflictos`;
  - caja bloqueada sin red.
- **Móvil:**
  - DTO con `fromJson` sobre payloads literales del backend;
  - repositorio SQLite con `sqflite_common_ffi` en pruebas;
  - cola y estados.
- **Manual en un dispositivo físico:** modo avión, reservar, reiniciar la app, reconectar y sincronizar. Además, la compra interrumpida cortando la red justo después del cobro.

## 7. Fuera de alcance

- Caja en el móvil (CU16/CU17 Flutter): cambio siguiente.
- Push real (Firebase / Web Push): la bandeja cubre el contenido (decisión del usuario).
- Compras sin conexión en la web: el documento solo las prevé en el móvil.
- RN21 (una fila de inventario por variante y sucursal, sin temporada): este cambio sigue con la
  clave real `(id_variante, id_sucursal, id_temporada)`; la unificación es otro cambio.
- Sincronización incremental del catálogo («solo lo que cambió»): cada descarga es completa; el
  catálogo de una empresa es pequeño.
