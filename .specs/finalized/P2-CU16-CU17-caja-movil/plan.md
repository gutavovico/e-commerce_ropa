# Diseño · P2-CU16 y P2-CU17 — Caja en el móvil
**Requisitos:** `spec.md` · **Fase SDD:** 2 de 4 (Diseño) · **Estado:** borrador

## 1. Enfoque

- **Solo móvil.** Ni backend ni web cambian: la app consume `/api/v1/pos`, `/api/v1/mis-sucursales`
  y `/api/v1/admin/pagos/{id}/confirmar-efectivo|cancelar-efectivo` con el mismo contrato que la caja
  web (`.specs/modules/compras_pagos/CU31-CU32-punto-de-venta-presencial.md` §3).
- **Entrada (E1):** `main.dart` abre `PantallaCaja` para los roles de empleado en lugar del hub. La caja
  es el «espacio del empleado»: no lleva la barra de 4 pestañas del cliente (Hub-and-Spoke sigue
  intacto para el cliente) y sus subpantallas se abren con `Navigator.push` y `BackButton`.
- **Estado:** `CajaBloc` (`ChangeNotifier` con estados sellados, como el resto de la app): sucursal,
  venta en curso (líneas, cliente, reserva, cupón), previsualización, venta en cobro, pendientes y
  pedidos web.
- **Dinero:** la app solo envía variantes, cantidades, cupón, reserva y datos del cobro; muestra lo que
  devuelve el servidor (cadenas `Decimal`, parseo tolerante).
- **Sin conexión:** `connectivity_plus` (ya instalada) deshabilita registrar y cobrar (AC-15).

Descartado: reutilizar el hub con una pestaña «Caja» (rompe la regla de exactamente cuatro raíces) y
generar el ticket en el teléfono (E2: lo que se muestra es lo que devuelve el servidor).

## 2. Contratos que se consumen (sin cambios)

| Método y ruta | Uso en la app |
| :--- | :--- |
| `GET /mis-sucursales` | Sucursales del empleado (selector si hay más de una o es administrador) |
| `GET /pos/variantes?q=&id_sucursal=` | Buscador (300 ms de espera, mín. 2 caracteres) |
| `GET /pos/clientes?q=` · `GET /pos/clientes/{id}/reservas?id_sucursal=` | Cliente y sus reservas |
| `GET /pos/reservas/{referencia}?id_sucursal=` | Carga por código |
| `GET /pos/cupones?q=` | Cupones vigentes |
| `POST /pos/ventas/previsualizar` · `POST /pos/ventas` | Totales y registro (cuerpo `VentaPosIn`) |
| `POST /pos/ventas/{id}/cobrar` | `{metodo_pago, monto_recibido, referencia, aprobado}` |
| `POST /pos/ventas/{id}/anular` | `{motivo}` |
| `GET /pos/ventas?estado=&solo_hoy=&id_sucursal=` · `GET /pos/ventas/{id}` | Pendientes, del día y comprobante |
| `GET /pos/pedidos-web-efectivo?id_sucursal=` | Pedidos web por cobrar (E3) |
| `POST /admin/pagos/{id}/confirmar-efectivo` · `cancelar-efectivo` | Cobro de un pedido web |

El administrador envía `id_sucursal` en cada petición (si falta: `422 SUCURSAL_REQUERIDA`).

## 3. Capas y archivos

| Capa | Archivos |
| :--- | :--- |
| `datos/` | `lib/src/modulos/compras_pagos/cu16_cu17_caja/datos/{caja_api.dart, modelos_caja.dart}` — DTO con `fromJson` y `CajaApi` con `ClienteHttpApi()` (cabecera `X-Tenant` de la empresa del empleado) y `CajaException {mensaje, codigoHttp, codigo}` |
| `presentacion/` | `bloc/caja_bloc.dart` · `pantallas/pantalla_caja.dart` (raíz del empleado: sucursal, nueva venta, total, «Registrar y cobrar») · `pantallas/pantalla_cobro.dart` · `pantallas/pantalla_comprobante.dart` · `pantallas/pantalla_ventas_caja.dart` (pendientes, del día y pedidos web) · `widgets/` (buscador, línea, cliente y reservas, cupón) |
| Entrada | `lib/main.dart` (`_despuesDelLogin` / `_abrirHub`): empleado → `PantallaCaja` |

## 4. Reglas y estados

- Registrar y cobrar se deshabilitan mientras haya una petición en curso (doble toque = una sola venta).
- Tras registrar, la venta pasa al estado «en cobro»; si el cobro se rechaza, sigue pendiente y se
  puede reintentar con otro medio; si se abandona, queda en «Pendientes» (el servidor la vence a las 2 h).
- `RenderFlex overflowed`: `Expanded`/`Flexible` con `ellipsis` en nombres; los importes en `Wrap`.
- Tokens de `AppTheme` (`AppSpacing`, `AppColors`, `AppTypography`, `AppRadius`); marca con
  `EmpresaActual.instancia.marca`.

## 5. Riesgos

| Riesgo | Decisión |
| :--- | :--- |
| Empleado sin ficha de `empleados` | El servidor responde 409 `EMPLEADO_NO_REGISTRADO`; la app lo muestra. |
| DTO que no coinciden con el backend (lección de CU12 móvil) | Pruebas con payloads literales generados con los esquemas Pydantic de `cu31_cu32_punto_venta`. |
| El administrador olvida elegir sucursal | Selector obligatorio antes de buscar prendas. |
| Pantallas largas en móviles pequeños | Una columna con desplazamiento; el total y la acción en la barra inferior (`bottomNavigationBar` de acción, admitido por la directriz). |

## 6. Estrategia de pruebas

| AC | Prueba |
| :--- | :--- |
| 1, 3 | Widget: login de empleado abre `PantallaCaja`; selector según las sucursales |
| 4–9 | `CajaBloc` con `MockClient`: buscar, añadir, previsualizar (totales del servidor), cupón inválido, reserva, registrar |
| 10–11 | Cobro en efectivo con cambio del servidor; monto insuficiente; rechazo del datáfono |
| 12–14 | Comprobante con payload literal; anular con motivo; pedidos web |
| 15 | Sin conexión: botones deshabilitados |
| DTO | `fromJson` de cada respuesta con payloads literales |
| Manual | Dispositivo físico: venta en efectivo y con tarjeta en una sucursal de prueba |
