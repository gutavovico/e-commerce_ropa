# Especificación Técnica Permanente: Cambio de prenda — P2-CU18

**Fuente:** `SI2-Parcial2.md` CU18 «Registrar cambio de prenda» (Web/Móvil, con conexión), RN30 (plazo),
RN31 (cantidad cambiada), RN32 (inventario en cambios), CU11 (`dias_cambio_prenda`). Decisiones del
usuario del 2026-11-10: F1 la diferencia a favor del cliente se devuelve en efectivo · F2 la prenda
devuelta vale lo pagado, con el cupón repartido · F3 backend, web y móvil.
**Paquete de Dominio:** `compras_pagos`.
**Backend:** `app/modules/compras_pagos/cu18_cambio_prenda/` · modelos `CambioPrendaORM` y
`CambioPrendaDetalleORM` en `compras_pagos/modelos.py` · migración `0021_cambios_prenda`.
**Frontend:** `cu31_cu32_punto_venta/componentes/cambio-prenda/`, `servicios/cambio-prenda.service.ts`,
`modelos/cambio-prenda.dto.ts`; pestaña «Cambios» de `/admin/pos`.
**Mobile:** `lib/src/modulos/compras_pagos/cu18_cambio_prenda/` (`datos/cambio_prenda_api.dart`,
`presentacion/bloc/cambio_prenda_bloc.dart`, `presentacion/pantallas/pantalla_cambio_prenda.dart`);
entrada desde el menú de `PantallaCaja`.
**Estado:** Aprobado (2026-11-10). Pendiente: prueba manual en dispositivo físico.
**Historial del cambio:** `.specs/finalized/P2-CU18-cambio-prenda/`

---

## 1. Actores

Cajero, encargado de sucursal y administrador (roles de la caja), en una sucursal autorizada (RN07,
`SucursalesEmpleadoServicio.autoriza`), con suscripción vigente y la funcionalidad «ventas», y con
conexión. El cliente trae el número de comprobante de una venta **pagada** de la empresa.

## 2. Reglas

| ID | Regla |
| :--- | :--- |
| R1 | Plazo: días transcurridos desde la venta, en hora de Bolivia (`core/tiempo.py`), ≤ `dias_cambio_prenda` (`ParametrosEmpresaServicio.vigentes`). `0` = la empresa no admite cambios. |
| R2 | Unidades por cambiar de una línea = vendidas − Σ devueltas en cambios anteriores (RN31). Una venta admite varios cambios. |
| R3 | Valor unitario devuelto (F2) = `precio_unitario × ventas.total / Σ subtotal_linea`, redondeado a 2 decimales y nunca mayor que el precio de la línea. Sin cupón, el precio de la línea. |
| R4 | Valor de las prendas nuevas: precio vigente con sus promociones (cálculo de la caja), sin cupón. |
| R5 | `diferencia = valor_nuevo − valor_devuelto`. `> 0` se cobra (efectivo con monto y vuelto; tarjeta, QR o transferencia con referencia). `< 0` se devuelve en efectivo (F1). `= 0` sin cobro. |
| R6 | Todo importe lo calcula el servidor; los que envíe la app se ignoran. |
| R7 | Inventario de la sucursal del cambio (RN32): la devuelta entra (movimiento `devolucion`), la nueva sale (`venta_confirmada`), con referencia `CAMBIO-{id}` y el empleado como responsable. Si la sucursal no tenía fila para la devuelta, se crea con la temporada más reciente de la variante. |
| R8 | La venta original no cambia: sigue `pagada` con sus totales. El cambio es un documento propio con comprobante `CAM-AAAA-NNNNN`, correlativo por empresa. |
| R9 | No se cambia una prenda recibida en un cambio (no pertenece a la venta original). |

## 3. Contrato (`/api/v1/pos/cambios`, JWT de un rol de caja)

| Método y ruta | Entrada | Salida |
| :--- | :--- | :--- |
| `GET /venta?comprobante=&id_sucursal=` | — | `VentaCambiableOut`: venta, fecha, cliente, `dias_transcurridos`, `plazo_dias`, líneas con `vendidas`, `ya_cambiadas`, `cambiables`, `valor_unitario` |
| `POST /previsualizar` | `CambioIn` | `CambioPrevioOut`: `devueltas`, `nuevas`, `valor_devuelto`, `valor_nuevo`, `diferencia` |
| `POST ""` (`requiere_funcionalidad("ventas")`) | `CambioIn` con `cobro` | 201 `CambioOut`: lo anterior más comprobante, sucursal, quién atendió, cobro (`metodo_pago`, `monto_recibido`, `vuelto`, `referencia`) y `devuelto_al_cliente` |
| `GET ?id_sucursal=&solo_hoy=` · `GET /{id}` | — | `CambioOut` |

`CambioIn = {id_venta, id_sucursal?, devueltas: [{id_venta_detalle, cantidad}], nuevas: [{id_variante,
cantidad}], cobro?: {metodo_pago, monto_recibido?, referencia?}}`; `devueltas` y `nuevas` con al menos
una línea. Los importes viajan como cadena (`Decimal`).

| Caso | Respuesta |
| :--- | :--- |
| Venta inexistente, de otra empresa o no pagada | 404 `VENTA_NO_ENCONTRADA` |
| Plazo vencido o cambios desactivados | 409 `PLAZO_DE_CAMBIO_VENCIDO`, con `dias_transcurridos` y `plazo_dias` |
| Línea ajena o más unidades de las que quedan | 409 `CANTIDAD_NO_CAMBIABLE` |
| Prenda nueva sin stock en la sucursal | 409 `STOCK_INSUFICIENTE` |
| Cambio vacío | 422 |
| Diferencia positiva sin cobro · monto corto · sin referencia | 422 `COBRO_REQUERIDO` / `MONTO_INSUFICIENTE` / `REFERENCIA_REQUERIDA` |
| Sucursal no autorizada · suscripción | 403 `SUCURSAL_AJENA` / `SUSCRIPCION_NO_VIGENTE` |

## 4. Datos (`0021_cambios_prenda`)

Tablas de empresa con `id_tenant` (valor por defecto del contexto), `UNIQUE (id_tenant, pk)`, FK
compuestas, política `aislamiento_tenant` y permisos de `fashionstore_app`:

- `cambios_prenda`: comprobante (`UNIQUE (id_tenant, numero_comprobante)`), venta, sucursal, usuario,
  `creado_en`, `valor_devuelto`, `valor_nuevo`, `diferencia` (`CHECK diferencia = valor_nuevo −
  valor_devuelto`), `metodo_pago`, `monto_recibido`, `vuelto`, `referencia`.
- `cambio_prenda_detalle`: `tipo` (`devuelta`/`nueva`), `id_venta_detalle` (solo las devueltas, por
  `CHECK`), variante, `cantidad > 0`, `precio_unitario`, `subtotal`.

No modifica tablas existentes; reversible.

## 5. Transacción y concurrencia

Una transacción por cambio: `SELECT … FOR UPDATE` de la venta (serializa dos cambios sobre la misma
venta) → plazo y unidades por cambiar → inventario con `FOR UPDATE` en orden de `id_inventario` y sus
movimientos → cobro → comprobante bajo `pg_advisory_xact_lock` por empresa → bitácora `CAMBIO_PRENDA`
(`registrar_evento_seguro`). Dos cambios simultáneos sobre la última unidad: pasa uno; el otro recibe
`CANTIDAD_NO_CAMBIABLE` (prueba de integración con dos conexiones).

## 6. Web y móvil

| | Web (`/admin/pos`, pestaña «Cambios») | Móvil (menú de la caja → «Cambio de prenda») |
| :--- | :--- | :--- |
| Flujo | Comprobante → qué devuelve (± hasta lo cambiable) → qué se lleva (buscador de la caja) → diferencia del servidor → cobro o devolución → registrar | Igual; hoja con `BackButton` y barra de acción con la diferencia |
| Comprobante | Ticket imprimible (`pos-ticket`) | En pantalla, con «Nuevo cambio» |
| Sin conexión | Aviso y botón deshabilitado | Aviso y botón deshabilitado (estado de red de la caja) |
| Reutiliza | Buscador y estilos del ticket de la caja | `CajaBloc` (sucursal, búsqueda, red, `api`) y `CajaApi.solicitar` |

## 7. Pruebas

- **Backend:** `tests/modules/compras_pagos/test_p2_cu18_cambio_prenda.py` (20: plazo, cantidades,
  prorrateo con y sin cupón, diferencia, cobro, registro, contrato) e integración en
  `tests/integracion/test_multitenant.py` (3: cambio completo con kardex y aislamiento, plazo vencido,
  concurrencia real).
- **Web:** `cambio-prenda.service.spec.ts` (2) y `cambio-prenda.component.spec.ts` (3), con payloads
  generados por el backend.
- **Móvil:** `test/cambio/cambio_dto_test.dart` (2) y `cambio_prenda_test.dart` (3), con payloads
  literales (`payloads_cambio.dart`).

## 8. Fuera de alcance

Devolución sin cambio (reembolso) y notas de crédito; cambiar otra vez una prenda recibida en un
cambio; reflejar los cambios en reportes, indicadores y predicciones; PDF del comprobante.
