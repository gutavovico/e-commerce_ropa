# Plan de Tareas: Modulo de Caja (CU17 y CU18)

**ID del Cambio:** `CU17-CU18-caja`
**Nivel SDD:** Nivel 3 (Alto riesgo)
**Politica de Emojis:** Cero Emojis en todo el archivo y en la ejecucion.

---

## Oleada 1: Backend (Ec-backend) [Completada y Aprobada]

- [x] **T-BE-01: Esquemas y Errores de Dominio para CU17 (Cobro en Caja)**
  - Archivos:
    * `app/modules/comercial/cu17_cobro_caja/errores.py`
    * `app/modules/comercial/cu17_cobro_caja/esquemas.py`
  - Validaciones: `monto_recibido >= total`, metodos de pago ('efectivo', 'tarjeta_pos', 'qr_estatico').
  - Verificacion: Compilacion e importacion limpia en Python.

- [x] **T-BE-02: Servicio Transaccional de Cobro en Caja (CU17)**
  - Archivo: `app/modules/comercial/cu17_cobro_caja/servicio.py`
  - Logica:
    * Busqueda de ordenes pendientes filtradas por `id_sucursal` del cajero.
    * Bloqueo defensivo con `FOR UPDATE`.
    * Validacion de monto, calculo de vuelto.
    * Transicion de venta a `pagada`, creacion de registro en `fashionstore.pagos`.
    * Movimiento de inventario Kardex y auditoria no bloqueante (`COBRO_CAJA`).

- [x] **T-BE-03: Router REST de Cobro en Caja (CU17)**
  - Archivo: `app/modules/comercial/cu17_cobro_caja/router.py`
  - Endpoints:
    * `GET /api/v1/caja/ordenes-pendientes`
    * `POST /api/v1/caja/cobrar`
  - Seguridad: `require_roles(["cajero", "encargado_sucursal", "administrador", "admin"])`.
  - Integracion: Montar en `app/modules/comercial/router.py`.

- [x] **T-BE-04: Esquemas y Errores de Dominio para CU18 (Entrega de Reserva)**
  - Archivos:
    * `app/modules/reservas/cu18_entrega_reserva/errores.py`
    * `app/modules/reservas/cu18_entrega_reserva/esquemas.py`

- [x] **T-BE-05: Servicio Transaccional de Entrega y Gestion de Reservas (CU18)**
  - Archivo: `app/modules/reservas/cu18_entrega_reserva/servicio.py`
  - Logica:
    * Busqueda de reservas pendientes por sucursal del cajero.
    * Confirmacion de entrega (`atendida`).
    * Inasistencia (`cancelada`) con devolucion de stock apartado a disponible y Kardex (`liberacion_reserva`).
    * Conversion fluida a venta presencial para cobro inmediato en caja.
    * Auditoria no bloqueante (`ENTREGA_RESERVA`).

- [x] **T-BE-06: Router REST de Entrega de Reserva (CU18)**
  - Archivo: `app/modules/reservas/cu18_entrega_reserva/router.py`
  - Endpoints:
    * `GET /api/v1/caja/reservas-pendientes`
    * `POST /api/v1/caja/reservas/{id_reserva}/entregar`
    * `POST /api/v1/caja/reservas/{id_reserva}/no-asistio`
    * `POST /api/v1/caja/reservas/{id_reserva}/convertir-venta`
  - Seguridad: `require_roles(["cajero", "encargado_sucursal", "administrador", "admin"])`.
  - Integracion: Montar en `app/modules/reservas/router.py`.

- [x] **T-BE-07: Pruebas Unitarias e Integracion Backend (Pytest)**
  - Archivos:
    * `tests/modules/comercial/test_cu17_cobro_caja.py`
    * `tests/modules/reservas/test_cu18_entrega_reserva.py`
  - Cobertura:
    * Autenticacion 401 y autorizacion RBAC 403 (rechazo a cliente).
    * Segregacion territorial por sucursal.
    * Calculo de cambio y monto insuficiente.
    * Flujo completo de cobro y registro en pagos / inventario.
    * Entrega de reserva, inasistencia con liberacion de stock y conversion a venta.
  - Verificacion: 24/24 pruebas pasadas (486/486 en suite completa).

---

## Punto de Detencion
Al completar la Oleada 1 (Backend) y validar que todas las pruebas pasen al 100%, detenerse y presentar el informe de avance al usuario antes de proceder a la Oleada 2 (Frontend). [Aprobado]

---

## Oleada 2: Frontend Web (Ec-frontend) [Completada y Verificada]

- [x] **T-FE-01: Modelos y Servicio HTTP de Caja con Signals**
  - Implementar DTOs y `CajaService` reactivo para cobro y reservas (`caja.dto.ts`, `caja.service.ts`, `caja.service.spec.ts`).
- [x] **T-FE-02: Vista Standalone `/caja/cobro` (CU17)**
  - Buscador reactivo, ficha de orden, calculadora de cambio y selector de metodo (`cobro-caja.component.ts`, `.html`, `.scss`, `.spec.ts`).
- [x] **T-FE-03: Vista Standalone `/caja/reservas` (CU18)**
  - Buscador de citas, listado de prendas y botones de accion Entregar, No Asistio, Convertir a Venta (`entrega-reservas.component.ts`, `.html`, `.scss`, `.spec.ts`).
- [x] **T-FE-04: Rutas y Acceso en Navbar / Layout / Login**
  - Enrutamiento protegido `caja/cobro` y `caja/reservas` en `app.routes.ts`.
  - Redireccion directa para rol `cajero` en `login.component.ts`.
  - Toolbar corporativa de mostrador y enlaces con directiva dual (`routerLink` + `(click)`) en `main-layout.component.ts`.
- [x] **T-FE-05: Pruebas Unitarias en Vitest**
  - Verificacion con 100% de exito (532/532 pruebas pasando en frontend).

---

## Oleada 3: Cierre y Verificacion Integral [Completada y Verificada]

- [x] **T-INT-01: Verificacion Integral Backend y Frontend**
  - Backend: 486/486 pruebas pasadas en pytest (`pytest tests/`).
  - Frontend: 532/532 pruebas pasadas en vitest (`npm test -- --watch=false`).
  - Compilacion de produccion limpia con `npm run build` (codigo de salida 0).
- [x] **T-INT-02: Auditoria de Cero Emojis**
  - Verificacion estricta de 0 emojis en todo el codigo fuente, plantillas, estilos y documentacion.
