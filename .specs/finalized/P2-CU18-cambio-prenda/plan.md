# Diseño · P2-CU18 — Registrar cambio de prenda
**Requisitos:** `spec.md` · **Fase SDD:** 2 de 4 (Diseño) · **Estado:** aprobado

## 1. Enfoque

- **Backend:** `compras_pagos/cu18_cambio_prenda` (`router`, `servicio`, `repositorio`, `esquemas`) bajo
  `/api/v1/pos/cambios`, con los mismos roles y alcance de sucursal que la caja (`ROLES_CAJA`,
  `SucursalesEmpleadoServicio.autoriza`). Reutiliza la búsqueda de prendas de la caja
  (`GET /pos/variantes`) y su validación de cobro.
- **Cambio = documento propio** (`cambios_prenda`), asociado a la venta original, que sigue `pagada`.
  No se crea una venta nueva: así los totales de la venta original no cambian.
- **Web:** pestaña «Cambios» en la caja `/admin/pos`. **Móvil:** «Cambio de prenda» en la caja.

## 2. Contrato (`/api/v1/pos/cambios`, JWT de un rol de caja)

| Método y ruta | Entrada | Salida | Códigos |
| :--- | :--- | :--- | :--- |
| `GET /venta?comprobante=&id_sucursal=` | — | `VentaCambiableOut`: venta, fecha, días transcurridos, plazo, líneas con `vendidas`, `ya_cambiadas`, `cambiables`, `valor_unitario` | 200 · 404 · 409 plazo |
| `POST /previsualizar` | `CambioIn` | `CambioPrevioOut`: líneas devueltas y nuevas con valores, `valor_devuelto`, `valor_nuevo`, `diferencia` | 200 · 404 · 409 · 422 |
| `POST ""` | `CambioIn` + `cobro` | `CambioOut` (comprobante) | 201 · 400 · 403 · 404 · 409 · 422 |
| `GET ?id_sucursal=&solo_hoy=` · `GET /{id}` | — | `CambioOut` | 200 · 404 |

`CambioIn`: `{id_venta, id_sucursal?, devueltas: [{id_venta_detalle, cantidad}], nuevas: [{id_variante,
cantidad}], cobro?: {metodo_pago, monto_recibido?, referencia?}}`. El servidor ignora cualquier importe
que envíe la app.

## 3. Cálculo (servidor, `Decimal`)

- **Valor unitario devuelto (F2):** `precio_unitario × ventas.total / Σ subtotal_linea`, redondeado a
  2 decimales. Las líneas ya llevan las promociones de la prenda y `ventas.total` es lo pagado, así que
  el factor reparte solo el cupón; sin cupón vale 1 y el valor es el precio de la línea. Nunca supera
  lo pagado por esa línea.
- **Valor de las nuevas:** precio vigente con las promociones de la prenda (mismo cálculo que la caja),
  sin cupón.
- **Diferencia** = nuevo − devuelto. `> 0` se cobra (validación de la caja: `MONTO_INSUFICIENTE`,
  `REFERENCIA_REQUERIDA`); `< 0` se devuelve en efectivo (F1); `= 0` sin cobro.

## 4. Datos — migración `0021_cambios_prenda` (`down_revision = "0020"`)

Tablas de empresa (`id_tenant` con valor por defecto del contexto, `UNIQUE (id_tenant, pk)`, FK
compuestas, RLS `aislamiento_tenant`, permisos de `fashionstore_app`):

| Tabla | Columnas |
| :--- | :--- |
| `cambios_prenda` | `id_cambio`, `numero_comprobante` (`UNIQUE (id_tenant, numero_comprobante)`, `CAM-AAAA-NNNNN`), `id_venta`, `id_sucursal`, `id_usuario` (quien atiende), `creado_en`, `valor_devuelto`, `valor_nuevo`, `diferencia` (`NUMERIC(12,2)`), `metodo_pago` (nulo si diferencia ≤ 0), `monto_recibido`, `vuelto`, `referencia` |
| `cambio_prenda_detalle` | `id_cambio_detalle`, `id_cambio`, `tipo` (`devuelta`/`nueva`, `CHECK`), `id_venta_detalle` (solo devuelta), `id_variante`, `cantidad > 0`, `precio_unitario`, `subtotal` |

Sin cambios en tablas existentes, así que el código anterior sigue funcionando entre la migración y el
despliegue. Reversible.

## 5. Transacción y concurrencia

Una transacción por cambio:
1. `SELECT … FOR UPDATE` de la venta (serializa dos cambios sobre la misma venta, AC-11).
2. Plazo (AC-3) y unidades por cambiar = vendidas − Σ devueltas en cambios anteriores (AC-4).
3. Inventario con `FOR UPDATE` en orden de `id_inventario`: la devuelta entra en `cantidad_disponible`
   de la sucursal del cambio (movimiento `devolucion`); la nueva sale (movimiento `venta_confirmada`).
   Referencia `CAMBIO-{id}`, responsable el empleado. La fila de la devuelta es la de su temporada más
   reciente en esa sucursal; si no existe, se crea con la temporada vigente.
4. Cobro de la diferencia validado; comprobante `CAM-AAAA-NNNNN` con bloqueo de la secuencia por
   empresa (`pg_advisory_xact_lock`).
5. Bitácora `CAMBIO_PRENDA` (`registrar_evento_seguro`).

## 6. Web y móvil

- **Web:** pestaña «Cambios» en `/admin/pos`: buscar comprobante → líneas con cantidad a devolver →
  buscador de prendas nuevas → totales del servidor → cobro o devolución → ticket imprimible. Sin red,
  deshabilitado.
- **Móvil:** «Cambio de prenda» en el menú de la caja (hoja con `BackButton`), mismo flujo; comprobante
  en pantalla. `ClienteHttpApi()` y payloads literales en las pruebas.

## 7. Riesgos

| Riesgo | Decisión |
| :--- | :--- |
| Devolver más de lo pagado con cupón | Prorrateo F2 con tope en lo pagado; pruebas con y sin cupón. |
| Doble cambio concurrente de la misma línea | `FOR UPDATE` de la venta; prueba de integración con dos conexiones. |
| Última unidad de la prenda nueva | `FOR UPDATE` del inventario; prueba de integración. |
| Venta web (domicilio o recogida) | Se puede cambiar en cualquier sucursal autorizada del empleado; el stock entra y sale de esa sucursal. |
| Numeración del comprobante | Secuencia por empresa bajo bloqueo; `UNIQUE` como última defensa. |
| Migración `0021` | Avisar al equipo del número; ensayo `upgrade → downgrade → upgrade` en `pruebas-multitenant`; producción a mano antes del push. |

## 8. Pruebas

| AC | Prueba |
| :--- | :--- |
| 1–7, 10 | Unitarias del servicio: plazo (dentro, límite, vencido, 0), cantidades, línea ajena, prorrateo con y sin cupón, diferencia ±0, cobro |
| 8 | Integración: movimientos `devolucion` y `venta_confirmada`, saldos, comprobante único |
| 11 | Integración concurrente: dos cambios sobre la última unidad cambiable; última unidad de la prenda nueva |
| 12 | Integración: aislamiento entre empresas; 403 en sucursal no autorizada |
| Web | Pestaña «Cambios» con payloads literales; sin red deshabilitado |
| Móvil | DTO y bloc con payloads literales; pantalla del cambio |
