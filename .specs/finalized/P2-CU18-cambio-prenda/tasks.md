# Tareas · P2-CU18 — Registrar cambio de prenda
**Fase SDD:** 3 de 4 (Tareas) · **Estado:** aprobado · Contexto: `spec.md`, `plan.md`

Cada tarea se marca **en cuanto se termina y se verifica**, con lo que cambió respecto a lo planeado.

## Bloque 1 — Backend
- [x] **T-BE-01 · Migración `0021_cambios_prenda`** y modelos ORM. Verificación: `upgrade → downgrade → upgrade` en `pruebas-multitenant`; `test_esquema_bd`.
  - Hecho (2026-11-10): CHECK de que `diferencia = valor_nuevo − valor_devuelto` y de que solo las devueltas llevan línea de venta; modelos `CambioPrendaORM` y `CambioPrendaDetalleORM` en `compras_pagos/modelos.py`.
  - Verificado: `0020 → 0021 → 0020 → 0021` en `pruebas-multitenant`; `alembic heads` = `0021`; `test_esquema_bd` 4/4.
- [x] **T-BE-02 · Servicio**: venta cambiable, prorrateo (F2), previsualizar, registrar (inventario, cobro, comprobante, bitácora). Criterios: AC-1–AC-10. Verificación: unitarias de `tests/modules/compras_pagos/test_p2_cu18_cambio_prenda.py`.
  - Hecho (2026-11-10): `cu18_cambio_prenda/{esquemas,repositorio,servicio}.py`. Reutiliza `PuntoVentaServicio.resolver_sucursal`, el precio vigente de la caja (`CarritoServicio.precio_linea`) y su bitácora. Cambió: si la sucursal no tenía fila para la prenda devuelta, se crea con la temporada más reciente de la variante; el comprobante es correlativo por empresa bajo `pg_advisory_xact_lock`; 422 `COBRO_REQUERIDO` si falta el cobro de una diferencia positiva.
  - Verificado: 17/17 (prorrateo, plazo con hora de Bolivia, cantidades, stock, cobro y registro con movimientos).
- [x] **T-BE-03 · Router** `/api/v1/pos/cambios` con roles y sucursal. Criterios: AC-12.
  - Hecho (2026-11-10): `GET /venta`, `POST /previsualizar`, `POST ""` (con `requiere_funcionalidad("ventas")`), `GET ""` y `GET /{id}`; registrado en `compras_pagos/router.py`.
  - Verificado: 3 pruebas de contrato (403 cliente, 409 con `dias_transcurridos` y `plazo_dias`, 422 cambio vacío); archivo 20/20.
- [x] **T-BE-04 · Integración** (`tests/integracion/test_multitenant.py`): kardex, aislamiento y concurrencia. Criterios: AC-8, AC-11, AC-12.
  - Hecho (2026-11-10): 3 pruebas contra `pruebas-multitenant`: cambio completo con cupón repartido (90,00), `COBRO_REQUERIDO`, cobro con vuelto, movimientos `devolucion`/`venta_confirmada`, venta que sigue `pagada`, RN31, aislamiento con FASHION STORE; plazo vencido con los días; dos cambios a la vez sobre la última unidad (uno pasa, el otro `CANTIDAD_NO_CAMBIABLE`).
  - Cambió: la limpieza del fixture `empresa_confirmada` (bloque 3) incluye ahora ventas, cambios, empleados y usuarios de la empresa.
  - Verificado: 5/5 (las 3 de CU18 y las 2 de concurrencia del bloque 3); la rama de pruebas queda limpia.
- [x] **T-BE-05 · Suite y guardas**: `pytest -q` completo y `guardas.sh`.
  - Verificado (2026-11-10): `pytest` 875/875 con integración contra `pruebas-multitenant`; guardas en verde.

## Bloque 2 — Web
- [x] **T-WEB-01 · Servicio y modelos** de cambios en `cu31_cu32_punto_venta`.
  - Hecho (2026-11-10): `modelos/cambio-prenda.dto.ts` (importes como `string`) y `servicios/cambio-prenda.service.ts`.
  - Verificado: `tsc` sin errores; `cambio-prenda.service.spec.ts` 2/2 con el payload generado por el backend.
- [x] **T-WEB-02 · Pestaña «Cambios»** en `/admin/pos` con ticket imprimible y bloqueo sin red. Criterios: AC-1, AC-6, AC-7, AC-9, AC-13.
  - Hecho (2026-11-10). Cambió: la pestaña es un componente propio, `componentes/cambio-prenda/` (la página de la caja ya rondaba las 800 líneas); reutiliza el buscador de prendas de la caja y los estilos del ticket (`pos-ticket`, `pos-no-imprimir`).
  - Verificado: `cambio-prenda.component.spec.ts` 3/3 (flujo completo con cobro y ticket, plazo vencido, sin conexión); specs de la caja 26/26.
- [x] **T-WEB-03 ·** `tsc`, `ng test`, `ng build` y guardas en verde.
  - Verificado (2026-11-10): `tsc` sin errores; `ng test` 711/711 (5 nuevas); `ng build` correcto; guardas en verde.

## Bloque 3 — Móvil
- [x] **T-MOV-01 · DTO y API** de cambios en `cu16_cu17_caja` (o módulo `cu18_cambio_prenda`).
  - Hecho (2026-11-10): módulo propio `cu18_cambio_prenda/datos/cambio_prenda_api.dart` (DTO `VentaCambiable`, `LineaCambiable`, `CambioPrenda`, `LineaCambio`; importes como `String`). Cambió: para no duplicar el manejo HTTP y de errores, `CajaApi._enviar` pasó a ser público como `CajaApi.solicitar`, que reutiliza `CambioPrendaApi`.
  - Verificado: `dart analyze` sin incidencias; `test/cambio/cambio_dto_test.dart` 2/2 con los payloads literales generados por el backend.
- [x] **T-MOV-02 · Bloc y pantalla «Cambio de prenda»** desde el menú de la caja; comprobante en pantalla. Criterios: AC-1, AC-6, AC-7, AC-9, AC-13.
  - Hecho (2026-11-10): `presentacion/bloc/cambio_prenda_bloc.dart` (estados sellados `CambioSinVenta` / `CambioEligiendo` / `CambioRegistrado`; solo vale la última previsualización pedida) y `presentacion/pantallas/pantalla_cambio_prenda.dart` (hoja con `BackButton`, barra de acción con la diferencia del servidor, cobro con los cinco métodos, comprobante en pantalla y «Nuevo cambio»). Opción «Cambio de prenda» en el menú de `PantallaCaja` cuando hay sucursal.
  - Cambió: la pantalla reutiliza la caja abierta (sucursal, buscador de prendas, estado de la red y su `CajaApi`, expuesto con `CajaBloc.api`); `ServidorCaja` de las pruebas admite `otrasRutas`.
  - Verificado: `test/cambio/cambio_prenda_test.dart` 3/3 (flujo completo con cobro, vuelto y comprobante; plazo vencido con el mensaje del servidor; sin conexión deshabilita registrar).
- [ ] **T-MOV-03 ·** `dart analyze --fatal-infos` y `flutter test` en verde; prueba manual en dispositivo físico.
  - Verificado (2026-11-10): `dart analyze --fatal-infos` sin incidencias; `flutter test` 330/330 (5 nuevas); guardas en verde.
  - Pendiente: prueba manual en dispositivo físico (usuario).

## Publicación y cierre
- [ ] **T-PR-01 (usuario) ·** Aplicar `0021` en producción antes del push; PR con los seis checks.
- [x] **T-PR-02 ·** `CHANGELOG.md`, spec permanente, `CLAUDE.md` (cadena `0021`) y promoción a `finalized/`.
  - Hecho (2026-11-10): entrada en `CHANGELOG.md` (sin defecto numerado: es funcionalidad nueva); `.specs/modules/compras_pagos/P2-CU18-cambio-prenda.md`; `CLAUDE.md` con la cadena hasta `0021`, siguiente `0022`, el módulo en `compras_pagos` y la regla de reutilizar `CajaBloc` en las hojas de empleado; carpeta movida a `.specs/finalized/P2-CU18-cambio-prenda/`.
  - Cambió: `CLAUDE.md` ya da producción en `0021`; solo es cierto tras T-PR-01, que va antes del push.
