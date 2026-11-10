# Tareas · P2-CU14, CU15, CU19 y CU20 — Operación sin conexión
**Fase SDD:** 3 de 4 (Tareas) · **Estado:** borrador · Contexto de todas: `spec.md`, `plan.md`

Las tareas de una oleada no dependen entre sí; una oleada empieza cuando termina la anterior.
Cada bloque (Backend, Web, Móvil) termina en su puerta de `checkpoint.md`.

---

## Bloque 1 — Backend

### Oleada B1 — Cimientos
- [x] **T-BE-01 · Migración `0020_sin_conexion`**
  - Objetivo: las 5 tablas, `vence_en` (con relleno) y `codigo_provisional` en `reservas`, RLS y permisos (`plan.md` §4).
  - Archivos: `alembic/versions/0020_sin_conexion.py`
  - Criterios: AC-T.1, AC-15.1 (columna)
  - Boundaries: sin `ENUM` nuevos; nada en producción (lo aplica el usuario).
  - Verificación: `alembic -x db=pruebas upgrade head` → `downgrade -1` → `upgrade head`; `alembic heads` con una sola cabeza.
- [x] **T-BE-02 · Modelos ORM**
  - Archivos: `app/modules/sincronizacion/{__init__,modelos}.py`; `vence_en` y `codigo_provisional` en `ReservaORM` (donde ya vive).
  - Verificación: `pytest tests/test_esquema_bd.py` contra la rama de pruebas.
- [x] **T-BE-03 · `StripeService.reembolsar`**
  - Archivos: `app/integrations/stripe_service.py`, `tests/modules/sincronizacion/test_stripe_reembolso.py`
  - Criterios: AC-20.4, AC-20.6 · Boundaries: sin cambiar los métodos existentes; simulador determinista sin clave; `idempotency_key`.
  - Verificación: `pytest tests/modules/sincronizacion -k reembolso`

### Oleada B2 — Negocio
- [x] **T-BE-04 · CU15: `vence_en` y alternativas** (depende de T-BE-02)
  - Archivos: `reservas/cu12_reservar_prendas/{servicio,esquemas}.py`, `reservas/cu13_consultar_cancelar_reservas/servicio.py`, sus pruebas.
  - Criterios: AC-15.1–AC-15.4 · Verificación: `pytest tests/modules/reservas -q`
- [x] **T-BE-05 · Dispositivos, catálogo y avisos** (depende de T-BE-02)
  - Archivos: `sincronizacion/{cu14_dispositivo_catalogo,avisos_cliente}/{servicio,repositorio,esquemas}.py`, pruebas.
  - Criterios: AC-14.1–AC-14.4, AC-14.8, AC-AV.1 · Verificación: `pytest tests/modules/sincronizacion -k "cu14 or avisos"`
- [x] **T-BE-06 · CU19: sincronización** (depende de T-BE-04)
  - Archivos: `sincronizacion/cu19_sincronizar/{servicio,repositorio,esquemas,saneado}.py`, pruebas.
  - Criterios: AC-19.2–AC-19.9, AC-19.12 · Boundaries: reutiliza `ReservaServicio` y la confirmación de pago de `cu16_realizar_pago`, sin copiar sus reglas.
  - Verificación: `pytest tests/modules/sincronizacion -k cu19`
- [x] **T-BE-07 · CU20: conflictos y cierre** (depende de T-BE-03 y T-BE-06)
  - Archivos: `sincronizacion/cu20_conflictos/{servicio,repositorio,esquemas}.py`, pruebas.
  - Criterios: AC-20.1–AC-20.8 · Verificación: `pytest tests/modules/sincronizacion -k cu20`

### Oleada B3 — Exposición y pruebas
- [x] **T-BE-08 · Routers** (depende de B2)
  - Archivos: `sincronizacion/router.py` y los `router.py` de cada CU; una línea en `app/main.py`.
  - Verificación: `pytest tests/modules/sincronizacion -q`
- [x] **T-BE-09 · Integración contra `pruebas-multitenant`** (depende de T-BE-08)
  - Archivos: `tests/integracion/test_multitenant.py`
  - Criterios: AC-T.1, AC-T.2, AC-19.3 (concurrente), cierre sin doble reembolso, PI-14.
  - Verificación: `pytest tests/integracion -q`
- [x] **T-BE-10 · Suite y guardas**
  - Verificación: `pytest -q` completo y `bash .github/scripts/guardas.sh`.

## Bloque 2 — Web

### Oleada W1 — Cimientos
- [x] **T-WEB-01 · PWA:** `@angular/service-worker`, `ngsw-config.json` sin la API, manifiesto e iconos; revisar `vercel.json`. Criterios: AC-T.4. Verificación: `npx ng build` genera `ngsw-worker.js`.
- [x] **T-WEB-02 · Almacén local:** `idb`, catálogo y cola por empresa, correlativo `PROV`. Criterios: AC-14.5, AC-15.5, AC-T.3. Verificación: `ng test --include` del almacén.
- [x] **T-WEB-03 · Estado de red y banda sin conexión.** Criterios: AC-14.7. Verificación: specs del servicio de red.

### Oleada W2 — Funcionalidad
- [x] **T-WEB-04 · Catálogo, búsqueda y detalle sin red** (depende de W1). Criterios: AC-14.6, AC-14.7.
- [x] **T-WEB-05 · Reservar sin red y sincronizador** con reintento creciente y sesión expirada (depende de W1). Criterios: AC-15.5, AC-19.1, AC-19.10, AC-19.11, AC-19.13.
- [x] **T-WEB-06 · Hoja `/{codigo}/sincronizacion` y bandeja de avisos.** Criterios: AC-19.13, AC-AV.1.
- [x] **T-WEB-07 · `/admin/conflictos`** con `roleGuard`, detalle, aceptar, cierre (con confirmación) y tarjeta con contador. Criterios: AC-20.1–AC-20.9.
- [x] **T-WEB-08 · Caja sin red.** Criterios: AC-16.1.

### Oleada W3 — Verificación
- [x] **T-WEB-09 ·** `npx tsc -p tsconfig.app.json --noEmit`, `npx ng test --watch=false`, `npx ng build`, guardas; specs con payloads literales del backend; `app.routes.spec.ts` actualizado.

## Bloque 3 — Móvil

### Oleada M1 — Cimientos
- [x] **T-MOV-01 · Dependencias y SQLite:** `sqflite`, `path_provider`, `connectivity_plus`, `uuid`; esquema local por empresa. Criterios: AC-T.3. Verificación: `flutter test` del repositorio con `sqflite_common_ffi`.
- [x] **T-MOV-02 · DTO** con `fromJson` sobre payloads literales. Verificación: `flutter test test/sincronizacion`.
- [x] **T-MOV-03 · Conectividad** con comprobación de `/health`.

### Oleada M2 — Funcionalidad
- [x] **T-MOV-04 · Catálogo y detalle sin red** con aviso de fecha. Criterios: AC-14.5–AC-14.7.
- [x] **T-MOV-05 · Reservar sin red y cola.** Criterios: AC-15.5, AC-19.1, AC-19.10, AC-19.11.
- [x] **T-MOV-06 · Compra interrumpida.** Criterios: AC-19.7–AC-19.9.
- [x] **T-MOV-07 · Pantalla «Sincronización» (hoja con `BackButton`) y bandeja en Perfil.** Criterios: AC-19.13, AC-AV.1.

### Oleada M3 — Verificación
- [ ] **T-MOV-08 ·** `dart analyze --fatal-infos` y `flutter test`; prueba manual en dispositivo físico (`plan.md` §9).

## Bloque 4 — Publicación y cierre
- [ ] **T-PR-01 (usuario) ·** Confirmar que `0017`–`0019` están en producción; aplicar `0020` a mano y comprobar `alembic current` **antes** del push.
- [ ] **T-PR-02 (usuario) ·** Commit, push y PR; seis checks en verde.
- [ ] **T-PR-03 ·** `CHANGELOG.md`, spec permanente en `.specs/modules/sincronizacion/`, nota en `CLAUDE.md` (nuevo paquete y regla de vencimiento) y promoción a `finalized/`.
