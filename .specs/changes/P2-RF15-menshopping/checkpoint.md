# Checkpoints — Empresa de prueba Menshopping (P2-RF15)

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟡 Pendiente | El usuario aprueba §1 y R1–R7. |
| 0b — Insumos | ⚪ | Los 4 PNG en una carpeta indicada por el usuario. |
| 1 — Script | ⚪ | `pytest` completo en verde, incluida la carga con rollback contra la rama de pruebas. |
| 2 — Ensayo | ⚪ | Carga aplicada en `pruebas-multitenant` y revisada en la web local. |
| 3 — Producción | ⚪ | PNG desplegados en Vercel; carga aplicada por el usuario; ventas reales en la caja. |
| 4 — Cierre | ⚪ | `CHANGELOG.md`, spec permanente y promoción a `finalized/`. |
