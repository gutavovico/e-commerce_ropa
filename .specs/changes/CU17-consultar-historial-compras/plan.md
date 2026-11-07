# Plan Técnico — CU17: Consultar Historial de Compras

## Estrategia por Bloques

Siguiendo la regla de trabajo de `CLAUDE.md`, la implementación se divide en 3 bloques independientes con compuerta de aprobación entre ellos:
1. **Bloque 1 — Backend (`Ec-backend`)**
2. **Bloque 2 — Frontend Web (`Ec-frontend`)**
3. **Bloque 3 — Móvil (`Ec-mobile`)**

---

## Bloque 1 — Backend (`Ec-backend`)

### Estructura de Archivos

Se creará el subpaquete `app/modules/compras_pagos/cu17_historial_compras/`:
- `__init__.py`
- `esquemas.py`: Modelos Pydantic `ItemHistorialCompraOut`, `PedidoHistorialOut`, `HistorialComprasOut`.
- `repositorio.py`: `RepositorioHistorialCompras` con `listar_ventas_cliente(db, id_cliente: int) -> Sequence[VentaORM]` ordenada por `fecha_venta DESC, id_venta DESC`. Reutiliza `VentaORM`, `VentaDetalleORM` y `PagoORM` desde `app/modules/compras_pagos/modelos.py` (**sin redeclarar tablas ORM**).
- `servicio.py`: `ServicioHistorialCompras.obtener_historial_cliente(db, usuario)`:
  1. Ejecuta la expiración perezosa de órdenes `pendiente` vencidas del cliente (reutilizando `PagoRepositorio` / `PagoServicio` de CU16) para no mostrar como pendientes órdenes cuyo plazo expiró.
  2. Obtiene las ventas del cliente desde `RepositorioHistorialCompras`.
  3. Mapea cada `VentaORM` a `PedidoHistorialOut`, calculando `pedidos_completados` (`estado in ('pagada', 'entregada')`).
- `router.py`: Expone `GET /mias` (montado bajo `/api/v1/ventas` en `app/modules/compras_pagos/router.py` → ruta final `GET /api/v1/ventas/mias`).

### Pruebas Backend
- `tests/modules/compras_pagos/test_cu17_historial_compras.py`:
  - Cliente con compras: verifica orden cronológico descendente, conteo `total_pedidos` / `pedidos_completados`, desglose de `items` y datos de pago.
  - Cliente sin compras: verifica respuesta `200 OK` con lista vacía (`total_pedidos = 0`).
  - Petición sin token: verifica `401 Unauthorized`.

---

## Bloque 2 — Frontend Web (`Ec-frontend`)

### Archivos a Modificar
- `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/modelos/perfil.dto.ts`:
  - Añadir interfaces `ItemHistorialCompraDto`, `PedidoHistorialDto` e `HistorialComprasDto` alineadas 1:1 con `GET /api/v1/ventas/mias`.
- `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/servicios/perfil.service.ts`:
  - Eliminar el arreglo harcodeado de `pedidos` (`PED-001`, `PED-002`, `PED-003`).
  - Añadir señales `pedidos`, `totalPedidos`, `pedidosCompletados`, `cargandoPedidos` y método `cargarHistorialCompras()` que consuma `GET /api/v1/ventas/mias`.
- `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component.ts` y `perfil.component.html`:
  - Invocar `cargarHistorialCompras()` al inicializar el perfil.
  - Reemplazar el badge estático `5 PEDIDOS COMPLETADOS` por el contador real.
  - Mostrar estados de carga, vacío (con enlace a `/catalogo`) y lista de pedidos reales con sus ítems, canal (`digital_web`, `digital_movil`, `presencial`), sucursal/entrega y estado (`pagada`, `pendiente`, `entregada`, `anulada`).
  - Reemplazar `alert(...)` en `descargarFactura(pedido)` por un modal limpio de **Comprobante Digital** con opción de imprimir (`window.print()`) o continuar al checkout si la orden está `pendiente`.
- `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component.spec.ts`:
  - Actualizar pruebas unitarias para validar la carga de `/api/v1/ventas/mias`, el estado vacío y el modal de comprobante.

---

## Bloque 3 — Móvil (`Ec-mobile`)

### Archivos a Modificar
- `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/datos/modelos/perfil_dto.dart`:
  - Actualizar `PedidoMovilDto` y añadir `ItemPedidoMovilDto` e `HistorialComprasMovilDto` con `fromJson` para mapear `GET /api/v1/ventas/mias`.
- `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/datos/fuentes/perfil_api.dart` y `repositorios/perfil_repositorio.dart`:
  - Añadir `obtenerHistorialCompras()` consumiendo `GET /api/v1/ventas/mias`.
- `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/bloc/perfil_bloc.dart` (y `perfil_estado.dart`):
  - Cargar el historial junto con el perfil (sin bloquear la carga del perfil si el historial falla, exponiendo la lista real de pedidos).
- `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart`:
  - Eliminar la lista estática `_pedidos` (`PED-01`..`PED-03`) y el texto fijo `'3 pedidos'`.
  - Renderizar el estado vacío o las tarjetas reales de compra y abrir un `showModalBottomSheet` con el comprobante digital detallado al tocar una orden.
- `test/`: Añadir/actualizar prueba de deserialización y widget para el historial real.

