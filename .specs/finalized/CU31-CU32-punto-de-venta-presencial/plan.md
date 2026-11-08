# Plan Técnico — CU31-CU32: Punto de Venta Presencial

Basado en `spec.md` (aprobada el 2026-11-08, D1–D11 + PDF). Orden de gates: **Bloque 0 → Bloque 1 (Backend)
→ Bloque 2 (Web)**. Mobile excluido.

## Bloque 0 — Prerrequisito de personal (D3)

- **CU20:** al crear un usuario con rol `cajero`, `encargado_sucursal` o `administrador`, o al cambiarlo a uno
  de ellos, crear su fila en `empleados` (`codigo_empleado = EMP-<id_usuario>`, `cargo` según el rol) si no
  existe. Mismo servicio y transacción que el alta.
- **Regularización única** (script idempotente, no migración de esquema): insertar la fila de `empleados` del
  personal existente que no la tiene (hoy: usuarios 13 y 14). Se ejecuta contra Neon y se verifica.

## Bloque 1 — Backend (`app/modules/compras_pagos/cu31_cu32_punto_venta/`)

**Capas:** `router.py` (solo HTTP, `require_roles(ROLES_CAJA)`) → `servicio.py` (negocio y transacción, sin
`fastapi`) → `repositorio.py` (consultas, `FOR UPDATE`) → ORM existente (`VentaORM`, `VentaDetalleORM`,
`PagoORM`, `InventarioSucursalORM`, `MovimientoInventarioORM`; no se redeclara ninguno).

1. **Precios reutilizables.** Extraer de `CarritoServicio.calcular_lineas` y `CheckoutServicio._resolver_cupon`
   una función de cálculo que opere sobre líneas `(variante, cantidad)`, sin depender del carrito. CU11/CU15
   pasan a usarla sin cambiar su comportamiento: sus suites deben seguir en verde. El cupón se divide en
   **validar** (CU31 / previsualizar) y **consumir** (CU32), sin alterar el flujo de CU15.
2. **Comprobante:** reutilizar `CheckoutServicio._generar_numero_comprobante` (`seq_comprobante_venta`).
3. **Reservas por su servicio (regla de arquitectura entre paquetes).** En el paquete `reservas`, un servicio
   de atención en caja con tres operaciones:
   - `obtener_para_caja(id_o_codigo, id_sucursal)`: aplica el vencimiento perezoso de CU13 y valida el estado;
   - `consolidar_lineas(...)`: `venta_confirmada` sobre la fila del movimiento `reserva`;
   - `liberar_lineas(...)`: `liberacion_reserva` y marcado como `atendida`.

   El POS nunca toca los modelos de `reservas` directamente.
4. **Registrar (CU31):** validar alcance de sucursal y empleado → bloquear y validar el inventario de las
   líneas nuevas → precios → venta, líneas y retención (`venta`) → bitácora. Todo en una transacción.
5. **Cobrar (CU32):** `FOR UPDATE` sobre la venta → validar `pendiente` y vencimiento → validar el pago por
   método → consumir el cupón → pago `confirmado` → consolidar el stock (líneas nuevas desde la retención de la
   venta; líneas de reserva desde su fila) → liberar las líneas de reserva excluidas → reserva `atendida` →
   venta `pagada` → bitácora. El rechazo de tarjeta solo inserta un pago `rechazado`.
6. **Anular y vencer:** liberar con `cancelacion_pedido` solo las líneas que retuvo el POS. Vencimiento
   perezoso de 2 h en listar y cobrar.
7. **PDF:** `generadores/comprobante_pdf.py` con `reportlab`, página de 80 mm de ancho y alto según el número
   de líneas, en memoria; el router devuelve `StreamingResponse`.
8. **Excepciones de dominio** en `core/errors.py` o en el propio submódulo: `STOCK_INSUFICIENTE`,
   `SKU_NO_ENCONTRADO`, `CLIENTE_NO_ENCONTRADO`, `RESERVA_NO_ATENDIBLE`, `SUCURSAL_AJENA`,
   `EMPLEADO_NO_REGISTRADO`, `VENTA_NO_PENDIENTE`, `MONTO_INSUFICIENTE`, `REFERENCIA_REQUERIDA`,
   `CUPON_AGOTADO`, `COMPROBANTE_NO_DISPONIBLE`.
9. **Pruebas:** `tests/modules/compras_pagos/test_cu31_cu32_punto_venta.py`, con un escenario por criterio
   Gherkin. Saldos de inventario comprobados movimiento a movimiento. Más una **verificación end-to-end contra
   Neon**: una venta directa y una desde reserva, cobradas, con comprobación de stock y movimientos, y anulación
   de las órdenes de prueba al terminar.

## Bloque 2 — Web (`src/app/modules/compras_pagos/cu31_cu32_punto_venta/`)

- **Ruta** `/admin/pos` al nivel raíz de `app.routes.ts`, con
  `roleGuard(['administrador','admin','encargado_sucursal','cajero'])` y `← Volver` (Hub-and-Spoke).
  Actualizar `app.routes.spec.ts`.
- **`PosService`** (Signals): los importes son `string`; el estado se reemplaza con la respuesta del servidor;
  sin derivación de importes en el cliente.
- **Página `PuntoVentaComponent`:** pestañas *Nueva venta*, *Pendientes y del día* y *Pedidos web por cobrar*
  (endpoints de CU16).
- **Componentes:** buscador incremental de prendas (nombre, categoría o SKU), panel de cliente, panel de reserva, tabla de líneas,
  panel de cobro y ticket (`@media print`, 80 mm).
- **PDF:** `HttpClient` con `responseType: 'blob'` y descarga con el nombre del comprobante.
- **Panel `/admin`:** tarjeta «Punto de Venta» para administrador y encargado. El cajero no usa el panel: `cajeroACajaGuard` lo lleva a `/admin/pos`.
- **Pruebas:** `ng test` del servicio y la página, y `ng build`.

## Documentación y cierre

Actualizar `checkpoint.md` en cada gate. Al cerrar: `CHANGELOG.md`, nota de numeración en CLAUDE.md y
promoción a `.specs/finalized/` y `.specs/modules/compras_pagos/`.
