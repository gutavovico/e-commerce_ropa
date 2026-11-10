# Requisitos · P2-CU14, CU15, CU19 y CU20 — Operación sin conexión   Nivel: 3   Estado: ✅ cerrada y en producción (2026-11-10)

**ID del cambio:** `P2-CU14-CU15-CU19-CU20-sin-conexion`
**Aprobado por:** Gustavo (usuario) **Fecha:** 2026-11-09
**Fase SDD:** 1 de 4 (Requisitos). Diseño en `plan.md`, tareas en `tasks.md`, puertas en `checkpoint.md`.
**Fuente:** `SI2-Parcial2.md` CU14, CU15, CU16 A4, CU17 A4, CU19 y CU20; RN25, RN33–RN43, RNF03, RNF15.
**Decisiones del usuario (2026-11-09):** D1 avisos en una bandeja dentro de la app, sin Firebase ·
D2 reembolsos del cierre de mes con un botón del administrador · D3 caja móvil (CU16/CU17 Flutter)
en un cambio aparte.
**Depende de:** `P2-CU13-CU12-fundacion-multitenant`, `P2-CU11-parametros-empresa` y de que Tony
aplique `0017`–`0019` en producción antes de la migración de este cambio.
**Nivel 3 porque** toca inventario, reservas, pagos y reembolsos, migración que altera datos y tres stacks.

---

## Propósito

Que el cliente pueda consultar el catálogo y reservar prendas sin internet, en la PWA y en la app
móvil, y que esas operaciones lleguen al servidor sin duplicarse cuando vuelve la conexión. Lo que
el servidor no pueda aceptar se cancela (reservas) o se reembolsa (compras ya cobradas), con aviso
al cliente y revisión del encargado o el administrador.

## Actores y precondiciones

| Actor | Precondiciones |
| :--- | :--- |
| Cliente | Sesión iniciada; registrado en la empresa (`cliente_tenant`); PWA o app Flutter. |
| Encargado de sucursal | Sesión iniciada; ve solo sus sucursales autorizadas (RN07). |
| Administrador | Sesión iniciada; ve toda su empresa. |
| Stripe (modo de prueba) | Verifica cobros y procesa reembolsos; simulador determinista sin clave. |

## Hallazgos que condicionan los requisitos (código al 2026-11-09)

- No existen las tablas de dispositivos, operaciones, conflictos, registro de sincronización ni avisos.
- No hay PWA (sin service worker ni manifiesto) ni SQLite en el móvil.
- La reserva en línea existe (`POST /api/v1/reservas`), pero vence **2 h después de la cita**, no a
  las horas de la empresa (RN25), y no guarda su vencimiento.
- `StripeService` no sabe reembolsar.

---

## Requisitos (EARS)

### CU14 · Descargar catálogo y registrar dispositivo

- **AC-14.1** Cuando el cliente abre la app por primera vez en una empresa, el sistema deberá
  registrar el dispositivo con su identificador (UUID generado en el dispositivo) y su plataforma
  (`pwa`/`flutter`), asociado al cliente y a esa empresa, y devolver su código corto de 4 caracteres.
- **AC-14.2** Si el dispositivo ya está registrado en esa empresa, entonces el sistema deberá
  reutilizarlo sin crear otro (A1).
- **AC-14.3** Cuando el cliente pide la descarga, el sistema deberá entregar los productos activos
  con variantes y precios, categorías, tallas, colores, promociones vigentes, sucursales activas y
  existencias por sucursal **solo de la empresa de la cabecera**, con la fecha `generado_en`.
- **AC-14.4** Cuando la descarga termina, el sistema deberá guardar la fecha de la última descarga del
  dispositivo y una fila en el registro de sincronización.
- **AC-14.5** Si la descarga se interrumpe, entonces la app deberá conservar los datos anteriores sin
  reemplazarlos (A2).
- **AC-14.6** Si el dispositivo no tiene espacio, entonces la app deberá informarlo y pedir la
  descarga `indispensable`, sin descripciones, promociones ni colecciones (A3).
- **AC-14.7** Mientras no haya conexión, la app deberá mostrar el catálogo descargado con el aviso
  «Puede estar desactualizado · Datos del dd/mm/aaaa hh:mm» (A4, RN42, RNF15).
- **AC-14.8** Donde la empresa tenga `operacion_offline_habilitada = false`, el sistema deberá
  registrar el dispositivo y la app no deberá permitir reservar sin conexión (A5).

### CU15 · Reservar varias prendas

- **AC-15.1** Cuando el cliente confirma una reserva en línea, el sistema deberá validar plan y
  suscripción (CU12) y existencias en la sucursal, crearla `pendiente`, apartar las unidades con su
  movimiento de inventario y fijar `vence_en = creado_en + horas_vencimiento_reserva` con el valor
  vigente en ese momento (RN25, CU11 C7).
- **AC-15.2** Si una línea supera las existencias en línea, entonces el sistema deberá responder 409
  `STOCK_INSUFICIENTE` con el máximo disponible y las sucursales que sí tienen las unidades (A3).
- **AC-15.3** Si el plan no incluye reservas o la suscripción no está vigente, entonces el sistema
  deberá responder 403 `FUNCIONALIDAD_NO_INCLUIDA` o `SUSCRIPCION_NO_VIGENTE` (A4).
- **AC-15.4** Cuando pasa `vence_en` sin atenderse, la reserva deberá pasar a `vencida` y liberar sus
  unidades con su movimiento (A5); se comprueba de forma perezosa al consultarla, como hoy.
- **AC-15.5** Mientras no haya conexión y la empresa lo permita, la app deberá guardar la reserva en el
  dispositivo con un identificador único, el estado «registrada localmente» y el código provisional
  `PROV-<código corto>-<correlativo de 6 dígitos>` (A1, RN34).

### CU19 · Sincronizar operaciones pendientes

- **AC-19.1** Cuando vuelve la conexión, al entrar en la tienda o cuando el cliente pulsa
  «Sincronizar», la app deberá enviar las operaciones pendientes y marcarlas «enviada».
- **AC-19.2** Cuando el servidor recibe una operación, deberá procesarla en este orden: empresa de la
  cabecera (CU13), suscripción vigente y plan con reservas (CU12), antigüedad ≤
  `dias_antiguedad_offline` (RN41), sucursal activa, producto y variante activos, y stock (RN39).
- **AC-19.3** Si una operación ya se había recibido (mismo identificador en la empresa), entonces el
  servidor deberá devolver el resultado guardado sin ejecutar nada de nuevo (A2, RN35).
- **AC-19.4** Cuando una reserva pasa todas las reglas, el servidor deberá crearla con el flujo de
  AC-15.1, asignarle su código definitivo y conservar el provisional; la operación queda `confirmada`.
- **AC-19.5** Si una reserva no tiene stock, entonces el servidor deberá rechazarla con el motivo
  `STOCK_INSUFICIENTE` y dejar un aviso al cliente en su bandeja (A3, RN40; D1 sustituye la
  notificación push del documento).
- **AC-19.6** Si la suscripción venció o la operación supera la antigüedad máxima, entonces el servidor
  deberá rechazarla e informar el motivo (A4).
- **AC-19.7** Cuando llega una compra interrumpida (solo móvil), el servidor deberá verificar el cobro
  con Stripe (RN38) y confirmar la compra con el mismo flujo del pago en línea.
- **AC-19.8** Si una compra cobrada no puede confirmarse por cualquier regla de AC-19.2, entonces el
  servidor deberá dejarla `en_conflicto` y crear un conflicto para CU20. **Una compra cobrada nunca
  queda `rechazada`.**
- **AC-19.9** Si el pago de una compra interrumpida no fue aprobado por Stripe, entonces el servidor
  deberá rechazar la operación (no hubo cobro).
- **AC-19.10** Si falla la red o el servidor no responde, entonces la app deberá conservar las
  operaciones y reintentar con espera creciente (A1, RN37).
- **AC-19.11** Si la sesión expiró, entonces la app deberá pedir iniciar sesión y conservar las
  operaciones (A5).
- **AC-19.12** El sistema deberá dejar en el registro de sincronización cada envío con conteos y
  resultado, sin tokens, contraseñas ni datos de pago (RN43).
- **AC-19.13** La app deberá conservar cada operación tras enviarla y mostrar su estado final
  (`confirmada`, `rechazada` o `en_conflicto`) (RN36, RN37, RNF03).

### CU20 · Resolver conflictos de sincronización

- **AC-20.1** Cuando el encargado o el administrador entra en «Conflictos», el sistema deberá listar
  los pendientes con su tipo: stock insuficiente, precio modificado, producto inactivo, sucursal
  inactiva o suscripción no vigente.
- **AC-20.2** Cuando abre un conflicto, el sistema deberá mostrar la compra original, su pago y el dato
  que no coincide (esperado y encontrado).
- **AC-20.3** Cuando acepta el reembolso, el sistema deberá anular la compra **sin tocar el
  inventario**, dejar el reembolso pendiente para el cierre del mes, avisar al cliente en su bandeja
  («Recibirá su reembolso al finalizar el mes o en 15 días hábiles») y registrarlo en la bitácora.
- **AC-20.4** Cuando el administrador pulsa «Procesar reembolsos del cierre» el último día del mes
  (hora de Bolivia), el sistema deberá reembolsar con Stripe cada conflicto pendiente de reembolso,
  marcar el pago `reembolsado`, el conflicto `resuelto` y avisar al cliente (D2).
- **AC-20.5** Si el administrador pulsa el botón otro día, entonces el sistema deberá pedir una
  confirmación explícita de «cierre anticipado de prueba» y registrarlo así en la bitácora; sin esa
  confirmación responde 409 `CIERRE_NO_DISPONIBLE`.
- **AC-20.6** Si el reembolso falla en Stripe, entonces el conflicto deberá seguir pendiente con el
  motivo y el número de intento, para el siguiente cierre (A1).
- **AC-20.7** Mientras el usuario sea encargado, el sistema no deberá mostrarle ni dejarle tocar los
  conflictos de sucursales no autorizadas (A2). El cajero no ve ninguno.
- **AC-20.8** Si el conflicto ya lo resolvió otro usuario, entonces el sistema deberá responder 409
  `CONFLICTO_YA_RESUELTO` y la web refrescar la lista (A3).
- **AC-20.9** El panel deberá mostrar el número de conflictos pendientes, sin push (A4).

### Caja web (CU16 A4 y CU17 A4)

- **AC-16.1** Mientras el navegador esté sin conexión, la caja `/admin/pos` deberá mostrar «Sin
  conexión» y no permitir registrar ni cobrar.

### Avisos al cliente (D1)

- **AC-AV.1** El sistema deberá guardar cada aviso al cliente (reserva cancelada, reembolso aceptado,
  reembolso procesado) en su empresa; la app los mostrará en una bandeja en Perfil con contador de no
  leídos y permitirá marcarlos como leídos.

### Transversales

- **AC-T.1** El sistema deberá aislar por empresa todas las tablas nuevas (RLS y `id_tenant`); un
  dispositivo de una empresa no podrá operar sobre sucursales ni productos de otra (CU13).
- **AC-T.2** Si dos operaciones compiten por la última unidad, entonces solo una deberá llevársela y el
  stock no deberá quedar negativo (ERR-04).
- **AC-T.3** El almacenamiento local deberá separar los datos por empresa y conservar las operaciones
  pendientes tras cerrar sesión o reiniciar (RNF03).
- **AC-T.4** El service worker no deberá cachear respuestas de la API: los datos sin conexión salen solo
  del almacenamiento local que escribe la app.

---

## Casos de error

| Caso | Respuesta |
| :--- | :--- |
| Cliente no registrado en la empresa | 403 `CLIENTE_NO_REGISTRADO` |
| Dispositivo desconocido para la empresa | 404 `DISPOSITIVO_NO_ENCONTRADO` |
| Lote con más de 50 operaciones | 422 |
| Stock insuficiente en línea | 409 `STOCK_INSUFICIENTE` + `alternativas` |
| Plan sin reservas / suscripción vencida | 403 `FUNCIONALIDAD_NO_INCLUIDA` / `SUSCRIPCION_NO_VIGENTE` |
| Conflicto ya resuelto | 409 `CONFLICTO_YA_RESUELTO` |
| Cierre fuera del último día sin forzar | 409 `CIERRE_NO_DISPONIBLE` |
| Encargado sobre sucursal no autorizada / cajero | 404 (no existe para él) / 403 |
| Reglas de una operación sincronizada | No es un error HTTP: el lote responde 200 y cada operación lleva `estado` y `motivo` |

## Diferencias con el documento (delta)

- **MODIFIED** CU15 A2, CU19 A3 y CU20 paso 4: «notificación push» → aviso en la bandeja de la app (D1).
- **MODIFIED** RN25 en el código: la reserva vencía 2 h después de la cita (Parcial 1) → vence a
  `creado_en + horas_vencimiento_reserva`. Las reservas existentes reciben `creado_en + 24 h`.
- **ADDED** cierre anticipado de prueba (AC-20.5), para poder demostrarlo cualquier día.

### Ajustes de la implementación del backend (2026-11-09, a revisar en la puerta 4a)

- **ADDED AC-15.6** Si la hora de la cita es posterior a `vence_en`, entonces el sistema deberá
  rechazar la reserva con 400 `CITA_FUERA_DE_PLAZO` sin apartar stock. Con 24 h por defecto, una cita
  a dos días vencería antes de la visita; la web y el móvil deberán limitar el selector de fecha.
- **ADDED AC-14.9** Si el plan no incluye `operacion_offline` (RN16), entonces registrar el dispositivo
  y descargar el catálogo deberán responder 403 `FUNCIONALIDAD_NO_INCLUIDA`. Sincronizar lo ya
  pendiente sigue permitido (CU11 A2).
- **ADDED** estado de respuesta `reintentar` (no se guarda): Stripe no respondió al verificar una
  compra interrumpida; la app conserva la operación y la reenvía (A1).
- **ADDED** tipo de conflicto `antiguedad_excedida`: una compra **cobrada** que supera la antigüedad
  máxima también se reembolsa. Su antigüedad se mide desde `ventas.fecha_venta` (reloj del servidor).
- **ADDED** un solo conflicto por compra (`UNIQUE (id_tenant, id_venta)`): otro envío con un UUID
  distinto para la misma compra responde `en_conflicto` con el conflicto existente.
- **MODIFIED** AC-15.2: el código del 409 se mantiene `STOCK_INSUFICIENTE_RESERVA` (lo usan la web y
  el móvil); se añaden `disponible` y `alternativas` al cuerpo.
- **NO IMPLEMENTADO** `precio_modificado` como causa: el precio de una compra se congela en el
  checkout (invariante del dominio) y una reserva no tiene precio. El tipo existe en la tabla.

### Ajustes de la implementación de la web (2026-11-09, a revisar en la puerta 4b)

- **MODIFIED** AC-14.7 (plan §4): el catálogo sin conexión es una hoja propia del portal,
  `/{codigo}/sin-conexion` (búsqueda, detalle con existencias por sucursal y reserva), en lugar de
  hacer que las páginas en línea de catálogo, búsqueda y detalle lean IndexedDB. Así no se toca el
  flujo en línea. La banda «Sin conexión» enlaza con ella.
- **ADDED** sin red, el portal de una tienda ya visitada se abre con los datos públicos guardados de
  la última visita (`tenantGuard`); sin visita previa vuelve al directorio.
- **ADDED** el service worker guarda también Tailwind (CDN) y las fuentes de Google: sin ellos la
  aplicación se abría sin estilos. Siguen fuera la API y cualquier dato (S18).
- **FIXED** el modal de reserva en línea enviaba la cita siempre para «mañana a las 11:30», con
  franjas fijas («VIERNES 12:00H») que no se usaban. Ahora ofrece horas dentro del vencimiento
  (AC-15.6) y el 409 muestra las sucursales alternativas (AC-15.2).
- Iconos de la PWA neutros (una percha), sin marca: la misma aplicación sirve a varias tiendas.
- **ADDED** la web solo llama a la API sin conexión cuando sabe que el cliente está registrado en la
  tienda; si no lo está, la hoja «Sincronización» lo dice en lugar de un error de red (hallado al
  probar contra `pruebas-multitenant`).

### Ajustes de la implementación móvil (2026-11-09, a revisar en la puerta 4c)

- **MODIFIED** AC-14.7: como en la web, el catálogo sin conexión es una hoja propia
  (`PantallaCatalogoSinConexion`, con `BackButton`) y no se tocan las pantallas en línea. La banda de
  estado va encima de la barra de navegación del hub, para no tapar la barra de estado del sistema.
- **MODIFIED** dependencias: no se usa `path_provider` (`sqflite` ya da la ruta con
  `getDatabasesPath`). Quedan `sqflite`, `connectivity_plus` y `uuid`, y `sqflite_common_ffi` en pruebas.
- **ADDED** el id del cliente se lee del `sub` del JWT que ya recibe el hub (sin petición extra); solo
  para separar los datos locales por cliente, la firma la comprueba el servidor.
- **ADDED** compra interrumpida: si `confirmarPago` falla por la red después de abrir el cobro, el
  pago queda en el estado `PagoPendienteDeSincronizar` y se guarda `{id_venta, id_pago}`. Un rechazo
  402 no se guarda (no hubo cobro).
- **FIXED** la reserva en línea del detalle de producto enviaba la cita siempre para «ahora + 1 día»
  con franjas fijas; ahora usa las mismas franjas dentro del vencimiento que la web, y el 409 muestra
  las sucursales alternativas.

## Fuera de alcance

- Caja en el móvil (CU16/CU17 Flutter): cambio siguiente (D3).
- Push real (Firebase o Web Push) (D1).
- Compras sin conexión en la web: el documento solo prevé la compra interrumpida en el móvil.
- RN21 (inventario sin temporada): se sigue con la clave real `(id_variante, id_sucursal, id_temporada)`.
- Descarga incremental del catálogo: cada descarga es completa.

## Preguntas abiertas

Ninguna. Las tres decisiones pendientes se cerraron el 2026-11-09 (D1–D3).
