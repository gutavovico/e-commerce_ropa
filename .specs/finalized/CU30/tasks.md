# Plan de Tareas: [CU30] Consultar bitacora

## Oleada 1: Backend (Ec-backend)
- [x] **Tarea 1.1: Migracion DDL y Modelo ORM**
  - Crear migracion Alembic `0011_cu30_bitacora.py` para crear la tabla `fashionstore.bitacora` con sus indices.
  - Crear `app/modules/seguridad/cu30_bitacora/modelos.py` con la entidad `Bitacora`.
- [x] **Tarea 1.2: Esquemas Pydantic v2 y Errores**
  - Crear `app/modules/seguridad/cu30_bitacora/esquemas.py` con filtros, resumen, detalle y metricas.
  - Crear `app/modules/seguridad/cu30_bitacora/errores.py`.
- [x] **Tarea 1.3: Servicio y Router REST**
  - Implementar `ServicioBitacoraAuditoria` en `servicio.py`.
  - Implementar endpoints en `router.py` montados en `/api/v1/admin/bitacora`.
  - Registrar el router en `app/main.py`.
- [x] **Tarea 1.4: Suite de Pruebas Backend**
  - Crear `tests/modules/seguridad/test_cu30_bitacora.py` con cobertura completa (401, 403, filtros, orden, detalle).
  - Validar ejecucion limpia con `pytest` (14 pruebas CU30, 312 totales en verde).

## Oleada 2: Frontend Web (Ec-frontend)
- [x] **Tarea 2.1: Modelos y Servicio Angular**
  - Crear `src/app/modules/seguridad/cu30_bitacora/modelos/bitacora.dto.ts`.
  - Crear `src/app/modules/seguridad/cu30_bitacora/servicios/bitacora-admin.service.ts` y sus pruebas unitarias.
- [x] **Tarea 2.2: Componente y Vista de Auditoria**
  - Implementar `bitacora-admin.component.ts`, `.html` y `.scss`.
  - Configurar visualizacion de KPIs, tabla cronologica, filtros con debounce y modal de payloads JSON.
  - Registrar ruta en `app.routes.ts`: `path: 'admin/bitacora'` con `[authGuard, roleGuard(['administrador', 'admin'])]`.
- [x] **Tarea 2.3: Integracion en AdminDashboard y Pruebas Unitarias**
  - Agregar tarjeta duodecima (#btn-consultar-bitacora) en `admin-dashboard.component.html` con directiva dual y `@if (esAdmin())`.
  - Actualizar `admin-dashboard.component.ts` con conteo de 12 modulos activos para administrador.
  - Actualizar `admin-dashboard.component.spec.ts` con prueba de clic en `#btn-consultar-bitacora` invocando `router.navigateByUrl`.
  - Crear `bitacora-admin.component.spec.ts` con cobertura de KPIs, filtros y tabla.

## Oleada 3: Cierre, Promocion y DoD
- [x] **Tarea 3.1: Verificacion Integral de Suites**
  - Ejecutar `pytest` en backend (312/312 pasadas en 4.23s).
  - Ejecutar `ng test --watch=false` en frontend (358/358 pasadas en 33 archivos en 9.33s).
  - Ejecutar `npm run build` en Ec-frontend (compilacion limpia con 0 errores y 0 advertencias).
- [x] **Tarea 3.2: Promocion Documental y Changelogs**
  - Promover a `.specs/finalized/CU30/` y `.specs/modules/seguridad/CU30-consultar-bitacora.md`.
  - Actualizar `CHANGELOG.md` y `.specs/CHANGELOG.md` con version v2.7.0.
  - Limpiar `.specs/changes/CU30/` dejando `.gitkeep`.
- [x] **Tarea 3.3: Auditoria de Cero Emojis y Balance Final**
  - Auditar 0 emojis en todo el repositorio y emitir balance formal de terminacion.
