# Requisitos · P2-Cierre — Sesión sin conexión, respaldos y notificaciones push   Nivel: 3   Estado: aprobado

**ID del cambio:** `P2-cierre-sesion-respaldos-push`
**Fase SDD:** 1 de 4 (Requisitos). Diseño en `plan.md`, tareas en `tasks.md`, puertas en `checkpoint.md`.
**Fuente:** `SI2-Parcial2.md` RNF03 y CU14/CU15 (consultar y reservar sin conexión), RNF18 (respaldo de
base de datos), RF37 (notificaciones push por eventos), PF-27 y las pruebas de CU20 (aviso push).
**Nivel 3 porque** toca producción (respaldos y restauración), añade una migración (`0022`) y una
integración externa nueva (Firebase).

Tres partes independientes, en este orden, cada una con su PR: **A** (defecto, solo móvil) → **B**
(RNF18) → **C** (RF37). Si el tiempo se acaba, lo publicado queda completo.

---

## Decisiones propuestas (se aprueban con la spec)

| ID | Decisión | Por qué |
| :--- | :--- | :--- |
| H1 | **A:** se guarda la sesión de clientes y empleados; sin conexión solo el cliente opera (el empleado ve su caja bloqueada, como hoy). | Mismo código para todos; la caja exige red por documento. |
| H2 | **B:** el respaldo manual de la web es de **datos** (SQL con `COPY`, sin `pg_dump`), restaurable sobre un esquema creado con `alembic upgrade head` de la misma revisión, que va escrita en la cabecera. El automático sí es `pg_dump` completo (esquema y datos). | Render no tiene `pg_dump` de la versión de Neon; generar el SQL en Python evita instalarlo. |
| H3 | **B:** la restauración la hace el super administrador con un script (`scripts/restaurar_respaldo.py`) contra una **rama nueva de Neon**, nunca desde la web ni sobre producción directamente. | Restaurar desde la web pone en riesgo producción; el documento solo exige que restaure el super administrador. |
| H4 | **B:** respaldo automático diario a las 03:00 de Bolivia; R2 conserva 30 días (regla de ciclo de vida del bucket). Cifrado `gpg` simétrico AES-256 con una frase guardada como secreto de GitHub; el super administrador la custodia fuera del repo. | Lo más simple que cumple «cifra y guarda en R2». |
| H5 | **B:** la rama de Neon previa a cada migración es un paso más del procedimiento manual (casilla en la plantilla del PR y `CLAUDE.md`), con el comando `neonctl`. | Las migraciones ya se aplican a mano; automatizarlo no ahorra nada. |
| H6 | **C:** solo Android (FCM). El token push se guarda en la tabla `dispositivos` existente (columna nueva `token_push`), no en una tabla nueva. | El dispositivo ya se registra por empresa y cliente en CU14. |
| H7 | **C:** «pedido listo para recoger» = el pago confirmado de una compra con retiro en sucursal (no existe otro estado de preparación). | No hay flujo de preparación del pedido; no se inventa uno. |
| H8 | **C:** el vencimiento de reservas, hoy perezoso, se hace también con una tarea programada (GitHub Actions cada hora) que llama a un endpoint protegido por un secreto. | Sin ella, el push «tu reserva venció» solo llegaría cuando alguien consulta. |
| H9 | **C:** en primer plano el aviso se muestra dentro de la app (barra inferior), sin paquete de notificaciones locales. | Menos dependencias; en segundo plano y cerrada lo muestra Android. |
| H10 | Aprobación **por parte** (A, B, C), cada una con backend, web y móvil juntos, en lugar de por capa. | Ahorra dos rondas por parte. |

---

## Parte A — Volver a entrar sin conexión (defecto del bloque 3)

**Hallazgo:** `main.dart` siempre arranca en el login y el login necesita el servidor. Si Android cierra la
app, el cliente no puede volver a entrar sin internet, aunque el catálogo y sus reservas pendientes sigan
en SQLite.

- **AC-A1** Cuando el usuario inicia sesión, la app deberá guardar en la base local el token, los datos
  del usuario y la tienda elegida.
- **AC-A2** Cuando la app se abre con una sesión guardada cuyo token no ha vencido, deberá entrar
  directamente a su destino (hub de la tienda guardada o caja), con o sin conexión.
- **AC-A3** Si el token guardado venció o el servidor responde 401, entonces la app deberá borrar la
  sesión guardada y mostrar el login, sin borrar las operaciones pendientes (RN37).
- **AC-A4** Cuando el usuario cierra sesión, la app deberá borrar la sesión guardada.
- **AC-A5** Cuando el cliente cambia de tienda desde Perfil, la sesión guardada deberá reflejar la nueva.

## Parte B — Respaldos (RNF18)

- **AC-B1** Cada día a las 03:00 de Bolivia, un flujo de GitHub Actions deberá respaldar toda la base con
  `pg_dump`, cifrar el archivo y subirlo a Cloudflare R2. También se podrá lanzar a mano desde GitHub.
- **AC-B2** Si el respaldo automático falla en cualquier paso, entonces el flujo deberá terminar en rojo
  y no dejar ningún archivo sin cifrar fuera del runner.
- **AC-B3** Cuando el super administrador pide desde la web un respaldo de **toda la plataforma**, el
  sistema deberá descargarle un archivo SQL con los datos de todas las tablas.
- **AC-B4** Cuando lo pide de **una empresa**, el archivo deberá contener solo filas de ese `id_tenant`
  (más su fila de `tenants` y las cuentas globales de sus empleados y clientes registrados), sin ninguna
  fila de otra empresa.
- **AC-B5** Si otro rol pide un respaldo, entonces el sistema deberá responder 403.
- **AC-B6** Cada respaldo manual deberá quedar en la bitácora con quién, cuándo y de qué alcance.
- **AC-B7** Ningún respaldo deberá guardarse en el repositorio ni en el disco del servidor (se genera en
  memoria y se transmite).
- **AC-B8** El script de restauración deberá negarse a escribir sobre la rama principal de Neon.

## Parte C — Notificaciones push (RF37)

- **AC-C1** Cuando el cliente entra a una tienda en el móvil Android, la app deberá pedir permiso de
  notificaciones y registrar su token en su dispositivo de esa empresa; si el token cambia, actualizarlo.
- **AC-C2** El sistema deberá enviar un push al cliente cuando: su reserva se **confirma**, se **cancela**
  o **vence**; se **resuelve un conflicto** (aviso de reembolso o reserva cancelada al sincronizar); su
  **pedido está listo para recoger** (H7); se **confirma un pago** hecho desde el móvil; y el
  **asistente le responde**.
- **AC-C3** El push solo deberá enviarse si la operación se confirma en la base; si la transacción se
  revierte, no se envía.
- **AC-C4** Si Firebase falla o no está configurado, entonces la operación de negocio deberá completarse
  igual (el envío es de mejor esfuerzo y queda en el log).
- **AC-C5** Cuando el cliente toca el push, la app deberá abrir la pantalla del evento (mis reservas,
  bandeja de avisos, historial de compras o asistente), también si estaba cerrada.
- **AC-C6** El push de una empresa solo deberá llegar a dispositivos registrados en esa empresa.
- **AC-C7** Cada hora, la tarea programada deberá vencer las reservas cuyo plazo pasó, liberar su stock
  como hoy y avisar por push (H8). Sin el secreto correcto, el endpoint responde 401.
- **AC-C8** Los encargados siguen recibiendo sus avisos dentro de la web, sin push (ya existe).

## Fuera de alcance

iOS · notificaciones push en la PWA · restauración desde la web · respaldos incrementales · preferencias
del cliente para silenciar tipos de aviso · un estado nuevo de «pedido en preparación».

## Lo que necesita el usuario (en paralelo, antes de B y C)

1. **Cloudflare R2:** bucket `fashionstore-respaldos` con regla de 30 días y un token de API de lectura y
   escritura solo sobre él.
2. **GitHub → Secrets:** `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`, `R2_ENDPOINT`, `R2_BUCKET`,
   `RESPALDO_FRASE` (frase de cifrado), `DATABASE_URL_RESPALDO` (rol dueño), `TAREAS_TOKEN` y
   `BACKEND_URL`.
3. **Firebase:** proyecto con app Android `com.…` (el `applicationId` actual), `google-services.json`
   (fuera del repo: gitleaks lo rechaza) y una cuenta de servicio para FCM, cuyo JSON va como variable de
   Render (`FIREBASE_CREDENCIALES`), nunca en el repo ni en el chat.
4. **Render:** `FIREBASE_CREDENCIALES` y `TAREAS_TOKEN`.
5. Avisar al equipo de que `0022` queda tomada.
