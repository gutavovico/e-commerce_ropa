# Tareas — Moneda y zona horaria de Bolivia (fix de P2-CU11)

## Bloque 0 — Preparación
- [ ] **T-0-01 (usuario):** avisar a Tony: «tomo la migración 0016».

## Bloque 1 — Backend
- [x] **T-BE-01:** Migración `0016_moneda_zona_bolivia`; `upgrade → downgrade → upgrade` en `pruebas-multitenant`.
- [x] **T-BE-02:** `core/tiempo.py` y `TimeZone` de la sesión en `after_begin`; sustituir `date.today()` y `datetime.now()` (§0.1).
- [x] **T-BE-03:** Configuración: moneda y zona editables, `moneda_bloqueada`, 409 `MONEDA_CON_OPERACIONES`.
- [x] **T-BE-04:** `moneda` en `EmpresaOut`, login, carrito, checkout y pago; Stripe con la moneda de la empresa.
- [x] **T-BE-05:** `formatear_importe` (PDF y textos) e IVA del 13 %.
- [x] **T-BE-06:** Pruebas unitarias e integración (§6); suite completa en verde.

## Bloque 2 — Web
- [x] **T-WEB-01:** Moneda de la tienda en `TenantService` y en la sesión del panel; pipe `importe`.
- [x] **T-WEB-02:** Sustituir las 74 apariciones de «€»/`EUR`; IVA 13 %.
- [x] **T-WEB-03:** Configuración con selectores de moneda y zona (M10).
- [x] **T-WEB-04:** Specs y guardia sin «€»; `tsc`, `ng test` y `ng build` en verde.

## Bloque 3 — Mobile
- [x] **T-MOB-01:** `EmpresaTienda.moneda` y `formatoImporte`; sustituir las 41 apariciones; IVA 13 %.
- [x] **T-MOB-02:** Pruebas con payloads literales; `dart analyze` y `flutter test` en verde.

## Bloque 4 — Publicación y cierre
- [ ] **T-PR-01 (usuario):** `alembic upgrade head` en producción **antes** del push; `alembic current` = `0016`.
- [ ] **T-PR-02:** Comprobar en producción: moneda BOB en el portal, un pago de prueba de Stripe en BOB, «ventas del día» de la caja.
- [x] **T-PR-03:** `CHANGELOG.md`, `CLAUDE.md` (Bolivia: zona, moneda, IVA), spec permanente de P2-CU11 actualizada y promoción a `finalized/`.
