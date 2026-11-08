# Checkpoints — CU31-CU32: Punto de Venta Presencial

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-11-08 (D1–D11 recomendadas + PDF del comprobante) | — |
| 0b — Personal en `empleados` | 🟢 Completo | CU20 crea la ficha (29/29 pruebas); regularización aplicada en Neon (EMP-13, EMP-14). |
| 1 — Backend | 🟢 Completo | `pytest` 551 en verde (30 nuevas del POS; solo fallan los tests de webhook de CU16, previos). End-to-end contra Neon: 30/30 comprobaciones, con rollback total. |
| 2 — Web | 🟢 Aprobado por el usuario (2026-11-08, tras su prueba manual) | `ng test` 624/624 (19 del POS) (12 nuevas del POS + dashboard, login y rutas); `tsc` app y spec limpios; `ng build` sin errores (chunk `punto-venta` 50,6 kB). |
| 3 — Cierre | 🟢 Completo (2026-11-08) | CHANGELOG (resumen y defectos 49–52), CLAUDE.md, spec permanente `.specs/modules/compras_pagos/CU31-CU32-punto-de-venta-presencial.md`. Backend 567/567 · Web 624/624. |
