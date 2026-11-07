# Tareas — CU17: Consultar Historial de Compras

## Bloque 1 — Backend (`Ec-backend`)

- [x] **T-BE-01:** Crear `app/modules/compras_pagos/cu17_historial_compras/esquemas.py` con `ItemHistorialCompraOut`, `PedidoHistorialOut` y `HistorialComprasOut`.
- [x] **T-BE-02:** Crear `repositorio.py` y `servicio.py` en `cu17_historial_compras/` reutilizando `VentaORM`, `VentaDetalleORM` y `PagoORM` (con expiración perezosa de órdenes pendientes vencidas y orden `fecha_venta DESC, id_venta DESC`).
- [x] **T-BE-03:** Crear `router.py` con `GET /api/v1/ventas/mias` y registrarlo en `app/modules/compras_pagos/router.py`.
- [x] **T-BE-04:** Añadir pruebas en `tests/modules/compras_pagos/test_cu17_historial_compras.py` y verificar con `pytest` y `ruff check`.

## Bloque 2 — Frontend Web (`Ec-frontend`)

- [x] **T-FE-01:** Añadir DTOs del historial de compras en `perfil.dto.ts` y consumir `GET /api/v1/ventas/mias` en `perfil.service.ts`, eliminando los 3 pedidos harcodeados (`PED-001`..`PED-003`).
- [x] **T-FE-02:** Actualizar `perfil.component.ts` y `perfil.component.html` con el contador real, estado de carga, estado vacío y modal de comprobante digital (reemplazando el `alert`).
- [x] **T-FE-03:** Actualizar `perfil.component.spec.ts` y verificar con `npm test -- --watch=false` y `npm run build`.

## Bloque 3 — Móvil (`Ec-mobile`)

- [x] **T-MO-01:** Actualizar `perfil_dto.dart`, `perfil_api.dart`, `perfil_repositorio.dart` y `perfil_bloc.dart` para consumir `GET /api/v1/ventas/mias`.
- [x] **T-MO-02:** Eliminar la lista estática `_pedidos` en `pantalla_perfil.dart`, mostrar el conteo real, el estado vacío y el `ModalBottomSheet` con el comprobante digital.
- [x] **T-MO-03:** Añadir pruebas de DTO/widget para CU17 y verificar con `flutter analyze` y `flutter test`.

