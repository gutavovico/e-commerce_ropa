# Tareas de Implementación: `P2-CU23-CU25-aprendizaje-ml`

## Bloque 0 — Especificación SDD (`Gate 0`)
- [x] **T0.1** Redactar `spec.md`, `plan.md`, `tasks.md` y `checkpoint.md` para `P2-CU23`, `P2-CU24` y `P2-CU25` con soporte de Bolivianos (`Bs. / BOB`) y tipo de cambio.

## Bloque 1 — Base de Datos y Backend (`Gate 1`)
- [x] **T1.1** Crear migración Alembic `0018_aprendizaje_automatico_ml.py` (`down_revision = "0017"`) con las tablas `datasets_ml`, `modelos_ml`, `predicciones_ml` y `segmentos_clientes_ml` (con `id_tenant` y políticas RLS).
- [x] **T1.2** Implementar paquete `Ec-backend/app/modules/comercial/cu23_cu25_aprendizaje_ml/` (`modelos.py`, `esquemas.py`, `motor_ml.py`, `repositorio.py`, `servicio.py`, `router.py`) y montarlo en `Ec-backend/app/modules/comercial/router.py`.
- [x] **T1.3** Crear suite de pruebas unitarias `Ec-backend/tests/modules/comercial/test_p2_cu23_cu25_aprendizaje_ml_unitarias.py` cubriendo `AC-01` a `AC-08` y verificar `alembic heads` (`0018 (head)`) + `pytest` (`77 passed`).

## Bloque 2 — Frontend Web (`Gate 2`)
- [x] **T2.1** Crear módulo `Ec-frontend/src/app/modules/comercial/cu23_cu25_aprendizaje_ml/` (`modelos/aprendizaje-ml.model.ts`, `servicios/aprendizaje-ml.service.ts`, `paginas/aprendizaje-ml-admin.component.{ts,html,scss,spec.ts}`).
- [x] **T2.2** Registrar ruta `/admin/aprendizaje-ml` en `app.routes.ts` (antes de `:codigo`) y añadir tarjeta en `admin-dashboard.component.html`.
- [x] **T2.3** Ejecutar `tsc --noEmit`, `ng test --watch=false` (`39 passed`) y `ng build`.

## Bloque 3 — Cierre y Documentación
- [x] **T3.1** Actualizar `CHANGELOG.md` (sin número de defecto) y cerrar `checkpoint.md`.

