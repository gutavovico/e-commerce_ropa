# Lista de Tareas Atómicas: Realizar Pago Electrónico

**ID del Cambio:** `CU16-realizar-pago-electronico`
**Caso de Uso:** CU16 — Realizar Pago Electrónico
**Metodología:** Spec-Driven Development (SDD)
**Estado:** 🟢 Los 3 bloques implementados para tarjeta/Bizum-QR/PayPal (Backend, Web y Mobile). El pago en efectivo en sucursal (`T-FE-15`/`T-MO-12`) queda para un ciclo posterior.

---

## Bloque 1 — Backend

- [x] **T-BE-01**: `PagoORM` en `compras_pagos/modelos.py`, verificado con `pytest tests/test_esquema_bd.py`.
- [x] **T-BE-02**: Mapear `saldo_anterior` y `saldo_nuevo` en `MovimientoInventarioORM` y rellenarlos con valores reales en CU12, CU15 y CU16 (§0.3 de `spec.md`).
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
- [x] **T-BE-13**: `PagoServicio._registrar_pago_efectivo` rechaza `metodo_pago: "efectivo"` con `422 METODO_NO_SOPORTADO` cuando `tipo_entrega != 'recogida_boutique'`; en caso contrario inserta el pago en `estado='pendiente'` sin liquidar la venta. `metodos_disponibles` de `GET /ventas/{id}/resumen-pago` solo lista `efectivo` con recogida en boutique.
- [x] **T-BE-14**: `PagoServicio.confirmar_pago_efectivo` y su router administrativo `POST /api/v1/admin/pagos/{id_pago}/confirmar-efectivo`, con RBAC `administrador`/`encargado_sucursal`/`cajero`, estos dos últimos acotados a `venta.id_sucursal_retiro == usuario.id_sucursal`.
- [x] **T-BE-15**: `PagoServicio.cancelar_pago_efectivo` y su router administrativo `POST /api/v1/admin/pagos/{id_pago}/cancelar-efectivo`, misma restricción de alcance.
- [x] **T-BE-16**: Verificación perezosa de expiración a las 24h desde `pagos.creado_en` (`_calcular_expiracion`/`confirmar_pago_efectivo`), distinta e independiente de los 25 minutos de CU15.

## Bloque 2 — Frontend Web

- [x] **T-FE-01**: Modelos TypeScript espejo de los esquemas Pydantic (`pago.model.ts`). Corregido `PagoConfirmado`, que no coincidía con `PagoConfirmadoOut` (`ultimos_digitos_tarjeta`→`ultimos_digitos`, `fecha_pago`→`confirmado_en`, `mensaje`→`mensaje_confirmacion`, faltaba `estado_venta`) — el mismo defecto de contrato que ya advertía `CLAUDE.md`.
- [x] **T-FE-02**: `PagoService` con Signals y traducción de errores (`pago.service.ts`).
- [x] **T-FE-03**: Ruta `/pago/:idVenta` fuera del layout, con `authGuard` y en el orden correcto. `BolsaCompraComponent.tramitarPedido()` navega aquí tras el 201 de checkout.
- [x] **T-FE-04**: `CheckoutPagoComponent` a dos columnas fiel a `image_f4fca1.png`, con cabecera, migas de progreso y contador de reserva.
- [x] **T-FE-05**: Widget de tarjeta visual que refleja en vivo número, titular y expiración.
- [x] **T-FE-06**: Formulario tipado con validación, máscaras y feedback de error por campo.
- [x] **T-FE-07**: Selector de método (tarjeta / Bizum-QR / PayPal) con revelado condicional.
- [x] **T-FE-08**: Resumen lateral con líneas congeladas, desglose (incluidas las líneas informativas de envío/sastrería/financiación) y destino real de la orden (domicilio o recogida en boutique, según `tipo_entrega`).
- [x] **T-FE-09**: Cuenta atrás con limpieza en `ngOnDestroy` (antes ausente: el temporizador de la orden no se detenía al salir de la pantalla).
- [x] **T-FE-10**: Estado de procesamiento, pantalla de confirmación y manejo de `402` con reintento.
- [x] **T-FE-11**: Enlazar la confirmación de CU15 con `/pago/:idVenta`.
- [x] **T-FE-12**: Pruebas Vitest con mocks construidos sobre payloads reales del backend (35/35 en `checkout-pago.component.spec.ts`, antes 5).
- [x] **T-FE-13**: Vista expandida de Bizum/Código QR — QR real, cuenta atrás propia del código (5 min, independiente de la ventana de la orden) e instrucciones numeradas.
- ❌ **T-FE-14** *(descartada el 2026-09-27, §1.5.1 de `spec.md`)*: ~~Checkbox «Guardar tarjeta para futuras compras»~~. Eliminado del componente y del template; verificado con test de regresión.
- [ ] **T-FE-15** *(mockup §0.6 — diseño resuelto en §1.6 de `spec.md`, pendiente de implementar)*: Tarjeta de método «Pago en efectivo en sucursal», visible solo cuando `tipo_entrega: recogida_boutique`. Se deja para un ciclo posterior: requiere además la pantalla administrativa de confirmación/cancelación en caja (`T-BE-14`/`T-BE-15` ya cubren el backend).

**Estados obligatorios cubiertos:** carga (skeleton), error (orden no disponible, con retorno a `/bolsa`), procesamiento y contenido — antes el formulario se pintaba incondicionalmente con literales de relleno (`|| '1.940,00'`, `|| 'Ana Valenzuela'`, dos prendas de ejemplo si `items` venía vacío) incluso mientras `resumen()` era `null`, violando la regla de «cero datos inventados» (CP-28). Corregido: el formulario solo se renderiza una vez que `resumen()` resuelve, sin ningún valor de respaldo inventado.

## Bloque 3 — Mobile

- [x] **T-MO-01**: DTO de pago con parseo tolerante de `Decimal` (`pago_dto.dart`), reutilizando `parsearImporte` de CU11. `PagoConfirmadoDto` ya nace con los nombres de campo correctos (`estado_venta`, `ultimos_digitos`, `confirmado_en`), sin arrastrar el defecto de contrato que hubo que corregir en Web.
- [x] **T-MO-02**: `PagoApi`/`PagoApiImpl` con manejo de 401 vía `SesionManager` y traducción de errores de dominio (`PagoException`), mismo patrón que `CarritoApi`.
- [x] **T-MO-03**: `PagoBloc` con los siete estados sellados (`PagoInicial`, `PagoCargandoResumen`, `PagoListo`, `PagoProcesando`, `PagoExitoso`, `PagoRechazado`, `PagoError`) y clave de idempotencia generada una sola vez por intento.
- [x] **T-MO-04**: `CheckoutPaymentScreen` sin `BottomNavigationBar`, con `AppBar` de retorno, banner de reserva activa (boutiques reales de expedición, no literales) y carrusel de prendas.
- [x] **T-MO-05**: Widget «Atelier Privé Black Card» interactivo, reflejando en vivo los últimos dígitos, titular y expiración tecleados.
- [x] **T-MO-06**: Radio tiles de método (tarjeta / Bizum-QR / PayPal), insignias de seguridad y banner de reserva activa.
- [x] **T-MO-07**: Barra de acción fija `CONFIRMAR Y PAGAR` con el monto real, inhabilitada mientras `PagoProcesando`.
- [x] **T-MO-08**: `ShoppingBagScreen` navega a `CheckoutPaymentScreen` en cuanto `ordenConfirmada` llega (sin la confirmación en línea que había antes), propagando `widget.token`; al volver, refresca la bolsa.
- [x] **T-MO-09**: Pruebas de contrato (`pago_dto_test.dart`, 9), de BLoC (`pago_bloc_test.dart`, 7) y de widget (`checkout_payment_screen_test.dart`, 7), más `shopping_bag_test.dart` actualizado para la navegación (30 nuevas en total).
- [x] **T-MO-10**: Vista expandida de Bizum/Código QR con el mismo generador que Web (`api.qrserver.com`), cuenta atrás propia e instrucciones numeradas.
- ❌ **T-MO-11** *(descartada el 2026-09-27, §1.5.1 de `spec.md`)*: ~~Checkbox «Guardar tarjeta para futuras compras»~~. Nunca se implementó; verificado con test de regresión.
- [ ] **T-MO-12** *(mockup §0.6 — diseño resuelto en §1.6 de `spec.md`, pendiente de implementar)*: Tarjeta de método «Pago en efectivo en sucursal» en Mobile, igual que `T-FE-15`. Se deja para un ciclo posterior.

**Defecto corregido durante la ejecución:** `RenderFlex overflowed` en la fila «Selecciona Forma de
Pago» + badge «CIFRADO SEGURO» (sin `Expanded`) y en `_filaResumen` de la pantalla de confirmación.
Es la sexta aparición de este defecto en el proyecto (CHANGELOG, entradas 9, 20, 26 y 31). Se
resolvió con `Expanded`/`TextOverflow.ellipsis`, no reduciendo tamaños de fuente, según la práctica
ya fijada en `CLAUDE.md`.

## Ronda 2 — Migración de tarjeta en crudo a tokens de Stripe (2026-09-28)

Motivo: `TarjetaIn` recogía el PAN/CVV en el propio backend y los reenviaba a Stripe como
`payment_method_data.card.*` — justo lo que Stripe bloquea por defecto en cuentas nuevas («raw
card data APIs»). Ver la nota al inicio de §A.2 de `spec.md` y el CHANGELOG (entrada 67).

### Bloque 1 — Backend

- [x] **T-BE-16**: `stripe_service.py` reescrito: `crear_intento`/`verificar_intento`/`recuperar_client_secret` sustituyen a `procesar_cargo`; se elimina `DatosTarjeta` y la construcción de `payment_method_data.card` con PAN en crudo. El simulador es determinista por `escenario_prueba`, no por sufijo de PAN.
- [x] **T-BE-17**: `esquemas.py`: se elimina `TarjetaIn`/`PagoProcesarIn`; se añaden `PagoEfectivoIn`, `PagoIniciarIn` (sin ningún campo de tarjeta) y `PagoIntentoOut`.
- [x] **T-BE-18**: `servicio.py`: `procesar_pago` se divide en `registrar_pago_efectivo` (sin cambios de comportamiento), `iniciar_pago` (abre el `PaymentIntent`, nunca ve el PAN) y `confirmar_pago` (verifica el desenlace contra Stripe, nunca contra lo que el cliente reporte).
- [x] **T-BE-19**: `router.py`: `POST /pagos/procesar` se reemplaza por `POST /pagos/efectivo`, `POST /pagos/intentos` y `POST /pagos/{id_pago}/confirmar`.
- [x] **T-BE-20**: `test_cu16_pagos.py` reescrito (49 pruebas) para el flujo de dos pasos; suite completa 442/442. Verificado end-to-end contra Neon real, en una transacción revertida: `iniciar_pago` + `confirmar_pago` sobre una venta y un inventario reales.

### Bloque 2 — Frontend Web

- [x] **T-FE-16**: `@stripe/stripe-js` instalado. `src/environments/environment.ts`/`environment.prod.ts` creados (el proyecto no tenía ningún archivo de entorno hasta ahora) con `stripePublishableKey`, y `fileReplacements` añadido en `angular.json` para que el build `production` use `environment.prod.ts`.
- [x] **T-FE-17**: Retirado el formulario reactivo (`formTarjeta`, campos `numero`/`titular`/`expiracion`/`cvv`) y los quick-fill de PAN. La «Atelier Privé Black Card» pasa a ser puramente decorativa (ya no refleja en vivo lo tecleado, porque ya no hay nada que este componente pueda leer). En su lugar se monta el **Payment Element** de Stripe en `#stripe-payment-element`, en modo *deferred* (`elements({mode:'payment', amount, currency})`, sin `clientSecret` todavía) para que el cliente pueda ver y rellenar el campo de tarjeta antes de pulsar pagar.
- [x] **T-FE-18**: `PagoService.procesarPago` se divide en `iniciarPago` (`POST /pagos/intentos`) y `confirmarPago` (`POST /pagos/{id_pago}/confirmar`), más `registrarPagoEfectivo` (`POST /pagos/efectivo`). `CheckoutPagoComponent.confirmarYPagar()` encadena `elements.submit()` → `iniciarPago()` → `stripe.confirmPayment({elements, clientSecret, redirect:'if_required'})` → `confirmarPago()`. `redirect:'if_required'` evita una redirección completa salvo que el método de pago la exija (algunos SCA); para ese caso se añadió `intentarReanudarTrasRedireccionDeStripe()`, que detecta el retorno por `payment_intent_client_secret` en la URL y retoma la confirmación con el `id_pago` guardado en `sessionStorage` antes de salir.
- [x] **T-FE-19**: `StripeConfigService`/`StripeLoaderService` nuevos: envuelven `environment.stripePublishableKey` y `loadStripe()` en servicios inyectables, porque el sistema de pruebas de este proyecto (`@angular/build:unit-test`) **rechaza `vi.mock` sobre imports relativos** («Please use Angular TestBed for mocking dependencies») — se descubrió al intentar mockear `environment`/`@stripe/stripe-js` directamente. `checkout-pago.component.spec.ts` reescrito (22 pruebas: modo simulador, sin clave real) más `checkout-pago-stripe-real.component.spec.ts` nuevo (con clave real mockeada vía `TestBed`, sin salir a la red). Sin clave publicable configurada, el componente muestra un panel de «modo simulador» con 3 botones (`aprobado`/`rechazado`/`fondos_insuficientes`) que reflejan `escenario_prueba`, el mismo mecanismo del simulador del backend.

**Verificación:** Web 484/484 (`ng test`), `npx tsc --noEmit` limpio, `ng build` (producción, con `fileReplacements`) exitoso. `ng serve` arrancado y la ruta `/pago/:idVenta` responde 200 sin errores de compilación/runtime. **No verificado con una tarjeta de prueba real (`4242 4242 4242 4242`) contra Stripe.js real**: no hay ninguna `STRIPE_PUBLISHABLE_KEY`/`STRIPE_SECRET_KEY` real configurada en este proyecto todavía (ver la guía de conexión con Stripe ya entregada); sin esas claves no existe ningún `PaymentIntent` real contra el que Stripe.js pueda confirmar nada. El flujo de Stripe real se verificó en cambio mockeando `StripeLoaderService` (`checkout-pago-stripe-real.component.spec.ts`), que ejercita la misma secuencia de llamadas (`elements.submit()` → `iniciarPago` → `stripe.confirmPayment()` → `confirmarPago`) que se ejecutaría con Stripe.js real.

### Bloque 3 — Mobile

- [x] **T-MO-13**: `flutter_stripe` instalado (`flutter pub add`). `STRIPE_PUBLISHABLE_KEY` añadida a `lib/api_config.dart` vía `String.fromEnvironment`, mismo patrón que `API_URL`; `main()` la lee e inicializa `Stripe.publishableKey`/`Stripe.instance.applySettings()` solo si no está vacía. Nativo: iOS ya declaraba `IPHONEOS_DEPLOYMENT_TARGET = 13.0` y Android hereda `flutter.minSdkVersion` de Flutter — ambos ya satisfacen el mínimo que exige el plugin sin tocar `build.gradle`/`Podfile`.
- [x] **T-MO-14**: Retirados los cuatro `TextEditingController` (número/titular/expiración/CVV) y `validarLuhn` de `checkout_payment_screen.dart`. La «Atelier Privé Black Card» pasa a ser decorativa. En su lugar se monta el `CardField` de `flutter_stripe` cuando hay clave publicable real; sin ella, un panel de «modo simulador» (`ChoiceChip` con los 3 escenarios del simulador del backend).
- [x] **T-MO-15**: `PagoApi.procesarPago` dividido en `iniciarPago`/`confirmarPago`, espejo de los dos endpoints nuevos. Se creó `StripeGateway` (`stripe_gateway.dart`) para desacoplar `PagoBloc` del SDK de Stripe: `StripeGatewayReal.confirmarPago` envuelve `Stripe.instance.confirmPayment(...)`, y su `disponible` (que lee `ApiConfig.stripePublishableKey`) es lo que decide si `PagoBloc.confirmarYPagar()` sigue el camino de Stripe real (`iniciarPago` → `_stripeGateway.confirmarPago` → `confirmarPago`) o el del simulador (`iniciarPago` con `escenario_prueba` → `confirmarPago` directo, sin ningún SDK real de por medio). Bizum/QR y PayPal siguen siendo simulaciones decorativas del proyecto y se abren siempre con `escenario_prueba: 'aprobado'`, con o sin Stripe real inicializado.
- [x] **T-MO-16**: `pago_dto_test.dart`/`pago_bloc_test.dart`/`checkout_payment_screen_test.dart`/`mocks/mock_pago_api.dart` reescritos para el flujo de dos pasos, con un `StripeGateway` falso para las pruebas que ejercitan el camino de Stripe real. `dart analyze` sin incidencias; `flutter test` 181/181.

**Verificación:** `dart analyze` y `flutter test` (181/181) pasan de extremo a extremo. **No
verificado en un emulador/dispositivo real** — este entorno no tiene uno disponible, así que ni el
`CardField` nativo ni una confirmación real con `4242 4242 4242 4242` se ejercitaron end-to-end;
la cobertura de ese camino se limita a `StripeGateway` mockeado vía `TestBed`-equivalente
(inyección directa en `PagoBloc`), igual que en Web con `StripeLoaderService`.

**Pendiente de decisión, fuera de esta ronda:** el webhook de Stripe (`payment_intent.succeeded`)
que reconciliaría un pago aprobado en Stripe pero nunca reportado a `confirmar_pago` por un cierre
de pestaña/app a mitad de camino. Ver la nota al final de §A.2 de `spec.md`.
