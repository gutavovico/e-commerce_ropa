# Plan de Tareas: [CU28] Consultar ventas y reservas

**Codigo del Caso de Uso:** CU28  
**Denominacion Oficial:** Consultar ventas y reservas  
**Modulo:** Gestion Comercial / Auditoria y Ventas (`gestion_comercial` / `comercial`)  
**Metodologia:** Spec-Driven Development (SDD) & Ejecucion por Oleadas  
**Entorno:** 100% Local (Prohibido git push)  
**Exclusion Formal:** `Ec-mobile` (Flutter 3.x) 100% excluida  

---

## Resumen de Oleadas y Dependencias

```
+--------------------------------------------------------------------------------+
| OLEADA 1: Backend (Ec-backend - FastAPI + PostgreSQL Neon)                     |
| [x] Tarea 1.1: Modelos ORM y Registro de Entidades Relacionales                |
| [x] Tarea 1.2: Esquemas Pydantic v2 y Jerarquia de Errores Semanticos          |
| [x] Tarea 1.3: Servicio de Consulta Analitica con Gobernanza RBAC              |
| [x] Tarea 1.4: Router REST FastAPI y Registro en API v1                        |
| [x] Tarea 1.5: Suite de Pruebas Automatizadas Pytest                           |
+---------------------------------------+----------------------------------------+
                                        | (Requiere aprobacion previa)
                                        v
+---------------------------------------+----------------------------------------+
| OLEADA 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)                  |
| [x] Tarea 2.1: Modelos de Datos y DTOs TypeScript                              |
| [x] Tarea 2.2: Servicio HTTP Reactivo con Angular Signals                      |
| [x] Tarea 2.3: Tarjeta en AdminDashboardComponent con Directiva Dual y Clic   |
| [x] Tarea 2.4: Vista Principal /admin/ventas-reservas (KPIs, Filtros y Tabla)  |
| [x] Tarea 2.5: Modal de Detalle Transaccional y Luxury Banners                 |
| [x] Tarea 2.6: Suite de Pruebas Unitarias Vitest                               |
+---------------------------------------+----------------------------------------+
                                        | (Requiere aprobacion previa)
                                        v
+---------------------------------------+----------------------------------------+
| OLEADA 3: Cierre, Verificacion Cruzada Integral y DoD                          |
| [x] Tarea 3.1: Verificacion Cruzada Integral de Suites Locales                |
| [x] Tarea 3.2: Consolidacion y Promocion Documental a .specs/finalized/CU28/   |
| [x] Tarea 3.3: Actualizacion de Bitacoras CHANGELOG.md y Cierre de Ciclo       |
+--------------------------------------------------------------------------------+
```

---

## OLEADA 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

### [x] Tarea 1.1: Modelos ORM y Registro de Entidades Relacionales
- **Archivo destino:** `app/modules/comercial/cu28_ventas_reservas/modelos.py`
- **Descripcion:** Implementar las entidades declarativas de SQLAlchemy 2.0 bajo el esquema `fashionstore`:
  * `VentaORM`: Mapeo de `fashionstore.ventas` con claves foraneas a `clientes`, `sucursales`, `empleados` (cajero), `reservas` y relaciones con `detalles` y `pagos`.
  * `VentaDetalleORM`: Mapeo de `fashionstore.venta_detalle` relacionado con `variantes_producto`.
  * `PagoORM`: Mapeo de `fashionstore.pagos`.
  * `ReservaORM`: Mapeo de `fashionstore.reservas` con claves foraneas a `clientes`, `sucursales`, `empleados` y relacion con `detalles`.
  * `ReservaDetalleORM`: Mapeo de `fashionstore.reserva_detalle`.
- **Verificacion:** Compilacion limpia en Python sin colisiones de nombres relacionales.

### [x] Tarea 1.2: Esquemas Pydantic v2 y Jerarquia de Errores Semanticos
- **Archivos destino:**
  * `app/modules/comercial/cu28_ventas_reservas/esquemas.py`
  * `app/modules/comercial/cu28_ventas_reservas/errores.py`
- **Descripcion:**
  * En `esquemas.py`: Definir `TransaccionFiltrosIn` (con `ordenar_por: Literal['creado_en_desc', 'creado_en_asc', 'total_desc', 'total_asc', 'fecha_desc'] = 'creado_en_desc'`), validador cronologico de rango `fecha_desde <= fecha_hasta`, `TransaccionResumenItemOut`, `MetricasTransaccionalesOut`, `RespuestaPaginadaTransaccionesOut`, `VentaDetalleCompletoOut`, `ReservaDetalleCompletoOut`, `LineaDetalleOut` y `PagoItemOut`.
  * En `errores.py`: Definir excepciones semanticas `VentasReservasError`, `VentaNoEncontradaError` (404), `ReservaNoEncontradaError` (404), `SucursalNoAutorizadaError` (403), `RangoFechasInvalidoError` (422).
- **Verificacion:** Pruebas unitarias de esquemas y validacion de tipos Pydantic.

### [x] Tarea 1.3: Servicio de Consulta Analitica con Gobernanza RBAC
- **Archivo destino:** `app/modules/comercial/cu28_ventas_reservas/servicio.py`
- **Descripcion:** Implementar la clase `ServicioConsultarVentasReservas`:
  * Segregacion de sucursal obligatoria segun rol del usuario (`administrador` vs `encargado_sucursal`).
  * Metodo `listar_transacciones`: Consulta combinada paginada determinista con filtros multicriterio (`q`, `tipo_operacion`, `estado`, `id_sucursal`, `fecha_desde`, `fecha_hasta`, `metodo_pago`, `canal_origen`, `ordenar_por`).
  * Metodo `obtener_metricas`: Calculo consolidado cuantitativo de `monto_total_facturado`, `total_ventas_concluidas`, `reservas_activas` y `ticket_promedio`.
  * Metodos `obtener_detalle_venta` y `obtener_detalle_reserva` con validacion de autorizacion por sucursal.
- **Verificacion:** Invocacion aislada de metodos de servicio con base de datos en sesion mock o transaccional.

### [x] Tarea 1.4: Router REST FastAPI y Registro en API v1
- **Archivos destino:**
  * `app/modules/comercial/cu28_ventas_reservas/router.py`
  * `app/main.py`
- **Descripcion:**
  * En `router.py`: Endpoints `GET /admin/ventas-reservas`, `GET /admin/ventas-reservas/ventas/{id_venta}`, `GET /admin/ventas-reservas/reservas/{id_reserva}` protegidos por `require_roles(["administrador", "encargado_sucursal"])`.
  * En `main.py`: Incluir el router bajo el prefijo `/api/v1` con etiqueta comercial.
- **Verificacion:** Verificacion de montaje de rutas en FastAPI y documentacion Swagger `/docs`.

### [x] Tarea 1.5: Suite de Pruebas Automatizadas Pytest
- **Archivo destino:** `tests/modules/comercial/test_cu28_ventas_reservas.py`
- **Descripcion:** Suite exhaustiva cubriendo:
  * Autenticacion obligatoria (HTTP 401).
  * Control de acceso RBAC por rol (HTTP 403 para cajero y cliente).
  * Segregacion por sucursal para encargado de sucursal.
  * Listado paginado con filtros multicriterio y calculo de metricas.
  * Validacion de rango cronologico invertido (HTTP 422).
  * Detalle de venta y reserva (HTTP 200 y HTTP 404).
- **Verificacion:** `pytest tests/modules/comercial/test_cu28_ventas_reservas.py` ejecutado al 100% en verde.

---

## OLEADA 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### [x] Tarea 2.1: Modelos de Datos y DTOs TypeScript
- **Archivo destino:** `src/app/modules/comercial/cu28_ventas_reservas/modelos/ventas-reservas.dto.ts`
- **Descripcion:** Definir interfaces TypeScript estrictas: `TransaccionFiltros`, `TransaccionResumenItem`, `MetricasTransaccionales`, `RespuestaPaginadaTransacciones`, `VentaDetalleCompleto`, `ReservaDetalleCompleto`, `LineaDetalle`, `PagoItem`.
- **Verificacion:** Compilacion TypeScript sin errores de tipos (`tsc --noEmit`).

### [x] Tarea 2.2: Servicio HTTP Reactivo con Angular Signals
- **Archivo destino:** `src/app/modules/comercial/cu28_ventas_reservas/servicios/ventas-reservas-admin.service.ts`
- **Descripcion:** Implementar `VentasReservasAdminService`:
  * Signals reactivos: `transacciones`, `metricas`, `totalTransacciones`, `totalPaginas`, `cargando`, `error`.
  * Metodos HTTP: `listarTransacciones`, `obtenerDetalleVenta`, `obtenerDetalleReserva`, `cargarSucursalesAuxiliares`.
- **Verificacion:** Pruebas unitarias aisladas del servicio con `HttpClientTestingModule`.

### [x] Tarea 2.3: Tarjeta en AdminDashboardComponent con Directiva Dual y Clic
- **Archivos destino:**
  * `src/app/modules/admin/dashboard/admin-dashboard.component.html`
  * `src/app/modules/admin/dashboard/admin-dashboard.component.ts`
  * `src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  * `src/app/app.routes.ts`
- **Descripcion:**
  * En `admin-dashboard.component.html`: Agregar la tarjeta comercial con boton `#btn-consultar-ventas-reservas`, `routerLink="/admin/ventas-reservas"` y `(click)="navegar('/admin/ventas-reservas', $event)"`.
  * En `app.routes.ts`: Registrar la ruta `/admin/ventas-reservas` con guards y carga perezosa (`loadComponent`).
  * En `admin-dashboard.component.spec.ts`: Incorporar prueba obligatoria de despacho de evento click sobre `#btn-consultar-ventas-reservas` y llamada a `navegar`.
- **Verificacion:** Prueba unitaria en verde verificando la presencia, directiva dual y navegacion del boton.

### [x] Tarea 2.4: Vista Principal /admin/ventas-reservas (KPIs, Filtros y Tabla)
- **Archivos destino:**
  * `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.ts`
  * `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.html`
  * `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.scss`
- **Descripcion:**
  * Layout editorial boutique con encabezado H1 "Consultar ventas y reservas", breadcrumbs y boton "<- Volver al Panel Principal".
  * Grid superior de 4 tarjetas KPIs reactivas alimentadas por Signals.
  * Barra reactiva de filtros multicriterio con debounce de 300 ms.
  * Tabla maestra consolidada de transacciones con badges semanticos y botones de accion unitaria.
- **Verificacion:** Renderizado responsivo limpio y pruebas de interaccion de filtrado.

### [x] Tarea 2.5: Modal de Detalle Transaccional y Luxury Banners
- **Archivos destino:**
  * `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.html`
  * `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.ts`
- **Descripcion:**
  * Modal accesible (`role="dialog"`) para consulta expandida de comprobante de venta o detalle de reserva.
  * Desglose de lineas de prenda, descuentos, metodos de pago y estado de entrega.
  * Luxury Banners contextuales para retroalimentacion amigable y no destructiva ante contingencias.
- **Verificacion:** Apertura y cierre de modal accesible mediante teclado (Escape) y click en overlay.

### [x] Tarea 2.6: Suite de Pruebas Unitarias Vitest
- **Archivo destino:** `src/app/modules/comercial/cu28_ventas_reservas/paginas/ventas-reservas-admin.component.spec.ts`
- **Descripcion:** Suite completa validando renderizado de KPIs, filtros con debounce, tabla, modal de detalle y navegacion.
- **Verificacion:** `npx ng test --watch=false` al 100% en verde.

---

## OLEADA 3: Cierre, Verificacion Cruzada Integral y DoD

### [x] Tarea 3.1: Verificacion Cruzada Integral de Suites Locales
- **Descripcion:** Revalidacion de las suites completas en ambos proyectos:
  * Backend: `pytest tests/` (100% en verde).
  * Frontend: `npx ng test --watch=false` y `npm run build` (100% en verde, 0 errores).
  * Auditoria de emojis: 0 emojis detectados en todo el codigo fuente y pruebas.
- **Verificacion:** Registro cuantitativo de ejecucion limpia sin errores de compilacion ni regresiones.

### [x] Tarea 3.2: Consolidacion y Promocion Documental a .specs/finalized/CU28/
- **Archivos destino:**
  * `.specs/finalized/CU28/spec.md`
  * `.specs/finalized/CU28/design.md`
  * `.specs/finalized/CU28/tasks.md`
  * `.specs/modules/comercial/CU28-consultar-ventas-reservas.md`
- **Descripcion:** Copiar y consolidar las especificaciones aprobadas en el historico oficial de finalizados y en el catalogo modular.
- **Verificacion:** Integridad de referencias cruzadas y existencia de los archivos consolidados.

### [x] Tarea 3.3: Actualizacion de Bitacoras CHANGELOG.md y Cierre de Ciclo
- **Archivos destino:**
  * `CHANGELOG.md` (raiz)
  * `.specs/CHANGELOG.md`
- **Descripcion:** Registrar la version `v2.5.0` con la incorporacion de [CU28] Consultar ventas y reservas, dejando constancia documental de la exclusion formal de Ec-mobile y borrado de la carpeta temporal `.specs/changes/CU28/`.
- **Verificacion:** Historial sincronizado y espacio de trabajo 100% limpio.
