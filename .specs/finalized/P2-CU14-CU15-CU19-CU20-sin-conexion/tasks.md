# Tareas · P2-CU14, CU15, CU19 y CU20 — Operación sin conexión
**Fase SDD:** 3 de 4 (Tareas) · **Estado:** aprobado el 2026-11-09 · Contexto de todas: `spec.md`, `plan.md`

Las tareas de una oleada no dependen entre sí; una oleada empieza cuando termina la anterior.
Cada bloque (Backend, Web, Móvil) termina en su puerta de `checkpoint.md`.

> **Nota del 2026-11-10.** Durante la implementación las tareas se marcaron en bloque al final de
> cada stack, no una a una, y las de Web y Móvil quedaron sin marcar por error. Este archivo se
> rehízo a partir del trabajo real: cada tarea dice qué cambió respecto a lo planeado y con qué se
> verificó. Desde ahora se marca cada tarea al terminarla (petición del usuario).

---

## Bloque 1 — Backend · 🟢 aprobado

### Oleada B1 — Cimientos
- [x] **T-BE-01 · Migración `0020_sin_conexion`**
  - Hecho: 5 tablas, `vence_en` y `codigo_provisional` en `reservas`, RLS y permisos.
  - Cambió: tipo de conflicto `antiguedad_excedida`; `UNIQUE (id_tenant, id_venta)` en `conflictos_sync` (un reembolso por compra); `vence_en` con valor por defecto `now() + 24 h` para que el código anterior siga creando reservas entre la migración y el despliegue (defecto 55).
  - Para ensayarla se aplicaron antes `0017`–`0019` (Tony) en `pruebas-multitenant`.
  - Verificado: `0016 → 0019 → 0020 → 0019 → 0020` varias veces; una sola cabeza; `INSERT` sin `vence_en` simulado.
- [x] **T-BE-02 · Modelos ORM**: `sincronizacion/modelos.py` y columnas en `ReservaORM`. Verificado: `test_esquema_bd` 4/4.
- [x] **T-BE-03 · `StripeService.reembolsar`** con simulador (`reembolso_fallido`) e `idempotency_key`.
  - Cambió: las pruebas quedaron en `tests/modules/sincronizacion/test_p2_cu14_cu20_avisos.py`.

### Oleada B2 — Negocio
- [x] **T-BE-04 · CU15: `vence_en` y alternativas**
  - Cambió: `ReservaServicio.registrar` (sin `commit`) separado de `crear_reserva_presencial`; nueva regla 400 `CITA_FUERA_DE_PLAZO`; el 409 conserva `STOCK_INSUFICIENTE_RESERVA` y añade `alternativas` (`DomainError.datos` en `core/errors.py`).
  - Verificado: `tests/modules/reservas` 41/41 (7 nuevas en `test_p2_cu15_vencimiento.py`).
- [x] **T-BE-05 · Dispositivos, catálogo y avisos**
  - Cambió: registrar y descargar exigen la funcionalidad `operacion_offline` del plan; 409 `DISPOSITIVO_DE_OTRO_CLIENTE`; los cupones no viajan en el catálogo.
- [x] **T-BE-06 · CU19: sincronización**
  - Cambió: una transacción por operación (no un `SAVEPOINT` por operación); estado `reintentar` si Stripe no responde; piezas sin `commit` en `PagoServicio` y `CheckoutServicio.devolver_existencias`.
- [x] **T-BE-07 · CU20: conflictos y cierre** con `FOR UPDATE SKIP LOCKED` y cierre anticipado de prueba.
  - Verificado: 49 unitarias de `tests/modules/sincronizacion`.

### Oleada B3 — Exposición y pruebas
- [x] **T-BE-08 · Routers**: 12 endpoints bajo `/api/v1`.
- [x] **T-BE-09 · Integración contra `pruebas-multitenant`**: 5 pruebas, 2 de concurrencia real (última unidad y mismo UUID) con datos confirmados que se borran al terminar.
  - Además se corrigieron 3 pruebas existentes (zona horaria y columnas de `0019`), anotadas en `CHANGELOG.md`.
- [x] **T-BE-10 · Suite y guardas**: `pytest` 852/852; guardas en verde.

## Bloque 2 — Web · 🟢 aprobado (probado en local contra `pruebas-multitenant`)

### Oleada W1 — Cimientos
- [x] **T-WEB-01 · PWA**: `@angular/service-worker` 21.2.22, `ngsw-config.json`, manifiesto e iconos neutros.
  - Cambió: el service worker guarda también Tailwind (CDN) y las fuentes; `vercel.json` no necesitó cambios (Vercel sirve primero los archivos reales).
  - Verificado: `ng build` genera `ngsw-worker.js` y `ngsw.json` sin `/api/`.
- [x] **T-WEB-02 · Almacén local**: `idb` 8, `AlmacenLocal` con implementación en memoria para las pruebas.
- [x] **T-WEB-03 · Estado de red y banda sin conexión** (`ConectividadService`, `BandaSinConexionComponent`).
  - Cambió: `tenantGuard` abre sin red una tienda ya visitada con los datos guardados.

### Oleada W2 — Funcionalidad
- [x] **T-WEB-04 · Catálogo sin red**
  - Cambió: hoja propia `/{codigo}/sin-conexion`, en lugar de hacer que las páginas en línea lean IndexedDB.
- [x] **T-WEB-05 · Reservar sin red y sincronizador** con reintento creciente y sesión expirada.
  - Cambió: solo llama a la API cuando sabe que el cliente está registrado en la tienda (hallado al probar).
- [x] **T-WEB-06 · Hoja `/{codigo}/sincronizacion`** y bandeja de avisos; tarjeta en Perfil.
- [x] **T-WEB-07 · `/admin/conflictos`** y tarjeta del panel con contador.
- [x] **T-WEB-08 · Caja sin red.**
  - Además: el modal de reserva en línea ignoraba la franja elegida y quedaba fuera del plazo; corregido (`CHANGELOG.md`).

### Oleada W3 — Verificación
- [x] **T-WEB-09 ·** `tsc` sin errores; `ng test` 706/706; `ng build` correcto; guardas en verde.

## Bloque 3 — Móvil · 🟢 aprobado

### Oleada M1 — Cimientos
- [x] **T-MOV-01 · Dependencias y SQLite**: `sqflite`, `connectivity_plus`, `uuid`; `sqflite_common_ffi` en pruebas; `AlmacenSqlite`.
  - Cambió: sin `path_provider` (`getDatabasesPath` de `sqflite` basta).
- [x] **T-MOV-02 · DTO** con `fromJson` sobre payloads generados con los esquemas del backend.
- [x] **T-MOV-03 · Conectividad**: `connectivity_plus` y comprobación de `/api/v1/health`.

### Oleada M2 — Funcionalidad
- [x] **T-MOV-04 · Catálogo sin red**
  - Cambió: hoja propia `PantallaCatalogoSinConexion`; banda de estado encima de la barra del hub.
- [x] **T-MOV-05 · Reservar sin red y cola**
  - Cambió: el id del cliente se lee del `sub` del JWT.
- [x] **T-MOV-06 · Compra interrumpida**: estado `PagoPendienteDeSincronizar`; un 402 no se guarda.
- [x] **T-MOV-07 · Pantalla «Sincronización»** (hoja con `BackButton`) y tarjeta de avisos en Perfil.
  - Además: la reserva en línea del detalle de producto tenía el mismo defecto de franjas que la web; corregido.

### Oleada M3 — Verificación
- [ ] **T-MOV-08 ·** Hecho: `dart analyze --fatal-infos` sin incidencias y `flutter test` 299/299.
  - **Falta la prueba manual en dispositivo físico** (`plan.md` §9): modo avión, reservar, reiniciar, reconectar; y la compra interrumpida.

## Bloque 4 — Publicación y cierre
- [x] **T-PR-01 (usuario) ·** `0017`–`0019` y `0020` aplicadas en producción antes del push. Verificado el 2026-11-10: `alembic current` → `0020 (head)`.
- [x] **T-PR-02 (usuario) ·** PR #11 y #12 fusionados en `main`. Verificado en producción: `/api/v1/health` 200, endpoints nuevos en el OpenAPI y `/api/v1/avisos` sin token → 401.
- [x] **T-PR-03 ·** `CHANGELOG.md`, spec permanente en `.specs/modules/sincronizacion/`, `CLAUDE.md` y promoción a `finalized/` (2026-11-10).
