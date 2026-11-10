# Checkpoints · P2-CU16 y P2-CU17 — Caja en el móvil

Nivel 2. El usuario aprobó las puertas 1, 2 y 3 a la vez el 2026-11-10 («si»).

| Puerta | Estado | Condición de paso |
| :--- | :--- | :--- |
| 1 — Requisitos (`spec.md`) | 🟢 Aprobada (2026-11-10) | AC verificables; excepciones de CU16 y CU17 cubiertas; fuera de alcance escrito. |
| 2 — Diseño (`plan.md`) | 🟢 Aprobado (2026-11-10) | Contratos existentes, capas, riesgos y pruebas. Sin dependencias nuevas. |
| 3 — Tareas (`tasks.md`) | 🟢 Aprobadas (2026-11-10) | Tareas por oleadas con verificación. |
| 4 — Móvil | 🟢 Aprobado por el usuario (2026-11-10); la prueba manual en dispositivo físico (T-08) queda pendiente · `dart analyze --fatal-infos` sin incidencias; `flutter test` 325/325 (26 nuevas); guardas en verde. Falta la prueba manual en dispositivo físico (T-08). | `dart analyze --fatal-infos` y `flutter test` en verde; prueba manual en dispositivo físico. |
| 5 — Publicación | 🟢 PR #14 fusionado en `main` (2026-11-10), sin migración | PR con los seis checks (sin migración). |
| 6 — Cierre | 🟢 Completo (2026-11-10): `CHANGELOG.md`, spec permanente, spec de CU31-CU32, `CLAUDE.md` y promoción a `finalized/`; va en el mismo PR que el código | `CHANGELOG.md`, spec permanente y promoción a `finalized/`. |
