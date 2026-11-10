# Checkpoints · P2-CU14, CU15, CU19 y CU20 — Operación sin conexión

Nivel 3: no se salta ninguna puerta. El usuario aprobó las puertas 1, 2 y 3 a la vez el 2026-11-09 («está bien, ahora sí empieza por el bloque 1»).

| Puerta | Estado | Condición de paso |
| :--- | :--- | :--- |
| 1 — Requisitos (`spec.md`) | 🟢 Aprobada (2026-11-09) | Cada AC verificable; excepciones de CU14, CU15, CU19 y CU20 cubiertas; fuera de alcance escrito; sin preguntas abiertas. |
| 2 — Diseño (`plan.md`) | 🟢 Aprobado (2026-11-09), con las dependencias nuevas | Contrato, migración `0020`, transacciones y concurrencia, riesgos decididos y **dependencias nuevas aprobadas**. |
| 3 — Tareas (`tasks.md`) | 🟢 Aprobadas (2026-11-09) | Tareas atómicas por oleadas, cada una con archivos y verificación. |
| 4a — Backend | 🟢 Aprobado por el usuario (2026-11-09), con los 7 ajustes de `spec.md` · `pytest` **852/852** con integración contra `pruebas-multitenant` (5 nuevas, 2 de concurrencia real con dos conexiones: última unidad y mismo UUID). `0016 → 0019 → 0020 → 0019 → 0020` ensayado en la rama de pruebas; `test_esquema_bd` 4/4; guardas limpias. Ajustes a revisar: `spec.md` § «Ajustes de la implementación». | `pytest -q` completo en verde, incluida la integración contra `pruebas-multitenant`; migración ensayada `upgrade → downgrade → upgrade`; guardas. |
| 4b — Web | 🟢 Aprobada por el usuario (2026-11-09) tras probarla en local contra `pruebas-multitenant` · `tsc` sin errores; `ng test` **704/704** (12 nuevas: servicio sin conexión con payloads generados por los esquemas del backend, franjas de cita, guard sin red, caja sin red, rutas, conflictos y catálogo local); `ng build` genera `ngsw-worker.js` y `ngsw.json` sin la API; guardas en verde. Desviaciones: `spec.md` § «Ajustes de la implementación de la web». Falta la prueba manual en el navegador (modo avión). | `tsc`, `ng test`, `ng build` y guardas en verde. |
| 4c — Móvil | 🟢 Aprobado por el usuario (2026-11-09); la prueba manual en dispositivo físico queda pendiente · `dart analyze --fatal-infos` sin incidencias; `flutter test` **299/299** (19 nuevas: DTO con payloads generados por los esquemas del backend, SQLite real con `sqflite_common_ffi`, servicio sin conexión, compra interrumpida en `PagoBloc`, franjas, JWT y dos pruebas de pantalla). Desviaciones: `spec.md` § «Ajustes de la implementación móvil». **Falta la prueba manual en dispositivo físico.** | `dart analyze --fatal-infos` y `flutter test` en verde; prueba manual en dispositivo físico. |
| 5 — Producción | ⚪ Pendiente | `0017`–`0019` y `0020` aplicadas a mano antes del push; PR con los seis checks. |
| 6 — Cierre | ⚪ Pendiente | `CHANGELOG.md`, spec permanente, `CLAUDE.md` y promoción a `finalized/`. |
