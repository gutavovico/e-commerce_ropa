# Tareas — Parámetros de la empresa (P2-CU11)

## Bloque 1 — Backend
- [x] **T-BE-01:** `ParametrosEmpresaServicio` (`vigentes`, `obtener`, `actualizar`) con creación de la fila que falte (C4) y bitácora de lo que cambió (C5).
- [x] **T-BE-02:** `GET` y `PUT /admin/configuracion` (administrador; suscripción vigente al guardar), rangos de C3.
- [x] **T-BE-03:** Pruebas unitarias e integración (§5); suite completa en verde.

## Bloque 2 — Web
- [x] **T-WEB-01:** Página `/admin/configuracion`, ruta con `roleGuard` y tarjeta en el panel.
- [x] **T-WEB-02:** Aviso al desactivar la operación sin conexión (A2).
- [x] **T-WEB-03:** Specs; `tsc`, `ng test` y `ng build` en verde.

## Bloque 3 — Publicación y cierre
- [ ] **T-PR-01:** Commit y push (sin migración); comprobación en producción con una cuenta de administrador.
- [x] **T-PR-02:** `CHANGELOG.md`, `CLAUDE.md` (regla C7), spec permanente y promoción a `finalized/`.
- [ ] **T-PR-03 (usuario):** avisar a Tony de §6 (fila de `configuracion_tenant` en el alta de empresa).
