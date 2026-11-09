# Tareas de Implementación: `P2-CU09-CU10-suscripcion-stripe`

## Bloque 0 — Especificación SDD (`Gate 0`)
- [x] **T0.1** Redactar `spec.md` con casos de uso `P2-CU09` y `P2-CU10`, reglas `RN12`-`RN17`, cursos alternos (`CU09 A1`, `CU09 A2`, `CU10 A1`, `CU10 A2`, `CU10 A4`), contratos de API y criterios `AC-01` a `AC-08`.
- [x] **T0.2** Redactar `plan.md`, `tasks.md` y `checkpoint.md`.

## Bloque 1 — Backend: `CU09` y `CU10` (`Gate 1`)
- [x] **T1.1** Crear paquete `Ec-backend/app/modules/plataforma/cu09_cu10_suscripcion_empresa/` (`__init__.py`, `esquemas.py`, `repositorio.py`, `servicio.py`, `router.py`).
- [x] **T1.2** Registrar `router_cu09_cu10_suscripcion_empresa` en `Ec-backend/app/modules/plataforma/router.py` bajo `/api/v1/plataforma/mi-suscripcion`.
- [x] **T1.3** Crear suite de pruebas unitarias `Ec-backend/tests/modules/plataforma/test_p2_cu09_cu10_unitarias.py` cubriendo `AC-01` a `AC-07` (`CU09` normal, `CU09 A1` vencida, `CU09 A2` uso al límite, `CU10` listado de planes con compatibilidad, `CU10 A1` bloqueo por exceso de sucursales/empleados, `CU10 A2` pago Stripe rechazado, `CU10` éxito de cambio de plan y renovación con historial `RN17` y bitácora).
- [x] **T1.4** Ejecutar `pytest tests/modules/plataforma/ -v` y verificar 100% de pruebas en verde (`63 passed`).

## Bloque 2 — Frontend Web: `/admin/suscripcion` (`Gate 2`)
- [x] **T2.1** Crear modelos TypeScript en `Ec-frontend/src/app/modules/plataforma/mi_suscripcion/modelos/mi-suscripcion.model.ts`.
- [x] **T2.2** Crear servicio HTTP en `Ec-frontend/src/app/modules/plataforma/mi_suscripcion/servicios/mi-suscripcion.service.ts`.
- [x] **T2.3** Construir componente standalone `MiSuscripcionAdminComponent` (`mi-suscripcion-admin.component.{ts,html,scss,spec.ts}`) en `Ec-frontend/src/app/modules/plataforma/mi_suscripcion/paginas/`.
- [x] **T2.4** Agregar ruta `/admin/suscripcion` en `Ec-frontend/src/app/app.routes.ts` (antes de `:codigo`) y tarjeta de acceso en `admin-dashboard.component.html`.
- [x] **T2.5** Ejecutar `npx tsc -p tsconfig.app.json --noEmit`, `npx tsc -p tsconfig.spec.json --noEmit`, `npx ng test --watch=false` (`44 passed`) y `npx ng build`.

## Bloque 3 — Cierre y Documentación
- [x] **T3.1** Actualizar `CHANGELOG.md` (sin número de defecto) y marcar `checkpoint.md` en `🟢 Completado`.

