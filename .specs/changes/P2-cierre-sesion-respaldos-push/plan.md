# Diseño · P2-Cierre — Sesión sin conexión, respaldos y notificaciones push
**Requisitos:** `spec.md` · **Fase SDD:** 2 de 4 (Diseño) · **Estado:** aprobado

## Parte A — Sesión guardada (solo móvil, sin migración)

- `core/sesion_guardada.dart`: lee y escribe `{token, usuario, codigoTienda}` en la tabla `dispositivos`
  de `AlmacenLocal` (clave `sesion`), sin paquete nuevo. Vencimiento con el `exp` del JWT
  (`token_jwt.dart`).
- `main.dart`: `home` pasa a un arranque que restaura la sesión y llama a `_despuesDelLogin` (o abre el
  hub con la tienda guardada, sin `PantallaSeleccionEmpresa`). `_volverAlLogin` y «Cerrar sesión» la
  borran; `EmpresaActual` la actualiza al cambiar de tienda.
- Sin conexión, el hub ya muestra la banda y el catálogo local; las llamadas fallidas no deben tratarse
  como 401.
- **Pruebas:** arranque con sesión vigente (sin red) → hub; vencida → login; 401 → login conservando
  operaciones; cierre de sesión → borrada.

## Parte B — Respaldos

**Automático** · `.github/workflows/respaldo.yml` (`schedule: '0 7 * * *'` = 03:00 Bolivia, y
`workflow_dispatch`):
1. Instala `postgresql-client` de la versión mayor del servidor (repositorio PGDG).
2. `pg_dump -Fc "$DATABASE_URL_RESPALDO" | gpg --batch --symmetric --cipher-algo AES256 --passphrase-fd 3`
   → `fashionstore-AAAAMMDD-HHMM.dump.gpg` (`set -o pipefail`: si falla el volcado, falla el flujo).
3. `aws s3 cp --endpoint-url "$R2_ENDPOINT"` al bucket. El runner es efímero y nada sin cifrar toca disco.

**Manual (web)** · módulo `plataforma/cu05_empresas_supervision/respaldos` (o `plataforma/rnf18_respaldos`):
- `GET /api/v1/plataforma/respaldos?id_tenant=` (solo `super_administrador`) → `StreamingResponse`
  `text/sql`, nombre `respaldo-<alcance>-<fecha>.sql`.
- Generador: lista las tablas de `fashionstore` y las ordena por sus FK (consulta a `pg_constraint`,
  orden topológico); para cada una, `COPY (SELECT … [WHERE id_tenant = :id]) TO STDOUT` con psycopg y
  escribe bloques `COPY tabla (cols) FROM stdin;`. Cabecera con la revisión de Alembic, fecha y alcance.
  Columnas generadas (`subtotal_linea`) excluidas.
- Toda la plataforma: transacción `REPEATABLE READ, READ ONLY` en modo plataforma (la RLS de las 31
  tablas y de `0020`/`0021` ya lo admite). Por empresa: además del filtro `id_tenant`, la fila de
  `tenants`, `usuarios` de sus empleados y de los clientes de `cliente_tenant`, y esos `clientes`.
- Bitácora con `registrar_evento_seguro` (`RESPALDO_MANUAL`, alcance).
- **Web:** página `/admin/plataforma/respaldos` del panel del super administrador (`roleGuard`): «Toda la
  plataforma» o selector de empresa → descarga.
- **Restauración:** `scripts/restaurar_respaldo.py`: rechaza la URL de la rama principal (compara el
  host del endpoint con `DATABASE_URL_MIGRACIONES`); para `.dump.gpg` descifra y ejecuta `pg_restore`;
  para `.sql` aplica `alembic upgrade <revisión>` y luego `psql -f`. Documentado en `CLAUDE.md`.
- **Rama previa a migración (H5):** casilla en `.github/pull_request_template.md` y paso en `CLAUDE.md`:
  `neonctl branches create --name respaldo-pre-NNNN`.
- **Pruebas:** unitarias del orden por FK y del formato `COPY`; 403 a otros roles; integración en
  `pruebas-multitenant`: el respaldo de Menshopping no contiene ningún `id_tenant` de FASHION STORE, y el
  de toda la plataforma contiene ambas.

## Parte C — Notificaciones push

**Migración `0022_token_push`** (`down_revision = "0021"`): `dispositivos.token_push VARCHAR(255) NULL` y
`token_push_actualizado_en TIMESTAMPTZ NULL`; la `CHECK` de plataforma no cambia. Nullable: el código
desplegado sigue funcionando entre la migración y el push.

**Backend**
- `integrations/fcm_service.py`: FCM HTTP v1 con `httpx` y `google-auth` (dependencia nueva) a partir de
  `FIREBASE_CREDENCIALES` (`core/config.py`). Sin credenciales, simulador que solo registra en el log,
  como Stripe y Gemini. Un token inválido (`UNREGISTERED`) se borra del dispositivo.
- `core/notificaciones.py`: `programar_push(db, id_cliente, tipo, titulo, cuerpo, datos)` guarda el envío
  en `db.info`; un listener `after_commit` lo despacha en un `ThreadPoolExecutor` (no frena la respuesta);
  `after_rollback` lo descarta (AC-C3). Errores al log (AC-C4). Los tokens se leen dentro de la
  transacción, con la RLS de la empresa (AC-C6).
- `PUT /api/v1/sincronizacion/dispositivos/{identificador}/token-push` (cliente dueño del dispositivo).
- Puntos de envío (una línea cada uno):

  | Evento | Dónde |
  | :--- | :--- |
  | Reserva confirmada | `reservas/atencion_caja.py` (estado `confirmada`) |
  | Reserva cancelada | `cu13_consultar_cancelar_reservas` (cancelación) |
  | Reserva vencida | `_vencer_si_corresponde` (perezoso y tarea programada) |
  | Conflicto resuelto / reembolso / reserva cancelada al sincronizar | `AvisosServicio` (cada aviso nuevo genera su push) |
  | Pago confirmado desde el móvil · pedido listo para recoger (H7) | confirmación del pago en `cu16_realizar_pago` (y webhook), si el canal es móvil; con retiro en sucursal, el texto es «listo para recoger» |
  | Respuesta del asistente | servicio del asistente (CU19 del P1) |

- **Tarea programada (H8):** `POST /api/v1/plataforma/tareas/vencer-reservas` con cabecera
  `X-Tarea-Token` = `TAREAS_TOKEN` (comparación en tiempo constante); recorre las empresas activas y
  aplica `_vencer_si_corresponde` con el usuario del cliente como responsable, como el vencimiento
  perezoso. Flujo `.github/workflows/tareas-programadas.yml` cada hora.

**Móvil**
- `firebase_core` + `firebase_messaging`; plugin `com.google.gms.google-services` en Gradle;
  `google-services.json` en `.gitignore`. `core/push/servicio_push.dart` (interfaz) con implementación
  Firebase y una falsa para las pruebas.
- Tras elegir tienda (`prepararTienda`): permiso (Android 13), token → `PUT …/token-push`;
  `onTokenRefresh` igual.
- Al tocar: `getInitialMessage` (app cerrada, tras restaurar la sesión de A) y `onMessageOpenedApp` →
  `datos.tipo` → pantalla, con el `navigatorKey` global. En primer plano, `SnackBar` con «Ver» (H9).
- **Pruebas:** enrutado por tipo con el servicio falso; registro del token con payload literal.

**Backend · pruebas:** unitarias de `programar_push` (commit envía, rollback no, fallo no rompe), de cada
punto de envío con FCM simulado y del endpoint de tareas (401 sin secreto). Integración: el push de una
reserva de Menshopping no lee tokens de FASHION STORE.

## Orden y paralelismo

| Paso | Quién | Depende de |
| :--- | :--- | :--- |
| Cuentas R2 y Firebase, secretos | Usuario | — (en paralelo con A) |
| A (móvil) → PR | Claude → usuario | — |
| B (workflow, backend, web, script) → PR | Claude → usuario | Secretos de R2 para probar el flujo |
| C (`0022`, backend, móvil) → migración en producción → PR | Claude → usuario | A (abrir pantalla con la app cerrada), Firebase |

## Riesgos

| Riesgo | Decisión |
| :--- | :--- |
| `google-services.json` o la cuenta de servicio en el repo | `.gitignore`, gitleaks en CI y variable de Render. |
| La tarea programada y Render dormido | La llamada lo despierta; el endpoint es idempotente. |
| Respaldo de toda la plataforma grande para Render | Datos actuales pequeños; `StreamingResponse` sin cargar todo en memoria. |
| Push duplicado si un evento se procesa dos veces | Los puntos de envío están tras cambios de estado únicos (de `pendiente` a `vencida`, etc.). |
| Restaurar sobre producción por error | El script rechaza la rama principal (AC-B8). |
