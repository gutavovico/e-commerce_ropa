# Plan de Tareas y Oleadas de Implementacion: CU26 - Consultar inventario global

**ID del Caso de Uso:** CU26  
**Nombre:** Consultar inventario global  
**Paquete Arquitectonico:** `gestion_operativa` / `inventario`  
**Modulo Backend:** `app/modules/gestion_operativa/cu26_inventario_global`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu26_inventario_global`  
**Referencias:** `.specs/changes/CU26/spec.md` y `.specs/changes/CU26/design.md`  
**Estado:** Planificado (Fase 3 - Plan de Tareas)  

---

## 1. Estrategia General de Implementacion

El caso de uso **CU26 - Consultar inventario global** implementa la capacidad analitica y operativa centralizada para supervisar en tiempo real las existencias fisicas de todas las prendas y variantes comerciales (SKUs) en la red de sucursales de **FashionStore**.

Permite a los roles autorizados (`administrador` y `encargado_sucursal`) disponer de una vision panoramica transversal de stock disponible y reservado, consultar desgloses inmediatos por cada boutique activa con informacion de contacto logistico para derivacion inter-tiendas, y anticipar quiebres de inventario mediante indicadores cuantitativos consolidados.

### 1.1 Exclusion Formal Ratificada de la Aplicacion Movil (Ec-mobile)
Se ratifica de manera estricta e irrevocable la total exclusion de desarrollo e implementacion en `Ec-mobile`. La aplicacion movil en Flutter 3.x esta destinada exclusivamente al consumidor final (B2C) y la experiencia de vestidor con Realidad Aumentada (AR). La consulta analitica consolidada, el balance global de red y la auditoria de existencias multi-sede corresponden al panel corporativo de escritorio (`Ec-frontend`). Por consiguiente, se asignan cero (0) tareas a Flutter o la aplicacion movil en este plan.

### 1.2 Secuenciacion de Oleadas
El plan de tareas se estructura en tres (3) oleadas de ejecucion estrictamente secuenciales:
1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon):**
   DTOs Pydantic v2 con validadores defensivos, jerarquia de excepciones semanticas de dominio, servicio analitico `ServicioInventarioGlobal` con consultas SQL agregadas de alto rendimiento (`SUM`, `COALESCE`, discriminacion de sedes inactivas), router REST protegido por RBAC (`/api/v1/admin/inventario/global`) e integracion en el agregador de gestion operativa, respaldado por una suite Pytest exhaustiva de 10 pruebas al 100% en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Contratos TypeScript fuertemente tipados, servicio reactivo `InventarioGlobalAdminService` con Angular Signals, integracion de tarjeta boutique en `AdminDashboardComponent` bajo "Gestion Operativa", pagina `InventarioGlobalAdminComponent` con estetica editorial Atelier, tarjetas de KPIs de red, barra de filtros reactiva con debounce de 300 ms, tabla maestra consolidada con chips de stock por boutique, modal logistico con datos de contacto directo, Luxury Banners y suite unitaria Vitest al 100% en verde.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD):**
   Revalidacion cruzada de ambas suites automatizadas (`pytest`, `ng test`, `ng build`, `audit_emojis.py`), promocion formal de artefactos a `.specs/finalized/CU26/` y `.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md`, registro formal del incremento funcional en `CHANGELOG.md` y `.specs/CHANGELOG.md` (version 2.2.0) y limpieza del directorio temporal.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- [x] **Tarea 1.1: Esquemas Pydantic v2 en `app/modules/gestion_operativa/cu26_inventario_global/esquemas.py`**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu26_inventario_global/esquemas.py`
  - **Descripcion:**
    * Crear el directorio `app/modules/gestion_operativa/cu26_inventario_global/` con su archivo `__init__.py`.
    * Implementar los esquemas DTO de salida y entrada con `ConfigDict(from_attributes=True)`:
      - `ExistenciaSucursalItemOut`: `id_sucursal` (int), `nombre_sucursal` (str), `ciudad` (str), `direccion` (str), `telefono` (Optional[str]), `cantidad_disponible` (int, default 0), `cantidad_reservada` (int, default 0).
      - `InventarioGlobalItemOut`: `id_variante` (int), `id_producto` (int), `nombre_producto` (str), `sku` (str), `categoria` (str), `talla` (str), `color` (str), `swatches_hex` (Optional[str]), `total_disponible` (int), `total_reservado` (int), `total_fisico` (int), `estado_stock` (`Literal["optimo", "alerta_baja", "agotado"]`), `desglose_sucursales` (List[ExistenciaSucursalItemOut]).
      - `MetricasInventarioGlobalOut`: `total_unidades_red` (int), `variantes_monitoreadas` (int), `alertas_stock_bajo` (int), `sedes_activas` (int).
      - `InventarioGlobalFiltrosIn`: `q` (Optional[str]), `id_categoria` (Optional[int]), `id_sucursal` (Optional[int]), `estado_stock` (Optional[Literal["optimo", "alerta_baja", "agotado", "todos"]]), `ordenar_por` (Optional[Literal["stock_asc", "stock_desc", "nombre_asc", "nombre_desc", "sku_asc"]]), `pagina` (int, ge=1), `limite` (int, ge=1, le=100).
      - `RespuestaInventarioGlobalOut`: `items` (List[InventarioGlobalItemOut]), `metricas` (MetricasInventarioGlobalOut), `total` (int), `pagina` (int), `limite` (int), `total_paginas` (int).
  - **Criterios Mapeados:** `# AC-3`, `# AC-4`, `# AC-5`, `# AC-6`.
  - **Verificacion:** Pruebas de serializacion/deserializacion y validacion de tipos Pydantic v2.

- [x] **Tarea 1.2: Excepciones semanticas en `app/modules/gestion_operativa/cu26_inventario_global/errores.py`**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu26_inventario_global/errores.py`
  - **Descripcion:**
    * Implementar la jerarquia de excepciones de dominio conectadas a `core.errors`:
      - `InventarioGlobalError`: Excepcion base heredando de `DomainError` (HTTP 400).
      - `SucursalInvalidaConsultaError`: Hereda de `NotFoundError` (HTTP 404), lanzada cuando el `id_sucursal` provisto no existe o esta inactivo.
      - `CategoriaInvalidaConsultaError`: Hereda de `NotFoundError` (HTTP 404), lanzada cuando el `id_categoria` provisto no existe.
      - `ParametroConsultaInvalidoError`: Hereda de `UnprocessableEntityError` (HTTP 422), lanzada ante valores incongruentes o no conformes.
  - **Criterios Mapeados:** `# AC-6`.
  - **Verificacion:** Pruebas unitarias de instanciacion verificando codigos de estado HTTP y codigos de error asignados.

- [x] **Tarea 1.3: Servicio analitico de agregacion `ServicioInventarioGlobal` en `app/modules/gestion_operativa/cu26_inventario_global/servicio.py`**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu26_inventario_global/servicio.py`
  - **Descripcion:**
    * Implementar `ServicioInventarioGlobal.consultar_inventario_global(db: Session, filtros: InventarioGlobalFiltrosIn) -> RespuestaInventarioGlobalOut`:
      - Validar previamente la existencia activa de `id_sucursal` e `id_categoria` si vienen especificados en los filtros.
      - Cargar el directorio de todas las sucursales activas con sus datos de contacto y ciudad (`SucursalORM.activa.is_(True)`).
      - Formular la consulta analitica uniendo `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `TallaORM`, `ColorORM`, con `LEFT OUTER JOIN` hacia `InventarioSucursalORM` y `SucursalORM` (filtrando sedes activas).
      - Computar `total_disponible` y `total_reservado` mediante `func.sum` y `func.coalesce`, agrupando por identificadores de variante.
      - Aplicar filtros `q` (`ILIKE` sobre prenda y SKU), `id_categoria`, `id_sucursal`, `estado_stock` (en clausula `HAVING`) y ordenamiento dinamico.
      - Ejecutar conteo total con subconsulta para calcular `total_paginas` y paginar de forma determinista con `offset` y `limit`.
      - Ingerir en memoria el desglose matricial por boutique activa para las variantes de la pagina (`ExistenciaSucursalItemOut`), asegurando `cantidad_disponible = 0` para boutiques sin registro previo.
      - Calcular metricas consolidadas globales de red (`total_unidades_red`, `variantes_monitoreadas`, `alertas_stock_bajo`, `sedes_activas`).
      - Clasificar el estado segun umbral semaforico: `agotado` ($total \le 0$), `alerta_baja` ($0 < total \le 5$), `optimo` ($total > 5$).
  - **Criterios Mapeados:** `# AC-2`, `# AC-3`, `# AC-4`, `# AC-5`, `# AC-7`.
  - **Verificacion:** Verificacion de metodos del servicio con fixtures de base de datos y sesion transaccional.

- [x] **Tarea 1.4: Router REST analitico en `app/modules/gestion_operativa/cu26_inventario_global/router.py`**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu26_inventario_global/router.py`
    - `Ec-backend/app/modules/gestion_operativa/router.py`
  - **Descripcion:**
    * Crear router FastAPI con prefijo `/api/v1/admin/inventario/global`.
    * Exponer endpoint `GET /api/v1/admin/inventario/global` con query params (`q`, `id_categoria`, `id_sucursal`, `estado_stock`, `ordenar_por`, `pagina`, `limite`).
    * Custodiar con dependencia `require_roles(["administrador", "encargado_sucursal"])`.
    * Conectar el router en el agregador principal `app/modules/gestion_operativa/router.py`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-2`, `# AC-3`, `# AC-4`, `# AC-6`.
  - **Verificacion:** Consulta a la documentacion OpenAPI `/docs` y prueba manual con cliente HTTP.

- [x] **Tarea 1.5: Suite de pruebas automatizadas en `tests/modules/gestion_operativa/test_cu26_inventario_global.py`**
  - **Archivo:** `Ec-backend/tests/modules/gestion_operativa/test_cu26_inventario_global.py`
  - **Descripcion:**
    * Implementar 10 pruebas unitarias y de integracion con Pytest:
      1. `test_cu26_rbac_sin_token`: Peticion sin credenciales retorna HTTP 401 Unauthorized.
      2. `test_cu26_rbac_rol_cajero_denegado`: Token con rol cajero retorna HTTP 403 Forbidden.
      3. `test_cu26_rbac_rol_cliente_denegado`: Token con rol cliente retorna HTTP 403 Forbidden.
      4. `test_cu26_acceso_administrador_exitoso`: Token con rol administrador retorna HTTP 200 OK con payload estructurado.
      5. `test_cu26_acceso_encargado_exitoso`: Token con rol encargado_sucursal retorna HTTP 200 OK en modo consulta multi-sede.
      6. `test_cu26_agregacion_stock_red`: Comprobacion de que la suma de existencias de multiples sucursales es exacta y clasifica en 'optimo'.
      7. `test_cu26_variante_sin_inventario_retorna_cero`: Comprobacion de que variantes sin filas en `inventario_sucursal` devuelven stock 0 y estado 'agotado' sin fallos.
      8. `test_cu26_filtro_textual_q`: Busqueda insensible a mayusculas por nombre de producto y SKU.
      9. `test_cu26_filtro_estado_alerta_baja`: Filtrado de variantes con stock entre 1 y 5 unidades.
      10. `test_cu26_exclusion_sucursales_inactivas`: Comprobacion de que existencias en sucursales con `activa = False` no se contabilizan en el disponible de red.
  - **Criterios Mapeados:** `# AC-1` al `# AC-7`.
  - **Verificacion:** Ejecucion de `pytest tests/modules/gestion_operativa/test_cu26_inventario_global.py` con 10/10 tests en verde.


---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Contratos TypeScript en `src/app/modules/gestion_operativa/cu26_inventario_global/modelos/inventario-global.dto.ts`**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/modelos/inventario-global.dto.ts`
  - **Descripcion:**
    * Definir tipos literales: `EstadoStockGlobal` ('optimo' | 'alerta_baja' | 'agotado') y `CriterioOrdenacionInventario`.
    * Declarar interfaces fuertemente tipadas:
      - `ExistenciaSucursalItemOut`: identificador, nombre, ciudad, direccion, telefono, cantidades disponible y reservada.
      - `InventarioGlobalItemOut`: identificadores, SKU, producto, categoria, talla, color, swatch hex, totales de stock, estado y array de desglose.
      - `MetricasInventarioGlobalOut`: total unidades, variantes monitoreadas, alertas y sedes activas.
      - `InventarioGlobalFiltros`: estructura reactiva para el estado de busqueda y paginacion.
      - `RespuestaInventarioGlobalOut`: envoltura del endpoint con items, metricas y paginacion.
  - **Criterios Mapeados:** `# AC-10`, `# AC-12`.
  - **Verificacion:** Compilacion de TypeScript sin errores de tipado.

- [x] **Tarea 2.2: Servicio HTTP reactivo `InventarioGlobalAdminService` con Angular Signals en `src/app/modules/gestion_operativa/cu26_inventario_global/servicios/inventario-global-admin.service.ts`**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/servicios/inventario-global-admin.service.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/servicios/inventario-global-admin.service.spec.ts`
  - **Descripcion:**
    * Crear servicio inyectable en root consumiendo `${environment.apiUrl}/api/v1/admin/inventario/global`.
    * Manejar estado centralizado con Angular Signals: `items`, `metricas`, `totalRegistros`, `totalPaginas`, `cargando`, `error`, `filtros`, `itemSeleccionadoDetalle`, `modalDetalleAbierto`.
    * Implementar metodos reactivos: `cargarInventario()`, `actualizarFiltros()`, `cambiarPagina()`, `limpiarFiltros()`, `abrirDetalle()`, `cerrarDetalle()`.
    * Elaborar suite de pruebas unitarias `inventario-global-admin.service.spec.ts` con `HttpClientTestingModule` simulando respuestas exitosas y errores 500.
  - **Criterios Mapeados:** `# AC-9`, `# AC-10`, `# AC-11`, `# AC-14`.
  - **Verificacion:** Ejecucion de `ng test -- --include src/app/modules/gestion_operativa/cu26_inventario_global/servicios/inventario-global-admin.service.spec.ts` en verde.

- [x] **Tarea 2.3: Integracion de tarjeta en `AdminDashboardComponent`**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Incorporar la septima tarjeta boutique en `admin-dashboard.component.html` dentro de la categoria *"Gestion Operativa"*:
      - Condicion de visibilidad: `@if (esAdmin() || esEncargado())`.
      - Titulo oficial: `"Consultar inventario global"`.
      - Descripcion: `"Consolidado multi-sucursal de existencias, balances de red comercial y alertas de stock bajo."`.
      - Icono editorial: SVG limpio de red global / bodega (cero emojis).
      - Boton de accion: `"Consultar inventario global"` con `id="btn-consultar-inventario-global"` y `routerLink="/admin/inventario-global"`.
    * Actualizar en `admin-dashboard.component.ts` la propiedad computada `totalModulosActivos`:
      - Rol administrador: `'7 Activos'`.
      - Rol encargado_sucursal: `'5 Activos'`.
    * Actualizar `admin-dashboard.component.spec.ts` verificando el enlace, el boton y el conteo de modulos activos.
  - **Criterios Mapeados:** `# AC-8`.
  - **Verificacion:** Ejecucion de `ng test -- --include src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts` en verde.

- [x] **Tarea 2.4: Componente Standalone `InventarioGlobalAdminComponent` y ruta protegida**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.scss`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Declarar la ruta `/admin/inventario-global` en `app.routes.ts` custodiada por `canActivate: [authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
    * Crear `InventarioGlobalAdminComponent` con `ChangeDetectionStrategy.OnPush` y layout editorial centrado `max-w-[1440px]`.
    * Implementar cabecera institucional: H1 principal `"Consultar inventario global"`, migas de pan (`ADMINISTRACION CORPORATIVA / CONSULTAR INVENTARIO GLOBAL`) y boton superior `"<- Volver al Panel Principal"` con `routerLink="/admin"`.
  - **Criterios Mapeados:** `# AC-9`, `# AC-15`.
  - **Verificacion:** Navegacion fluida desde el dashboard corporativo hacia `/admin/inventario-global`.

- [x] **Tarea 2.5: Tarjetas de metricas superiores y barra reactiva de filtros**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.html`
  - **Descripcion:**
    * Crear bloque superior de 4 tarjetas de metricas cuantitativas sincronizadas con `service.metricas()`:
      1. Unidades Totales en Red (cifra de stock fisico disponible acumulado).
      2. Variantes Monitoreadas (total de SKUs evaluados).
      3. Alertas de Stock Bajo (indicador preventivo en tono ambar/camel).
      4. Sedes Comerciales Activas (total de boutiques fisicas operativas).
    * Desarrollar barra de herramientas de filtrado reactivo:
      - Buscador textual con *Subject* y *debounce* de 300 ms enlazado a `q`.
      - Selector reactivo de Categoria cargado dinamicamente desde el catalogo.
      - Selector reactivo de Sucursal para consultar una boutique especifica o *"Todas las sucursales"*.
      - Selector reactivo de Estado de Stock (*"Todos"*, *"Optimo"*, *"Alerta baja"*, *"Agotado"*).
      - Boton para limpiar filtros y regresar al estado inicial.
  - **Criterios Mapeados:** `# AC-10`, `# AC-11`.
  - **Verificacion:** Validacion de debounce en busqueda textual y actualizacion de metricas en tiempo real.

- [x] **Tarea 2.6: Tabla maestra consolidada, modal de desglose logistico, Luxury Banners y suite Vitest**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu26_inventario_global/paginas/inventario-global-admin.component.spec.ts`
  - **Descripcion:**
    * Construir la tabla maestra con estetica Atelier:
      - Prenda, thumbnail, categoria y codigo SKU en tipografia monoespaciada.
      - Talla y circulo de color con swatch `#HEX`.
      - Columna de existencias con chips interactivos para cada boutique activa coloreados segun disponibilidad (verde esmeralda, ambar o rojo).
      - Stock Total en Red destacando disponible y reservado.
      - Badges cromados de estado de existencias (*"Optimo"*, *"Alerta baja"*, *"Agotado"*).
      - Boton de accion para consultar detalle logistico ampliado.
    * Desarrollar modal accesible de detalle logistico por sede:
      - Desglose por boutique con nombre, direccion, telefono directo con enlace `tel:`, stock disponible y stock reservado para coordinacion inmediata de derivaciones inter-tiendas.
      - Cierre mediante tecla Escape, boton de aspa o clic en backdrop.
    * Implementar Luxury Banners para manejo no destructivo de errores HTTP 500 y skeletons de carga.
    * Desarrollar suite de pruebas unitarias `inventario-global-admin.component.spec.ts` con Vitest cubriendo los criterios `# AC-8` al `# AC-15`.
  - **Criterios Mapeados:** `# AC-8` al `# AC-15`.
  - **Verificacion:** Suite de componentes de Angular ejecutandose al 100% en verde con `ng test`.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada de suites automatizadas locales y auditoria de entorno**
  - **Comandos / Archivos:**
    - Backend: `pytest tests/modules/gestion_operativa/ -v`
    - Frontend: `npm test -- --watch=false`
    - Build: `npm run build`
    - Script de higiene: `python scratch/audit_emojis.py`
  - **Descripcion:**
    * Ejecutar la suite completa de pruebas de backend garantizando que ningun test preexistente ni los 10 tests de CU26 fallen.
    * Ejecutar la suite completa de pruebas unitarias de frontend en Vitest asegurando 0 regresiones.
    * Compilar el bundle de produccion de Angular verificando 0 errores de TypeScript y plantillas HTML.
    * Ejecutar la auditoria estricta de emojis en codigo fuente, documentacion y comentarios.
  - **Verificacion:** 100% de pruebas en verde y 0 emojis detectados.

- [x] **Tarea 3.2: Promocion de artefactos desde `.specs/changes/CU26/` hacia `.specs/finalized/CU26/` y modulo permanente**
  - **Archivos:**
    - `.specs/finalized/CU26/spec.md`
    - `.specs/finalized/CU26/design.md`
    - `.specs/finalized/CU26/tasks.md`
    - `.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md`
  - **Descripcion:**
    * Promocionar formalmente los documentos aprobados de cambio a la carpeta permanente `.specs/finalized/CU26/`.
    * Consolidar la especificacion permanente en `.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md`.
    * Limpiar `.specs/changes/CU26/` preservando unicamente `.gitkeep`.
  - **Verificacion:** Estructura de carpetas en `.specs/` consistente y sincronizada.

- [x] **Tarea 3.3: Registro formal del incremento funcional en CHANGELOGs (v2.2.0)**
  - **Archivos:**
    - `CHANGELOG.md`
    - `.specs/CHANGELOG.md`
  - **Descripcion:**
    * Documentar la version 2.2.0 reflejando la entrega del caso de uso CU26: "Consultar inventario global".
    * Detallar los componentes backend y frontend incorporados.
    * Registrar formalmente la exclusion definitiva de la aplicacion movil `Ec-mobile`.
  - **Verificacion:** Lectura y validacion de bitacora de cambios institucional.

---

## 3. Matriz de Trazabilidad Criterio EARS vs. Tareas de Implementacion

| Criterio EARS | Descripcion Sintetica | Capa | Tarea(s) Asignada(s) |
| :--- | :--- | :--- | :--- |
| **# AC-1** | Seguridad y Control de Acceso RBAC (401 / 403) | Backend | Tarea 1.4, Tarea 1.5 |
| **# AC-2** | Segregacion Funcional de Consulta por Rol | Backend | Tarea 1.3, Tarea 1.4, Tarea 1.5 |
| **# AC-3** | Endpoint Analitico de Inventario Global y Agregaciones | Backend | Tarea 1.1, Tarea 1.3, Tarea 1.4, Tarea 1.5 |
| **# AC-4** | Filtros Multicriterio (q, categoria, sucursal, estado) | Backend | Tarea 1.1, Tarea 1.3, Tarea 1.4, Tarea 1.5 |
| **# AC-5** | Tratamiento Defensivo contra Nulos y Sedes Inactivas | Backend | Tarea 1.1, Tarea 1.3, Tarea 1.5 |
| **# AC-6** | Validacion Estricta de Parametros y Paginacion (422) | Backend | Tarea 1.1, Tarea 1.2, Tarea 1.4, Tarea 1.5 |
| **# AC-7** | Consulta de Directorio Logistico de Sedes | Backend | Tarea 1.3, Tarea 1.5 |
| **# AC-8** | Tarjeta Boutique en AdminDashboardComponent | Frontend | Tarea 2.3, Tarea 2.6 |
| **# AC-9** | Arquitectura y Layout de /admin/inventario-global | Frontend | Tarea 2.2, Tarea 2.4, Tarea 2.6 |
| **# AC-10** | Tarjetas de Metricas Superiores (KPIs de Red) | Frontend | Tarea 2.1, Tarea 2.2, Tarea 2.5, Tarea 2.6 |
| **# AC-11** | Barra de Filtros Reactiva con Debounce (300 ms) | Frontend | Tarea 2.2, Tarea 2.5, Tarea 2.6 |
| **# AC-12** | Tabla Maestra Consolidada Multi-Sede | Frontend | Tarea 2.1, Tarea 2.6 |
| **# AC-13** | Modal de Detalle Logistico Multi-Sucursal | Frontend | Tarea 2.6 |
| **# AC-14** | Luxury Banners y Manejo No Destructivo de Errores | Frontend | Tarea 2.2, Tarea 2.6 |
| **# AC-15** | Estados de Carga, Paginacion y Empty State | Frontend | Tarea 2.4, Tarea 2.6 |

---

## 4. Definicion de Terminado (Definition of Done - DoD) para Fase 3

La Fase 3 (Plan de Tareas) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU26/tasks.md` se encuentre debidamente redactado y almacenado en el repositorio local.
2. Todas las casillas de tareas se encuentren en estado pendiente `[ ]` listas para su ejecucion controlada.
3. Se mantenga estrictamente la denominacion oficial: *"Consultar inventario global"*.
4. Se haya auditado que el documento carece al 100% de caracteres emoji o informales.
5. No se haya generado ni modificado codigo productivo en `Ec-backend`, `Ec-frontend` o `Ec-mobile`.
6. El usuario apruebe formalmente este plan de tareas para autorizar el inicio de la ejecucion de la **Oleada 1: Backend**.
