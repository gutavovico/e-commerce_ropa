# Especificacion de Requisitos: [CU28] Consultar ventas y reservas

**Codigo del Caso de Uso:** CU28  
**Denominacion Oficial:** Consultar ventas y reservas  
**Modulo Funcional:** Gestion Comercial / Auditoria y Ventas (`gestion_comercial` / `comercial`)  
**Actores Primarios:**  
- Administrador Corporativo (Acceso irrestricto de consulta, agregacion analitica y auditoria multi-sucursal sobre toda la red empresarial)  
- Encargado de Sucursal (Consulta analitica acotada estrictamente a las transacciones de venta y reservas originadas o asignadas a su sede operativa)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica de segregacion funcional y seguridad RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Entorno de Implementacion:** Web corporativa exclusiva (`Ec-backend` FastAPI y `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal de Plataforma:** `Ec-mobile` (Flutter) 100% excluida  

---

## 1. Vision General del Caso de Uso

### 1.1 Proposito y Justificacion de Negocio
El caso de uso "Consultar ventas y reservas" constituye el centro de monitoreo comercial, auditoria transaccional y conciliacion operativa de la cadena FashionStore.  
En una operacion omnicanal de retail de moda, la direccion corporativa y las jefaturas de sede necesitan supervisar de manera unificada tanto el flujo de transacciones monetarias concluidas (ventas fisicas y digitales) como los compromisos de apartado de stock vigentes (reservas de probador o mostrador).

Este modulo centralizado permite:
1. Analizar el rendimiento comercial consolidado mediante indicadores clave (Total Facturado, Ventas Concluidas, Reservas Activas y Ticket Promedio).
2. Trazar el ciclo de vida de cada operacion transaccional desde su origen (venta digital web, venta digital movil, venta presencial en boutique) hasta su perfeccionamiento, pago y entrega.
3. Monitorear las reservas de prendas en tiempo real para evitar retenciones indebidas de stock y garantizar la disponibilidad de inventario para atencion inmediata.
4. Auditar comprobantes, metodos de pago aplicados (efectivo, tarjetas, transferencias, pasarelas digitales) y desglose de lineas de prenda por talla, color y descuento comercial.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Arquitectonica y de Negocio
La aplicacion movil de FashionStore (`Ec-mobile`), implementada en Flutter 3.x, tiene como mision exclusiva brindar la experiencia de compra B2C interactiva para el cliente final (navegacion del catalogo de moda, probador virtual inmersivo mediante Realidad Aumentada, configuracion de bolsa de compras y checkout digital con pasarela de pago).

La consulta analitica consolidada de facturacion, la auditoria fiscal multi-sucursal, la conciliacion financiera y el control de transacciones globales son facultades exclusivas de la administracion corporativa y de las jefaturas de tienda. Estas actividades se llevan a cabo de manera confidencial en estaciones de trabajo de escritorio mediante el portal web de gestion `Ec-frontend`.

### 2.2 Ratificacion de Alcance Tecnico
1. Cero pantallas en `Ec-mobile`: No se construira ninguna vista, widget, grafico ni reporte de administracion de ventas y reservas en Flutter.
2. Cero servicios analiticos en Flutter: No se definira ninguna peticion hacia `/api/v1/admin/ventas-reservas` en la aplicacion movil.
3. Generacion pasiva de datos: La aplicacion movil unicamente actua como canal de origen de pedidos y reservas (`canal_origen = 'movil'`), los cuales son consultados y auditados de forma exclusiva desde el frontend web corporativo.

---

## 3. Especificacion de Requisitos Funcionales bajo Sintaxis EARS

### Bloque A: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

#### Seguridad, Autenticacion y Control de Acceso RBAC
- **# AC-1 (Ubicuo - Autenticacion Obligatoria):**  
  El sistema debera requerir un token JWT valido en la cabecera `Authorization: Bearer <token>` para todas las peticiones dirigidas a `/api/v1/admin/ventas-reservas`. Ante una solicitud no autenticada, con token vencido o malformado, el sistema debera rechazar la operacion de forma determinista con HTTP 401 Unauthorized.

- **# AC-2 (Condicional - Control de Acceso RBAC por Rol):**  
  Si un usuario autenticado con rol `cajero` o `cliente` intenta acceder a cualquier endpoint de consulta bajo `/api/v1/admin/ventas-reservas`, el sistema debera denegar el acceso respondiendo con HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

- **# AC-3 (Ubicuo - Segregacion Funcional de Operacion por Rol y Sede):**  
  El sistema debera filtrar las transacciones segun el rol del usuario autenticado:
  * Rol `administrador`: Acceso irrestricto y transversal a todas las transacciones de venta y reserva de toda la red empresarial multi-sucursal.
  * Rol `encargado_sucursal`: Acceso acotado obligatoriamente a las transacciones correspondientes a su sucursal de asignacion (`usuarios.id_sucursal`), ignorando cualquier parametro de sede foraneo enviado en la peticion.

#### Consulta Consolidada, Filtros Multicriterio y Metricas
- **# AC-4 (Ubicuo - Mapeo y Persistencia de Entidades Transaccionales):**  
  El sistema debera soportar la consulta analitica sobre el modelo relacional persistido en PostgreSQL Neon compuesto por:
  * `fashionstore.ventas`: Identificador `id_venta`, `numero_comprobante`, `id_cliente`, `id_sucursal`, `id_cajero`, `id_reserva`, `tipo_venta` (`presencial`, `digital_web`, `digital_movil`), `estado` (`pendiente`, `pagada`, `anulada`, `devuelta`), `subtotal`, `descuento`, `total`, `fecha_venta`.
  * `fashionstore.venta_detalle`: Lineas de transaccion con `id_variante`, `cantidad`, `precio_unitario` y `subtotal_linea`.
  * `fashionstore.pagos`: Desglose de liquidacion monetaria con `metodo_pago` (`efectivo`, `tarjeta_debito`, `tarjeta_credito`, `pasarela_digital`, `qr`, `transferencia`), `monto`, `estado` (`pendiente`, `autorizado`, `confirmado`, `rechazado`, `reembolsado`) y `referencia_pasarela`.
  * `fashionstore.reservas`: Identificador `id_reserva`, `id_cliente`, `id_sucursal`, `fecha_hora_atencion`, `estado` (`pendiente`, `confirmada`, `en_atencion`, `atendida`, `cancelada`, `vencida`), `canal_origen` (`web`, `movil`, `sucursal`), `creado_en`, `atendido_por`, `observacion`.
  * `fashionstore.reserva_detalle`: Desglose de prendas apartadas por `id_variante` y `cantidad`.

- **# AC-5 (Por Evento - Listado Unificado Paginado con Filtros Multicriterio):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/ventas-reservas`, el sistema debera retornar un listado paginado unificado de transacciones aplicando los siguientes criterios opcionales de filtrado:
  * `q`: Busqueda textual insensible a mayusculas/minusculas sobre numero de comprobante/reserva, nombre o email del cliente, y SKU de variante.
  * `tipo_operacion`: Filtrado por `'venta'`, `'reserva'` o `'todas'` (por defecto `'todas'`).
  * `estado`: Filtrado por estado especifico de transaccion (`'pendiente'`, `'confirmada'`, `'pagada'`, `'completada'`, `'anulada'`, `'devuelta'`, `'cancelada'`, `'vencida'` o `'todos'`).
  * `id_sucursal`: Filtrado por sucursal especifica (para administradores; ignorado y forzado a la sucursal del usuario para encargados).
  * `fecha_desde` y `fecha_hasta`: Rango temporal sobre la fecha de registro (`fecha_venta` o `creado_en`).
  * `metodo_pago`: Filtrado por modalidad de pago en operaciones de venta.
  * `canal_origen`: Filtrado por canal de origen (`'web'`, `'movil'`, `'sucursal'`, `'todos'`).
  * `ordenar_por`: Criterio de ordenacion admitiendo `'creado_en_desc'` (por defecto), `'creado_en_asc'`, `'total_desc'`, `'total_asc'`, `'fecha_desc'`.
  * `pagina`: Entero mayor o igual a 1 (por defecto 1).
  * `limite`: Entero entre 1 y 100 (por defecto 10).

- **# AC-6 (Ubicuo - Calculo de Metricas Cuantitativas de Red):**  
  El sistema debera incluir en la respuesta del listado un objeto consolidado de metricas de red computado dentro del alcance del rol (global para administrador, por sucursal para encargado):
  * `monto_total_facturado`: Sumatoria monetaria de ventas en estado `'pagada'`.
  * `total_ventas_concluidas`: Conteo de transacciones de venta concluidas exitosamente.
  * `reservas_activas`: Conteo de reservas en estado operativo vigente (`'pendiente'`, `'confirmada'`, `'en_atencion'`).
  * `ticket_promedio`: Cociente entre el monto total facturado y el total de ventas concluidas (0.00 si no existen ventas).

- **# AC-7 (Por Evento - Detalle Transaccional Completo de Venta):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/ventas-reservas/ventas/{id_venta}`, el sistema debera retornar el desglose integral de la venta conteniendo: metadatos de cabecera, comprobante, cliente (nombre, email, telefono), sucursal, cajero responsable, lineas de detalle de prendas (modelo, SKU, talla, color, precio unitario, cantidad, subtotal de linea) y pagos registrados con su estado y referencia. Si el id no existe, retornara HTTP 404 Not Found (`VENTA_NO_ENCONTRADA`). Si un encargado intenta consultar una venta de otra sucursal, retornara HTTP 403 Forbidden (`SUCURSAL_NO_AUTORIZADA`).

- **# AC-8 (Por Evento - Detalle Transaccional Completo de Reserva):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/ventas-reservas/reservas/{id_reserva}`, el sistema debera retornar el desglose exhaustivo de la reserva: codigo identificador, cliente, sucursal de atencion, fecha y hora programada, estado de atencion, canal de origen, prendas reservadas (con SKU, modelo, talla y color) y observaciones. Si la reserva no existe, retornara HTTP 404 Not Found (`RESERVA_NO_ENCONTRADA`). Si un encargado intenta consultar una reserva de otra sucursal, retornara HTTP 403 Forbidden (`SUCURSAL_NO_AUTORIZADA`).

- **# AC-9 (Condicional - Validacion de Consistencia Cronologica de Rango):**  
  Si en una consulta se proporciona `fecha_desde` y `fecha_hasta`, y `fecha_desde > fecha_hasta`, el sistema debera rechazar la peticion respondiendo con HTTP 422 Unprocessable Entity (`RANGO_FECHAS_INVALIDO`).

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en el Panel Principal (AdminDashboardComponent)
- **# AC-10 (Ubicuo - Tarjeta Comercial y Regla Anti-Botones Estaticos):**  
  El componente `AdminDashboardComponent` debera exhibir una tarjeta boutique con:
  * Categoria: "Gestion Comercial"
  * Titulo oficial: "Consultar ventas y reservas"
  * Subtitulo descriptivo: "Monitoreo consolidado de facturacion, pedidos omnicanal, reservas de prendas y conciliacion."
  * Puntos clave: "Facturacion omnicanal y desglose de pagos", "Control de reservas activas y atencion en tienda".
  * Badge de estado: "Auditoria Transaccional"
  * Boton de accion con directiva dual obligatoria:
    ```html
    <a
      id="btn-consultar-ventas-reservas"
      routerLink="/admin/ventas-reservas"
      (click)="navegar('/admin/ventas-reservas', $event)"
      class="w-full inline-flex items-center justify-center gap-2 bg-[#0F172A] hover:bg-black text-white text-xs font-bold uppercase tracking-wider py-3 px-4 rounded-xl shadow-xs transition-all cursor-pointer"
    >
      <span>Consultar ventas y reservas</span>
      <svg class="w-3.5 h-3.5 text-[#AD8C63] group-hover:translate-x-1 transition-transform" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </a>
    ```
  * Visibilidad RBAC: Visible para roles `administrador` y `encargado_sucursal`.

#### Vista Administrativa Principal (`VentasReservasAdminComponent`)
- **# AC-11 (Ubicuo - Encabezado Editorial y Navegacion Superior):**  
  La vista ubicada en `/admin/ventas-reservas` debera respetar los lineamientos de diseno boutique de FashionStore:
  * Encabezado con titulo H1 formal "Consultar ventas y reservas".
  * Miga de pan interactiva: `Inicio > Panel Administrativo > Ventas y Reservas`.
  * Boton de retorno superior: "<- Volver al Panel Principal" enlazado a `/admin`.
  * Indicador de sesion y rol activo con chip institucional Camel/Slate.

- **# AC-12 (Ubicuo - Grid Superior de Tarjetas KPIs de Rendimiento):**  
  La interfaz debera desplegar en la parte superior un grid responsivo de 4 tarjetas de metricas cuantitativas alimentadas reactivamente por Angular Signals:
  1. "Monto Total Facturado": Monto acumulado en formato monetario institucional (`$X.XX` o `Bs. X.XX`), con acento Camel y badge de crecimiento.
  2. "Ventas Concluidas": Total numerico de ventas pagadas y despachadas, con icono de bolsa de compras.
  3. "Reservas Activas": Conteo de reservas pendientes o en atencion, con indicador de alerta suave.
  4. "Ticket Promedio": Promedio monetario por venta, reflejando el valor comercial de la red.

- **# AC-13 (Por Evento - Barra Reactiva de Filtros con Debounce):**  
  La vista debera incorporar controles reactivos de filtrado sincronizados con el estado de Angular Signals:
  * Campo de busqueda por texto libre con debounce de 300 milisegundos (`#input-busqueda-transacciones`).
  * Selector de tipo de operacion (`#select-tipo-operacion`): "Todas las operaciones", "Solo Ventas", "Solo Reservas".
  * Selector de estado (`#select-estado-transaccion`): "Todos los estados", "Pagadas / Concluidas", "Pendientes", "Canceladas / Anuladas".
  * Selector de sucursal (`#select-sucursal`): Visible y habilitado para Administrador; preseleccionado y bloqueado para Encargado de Sucursal.
  * Selector de rango de fechas (Fecha Desde, Fecha Hasta).
  * Boton de restablecimiento de filtros (`#btn-limpiar-filtros`).

- **# AC-14 (Ubicuo - Tabla Maestra Consolidada de Transacciones):**  
  La vista debera presentar una tabla editorial estructurada con las siguientes columnas:
  * Comprobante / Codigo: Codigo alfanumerico distintivo (ej. `VEN-2026-0001` o `RES-00042`).
  * Tipo: Chip visual diferenciado (Venta: Slate/Camel; Reserva: Indigo/Slate).
  * Cliente: Nombre completo y correo electronico.
  * Sucursal: Denominacion de la sede fisica o canal digital.
  * Fecha y Hora: Marca temporal formateada de forma legible.
  * Monto Total: Importe monetario formateado (o `N/A - Sin Costo Inicial` para reservas de prueba).
  * Estado: Badge semantico de estado (`Pagada` en verde/esmeralda, `Pendiente` en ambar, `Anulada` o `Cancelada` en carmesi).
  * Acciones: Boton de accion unitaria "Ver Comprobante" / "Ver Detalle" (`#btn-ver-detalle-{id}`).

- **# AC-15 (Por Evento - Modal Accesible de Detalle Transaccional):**  
  Al pulsar el boton "Ver Detalle" de una transaccion, el sistema debera desplegar un modal accesible (`role="dialog"`, `aria-modal="true"`) con:
  * Resumen de cabecera con identificador unico y estado general.
  * Datos del cliente y canal de origen.
  * Tabla de desglose de lineas de prenda: miniatura/modelo, descripcion, talla, color, precio unitario, cantidad y subtotal.
  * Bloque de liquidacion financiera: subtotal, descuentos de campana aplicados y total neto.
  * Informacion de cobro: metodo de pago, referencia de pasarela y estado de confirmacion.
  * Boton de cierre de modal con tecla Escape o clic fuera del contenedor.

- **# AC-16 (Ubicuo - Luxury Banners y Manejo de Errores):**  
  Ante cualquier contingencia de red o rechazo de autorizacion, la aplicacion debera desplegar un Luxury Banner no intrusivo con tipografia Outfit/Inter y acentos institucionales, sin recurrir a alertas intrusivas del navegador (`alert()`).

---

## 4. Matriz de Trazabilidad de Requisitos

| Requisito | Descripcion Resumida | Capa Backend | Capa Frontend |
|---|---|---|---|
| # AC-1 | Autenticacion obligatoria JWT | `deps.py`, `router.py` | `auth.guard.ts` |
| # AC-2 | Control RBAC (bloqueo cajero y cliente) | `deps.py`, `router.py` | `role.guard.ts` |
| # AC-3 | Segregacion funcional por rol y sucursal | `servicio.py` | `ventas-reservas-admin.component.ts` |
| # AC-4 | Mapeo relacional de ventas y reservas | `modelos.py` | `ventas-reservas.dto.ts` |
| # AC-5 | Listado paginado y filtros multicriterio | `router.py`, `servicio.py` | `ventas-reservas-admin.service.ts` |
| # AC-6 | Calculo cuantitativo de metricas de red | `servicio.py` | `ventas-reservas-admin.component.ts` (KPIs) |
| # AC-7 | Detalle completo de venta | `router.py`, `servicio.py` | `modal-detalle.component.ts` |
| # AC-8 | Detalle completo de reserva | `router.py`, `servicio.py` | `modal-detalle.component.ts` |
| # AC-9 | Validacion de rango de fechas cronologico | `esquemas.py`, `servicio.py` | `ventas-reservas-admin.component.ts` |
| # AC-10 | Tarjeta dashboard y regla anti-botones estaticos | N/A | `admin-dashboard.component.html` |
| # AC-11 | Layout editorial y navegacion de retorno | N/A | `ventas-reservas-admin.component.html` |
| # AC-12 | Grid de 4 tarjetas KPIs reactivas | N/A | `ventas-reservas-admin.component.html` |
| # AC-13 | Filtros reactivos con debounce | N/A | `ventas-reservas-admin.component.ts` |
| # AC-14 | Tabla maestra de transacciones | N/A | `ventas-reservas-admin.component.html` |
| # AC-15 | Modal accesible de detalle de transaccion | N/A | `ventas-reservas-admin.component.html` |
| # AC-16 | Luxury Banners contextuales | N/A | `ventas-reservas-admin.component.html` |
