# Especificacion Tecnica Formal: Modulo de Caja (CU17 y CU18)

**ID del Cambio:** `CU17-CU18-caja`
**Modulos Afectados:** `comercial` (CU17: Cobro en Caja) y `reservas` (CU18: Entrega de Reserva en Boutique)
**Casos de Uso:**
- **CU17:** Registrar cobro en caja
- **CU18:** Atender entrega de reserva en boutique
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)
**Nivel SDD:** Nivel 3 (Alto riesgo: transacciones monetarias en caja fisica, transiciones de venta, liquidacion de inventario, liberacion de reservas)
**Fuente de Verdad de Datos:** PostgreSQL en Neon (`fashionstore.ventas`, `fashionstore.venta_detalle`, `fashionstore.pagos`, `fashionstore.reservas`, `fashionstore.reserva_detalle`, `fashionstore.inventario_sucursal`, `fashionstore.movimientos_inventario`, `fashionstore.bitacora`)
**Politica de Emojis:** Cero Emojis en todo el ciclo de vida del cambio.

---

## 1. Justificacion de Exclusion Formal de Ec-mobile

Las operaciones de punto de venta (POS), cobro fisico de mostrador, apertura y cuadre de operaciones de caja, y recepcion y despacho de clientes en cita de mostrador corresponden a terminales de escritorio instaladas en la recepcion de la boutique fisica.

1. **Ec-mobile:** Aplicacion orientada al cliente final para navegacion de catalogo, compra digital y probador virtual con Realidad Aumentada. No contiene funciones operativas de mostrador. Cero modificaciones en Flutter.
2. **Ec-frontend:** Aplicacion web institucional utilizada por personal de boutique y clientes en escritorio. Aloja el panel de mostrador para cajeros y supervisores (`/caja/cobro` y `/caja/reservas`).

---

## 2. Matriz de Control de Acceso y Segregacion Territorial (RBAC)

| Rol | Alcance Territorial | Permiso CU17 (Cobro) | Permiso CU18 (Reservas) |
| :--- | :--- | :--- | :--- |
| `cajero` | Estrictamente acotado a `usuario.id_sucursal` | Permitido (operacion mostrador) | Permitido (entrega y no-asistio) |
| `encargado_sucursal` | Estrictamente acotado a `usuario.id_sucursal` | Permitido (supervision y operacion) | Permitido (supervision y operacion) |
| `administrador` / `admin` | Global (todas las sucursales o filtro opcional) | Permitido (control total) | Permitido (control total) |
| `cliente` | N/A | Denegado (HTTP 403 Forbidden) | Denegado (HTTP 403 Forbidden) |
| `proveedor` | N/A | Denegado (HTTP 403 Forbidden) | Denegado (HTTP 403 Forbidden) |
| Anonimo (sin token) | N/A | Denegado (HTTP 401 Unauthorized) | Denegado (HTTP 401 Unauthorized) |

---

## 3. Requisitos en Formato EARS

### 3.1 Requisitos Ubicuos (Ubiquitous)
- **REQ-UB-01:** El sistema debera exigir autenticacion mediante token Bearer JWT en todos los endpoints de caja (`/api/v1/caja/...`). Si la peticion no contiene un token valido, el sistema respondera HTTP 401.
- **REQ-UB-02:** El sistema debera denegar el acceso con HTTP 403 a usuarios con rol `cliente` o `proveedor` en cualquier operacion de mostrador o caja.
- **REQ-UB-03:** Toda transaccion de cobro confirmada o alteracion de reserva debera registrar un evento no bloqueante en la bitacora inmutable (`fashionstore.bitacora`), con la direccion IP y el usuario responsable.

### 3.2 Requisitos Basados en Estado (State-driven)
- **REQ-CU17-SD-01:** Cuando un usuario con rol `cajero` o `encargado_sucursal` consulte ordenes pendientes (`GET /api/v1/caja/ordenes-pendientes`), el sistema debera restringir los resultados exclusivamente a las ordenes pertenecientes a `usuario.id_sucursal`.
- **REQ-CU17-SD-02:** Cuando un usuario con rol `administrador` o `admin` consulte ordenes pendientes, el sistema debera permitir consultar cualquier sucursal o aplicar un filtro explicito por `id_sucursal`.
- **REQ-CU18-SD-01:** Cuando un usuario con rol `cajero` o `encargado_sucursal` consulte reservas pendientes (`GET /api/v1/caja/reservas-pendientes`), el sistema debera restringir los resultados a las reservas de `usuario.id_sucursal`.

### 3.3 Requisitos Dirigidos por Eventos (Event-driven)
- **REQ-CU17-ED-01:** Cuando el cajero busque ordenes pendientes con parametros de busqueda (codigo de orden `FS-YYYY-XXXXXX`, cliente o rango de fecha), el sistema debera retornar las ordenes en estado `pendiente` con sus prendas, cantidades, precios y total a cobrar.
- **REQ-CU17-ED-02:** Cuando el cajero registre el cobro de una orden (`POST /api/v1/caja/cobrar`), el sistema debera validar que `monto_recibido >= total_orden`, calcular `cambio_devuelto = monto_recibido - total_orden`, actualizar el estado de la venta a `pagada`, registrar el comprobante en `fashionstore.pagos` con estado `confirmado` y actualizar el Kardex en `fashionstore.movimientos_inventario`.
- **REQ-CU18-ED-01:** Cuando el cajero confirme la entrega de prendas reservadas (`POST /api/v1/caja/reservas/{id_reserva}/entregar`), el sistema debera validar que la reserva se encuentre en estado `confirmada`, `pendiente` o `en_atencion`, cambiar su estado a `atendida`, actualizar la cantidad reservada en inventario y registrar el evento `ENTREGA_RESERVA` en bitacora.
- **REQ-CU18-ED-02:** Cuando el cajero marque una reserva como no asistida (`POST /api/v1/caja/reservas/{id_reserva}/no-asistio`), el sistema debera cambiar el estado a `cancelada`, devolver el stock apartado a disponible (`cantidad_reservada -= cant`, `cantidad_disponible += cant`), asentar un movimiento `liberacion_reserva` en el Kardex y registrar la auditoria.
- **REQ-CU18-ED-03:** Cuando el cliente decida comprar inmediatamente las prendas de una reserva en boutique (`POST /api/v1/caja/reservas/{id_reserva}/convertir-venta`), el sistema debera generar una orden de venta presencial (`tipo_venta='presencial'`, `estado='pendiente'`), vincular `id_reserva`, marcar la reserva como `atendida` y retornar la orden lista para cobro inmediato en caja.

### 3.4 Requisitos para Casos No Deseados (Unwanted Behavior)
- **REQ-CU17-UW-01:** Si el `monto_recibido` es inferior al total de la orden, el sistema debera rechazar la operacion con HTTP 422 y codigo `MONTO_INSUFICIENTE`.
- **REQ-CU17-UW-02:** Si la orden pertenece a una sucursal distinta a la del cajero, el sistema debera rechazar con HTTP 403 y codigo `SUCURSAL_NO_AUTORIZADA`.
- **REQ-CU17-UW-03:** Si la orden ya se encuentra en estado `pagada` o `anulada`, el sistema debera rechazar con HTTP 409 y codigo `VENTA_YA_LIQUIDADA` o `VENTA_ESTADO_INVALIDO`.
- **REQ-CU18-UW-01:** Si la reserva pertenece a otra sucursal, el sistema debera responder HTTP 403 y codigo `SUCURSAL_NO_AUTORIZADA`.
- **REQ-CU18-UW-02:** Si la reserva ya esta `atendida` o `cancelada`, el sistema debera rechazar la accion con HTTP 409 y codigo `RESERVA_ESTADO_INVALIDO`.
