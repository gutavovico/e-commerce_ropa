# Especificación Técnica Permanente: CU16 — Realizar Pago Electrónico

**Código:** CU16
**Paquete de Dominio:** `compras_pagos`
**Backend:** `app/modules/compras_pagos/cu16_realizar_pago/` · `app/integrations/stripe_service.py`
**Frontend:** `src/app/modules/compras_pagos/cu16_realizar_pago/` (`CheckoutPagoComponent`) · caja de mostrador en CU28 y en el POS (CU31-CU32)
**Mobile:** `lib/src/modulos/compras_pagos/cu16_realizar_pago/` (`CheckoutPaymentScreen`, `PagoBloc`)
**Actores:** Cliente autenticado · cajero, encargado de sucursal y administrador (cobro en efectivo)
**Estado:** Aprobado y promovido a permanente (2026-11-08; rondas 1–3, CP-01 a CP-38)
**Historial del cambio:** `.specs/finalized/CU16-realizar-pago-electronico/` · `CHANGELOG.md` defecto 52

---

## 1. Contratos

| Método y ruta | Uso |
| :--- | :--- |
| `GET /api/v1/ventas/{id_venta}/resumen-pago` | Resumen de la orden a pagar (`403 VENTA_AJENA`, `404 VENTA_NO_ENCONTRADA`, `409 VENTA_NO_PAGABLE`) |
| `POST /api/v1/pagos/intentos` | Abre un `PaymentIntent` de Stripe y devuelve su `client_secret`. No admite datos de tarjeta |
| `POST /api/v1/pagos/{id_pago}/confirmar` | Cierra el cobro: el resultado se recupera siempre de Stripe (`PaymentIntent.retrieve`), nunca del cliente |
| `POST /api/v1/pagos/efectivo` | `{id_venta, clave_idempotencia}`: registra la intención de pagar en efectivo; solo con `tipo_entrega = recogida_boutique` (`422 METODO_NO_SOPORTADO`) |
| `POST /api/v1/admin/pagos/{id_pago}/confirmar-efectivo` | El cajero cobra en mostrador: pago `confirmado`, venta `pagada`, `venta_confirmada` con `id_usuario_responsable` |
| `POST /api/v1/admin/pagos/{id_pago}/cancelar-efectivo` | Anula el pago pendiente y libera el stock (`cancelacion_pedido`) |
| `POST /api/v1/pagos/webhook` | Reconciliación asíncrona de Stripe (`payment_intent.succeeded` liquida y consolida; `payment_intent.payment_failed` rechaza). Idempotente |

`POST /api/v1/pagos/procesar` (un paso, tarjeta en crudo) está retirado desde la Ronda 2: el servidor no recibe nunca el PAN ni el CVV.

## 2. Reglas

- **Tarjeta tokenizada:** la tarjeta se recoge con Stripe.js (Web) o el SDK de Flutter (Mobile) y el cliente confirma el `PaymentIntent` directamente contra Stripe.
- **Efectivo en sucursal:** la opción solo aparece con recogida en boutique (Web `esRecogidaBoutique()`, Mobile `resumen.esRecogidaBoutique`). Las prendas quedan apartadas con un plazo de **24 h**; vencido, la retención se libera de forma perezosa al consultar o intentar confirmar. El cobro lo hace el personal de la boutique de recogida (RBAC por sucursal) desde CU28 o desde la pestaña «Pedidos web por cobrar» del POS.
- **Webhook:** con `STRIPE_WEBHOOK_SECRET` configurado exige `Stripe-Signature` válida (`400 WEBHOOK_SIN_FIRMA | FIRMA_WEBHOOK_INVALIDA`); sin secreto (simulador o desarrollo) acepta el JSON plano. Cuerpo no parseable: `400 PAYLOAD_WEBHOOK_INVALIDO`.
- **Simulador:** sin `STRIPE_SECRET_KEY`, `StripeService` responde de forma determinista según `escenario_prueba`.
- Importes `Decimal` serializados como cadena; el servidor recalcula siempre y nunca confía en el cliente para el resultado de un cobro.
- Fuera de alcance: notificar al cliente (correo o in-app) al confirmarse el pago.
