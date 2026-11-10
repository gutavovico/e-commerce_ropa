# Plan — Panel del Super Administrador SaaS (P2-CU05 · P2-CU06 · P2-CU07 · P2-CU08)

## Orden de Ejecución (con Puertas de Aprobación)

1. **Gate 0 — Aprobación de Especificación (`spec.md`):**
   - Revisar y aprobar las decisiones **S1–S4** (migración `0017` para `activo` en catálogos globales + creación de `super_administrador` fuera de banda, y contratos `/api/v1/plataforma/...`).
2. **Bloque 1 — Backend (`Ec-backend/`, Gate 1):**
   - Coordinar con Gustavo el número de migración (`0017`) según `Repartición.md` regla #1 y ensayarla en la rama de Neon de pruebas (`upgrade → downgrade → upgrade`).
   - Implementar `app/modules/plataforma/dependencias.py` (`exigir_super_administrador` con `modo_plataforma=True`).
   - Implementar `cu05_empresas_supervision`, `cu06_planes_funcionalidades`, `cu07_suscripciones` y `cu08_catalogos_globales`.
   - Registrar el router agregador de plataforma en `app/main.py` (solo por adición).
   - Escribir y ejecutar pruebas unitarias (`tests/modules/plataforma/test_p2_cu05_cu08_unitarias.py`) y de integración multitenant.
3. **Bloque 2 — Frontend Web (`Ec-frontend/`, Gate 2):**
   - Implementar modelos y `SuperadminService` (`src/app/modules/plataforma/superadmin/`).
   - Implementar `SuperadminPanelComponent` con las 5 pestañas operativas: Empresas, Planes y Funcionalidades, Suscripciones, Catálogos Globales y Bitácora de Plataforma.
   - Registrar `/admin/plataforma` en `app.routes.ts` (antes de `:codigo`) y el destino de login para `super_administrador`.
   - Escribir y ejecutar pruebas en `superadmin.service.spec.ts`, `superadmin-panel.component.spec.ts` y `app.routes.spec.ts` (`npx tsc --noEmit`, `npx ng test --watch=false`, `npx ng build`).
4. **Cierre del Bloque:**
   - Registrar entrada sin número en `CHANGELOG.md` (`Repartición.md` regla #8).
   - Actualizar `checkpoint.md` y abrir Pull Request de `p2/cu05-cu08-superadmin` a `main`.

