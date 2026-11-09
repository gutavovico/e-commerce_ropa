# Checkpoints — Parámetros de la empresa (P2-CU11)

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-11-09 | C1–C9. |
| 1 — Backend | 🟢 Aprobado (2026-11-09) | `pytest` **695/695**: 17 unitarias de CU11 y 2 de integración contra `pruebas-multitenant` (la empresa B crea, lee y cambia su fila sin tocar la de FASHION STORE; el CHECK rechaza 0 horas). Condición: `pytest` completo en verde, incluida la integración contra la rama de pruebas. |
| 2 — Web | 🟢 Aprobado (2026-11-09) | `tsc` sin errores; `ng test` **651/651** (6 de la página con el payload literal del backend: lectura, guardado, rangos, aviso A2 confirmado y cancelado, 403 de suscripción; 1 de la ruta); `ng build` correcto. Condición: `tsc`, `ng test` y `ng build` en verde. |
| 3 — Producción | ⚪ Pendiente del push del usuario | Push sin migración (un solo commit, decisión del usuario); comprobación con una cuenta de administrador. |
| 4 — Cierre | 🟢 Completo (2026-11-09) | `CHANGELOG.md` (sección P2-CU11), `CLAUDE.md` (regla C7), spec permanente en `.specs/modules/plataforma/`, promoción a `finalized/`. |
