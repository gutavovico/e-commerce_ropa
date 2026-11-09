# Checkpoints — Acceso por empresa (P2-CU02 · P2-CU01)

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-11-08 | A1–A16 |
| 0b — Preparación | 🟢 Completa | `SI2-Parcial2.md` corregido (20 cambios). 0 correos repetidos en pruebas (precondición de `0015`) y en producción (consulta del usuario, 2026-11-08). |
| 1 — Backend | 🟢 Aprobado (2026-11-08) | `0015` en `pruebas-multitenant` con `upgrade → downgrade → upgrade`; `pytest` **624/624** (integración contra la rama de pruebas con `fashionstore_app`, incluido `test_esquema_bd`). Defecto evitado: Δ2 (bitácora sin empresa → 500 en el login). Producción sigue en `0014`. |
| 2 — Web | 🟢 Aprobado (2026-11-08) | `tsc` sin errores; `ng test` **638/638** (13 pruebas nuevas en `core/tenant/tenant.spec.ts` y `app.routes.spec.ts` reescrito); `ng build` correcto. Deltas Δ5–Δ12 (Δ12: página en blanco por NG0200, corregida). Sin prueba manual en navegador: requiere un backend con `0015`, que solo existe en la rama de pruebas (se hará en T-PR-03). |
| 3 — Producción | 🟡 En curso | `0015` aplicada por el usuario (`alembic current` = `0015`); `TENANT_POR_DEFECTO` no existía en `.env` ni en Render. Falta: push conjunto y verificación de extremo a extremo. |
| 4 — Móvil | 🟢 Aprobado (2026-11-08) | `dart analyze` sin incidencias; `flutter test` **276/276** (10 nuevas en `test/p2_cu02_acceso_empresa_test.dart`, con payloads literales). Deltas Δ13–Δ17. Prueba en dispositivo pendiente: requiere el backend con `0015`. Se publica junto con backend y web (decisión del usuario). |
| 5 — Cierre | ⚪ Pendiente | Documentación y promoción |
