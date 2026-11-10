# Especificación Técnica Permanente: Caja en el móvil — P2-CU16 y P2-CU17

**Fuente:** `SI2-Parcial2.md` CU16 (Registrar venta presencial) y CU17 (Procesar venta presencial y
emitir comprobante), «Web/Móvil». Decisiones del usuario del 2026-11-10: E1 entrada directa a la caja,
E2 comprobante en pantalla, E3 pedidos web en efectivo incluidos.
**Paquete de Dominio:** `compras_pagos` · módulo móvil `cu16_cu17_caja` (no confundir con
`cu16_realizar_pago`, el pago electrónico del cliente).
**Backend:** sin cambios: consume el de la caja web (`CU31-CU32-punto-de-venta-presencial.md`).
**Frontend:** sin cambios.
**Mobile:** `lib/src/modulos/compras_pagos/cu16_cu17_caja/` · entrada en `lib/main.dart` (`destinoTrasLogin`).
**Estado:** Aprobado (2026-11-10). Pendiente: prueba manual en dispositivo físico.
**Historial del cambio:** `.specs/finalized/P2-CU16-CU17-caja-movil/`

---

## 1. Entrada y roles (E1)

| Rol | Tras el login | Sucursal |
| :--- | :--- | :--- |
| `cajero`, `encargado_sucursal` | `PantallaCaja`, sin el hub del cliente | Las autorizadas (`/mis-sucursales`); con una sola, sin preguntar |
| `administrador` | `PantallaCaja` | La que elija entre las de su empresa |
| `cliente` | Selección de tienda y hub (sin cambios) | — |
| `super_administrador` | Hub, como antes | — |

Menú de la caja: cambiar de sucursal (si hay más de una), «Reportes por voz» (administrador y
encargado) y «Cerrar sesión». El hub de cuatro raíces sigue siendo solo del cliente (Hub-and-Spoke).

## 2. Reglas

| ID | Regla |
| :--- | :--- |
| R1 | La app solo envía variantes, cantidades, cliente, reserva, cupón y los datos del cobro. Subtotal, descuento, total, IVA incluido y cambio salen del servidor y se muestran tal cual (`formatoImporte`). |
| R2 | Una prenda sin existencias en la sucursal no se añade (CU16 A1). |
| R3 | Un cupón rechazado (`CUPON_*`) se quita con el motivo del servidor y la venta sigue sin descuento (A2); otros errores no se ocultan. |
| R4 | Efectivo: monto recibido. Tarjeta, QR o transferencia: referencia, con «Datáfono rechazó la tarjeta» (`aprobado: false`), que deja la venta pendiente (CU17 A1). |
| R5 | Comprobante en pantalla con los datos de la venta que devuelve el servidor; sin PDF (E2). |
| R6 | Pendientes del día: cobrar o anular con motivo de 3–250 caracteres. Pedidos web en efectivo: confirmar o cancelar (E3). |
| R7 | Sin conexión (`connectivity_plus`) no se registra ni se cobra (CU16 A4, CU17 A4). |
| R8 | `CajaApi` usa `ClienteHttpApi()` (cabecera `X-Tenant` de la empresa del empleado); un 401 vuelve al login (`SesionManager`). |

## 3. Contratos consumidos

`GET /mis-sucursales` · `GET /pos/variantes` · `GET /pos/clientes` · `GET /pos/clientes/{id}/reservas` ·
`GET /pos/reservas/{referencia}` · `GET /pos/cupones` · `POST /pos/ventas/previsualizar` ·
`POST /pos/ventas` · `POST /pos/ventas/{id}/cobrar` · `POST /pos/ventas/{id}/anular` · `GET /pos/ventas` ·
`GET /pos/ventas/{id}` · `GET /pos/pedidos-web-efectivo` · `POST /admin/pagos/{id}/confirmar-efectivo|cancelar-efectivo`.
Con `id_sucursal` en cada petición de la sucursal elegida.

## 4. Pruebas

`test/caja/`: DTO con payloads generados con los esquemas del backend (5), `CajaBloc` con `MockClient`
(12), pantallas (7) y destino tras el login (2).

## 5. Fuera de alcance

PDF, impresión y compartir el comprobante · lector de código de barras · apertura, arqueo y cierre de
caja · funciones del panel web para empleados en el móvil · CU18 (cambio de prenda).
