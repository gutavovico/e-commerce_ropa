# Especificación — CU17: Consultar Historial de Compras

## 1. Contexto y Objetivo

En `SI2-Parcial1.md` (sección 2.1.4.2), el caso de uso **CU17. Consultar historial de compras** permite al cliente autenticado revisar el histórico consolidado de sus compras realizadas en cualquier canal (`digital_web`, `digital_movil`, `presencial`), ordenadas de la más reciente a la más antigua, junto con el desglose de productos adquiridos (`venta_detalle`) y la visualización de su comprobante digital.

Actualmente:
- **Backend (`Ec-backend`):** Cuenta con `GET /api/v1/pagos/ordenes/{id_venta}` (CU15/CU16, detalle unitario para checkout), pero **no existe** un endpoint que liste todas las compras del cliente autenticado.
- **Web (`Ec-frontend`):** `perfil.service.ts` tiene un arreglo estático de 3 pedidos inventados (`PED-001`, `PED-002`, `PED-003` en Madrid/París), `perfil.component.html` muestra el badge fijo `5 PEDIDOS COMPLETADOS`, y el botón «VER FACTURA DIGITAL» dispara un `alert(...)`.
- **Móvil (`Ec-mobile`):** `pantalla_perfil.dart` tiene una lista fija `_pedidos` con los mismos 3 pedidos inventados (`PED-01`..`PED-03`) y el texto fijo `'3 pedidos'`.

Esta especificación define el contrato y comportamiento para reemplazar todos los datos estáticos por consultas reales a PostgreSQL (`fashionstore.ventas`, `fashionstore.venta_detalle`, `fashionstore.pagos`), cumpliendo la regla **Cero datos inventados**.

---

## 2. Esquema de Base de Datos (Sin Migración)

No se requiere ninguna migración de Alembic (`0011` se mantiene como `head`). Las tablas ya existen en Neon y están mapeadas en `app/modules/comercial/cu28_ventas_reservas/modelos.py` (re-exportadas en `app/modules/compras_pagos/modelos.py`):

- `fashionstore.ventas` (`VentaORM`) — cabecera con `id_venta`, `numero_comprobante`, `id_cliente`, `id_sucursal`, `tipo_venta`, `tipo_entrega`, `id_sucursal_retiro`, `direccion_envio`, `subtotal`, `descuento`, `total`, `estado`, `fecha_venta`.
- `fashionstore.venta_detalle` (`VentaDetalleORM`) — líneas con `id_venta_detalle`, `id_variante`, `id_sucursal`, `cantidad`, `precio_unitario`, `subtotal_linea`.
- `fashionstore.pagos` (`PagoORM`) — registros de pago con `metodo_pago`, `estado_pago`, `referencia_pasarela`, `confirmado_en`.

---

## 3. Contrato del Endpoint

### `GET /api/v1/ventas/mias`

- **Autenticación:** Requiere JWT válido (`obtener_usuario_actual`).
- **Ordenamiento:** `fecha_venta DESC, id_venta DESC`.
- **Expiración perezosa:** Antes de construir la respuesta, si el cliente tiene órdenes en estado `pendiente` cuyo plazo de pago ya venció (reutilizando la lógica de expiración de `PagoServicio`), se anulan y liberan stock para que el historial refleje el estado real.

#### Respuesta `200 OK` (`HistorialComprasOut`)

```json
{
  "total_pedidos": 2,
  "pedidos_completados": 1,
  "pedidos": [
    {
      "id_venta": 42,
      "numero_comprobante": "FS-20260411-000042",
      "fecha_venta": "2026-04-11T15:30:00Z",
      "tipo_venta": "digital_web",
      "estado": "pagada",
      "tipo_entrega": "envio_domicilio",
      "nombre_sucursal": "Boutique Equipetrol",
      "nombre_sucursal_retiro": null,
      "direccion_envio": "Av. San Martín #450, Santa Cruz",
      "codigo_promocion": null,
      "subtotal": "890.00",
      "descuento": "0.00",
      "total": "890.00",
      "metodo_pago": "tarjeta_debito",
      "referencia_pasarela": "pi_3Pxyz...",
      "items": [
        {
          "id_venta_detalle": 101,
          "id_producto": 7,
          "id_variante": 19,
          "sku": "FS-ABR-007-M-NEG",
          "nombre_producto": "Abrigo de Lana Merino",
          "imagen_url": "https://...",
          "talla": "M",
          "color": "Negro",
          "color_hex": "#111111",
          "cantidad": 1,
          "precio_unitario": "890.00",
          "subtotal_linea": "890.00",
          "nombre_sucursal": "Boutique Equipetrol"
        }
      ]
    }
  ]
}
```

> Si el cliente no registra compras, responde `200 OK` con `{"total_pedidos": 0, "pedidos_completados": 0, "pedidos": []}`.

---

## 4. Requisitos (Formato EARS)

- **REQ-CU17-01 (Listado autenticado):** **Cuando** un usuario autenticado envíe `GET /api/v1/ventas/mias`, el sistema **deberá** retornar únicamente las ventas donde `ventas.id_cliente == usuario.id_usuario`, ordenadas por `fecha_venta DESC, id_venta DESC`, incluyendo su desglose `items` y el método/referencia del pago confirmado (o del último intento de pago si sigue pendiente).
- **REQ-CU17-02 (Rechazo sin sesión):** **Si** la petición a `GET /api/v1/ventas/mias` no incluye un token JWT válido, el sistema **deberá** responder `401 Unauthorized`.
- **REQ-CU17-03 (Cero datos inventados en Web y Móvil):** **Cuando** se abra la vista de Perfil en Web (`/perfil`) o Móvil (`PantallaPerfil`), el sistema **deberá** consultar `GET /api/v1/ventas/mias` y renderizar el conteo real (`pedidos_completados` / `total_pedidos`) y las tarjetas reales de compra; **en ningún caso** mostrará pedidos harcodeados.
- **REQ-CU17-04 (Estado vacío):** **Si** `pedidos` está vacío (`total_pedidos == 0`), tanto Web como Móvil **deberán** mostrar un estado vacío informativo con opción de ir al catálogo (Flujo Alternativo 4a de `SI2-Parcial1.md`).
- **REQ-CU17-05 (Comprobante digital):** **Cuando** el cliente pulse «Ver comprobante / factura digital» en un pedido del historial (Web o Móvil), el sistema **deberá** abrir un modal/hoja de detalle con los datos del comprobante (`numero_comprobante`, fecha, canal, sucursal/entrega, líneas con talla/color/cantidad/precio, subtotal, descuento, total y método de pago), reemplazando el `alert(...)` temporal.

