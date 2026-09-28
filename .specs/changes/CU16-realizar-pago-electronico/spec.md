# Especificación Técnica Formal: Realizar Pago Electrónico

**ID del Cambio:** `CU16-realizar-pago-electronico`
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
**Estado:** 🟢 Bloques 1 (Backend), 2 (Web) y 3 (Mobile) implementados y verificados (ronda 1) ·
🟢 Ronda 2 (2026-09-28) completa: migración de tarjeta en crudo a tokens de Stripe en los tres
bloques (ver §A.2, `tasks.md`). Pendiente de decisión: webhook de Stripe (fuera de esta ronda).
**Fecha:** 2026-09-22 (ronda 1) · 2026-09-28 (ronda 2, tokenización)

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

### 0.6 Mockups ampliados recibidos el 2026-09-27 (Web y Mobile, con estados expandidos)

Se recibieron cuatro capturas adicionales, más detalladas que `image_f4fca1.png`/`image_f4fcc0.png`,
que amplían el alcance visual de la pantalla de pago. Se documentan aquí como nueva fuente de
verdad visual; **no se ha escrito ni modificado ningún archivo de código a partir de ellas** —
solo se actualiza la documentación de `plan.md`, `tasks.md` y `checkpoint.md`.

**Punto de entrada confirmado:** la navegación ya está resuelta en el código existente.
`BolsaCompraComponent.tramitarPedido()` (`bolsa-compra.component.ts:185-192`) invoca
`this.router.navigate(['/pago', venta.id_venta])` en cuanto `POST /ventas/checkout` responde `201`.
Es decir: esta pantalla se despliega **inmediatamente después de pulsar «TRAMITAR PEDIDO» en la
Bolsa de Compra (CU11)**, sin pantalla intermedia de confirmación. Lo único que falta para que esa
navegación funcione es registrar la ruta `/pago/:idVenta` en `app.routes.ts` (`T-FE-03`) — hoy
inexistente, que es la causa del error `NG04002: Cannot match any routes. URL Segment: 'pago/1'`
observado en la suite de Vitest.

**Anatomía nueva respecto a la spec original (§A.2):**

| Elemento nuevo | Dónde aparece | Detalle |
| :--- | :--- | :--- |
| Migas de progreso con contador de reserva | Web, barra bajo la cabecera | `BOLSA DE COMPRA (n) › ENVÍO & ENTREGA › MÉTODO DE PAGO (activo)` junto a `Reserva activa: mm:ss restantes \| <sucursales de expedición>`. El contador es el mismo `segundos_restantes` de `ResumenPagoOut`, ya contemplado en la spec original — solo cambia dónde se pinta. |
| Banner de reserva + carrusel de prendas | Mobile, bajo el `AppBar` | Banner color crema `Reserva activa: mm:ss restantes \| FLAGSHIPS ACTIVAS`, monto total con ícono de bolsa, línea de entrega (`Entrega: <cliente> · <dirección truncada>` con badge `PRIORITY`) y un carrusel horizontal de miniaturas circulares de las prendas de la orden. |
| **Tercer método de pago: «Pago en efectivo en sucursal»** | Web y Mobile | Badge `EN TIENDA` / tarjeta expandida `LIQUIDACIÓN PRESENCIAL`: reserva las prendas y liquida en caja física en la boutique de recogida. El mockup rotula «48h», pero la ventana real decidida es de **24 horas** (§1.5.2) — el texto de la interfaz debe corregirse para no prometer un plazo distinto al implementado. Solo se ofrece cuando `tipo_entrega: recogida_boutique` (§1.6.2). **No estaba contemplado en `A.2` ni en el enum `MetodoPago` de TypeScript**, aunque el valor `efectivo` ya existe en el enum `metodo_pago` de PostgreSQL (§0.1) — no requiere DDL, solo extender el contrato de cliente. Diseño completo resuelto en §1.5.2 y §1.6; sigue sin implementarse (`T-FE-15`/`T-MO-12`). |
| Vista expandida de Bizum/Código QR | Web y Mobile | Al seleccionar la opción, se pinta un QR real, su propia cuenta atrás de expiración (`Expira en: 04:59`, independiente de `segundos_restantes` de la venta) y tres instrucciones numeradas: abrir la app bancaria/Bizum, escanear o teclear un código corto (`#ATEL-9402` en el mock) e importar el monto exacto. |
| Checkbox «Guardar tarjeta para futuras compras» | Web y Mobile | Aparecía marcada por defecto en ambos mockups nuevos, contradiciendo la Opción A ya aprobada en §1.2. **Se descarta definitivamente** (§1.5.1): ningún cliente la muestra. |
| Resumen de orden con línea de financiación | Web, columna derecha | `o en 3 plazos de 646,66 € sin intereses con Atelier Pay`. Es la misma etiqueta decorativa «Atelier Pay» ya usada en CU07 para cuotas — **no existe ninguna integración de financiación real** ni tabla de plazos. Se mantiene como texto informativo, no como funcionalidad a implementar. |
| Línea de envío/sastrería en el desglose | Web, columna derecha | `Envío asegurado con guante blanco: GRATUITO` y `Ajuste de sastrería de cortesía: INCLUIDO`. Son etiquetas de valor de marca sin cargo asociado — no alteran `subtotal`/`descuento`/`total` (§A.2 de CU11/CU15). |
| Insignias de seguridad y nota de empaquetado | Web y Mobile, pie del formulario | `SSL 256-BIT` · `PCI-DSS NIVEL 1` · `GARANTÍA ATELIER` (devolución 30 días) + texto sobre empaquetado con guante blanco. Puramente decorativo/informativo, sin lógica asociada. |

> **Nota de honestidad de datos:** igual que en §0.5, todo boutique, prenda, precio y dirección de
> estas pantallas debe proceder de `ResumenPagoOut` (ya especificado en `A.2`). Los elementos de
> la tabla anterior que son puramente informativos (financiación, insignias, empaquetado) no
> implican ninguna consulta nueva a la base; los que sí muestran datos reales (prendas, sucursal,
> dirección, cliente, cuenta atrás) ya estaban cubiertos por el contrato existente.

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

### 1.5 «Guardar tarjeta» y pago en efectivo en sucursal — resuelto el 2026-09-27

Las dos preguntas abiertas por los mockups ampliados de §0.6 quedan decididas así:

#### 1.5.1 «Guardar tarjeta»: descartada

**Se descarta el checkbox por completo**, tanto en Web como en Mobile. Se confirma la Opción A ya
recomendada en §1.2: la interfaz **no** muestra la casilla «Guardar tarjeta para futuras compras»
en ningún mockup, presente o futuro, de este ciclo. El campo `guardar_tarjeta` se conserva en
`PagoProcesarIn` únicamente por compatibilidad de contrato (aceptado y ya siempre ignorado por el
servidor), pero ningún componente de cliente lo expone ni lo envía. Queda retirado también de la
Fase 2.3/3.3 de `plan.md` y de las tareas `T-FE-14`/`T-MO-11` de `tasks.md`.

#### 1.5.2 Pago en efectivo en sucursal: Opción A, con ventana propia de 24 horas

**Se adopta la Opción A**: `POST /pagos/procesar` con `metodo_pago: "efectivo"` inserta un pago en
`estado='pendiente'` (no `confirmado`) y la venta permanece `pendiente`. La confirmación real
ocurre después, cuando el cliente se presenta en la boutique y paga en efectivo, y la registra un
cajero.

**Dos ventanas de tiempo distintas y no confundibles, ambas medidas desde `ventas.fecha_venta`:**

| Ventana | Duración | Qué protege | Dónde se define |
| :--- | :--- | :--- | :--- |
| Retención de la bolsa (CU15) | **25 minutos** | El tiempo prudente para que el cliente complete el checkout desde que tramita el pedido — es la ventana ya vigente de `MINUTOS_RETENCION_VENTA`, sin cambios. | `reservas`/`compras_pagos`, CU15 |
| Espera de pago en efectivo (CU16, nueva) | **24 horas** | El tiempo que se le da al cliente para presentarse físicamente en la boutique y pagar en efectivo antes de perder la reserva de sus prendas. Se cuenta **a partir de que se registra el pago `pendiente` en efectivo** (`pagos.creado_en`), no desde el checkout. | `compras_pagos/cu16_realizar_pago`, nueva |

Es decir: la venta ya superó la ventana de 25 minutos en cuanto `POST /pagos/procesar` se llama con
éxito y registra el intento en efectivo — a partir de ahí, el criterio de expiración pasa a ser el
de las 24 horas, no el de CU15. La retención de inventario (`cantidad_reservada`) debe extenderse
para cubrir esa ventana de 24h mientras el pago siga `pendiente`, y liberarse igual que en §1.3 si
expira sin confirmación del cajero (movimiento `cancelacion_pedido`, venta a `anulada`).

**Resuelto el 2026-09-27** (ver §1.6): endpoint administrativo nuevo, restringido a
`recogida_boutique`, con cancelación manual disponible y verificación perezosa para la expiración.

---

### 1.6 Pago en efectivo en sucursal — diseño resuelto (2026-09-27)

Las cuatro preguntas de implementación planteadas tras los mockups de §0.6 quedan decididas así.
Sigue **sin implementarse** — esto es la especificación completa que habilita empezar a escribir
código en un ciclo posterior, no la implementación en sí.

1. **Confirmación por endpoint administrativo nuevo.** `POST
   /api/v1/admin/pagos/{id_pago}/confirmar-efectivo`, restringido por RBAC a `cajero` /
   `encargado_sucursal` de la boutique de recogida de la venta, o a `administrador`. El cajero
   localiza la orden por `numero_comprobante` (lo que el cliente trae impreso o en pantalla) en un
   buscador simple del panel admin, que resuelve internamente `id_pago`/`id_venta`; el endpoint en
   sí opera por `id_pago` una vez localizado. Transiciona `pagos.estado → 'confirmado'` y
   `ventas.estado → 'pagada'`, con la misma consolidación de inventario que el flujo online
   (`cantidad_reservada -= n`, movimiento `venta_confirmada` con saldos reales e
   `id_usuario_responsable` = el cajero autenticado). No crea un rol nuevo: se reutiliza
   `encargado_sucursal`, ya existente y ya acotado a la sucursal asignada (mismo patrón que CU28).
2. **Restringido a `tipo_entrega: recogida_boutique`.** El selector de método en el cliente oculta
   «Pago en efectivo en sucursal» si el tipo de entrega elegido en CU15 fue `domicilio`. El backend
   refuerza la misma regla en `PagoServicio.procesar_pago`: `metodo_pago: "efectivo"` sobre una
   venta con `tipo_entrega != 'recogida_boutique'` responde `422 METODO_NO_SOPORTADO`.
3. **Cancelación manual disponible.** El mismo endpoint admin (o uno hermano,
   `POST /api/v1/admin/pagos/{id_pago}/cancelar-efectivo`) permite al cajero anular el pago
   `pendiente` antes de que expiren las 24h — cliente que se arrepiente o no se presenta y avisa.
   Libera el stock de inmediato: `cantidad_reservada -= n`, `cantidad_disponible += n`, venta a
   `anulada`, movimiento `cancelacion_pedido`. Es la misma mecánica de §1.3, invocada a demanda en
   vez de por expiración de ventana.
4. **Expiración por verificación perezosa**, igual que los 25 minutos de CU15 (§0.4): no hay
   proceso en segundo plano dedicado. La comprobación ocurre cada vez que alguien consulta o intenta
   confirmar la venta — si ya pasaron 24h desde `pagos.creado_en` y sigue `pendiente`, se libera en
   ese mismo acto (mismo mecanismo de `liberar_retencion_venta`, parametrizado por la ventana que
   corresponda a cada método de pago). La automatización real (cron) sigue como decisión pendiente
   común a ambas ventanas, ya registrada en §0.4.

**Notificación al cliente al confirmarse el pago (correo, notificación in-app):** queda **fuera de
alcance de este cambio**, sin decidir todavía; no bloquea la implementación de lo anterior.

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
        │                                          **carrito_detalle: se retiran las prendas**
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

**Invariante de la bolsa (revisada el 2026-09-28):** `carrito_detalle` sobrevive al checkout. CU15
solo emite la orden y retiene existencias; las prendas se retiran de la bolsa **únicamente cuando
el cobro queda confirmado**, en cualquiera de sus tres caminos:

| Método | Quién confirma | Cuándo se vacía la bolsa |
| :--- | :--- | :--- |
| Tarjeta de crédito/débito | Pasarela (Stripe sandbox) | Al responder `aprobado` |
| Bizum / Código QR | Pasarela | Al responder `aprobado` |
| Efectivo en sucursal | El cajero, en mostrador | Al llamar a `confirmar-efectivo` (§1.6), no al registrar el pago |

Un pago rechazado, abandonado o pendiente de caja deja la bolsa intacta: el cliente no ha comprado
nada todavía y no puede perder su selección. Se retiran solo las líneas de la venta pagada
—emparejadas por `(id_variante, id_sucursal)`—, no la bolsa entera, porque el cliente puede haber
añadido otras prendas mientras el pago estaba pendiente.

**Contrapartida — una sola orden viva por cliente.** Como la bolsa ya no se vacía, `POST
/ventas/checkout` rechaza con `409 ORDEN_PENDIENTE_EXISTENTE` si el cliente ya tiene una orden
`pendiente` dentro de su ventana; sin esa guarda, pulsar «TRAMITAR PEDIDO» dos veces emitiría dos
ventas y retendría el inventario dos veces. Si la ventana de la orden anterior ya venció, se libera
en el acto (verificación perezosa) y el nuevo checkout continúa.

**Renombrado de la promoción automática (2026-09-28).** La fila `id_promocion = 2`, sembrada por la
migración `0010` de `Ec-backend` y aplicada a las 3 prendas activas de mayor precio a través de
`promocion_producto`, se llamaba «Membresía Privé». El nombre venía directo del mockup, pero el
sistema no tiene ningún concepto de membresía ni de segmentación de clientes: el 15 % se aplica a
cualquiera que compre esas prendas, con sesión o sin ella, sin importar quién sea. Se renombró a
**«Selección Atelier»** en la base de datos real (Neon), en el seed de la migración `0010` y en
cada literal de código/pruebas que la citaba (`motivo_descuento` en el backend, la etiqueta
`Beneficio {{ nombre }}` de `checkout-pago.component.html` en Web y el equivalente en
`pantalla_producto_detalle.dart` en Mobile). La mecánica no cambió: sigue siendo una promoción de
catálogo (`alcance='producto'`, sin `codigo_cupon`) que se aplica automáticamente a cualquier
línea del carrito que contenga uno de sus 3 productos vinculados, vía
`CarritoRepositorio.obtener_promociones_por_producto()`. Distinta de «Bono Atelier de Bienvenida»
(`MAISON-2025`, `alcance='global'`), que sí exige que el cliente teclee el cupón.

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

> **Sobre `efectivo` en `metodos_disponibles`:** el mockup ampliado de §0.6 añade una opción de
> pago en efectivo en sucursal, con diseño ya resuelto en §1.6. El valor `efectivo` del enum
> `metodo_pago` ya existe en PostgreSQL (§0.1); **no se agrega todavía a este ejemplo ni al enum
> `MetodoPago` de TypeScript** porque sigue sin implementarse (ver `tasks.md`, `T-FE-15`/`T-MO-12`),
> y cuando se implemente `metodos_disponibles` solo debe listarlo si la venta tiene
> `tipo_entrega: 'recogida_boutique'` (§1.6.2).

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

#### Cobro digital: dos pasos, tokenizado (revisado el 2026-09-28)

> **Se sustituye el `POST /api/v1/pagos/procesar` de un solo paso** descrito hasta la ronda 1.
> Aquella versión recibía `tarjeta: {numero, titular, mes_expiracion, anio_expiracion, cvv}` en
> crudo y la reenviaba a Stripe como `payment_method_data.card.number` — exactamente lo que
> Stripe **bloquea por defecto** en cuentas nuevas desde 2019 (regla anti-PCI de «raw card data
> APIs»). Con una clave de prueba real, esa llamada habría fallado del lado de Stripe, no del
> nuestro. El rediseño mueve la recolección de la tarjeta al navegador/app, con Stripe.js
> (Web) o el SDK de Flutter (Mobile): **este servidor no vuelve a recibir el PAN ni el CVV**.
>
> El cobro se abre con `POST /pagos/intentos` y se cierra con `POST /pagos/{id_pago}/confirmar`.
> Entre ambos, el cliente confirma el `PaymentIntent` **directamente contra Stripe** — este
> servidor no participa de esa confirmación. `confirmar_pago` nunca toma el desenlace de lo que
> el cliente reporte: siempre lo recupera de Stripe por su cuenta
> (`stripe.PaymentIntent.retrieve`), aplicando la misma regla que ya rige los importes de una
> orden — el servidor jamás confía en el cliente para el resultado de un cobro.
>
> El pago en efectivo en sucursal no cambia: nunca tocó una tarjeta, así que sigue siendo
> `POST /api/v1/pagos/efectivo` de un solo paso (antes vivía en el mismo `/pagos/procesar`
> genérico; ahora tiene su propia ruta, sin cambio de comportamiento).

---

#### `POST /api/v1/pagos/efectivo`

Registra la intención de pago en efectivo. No cobra nada.

```jsonc
// PagoEfectivoIn
{ "id_venta": 1, "clave_idempotencia": "b3f1c0de-…" }
```

Respuesta y códigos: sin cambios respecto a la ronda 1 (ver §1.5.2/§1.6 más abajo).

---

#### `POST /api/v1/pagos/intentos`

Abre un `PaymentIntent` en Stripe y devuelve su `client_secret`. **No admite ningún dato de
tarjeta.**

```jsonc
// PagoIniciarIn
{
  "id_venta": 1,
  "metodo_pago": "tarjeta_credito",
  "clave_idempotencia": "b3f1c0de-…",
  "escenario_prueba": null
}
```

`escenario_prueba` (`"aprobado" | "rechazado" | "fondos_insuficientes"`, opcional) solo tiene
efecto cuando el simulador está activo (sin `STRIPE_SECRET_KEY` real configurada): fuerza el
desenlace que `confirmar_pago` va a decidir después, para que las pruebas automatizadas y las
demos sean deterministas. Con Stripe real se ignora por completo.

**Secuencia transaccional:**

1. Cargar la venta con sus detalles y bloquearla (`SELECT … FOR UPDATE`).
2. Verificar pertenencia al cliente autenticado → `403 VENTA_AJENA`.
3. Idempotencia: si la `clave_idempotencia` ya abrió un intento `pendiente`, se devuelve su mismo
   `client_secret` (recuperado de Stripe) sin abrir uno nuevo; si ya produjo un pago `confirmado`,
   se devuelve esa confirmación con `ya_confirmado: true` y `client_secret: null`.
4. Si `estado != 'pendiente'` → `409 VENTA_YA_LIQUIDADA` o `VENTA_ANULADA`.
5. Si la ventana expiró → liberar retención (§1.3) y `409 ORDEN_EXPIRADA`.
6. `stripe.PaymentIntent.create(amount=céntimos, currency='eur', automatic_payment_methods={'enabled': True}, idempotency_key=clave_idempotencia)`
   — **sin `confirm=True`** y **sin `allow_redirects: 'never'`**: Stripe decide si el método de
   pago exige un paso adicional (3D Secure/SCA) y se lo pide al cliente directamente.
7. Insertar en `pagos` con `estado='pendiente'`, `referencia_pasarela=<id del PaymentIntent>` y
   `payload_respuesta` (incluye `escenario_prueba`, nunca el `client_secret`); `COMMIT`.

```jsonc
// PagoIntentoOut — 201
{
  "id_pago": 12,
  "client_secret": "pi_3P.../secret_...",
  "ya_confirmado": false,
  "confirmacion": null
}
```

| Código | Situación |
| :--- | :--- |
| `201` | Intento abierto (o reenvío idempotente) |
| `401` | Sin sesión |
| `403` | `VENTA_AJENA` |
| `404` | `VENTA_NO_ENCONTRADA` |
| `409` | `VENTA_YA_LIQUIDADA` · `VENTA_ANULADA` · `ORDEN_EXPIRADA` |
| `422` | `metodo_pago` inválido (`efectivo` no aplica aquí; solo tarjeta/Bizum/QR/PayPal) |

---

#### `POST /api/v1/pagos/{id_pago}/confirmar`

El cliente llama a este endpoint **después** de que Stripe.js/el SDK de Flutter confirme el
`PaymentIntent` directamente contra Stripe. El servidor no confía en ese reporte: recupera el
intento por su id y decide el desenlace con lo que Stripe le devuelva.

Sin cuerpo — el `id_pago` en la ruta basta.

**Secuencia transaccional:**

1. Cargar el pago (bloqueado) y su venta (bloqueada). Si el pago no existe, no es digital o no
   tiene `referencia_pasarela` → `404`/`409 METODO_NO_SOPORTADO`.
2. Si el pago ya está `confirmado` → devolver esa misma confirmación (reenvío idempotente natural:
   doble clic, reintento de red). Si no está `pendiente` (por ejemplo, ya `rechazado`) →
   `409 PAGO_NO_PENDIENTE`.
3. Verificar pertenencia, estado y ventana de la venta, igual que en `iniciar_pago`.
4. `stripe.PaymentIntent.retrieve(referencia, expand=['payment_method'])` — la marca y los
   últimos 4 dígitos de la tarjeta se leen de ahí, nunca de un dato que el cliente haya enviado.
5. **Rechazo:** `pagos.estado='rechazado'`, se fusiona el desenlace sobre `payload_respuesta`;
   `COMMIT`; responder `402 PAGO_RECHAZADO`. La venta sigue `pendiente` y el stock retenido.
6. **Aprobación**, todo en la misma transacción: `pagos.estado='confirmado'` + `confirmado_en`;
   `ventas.estado='pagada'`; por cada línea, `cantidad_reservada -= cantidad` con
   `movimientos_inventario` (`tipo_movimiento='venta_confirmada'`, `saldo_anterior`/`saldo_nuevo`
   reales); se retiran de la bolsa solo las líneas de esta venta (§A.1); `COMMIT`.

```jsonc
// PagoConfirmadoOut — 200
{
  "id_pago": 12,
  "id_venta": 1,
  "numero_comprobante": "FS-2026-000001",
  "estado_pago": "confirmado",
  "estado_venta": "pagada",
  "metodo_pago": "tarjeta_credito",
  "referencia_pasarela": "pi_3P...",
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
| `200` | Pago confirmado (o rechazo verificado, dentro del propio flujo de error) |
| `401` | Sin sesión |
| `402` | `PAGO_RECHAZADO` — la pasarela denegó el cargo. La orden admite un nuevo intento |
| `403` | `VENTA_AJENA` |
| `404` | `PAGO_NO_ENCONTRADO` |
| `409` | `PAGO_NO_PENDIENTE` · `METODO_NO_SOPORTADO` · `VENTA_YA_LIQUIDADA` · `VENTA_ANULADA` · `ORDEN_EXPIRADA` |

> **Limitación conocida, pendiente de decisión:** `automatic_payment_methods` sin restricción deja
> que Stripe pida 3D Secure cuando la tarjeta lo exige, pero **no existe todavía un webhook** que
> reciba `payment_intent.succeeded` de forma asíncrona (`STRIPE_WEBHOOK_SECRET` está declarada en
> `config.py`/`render.yaml` pero ningún endpoint la consume). Si el cliente cierra la pestaña o la
> app entre la confirmación en Stripe y la llamada a `confirmar_pago`, el pago queda aprobado en
> Stripe pero sin reflejarse en `pagos`/`ventas` hasta que alguien vuelva a llamar a ese endpoint.
> Añadir el webhook como fuente de verdad secundaria queda fuera de esta ronda.

### A.3 Mapeo de `PagoORM`

En `compras_pagos/modelos.py`, junto a `CarritoORM`. Verificado contra la introspección de §0.1:
`payload_respuesta` como `JSONB`, `monto` como `Numeric(12, 2)` y los enums declarados con
`create_type=False`, como el resto del proyecto.

### A.4 Servicio de pasarela sandbox

Aislado en `app/integrations/stripe_service.py`, fuera del servicio de dominio, conforme a la
regla de integraciones externas de la constitución de backend. Interfaz mínima (revisada el
2026-09-28: dos pasos, sin datos de tarjeta):

```
crear_intento(monto, metodo_pago, descripcion, metadatos, idempotency_key) -> IntentoPago
    IntentoPago: referencia · client_secret · payload

verificar_intento(referencia, escenario_prueba=None) -> ResultadoPasarela
    ResultadoPasarela: aprobado · referencia · codigo_respuesta · mensaje · marca · ultimos_digitos
```

`escenario_prueba` solo lo consulta el simulador (§A.2); con Stripe real el desenlace lo decide
la pasarela y ese parámetro no existe en su API. La latencia se inyecta para poder anularla en
pruebas.

### A.5 Criterios de Aceptación (Gherkin)

> Los escenarios siguientes documentan el contrato de la **ronda 1** (`POST /pagos/procesar` de un
> solo paso, con tarjeta en el cuerpo) y se conservan por su valor histórico: siguen describiendo
> correctamente la lógica de negocio (rechazo, idempotencia, ventana expirada…), que no cambió.
> Lo único que cambió es el transporte: ese único POST se dividió en `POST /pagos/intentos` +
> `POST /pagos/{id_pago}/confirmar` (§A.2), y el escenario «Tarjeta con formato inválido» ya no
> aplica porque el backend no vuelve a validar un PAN — Stripe.js lo hace en el navegador antes de
> que exista ninguna petición a este servidor. El contrato real y vigente para pruebas automatizadas
> es el de `tests/modules/compras_pagos/test_cu16_pagos.py`.

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

> ⛔ **NOTA HISTÓRICA:** este gate se registró el 2026-09-22, antes de iniciar el Bloque 1. Las
> cuatro decisiones fueron aprobadas y el Backend quedó implementado y verificado (ver
> `checkpoint.md`, CP-01 a CP-14). Los Bloques 2 (Web) y 3 (Mobile) siguen en curso.

### Gate ampliado — mockups del 2026-09-27 (totalmente resuelto)

- **§1.5.1** — El checkbox «Guardar tarjeta» se descarta por completo, en Web y Mobile.
- **§1.5.2/§1.6** — El pago en efectivo en sucursal usa la Opción A: pago `pendiente` hasta que un
  cajero lo confirma en un endpoint administrativo nuevo (`POST
  /api/v1/admin/pagos/{id_pago}/confirmar-efectivo`, RBAC `encargado_sucursal`/`administrador`),
  restringido a `tipo_entrega: recogida_boutique`, con cancelación manual disponible
  (`cancelar-efectivo`) y expiración por verificación perezosa a las **24 horas** desde
  `pagos.creado_en` (no 48h, y distinta de los 25 minutos de retención de la bolsa en CU15). La
  notificación al cliente al confirmarse queda fuera de alcance, sin decidir.

Con esto, la especificación completa de `POST /pagos/procesar` con `metodo_pago: "efectivo"` y su
confirmación/cancelación administrativa queda lista para implementarse en un ciclo posterior.
Ninguna de estas decisiones bloquea tarjeta, Bizum/QR ni PayPal, que siguen con el flujo ya
aprobado en §A.2 y son las que deben implementarse primero en los Bloques 2 y 3.
