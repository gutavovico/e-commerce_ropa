# Diseño · P2-CU14, CU15, CU19 y CU20 — Operación sin conexión
**Requisitos:** `spec.md` (pendiente de aprobación) · **Fase SDD:** 2 de 4 (Diseño) · **Estado:** borrador

---

## 1. Enfoque

- **Un paquete nuevo de backend, `sincronizacion`**, con `cu14_dispositivo_catalogo`,
  `cu19_sincronizar`, `cu20_conflictos` y `avisos_cliente`. CU15 sigue en
  `reservas/cu12_reservar_prendas` (ya existe): se amplía, no se duplica.
- **La sincronización reutiliza los servicios en línea.** Una reserva sincronizada pasa por el mismo
  `ReservaServicio` que la reserva en línea; una compra interrumpida, por la misma confirmación de
  pago de `cu16_realizar_pago`. Así no hay dos implementaciones de las reglas de stock y dinero.
- **Lote con un punto de guardado por operación** (`begin_nested`): una operación que falla no tumba
  las demás ni el registro del lote.
- **Estados y tipos como `VARCHAR` con `CHECK`**, no `ENUM`: un `ENUM` no admite quitar valores en el
  `downgrade`.
- **Web:** PWA con `@angular/service-worker` (solo la aplicación) e IndexedDB (`idb`) para datos.
  **Móvil:** `sqflite`.

**Descartado:**
- Cachear la API en el service worker. Mezclaría empresas y sesiones; los datos salen de IndexedDB.
- Un proceso programado para el cierre de mes. Render no garantiza cron en el plan actual; el usuario
  eligió un botón (D2).
- Firebase para avisos (D1).

## 2. Contrato de API (prefijo `/api/v1`)

| Método y ruta | Rol | Entrada | Salida | Códigos |
| :--- | :--- | :--- | :--- | :--- |
| `POST /sin-conexion/dispositivos` | cliente + `X-Tenant` | `{identificador: uuid, plataforma: "pwa"\|"flutter"}` | `{id_dispositivo, codigo_corto, operacion_offline_habilitada, dias_antiguedad_offline, ultima_descarga_en}` | 200 (reutilizado) · 201 · 403 |
| `GET /sin-conexion/catalogo?dispositivo=&modo=completo\|indispensable` | cliente | — | `{generado_en, productos[], categorias[], tallas[], colores[], promociones[], sucursales[], existencias[]}` | 200 · 404 |
| `POST /sin-conexion/sincronizar` | cliente | `{dispositivo, operaciones: [{uuid, tipo, id_sucursal, registrada_en, codigo_provisional, datos}]}` (máx. 50) | `{resultados: [{uuid, estado, motivo?, codigo_reserva?, id_venta?, id_conflicto?}], id_sync_log}` | 200 · 404 · 422 |
| `GET /sin-conexion/operaciones?dispositivo=` | cliente | — | estado actual de cada operación del dispositivo | 200 |
| `GET /avisos` · `POST /avisos/{id}/leido` | cliente | — | `{no_leidos, avisos[]}` | 200 · 404 |
| `GET /conflictos-sync?estado=` · `GET /conflictos-sync/{id}` | administrador, encargado | — | lista / detalle con venta, pago, `esperado` y `encontrado` | 200 · 403 · 404 |
| `GET /conflictos-sync/resumen` | administrador, encargado | — | `{pendiente, reembolso_pendiente}` | 200 |
| `POST /conflictos-sync/{id}/aceptar-reembolso` | administrador, encargado | — | conflicto actualizado | 200 · 404 · 409 `CONFLICTO_YA_RESUELTO` |
| `POST /conflictos-sync/procesar-cierre` | administrador | `{forzar: bool}` | `{procesados, reembolsados, fallidos[]}` | 200 · 409 `CIERRE_NO_DISPONIBLE` |
| `POST /reservas` (cambio) | cliente | igual que hoy | añade `vence_en` | 409 `STOCK_INSUFICIENTE` con `alternativas` |

Ejemplos (los importes, como cadena, igual que el resto de la API):

```json
// POST /sin-conexion/sincronizar
{"dispositivo": "3f9a2c1e-…", "operaciones": [
  {"uuid": "b1c2…", "tipo": "reserva", "id_sucursal": 3, "registrada_en": "2026-11-08T15:02:00-04:00",
   "codigo_provisional": "PROV-3F9A-000004",
   "datos": {"fecha_hora_atencion": "2026-11-09T11:00:00-04:00", "items": [{"id_variante": 41, "cantidad": 1}]}}]}
// 200
{"resultados": [{"uuid": "b1c2…", "estado": "confirmada", "codigo_reserva": "RES-2026-000123"}], "id_sync_log": 88}
// sin stock
{"resultados": [{"uuid": "b1c2…", "estado": "rechazada", "motivo": "STOCK_INSUFICIENTE"}], "id_sync_log": 89}
// compra interrumpida cobrada sin stock
{"resultados": [{"uuid": "c9…", "estado": "en_conflicto", "motivo": "STOCK_INSUFICIENTE", "id_venta": 501, "id_conflicto": 7}], "id_sync_log": 90}
```

## 3. Capas afectadas

| Capa | Archivos |
| :--- | :--- |
| Router | `app/modules/sincronizacion/{router.py, cu14_dispositivo_catalogo/, cu19_sincronizar/, cu20_conflictos/, avisos_cliente/}` · una línea en `app/main.py` · `reservas/cu12_reservar_prendas/router.py` (respuesta con `vence_en`) |
| Servicio | `DispositivoServicio`, `CatalogoSinConexionServicio`, `SincronizacionServicio`, `ConflictosServicio`, `AvisosServicio`. Cambios en `ReservaServicio` (`vence_en`, alternativas) y en la consulta de vencidas de `cu13_consultar_cancelar_reservas`. |
| ORM | `app/modules/sincronizacion/modelos.py` (5 tablas nuevas). `ReservaORM` (en `comercial/cu28_ventas_reservas/modelos.py`) gana `vence_en` y `codigo_provisional` donde ya vive. |
| Integración | `stripe_service.py`: `reembolsar(id_intento, monto)` con simulador determinista sin clave, sin tocar los métodos existentes. |
| Otros paquetes | Solo por su servicio: `SuscripcionServicio`, `ParametrosEmpresaServicio`, `SucursalesEmpleadoServicio`, confirmación de pago de `cu16_realizar_pago`, `registrar_evento_seguro`. |
| Web | `src/app/core/sin-conexion/` (estado de red, IndexedDB, cola, sincronizador) · `modules/sincronizacion/{cu19_sincronizacion, avisos, cu20_conflictos}` · `app.routes.ts` · `ngsw-config.json`, `manifest.webmanifest`, `angular.json`, `app.config.ts` · caja `/admin/pos` (aviso sin red). |
| Móvil | `lib/src/core/sin_conexion/` (SQLite, conectividad, cola) · `lib/src/modulos/sincronizacion/{cu19_sincronizacion, avisos}` · detalle de producto (reservar sin red) · flujo de pago (compra interrumpida) · Perfil (bandeja). |

## 4. Datos y migración `0020_sin_conexion` (`down_revision = "0019"`)

Todas son tablas de empresa: `id_tenant NOT NULL` con el valor por defecto del contexto,
`UNIQUE (id_tenant, pk)`, FK compuestas `(id_tenant, fk)` y política `aislamiento_tenant`. Permisos
para `fashionstore_app`.

| Tabla | Columnas principales | Claves |
| :--- | :--- | :--- |
| `dispositivos` | `id_dispositivo`, `identificador UUID`, `id_cliente_tenant`, `plataforma`, `codigo_corto CHAR(4)`, `registrado_en`, `ultima_descarga_en`, `ultima_sincronizacion_en` | `UNIQUE (id_tenant, identificador)` |
| `operaciones_sync` | `id_operacion_sync`, `uuid_operacion UUID`, `id_dispositivo`, `id_sucursal`, `tipo` (`reserva`/`compra_interrumpida`), `estado` (`confirmada`/`rechazada`/`en_conflicto`), `codigo_provisional`, `registrada_en`, `recibida_en`, `datos JSONB` saneado, `resultado JSONB`, `motivo`, `id_reserva`, `id_venta` | `UNIQUE (id_tenant, uuid_operacion)` |
| `conflictos_sync` | `id_conflicto`, `id_operacion_sync`, `id_venta`, `id_pago`, `id_sucursal`, `tipo`, `detalle JSONB` (`esperado`/`encontrado`), `estado` (`pendiente`/`reembolso_pendiente`/`resuelto`), `aceptado_por`, `aceptado_en`, `resuelto_en`, `referencia_reembolso`, `intentos_reembolso`, `ultimo_error` | índice `(id_tenant, estado)` |
| `sync_log` | `id_sync_log`, `id_dispositivo`, `tipo` (`descarga`/`sincronizacion`), `iniciado_en`, `finalizado_en`, `resultado` (`ok`/`parcial`/`error`), `enviadas`, `confirmadas`, `rechazadas`, `en_conflicto`, `mensaje` | — |
| `avisos_cliente` | `id_aviso`, `id_cliente_tenant`, `tipo`, `titulo`, `mensaje`, `id_reserva`, `id_venta`, `creado_en`, `leido_en` | índice `(id_tenant, id_cliente_tenant, leido_en)` |
| `reservas` (cambio) | `vence_en TIMESTAMPTZ`: se añade nula, se rellena con `creado_en + interval '24 hours'` , pasa a `NOT NULL` y lleva por defecto `now() + interval '24 hours'`: así el código anterior sigue creando reservas entre la migración y el despliegue (defecto 55). `codigo_provisional VARCHAR(24)` nula. | — |

- **Reversible:** el `downgrade` borra las 5 tablas y las 2 columnas. El relleno de `vence_en` se
  pierde, y no hace falta conservarlo.
- **Sin triggers ni vistas afectados.**
- **Ensayo:** `pruebas-multitenant` con `upgrade → downgrade → upgrade` y `test_esquema_bd`. Después,
  producción **a mano antes del push** (defecto 55), y solo cuando `0017`–`0019` ya estén aplicadas.
- Antes de crearla: avisar del número `0020` al equipo y comprobar `alembic heads`.

## 5. Reglas, transacciones y concurrencia

| Operación | Transacción y bloqueos |
| :--- | :--- |
| Registrar dispositivo | `INSERT … ON CONFLICT (id_tenant, identificador) DO NOTHING` y lectura: dos registros simultáneos del mismo UUID dan un solo dispositivo. |
| Descarga | Solo lectura más `sync_log` y `ultima_descarga_en` en la misma transacción. |
| Lote de sincronización | **Implementado:** una transacción **por operación** (en lugar de un `SAVEPOINT` por operación dentro de una sola transacción: los servicios reutilizados confirman y un `commit` dentro de un punto de guardado confirmaría todo el lote). Cada operación ejecuta su efecto e inserta su fila de `operaciones_sync` en la misma transacción y confirma. Si dos envíos del mismo UUID compiten, el segundo choca con la clave única al insertar, se deshace entero (también su reserva) y devuelve el `resultado` del primero (AC-19.3). Probado con dos conexiones reales. |
| Stock (reserva y compra) | `SELECT … FOR UPDATE` sobre `inventario_sucursal` filtrando por `(id_variante, id_sucursal, id_temporada)`, en orden creciente de `id_inventario` para no provocar interbloqueos entre lotes con varias líneas. Movimiento de inventario en la misma transacción, con el cliente como responsable. |
| Antigüedad | `registrada_en` del dispositivo contra `ahora()` de `core/tiempo.py`, con 5 min de margen por desfase de reloj. Una fecha futura de más de 5 min se rechaza (`FECHA_INVALIDA`). |
| Compra interrumpida | `SELECT … FOR UPDATE` sobre la venta. Si ya está `pagada`, se devuelve `confirmada` (el webhook llegó antes). Si sigue `pendiente`: se verifica con Stripe y se llama a la confirmación existente. Si la retención caducó, se vuelve a tomar stock (fila anterior). Si falla cualquier regla y Stripe confirmó el cobro, se crea `conflictos_sync` en el mismo punto de guardado. |
| Aceptar reembolso | `SELECT … FOR UPDATE` del conflicto; si su estado no es `pendiente` → 409 `CONFLICTO_YA_RESUELTO`. Venta `pendiente → anulada`, sin movimiento de inventario (la retención ya caducó o nunca se volvió a tomar). Aviso y bitácora en la misma transacción. |
| Cierre de mes | Un conflicto por transacción: un fallo de Stripe no deshace los demás. Antes de llamar a Stripe se toma `FOR UPDATE SKIP LOCKED`, así dos cierres simultáneos no reembolsan dos veces. Stripe recibe una `idempotency_key` = `reembolso-<id_tenant>-<id_conflicto>-<intento>`. |
| Vencimiento de reservas | Igual que hoy, perezoso al consultar, pero comparando con `vence_en`. |

**Saneado de `datos` (AC-19.12):** lista blanca de claves por tipo de operación. Nunca se guardan
`client_secret`, tokens ni datos de tarjeta; de la compra solo `id_venta` e `id_pago`.

## 6. Errores

| Excepción de dominio | HTTP | Código |
| :--- | :--- | :--- |
| `AuthorizationError` | 403 | `CLIENTE_NO_REGISTRADO`, `FUNCIONALIDAD_NO_INCLUIDA`, `SUSCRIPCION_NO_VIGENTE` |
| `NotFoundError` | 404 | `DISPOSITIVO_NO_ENCONTRADO`, `CONFLICTO_NO_ENCONTRADO` (también para el encargado sin la sucursal) |
| `ConflictError` | 409 | `STOCK_INSUFICIENTE`, `CONFLICTO_YA_RESUELTO`, `CIERRE_NO_DISPONIBLE` |
| Validación Pydantic | 422 | lote vacío o con más de 50 operaciones |

Dentro del lote, los motivos van en el resultado, no como HTTP: `STOCK_INSUFICIENTE`,
`ANTIGUEDAD_EXCEDIDA`, `FECHA_INVALIDA`, `SUSCRIPCION_NO_VIGENTE`, `FUNCIONALIDAD_NO_INCLUIDA`,
`SUCURSAL_INACTIVA`, `PRODUCTO_INACTIVO`, `PAGO_NO_APROBADO`, `DATOS_INVALIDOS`, `VENTA_NO_ENCONTRADA`,
`VENTA_AJENA`, `UUID_DUPLICADO`, `CONFLICTO_EXISTENTE` y, sin guardarse, `PASARELA_NO_DISPONIBLE`
(estado `reintentar`). Fuera del lote: 400 `CITA_FUERA_DE_PLAZO` (CU15) y 409 `DISPOSITIVO_DE_OTRO_CLIENTE`.

## 7. No funcionales

- **Seguridad:** el cliente solo ve sus dispositivos, operaciones y avisos (filtro por
  `id_cliente_tenant` además de la RLS). El encargado, solo los conflictos de
  `SucursalesEmpleadoServicio.autoriza`. Rutas web de conflictos con `roleGuard`.
- **Auditoría:** bitácora con `registrar_evento_seguro` (nunca el ORM, defecto 57):
  `DISPOSITIVO_REGISTRADO`, `SINCRONIZACION`, `CONFLICTO_REGISTRADO`, `REEMBOLSO_ACEPTADO`,
  `CIERRE_REEMBOLSOS` (con `forzado`) y `REEMBOLSO_FALLIDO`.
- **Rendimiento:** catálogo de una empresa en una sola respuesta (decenas de productos); un lote de 50
  operaciones en menos de 5 s contra Neon.
- **Hora:** «último día del mes» y la antigüedad, con `core/tiempo.py` (`America/La_Paz`).
- **Web:** comprobar que `vercel.json` sirve `ngsw-worker.js`, `ngsw.json` y el manifiesto sin
  reescribirlos a `index.html`, y que **no** se activa `cleanUrls` (defecto 59).
- **Móvil:** todo datasource nuevo con `ClienteHttpApi()`; overflow con `Expanded`/`Flexible`.

## 8. Riesgos y decisiones (Nivel 3)

| Riesgo | Decisión |
| :--- | :--- |
| `dominio.md` §5.7 — vencimiento de reservas | Perezoso al consultar, con `vence_en` guardado (AC-15.4). |
| `dominio.md` §5.8 — webhook de Stripe | La compra interrumpida comprueba si el webhook ya pagó la venta y nunca la confirma dos veces. |
| ERR-04 — última unidad concurrente | `FOR UPDATE` ordenado; prueba de integración con dos lotes simultáneos. |
| Doble envío del mismo UUID | Clave única + punto de guardado; prueba de integración concurrente. |
| Doble reembolso | Estado bajo `FOR UPDATE SKIP LOCKED` + `idempotency_key` de Stripe. |
| Reloj del dispositivo manipulado | Margen de 5 min; una fecha futura se rechaza; la antigüedad es la única regla que usa el reloj del dispositivo. |
| Fuga entre empresas en el navegador | Claves de IndexedDB con el código de la empresa; el service worker no cachea la API. |
| Cambio de regla de vencimiento | Relleno `creado_en + 24 h` en la migración; las reservas `atendida`/`cancelada` no cambian. |
| Migración encadenada a la de Tony | `0020` no se aplica en producción hasta que `0017`–`0019` lo estén. |
| Dependencias nuevas (Ask First) | Web: `@angular/service-worker` (versión de Angular) e `idb`. Móvil: `sqflite`, `path_provider`, `connectivity_plus`, `uuid`; en pruebas, `sqflite_common_ffi`. **Se aprueban con este diseño.** |

## 9. Estrategia de pruebas (AC → prueba)

| AC | Prueba |
| :--- | :--- |
| 14.1, 14.2 | Unitaria del servicio (alta y reutilización) · integración: registro concurrente del mismo UUID |
| 14.3, 14.4 | Unitaria (contenido y `modo=indispensable`) · integración: la descarga de la empresa B no trae nada de A |
| 14.5–14.8 | Web: servicio de catálogo local con IndexedDB falso · Móvil: repositorio SQLite con `sqflite_common_ffi` |
| 15.1–15.4 | Unitarias de `ReservaServicio` (`vence_en`, 409 con alternativas, 403) · integración: relleno de `vence_en` tras la migración |
| 15.5 | Web y móvil: código `PROV` y correlativo persistente |
| 19.2–19.9 | Unitarias de `SincronizacionServicio`, una por regla y por resultado; compra: confirmada, ya pagada por webhook, en conflicto, no aprobada |
| 19.3, T.2 | **Integración concurrente:** mismo UUID en dos conexiones; dos lotes por la última unidad (ninguna existencia negativa) |
| 19.10–19.13 | Web y móvil: la cola sobrevive a recargar o reiniciar; reintento; sesión expirada conserva la cola |
| 19.12 | Unitaria del saneado (no aparece `client_secret` ni tokens) |
| 20.1–20.9 | Unitarias de `ConflictosServicio` (visibilidad, aceptar, 409, cierre en fecha / forzado / fuera de fecha, Stripe fallido) · integración: cierre concurrente sin doble reembolso · Web: página y guardas |
| 16.1 | Web: caja deshabilitada con `navigator.onLine = false` |
| AV.1 | Unitaria y web/móvil con payload literal del backend |
| T.1 | Integración: aislamiento de las 5 tablas; dispositivo de A con sucursal de B (PI-14) |
| Esquema | `tests/test_esquema_bd.py` cubre los modelos nuevos |
| Manual | Dispositivo físico: modo avión, reservar, reiniciar, reconectar y sincronizar; cortar la red justo tras el cobro |
