# Checkpoints — Moneda y zona horaria de Bolivia (fix de P2-CU11)

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-11-09 | M1–M10. |
| 1 — Backend | 🟢 Aprobado (2026-11-09) | `0016` en `pruebas-multitenant` con `upgrade → downgrade → upgrade`; `pytest` **715/715** (12 unitarias nuevas del fix, 3 de integración: `TimeZone` y `current_date` de Bolivia, CHECK de moneda y zona, 409 con las ventas reales de FASHION STORE, empresa B a USD visible en directorio y login). `tzdata` añadido a `requirements.txt`. Producción sigue en `0015`. |
| 2 — Web | 🟢 Aprobado (2026-11-09) | `tsc` sin errores; `ng test` **656/656** (`moneda.spec.ts`: formato, prioridad portal → sesión → BOB y pipe reactivo; Configuración: selectores, envío de USD con actualización de la sesión, moneda bloqueada; expectativas y payloads literales en Bs con el IVA del 13 %); `ng build` correcto; `grep` sin «€», `'EUR'` ni «21 %» fuera de las specs. Deltas Δ1–Δ2. |
| 3 — Mobile | 🟢 Aprobado (2026-11-09) | `dart analyze` sin incidencias; `flutter test` **280/280** (4 nuevas en `test/p2_cu11_moneda_test.dart` con payload literal del login; mocks con `moneda: 'BOB'` e IVA al 13 %); `grep` sin «€», `'EUR'` ni «21 %» en `lib/`. Delta Δ3. |
| 4 — Producción | ⚪ Pendiente del usuario | `0016` en producción **antes** del push (`alembic current` = `0016`); después, portal en Bs, pago de prueba en BOB y «ventas del día» de la caja. |
| 5 — Cierre | 🟢 Completo (2026-11-09) | `CHANGELOG.md` (sección del fix y defectos 66–68), `CLAUDE.md` (Alembic `0016`, IVA 13 %, moneda y hora de Bolivia, RenderFlex siete veces), spec permanente de P2-CU11 (C2 superada) y promoción a `finalized/`. |

## Deltas respecto a la spec

- **Δ1:** la landing tenía dos tarjetas ilustrativas del chat con precios fijos (875 € y 550 €). Pasarlas a Bs habría mantenido precios inventados (`CLAUDE.md`, «cero datos inventados»): se quitaron las dos líneas de precio y se conservó la ilustración.
- **Δ2:** la guardia «sin €» de §6 se hace con `grep` en el checkpoint, no con una prueba: el entorno de Vitest de Angular no lee el código fuente.
- **Δ3 (RenderFlex, séptima aparición):** con «Bs 890,00» en lugar de «890 €», la fila de precios de la ficha de producto y la de las piezas de colecciones desbordaban. Ficha: `Wrap` (un precio no debe truncarse); piezas: `Flexible` con elipsis. Sin reducir fuentes.
