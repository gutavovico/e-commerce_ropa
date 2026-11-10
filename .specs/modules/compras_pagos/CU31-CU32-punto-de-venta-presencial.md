# Especificación Técnica Permanente: CU31 + CU32 — Punto de Venta Presencial

**Código:** CU31 (Registrar venta presencial) · CU32 (Procesar venta presencial y emitir comprobante) de `SI2-Parcial1.md`
**Paquete de Dominio:** `compras_pagos` (las reservas se operan por el servicio del paquete `reservas`)
**Backend:** `app/modules/compras_pagos/cu31_cu32_punto_venta/` · `app/modules/reservas/atencion_caja.py`
**Frontend:** `src/app/modules/compras_pagos/cu31_cu32_punto_venta/` (ruta `/admin/pos`)
**Mobile:** desde el 2026-11-10, caja móvil con el mismo contrato: `P2-CU16-CU17-caja-movil.md`
**Actores:** cajero · encargado de sucursal · administrador
**Estado:** Aprobado y promovido a permanente (2026-11-08)
**Historial del cambio:** `.specs/finalized/CU31-CU32-punto-de-venta-presencial/` · `CHANGELOG.md` defectos 49 y 50

> **Colisión de numeración:** `cu31_reportes_voz` (paquete `comercial`) es otro módulo: cubre CU34 + CU35.

---

## 1. Alcance y roles

| Rol | Boutique | Acceso |
| :--- | :--- | :--- |
| `cajero` | La suya (`usuarios.id_sucursal`), fija | Solo `/admin/pos`: entra directo tras el login; `cajeroACajaGuard` lo devuelve allí desde el panel. Muestra su nombre y «Cerrar sesión». |
| `encargado_sucursal` | La suya, fija | Tarjeta «Punto de venta» en `/admin` junto a sus módulos. |
| `administrador` | La que elija (`id_sucursal` en query/cuerpo; sin ella `422 SUCURSAL_REQUERIDA`) | Igual que el encargado. |

Toda venta exige ficha en `empleados` del usuario que cobra (`409 EMPLEADO_NO_REGISTRADO`); CU20 la crea al dar de alta o cambiar a un rol de personal.

## 2. Modelo de stock (mismo patrón que CU15/CU16)

- **Registrar** (venta `pendiente`, `tipo_venta = presencial`, `tipo_entrega = recogida_boutique`): las líneas añadidas en caja pasan de `disponible` a `reservada` con un movimiento `reserva`, `referencia_documento = VENTA-{id}`.
- Las líneas de una **reserva** no se retienen otra vez (ya están en `reservada` desde CU12). La reserva pasa a `en_atencion` mientras está en la orden de caja, para que el vencimiento perezoso de CU13 no la libere.
- **Cobrar**: `venta_confirmada` sobre la fila exacta de cada retención (localizada por su movimiento, nunca recalculando la temporada); lo que el cliente deja de la reserva vuelve a `disponible` (`liberacion_reserva`); la reserva pasa a `atendida`; el cupón consume su uso aquí, no al registrar.
- **Anular** (con motivo, o por vencimiento perezoso a las **2 h**): libera solo lo retenido por la caja (`cancelacion_pedido`); la reserva vuelve a `confirmada` con su stock apartado.
- Todo importe lo calcula el servidor (`Decimal`); el cuerpo de la venta solo lleva variantes y cantidades.

## 3. Contratos (`/api/v1/pos`, JWT de un rol de caja)

| Método y ruta | Uso |
| :--- | :--- |
| `GET /variantes?q=` | Prendas por nombre, categoría o SKU (mín. 2 caracteres, máx. 60 resultados): cada talla/color con `categoria_nombre`, precio vigente y `disponible_en_sucursal`, agotadas incluidas |
| `GET /variantes/{sku}` | Variante por SKU exacto (`404 SKU_NO_ENCONTRADO`) |
| `GET /clientes?q=` | Clientes registrados por nombre, apellidos o correo (máx. 20). Sin coincidencia, la venta es presencial sin cuenta |
| `GET /clientes/{id}/reservas` | Reservas del cliente cargables en esta caja: `pendiente`/`confirmada`, de la boutique y no vencibles. Solo lectura |
| `GET /reservas/{referencia}` | Carga una reserva por id o `RES-AAAA-NNNN` (`403 SUCURSAL_AJENA`, `409 RESERVA_NO_ATENDIBLE`) |
| `GET /cupones?q=` | Cupones vigentes con usos; sin `q`, todos; con `q`, por código o nombre |
| `POST /ventas/previsualizar` | Totales sin persistir ni consumir el cupón |
| `POST /ventas` → 201 | CU31: registra la orden `pendiente` y retiene stock (`409 STOCK_INSUFICIENTE`, `422 VENTA_VACIA`, `409 VARIANTE_YA_EN_RESERVA`, `409 LINEA_RESERVA_DESCONOCIDA`) |
| `GET /ventas?estado=&solo_hoy=` · `GET /ventas/{id}` | Listado de la boutique y detalle |
| `POST /ventas/{id}/cobrar` | CU32: `{metodo_pago, monto_recibido, referencia, aprobado}`. Efectivo exige monto (`MONTO_REQUERIDO`/`MONTO_INSUFICIENTE`) y el cambio lo devuelve el servidor; tarjeta, QR y transferencia exigen referencia (`REFERENCIA_REQUERIDA`); `aprobado: false` registra el rechazo del datáfono y la venta sigue pendiente |
| `POST /ventas/{id}/anular` | `{motivo}` (3–250) |
| `GET /ventas/{id}/comprobante.pdf` | PDF de 80 mm; `409 COMPROBANTE_NO_DISPONIBLE` si la venta sigue pendiente |
| `GET /pedidos-web-efectivo` | Pedidos web con pago en efectivo por cobrar en la boutique; se confirman o cancelan con los endpoints de CU16 (`/admin/pagos/{id}/confirmar-efectivo` · `cancelar-efectivo`) |

Métodos de cobro: `efectivo`, `tarjeta_debito`, `tarjeta_credito`, `qr`, `transferencia`. Bitácora: `POS_REGISTRAR_VENTA`, `POS_COBRAR_VENTA`, `POS_COBRO_RECHAZADO`, `POS_ANULAR_VENTA`.

## 4. Interfaz web (`/admin/pos`)

- **Nueva venta:** buscador incremental de prendas (300 ms, todas las coincidencias); cliente por nombre o correo, o «Venta presencial sin cuenta»; al elegir cliente, sus reservas activas con «Cargar» (y carga por código como alternativa), con casillas para excluir lo que no se lleva; cupón que lista todos los vigentes con el campo vacío y filtra al escribir. Totales siempre desde `previsualizar`.
- **Cobro** en panel lateral; **ticket** imprimible de 80 mm (`@media print`) y «Descargar PDF» (`Blob`).
- **Pendientes y del día:** cobrar, anular con motivo, reimprimir o descargar el PDF.
- **Pedidos web por cobrar** (CU16).

## 5. Fuera de alcance

Apertura, arqueo y cierre de caja (fondo inicial, cuadre por método de pago, sobrantes y faltantes): pendiente de especificar en un ciclo futuro.
