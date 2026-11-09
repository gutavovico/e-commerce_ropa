# Tareas — Empresa de prueba Menshopping (P2-RF15)

## Bloque 0 — Insumos del usuario
- [ ] **T-0-01 (usuario):** los 4 PNG de las prendas (prenda sola, fondo transparente o blanco) y, si quiere, 4 fotos de catálogo.
- [ ] **T-0-02 (usuario, opcional):** dirección y teléfono reales de las dos sucursales (si no, quedan «Dirección por confirmar»).

## Bloque 1 — Script y datos
- [ ] **T-SC-01:** `scripts/datos/menshopping.json` y `scripts/cargar_menshopping.py` (R1–R5).
- [ ] **T-SC-02:** Copiar los PNG a `Ec-frontend/public/ar/`.
- [ ] **T-SC-03:** Pruebas unitarias e integración (§4); suite completa en verde.

## Bloque 2 — Ensayo y carga
- [ ] **T-PR-01:** Ensayo con `--db pruebas --aplicar`; comprobar en la web local con la rama de pruebas (portal `/menshopping`, login de los 5 usuarios, vestidor).
- [ ] **T-PR-02 (usuario):** commit y push de los PNG (Vercel debe servirlos antes de la carga); después, `--aplicar` en producción.
- [ ] **T-PR-03 (usuario):** una venta real en la caja de cada sucursal de Menshopping (RF15: «ventas»).
- [ ] **T-PR-04:** `CHANGELOG.md`, spec permanente y promoción a `finalized/`.
