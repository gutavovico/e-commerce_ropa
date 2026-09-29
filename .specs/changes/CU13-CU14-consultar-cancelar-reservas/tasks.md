# Tareas: CU13 — Consultar y Cancelar Reservas (con CU14 integrado)

Estado: **Bloques 1 (Backend), 2 (Web) y 3 (Mobile) completos.** Pendiente de cierre (T-DOC-02) tras aprobación final del usuario.

## Bloque 1 — Backend

- [x] **T-BE-01**: Extraída `modules/reservas/utilidades.py::formatear_codigo_reserva`; CU12 la reutiliza (antes duplicaba el formato inline).
- [x] **T-BE-02**: `esquemas.py` de CU13 (`ReservaOut`, `ReservaItemOut`, `SucursalReservaOut`, `ResumenReservasOut`, `MisReservasOut`, `ReservaCancelarIn` con motivo 3-250).
- [x] **T-BE-03**: `repositorio.py`: listado por cliente (sin bloqueo, es lectura), `obtener_reserva_para_actualizar` con `FOR UPDATE`, `buscar_movimiento_reserva` (join a `inventario_sucursal` por variante), `obtener_inventario_por_id` con `FOR UPDATE`, `registrar_movimiento_liberacion`.
- [x] **T-BE-04**: `servicio.py`: `_liberar_stock` compartido entre cancelar y vencer (saldos sobre `cantidad_disponible`, igual que `cancelacion_pedido` de CU15 — verificado contra datos reales antes de escribir el código), `_vencer_si_corresponde` con relectura bloqueada (evita liberar dos veces por condición de carrera), `cancelar_reserva`, `listar_mis_reservas` con `puede_cancelar`/`resumen` calculados en el servidor.
- [x] **T-BE-05**: Bitácora `CANCELAR_RESERVA` y `VENCER_RESERVA` (CU30).
- [x] **T-BE-06**: `router.py` (`GET /reservas/mias`, `POST /reservas/{id_reserva}/cancelar`, rol `cliente`) registrado en `reservas/router.py`. Verificado en el esquema OpenAPI real de la app.
- [x] **T-BE-07**: `test_cu13_consultar_cancelar.py` — 25 pruebas (todos los escenarios Gherkin de `spec.md` §A.3 + localización correcta de la fila de inventario + idempotencia del vencimiento perezoso + doble cancelación).
- [x] **T-BE-08**: Suite completa 487/487 (462 previas + 25 nuevas). Verificado end-to-end contra Neon real en transacciones revertidas: (a) `listar_mis_reservas` sobre las 7 reservas reales y vencidas del cliente #2 — las 7 pasaron a `vencida` y su inventario volvió a `cantidad_reservada = 0`; (b) ciclo completo `crear_reserva_presencial` (CU12) → `cancelar_reserva` (CU13) sobre una reserva nueva — el inventario volvió exactamente a su valor original (13→11→13).

## Bloque 2 — Web ✅ Completo

- [x] **T-FE-01**: `reserva.model.ts` espejo del contrato (importes `string`).
- [x] **T-FE-02**: `MisReservasService` con Signals y traducción de errores. `cancelarReserva` recarga la lista completa desde el servidor tras el `200` en vez de parchear el estado local: el backend decide el nuevo reparto próximas/historial.
- [x] **T-FE-03**: Ruta raíz `/reservas` con `authGuard`, declarada como hoja fuera de `MainLayoutComponent`; `app.routes.spec.ts` con 2 pruebas nuevas (hoja fuera del layout, protegida por guard).
- [x] **T-FE-04**: `MisReservasComponent`: cabecera con `← Volver` (`Location.back()`), pestañas Próximas/Historial, tarjetas con badges de estado (HEX de `fashionstore-tokens.md` como valores arbitrarios de color — permitido; la restricción de la constitución es solo sobre espaciados), estados de carga (skeleton)/vacío (`Explorar Catálogo`)/error (reintento).
- [x] **T-FE-05**: `ModalCancelarReservaComponent` con motivo obligatorio (3-250, contador de caracteres) y protección de doble envío (`cancelando` deshabilita ambos botones).
- [x] **T-FE-06**: Tarjeta «Mis Reservas» en `perfil.component.html` (sustituye «Bolsa de Compra» y su literal «3 Artículos seleccionados · 1.250 €» inventado) — datos reales de `MisReservasService.resumen()`, con estado de carga y vacío propios.
- [x] **T-FE-07**: 31 pruebas nuevas (`mis-reservas.service.spec.ts` 6, `modal-cancelar-reserva.component.spec.ts` 8, `mis-reservas.component.spec.ts` 12, más 3 en `perfil.component.spec.ts` y 2 en `app.routes.spec.ts`) con payloads literales del backend. Web 538/538, `tsc --noEmit` limpio, `ng build` de producción exitoso. `ng serve` sirviendo `/perfil` y `/reservas` verificado (200, sin errores de compilación).

## Bloque 3 — Mobile ✅ Completo

- [x] **T-MO-01**: `reserva_dto.dart` con `fromJson` tolerante (`ReservaItemDto`, `SucursalReservaDto`, `ReservaDto`, `ResumenProximaReservaDto`, `ResumenReservasDto`, `MisReservasDto`); `precio_unitario` con `parsearImporte` (Decimal → cadena JSON).
- [x] **T-MO-02**: `ReservasApi`/`ReservasApiImpl` (401 → `SesionManager.notificarSesionExpirada`, `ReservaException` con `esNoCancelable`/`esAjena`/`esVencida`), espejo exacto de `PagoApiImpl`.
- [x] **T-MO-03**: `MisReservasBloc` con estados sellados (`Inicial`/`Cargando`/`Listo`/`Error`) y campos separados `cancelando`/`errorCancelacion` para que una cancelación en vuelo no oculte la lista ya cargada.
- [x] **T-MO-04**: `PantallaMisReservas` (hoja: `AppBar` con `BackButton`, sin `bottomNavigationBar`, pestañas Próximas/Historial, `RefreshIndicator`, badges de estado con los mismos HEX que Web).
- [x] **T-MO-05**: `HojaCancelarReserva` (bottom sheet) con motivo obligatorio (3-250), deshabilitado mientras `cancelando`, permanece abierta mostrando el error del servidor si la cancelación es rechazada.
- [x] **T-MO-06**: Tarjeta "Mis Reservas" en `pantalla_perfil.dart` (sustituye la de "Bolsa" y su literal `3 Artículos · 1.250 €`), con `MisReservasBloc` propagado igual que `PerfilBloc`, y `_abrirMisReservas` vía `Navigator.push`.
- [x] **T-MO-07**: 19 pruebas nuevas (`reserva_dto_test.dart` 6, `mis_reservas_bloc_test.dart` 5, `pantalla_mis_reservas_test.dart` 8) más el ajuste de `pantalla_perfil_test.dart` para inyectar `misReservasBloc` y actualizar las aserciones. Mobile 209/209 (190 previas + 19 nuevas), `dart analyze` limpio. Confirmado que `pantalla_principal_hub_test.dart` sigue en verde sin mock de `MisReservasBloc` (mismo patrón ya existente con `PerfilBloc`: el fallo de red se captura y transiciona a estado de error, sin llamada de red real hacia afuera del entorno de test).

## Cierre

- [x] **T-DOC-01**: Entradas en `CHANGELOG.md` y `.specs/CHANGELOG.md` (reservas vencidas reteniendo stock; literales inventados eliminados del Perfil).
- [ ] **T-DOC-02**: Promoción a `.specs/finalized/` y `.specs/modules/` tras aprobar el último bloque.
