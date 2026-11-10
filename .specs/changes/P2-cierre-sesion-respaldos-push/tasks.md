# Tareas · P2-Cierre — Sesión sin conexión, respaldos y notificaciones push
**Fase SDD:** 3 de 4 (Tareas) · **Estado:** aprobado · Contexto: `spec.md`, `plan.md`

Cada tarea se marca **en cuanto se termina y se verifica**, con lo que cambió respecto a lo planeado.

## Parte A — Sesión guardada (móvil) · PR 1
- [x] **T-A-01 · `SesionGuardada`** en la base local, con vencimiento por `exp`. Criterios: AC-A1, AC-A3, AC-A4.
  - Hecho (2026-11-10): `core/sesion_guardada.dart` (`SesionPersistida`, `vencimientoToken`, `SesionGuardada`); `AlmacenLocal` gana `valor`/`guardarValor`/`borrarValor` sobre la tabla `dispositivos` con clave `__sesion__` (sin cambiar el esquema SQLite). Un fallo de la base se trata como «sin sesión».
  - Nota: el token dura 24 h (`JWT_EXPIRE_MINUTES`), así que sin conexión se vuelve a entrar hasta 24 h después del último login.
  - Verificado: `test/sesion/sesion_guardada_test.dart` 4/4 (SQLite en memoria).
- [x] **T-A-02 · Arranque** en `main.dart` (restaurar → hub o caja; 401 → login sin borrar operaciones; cambio de tienda). Criterios: AC-A2, AC-A3, AC-A5.
  - Hecho (2026-11-10): `main()` lee la sesión vigente antes de `runApp`; `EcMobileApp(sesionInicial:)` va al mismo destino que tras el login (cliente con tienda → hub; sin tienda → selección; empleado → caja). Se guarda al iniciar sesión y al elegir o cambiar de tienda; se borra en `_volverAlLogin` (401 y cierre de sesión).
  - Cambió: (1) «Cerrar sesión» sin conexión se quedaba colgado porque la revocación en el servidor lanzaba error; ahora sale igual (`try/finally`). (2) `AlmacenSqlite` resolvía `databaseFactory` al construirse, así que un fallo de la base rompía el cierre de sesión antes de llegar al login; ahora se resuelve al abrir la base. Lo detectó la prueba existente del 401 en `widget_test.dart`.
  - Verificado: `test/sesion/arranque_con_sesion_test.dart` 5/5 (sin sesión → login; cajero → caja con su empresa; cliente con tienda → hub; cliente sin tienda → selección; 401 → login y sesión borrada).
- [ ] **T-A-03 ·** `dart analyze --fatal-infos`, `flutter test`, guardas; `CHANGELOG.md` (defecto). Prueba en dispositivo: abrir la app en modo avión.
  - Verificado (2026-11-10): `dart analyze --fatal-infos` sin incidencias; `flutter test` 339/339 (9 nuevas); guardas en verde; entrada en `CHANGELOG.md`.
  - Pendiente: prueba en dispositivo (usuario).

## Parte B — Respaldos (RNF18) · PR 2
- [ ] **T-B-01 (usuario) ·** Bucket R2 con regla de 30 días, token y secretos de GitHub.
- [ ] **T-B-02 · Flujo `respaldo.yml`** (`pg_dump` → `gpg` → R2). Criterios: AC-B1, AC-B2, AC-B7. Verificación: ejecución manual en GitHub y el archivo en R2 (usuario).
  - Hecho (2026-11-10): `.github/workflows/respaldo.yml` con dos trabajos. **respaldar** (cron `0 7 * * *` y manual): cliente PostgreSQL 18 de PGDG (Neon está en 18.6), `pg_dump -Fc` → `gpg` AES-256 directo a un archivo cifrado, comprobación (`gpg -d | pg_restore --list` con al menos una tabla con datos) y subida a R2 solo si todo fue bien; resumen en el job. **restaurar** (manual, con el nombre del archivo): se niega si `DATABASE_URL_RESTAURACION` es el endpoint de producción y restaura con `pg_restore --clean --if-exists --single-transaction` en esa rama.
  - Cambió: la restauración del respaldo automático va en el mismo flujo (no en el script local), así no hacen falta `gpg` ni `pg_restore` en el equipo del super administrador. Se quita `-pooler` de la URL: `pg_dump` necesita conexión directa.
  - Verificado: YAML válido, sintaxis de bash correcta, función de endpoint probada con URL con y sin pooler; guardas en verde.
  - Pendiente (usuario): ejecutar «respaldar» a mano en GitHub y ver el archivo en R2.
- [x] **T-B-03 · Endpoint de respaldo manual** (orden por FK, `COPY`, por empresa, bitácora). Criterios: AC-B3–AC-B7. Verificación: unitarias e integración de aislamiento.
  - Hecho (2026-11-10): `plataforma/rnf18_respaldos/{repositorio,servicio,router}.py`, `GET /api/v1/plataforma/respaldos?id_tenant=` (`exigir_super_administrador`, modo plataforma). Orden topológico por FK (hoy sin ciclos), `COPY (SELECT …) TO STDOUT` con psycopg, `setval` de las secuencias al final, cabecera con la cabeza de Alembic del código (el rol de la app no lee `alembic_version`), bitácora `RESPALDO_MANUAL` (WARN).
  - Cambió: (1) el archivo se arma en memoria y se devuelve entero, no por streaming: la sesión de `get_db` se cierra antes de que termine un `StreamingResponse`; la base actual pesa ~145 KB. (2) El respaldo de una empresa incluye también al super administrador en `usuarios` (aparece en su historial de suscripción y su bitácora) y excluye `codigos_recuperacion`. (3) `DATABASE_URL_RESTAURACION` declarada en `core/config.py` y `.env.example`.
  - Verificado: `tests/modules/plataforma/test_rnf18_respaldos.py` 12/12 (orden, filtros, cabecera, bitácora, 404, 403, lectura por el script, líneas `COPY` manipuladas, rechazo de producción); integración 5/5 en `pruebas-multitenant`: el respaldo de una empresa no lleva filas de otra, el de toda la plataforma lleva todas, y el de B, FASHION STORE y Menshopping no deja ninguna FK rota. Generado también contra producción solo en memoria (52 tablas, 946 filas), sin escribir nada.
- [x] **T-B-04 · Página web** del super administrador «Respaldos». Criterios: AC-B3, AC-B4.
  - Hecho (2026-11-10): `modules/plataforma/rnf18_respaldos/` (`RespaldosService`, `RespaldosComponent`): alcance «Toda la plataforma» o una empresa, descarga del archivo con el nombre del servidor, tablas y filas de las cabeceras, mensaje del servidor si falla.
  - Cambió: no es una página nueva sino una pestaña «Respaldos» del panel `/admin/plataforma` (ya protegido con `roleGuard(['super_administrador'])`), como componente propio; la pestaña carga las empresas si aún no estaban.
  - Verificado: `respaldos.component.spec.ts` 4/4; `tsc` sin errores; `ng test` 715/715; `ng build` correcto.
- [ ] **T-B-05 · `scripts/restaurar_respaldo.py`**, plantilla del PR (rama Neon previa) y `CLAUDE.md`. Criterios: AC-B8. Verificación: restaurar un respaldo en una rama nueva de Neon.
  - Hecho (2026-11-10): script en Python puro (psycopg, sin `psql`): rechaza el endpoint de `DATABASE_URL`/`DATABASE_URL_MIGRACIONES`, exige la revisión de Alembic de la cabecera y tablas vacías, pide escribir el endpoint para confirmar y restaura en una sola transacción. Solo acepta líneas `COPY` y `setval` con nombres simples (un archivo manipulado no puede colar SQL). Casilla `respaldo-pre-NNNN` en `.github/pull_request_template.md`; respaldos y rama previa en `CLAUDE.md`.
  - Verificado: unitarias (lectura de lo que genera el servicio, rechazo de líneas manipuladas y de producción con y sin pooler).
  - Pendiente (usuario): restaurar un respaldo en una rama nueva de Neon (el manual con el script y el automático con la acción «restaurar»).
- [x] **T-B-06 ·** `pytest`, `ng test`, `ng build`, guardas.
  - Verificado (2026-11-10): `pytest` 892/892 con integración contra `pruebas-multitenant` (17 nuevas: 12 unitarias y 5 de integración); `ng test` 715/715; `ng build` correcto; guardas en verde.

## Parte C — Notificaciones push (RF37) · PR 3
- [ ] **T-C-01 (usuario) ·** Proyecto Firebase, `google-services.json` local, cuenta de servicio en Render (`FIREBASE_CREDENCIALES`), `TAREAS_TOKEN`; avisar de `0022`.
- [ ] **T-C-02 · Migración `0022_token_push`** y modelo. Verificación: `upgrade → downgrade → upgrade` en `pruebas-multitenant`; `test_esquema_bd`.
- [ ] **T-C-03 · `fcm_service` y `programar_push`** (después del commit, simulador). Criterios: AC-C3, AC-C4, AC-C6.
- [ ] **T-C-04 · Registro del token** y **puntos de envío** de los siete eventos. Criterios: AC-C1, AC-C2.
- [ ] **T-C-05 · Tarea `vencer-reservas`** y `tareas-programadas.yml`. Criterios: AC-C7.
- [ ] **T-C-06 · Móvil:** Firebase, permiso, token, enrutado al tocar y aviso en primer plano. Criterios: AC-C1, AC-C5.
- [ ] **T-C-07 ·** `pytest` con integración, `dart analyze --fatal-infos`, `flutter test`, guardas. Prueba en dispositivo: un push de cada tipo, con la app abierta, en segundo plano y cerrada.
- [ ] **T-C-08 (usuario) ·** Aplicar `0022` en producción antes del push; PR.

## Cierre
- [ ] **T-CIERRE ·** `CHANGELOG.md`, specs permanentes (`plataforma/RNF18-respaldos.md`, `sincronizacion/RF37-notificaciones-push.md`), `CLAUDE.md` (cadena `0022`, siguiente `0023`; reglas de push y respaldos) y promoción a `finalized/`.
