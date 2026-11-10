# Especificación Funcional y Técnica: Suscripción y Uso de la Empresa + Cambio de Plan y Renovación con Stripe (`P2-CU09` y `P2-CU10`)

## 1. Contexto y Alcance
Este cambio implementa la **Fase 2** del Parcial 2 asignada a **Tony** según `Repartición.md` y `SI2-Parcial2.md`:
- **`P2-CU09` — Consultar suscripción y uso del plan**: Permite al `administrador` de una empresa (`tenant`) consultar el estado de su suscripción actual (plan contratado, estado, vigencia, días restantes), el consumo frente a los límites del plan (sucursales activas y empleados activos), las funcionalidades incluidas y no incluidas en su plan, y el historial completo de eventos de suscripción (`RN17`). Incluye el curso alterno **A1** (acceso garantizado aun con suscripción vencida o próxima a vencer para permitir renovar en `CU10`) y **A2** (aviso cuando se alcanza el límite de sucursales o empleados).
- **`P2-CU10` — Cambiar de plan y renovar suscripción**: Permite al `administrador` de una empresa consultar los planes disponibles con sus límites, funcionalidades y precios mensuales, elegir un plan destino y período de renovación/contratación, validar que el uso actual de sucursales activas y empleados activos no supere los límites del nuevo plan (**Curso Alterno A1**, listando las sucursales activas cuando hay exceso para que pueda desactivar las necesarias en `CU04`), procesar el cobro mediante **Stripe** en modo de prueba (`StripeService` con creación y verificación de `PaymentIntent` o simulador determinista) y actualizar la suscripción registrando el evento (`cambio_plan` o `renovacion`) en `historial_suscripcion` (`RN17`) y en `bitacora`.

**Frontera estricta de alcance:**
- **Backend (`Ec-backend/`)**: Paquete `app/modules/plataforma/cu09_cu10_suscripcion_empresa/`, montado en `app/modules/plataforma/router.py` bajo `/api/v1/plataforma/mi-suscripcion`. En `app/integrations/stripe_service.py` solo se agregan métodos/funciones de apoyo si hiciera falta (sin modificar los existentes). Cero cambios en `app/core/`.
- **Frontend Web (`Ec-frontend/`)**: Módulo standalone en `src/app/modules/plataforma/mi_suscripcion/`, ruta `/admin/suscripcion` en `app.routes.ts` (antes del comodín `:codigo`) y tarjeta de acceso en `admin-dashboard.component.html` por adición.
- **Móvil (`Ec-mobile/`)**: **CERO cambios** (`CU09` y `CU10` son exclusivos de Backend + Web).

---

## 2. Reglas de Negocio y Cursos Alternos (`SI2-Parcial2.md`)

| Código | Regla / Curso Alterno | Implementación |
|---|---|---|
| **RN12 / RN13** | Cada empresa tiene una suscripción asociada a un plan (`Basico`, `Profesional`, `Empresarial` u otro activo) con estados `prueba`, `activa`, `vencida`, `suspendida` o `cancelada`. | `GET /api/v1/plataforma/mi-suscripcion` devuelve la suscripción actual de la empresa (`id_tenant` del administrador autenticado) junto con el detalle del plan y el cálculo dinámico de vigencia (`vigente`, `dias_restantes`, `proxima_a_vencer`). |
| **RN14 / CU09 A1 / CU10 A4** | La vigencia se evalúa por fecha (`fecha_inicio <= hoy <= fecha_vencimiento`). Cuando la suscripción está vencida, `CU12` bloquea la operación normal pero permite al administrador consultar `CU09` y renovar en `CU10`. | Los endpoints de `CU09` y `CU10` exigen `require_roles(["administrador", "admin"])` y contexto de empresa (`tenant_actual(db)` o `usuario.id_tenant`), **sin** invocar `SuscripcionServicio.validar()`, de modo que un administrador con suscripción vencida o suspendida puede consultar su estado y renovar con Stripe para recuperar el acceso. |
| **RN15 / CU09 A2** | El plan define `max_sucursales_activas` y `max_empleados` (`None` = sin límite). Si el uso alcanza el límite, se informa qué recurso llegó al tope. | `GET /api/v1/plataforma/mi-suscripcion` calcula `sucursales_activas` y `empleados_activos` (roles `administrador`, `encargado_sucursal`, `cajero` activos), devuelve banderas `al_limite` / `excede_limite` y lista las sucursales activas de la empresa. |
| **RN16** | El plan determina las funcionalidades habilitadas (`productos`, `ventas`, `reservas`, `operacion_offline`, `reportes_convencionales`, `reportes_ia`). | `GET /api/v1/plataforma/mi-suscripcion` devuelve tanto `funcionalidades_incluidas` como `funcionalidades_no_incluidas` (con sugerencia de qué planes activos las incluyen). |
| **CU10 A1** | El uso actual supera el límite del plan elegido (ej. tiene 3 sucursales activas y elige un plan que permite 1): el sistema indica qué sucursales/recursos están activos y pide desactivar los necesarios antes de cambiar a ese plan. | `POST /api/v1/plataforma/mi-suscripcion/iniciar-pago` y `POST /api/v1/plataforma/mi-suscripcion/confirmar` validan el uso actual contra `plan_destino.max_sucursales_activas` y `plan_destino.max_empleados`. Si el uso supera el límite del nuevo plan, lanza `409 USO_SUPERA_LIMITE_PLAN` incluyendo en el mensaje/detalle el uso actual, el límite del plan elegido y los nombres de las sucursales activas para que el administrador las desactive en `CU04`. |
| **CU10 A2** | El pago con Stripe es rechazado o no se completa: el sistema mantiene el plan y la fecha de vencimiento actuales e informa el motivo. | Si `StripeService.verificar_intento` reporta estado distinto de `succeeded` (ej. `escenario_prueba="rechazado"` o `"fondos_insuficientes"`), lanza `402 PAGO_RECHAZADO` con el motivo sin modificar `suscripciones` ni `historial_suscripcion`. |
| **RN17** | Todo cambio de plan o renovación queda registrado en `historial_suscripcion` con usuario, fecha y detalle. | Al confirmar el pago con Stripe, actualiza `suscripciones` (`id_plan`, `estado = 'activa'`, nueva `fecha_inicio` y `fecha_vencimiento`), inserta en `historial_suscripcion` con `evento = 'cambio_plan'` (si cambió `id_plan`) o `'renovacion'` (si mantiene el mismo `id_plan`), `detalle` JSONB con plan anterior/nuevo, vigencia anterior/nueva, monto, moneda y referencia de pago Stripe, y registra en `bitacora`. |

---

## 3. Contratos de API (`/api/v1/plataforma/mi-suscripcion`)

Todos los endpoints requieren token Bearer JWT con rol `administrador` (o `admin`) perteneciente a una empresa (`id_tenant` no nulo).

1. **`GET /api/v1/plataforma/mi-suscripcion`** (`CU09`)
   - **Respuesta `200 OK` (`MiSuscripcionResumenOut`)**:
     - `empresa`: `{ id_tenant, codigo, nombre, estado, moneda }`
     - `suscripcion`: `{ id_suscripcion, id_plan, nombre_plan, precio_mensual, estado, estado_efectivo, fecha_inicio, fecha_vencimiento, dias_restantes, vigente, proxima_a_vencer }`
     - `uso`:
       - `sucursales`: `{ usados, limite, al_limite, excede_limite }`
       - `empleados`: `{ usados, limite, al_limite, excede_limite }`
       - `sucursales_activas_detalle`: `list[{ id_sucursal, codigo, nombre }]`
     - `funcionalidades_incluidas`: `list[{ codigo, nombre, descripcion }]`
     - `funcionalidades_no_incluidas`: `list[{ codigo, nombre, descripcion, planes_que_la_incluyen }]`
     - `historial`: `list[HistorialMiSuscripcionOut]` (`id_historial`, `id_suscripcion`, `evento`, `detalle`, `id_usuario`, `creado_en`)

2. **`GET /api/v1/plataforma/mi-suscripcion/planes`** (`CU10`)
   - **Respuesta `200 OK` (`list[PlanDisponibleEmpresaOut]`)**:
     - Lista de planes con `activo = true` ordenados por `precio_mensual, id_plan`.
     - Cada ítem incluye: `id_plan`, `nombre`, `precio_mensual`, `max_sucursales_activas`, `max_empleados`, `funcionalidades` (`list[str]`), `es_plan_actual` (`bool`), `compatible_con_uso_actual` (`bool`), `motivo_incompatibilidad` (`Optional[str]`).

3. **`POST /api/v1/plataforma/mi-suscripcion/iniciar-pago`** (`CU10`)
   - **Body (`IniciarPagoSuscripcionIn`)**:
     - `id_plan`: `int` (obligatorio)
     - `meses`: `int = 1` (`1..24`, por defecto `1`)
     - `metodo_pago_id`: `Optional[str] = None`
   - **Validaciones**:
     - El plan existe y está `activo = true` (`404 PLAN_NO_ENCONTRADO` / `409 PLAN_INACTIVO`).
     - Valida uso actual vs límites del plan elegido (`CU10 A1`). Si `sucursales_activas > plan.max_sucursales_activas` o (`plan.max_empleados is not None` y `empleados_activos > plan.max_empleados`), lanza `409 USO_SUPERA_LIMITE_PLAN` indicando qué sucursales activas o cuántos empleados exceden el límite.
   - **Comportamiento**:
     - Calcula `monto_total = round(plan.precio_mensual * meses, 2)`.
     - Invoca `StripeService.crear_intento(monto=monto_total, moneda=moneda_empresa, metodo_pago_id=..., metadata={...})` (si `monto_total == 0`, genera referencia sin cargo `pi_free_<hex>`).
   - **Respuesta `200 OK` (`IntentoPagoSuscripcionOut`)**:
     - `referencia`, `client_secret`, `estado_pago`, `monto`, `moneda`, `id_plan`, `nombre_plan`, `meses`, `operacion` (`"cambio_plan"` o `"renovacion"`), `requiere_accion` (`bool`).

4. **`POST /api/v1/plataforma/mi-suscripcion/confirmar`** (`CU10`)
   - **Body (`ConfirmarCambioSuscripcionIn`)**:
     - `id_plan`: `int`
     - `meses`: `int = 1` (`1..24`)
     - `referencia_pago`: `str` (`pi_...`)
     - `escenario_prueba`: `Optional[str] = None` (`None`, `"exito"`, `"rechazado"`, `"fondos_insuficientes"`)
   - **Validaciones y Comportamiento**:
     - Revalida que el plan exista, esté activo y sea compatible con el uso actual (`CU10 A1` → `409 USO_SUPERA_LIMITE_PLAN`).
     - Si `monto_total > 0`, verifica el intento con `StripeService.verificar_intento(referencia_pago, escenario_prueba=escenario_prueba)`. Si el pago no fue exitoso (`estado != "succeeded"`), lanza `402 PAGO_RECHAZADO` (`CU10 A2`) manteniendo intacta la suscripción actual.
     - Calcula nueva vigencia:
       - Si es una **renovación** del mismo plan y la suscripción actual aún no venció (`fecha_vencimiento >= hoy`), extiende `fecha_vencimiento = fecha_vencimiento_actual + (30 * meses) días` conservando `fecha_inicio`.
       - Si la suscripción estaba vencida o es un **cambio de plan**, fija `fecha_inicio = hoy` y `fecha_vencimiento = hoy + (30 * meses) días`, con `estado = "activa"`.
     - Actualiza `suscripciones`, inserta `HistorialSuscripcionORM` (`evento = "cambio_plan"` o `"renovacion"`), escribe en `bitacora` y limpia caché de tenants.
   - **Respuesta `200 OK` (`MiSuscripcionResumenOut`)**: Resumen actualizado de `CU09`.

---

## 4. Criterios de Aceptación (AC)
- **AC-01 (`CU09` Flujo Principal)**: Un administrador de empresa consulta `GET /api/v1/plataforma/mi-suscripcion` y recibe su suscripción actual, días restantes, uso de sucursales y empleados frente a los límites del plan, funcionalidades incluidas/no incluidas e historial.
- **AC-02 (`CU09 A1` / `CU10 A4` Suscripción vencida)**: Un administrador cuya suscripción está `vencida` (por estado o fecha pasada) puede consultar `GET /api/v1/plataforma/mi-suscripcion` y renovar en `CU10` sin ser bloqueado por `CU12` (`SUSCRIPCION_NO_VIGENTE`), viendo el estado efectivo `vencida` y la alerta correspondiente.
- **AC-03 (`CU09 A2` Uso al límite)**: Cuando `sucursales_activas >= max_sucursales_activas` o `empleados_activos >= max_empleados`, la respuesta marca `al_limite = true` en el recurso correspondiente.
- **AC-04 (`CU10` Catálogo de planes con compatibilidad)**: `GET /api/v1/plataforma/mi-suscripcion/planes` lista los planes activos indicando cuál es el plan actual y si cada plan es compatible con el uso actual de la empresa.
- **AC-05 (`CU10 A1` Bloqueo por exceso de uso al bajar de plan)**: Si la empresa tiene más sucursales activas o empleados activos de los que permite el plan elegido, `iniciar-pago` y `confirmar` rechazan la operación con `409 USO_SUPERA_LIMITE_PLAN` detallando las sucursales activas.
- **AC-06 (`CU10 A2` Pago rechazado en Stripe)**: Si el cobro en Stripe falla (`escenario_prueba="rechazado"` o `"fondos_insuficientes"`), `confirmar` devuelve `402 PAGO_RECHAZADO` y no modifica el plan ni la fecha de vencimiento actuales.
- **AC-07 (`CU10` Éxito de cambio de plan / renovación + `RN17`)**: Al aprobarse el pago en Stripe, se actualiza la suscripción a `activa` con el plan y vigencia correspondientes, se inserta el registro en `historial_suscripcion` con la referencia de Stripe y se registra en `bitacora`.
- **AC-08 (Frontend Web `/admin/suscripcion`)**: La vista `MiSuscripcionAdminComponent` en `/admin/suscripcion` muestra tarjetas de estado y vigencia, barras de progreso de sucursales y empleados, lista de funcionalidades incluidas/no incluidas, selector de plan y período con pasarela de prueba Stripe (incluyendo selector de escenario de prueba para demostración académica) e historial de suscripción.

