# Tareas · P2-CU16 y P2-CU17 — Caja en el móvil
**Fase SDD:** 3 de 4 (Tareas) · **Estado:** borrador · Contexto: `spec.md`, `plan.md`

Cada tarea se marca **en cuanto se termina y se verifica**, con lo que cambió respecto a lo planeado.

## Bloque único — Móvil

### Oleada 1 — Datos
- [x] **T-01 · DTO y `CajaApi`** (`cu16_cu17_caja/datos/{modelos_caja,caja_api}.dart`), con `ClienteHttpApi()` y `CajaException`.
  - Hecho (2026-11-10): `VentaCaja` reutiliza `PrevisualizacionCaja` para sus totales; payloads compartidos en `test/caja/payloads_caja.dart`.
  - Verificado: `flutter test test/caja/caja_dto_test.dart` 5/5; `dart analyze` sin incidencias.

### Oleada 2 — Estado
- [x] **T-02 · `CajaBloc`**: sucursal, venta en curso, previsualizar, registrar, cobrar, anular, pendientes y pedidos web.
  - Hecho (2026-11-10). Cambió: un cupón inválido (400 `CUPON_INVALIDO`) se quita y se vuelve a previsualizar sin él; otros errores no se ocultan. El bloc ignora notificaciones tras `dispose` (una petición puede terminar después de cerrar la caja).
  - Verificado: `flutter test test/caja` 17/17 (12 del bloc con `MockClient` y payloads literales); `dart analyze` sin incidencias.

### Oleada 3 — Pantallas
- [x] **T-03 · `PantallaCaja`** (raíz del empleado) con buscador, cliente y reservas, cupón y barra de total. Criterios: AC-2, AC-4–AC-9, AC-15, AC-16.
  - Hecho (2026-11-10). Cambió: el menú (cambiar de sucursal, «Reportes por voz», «Cerrar sesión») y el acceso a las ventas del día van en la barra superior; no se crearon `widgets/` aparte (todo cabe en la pantalla).
  - Verificado: `test/caja/pantallas_caja_test.dart` (búsqueda, total del servidor, sin conexión, menú por rol, selector de sucursal).
- [x] **T-04 · `PantallaCobro` y `PantallaComprobante`.** Criterios: AC-10–AC-12.
  - Hecho (2026-11-10). Verificado: registrar → cobrar en efectivo → comprobante con el cambio del servidor (prueba de widget).
- [x] **T-05 · `PantallaVentasCaja`**: pendientes, del día y pedidos web. Criterios: AC-13, AC-14.
  - Hecho (2026-11-10). Corregido durante la prueba: el diálogo del motivo liberaba su controlador mientras animaba el cierre (rompía el árbol); ahora es un diálogo con estado propio.
  - Verificado: prueba de widget de pendientes, pedidos web y anulación con motivo; `flutter test test/caja` 24/24.
- [x] **T-06 · Entrada desde `main.dart`**: empleado → caja; menú con «Reportes por voz» (administrador y encargado) y «Cerrar sesión». Criterios: AC-1, AC-2.
  - Hecho (2026-11-10). Cambió: la decisión de destino es una función pura `destinoTrasLogin(rol)` (cliente → elegir tienda; administrador, encargado y cajero → caja; super administrador → hub, como hasta ahora), porque el login usa el repositorio HTTP real y no se puede probar de punta a punta sin red.
  - Verificado: `test/caja/destino_tras_login_test.dart`; `flutter test test/caja` 26/26.

### Oleada 4 — Verificación
- [x] **T-07 ·** `dart analyze --fatal-infos` y `flutter test` en verde; pruebas de widget de entrada y cobro.
  - Verificado (2026-11-10): análisis sin incidencias; `flutter test` 325/325 (26 nuevas en `test/caja/`); guardas en verde.
- [ ] **T-08 ·** Prueba manual en dispositivo físico (venta en efectivo y con tarjeta). Pendiente del usuario.

## Publicación y cierre
- [ ] **T-PR-01 (usuario) ·** Commit, push y PR de `p2/caja-movil` (sin migración), con el cierre incluido.
- [x] **T-PR-02 ·** `CHANGELOG.md`, spec permanente (`.specs/modules/compras_pagos/P2-CU16-CU17-caja-movil.md`), «Mobile: excluido» corregido en la spec de CU31-CU32, regla del personal en `CLAUDE.md` y promoción a `finalized/` (2026-11-10).
