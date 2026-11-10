# Checkpoints · P2-Cierre — Sesión sin conexión, respaldos y notificaciones push

Nivel 3. Propuesta (H10): aprobar las puertas 1–3 juntas y después cada parte completa (A, B, C).
Publicación (decisión del usuario, 2026-11-10): las tres partes se suben juntas, en un solo PR, al terminar C; `0022` se aplica en producción antes de ese push.

| Puerta | Estado | Condición de paso |
| :--- | :--- | :--- |
| 1 — Requisitos (`spec.md`) | 🟢 Aprobada por el usuario (2026-11-10), con H1–H10 | AC verificables; decisiones H1–H10 aceptadas o cambiadas. |
| 2 — Diseño (`plan.md`) | 🟢 Aprobada por el usuario (2026-11-10), con H1–H10 | Contratos, migración `0022`, riesgos. |
| 3 — Tareas (`tasks.md`) | 🟢 Aprobada por el usuario (2026-11-10), con H1–H10 | Tareas por parte con verificación. |
| 4A — Sesión guardada | 🟢 Aprobada por el usuario (2026-11-10) · analyze sin incidencias, `flutter test` 339/339, guardas en verde. Pendiente: prueba en dispositivo. | Analyze, tests, prueba en modo avión. |
| 4B — Respaldos | 🟡 Pendiente de aprobación · `pytest` 892/892 con integración, `ng test` 715/715, `ng build`, guardas en verde. Pendiente (usuario): ejecutar el flujo en GitHub con archivo en R2 y restaurar en una rama nueva. | Flujo ejecutado con archivo en R2; integración de aislamiento; restauración en rama. |
| 4C — Push | ⚪ Pendiente | `0022` ensayada; tests; push de cada tipo en dispositivo. |
| 5 — Producción | ⚪ Pendiente | `0022` aplicada antes del push; un PR con las tres partes. |
| 6 — Cierre | ⚪ Pendiente | `CHANGELOG.md`, specs permanentes, `CLAUDE.md`, `finalized/`. |
