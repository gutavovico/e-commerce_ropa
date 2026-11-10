# Checkpoints · P2-CU18 — Registrar cambio de prenda

Nivel 3: no se salta ninguna puerta. El usuario aprobó las puertas 1, 2 y 3 a la vez el 2026-11-10 («está aprobada, puedes empezar»).

| Puerta | Estado | Condición de paso |
| :--- | :--- | :--- |
| 1 — Requisitos (`spec.md`) | 🟢 Aprobada (2026-11-10) | AC verificables; A1–A4 de CU18 cubiertas; fuera de alcance escrito. |
| 2 — Diseño (`plan.md`) | 🟢 Aprobado (2026-11-10) | Contrato, cálculo, migración `0021`, transacción y concurrencia, riesgos. |
| 3 — Tareas (`tasks.md`) | 🟢 Aprobadas (2026-11-10) | Tareas por bloque con verificación. |
| 4a — Backend | 🟢 Aprobado por el usuario (2026-11-10) · `pytest` 875/875 con integración (3 nuevas de CU18, 1 de concurrencia real); `0021` ensayada `upgrade → downgrade → upgrade`; `test_esquema_bd` 4/4; guardas en verde. | `pytest` completo con integración; migración ensayada; guardas. |
| 4b — Web | 🟢 Aprobada por el usuario (2026-11-10) · `tsc` sin errores; `ng test` 711/711 (5 nuevas con payloads generados por el backend); `ng build` correcto; guardas en verde. | `tsc`, `ng test`, `ng build` y guardas. |
| 4c — Móvil | 🟢 Aprobado por el usuario (2026-11-10) · `dart analyze --fatal-infos` sin incidencias; `flutter test` 330/330 (5 nuevas); guardas en verde. Pendiente: prueba en dispositivo físico. | `dart analyze --fatal-infos` y `flutter test`; prueba en dispositivo físico. |
| 5 — Producción | ⚪ Pendiente | `0021` aplicada antes del push; PR con los seis checks. |
| 6 — Cierre | 🟢 Preparado (2026-11-10) · CHANGELOG, spec permanente, `CLAUDE.md` (`0021`, siguiente `0022`) y promoción a `finalized/`. | `CHANGELOG.md`, spec permanente, `CLAUDE.md`, `finalized/`. |
