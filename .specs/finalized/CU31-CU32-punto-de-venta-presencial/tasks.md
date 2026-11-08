# Tareas — CU31-CU32: Punto de Venta Presencial

## Bloque 0 — Personal en `empleados` (D3)

- [x] **T-0-01:** CU20 crea la fila de `empleados` al dar de alta o cambiar a un rol de personal. Pruebas del alta y del cambio de rol.
- [x] **T-0-02:** Script idempotente de regularización para el personal existente sin fila; ejecutarlo en Neon y verificar los usuarios 13 y 14.

## Bloque 1 — Backend

- [x] **T-BE-01:** Extraer la función de precios por líneas `(variante, cantidad)` y la separación validar/consumir del cupón; CU11/CU15 la reutilizan con sus suites en verde.
- [x] **T-BE-02:** Servicio de atención en caja en el paquete `reservas` (`obtener_para_caja`, `consolidar_lineas`, `liberar_lineas`) con sus pruebas.
- [x] **T-BE-03:** Esquemas Pydantic del POS (importes `Decimal`, serializados como cadena).
- [x] **T-BE-04:** Repositorio del POS: variante por SKU con stock de la sucursal, cliente por correo y ventas de la sucursal; `FOR UPDATE` donde haya escritura.
- [x] **T-BE-05:** `registrar_venta` (CU31) con retención, bitácora y reglas POS-01 a POS-05.
- [x] **T-BE-06:** `previsualizar` (sin persistir ni consumir cupón).
- [x] **T-BE-07:** `cobrar_venta` (CU32), reglas POS-06 a POS-09, incluido el rechazo de tarjeta y la idempotencia.
- [x] **T-BE-08:** `anular_venta` y vencimiento perezoso de 2 h (POS-10).
- [x] **T-BE-09:** Generador `comprobante_pdf.py` (80 mm) y endpoint `GET /ventas/{id}/comprobante.pdf`.
- [x] **T-BE-10:** Router `/api/v1/pos` con `ROLES_CAJA`, montado en `compras_pagos/router.py`.
- [x] **T-BE-11:** Suite `test_cu31_cu32_punto_venta.py` (un escenario por criterio Gherkin, saldos movimiento a movimiento).
- [x] **T-BE-12:** Verificación end-to-end contra Neon (venta directa y desde reserva) y limpieza de los datos de prueba.

## Bloque 2 — Web

- [x] **T-FE-01:** DTOs y `PosService` (importes como `string`, PDF como `Blob`).
- [x] **T-FE-02:** Ruta `/admin/pos` con guard de roles de caja y prueba de orden de rutas.
- [x] **T-FE-03:** Pestaña «Nueva venta»: búsqueda de prendas, cliente, reserva, cupón, líneas y totales desde `previsualizar`.
- [x] **T-FE-10 (delta del usuario, 2026-11-08):** búsquedas incrementales sin mención a escáner: prendas por nombre/categoría/SKU con todas las coincidencias; clientes por nombre o correo (sin cuenta → presencial); reservas activas del cliente elegido; cupones (todos con el campo vacío, filtrados por código o nombre). Backend: `GET /pos/variantes?q`, `GET /pos/clientes?q` (sustituye a `?email`), `GET /pos/clientes/{id}/reservas`, `GET /pos/cupones`; 7 pruebas nuevas y consultas verificadas en Neon en solo lectura.
- [x] **T-FE-04:** Panel de cobro (efectivo con monto recibido; tarjeta, QR y transferencia con referencia; rechazo de tarjeta).
- [x] **T-FE-05:** Ticket imprimible de 80 mm y botón «Descargar PDF».
- [x] **T-FE-06:** Pestaña «Pendientes y del día» (cobrar, anular con motivo, reimprimir, PDF).
- [x] **T-FE-07:** Pestaña «Pedidos web por cobrar» (endpoints de CU16).
- [x] **T-FE-08:** Tarjeta «Punto de Venta» en el panel `/admin` para los roles de caja. Delta (decisión del usuario, 2026-11-08): la tarjeta es solo para administrador y encargado; el cajero **no comparte el panel corporativo**: el login lo lleva a `/admin/pos`, `cajeroACajaGuard` lo devuelve a la caja desde `/admin` (y desde `/admin/atributos` y `/admin/productos`, que no tenían guard de rol) y la caja le muestra su nombre y «Cerrar sesión» en lugar de «Volver al Panel Principal».
- [x] **T-FE-09:** Pruebas (`ng test`), `tsc --noEmit` y `ng build`.

## Cierre

- [x] **T-CI-01:** `CHANGELOG.md`, nota de numeración en CLAUDE.md, promoción a `.specs/finalized/` y spec permanente en `.specs/modules/compras_pagos/`.
