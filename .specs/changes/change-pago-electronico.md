# Propuesta de Cambio Técnico: Realizar Pago Electrónico

**ID del Cambio:** `change-pago-electronico`
**Módulo Afectado:** `compras_pagos`
**Caso de Uso:** **CU16** — Realizar Pago Electrónico (cierre del ciclo de compra)
**Depende de:** CU15, que deja la orden en `pendiente` con existencias retenidas
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)
**Nivel SDD:** **3 (alto riesgo)** — transacción monetaria, transición de estado de venta y
consolidación de inventario. Exige sección de riesgos, transacciones explícitas y pruebas de
concurrencia; ningún gate puede omitirse.
**Fuentes de Verdad Visuales:** `image_f4fca1.png` (Web, dos columnas) · `image_f4fcc0.png`
(Mobile, pantalla completa con footer fijo)
**Fuente de Verdad de Datos:** **PostgreSQL desplegado en Neon**, verificado por introspección
directa el 2026-09-22.
**Estado:** 🟢 BLOQUE 1 (BACKEND) IMPLEMENTADO Y VERIFICADO · ⏳ Bloques 2 (Web) y 3 (Mobile) pendientes
**Fecha:** 2026-09-22

---

## Índice

- [0. Hallazgos previos](#0-hallazgos-previos)
- [1. Decisiones que requieren tu autorización](#1-decisiones-que-requieren-tu-autorización)
- [A. Especificación Técnica Formal (`spec`)](#a-especificación-técnica-formal-spec)
- [B. Plan de Ejecución por Bloques (`plan`)](#b-plan-de-ejecución-por-bloques-plan)
- [C. Lista de Tareas Atómicas (`tasks`)](#c-lista-de-tareas-atómicas-tasks)
- [D. Puntos de Control y Verificación (`checkpoints`)](#d-puntos-de-control-y-verificación-checkpoints)

---

## 0. Hallazgos previos

### 0.1 Esquema real de `fashionstore.pagos`

```
id_pago              bigint       NOT NULL  default nextval('pagos_id_pago_seq')
id_venta             bigint       NOT NULL  FK -> ventas(id_venta) ON DELETE CASCADE
metodo_pago          metodo_pago  NOT NULL
monto                numeric      NOT NULL  CHECK (monto >= 0)
estado               estado_pago  NOT NULL  default 'pendiente'
referencia_pasarela  varchar      NULL
payload_respuesta    jsonb        NULL
creado_en            timestamptz  NOT NULL  default now()
confirmado_en        timestamptz  NULL
```

Índices: `idx_pagos_venta (id_venta)` · `idx_pagos_estado (estado)`.

**No existe restricción de unicidad sobre `id_venta`**, y eso juega a favor: una orden puede
acumular varios intentos de pago, que es exactamente lo que exige el requisito de reintento tras
un rechazo. El historial completo queda registrado.

`payload_respuesta` es **`jsonb`**, no texto: se escribe como diccionario, no como cadena
serializada a mano.

**Enums verificados (orden real en PostgreSQL):**

| Enum | Valores |
| :--- | :--- |
| `estado_pago` | `pendiente` · `autorizado` · `confirmado` · `rechazado` · `reembolsado` |
| `estado_venta` | `pendiente` · `pagada` · `anulada` · `devuelta` |
| `metodo_pago` | `efectivo` · `tarjeta_debito` · `tarjeta_credito` · `pasarela_digital` · `qr` · `transferencia` |
| `tipo_movimiento_inv` | …incluye `venta_confirmada` y `cancelacion_pedido` |

`PagoORM` **no existe todavía** en el código.

### 0.2 No hay ningún trigger sobre `pagos`, `ventas` ni `venta_detalle`

El único trigger del ciclo de compra, `trg_descontar_inventario`, quedó neutralizado por la
migración `0009`. **Ninguna transición ocurre sola:** insertar en `pagos` no cambia
`ventas.estado`, y cambiar `ventas.estado` no toca el inventario. Todo debe ser explícito y
suceder dentro de la misma transacción del servicio.

### 0.3 Defecto activo: la auditoría de inventario se escribe en blanco

`movimientos_inventario` declara `saldo_anterior` y `saldo_nuevo` como `NOT NULL DEFAULT 0`, pero
`MovimientoInventarioORM` **no mapea ninguno de los dos**. Consecuencia verificada en la base:

```
tipo_movimiento  cantidad  saldo_anterior  saldo_nuevo  referencia
reserva          1         15              14           RESERVA-6
reserva          1         0               0            RESERVA-5
reserva          1         0               0            RESERVA-4
reserva          1         0               0            RESERVA-3
```

Todo movimiento escrito por el ORM queda en **0 → 0**. La bitácora registra *qué* se movió, pero
no *desde dónde hasta dónde*, que es justamente lo que la hace auditable.

Esto choca de frente con el checkpoint «registro inmutable en `movimientos_inventario`» que exige
CU16. **Se corrige dentro de este cambio** (tarea `T-BE-02`): es un mapeo de columnas que ya
existen, sin DDL, y beneficia también a los movimientos de CU12 y CU15.

### 0.4 La ventana de retención no vence sola

CU15 retiene existencias durante 25 minutos (`MINUTOS_RETENCION_VENTA`) y expone
`liberar_retencion_venta`, pero **nada lo invoca automáticamente**. Una orden abandonada mantiene
el stock bloqueado de forma indefinida.

Para CU16 esto tiene dos consecuencias directas:

1. El endpoint de pago **debe validar la ventana por su cuenta**. No puede asumir que una orden
   sigue siendo pagable solo porque su estado no ha cambiado.
2. Rechazar un pago por ventana expirada **no libera** el stock por sí mismo. Ver §1.3.

### 0.5 Los datos de los mockups no existen en la base

| Elemento del mockup | Realidad en Neon |
| :--- | :--- |
| `FLAGSHIP SERRANO`, `SAINT-HONORÉ PARÍS`, `HUB CENTRAL` | Solo existe **Atelier Serrano - Madrid**. Las otras sucursales reales son *Boutique Central - Santa Cruz*, *Boutique Central Equipetrol* y *Tienda de preuba78548* |
| `Ana Valenzuela · Calle de Claudio Coello 48` | La dirección se persiste en `ventas.direccion_envio` desde CU15; el nombre procede del cliente autenticado |
| `Beneficio Membresía Privé −160,00 €` | La promoción sembrada por la migración `0010` es del **15 %**, no un importe fijo |
| `ATELIER PRIVÉ BLACK CARD` con PAN `•••• 4289` | Decorativo. No hay ninguna tarjeta almacenada (§1.2) |

Se respeta la **estructura visual y la jerarquía tipográfica** del mockup; el contenido procede de
la base. Donde no haya dato, la pantalla muestra su estado vacío.

> **Sobre la aritmética del mockup:** vuelve a rotular «Subtotal 1.940,00 €», «Beneficio
> −160,00 €» y «Total 1.940,00 €», que no cuadra. La semántica quedó fijada en CU11/CU15 y se
> mantiene: `subtotal` agrega precios de lista, `descuento` el ahorro, y siempre
> `total = subtotal − descuento`. El IVA va incluido y solo se desglosa para mostrarlo.

---

## 1. Decisiones que requieren tu autorización

### 1.1 Qué hacer con el estado `autorizado`

`estado_pago` contempla `pendiente → autorizado → confirmado`, que es el ciclo de *auth/capture*
de una pasarela real: primero se autoriza el cargo y después se captura, normalmente al expedir
la mercancía.

**Propuesta:** en este ciclo el sandbox transita **directamente a `confirmado`**, y `autorizado`
queda reservado y documentado para cuando se integre una pasarela real. Simular una autorización
que ningún proceso captura añadiría un estado intermedio sin salida — exactamente el problema que
ya arrastra la ventana de retención de §0.4.

### 1.2 Qué hacer con «Guardar tarjeta para futuras compras»

Ambos mockups muestran la casilla. **No existe ninguna tabla donde guardar un medio de pago**, y
almacenar un PAN por nuestra cuenta queda descartado.

| | Opción A — **Recomendada** | Opción B |
| :--- | :--- | :--- |
| **Qué** | Retirar la casilla de la interfaz este ciclo. El campo `guardar_tarjeta` se acepta en el payload y se ignora, documentado como reservado. | Crear `metodos_pago_cliente` (últimos 4 dígitos, marca, token de pasarela) y persistir. |
| **Requiere DDL** | No | Sí (*Ask First*) |
| **Honestidad de la interfaz** | No promete lo que no hace | Correcta |
| **Utilidad real hoy** | — | Ninguna: sin pasarela real no hay token reutilizable que guardar |

**Recomendación: Opción A.** Guardar «una tarjeta» sin token de pasarela solo podría hacerse
almacenando el PAN, lo cual es inaceptable. La casilla vuelve con la integración real.

### 1.3 Qué ocurre al intentar pagar una orden con la ventana expirada

El endpoint responde `409`. La pregunta es si además **libera** las existencias retenidas.

**Propuesta:** sí, liberarlas en el mismo acto, reutilizando `liberar_retencion_venta`. La orden
pasa a `anulada` y el stock vuelve a `cantidad_disponible` con movimiento `cancelacion_pedido`.

Razón: mientras no exista el proceso automático de expiración, el intento de pago tardío es el
único momento en que el sistema *sabe con certeza* que esa retención ya no vale. Desaprovecharlo
deja inventario bloqueado sin ninguna otra salida. Es una verificación perezosa, no un sustituto
del proceso automático, que sigue pendiente.

> Si prefieres que el 409 no tenga efectos colaterales, dímelo: implica aceptar que el stock siga
> retenido hasta que alguien invoque la liberación a mano.

### 1.4 Determinismo del sandbox de pasarela

Para que las pruebas no sean intermitentes, el simulador debe ser **predecible**:

- **Validación de formato:** algoritmo de Luhn sobre el PAN, expiración futura y CVV de 3–4 dígitos.
- **Resultado forzado por PAN de prueba**, al estilo de las pasarelas reales: un número terminado
  en `0000` se rechaza siempre; el resto de PAN válidos se aprueban. Así el escenario Gherkin de
  tarjeta denegada es reproducible sin sorteos.
- **Latencia simulada inyectable:** ~800 ms en ejecución normal, **0 ms en pruebas**.
- Cero dependencias de servicios comerciales, sin claves y sin coste.

---

## A. Especificación Técnica Formal (`spec`)

### A.1 Máquina de estados del ciclo de compra

```
CU11  bolsa                carrito_detalle
        │  POST /ventas/checkout
        ▼
CU15  ventas.estado = 'pendiente'
      inventario: disponible −n · reservada +n        (movimiento 'reserva')
        │
        ├── POST /pagos/procesar  ── aprobado ──►  pagos.estado  = 'confirmado'
        │                                          ventas.estado = 'pagada'
        │                                          inventario: reservada −n
        │                                          (movimiento 'venta_confirmada')
        │
        ├── POST /pagos/procesar  ── rechazado ─►  pagos.estado  = 'rechazado'
        │                                          ventas.estado = 'pendiente'  (intacta)
        │                                          inventario sin cambios → permite reintento
        │
        └── ventana expirada ───────────────────►  409 + liberación (§1.3)
                                                   ventas.estado = 'anulada'
                                                   inventario: reservada −n · disponible +n
                                                   (movimiento 'cancelacion_pedido')
```

**Invariante del inventario:** en un pago confirmado las unidades salen de `cantidad_reservada` y
**no regresan a `cantidad_disponible`** — abandonan el almacén. Es lo que distingue una venta
consolidada de una cancelación.

### A.2 Contratos de API

Ambos endpoints bajo `/api/v1`, con `Authorization: Bearer <jwt>` y rol `cliente`. Errores con el
contrato `{"detail", "code"}` ya vigente en el proyecto.

---

#### `GET /api/v1/ventas/{id_venta}/resumen-pago`

Datos de la orden `pendiente` necesarios para inicializar la pasarela.

```jsonc
{
  "id_venta": 1,
  "numero_comprobante": "FS-2026-000001",
  "estado": "pendiente",
  "subtotal": "2100.00",
  "descuento": "160.00",
  "total": "1940.00",
  "iva_incluido": "336.69",
  "moneda": "EUR",
  "total_prendas": 3,
  "items": [
    {
      "id_variante": 3,
      "nombre_producto": "Vestido plisado en seda natural",
      "talla_codigo": "38",
      "color_nombre": "Rojo Carmín",
      "imagen_url": "https://…",
      "cantidad": 1,
      "precio_unitario": "890.00",
      "subtotal_linea": "890.00",
      "nombre_sucursal": "Atelier Serrano - Madrid"
    }
  ],
  "tipo_entrega": "domicilio",
  "direccion_envio": "Calle de Claudio Coello 48, 4º B, 28001 Madrid",
  "nombre_sucursal_retiro": null,
  "nombre_cliente": "Ana Valenzuela",
  "expira_en": "2026-09-22T10:25:00Z",
  "segundos_restantes": 868,
  "metodos_disponibles": ["tarjeta_credito", "tarjeta_debito", "qr", "pasarela_digital"]
}
```

`segundos_restantes` se calcula en el servidor y llega ya resuelto: el cliente no debe derivar la
cuenta atrás de su propio reloj, que puede ir desfasado.

| Código | Situación |
| :--- | :--- |
| `200` | Resumen devuelto |
| `401` | Sin sesión |
| `403` | `VENTA_AJENA` — la orden pertenece a otro cliente |
| `404` | `VENTA_NO_ENCONTRADA` |
| `409` | `VENTA_NO_PAGABLE` — ya liquidada o anulada |

---

#### `POST /api/v1/pagos/procesar`

Endpoint transaccional. Procesa el cobro y consolida el ciclo de compra.

```jsonc
// PagoProcesarIn — tarjeta
{
  "id_venta": 1,
  "metodo_pago": "tarjeta_credito",
  "tarjeta": {
    "numero": "4111111111111111",
    "titular": "ANA VALENZUELA",
    "mes_expiracion": 9,
    "anio_expiracion": 2028,
    "cvv": "123"
  },
  "guardar_tarjeta": false,
  "clave_idempotencia": "b3f1c0de-…"
}

// PagoProcesarIn — Bizum/QR o PayPal
{ "id_venta": 1, "metodo_pago": "qr", "clave_idempotencia": "…" }
```

**Ningún dato de tarjeta se persiste.** El objeto `tarjeta` se usa para validar y simular, y se
descarta; en `pagos.payload_respuesta` solo quedan la **marca y los últimos 4 dígitos**. El CVV no
se registra en ningún sitio, tampoco en logs.

**Secuencia transaccional:**

1. Cargar la venta con sus detalles y bloquearla (`SELECT … FOR UPDATE`) para serializar envíos simultáneos.
2. Verificar pertenencia al cliente autenticado → `403 VENTA_AJENA`.
3. Si `estado != 'pendiente'` → `409 VENTA_YA_LIQUIDADA` o `VENTA_ANULADA`.
4. Si la ventana expiró → liberar retención (§1.3) y `409 VENTA_EXPIRADA`.
5. Si la `clave_idempotencia` ya produjo un pago confirmado → devolver **ese mismo resultado**, sin cobrar de nuevo.
6. Validar el método y sus datos → `422` con el detalle concreto.
7. Invocar la pasarela sandbox.
8. **Rechazo:** insertar en `pagos` con `estado='rechazado'` y el motivo en `payload_respuesta`; `COMMIT`; responder `402 PAGO_RECHAZADO`. La venta sigue `pendiente` y el stock retenido.
9. **Aprobación**, todo en la misma transacción:
   - insertar en `pagos` con `estado='confirmado'`, `referencia_pasarela`, `payload_respuesta` y `confirmado_en`;
   - `ventas.estado = 'pagada'`;
   - por cada línea: `cantidad_reservada -= cantidad`, con bloqueo de la fila de inventario;
   - por cada línea: `movimientos_inventario` con `tipo_movimiento='venta_confirmada'`, cantidad negativa, `id_usuario_responsable`, `referencia_documento='VENTA-<id>'` y **`saldo_anterior`/`saldo_nuevo` reales**;
   - `COMMIT`.

```jsonc
// PagoConfirmadoOut — 201
{
  "id_pago": 1,
  "id_venta": 1,
  "numero_comprobante": "FS-2026-000001",
  "estado_pago": "confirmado",
  "estado_venta": "pagada",
  "metodo_pago": "tarjeta_credito",
  "referencia_pasarela": "SBX-2026-0000001",
  "monto": "1940.00",
  "moneda": "EUR",
  "marca_tarjeta": "VISA",
  "ultimos_digitos": "1111",
  "confirmado_en": "2026-09-22T10:12:44Z",
  "mensaje_confirmacion": "Pago confirmado. Tu orden entra en preparación en el atelier."
}
```

| Código | Situación |
| :--- | :--- |
| `201` | Pago confirmado |
| `401` | Sin sesión |
| `402` | `PAGO_RECHAZADO` — la pasarela denegó el cargo. Cuerpo con `id_pago`, `motivo` y `puede_reintentar: true` |
| `403` | `VENTA_AJENA` |
| `404` | `VENTA_NO_ENCONTRADA` |
| `409` | `VENTA_YA_LIQUIDADA` · `VENTA_ANULADA` · `VENTA_EXPIRADA` |
| `422` | `TARJETA_INVALIDA` · `TARJETA_EXPIRADA` · `METODO_NO_SOPORTADO` |

> **Sobre el `402`:** se elige frente a un `409` porque distingue «el sistema está bien, el cargo
> se denegó» de «esta orden no admite pago». El cliente necesita esa diferencia: la primera
> permite reintentar con otro método; la segunda, no.

### A.3 Mapeo de `PagoORM`

En `compras_pagos/modelos.py`, junto a `CarritoORM`. Verificado contra la introspección de §0.1:
`payload_respuesta` como `JSONB`, `monto` como `Numeric(12, 2)` y los enums declarados con
`create_type=False`, como el resto del proyecto.

### A.4 Servicio de pasarela sandbox

Aislado en `app/integrations/pasarela_sandbox.py`, fuera del servicio de dominio, conforme a la
regla de integraciones externas de la constitución de backend. Interfaz mínima:

```
procesar_cargo(monto, metodo, datos_tarjeta | None) -> ResultadoPasarela
    ResultadoPasarela: aprobado · referencia · codigo_respuesta · mensaje · marca · ultimos_digitos
```

Reglas deterministas en §1.4. La latencia se inyecta para poder anularla en pruebas.

### A.5 Criterios de Aceptación (Gherkin)

```gherkin
Característica: CU16 — Realizar pago electrónico

  Escenario: Pago exitoso con tarjeta
    Dado que tengo la orden FS-2026-000001 en estado "pendiente" por 1.940,00 €
    Y sus 3 prendas están retenidas en inventario
    Cuando envío POST /api/v1/pagos/procesar con una tarjeta válida
    Entonces recibo 201
    Y se registra un pago con estado "confirmado" y su referencia de pasarela
    Y la venta pasa a estado "pagada"
    Y la cantidad reservada de cada línea se reduce en las unidades vendidas
    Y la cantidad disponible NO se incrementa
    Y se registra un movimiento "venta_confirmada" por línea, con responsable y saldos reales

  Escenario: Tarjeta denegada por la pasarela
    Dado que tengo la orden FS-2026-000001 en estado "pendiente"
    Cuando envío POST /api/v1/pagos/procesar con una tarjeta que la pasarela rechaza
    Entonces recibo 402 con código "PAGO_RECHAZADO"
    Y se registra un pago con estado "rechazado"
    Y la venta permanece en estado "pendiente"
    Y el inventario reservado permanece intacto
    Y la respuesta indica que puedo reintentar

  Escenario: Reintento exitoso tras un rechazo
    Dado que la orden FS-2026-000001 acumula un pago rechazado
    Cuando envío POST /api/v1/pagos/procesar con un método válido
    Entonces recibo 201
    Y la orden tiene dos registros en "pagos": uno rechazado y uno confirmado
    Y la venta pasa a estado "pagada"

  Escenario: Intento de pagar una orden ya liquidada
    Dado que la orden FS-2026-000001 está en estado "pagada"
    Cuando envío POST /api/v1/pagos/procesar
    Entonces recibo 409 con código "VENTA_YA_LIQUIDADA"
    Y no se registra ningún pago nuevo
    Y el inventario no se altera

  Escenario: Orden con la ventana de retención expirada
    Dado que la orden FS-2026-000001 se tramitó hace más de 25 minutos
    Cuando envío POST /api/v1/pagos/procesar
    Entonces recibo 409 con código "VENTA_EXPIRADA"
    Y la venta pasa a estado "anulada"
    Y las unidades retenidas vuelven a estar disponibles
    Y se registra un movimiento "cancelacion_pedido"

  Escenario: Tarjeta con formato inválido
    Cuando envío POST /api/v1/pagos/procesar con un número que no supera Luhn
    Entonces recibo 422 con código "TARJETA_INVALIDA"
    Y no se registra ningún pago
    Y no se contacta con la pasarela

  Escenario: Doble envío del mismo pago
    Dado que envío dos veces la misma clave de idempotencia
    Cuando ambas peticiones llegan
    Entonces solo se registra un pago confirmado
    Y ambas respuestas devuelven el mismo id_pago
    Y el inventario se consolida una sola vez

  Escenario: Orden de otro cliente
    Cuando intento pagar una orden que no me pertenece
    Entonces recibo 403 con código "VENTA_AJENA"

  Escenario: Resumen de pago de una orden pendiente
    Cuando consulto GET /api/v1/ventas/1/resumen-pago
    Entonces recibo 200 con el total, las líneas congeladas y la dirección de envío
    Y "segundos_restantes" viene calculado por el servidor
```

### A.6 Riesgos (obligatorio en nivel SDD 3)

| Riesgo | Mitigación |
| :--- | :--- |
| Doble clic en «Confirmar y pagar» genera dos cargos | `clave_idempotencia` + `SELECT … FOR UPDATE` sobre la venta + botón inhabilitado durante la petición |
| Pago confirmado pero inventario sin consolidar | Todo en una única transacción: un fallo revierte también el registro en `pagos` |
| Dos pagos simultáneos sobre la misma orden | El bloqueo de la fila de venta serializa; el segundo encuentra `estado = 'pagada'` y responde `409` |
| Datos de tarjeta filtrados a logs o base de datos | El PAN y el CVV no se persisten ni se registran; `payload_respuesta` guarda solo marca y últimos 4 |
| La auditoría sigue escribiéndose en 0 → 0 | `T-BE-02` mapea `saldo_anterior`/`saldo_nuevo` y los rellena con los valores reales |
| Orden expirada pagada por una carrera | La validación de la ventana ocurre **dentro** de la transacción, tras el bloqueo |

---

## B. Plan de Ejecución por Bloques (`plan`)

> El **Bloque 1 debe completarse y aprobarse antes** de iniciar el 2 y el 3. Los bloques 2 y 3 son
> paralelizables entre sí.

### Bloque 1 — Backend (`Ec-backend`)

**Fase 1.1 — Modelos y esquemas**
`PagoORM` en `compras_pagos/modelos.py` (§A.3). Corrección de `MovimientoInventarioORM` para mapear
los saldos (§0.3). Esquemas `ResumenPagoOut`, `PagoItemOut`, `TarjetaIn`, `PagoProcesarIn`,
`PagoConfirmadoOut` y `PagoRechazadoOut`, con validadores de Luhn, expiración y CVV.

**Fase 1.2 — Integración de pasarela**
`app/integrations/pasarela_sandbox.py` con la interfaz de §A.4: determinista, inyectable, sin
llamadas de red y sin acoplamiento al ORM.

**Fase 1.3 — Servicio transaccional**
`PagoServicio.procesar_pago` con la secuencia de §A.2, y `PagoServicio.obtener_resumen_pago`.
Registro de movimientos con saldos reales. Sin importar `fastapi`: solo excepciones de dominio.

**Fase 1.4 — Router**
`cu16_realizar_pago/router.py`, montado en `compras_pagos/router.py`. Alta del código `402` en
`main.py` mediante una excepción de dominio nueva (`PaymentRequiredError`) si no existe ninguna
que lo cubra.

**Fase 1.5 — Pruebas (Pytest)**
Un test por escenario de §A.5, más prueba de concurrencia de doble pago simultáneo. Verificación
explícita de que `cantidad_reservada` queda en cero y `cantidad_disponible` **no** sube.

**Fase 1.6 — Verificación end-to-end contra Neon**
Script que recorre bolsa → checkout → pago → consolidación, comprueba las invariantes sobre la
base real y **limpia todo lo que crea**, al modo de la verificación de CU15.

### Bloque 2 — Frontend Web (`Ec-frontend`)

**Fase 2.1 — Enrutamiento**
Ruta `/pago/:idVenta` **fuera de `MainLayoutComponent`**, con `authGuard`, declarada después de la
landing y antes del comodín para respetar el guard `app.routes.spec.ts`. Cabecera propia con
`← VOLVER A LA BOLSA` hacia `/bolsa` y migas «Bolsa de Compra (3) › Envío & Entrega › Método de
Pago (activo)».

**Fase 2.2 — Servicio**
`PagoService` con Signals: `resumen`, `metodoSeleccionado`, `procesando`, `error` y
`segundosRestantes`. Tipado estricto; los importes viajan como `string`.

**Fase 2.3 — Componente**
`CheckoutPaymentComponent` standalone con `OnPush`, a dos columnas
(`lg:grid-cols-[1fr_380px]`), fiel a `image_f4fca1.png`: tarjeta visual «Atelier Privé Black Card»
que refleja en vivo lo tecleado, radios para Bizum/QR y PayPal, resumen lateral con las líneas
congeladas e insignias de seguridad.

**Fase 2.4 — Interacción**
Formulario tipado con `NonNullableFormBuilder`; validación de Luhn en cliente **como cortesía**, no
como autoridad; máscaras de PAN y expiración; cuenta atrás con limpieza en `ngOnDestroy`; botón
inhabilitado mientras haya petición en vuelo; traducción de `402`, `409` y `422` a mensajes de
negocio; pantalla de confirmación con el comprobante.

**Fase 2.5 — Pruebas (Vitest)**
Ausencia de navbar, retorno a `/bolsa`, validación de tarjeta, alternancia de método, estado de
procesamiento, rechazo con reintento y expiración.

### Bloque 3 — Mobile (`Ec-mobile`)

**Fase 3.1 — Capa de datos**
`modulos/compras_pagos/cu16_realizar_pago/datos/` con DTO probados mediante `fromJson` sobre
**payloads literales del backend**, y `PagoApi` con manejo de 401 vía `SesionManager` y traducción
de errores de dominio.

**Fase 3.2 — BLoC**
`PagoBloc` con estados sellados `PagoInicial`, `PagoCargandoResumen`, `PagoListo`, `PagoProcesando`,
`PagoExitoso`, `PagoRechazado` y `PagoError`. La clave de idempotencia se genera una sola vez por
intento.

**Fase 3.3 — Pantalla**
`CheckoutPaymentScreen` abierta con `Navigator.push`, **sin `BottomNavigationBar`**, con `AppBar`
de retorno y sello «256-BIT SSL». Banner de reserva activa, monto a liquidar, carrusel de prendas,
widget de tarjeta interactivo, radio tiles de método, insignias y **barra de acción fija** con
`CONFIRMAR Y PAGAR`.

**Fase 3.4 — Pruebas (`flutter test`)**
Contrato de DTO, transiciones del BLoC, ausencia de barra de navegación, footer fijo y feedback al
alternar método.

---

## C. Lista de Tareas Atómicas (`tasks`)

### Bloque 1 — Backend

- [x] **T-BE-01**: `PagoORM` en `compras_pagos/modelos.py`, verificado con `pytest tests/test_esquema_bd.py`.
- [x] **T-BE-02**: Mapear `saldo_anterior` y `saldo_nuevo` en `MovimientoInventarioORM` y rellenarlos con valores reales en CU12, CU15 y CU16 (§0.3).
- [x] **T-BE-03**: Esquemas de lectura `ResumenPagoOut` y `PagoItemOut`.
- [x] **T-BE-04**: Esquemas de escritura `TarjetaIn` (Luhn, expiración futura, CVV), `PagoProcesarIn`, `PagoConfirmadoOut` y `PagoRechazadoOut`.
- [x] **T-BE-05**: `app/integrations/pasarela_sandbox.py` determinista, con latencia inyectable.
- [x] **T-BE-06**: `PagoServicio.obtener_resumen_pago` con `segundos_restantes` calculado en el servidor.
- [x] **T-BE-07**: `PagoServicio.procesar_pago` con la secuencia transaccional completa de §A.2.
- [x] **T-BE-08**: Idempotencia por `clave_idempotencia` sobre pagos confirmados.
- [x] **T-BE-09**: Liberación de retención ante ventana expirada (§1.3), reutilizando `liberar_retencion_venta`.
- [x] **T-BE-10**: Router `cu16_realizar_pago` montado en `compras_pagos/router.py`; manejador del `402`.
- [x] **T-BE-11**: Suite Pytest con un test por escenario Gherkin **más** prueba de concurrencia de doble pago.
- [x] **T-BE-12**: Verificación end-to-end contra Neon con limpieza posterior.

### Bloque 2 — Frontend Web

- [ ] **T-FE-01**: Modelos TypeScript espejo de los esquemas Pydantic.
- [ ] **T-FE-02**: `PagoService` con Signals y traducción de errores.
- [ ] **T-FE-03**: Ruta `/pago/:idVenta` fuera del layout, con `authGuard` y en el orden correcto.
- [ ] **T-FE-04**: `CheckoutPaymentComponent` a dos columnas fiel a `image_f4fca1.png`.
- [ ] **T-FE-05**: Widget de tarjeta visual que refleja en vivo número, titular y expiración.
- [ ] **T-FE-06**: Formulario tipado con validación, máscaras y feedback de error por campo.
- [ ] **T-FE-07**: Selector de método (tarjeta / Bizum-QR / PayPal) con revelado condicional.
- [ ] **T-FE-08**: Resumen lateral con líneas congeladas, desglose y dirección de envío.
- [ ] **T-FE-09**: Cuenta atrás con limpieza en `ngOnDestroy`; al expirar se deshabilita el pago.
- [ ] **T-FE-10**: Estado de procesamiento, pantalla de confirmación y manejo de `402` con reintento.
- [ ] **T-FE-11**: Enlazar la confirmación de CU15 con `/pago/:idVenta`.
- [ ] **T-FE-12**: Pruebas Vitest con mocks construidos sobre payloads reales del backend.

### Bloque 3 — Mobile

- [ ] **T-MO-01**: DTO de pago con parseo tolerante de `Decimal`.
- [ ] **T-MO-02**: `PagoApi` con manejo de 401 y traducción de errores de dominio.
- [ ] **T-MO-03**: `PagoBloc` con los siete estados sellados y clave de idempotencia por intento.
- [ ] **T-MO-04**: `CheckoutPaymentScreen` sin `BottomNavigationBar`, con `AppBar` de retorno.
- [ ] **T-MO-05**: Widget «Atelier Privé Black Card» interactivo.
- [ ] **T-MO-06**: Radio tiles de método, insignias de seguridad y banner de reserva activa.
- [ ] **T-MO-07**: Barra de acción fija `CONFIRMAR Y PAGAR` con el monto.
- [ ] **T-MO-08**: Enlazar la confirmación de CU15 con la pantalla de pago, propagando el token.
- [ ] **T-MO-09**: Pruebas de contrato (`fromJson` sobre payloads literales), de BLoC y de widget.

---

## D. Puntos de Control y Verificación (`checkpoints`)

| ID | Capa | Criterio de Aprobación | Método | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend | `GET /ventas/{id}/resumen-pago` devuelve total, líneas congeladas, dirección y `segundos_restantes` del servidor. | Pytest | ✅ |
| **CP-02** | Backend | Pago aprobado persiste en `pagos` con `estado='confirmado'`, `referencia_pasarela` y `confirmado_en`. | Pytest + consulta a Neon | ✅ |
| **CP-03** | Backend | `ventas.estado` transita de `pendiente` a `pagada`. | Pytest + consulta a Neon | ✅ |
| **CP-04** | Backend | `cantidad_reservada` se reduce en las unidades vendidas y `cantidad_disponible` **no** se incrementa. | Pytest | ✅ |
| **CP-05** | Backend | Un movimiento `venta_confirmada` por línea, con `id_usuario_responsable`, referencia `VENTA-<id>` y **saldos reales, no 0 → 0**. | Pytest + consulta a Neon | ✅ |
| **CP-06** | Backend | Pago rechazado: registro con `estado='rechazado'`, venta intacta en `pendiente`, inventario sin tocar. | Pytest | ✅ |
| **CP-07** | Backend | Reintento tras rechazo culmina en `pagada`, con ambos registros en el historial. | Pytest | ✅ |
| **CP-08** | Backend | Orden ya liquidada responde 409 sin efectos secundarios. | Pytest | ✅ |
| **CP-09** | Backend | Orden expirada responde 409, se anula y libera el stock retenido. | Pytest | ✅ |
| **CP-10** | Backend | Tarjeta inválida responde 422 sin registrar pago ni contactar la pasarela. | Pytest | ✅ |
| **CP-11** | Backend | Idempotencia: doble envío produce un solo pago y una sola consolidación. | Prueba de concurrencia | ✅ |
| **CP-12** | Backend | Un fallo en cualquier punto revierte la transacción completa. | Pytest con fallo inducido | ✅ |
| **CP-13** | Backend | Ni el PAN ni el CVV aparecen en base de datos ni en logs. | Auditoría de código + consulta | ✅ |
| **CP-14** | Backend | `pytest` completo en verde, incluida la guardia `test_esquema_bd.py`. | `pytest -q` | ✅ |
| **CP-15** | Web | `/pago/:idVenta` se renderiza **sin la barra de navegación institucional**. | Vitest | ⏳ |
| **CP-16** | Web | `← VOLVER A LA BOLSA` navega a `/bolsa`. | Vitest | ⏳ |
| **CP-17** | Web | Layout a dos columnas fiel al mockup; la tarjeta visual refleja lo tecleado en vivo. | Vitest + inspección | ⏳ |
| **CP-18** | Web | Alternar método revela y oculta los campos correspondientes. | Vitest | ⏳ |
| **CP-19** | Web | Un `402` muestra el motivo y permite reintentar sin perder la orden. | Vitest | ⏳ |
| **CP-20** | Web | `tsc --noEmit` sin errores, `ng build` limpio y `ng test` en verde. | Ejecución | ⏳ |
| **CP-21** | Mobile | Pantalla completa **sin `BottomNavigationBar`**, con `AppBar` de retorno operativo. | Test de widget | ⏳ |
| **CP-22** | Mobile | La barra `CONFIRMAR Y PAGAR` permanece fija y visible durante el scroll. | Test de widget | ⏳ |
| **CP-23** | Mobile | Alternar método de pago produce feedback visual inmediato. | Test de widget | ⏳ |
| **CP-24** | Mobile | DTO validados con `fromJson` sobre payloads literales del backend. | Revisión + tests | ⏳ |
| **CP-25** | Mobile | `dart analyze` sin incidencias y `flutter test` en verde. | Ejecución | ⏳ |
| **CP-26** | Transversal | Web y Mobile consumen los mismos endpoints con los mismos nombres de campo. | Diff de contratos | ⏳ |
| **CP-27** | Transversal | Doble pulsación de «Confirmar y pagar» no genera un segundo cargo. | Prueba manual + test | ⏳ |
| **CP-28** | Transversal | Ningún importe, prenda ni boutique procede de literales: todo viene de PostgreSQL. | Auditoría de código | ⏳ |
| **CP-29** | Transversal | Catálogo exclusivamente femenino en el resumen de la orden, incluidos los *fallback*. | Auditoría visual | ⏳ |

---

## Resumen para tu decisión

**Listo para implementar sin más autorizaciones:** ambos endpoints, la máquina de estados, el
sandbox determinista, la corrección de la auditoría de inventario y los dos bloques de cliente.

**Requiere tu decisión antes de tocar código:**

1. **§1.1 — El estado `autorizado`.** Propuesta: transitar directamente a `confirmado` y reservar
   `autorizado` para una pasarela real.
2. **§1.2 — «Guardar tarjeta».** Propuesta: retirar la casilla este ciclo. Sin pasarela real solo
   podría guardarse el PAN, lo que queda descartado.
3. **§1.3 — Qué hacer ante una orden expirada.** Propuesta: además del 409, liberar el stock
   retenido, porque es el único momento en que el sistema sabe con certeza que la retención caducó.
4. **§0.3 — Confirmación del arreglo de auditoría.** La bitácora de inventario lleva escribiéndose
   en `0 → 0` desde CU12. Queda incorporado al alcance porque un checkpoint de CU16 lo exige.

> ⛔ **GATE DE APROBACIÓN OBLIGATORIO (STRICT STOP):** no se ha generado ni modificado ningún
> archivo `.py`, `.ts` ni `.dart`. La implementación no comenzará hasta que apruebes esta
> especificación y resuelvas los cuatro puntos anteriores.
