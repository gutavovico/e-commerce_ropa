# Especificacion Tecnica Permanente: CU18 - Atender entrega de reserva en boutique

**Codigo:** CU18  
**Nombre Oficial:** Atender entrega de reserva en boutique  
**Paquete de Dominio:** `reservas` / `fitting_room`  
**Directorio Funcional Backend:** `app/modules/reservas/cu18_entrega_reserva`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/caja/paginas/entrega-reservas`  
**Directorio Funcional Mobile:** Excluido formalmente (la recepcion de citas en boutique y gestion de stock apartado en mostrador se opera exclusivamente desde estaciones de trabajo de escritorio)  
**Actores Primarios:**  
- Cajero (Atencion en mostrador, despacho de prendas, registro de no asistencia y conversion a venta presencial)  
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
El caso de uso CU18 gestiona la recepcion y atencion presencial de clientes con citas de reserva o fitting room en las boutiques de FashionStore. Permite consultar las citas agendadas por codigo `RES-` o cliente, confirmar la entrega fisica de las prendas apartadas, registrar la inasistencia del cliente restituyendo de inmediato las existencias al inventario disponible, o convertir la cita en una orden de venta presencial para cobro directo en caja.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil (`Ec-mobile`), desarrollada en Flutter 3.x, permite al cliente final agendar su reserva y seleccionar prendas.  
La atencion de mostrador, el despacho fisico en probador, la liberacion de stock por inasistencia y la liquidacion de prendas corresponden exclusivamente al personal de tienda en la aplicacion web corporativa (`Ec-frontend`). Se ratifica documentalmente cero cambios e intervencion nula en `Ec-mobile`.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Segregacion Territorial (RBAC):**
   - Endpoints custodiados bajo `/api/v1/caja/reservas/...` exigen token Bearer JWT con roles `cajero`, `encargado_sucursal`, `administrador` o `admin`.
   - Para `cajero` y `encargado_sucursal`, la atencion se confina a `usuario.id_sucursal`. Todo intento sobre reservas de otra boutique responde HTTP 403 Forbidden (`SUCURSAL_NO_AUTORIZADA`).

2. **RB-2: Confirmacion de Entrega y Cierre de Cita:**
   - La reserva pasa de estado `confirmada`, `pendiente` o `en_atencion` a estado `atendida`.
   - Se reduce el stock apartado (`cantidad_reservada`) en `fashionstore.inventario_sucursal`.
   - Se asienta la fecha de atencion y el operador responsable.

3. **RB-3: Inasistencia y Restitucion Inmediata de Stock:**
   - Si el cliente no acude a su cita, el cajero marca no asistencia (`POST /api/v1/caja/reservas/{id}/no-asistio`).
   - La reserva pasa a estado `cancelada` con motivo `no_asistio`.
   - El stock apartado vuelve inmediatamente a disponible: `cantidad_reservada -= cant`, `cantidad_disponible += cant`.
   - Se emite un movimiento de tipo `liberacion_reserva` en `fashionstore.movimientos_inventario` (Kardex).

4. **RB-4: Conversion Atomica a Venta Presencial:**
   - Si el cliente decide adquirir las prendas probadas en tienda (`POST /api/v1/caja/reservas/{id}/convertir-venta`), se crea una nueva orden en `fashionstore.ventas` con `tipo_venta = 'presencial'`, `estado = 'pendiente'`, vinculando `id_reserva`.
   - Se copian las lineas de reserva a `fashionstore.venta_detalle`.
   - La reserva transiciona a `atendida`.
   - La orden generada se devuelve para su cobro inmediato en `/caja/cobro` (CU17).

5. **RB-5: Trazabilidad en Bitacora Inmutable:**
   - Toda alteracion emite un evento no bloqueante con accion `ENTREGA_RESERVA` en `fashionstore.bitacora`.

---

## 2. Arquitectura Backend (`Ec-backend`)

### 2.1 Endpoints REST
- `GET /api/v1/caja/reservas-pendientes`: Consulta de citas activas por boutique y termino de busqueda.
- `POST /api/v1/caja/reservas/{id_reserva}/entregar`: Confirmacion de entrega y cierre.
- `POST /api/v1/caja/reservas/{id_reserva}/no-asistio`: Cancelacion por inasistencia y retorno de stock al inventario general.
- `POST /api/v1/caja/reservas/{id_reserva}/convertir-venta`: Generacion atomica de orden presencial para cobro de mostrador.

### 2.2 Modelos y Esquemas
- `ConfirmarEntregaIn`: `notas`.
- `EntregaReservaOut`: Datos de reserva atendida y prendas entregadas.
- `NoAsistioReservaOut`: Confirmacion de cancelacion, prendas devueltas y stock restituido.
- `ConvertirVentaOut`: Orden de venta generada con `id_venta`, `numero_comprobante`, `total` y prendas.

---

## 3. Arquitectura Frontend Web (`Ec-frontend`)

### 3.1 Vista Standalone y Rutas
- Ruta: `/caja/reservas` (custodiada por `[authGuard, roleGuard(['cajero', 'encargado_sucursal', 'administrador', 'admin'])]`).
- Componente: `EntregaReservasComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals.
- Ficha de Fitting Room interactiva con detalle de prendas apartadas, fecha limite y clienta.
- Botones de accion rapida:
  * `#btn-confirmar-entrega-reserva`: Cierre de cita.
  * `#btn-convertir-venta-reserva`: Conversion fluida y navegacion automatica a Cobro de Caja.
  * `#btn-marcar-no-asistio-reserva`: Liberacion de inventario.

### 3.2 Regla Anti-Botones Estaticos
- Implementacion estricta de directiva dual `routerLink` y `(click)="navegar(..., $event)"` (con `event.preventDefault()`).
- Verificacion unitaria con despacho de clics en el DOM.

---

## 4. Matriz de Pruebas y Cobertura

- **Backend (Pytest):** `test_cu18_entrega_reserva.py` (11 pruebas unitarias e integracion cubriendo autenticacion, RBAC, segregacion territorial, entrega, inasistencia con Kardex y conversion a venta).
- **Frontend (Vitest):** `entrega-reservas.component.spec.ts` (7 pruebas), `caja.service.spec.ts` (9 pruebas), `main-layout.component.spec.ts` (10 pruebas).
