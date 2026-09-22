# Especificacion Tecnica Permanente: CU28 - Consultar ventas y reservas

**Codigo:** CU28  
**Nombre:** Consultar ventas y reservas  
**Paquete de Dominio:** `comercial` / `auditoria_ventas`  
**Directorio Funcional Backend:** `app/modules/comercial/cu28_ventas_reservas`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/cu28_ventas_reservas`  
**Directorio Funcional Mobile:** Excluido formalmente (gestion analitica y auditoria transaccional reservada exclusivamente al back-office web corporativo)  
**Actores Primarios:**  
- Administrador (Acceso global analitico a todas las transacciones de la cadena y sucursales)  
- Encargado de Sucursal (Acceso analitico segregado estrictamente a su sucursal asignada)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.5.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Ventas y Reservas).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU28 centraliza la consulta consolidada, el monitoreo analitico y la auditoria transaccional de todas las operaciones comerciales (ventas directas facturadas y reservas de prendas en tienda fisica o canal digital) en la red de FashionStore. Proporciona una vision unificada y en tiempo real del flujo de ingresos, ticket promedio y estado operativo, garantizando la gobernanza de datos mediante control de acceso basado en roles (RBAC).

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada sobre Flutter 3.x, tiene como proposito exclusivo la experiencia de compra B2C orientada al consumidor final (exploracion de catalogo, vestidor virtual en Realidad Aumentada, bolsa de compras y checkout digital).  
La auditoria de ventas corporativas, la consolidacion de reservas inter-tiendas, el analisis de recaudacion multi-canal y la supervision del desempeno comercial corresponden exclusivamente a la direccion comercial y back-office corporativo (`Ec-frontend`).  
Por tanto, se ratifica formalmente la exclusion total de `Ec-mobile`: cero modelos, pantallas o servicios en Flutter para este caso de uso.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Las rutas base `/api/v1/admin/ventas-reservas` exigen JWT valido (HTTP 401 si ausente). Roles `cajero` o `cliente` son rechazados con HTTP 403 Forbidden. `administrador` tiene visibilidad global o filtrable por sede, mientras que `encargado_sucursal` esta estrictamente confinado a las transacciones de su sucursal asignada.

2. **RB-2: Segregacion Territorial de Transacciones:**
   - Si el usuario autenticado tiene el rol `encargado_sucursal`, el backend ignora cualquier parametro `id_sucursal` externo y fuerza obligatoriamente el filtro hacia su propia sucursal. Los intentos de acceder a detalles de ventas o reservas de otras sucursales son rechazados con HTTP 403 Forbidden.

3. **RB-3: Consistencia Cronologica de Rango de Fechas:**
   - En el filtrado temporal, la `fecha_hasta` debe ser mayor o igual a `fecha_desde` (`fecha_desde <= fecha_hasta`). En caso contrario, se rechaza la solicitud con HTTP 422 Unprocessable Entity en backend y se previene en frontend.

4. **RB-4: Metricas Cuantitativas en Tiempo Real:**
   - Cada consulta paginada retorna un bloque consolidado de metricas cuantitativas calculadas en tiempo real para el universo filtrado:
     * `monto_total_facturado`: Sumatoria de ventas completadas en el periodo.
     * `total_ventas_concluidas`: Conteo de transacciones de venta completadas.
     * `reservas_activas`: Conteo de reservas con estado `pendiente` o `confirmada`.
     * `ticket_promedio`: Cociente entre monto facturado y ventas concluidas (0 si no hay ventas).

5. **RB-5: Integridad y Trazabilidad de Lineas y Pagos:**
   - El detalle de venta expone las lineas de producto (variante, SKU, talla, color, precio unitario y subtotal) y la traza de pagos realizados (metodo de pago, monto y referencia de pasarela). El detalle de reserva desglosa las prendas reservadas, senas de adelanto y fecha limite de atencion.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/comercial/cu28_ventas_reservas`
- **Servicio:** `ServicioConsultarVentasReservas`:
  * `listar_transacciones`: Unificacion determinista de `ventas` y `reservas` con paginacion, ordenamiento y filtros multicriterio (`q`, `tipo_operacion`, `estado`, `id_sucursal`, `fecha_desde`, `fecha_hasta`, `metodo_pago`, `canal_origen`, `ordenar_por`).
  * `obtener_metricas`: Calculo analitico de KPIs cuantitativos sobre el conjunto filtrado.
  * `obtener_detalle_venta`: Consulta completa de comprobante de venta, desglose de prendas y medios de pago con validacion de autorizacion por sucursal.
  * `obtener_detalle_reserva`: Consulta completa de comprobante de reserva, desglose de prendas y fecha de caducidad con validacion de autorizacion por sucursal.
- **Excepciones Semanticas:** `VentasReservasError`, `VentaNoEncontradaError` (404), `ReservaNoEncontradaError` (404), `SucursalNoAutorizadaError` (403), `RangoFechasInvalidoError` (422).

### 2.2 Modelos Persistentes ORM
- Mapeo declarativo SQLAlchemy 2.0 bajo el esquema `fashionstore`:
  * `VentaORM` (`fashionstore.ventas`)
  * `VentaDetalleORM` (`fashionstore.venta_detalle`)
  * `PagoORM` (`fashionstore.pagos`)
  * `ReservaORM` (`fashionstore.reservas`)
  * `ReservaDetalleORM` (`fashionstore.reserva_detalle`)

### 2.3 Endpoints REST Expuestos
- `GET /api/v1/admin/ventas-reservas`: Listado paginado unificado con metricas consolidadas y filtros multicriterio.
- `GET /api/v1/admin/ventas-reservas/ventas/{id_venta}`: Detalle transaccional expandido de comprobante de venta.
- `GET /api/v1/admin/ventas-reservas/reservas/{id_reserva}`: Detalle transaccional expandido de reserva de prendas.

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Componentes y Rutas
- **Ruta:** `/admin/ventas-reservas` custodiada por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
- **Componente Principal:** `VentasReservasAdminComponent` (Standalone, `ChangeDetectionStrategy.OnPush`, Angular Signals).
- **Servicio:** `VentasReservasAdminService` (estado reactivo centralizado con Signals y cliente HTTP fuertemente tipado).

### 3.2 Interfaz de Usuario y Diseno Editorial
- Layout editorial `max-w-[1440px] px-6 py-8 mx-auto`, fondo Slate 50, tipografia Outfit, acentos Camel (`#AD8C63`) y Obsidian (`#0F172A`).
- Decima tarjeta corporativa en `AdminDashboardComponent` bajo la categoria "Gestion Comercial" con badge "Auditoria y Ventas", boton `#btn-consultar-ventas-reservas` y directiva dual de navegacion (`routerLink` y `(click)`).
- Rejilla superior de 4 tarjetas KPIs reactivas:
  * Facturacion Total
  * Ventas Concluidas
  * Reservas Activas
  * Ticket Promedio
- Barra reactiva de filtros multicriterio con debounce de 300 ms en busqueda textual, selectores de tipo de operacion, estado, sucursal, canal de origen, metodo de pago y ordenamiento.
- Tabla maestra unificada con badges semanticos cromaticos por tipo y estado (`completada`, `pendiente`, `cancelada`, `confirmada`).
- Modal accesible de detalle transaccional (`role="dialog"`) con soporte de navegacion por teclado (Escape), cierre por backdrop y desglose completo de prendas y pagos.
- Luxury Banners contextuales para retroalimentacion amigable ante contingencias y errores de comunicacion.
