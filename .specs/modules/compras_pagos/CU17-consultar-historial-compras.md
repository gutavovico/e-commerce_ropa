# Especificación Técnica Permanente: CU17 — Consultar Historial de Compras

**Código:** CU17
**Paquete de Dominio:** `compras_pagos`
**Backend:** `app/modules/compras_pagos/cu17_historial_compras/`
**Frontend:** `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/` (sección de pedidos de `/perfil`)
**Mobile:** `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/` (`PantallaPerfil`)
**Actor:** Cliente autenticado
**Estado:** Aprobado y promovido a permanente (2026-11-08)
**Historial del cambio:** `.specs/finalized/CU17-consultar-historial-compras/`

---

## 1. Contrato

### `GET /api/v1/ventas/mias` (JWT obligatorio; `401` sin sesión)

`{total_pedidos, pedidos_completados, pedidos[]}`, solo ventas con `id_cliente` del usuario, ordenadas por `fecha_venta DESC, id_venta DESC`, de cualquier canal (`digital_web`, `digital_movil`, `presencial`).

Cada pedido: `id_venta`, `numero_comprobante`, `fecha_venta`, `tipo_venta`, `estado`, `tipo_entrega`, `nombre_sucursal`, `nombre_sucursal_retiro`, `direccion_envio`, `codigo_promocion`, `subtotal`, `descuento`, `total`, `metodo_pago`, `referencia_pasarela` (del pago confirmado o, si sigue pendiente, del último intento) e `items[]` (`id_venta_detalle`, `id_producto`, `id_variante`, `sku`, `nombre_producto`, `imagen_url`, `talla`, `color`, `color_hex`, `cantidad`, `precio_unitario`, `subtotal_linea`, `nombre_sucursal`).

Sin compras: `200` con `{total_pedidos: 0, pedidos_completados: 0, pedidos: []}`.

## 2. Reglas

- Antes de responder se aplica la expiración perezosa de las órdenes pendientes cuyo plazo de pago venció (lógica de `PagoServicio`), para que el historial refleje el estado real.
- Cero datos inventados: web y móvil pintan el conteo y los pedidos reales; con lista vacía, estado vacío con acceso al catálogo.
- «Ver comprobante» abre un modal u hoja con los datos del comprobante (número, fecha, canal, sucursal o entrega, líneas, subtotal, descuento, total y método de pago).
- Importes `Decimal` serializados como cadena; los clientes no los recalculan.
