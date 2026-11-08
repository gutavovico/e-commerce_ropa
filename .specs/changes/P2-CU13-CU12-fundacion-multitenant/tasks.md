# Tareas — Fundación Multitenant (P2-CU13 · P2-CU12)

## Bloque 0 — Preparación (usuario)
- [x] **T-0-01:** Rama de Neon `respaldo-pre-0012`.
- [x] **T-0-02:** Rama de Neon `pruebas-multitenant` y `DATABASE_URL_PRUEBAS` en `Ec-backend/.env` (verificado: endpoint propio, Alembic en `0011`).
- [x] **T-0-03:** Rol `fashionstore_app` creado por SQL con `NOBYPASSRLS` en las ramas `pruebas-multitenant` y principal (los roles no se copian a ramas ya creadas).
- [x] **T-0-04:** En `.env`: `DATABASE_URL_MIGRACIONES` (copia de la URL actual, dueño) y `DATABASE_URL_PRUEBAS_APP` (rama de pruebas con el rol `fashionstore_app`). `DATABASE_URL` no cambia hasta T-PR-02.

## Bloque 1 — Base de datos (se aplica solo en la rama de pruebas)
- [x] **T-BD-01:** `0012_tenants_planes` con datos iniciales; `alembic heads` con una sola cabeza.
- [x] **T-BD-02:** `0013_id_tenant`: columnas, relleno, valores por defecto, claves únicas por empresa y FK compuestas.
- [x] **T-BD-03:** `0014_rls`: políticas, vistas `security_invoker`, enum y `GRANT`.
- [x] **T-BD-04:** `upgrade → downgrade → upgrade` sin errores en la rama de pruebas.
- [x] **T-BD-05:** `alembic/env.py` con `DATABASE_URL_MIGRACIONES`; `render.yaml` con la variable (`sync: false`).

## Bloque 2 — Backend
- [x] **T-BE-01:** `core/tenant.py` (contexto, `after_begin`, dependencia global) y configuración.
- [x] **T-BE-02:** JWT con `id_tenant`; `get_current_user` y `get_optional_current_user` resuelven la empresa antes de leer `usuarios`.
- [x] **T-BE-03:** Login con `codigo_empresa` opcional y `tenant` en la respuesta (§1.3).
- [x] **T-BE-04:** `id_tenant` con `FetchedValue()` en los ORM y modelos nuevos; `test_esquema_bd.py` en verde contra la rama de pruebas.
- [x] **T-BE-05:** `modules/plataforma/cu12_validar_suscripcion` (servicio, repositorio y dependencia) con pruebas unitarias.
- [x] **T-BE-06:** Conexión de P2-CU12 a las operaciones de F17.
- [x] **T-BE-07:** Webhook y `crear_intento` con metadatos y modo plataforma.
- [x] **T-BE-08:** Pruebas de integración de §A.5 contra la rama de pruebas con el rol `fashionstore_app`.
- [x] **T-BE-09:** Suite completa en verde y prueba de humo de los GET.

## Bloque 3 — Producción (solo con confirmación explícita)
- [ ] **T-PR-01:** `alembic upgrade head` en la rama principal de Neon.
- [ ] **T-PR-02:** `DATABASE_URL` de `.env` y de Render pasan al rol `fashionstore_app`; verificación de extremo a extremo.

## Cierre
- [ ] **T-CI-01:** Delta de la constitución (F20), `CLAUDE.md`, `CHANGELOG.md` y promoción de la spec.
