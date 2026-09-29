# Especificacion Tecnica Permanente: CU17 - Registrar cobro en caja

**Codigo:** CU17  
**Nombre Oficial:** Registrar cobro en caja  
**Paquete de Dominio:** `comercial` / `caja_pos`  
**Directorio Funcional Backend:** `app/modules/comercial/cu17_cobro_caja`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/caja/paginas/cobro-caja`  
**Directorio Funcional Mobile:** Excluido formalmente (las operaciones de caja fisica y mostrador POS operan exclusivamente en terminales de escritorio)  
**Actores Primarios:**  
- Cajero (Operacion directa de mostrador en boutique asignada)  
- Encargado de Sucursal (Operacion y supervision en boutique asignada)  
- Administrador (Acceso y control global o por sucursal)  
**Actores Bloqueados:**  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Proveedor (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.9.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU17 centraliza la gestion del punto de venta fisico (POS) en caja de mostrador para las boutiques de FashionStore. Permite buscar ordenes pendientes de cobro originadas de manera presencial o mediante conversion de reservas, registrar pagos en efectivo con calculo reactivo de cambio a devolver, registrar transacciones con tarjeta POS o QR estatico, actualizar el estado de la venta a pagada, rebajar existencias del inventario fisico en el Kardex y asentar el comprobante en la bitacora inmutable.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), construida con Flutter 3.x, esta orientada exclusivamente a la experiencia de compra B2C del cliente final (catalogo, vestidor virtual en Realidad Aumentada, bolsa y pago digital).  
Las operaciones de terminal de caja, recaudacion fisica de efectivo, integracion con datafonos POS fisicos y liquidacion de tickets en mostrador se ejecutan unicamente desde estaciones de trabajo de boutique con el frontend web (`Ec-frontend`). Se ratifica documentalmente cero cambios e intervencion nula en `Ec-mobile`.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Segregacion Territorial (RBAC):**
   - Endpoints custodiados bajo `/api/v1/caja/...` requieren token Bearer JWT con roles `cajero`, `encargado_sucursal`, `administrador` o `admin`.
   - Si el rol es `cajero` o `encargado_sucursal`, las consultas y cobros se restringen estrictamente a `usuario.id_sucursal`. Todo intento de interactuar con ventas de otra sucursal resulta en HTTP 403 Forbidden (`SUCURSAL_NO_AUTORIZADA`).

2. **RB-2: Integridad y Bloqueo Concurrente con FOR UPDATE:**
   - La orden de venta se recupera con bloqueo pesimista en base de datos (`SELECT ... FOR UPDATE`) para impedir doble cobro o condiciones de carrera sobre el mismo comprobante.

3. **RB-3: Validacion de Montos y Calculo de Cambio:**
   - Para pagos en efectivo: `monto_recibido >= total_orden`.
   - `cambio_devuelto = monto_recibido - total_orden`.
   - Si `monto_recibido < total_orden`, se rechaza con HTTP 422 Unprocessable Content (`MONTO_INSUFICIENTE`).
   - Para tarjeta POS y QR: `monto_recibido` se ajusta automaticamente al total exacto y el cambio devuelto es 0.00 BOB.

4. **RB-4: Transicion de Estado y Registro en Pagos:**
   - La venta pasa de estado `pendiente` a `pagada`.
   - Se crea un registro en `fashionstore.pagos` con estado `confirmado`, metodo de pago normalizado (`efectivo`, `tarjeta_pos`, `qr_estatico`), referencia de operacion y operador autenticado.

5. **RB-5: Afectacion Inmediata de Kardex e Inventario:**
   - Por cada detalle de prenda vendido, se descuenta la cantidad correspondiente en `fashionstore.inventario_sucursal` y se asienta un movimiento de tipo `venta_mostrador` en `fashionstore.movimientos_inventario`.

6. **RB-6: Trazabilidad en Bitacora Inmutable:**
   - Emision de auditoria no bloqueante con accion `COBRO_CAJA` en `fashionstore.bitacora`, registrando numero de comprobante, monto cobrado, metodo, operador y direccion IP.

---

## 2. Arquitectura Backend (`Ec-backend`)

### 2.1 Endpoints REST
- `GET /api/v1/caja/ordenes-pendientes`: Listado paginado y filtrable de ordenes pendientes con prendas asociadas.
- `POST /api/v1/caja/cobrar`: Procesamiento transaccional de cobro de una orden.

### 2.2 Modelos y Esquemas
- `CobroCajaIn`: `id_venta`, `metodo_pago`, `monto_recibido`, `referencia_operacion`, `notas`.
- `CobroCajaOut`: `id_venta`, `numero_comprobante`, `total`, `monto_recibido`, `cambio_devuelto`, `metodo_pago`, `estado`, `fecha_cobro`, `cajero_id`.
- `OrdenPendienteOut`: Detalle completo de orden y lista de prendas (`DetallePrendaCajaOut`).

---

## 3. Arquitectura Frontend Web (`Ec-frontend`)

### 3.1 Vista Standalone y Rutas
- Ruta: `/caja/cobro` (custodiada por `[authGuard, roleGuard(['cajero', 'encargado_sucursal', 'administrador', 'admin'])]`).
- Componente: `CobroCajaComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals.
- Calculadora de cambio reactiva con bloqueo instantaneo del boton `#btn-confirmar-cobro-caja` si el monto es insuficiente.
- Modal de comprobante tras emision exitosa del cobro.

### 3.2 Regla Anti-Botones Estaticos
- Implementacion estricta de directiva dual `routerLink` y `(click)="navegar(..., $event)"` (con `event.preventDefault()`).
- Verificacion en pruebas unitarias mediante despacho directo de eventos `MouseEvent` sobre el DOM.

---

## 4. Matriz de Pruebas y Cobertura

- **Backend (Pytest):** `test_cu17_cobro_caja.py` (13 pruebas unitarias e integracion cubriendo autenticacion, RBAC, segregacion territorial, validacion de montos y Kardex).
- **Frontend (Vitest):** `cobro-caja.component.spec.ts` (5 pruebas), `caja.service.spec.ts` (9 pruebas), `main-layout.component.spec.ts` (10 pruebas), `login.component.spec.ts` (6 pruebas).
