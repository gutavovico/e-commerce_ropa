# Dominio de FashionStore (para el backend)

## Contenido
1. Modelo de datos en resumen
2. Estados y transiciones
3. Invariantes que el backend debe garantizar
4. Contratos de API ya definidos (pruebas del documento)
5. Riesgos y huecos conocidos del diseño (leer antes de nivel 3)
6. Estado de especificación por CU

Fuente: DDL y casos de uso del documento del proyecto. Lo marcado **(propuesta)** no está en el documento y debe validarse en la fase de Requisitos.

---

## 1. Modelo de datos en resumen

Esquema `fashionstore`; extensiones `pgcrypto`, `citext`, `pg_trgm`.

| Grupo | Tablas | Notas |
|---|---|---|
| Ubicación | `ciudades`, `sucursales` | `sucursales.activa`; horario de apertura/cierre |
| Usuarios | `usuarios`, `clientes`, `empleados` | `usuarios.rol` (enum), `email` CITEXT único, `id_sucursal` nulo para clientes; `clientes` y `empleados` extienden a `usuarios` (PK = FK) |
| Proveedores | `proveedores` | `id_usuario` opcional (acceso al sistema) |
| Catálogo | `temporadas`, `colecciones`, `categorias` (con padre), `tallas`, `colores`, `productos`, `variantes_producto` | SKU = producto + talla + color; `sku` único; `UNIQUE(producto, talla, color)`; `productos.modelo_ar_url` habilita el vestidor |
| Inventario | `inventario_sucursal`, `movimientos_inventario` | `UNIQUE(variante, sucursal, temporada)`; `cantidad_disponible ≥ 0`, `cantidad_reservada ≥ 0`; trigger recalcula `estado` |
| Reservas | `reservas`, `reserva_detalle` | `UNIQUE(reserva, variante)`; `canal_origen` web/movil/sucursal |
| AR | `sesiones_vestidor_virtual` | `genero_interes` = terminó en carrito o reserva |
| Compras | `carritos` (uno por cliente), `carrito_detalle` (con `id_sucursal`), `ventas`, `venta_detalle`, `pagos` | `venta_detalle.subtotal_linea` es columna **generada** (no se inserta); `pagos.payload_respuesta` JSONB (auditoría) |
| Promociones | `promociones`, `promocion_producto` | `porcentaje_descuento` 0–100; `fecha_fin ≥ fecha_inicio` |
| IA | `historial_navegacion`, `recomendaciones_ia`, `interacciones_chatbot`, `solicitudes_reporte_ia` | `score_relevancia` 0–1 |
| Vistas | `vw_inventario_consolidado`, `vw_ventas_por_sucursal`, `vw_reservas_pendientes` | Base de reportes y dashboards; solo lectura |

Enums: `rol_usuario`, `estado_reserva`, `estado_prenda_stock`, `tipo_movimiento_inv`, `tipo_venta`, `estado_venta`, `estado_pago`, `metodo_pago`, `canal_origen`, `tipo_temporada`.

Lógica ya en la BD: trigger de estado de inventario (`trg_inventario_estado`), trigger de descuento de stock (`trg_descontar_inventario`, ver riesgos), CHECK de rangos y cantidades, columna generada de subtotal. **El backend debe convivir con ella, no duplicarla ni contradecirla.**

## 2. Estados y transiciones

Los valores de los enums están en el DDL; las **transiciones** no están en el documento. Las siguientes son una **(propuesta)** a validar:

**Reserva** (`estado_reserva`): `pendiente → confirmada → en_atencion → atendida`; `pendiente|confirmada → cancelada` (por el cliente); `pendiente|confirmada → vencida` (pasada `fecha_hora_atencion` sin atención). `atendida`, `cancelada` y `vencida` son finales.

**Venta** (`estado_venta`): `pendiente → pagada`; `pendiente → anulada`; `pagada → devuelta`. Solo las `pagada` cuentan en `vw_ventas_por_sucursal`.

**Pago** (`estado_pago`): `pendiente → autorizado → confirmado`; `pendiente|autorizado → rechazado`; `confirmado → reembolsado`. La venta pasa a `pagada` cuando el pago queda `confirmado`.

**Stock** (`estado_prenda_stock`): lo calcula el trigger a partir de las cantidades; no lo escribas a mano. El trigger solo produce `disponible`, `reservada` y `agotada`.

Cada transición se implementa en un service con una comprobación explícita del estado de origen; una transición inválida lanza una excepción de dominio (→ 409).

## 3. Invariantes que el backend debe garantizar

- `cantidad_disponible` y `cantidad_reservada` nunca son negativas; comprueba antes de escribir y confía en el CHECK como última defensa, no como validación de negocio.
- Toda variación de stock genera un `movimientos_inventario` (tipo, cantidad con signo, `referencia_documento` tipo `VENTA-<id>` o `RESERVA-<id>`, `id_usuario_responsable` cuando lo hay) en la misma transacción.
- Reservar mueve unidades de disponible a reservada; cancelar o vencer las devuelve (`liberacion_reserva`); atender y vender las consume.
- Una venta congela `precio_unitario = precio_base + precio_extra` y el descuento vigente en el momento del checkout; cambios posteriores de catálogo no la alteran.
- Los descuentos salen de promociones **activas y vigentes** (`activa` y fecha actual entre inicio y fin) asociadas al producto. Regla de acumulación de varias promociones sobre un mismo producto: **no definida** → Ask First.
- `numero_comprobante` es único y se genera en servidor (formato de ejemplo del documento: `WEB-2026-09001`; prefijo por canal **(propuesta)**).
- Un cliente tiene un solo carrito activo (`UNIQUE(id_cliente)`).
- Un encargado o cajero solo opera sobre su sucursal.
- El vestidor exige `productos.modelo_ar_url` configurado; si no, error de dominio → 422 o 409 según se defina.

## 4. Contratos de API ya definidos (sección 2.5 del documento)

Respétalos: el frontend y los tests del proyecto ya dependen de ellos. Códigos y campos son los del documento.

| CU | Método y ruta | Entrada (resumen) | Salida (resumen) | Código |
|---|---|---|---|---|
| CU06 | `POST /api/v1/catalogo/buscar` | `termino_busqueda`, `filtros{id_categoria,id_talla,id_color,precio_min,precio_max}` | `total_resultados`, `productos[]` con `variantes_coincidentes[]` (búsqueda difusa `pg_trgm`) | 200 |
| CU11 | `POST /api/v1/carrito/items` | `id_variante`, `id_sucursal`, `cantidad` | `id_carrito`, `items[]`, `resumen{subtotal,descuentos_aplicados,total_estimado}`; valida `cantidad_disponible ≥ cantidad` | 200 |
| CU10 | `POST /api/v1/vestidor/sesion` | `id_producto`, `dispositivo`, `resultado_url`, `genero_interes` | `id_sesion_ar`, `id_cliente`, … ; exige `modelo_ar_url` | 201 |
| CU22 | `POST /api/v1/admin/productos` | producto + `variantes[]` (talla, color, sku, precio_extra) | `id_producto`, `variantes_registradas[]`; SKU único; alta en cascada | 201 |
| CU15 | `POST /api/v1/ventas/checkout` | `id_carrito`, `tipo_venta` (`digital_web`\|`digital_movil`) | `id_venta`, `numero_comprobante`, `estado: pendiente`, `subtotal`, `descuento`, `total` | 201 |

Errores: el documento no fija un formato de error. Propuesta base: `{"detail": "<mensaje>", "code": "<CODIGO_DOMINIO>"}` con el código HTTP de la constitución; confírmalo en la primera spec que lo necesite.

## 5. Riesgos y huecos conocidos del diseño

Detectados al cruzar el DDL con los flujos del documento. **No los "corrijas" en silencio**: son decisiones de diseño (Ask First) y deben resolverse en la fase 2 del CU afectado.

1. **Descuento de stock antes del pago.** `trg_descontar_inventario` se dispara `AFTER INSERT` en `venta_detalle`, sin mirar el estado de la venta. En el checkout digital (CU15) la venta nace `pendiente`, así que el stock se descuenta *antes* de que exista pago. Si el pago se rechaza o expira, hoy no hay compensación definida. Opciones a decidir: (a) mantener el trigger y compensar con un movimiento de `devolucion` al rechazar/anular/expirar; (b) retirar el trigger y descontar al confirmar el pago, usando `cantidad_reservada` como retención durante `pendiente`. Con (b) el comportamiento de POS (CU31/32) también debe revisarse.
2. **Carrito multi-sucursal vs venta de una sola sucursal.** `carrito_detalle` guarda `id_sucursal` por línea, pero `ventas.id_sucursal` es único y el trigger descuenta del inventario de *esa* sucursal. Un carrito con líneas de varias sucursales produce un descuento incorrecto o un error. Decidir: restringir el carrito a una sucursal, o dividir el checkout en una venta por sucursal.
3. **Trigger con `LIMIT 1` sin temporada.** `inventario_sucursal` es único por (variante, sucursal, **temporada**), pero el trigger busca solo por variante y sucursal: si hay dos temporadas, elige una fila arbitraria.
4. **Cierre de sesión sin almacén de tokens.** El diseño (CU03) prevé `ServicioRevocarToken` y un modelo `TokenSesion`, pero el DDL no define esa tabla. Hay que decidir el mecanismo (tabla de tokens revocados, lista de denegación con expiración, o tokens de vida corta sin revocación) antes de implementar CU03.
5. **Bitácora limitada.** CU30/CU33 se implementa sobre `movimientos_inventario`, que solo cubre inventario. Inicio de sesión, cambios de roles o de precios no quedan registrados; si el requisito es auditoría general, falta una tabla.
6. **Numeración ambigua.** La bitácora aparece como CU30 (lista y priorización) y como CU33 (detalle y diagramas), y CU33 también es "Recuperar acceso de cuenta". Fija el ID en cada spec para no confundirlos.
7. **Reservas sin CU detallado** y sin definición de qué ocurre con el stock al vencer (job programado o comprobación perezosa): definir antes de implementar.
8. **Webhook de Stripe** no aparece en el diseño. El estado del pago debe confirmarlo el webhook (firma e idempotencia); añádelo como endpoint en el diseño del CU16.

## 6. Estado de especificación por CU

| Situación | CU | Consecuencia |
|---|---|---|
| Detallados en el documento (ciclo 1) | 01, 02, 03, 04, 20–26, 30/33 | Se puede empezar por la fase 2 (Diseño), citando el CU |
| Detallados en el documento (ciclo 2) | 05–11, 15, 27, 31, 32 | Ídem |
| **Sin flujo detallado** | 12, 13, 14, 16, 17, 18, 19, 28, 29, 34, 35, 33 (recuperar acceso) | Fase 1 obligatoria; implementación = Ask First |

"Detallado" significa que hay propósito, precondiciones, flujo principal, postcondiciones y excepciones; aun así, las reglas de los riesgos anteriores siguen abiertas.
