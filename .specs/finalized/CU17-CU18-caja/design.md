# Diseno Tecnico: Modulo de Caja (CU17 y CU18)

**ID del Cambio:** `CU17-CU18-caja`
**Nivel SDD:** Nivel 3 (Alto riesgo)
**Politica de Emojis:** Cero Emojis en todo el diseno.

---

## 1. Arquitectura y Capas del Backend

Siguiendo el patron monolito modular en capas de FashionStore:
1. **Routers HTTP Delgados:**
   - `app/modules/comercial/cu17_cobro_caja/router.py`: Rutas `/api/v1/caja/ordenes-pendientes` y `/api/v1/caja/cobrar`.
   - `app/modules/reservas/cu18_entrega_reserva/router.py`: Rutas `/api/v1/caja/reservas-pendientes`, `/api/v1/caja/reservas/{id_reserva}/entregar`, `/api/v1/caja/reservas/{id_reserva}/no-asistio`, `/api/v1/caja/reservas/{id_reserva}/convertir-venta`.
2. **Servicios Transaccionales:**
   - `app/modules/comercial/cu17_cobro_caja/servicio.py`: `ServicioCobroCaja` (consultas acotadas por sucursal, calculo de vuelto, cierre de venta, insercion de pago, actualizacion kardex y bitacora).
   - `app/modules/reservas/cu18_entrega_reserva/servicio.py`: `ServicioEntregaReserva` (validacion de citas, recepcion/entrega, liberacion de stock por inasistencia y conversion a venta presencial).
3. **Esquemas Pydantic v2:**
   - `app/modules/comercial/cu17_cobro_caja/esquemas.py`
   - `app/modules/reservas/cu18_entrega_reserva/esquemas.py`
4. **Modelos ORM Existentes Reutilizados:**
   - `fashionstore.ventas`, `fashionstore.venta_detalle`, `fashionstore.pagos`, `fashionstore.reservas`, `fashionstore.reserva_detalle` en `app/modules/comercial/cu28_ventas_reservas/modelos.py`.
   - `fashionstore.inventario_sucursal` en `app/modules/catalogo/modelos.py`.
   - `fashionstore.movimientos_inventario` en `app/modules/gestion_operativa/cu24_inventario_stock/modelos.py`.
   - `fashionstore.bitacora` en `app/modules/seguridad/cu30_bitacora/modelos.py`.

---

## 2. Contratos de API REST

### 2.1 [CU17] Endpoints de Cobro en Caja

#### `GET /api/v1/caja/ordenes-pendientes`
- **Seguridad:** Bearer JWT (`cajero`, `encargado_sucursal`, `administrador`, `admin`).
- **Query Params:**
  * `q`: (str opcional) Busqueda libre por codigo de orden (`FS-YYYY-XXXXXX`) o datos del cliente (nombre, apellido, email, telefono).
  * `fecha_desde`: (date opcional) Fecha inicio de filtro.
  * `fecha_hasta`: (date opcional) Fecha fin de filtro.
  * `id_sucursal`: (int opcional, solo para administrador/admin. Si rol es cajero o encargado, se fuerza `usuario.id_sucursal`).
  * `limite`: int = 50.
  * `salto`: int = 0.
- **Respuesta (200 OK):** `ListadoOrdenesPendientesOut`
  ```json
  {
    "total": 1,
    "items": [
      {
        "id_venta": 105,
        "numero_comprobante": "FS-2026-000105",
        "fecha_venta": "2026-09-28T14:30:00Z",
        "id_sucursal": 1,
        "nombre_sucursal": "Boutique Central",
        "id_cliente": 20,
        "cliente_nombre": "Luciana Mendoza",
        "cliente_documento": "CI-8472910",
        "cliente_telefono": "+591 71234567",
        "tipo_venta": "presencial",
        "estado": "pendiente",
        "subtotal": 850.00,
        "descuento": 0.00,
        "total": 850.00,
        "detalles": [
          {
            "id_venta_detalle": 210,
            "id_variante": 45,
            "sku": "VES-SEDA-NE-S",
            "nombre_producto": "Vestido de Noche Seda",
            "talla": "S",
            "color": "Negro",
            "cantidad": 1,
            "precio_unitario": 850.00,
            "subtotal_linea": 850.00
          }
        ]
      }
    ]
  }
  ```

#### `POST /api/v1/caja/cobrar`
- **Seguridad:** Bearer JWT (`cajero`, `encargado_sucursal`, `administrador`, `admin`).
- **Request Body:** `CobroCajaIn`
  ```json
  {
    "id_venta": 105,
    "monto_recibido": 900.00,
    "metodo_pago": "efectivo",
    "observaciones": "Cobro en caja fisica boutique central"
  }
  ```
- **Respuesta (200 OK):** `CobroCajaOut`
  ```json
  {
    "id_pago": 302,
    "id_venta": 105,
    "numero_comprobante": "FS-2026-000105",
    "monto_total": 850.00,
    "monto_recibido": 900.00,
    "cambio_devuelto": 50.00,
    "metodo_pago": "efectivo",
    "estado_venta": "pagada",
    "estado_pago": "confirmado",
    "cajero_id": 4,
    "cajero_nombre": "Tony Cajero",
    "fecha_cobro": "2026-09-28T21:15:00Z"
  }
  ```
- **Errores:**
  * 400 / 422: `MONTO_INSUFICIENTE` (monto_recibido < total).
  * 403: `SUCURSAL_NO_AUTORIZADA` (la venta pertenece a otra boutique).
  * 404: `VENTA_NO_ENCONTRADA`.
  * 409: `VENTA_YA_LIQUIDADA` o `VENTA_ESTADO_INVALIDO`.

---

### 2.2 [CU18] Endpoints de Entrega de Reserva en Boutique

#### `GET /api/v1/caja/reservas-pendientes`
- **Seguridad:** Bearer JWT (`cajero`, `encargado_sucursal`, `administrador`, `admin`).
- **Query Params:**
  * `q`: (str opcional) Busqueda por codigo (`RES-YYYY-XXXX`) o datos de cliente.
  * `fecha_cita`: (date opcional) Filtro por dia de cita.
  * `id_sucursal`: (int opcional, solo supervisores/admin).
  * `limite`: int = 50.
  * `salto`: int = 0.
- **Respuesta (200 OK):** `ListadoReservasPendientesOut`
  ```json
  {
    "total": 1,
    "items": [
      {
        "id_reserva": 42,
        "codigo_reserva": "RES-2026-0042",
        "id_cliente": 15,
        "cliente_nombre": "Valeria Rios",
        "cliente_documento": "CI-6192834",
        "cliente_telefono": "+591 79876543",
        "id_sucursal": 1,
        "nombre_sucursal": "Boutique Central",
        "fecha_hora_atencion": "2026-09-28T16:00:00Z",
        "estado": "confirmada",
        "canal_origen": "web",
        "observacion": "Prueba de vestido de gala",
        "prendas": [
          {
            "id_reserva_detalle": 80,
            "id_variante": 32,
            "sku": "BLU-LINO-BL-M",
            "nombre_producto": "Blusa de Lino Fino",
            "talla": "M",
            "color": "Blanco",
            "cantidad": 1,
            "precio_unitario": 320.00,
            "ubicacion_percha": "Percha Fitting 3"
          }
        ]
      }
    ]
  }
  ```

#### `POST /api/v1/caja/reservas/{id_reserva}/entregar`
- **Seguridad:** Bearer JWT.
- **Request Body (opcional):** `ConfirmarEntregaIn` (`observaciones`: str opcional).
- **Respuesta (200 OK):** `EntregaReservaOut`
  ```json
  {
    "id_reserva": 42,
    "codigo_reserva": "RES-2026-0042",
    "estado": "atendida",
    "atendido_por": 4,
    "atendido_en": "2026-09-28T21:20:00Z",
    "mensaje": "Entrega y atencion de reserva completada exitosamente."
  }
  ```

#### `POST /api/v1/caja/reservas/{id_reserva}/no-asistio`
- **Seguridad:** Bearer JWT.
- **Respuesta (200 OK):** `NoAsistioReservaOut`
  ```json
  {
    "id_reserva": 42,
    "codigo_reserva": "RES-2026-0042",
    "estado": "cancelada",
    "items_liberados": 1,
    "mensaje": "Reserva marcada como no asistida. Existencias liberadas al stock disponible."
  }
  ```

#### `POST /api/v1/caja/reservas/{id_reserva}/convertir-venta`
- **Seguridad:** Bearer JWT.
- **Respuesta (201 Created):** `ConvertirVentaReservaOut`
  ```json
  {
    "id_venta": 112,
    "numero_comprobante": "FS-2026-000112",
    "id_reserva": 42,
    "total": 320.00,
    "estado_venta": "pendiente",
    "mensaje": "Reserva convertida exitosamente a venta presencial para cobro en caja."
  }
  ```

---

## 3. Manejo Transaccional e Invariantes de Inventario

1. **Bloqueo Defensivo:**
   - En `cobrar`: `SELECT * FROM fashionstore.ventas WHERE id_venta = :id FOR UPDATE`.
   - En `no-asistio`: Bloqueo de fila de reserva y bloqueo de las filas de `fashionstore.inventario_sucursal` (`FOR UPDATE`) para asegurar que la devolucion de existencias `cantidad_reservada -= cant` y `cantidad_disponible += cant` sea estrictamente atomica.
2. **Kardex Obligatorio:**
   - En cobro de venta: si la venta no tenia movimientos de stock previos (venta presencial directa), se descuentan existencias y se asienta `tipo_movimiento='venta_confirmada'`. Si ya habia retencion (Click & Collect CU15), se consolida el movimiento.
   - En inasistencia: se asienta `tipo_movimiento='liberacion_reserva'` con saldos anterior y nuevo reales.
3. **Auditoria No Bloqueante:**
   - Evento `COBRO_CAJA` para CU17.
   - Evento `ENTREGA_RESERVA` para CU18 (tanto en entrega normal como en inasistencia y conversion).
