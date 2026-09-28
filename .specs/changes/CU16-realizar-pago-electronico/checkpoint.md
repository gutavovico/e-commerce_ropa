# Puntos de Control y Verificación: Realizar Pago Electrónico

**ID del Cambio:** `CU16-realizar-pago-electronico`
**Caso de Uso:** CU16 — Realizar Pago Electrónico
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)
**Estado:** 🟢 CP-01 a CP-32 y CP-34 a CP-36 aprobados (Backend + Web + Mobile) · ⏳ solo CP-33 pendiente (pago en efectivo en sucursal, fuera de alcance de este ciclo)
**Actualización 2026-09-27 (Backend):** se añadió el pago en efectivo en sucursal completo —
`PagoServicio._registrar_pago_efectivo`, `confirmar_pago_efectivo`, `cancelar_pago_efectivo` y los
dos endpoints administrativos, con RBAC acotado por sucursal y expiración perezosa a 24h. `pytest`
**424/424** en verde (35/35 específicos de CU16, 11 nuevos). CP-34 a CP-36 aprobados.
**Actualización 2026-09-27 (Web):** `CheckoutPagoComponent` completado para tarjeta/Bizum-QR/PayPal
— corregido el contrato `PagoConfirmado` (no coincidía con `PagoConfirmadoOut`: campos como
`ultimos_digitos_tarjeta`, `fecha_pago` y `mensaje` no existen en la respuesta real del backend),
descartado el checkbox «Guardar tarjeta» (§1.5.1), añadidos estados de carga/error ausentes hasta
ahora, eliminados los literales de relleno (`|| '1.940,00'`, prendas de ejemplo) y añadida la
cuenta atrás e instrucciones del código Bizum/QR. `ng test` **474/474** en verde (16/16 específicos
de este componente, antes 5) · `tsc --noEmit` y `ng build` limpios. El pago en efectivo en
sucursal (`T-FE-15`) se deja para otro ciclo.
**Actualización 2026-09-27 (Mobile):** paquete `cu16_realizar_pago` completo — `pago_dto.dart`
(espejo exacto de `PagoConfirmadoOut`, ya con `estado_venta`/`ultimos_digitos`/`confirmado_en`
correctos desde el origen, sin arrastrar el defecto de contrato que hubo que corregir en Web),
`pago_api.dart`, `PagoBloc` con los 7 estados sellados de la especificación
(`PagoInicial/PagoCargandoResumen/PagoListo/PagoProcesando/PagoExitoso/PagoRechazado/PagoError`) y
`CheckoutPaymentScreen`, fiel a `image_046a5d.png`: banner de reserva con boutiques reales, carrusel
de prendas, tarjeta interactiva, Bizum/QR con el mismo generador que Web y cuenta atrás propia,
PayPal, sin checkbox de «Guardar tarjeta», y barra de acción fija. `ShoppingBagScreen.tramitarPedido`
ahora navega aquí en lugar de mostrar una confirmación en línea (mismo patrón que Web, sin pantalla
intermedia), propagando el token. Se corrigió además un `RenderFlex overflowed` nuevo (título de
sección + badge sin `Expanded`) antes de que llegara a producción, siguiendo la práctica ya fijada
en `CLAUDE.md` de usar `Expanded`/`ellipsis` en vez de reducir fuentes. `dart analyze` 0 incidencias
· `flutter test` **173/173** en verde (30 nuevos: 9 de contrato de DTO, 7 de BLoC, 7 de widget y 1
actualizado en `shopping_bag_test.dart` para reflejar la navegación).
CP-01 a CP-32 quedan aprobados. Solo CP-33 (pago en efectivo en sucursal) sigue `⏳`: su diseño está
resuelto (§1.6 de `spec.md`) y el Backend ya lo implementa, pero ningún cliente lo expone todavía
(`T-FE-15`/`T-MO-12`), decisión deliberada para no ampliar más este ciclo.

---

## Matriz de Puntos de Control (Checkpoints)

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
| **CP-15** | Web | `/pago/:idVenta` se renderiza **sin la barra de navegación institucional**. | Vitest | ✅ |
| **CP-16** | Web | `← VOLVER A LA BOLSA` navega a `/bolsa`. | Vitest | ✅ |
| **CP-17** | Web | Layout a dos columnas fiel al mockup; la tarjeta visual refleja lo tecleado en vivo. | Vitest + inspección | ✅ |
| **CP-18** | Web | Alternar método revela y oculta los campos correspondientes. | Vitest | ✅ |
| **CP-19** | Web | Un `402` muestra el motivo y permite reintentar sin perder la orden. | Vitest | ✅ |
| **CP-20** | Web | `tsc --noEmit` sin errores, `ng build` limpio y `ng test` en verde. | Ejecución | ✅ |
| **CP-21** | Mobile | Pantalla completa **sin `BottomNavigationBar`**, con `AppBar` de retorno operativo. | Test de widget | ✅ |
| **CP-22** | Mobile | La barra `CONFIRMAR Y PAGAR` permanece fija y visible durante el scroll. | Test de widget | ✅ |
| **CP-23** | Mobile | Alternar método de pago produce feedback visual inmediato. | Test de widget | ✅ |
| **CP-24** | Mobile | DTO validados con `fromJson` sobre payloads literales del backend. | Revisión + tests | ✅ |
| **CP-25** | Mobile | `dart analyze` sin incidencias y `flutter test` en verde. | Ejecución | ✅ |
| **CP-26** | Transversal | Web y Mobile consumen los mismos endpoints con los mismos nombres de campo. | Diff de contratos | ✅ |
| **CP-27** | Transversal | Doble pulsación de «Confirmar y pagar» no genera un segundo cargo. | Prueba manual + test | ✅ |
| **CP-28** | Transversal | Ningún importe, prenda ni boutique procede de literales: todo viene de PostgreSQL. | Auditoría de código | ✅ |
| **CP-29** | Transversal | Catálogo exclusivamente femenino en el resumen de la orden, incluidos los *fallback*. | Auditoría visual | ✅ |
| **CP-30** | Transversal | La navegación desde «TRAMITAR PEDIDO» en la Bolsa de Compra abre esta pantalla en `/pago/:idVenta` sin pantalla intermedia. | Inspección + Vitest/test de widget | ✅ |
| **CP-31** | Web + Mobile | Seleccionar Bizum/Código QR expande un QR real con cuenta atrás propia e instrucciones numeradas. | Vitest + test de widget | ✅ |
| **CP-32** | Transversal | El checkbox «Guardar tarjeta» **no existe en ningún cliente** (descartado en §1.5.1 de `spec.md`); `guardar_tarjeta` nunca se envía en el payload. | Auditoría de código | ✅ |
| **CP-33** *(nuevo)* | Web + Mobile | La opción «Pago en efectivo en sucursal» solo aparece cuando `tipo_entrega: recogida_boutique`; con `domicilio` queda oculta. | Vitest + test de widget | ⏳ |
| **CP-34** | Backend | Un pago `efectivo` registrado como `pendiente` conserva la retención de inventario durante **24 horas** desde `pagos.creado_en`, no durante los 25 minutos de CU15; expira por verificación perezosa. | Pytest | ✅ |
| **CP-35** | Backend | `POST /api/v1/admin/pagos/{id_pago}/confirmar-efectivo` consolida el inventario (`venta_confirmada`, saldos reales) igual que la aprobación online, restringido a `encargado_sucursal`/`cajero` de la boutique de recogida o `administrador`. | Pytest | ✅ |
| **CP-36** | Backend | `POST /api/v1/admin/pagos/{id_pago}/cancelar-efectivo` libera la retención de inmediato (`cancelacion_pedido`, venta `anulada`) antes de que expiren las 24h. | Pytest | ✅ |
