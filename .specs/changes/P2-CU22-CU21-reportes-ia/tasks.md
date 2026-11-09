# Tareas de Implementación: `P2-CU22-CU21-reportes-ia`

## Bloque 0 — Especificación SDD (`Gate 0`)
- [x] **T0.1** Redactar `spec.md`, `plan.md`, `tasks.md` y `checkpoint.md` para `P2-CU22` y `P2-CU21` con soporte de Bolivianos (`Bs. / BOB`) y tipo de cambio.

## Bloque 1 — Base de Datos y Backend (`Gate 1`)
- [x] **T1.1** Crear migración Alembic `0018_catalogo_reportes_ia.py` (`down_revision = "0017"`) con tabla `catalogo_reportes_ia` (4 reportes semilla) y columnas de estado/exportación en `solicitudes_reporte_ia`.
- [x] **T1.2** Implementar paquete `Ec-backend/app/modules/plataforma/cu22_catalogo_reportes/` y registrarlo en `app/modules/plataforma/router.py`.
- [x] **T1.3** Implementar paquete `Ec-backend/app/modules/comercial/cu21_reportes_ia/` (con validación `CU12` `reportes_ia`, intérprete IA + fallback determinista, consultas controladas por `id_tenant`, conversión a Bolivianos `Bs./BOB` y exportación PDF/Excel) y registrarlo en `app/modules/comercial/router.py`.
- [x] **T1.4** Crear suite de pruebas unitarias `Ec-backend/tests/modules/comercial/test_p2_cu22_cu21_reportes_ia_unitarias.py` cubriendo `AC-01` a `AC-07` y ejecutar `pytest` (`72 passed`).

## Bloque 2 — Frontend Web (`Gate 2`)
- [x] **T2.1** Ampliar `/admin/plataforma` (`SuperadminPanelComponent`) con la pestaña **"Catálogo Reportes IA (CU22)"**.
- [x] **T2.2** Crear módulo `Ec-frontend/src/app/modules/comercial/cu21_reportes_ia/` (`ReportesIaAdminComponent`) con dictado por voz, selector de tipo de cambio en Bolivianos (`Bs.`), gráficos (`barras`, `linea`, `torta`), tabla, exportación PDF/Excel e historial.
- [x] **T2.3** Registrar `/admin/reportes-ia` en `app.routes.ts` y añadir tarjeta en `admin-dashboard.component.html`.
- [x] **T2.4** Ejecutar `tsc --noEmit`, `ng test --watch=false` (`35 passed`) y `ng build`.

## Bloque 3 — Cierre y Documentación
- [x] **T3.1** Actualizar `CHANGELOG.md` (sin número de defecto) y cerrar `checkpoint.md`.

