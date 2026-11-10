# Tareas — Panel del Super Administrador SaaS (P2-CU05 · P2-CU06 · P2-CU07 · P2-CU08)

## Bloque 0 — Especificación
- [x] **T-0-01:** Sincronizar `main`, crear rama `p2/cu05-cu08-superadmin` y redactar `spec.md`, `plan.md`, `tasks.md` y `checkpoint.md`.
- [x] **T-0-02 (Gate 0):** Aprobación de la especificación y decisiones S1–S4 por el usuario.

## Bloque 1 — Backend (`Ec-backend/`)
- [x] **T-BE-01:** Migración `0017_superadmin_catalogos` (`activo` en `ciudades`, `tallas`, `colores`, sin credenciales en código) + script fuera de banda `scripts/crear_superadmin.py` y actualización de modelos ORM.
- [x] **T-BE-02:** Dependencia `exigir_super_administrador` en `app/modules/plataforma/dependencias.py` (activa `app.modo_plataforma = 'on'`).
- [x] **T-BE-03 (CU05):** Implementar `cu05_empresas_supervision` (listar empresas, crear empresa + admin + config + suscripción + historial, cambiar estado, bitácora global de plataforma).
- [x] **T-BE-04 (CU06):** Implementar `cu06_planes_funcionalidades` (listar funcionalidades y planes, crear/editar plan, advertencia de reducción de límites A1 y bloqueo de desactivación con suscritos A2).
- [x] **T-BE-05 (CU07):** Implementar `cu07_suscripciones` (listar estado por empresa, asignar plan validando vigencia única A1 y fechas A2, suspender/reactivar/cancelar e historial).
- [x] **T-BE-06 (CU08):** Implementar `cu08_catalogos_globales` (CRUD + activar/desactivar A2 + bloqueo de borrado en uso A3 para ciudades, tallas y colores).
- [x] **T-BE-07:** Registrar router de plataforma en `app/main.py` por adición y ejecutar pruebas unitarias y de integración (`AC-01` a `AC-08`).

## Bloque 2 — Frontend Web (`Ec-frontend/`)
- [x] **T-WEB-01:** Modelos e interfaces TypeScript (`superadmin.model.ts`) y `SuperadminService` (`superadmin.service.ts`).
- [x] **T-WEB-02:** Componente `SuperadminPanelComponent` (`/admin/plataforma`) con pestañas de Empresas, Planes, Suscripciones, Catálogos Globales y Bitácora.
- [x] **T-WEB-03:** Añadir ruta `/admin/plataforma` en `app.routes.ts` y redirección de login para `super_administrador`.
- [x] **T-WEB-04:** Pruebas unitarias en Vitest (`ng test`), verificación de `app.routes.spec.ts`, `tsc --noEmit` y `ng build`.

## Bloque 3 — Cierre
- [x] **T-CI-01:** Añadir entrada sin número en `CHANGELOG.md` y actualizar `checkpoint.md`.

