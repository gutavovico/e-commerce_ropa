# Tareas — Usuarios y sucursales por empresa (P2-CU03 · P2-CU04)

## Bloque 0 — Preparación
- [x] **T-0-01:** Corregir `SI2-Parcial2.md` (§0.4 de la spec).
- [ ] **T-0-02:** Avisar a Tony de §6 de la spec (`uso()`, bloqueo de límites, rutas de ciudades retiradas).

## Bloque 1 — Backend
- [x] **T-BE-01:** B1 — `cu20` limitado a empleados de la empresa; 404 fuera de alcance. Prueba de integración de la fuga.
- [x] **T-BE-02:** `SucursalesEmpleadoServicio` (`autorizadas`, `autoriza`, `reemplazar`) y `GET /mis-sucursales`.
- [x] **T-BE-03:** `cu20`: B2 (roles), B3 (sucursales autorizadas y compatibilidad con `id_sucursal`), límite al reactivar, B9.
- [x] **T-BE-04:** `cu12`: `uso()` y bloqueo `pg_advisory_xact_lock` (B8). `GET /admin/sucursales/uso-plan`.
- [x] **T-BE-05:** `cu21`: retirar escritura de ciudades (B6), `total_empleados` por autorizados, B9.
- [x] **T-BE-06:** RN07 en los 7 sitios (B4), con sus códigos de error.
- [x] **T-BE-07:** Pruebas unitarias e integración (§5), incluida la activación simultánea; suite completa en verde.

## Bloque 2 — Web
- [x] **T-WEB-01:** Usuarios: roles, casillas de sucursales y principal, columna de sucursales.
- [x] **T-WEB-02:** Sucursales: uso del plan, aviso de límite, ciudades de solo lectura.
- [x] **T-WEB-03:** Caja: selector con `mis-sucursales` cuando hay más de una.
- [x] **T-WEB-04:** Specs; `tsc`, `ng test` y `ng build` en verde.

## Bloque 3 — Publicación y cierre
- [ ] **T-PR-01:** Commit y push (sin migración); comprobación en producción con una cuenta de administrador.
- [x] **T-PR-02:** `CHANGELOG.md` (defecto de la fuga de §0.1 y los que salgan), spec permanente en `.specs/modules/`, mover a `finalized/`.
