# Plan de Ejecución por Bloques: Realizar Pago Electrónico

**ID del Cambio:** `CU16-realizar-pago-electronico`
**Caso de Uso:** CU16 — Realizar Pago Electrónico
**Metodología:** Spec-Driven Development (SDD)
**Estrategia de Ejecución:** El Bloque 1 debe completarse y aprobarse antes de iniciar el 2 y el 3.
Los bloques 2 y 3 son paralelizables entre sí.

---

## Bloque 1 — Backend (`Ec-backend`)

**Fase 1.1 — Modelos y esquemas**
`PagoORM` en `compras_pagos/modelos.py` (§A.3 de `spec.md`). Corrección de `MovimientoInventarioORM`
para mapear los saldos (§0.3). Esquemas `ResumenPagoOut`, `PagoItemOut`, `TarjetaIn`,
`PagoProcesarIn`, `PagoConfirmadoOut` y `PagoRechazadoOut`, con validadores de Luhn, expiración y
CVV.

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

**Fase 1.7 — Backend administrativo para pago en efectivo en sucursal** *(nueva, diseño resuelto en
§1.5.2/§1.6 de `spec.md`, fuera del Bloque 1 original — pendiente, `T-BE-13` a `T-BE-16`)*
- `PagoServicio.procesar_pago` rechaza `metodo_pago: "efectivo"` con `422 METODO_NO_SOPORTADO`
  cuando `ventas.tipo_entrega != 'recogida_boutique'`; en caso contrario inserta el pago en
  `estado='pendiente'` sin tocar `ventas.estado`.
- `PagoServicio.confirmar_pago_efectivo` — transiciona `pagos.estado → 'confirmado'` y
  `ventas.estado → 'pagada'`, consolidando inventario igual que la aprobación online
  (`cantidad_reservada -= n`, movimiento `venta_confirmada`, `id_usuario_responsable` = cajero).
- `PagoServicio.cancelar_pago_efectivo` — libera la retención de inmediato
  (`cantidad_reservada -= n`, `cantidad_disponible += n`, venta `anulada`, movimiento
  `cancelacion_pedido`), invocable en cualquier momento antes de la confirmación o la expiración.
- Verificación perezosa de expiración a las 24h desde `pagos.creado_en`, reutilizando el patrón de
  `liberar_retencion_venta` mencionado en §0.4, parametrizado por ventana según el método de pago.
- Router administrativo nuevo: `POST /api/v1/admin/pagos/{id_pago}/confirmar-efectivo` y
  `POST /api/v1/admin/pagos/{id_pago}/cancelar-efectivo`, con RBAC `encargado_sucursal`
  (acotado a su propia sucursal, mismo patrón que CU28) y `administrador`.

---

## Bloque 2 — Frontend Web (`Ec-frontend`)

**Fase 2.0 — Punto de entrada (confirmado, ya resuelto en código)**
Esta pantalla se despliega **inmediatamente después de pulsar «TRAMITAR PEDIDO» en la Bolsa de
Compra (CU11)**, sin pantalla intermedia de confirmación. `BolsaCompraComponent.tramitarPedido()`
(`bolsa-compra.component.ts:185-192`) ya invoca `this.router.navigate(['/pago', venta.id_venta])`
en cuanto `POST /ventas/checkout` responde `201`. Lo único pendiente es registrar la ruta en
`app.routes.ts` (Fase 2.1) — hoy ausente, causa del `NG04002: Cannot match any routes` visto en
Vitest.

**Fase 2.1 — Enrutamiento**
Ruta `/pago/:idVenta` **fuera de `MainLayoutComponent`**, con `authGuard`, declarada después de la
landing y antes del comodín para respetar el guard `app.routes.spec.ts`. Cabecera propia
(`sticky top-0`) con `← VOLVER A LA BOLSA` hacia `/bolsa` (vía `Location.back()`), logotipo
`FASHION STORE` centrado, indicador `PAGO SEGURO · SSL 256-BIT` y avatar de sesión. Bajo la
cabecera, una barra de migas de progreso `BOLSA DE COMPRA (n) › ENVÍO & ENTREGA › MÉTODO DE PAGO
(activo)` junto al contador `Reserva activa: mm:ss restantes | <sucursales de expedición>`
(mismo `segundos_restantes` de `ResumenPagoOut`, solo cambia dónde se pinta).

**Fase 2.2 — Servicio**
`PagoService` con Signals: `resumen`, `metodoSeleccionado`, `procesando`, `error` y
`segundosRestantes`. Tipado estricto; los importes viajan como `string`.

**Fase 2.3 — Componente (anatomía detallada según mockup ampliado, §0.6 de `spec.md`)**
`CheckoutPaymentComponent` standalone con `OnPush`, a dos columnas (`lg:grid-cols-[1fr_380px]`):

- **Columna izquierda — «Selecciona Forma de Pago» (Paso 03 de 03)**, con badge
  `CIFRADO SEGURO 256-BIT SSL`, y tres tarjetas de método seleccionables por radio:
  1. **Tarjeta de Crédito/Débito** — marcas aceptadas (`VISA · MASTERCARD · AMEX`); tarjeta visual
     «ATELIER PRIVÉ BLACK CARD» que refleja en vivo número enmascarado, titular y expiración
     tecleados; formulario con número, titular, expiración y CVV. **Sin checkbox «Guardar
     tarjeta»**: se descartó definitivamente (§1.5.1 de `spec.md`) y no se muestra en ningún
     cliente.
  2. **Bizum / Código QR** (badge `INSTANTÁNEO`) — al seleccionarla, expande un QR real con su
     propia cuenta atrás de expiración del código (independiente de `segundos_restantes` de la
     venta) e instrucciones numeradas (abrir app bancaria/Bizum, escanear o teclear el código
     corto, autorizar el importe exacto).
  3. **PayPal** (mapea al `metodo_pago: "pasarela_digital"` ya contemplado en `A.2`, sin cambios de
     contrato).
  - **Pago en efectivo en sucursal** (badge `EN TIENDA`, tarjeta expandida `LIQUIDACIÓN
    PRESENCIAL` con boutique de recogida). El texto de la interfaz debe anunciar **24 horas**, no
    las 48h del mockup (§1.5.2 de `spec.md`). Diseño completo ya resuelto (§1.6 de `spec.md`:
    endpoint admin de confirmación/cancelación, restricción a `recogida_boutique`, expiración
    perezosa a 24h) — **queda fuera de esta fase de todos modos**, como tarea aparte (`T-FE-15`),
    porque implica además un endpoint y una pantalla administrativa nuevos no cubiertos por el
    Bloque 1 original.
  - Bloque de insignias (`SSL 256-BIT` · `PCI-DSS NIVEL 1` · `GARANTÍA ATELIER`) y nota de
    empaquetado con guante blanco, ambos puramente informativos.
- **Columna derecha — «Resumen de la Orden»**: lista de prendas (miniatura, nombre, sucursal de
  expedición, talla, precio); desglose (`Subtotal artículos`, `Beneficio Selección Atelier` u otro
  descuento aplicado — nombre renombrado el 2026-09-28, ver nota en `spec.md`; el mockup decía
  «Membresía Privé», pero el sistema no tiene noción de membresía ni de segmentación de clientes,
  `Envío asegurado con guante blanco: GRATUITO`, `Ajuste de sastrería de
  cortesía: INCLUIDO`, `Impuestos estimados (IVA 21% incluido)`); `TOTAL A LIQUIDAR`; línea
  informativa de financiación `o en N plazos sin intereses con Atelier Pay` (**decorativa, sin
  integración real**, igual que en CU07); bloque de entrega (domicilio programada o recogida en
  boutique) con nombre de cliente y dirección/sucursal reales de `ResumenPagoOut`; botón
  `CONFIRMAR Y PAGAR <total>`; leyenda `Transacción protegida por Pasarela Bancaria Central`.

**Fase 2.4 — Interacción**
Formulario tipado con `NonNullableFormBuilder`; validación de Luhn en cliente **como cortesía**, no
como autoridad; máscaras de PAN y expiración; cuenta atrás con limpieza en `ngOnDestroy`; botón
inhabilitado mientras haya petición en vuelo; traducción de `402`, `409` y `422` a mensajes de
negocio; pantalla de confirmación con el comprobante.

**Fase 2.5 — Pruebas (Vitest)**
Ausencia de navbar, retorno a `/bolsa`, validación de tarjeta, alternancia de método (incluida la
expansión del QR), estado de procesamiento, rechazo con reintento y expiración.

---

## Bloque 3 — Mobile (`Ec-mobile`)

**Fase 3.1 — Capa de datos**
`modulos/compras_pagos/cu16_realizar_pago/datos/` con DTO probados mediante `fromJson` sobre
**payloads literales del backend**, y `PagoApi` con manejo de 401 vía `SesionManager` y traducción
de errores de dominio.

**Fase 3.2 — BLoC**
`PagoBloc` con estados sellados `PagoInicial`, `PagoCargandoResumen`, `PagoListo`, `PagoProcesando`,
`PagoExitoso`, `PagoRechazado` y `PagoError`. La clave de idempotencia se genera una sola vez por
intento.

**Fase 3.3 — Pantalla (anatomía detallada según mockup ampliado, §0.6 de `spec.md`)**
`CheckoutPaymentScreen` abierta con `Navigator.push`, **sin `BottomNavigationBar`**:

- `AppBar` con botón de retorno, título «PAGO SEGURO» / subtítulo «Checkout Payment» y badge
  `256-BIT SSL`.
- Banner de reserva activa (color crema) `Reserva activa: mm:ss restantes | FLAGSHIPS ACTIVAS`.
- Bloque de monto total a liquidar con ícono de bolsa y subtítulo `N prendas exclusivas · IVA y
  aranceles incluidos`.
- Línea de entrega: ícono de camión + `Entrega: <cliente> · <dirección truncada>` con badge
  `PRIORITY` (datos reales de `ResumenPagoOut`, nunca literales).
- Carrusel horizontal de miniaturas circulares de las prendas de la orden.
- «Selecciona Forma de Pago» + badge `CIFRADO SEGURO`, con las mismas opciones que en Web: tarjeta
  (con la misma tarjeta visual interactiva, **sin checkbox «Guardar tarjeta»**, descartado en
  §1.5.1), Bizum/Código QR (con el mismo estado expandido de QR + cuenta atrás) y PayPal. El pago
  en efectivo en sucursal (diseño resuelto en §1.6 de `spec.md`) queda igualmente fuera de esta
  fase, como `T-MO-12` aparte.
- Insignias de seguridad y nota de empaquetado, igual que en Web.
- **Barra de acción fija** (`bottomNavigationBar`, no de navegación) con `CONFIRMAR Y PAGAR
  <total>` y la leyenda de pasarela protegida.

**Fase 3.4 — Pruebas (`flutter test`)**
Contrato de DTO, transiciones del BLoC, ausencia de barra de navegación, footer fijo y feedback al
alternar método (incluida la expansión del QR).
