# Especificacion Formal de Requisitos: CU26 - Consultar inventario global

**ID del Caso de Uso:** CU26  
**Nombre:** Consultar inventario global  
**Paquete Arquitectonico:** `gestion_operativa` / `inventario`  
**Modulo Backend:** `app/modules/gestion_operativa/cu26_inventario_global`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu26_inventario_global`  
**Actores Principales:**  
- **Administrador:** Acceso integral y sin restricciones a la vision global consolidada de existencias, analisis transversal de inventario, auditoria multi-sucursal y monitoreo de quiebres de stock en toda la red comercial.  
- **Encargado de Sucursal:** Acceso de consulta informativa multi-sede (para derivacion de clientes, coordinacion logistica entre boutiques y consulta de disponibilidad cruzada).  
**Actores Bloqueados:**  
- **Cajero:** Bloqueo estricto por politica RBAC (HTTP 403 Forbidden).  
- **Cliente:** Bloqueo estricto por politica RBAC (HTTP 403 Forbidden).  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Riesgo Medio-Alto: Exactitud analitica en agregaciones multi-sede, integridad en balances de disponibilidad de existencias y rendimiento en consultas agregadas)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

En el modelo omnicanal de alta costura de **FashionStore**, la gestion de existencias fisicas no se limita a la administracion aislada de una tienda (CU24). La direccion corporativa y los lideres de boutique requieren una vision panoramica, unificada y en tiempo real de todas las unidades distribuidas a lo largo de la red de sucursales (CU21).

Cada prenda de diseno (CU22) se comercializa a traves de variantes especificas de talla y color (CU23). En la operacion diaria surgen escenarios criticos de abastecimiento y servicio al cliente:
1. **Atencion y derivacion de clientes en tienda:** Si un cliente visita una boutique en busca de una talla o color agotado en ese local, el personal autorizado debe poder consultar al instante en que otra sucursal de la ciudad o red comercial existen unidades disponibles, conociendo el telefono y direccion para coordinar el retiro o envio.
2. **Supervision corporativa y balance de existencias:** La gerencia comercial necesita evaluar que prendas presentan quiebre inminente de stock (alertas de stock bajo), que variantes estan completamente agotadas a nivel red y donde se concentran los excedentes fisicos para planificar reabastecimientos o transferencias inter-sucursal.
3. **Auditoria y agregacion analitica de alta fidelidad:** La consolidacion de existencias exige computar el stock disponible, el stock retenido en reservas y el stock fisico total, desglosado por cada boutique activa, garantizando total consistencia con las tablas transaccionales de inventario.

El caso de uso **CU26 - Consultar inventario global** proporciona la infraestructura de consulta agregada, filtros avanzados y visualizacion analitica de alta densidad en el panel de administracion web, manteniendo la confidencialidad corporativa y segregacion adecuada de roles.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Tecnica y Funcional de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), construida en Flutter 3.x, esta orientada con caracter exclusivo al canal de consumo final (B2C):
- Exploracion del catalogo editorial de colecciones y prendas.
- Experiencia interactiva de vestidor virtual con Realidad Aumentada (AR).
- Gestion de compras personales, pedidos directos y reserva de citas de prueba en boutique.

La consulta consolidada de inventario multi-sucursal, el balance analitico de red comercial, la auditoria global de existencias y el monitoreo corporativo de quiebres de stock constituyen atribuciones estrictamente administrativas y directivas. Estas funciones demandan pantallas de alta densidad de datos (tablas maestras con multiples columnas, desglose matricial por sede, chips interactivos, modales logisticos y tarjetas de metricas consolidadas), concebidas para estaciones de trabajo con monitores panoramicos de escritorio (`Ec-frontend`).

### 2.2 Exclusion Completa y Definitiva
Por consiguiente, el caso de uso CU26 **queda formalmente excluido en su totalidad de Ec-mobile**:
- No se creara ningun endpoint publico orientado a la app movil para el inventario global consolidado.
- No se incorporara ningun modelo de datos Dart, servicio HTTP, controlador BLoC/Riverpod ni pantalla en el repositorio `Ec-mobile`.
- Cero archivos o modificaciones en `Ec-mobile`. Todos los requerimientos se concentran de forma desacoplada en `Ec-backend` (FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon) y `Ec-frontend` (Angular 19+ Standalone).

---

## 3. Alcance y Trazabilidad Documental

1. **Documento Maestro del Sistema:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md)
   - Seccion 1.2.2 Objetivo 1: Integracion omnicanal de gestion de sucursales, inventario y puntos de venta.
   - Seccion 1.4 Alcance - Modulo de Inventario: Auditoria global de stock, balances de red y control de mermas.
   - Seccion 2.1.2 Requisitos Funcionales: CU26 - Consultar y Gestionar Inventario Global (supervision consolidada de existencias por tienda y consistencia de red).
2. **Esquema Relacional en PostgreSQL Neon:**
   - Tabla `fashionstore.inventario_sucursal`:
     * `id_inventario` (BIGSERIAL PRIMARY KEY).
     * `id_variante` (BIGINT REFERENCES `fashionstore.variantes_producto(id_variante)`).
     * `id_sucursal` (INTEGER REFERENCES `fashionstore.sucursales(id_sucursal)`).
     * `id_temporada` (INTEGER REFERENCES `fashionstore.temporadas(id_temporada)`).
     * `cantidad_disponible` (INTEGER NOT NULL DEFAULT 0).
     * `cantidad_reservada` (INTEGER NOT NULL DEFAULT 0).
     * `stock_minimo` (INTEGER NOT NULL DEFAULT 0).
     * `stock_alerta` (INTEGER NOT NULL DEFAULT 5).
     * `estado` (ENUM `disponible`, `reservada`, `agotada`, `proxima_ingreso`).
   - Tabla `fashionstore.variantes_producto`:
     * `id_variante`, `id_producto`, `id_talla`, `id_color`, `sku`, `precio_extra`, `activo`.
   - Tabla `fashionstore.productos`:
     * `id_producto`, `id_categoria`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `activo`.
   - Tabla `fashionstore.sucursales`:
     * `id_sucursal`, `nombre`, `direccion`, `telefono`, `id_ciudad`, `estado_activo`.
   - Tablas maestras de apoyo: `fashionstore.categorias`, `fashionstore.tallas`, `fashionstore.colores`, `fashionstore.ciudades`.
3. **Estandares de Diseno y Codigo:**
   - Skills operativas: `fashionstore-backend-sdd` y `fashionstore-frontend-sdd`.
   - Tokens de diseno editorial Atelier: Fondo Slate 50 (`#F8FAFC`), Contenedores White (`#FFFFFF`), Acento Obsidian (`#0F172A`), Acento Camel (`#AD8C63`), Acento Exito Esmeralda (`#059669`), Acento Alerta Ambar (`#D97706`), Acento Peligro Carmesi (`#DC2626`), Bordes Slate 200 (`#E2E8F0`).
   - Paradigma reactivo web: Angular 19+, Standalone Components, ChangeDetectionStrategy.OnPush, Angular Signals y reactive filters con debounce.

---

## 4. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

#### Control de Acceso y Matriz RBAC
- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema debera exigir autenticacion valida mediante token Bearer JWT con rol `administrador` o `encargado_sucursal` para consumir el endpoint analitico `GET /api/v1/admin/inventario/global`.
  * Si la peticion carece de token o este ha expirado o es invalido, el sistema debera responder con HTTP 401 Unauthorized (`CREDENCIALES_INVALIDAS`).
  * Si el usuario autenticado posee rol `cajero` o `cliente`, el sistema debera rechazar la peticion con HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

- **# AC-2 (Ubicuo - Segregacion Funcional de Consulta por Rol):**  
  El sistema debera conceder acceso a la consulta consolidada segun el rol del usuario autenticado:
  * Rol `administrador`: Acceso irrestricto a la vision global consolidada, desgloses de la totalidad de sucursales activas y metricas de toda la red comercial.
  * Rol `encargado_sucursal`: Acceso informativo multi-sede a las existencias consolidadas y desglose de sucursales para soporte de derivacion inter-tiendas, sin facultades de alteracion global de inventario.

#### Consulta Agregada, Consolidacion y Metricas
- **# AC-3 (Por Evento - Endpoint Analitico de Inventario Global):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/inventario/global`, el sistema debera ejecutar una agregacion analitica sobre el inventario de todas las sucursales activas y retornar un objeto JSON con:
  * `items`: Lista paginada de registros consolidados a nivel de variante/prenda conteniendo:
    - Identificadores y datos de prenda: `id_variante`, `sku`, `id_producto`, `producto_nombre`, `categoria_nombre`, `talla_nombre`, `color_nombre`, `precio_base`, `imagen_url`.
    - Agregacion de red: `stock_total_disponible` (suma de `cantidad_disponible` en todas las sucursales activas), `stock_total_reservado` (suma de `cantidad_reservada`), `stock_total_fisico` (`stock_total_disponible` + `stock_total_reservado`).
    - Estado de existencia global (`estado_stock_global`):
      * `'agotado'`: Si `stock_total_disponible` es igual a 0.
      * `'alerta_baja'`: Si `stock_total_disponible` es mayor a 0 y menor o igual a un umbral consolidado de alerta (o si alguna sede con inventario se encuentra en o por debajo de su `stock_alerta`).
      * `'optimo'`: Si `stock_total_disponible` supera el umbral de alerta.
    - Desglose por sucursal (`desglose_sucursales`): Arreglo con la situacion en cada boutique activa: `id_sucursal`, `sucursal_nombre`, `ciudad`, `cantidad_disponible`, `cantidad_reservada`, `stock_alerta`, `estado_sucursal` (`'optimo'`, `'alerta_baja'`, `'agotado'`, `'sin_inventario'`).
  * `metricas`: Objeto de metricas globales de red calculadas:
    - `unidades_totales_red`: Suma total de existencias fisicas disponibles en la red comercial.
    - `variantes_monitoreadas`: Total de SKUs/variantes activas evaluadas.
    - `alertas_stock_bajo`: Total de variantes que presentan stock bajo o en alerta en la red.
    - `variantes_agotadas`: Total de variantes con 0 unidades disponibles en toda la red.
  * `paginacion`: Metadatos de control estructurados conteniendo `total`, `pagina`, `limite` y `total_paginas`.

- **# AC-4 (Opcional - Filtros Multicriterio de Inventario Global):**  
  Donde se especifiquen parametros opcionales de filtrado en la peticion `GET /api/v1/admin/inventario/global`:
  * `q`: Busqueda textual insensible a mayusculas (operador `ILIKE`) aplicada sobre el nombre de la prenda o el codigo `sku`.
  * `id_categoria`: Filtrado entero para restringir a prendas pertenecientes a una categoria especifica.
  * `id_sucursal`: Filtrado entero para evaluar o focalizar la disponibilidad de existencias en una boutique en particular.
  * `estado_stock`: Filtrado por estado consolidado con valores admitidos: `'optimo'`, `'alerta_baja'`, `'agotado'` o `'todos'`.
  * `ordenar_por`: Criterio de ordenamiento opcional con valores: `'stock_asc'`, `'stock_desc'`, `'nombre_asc'`, `'nombre_desc'` o `'sku_asc'`. Por defecto: `'nombre_asc'`.  
  El sistema debera combinar los filtros aplicados mediante conjuncion logica (`AND`).

#### Tratamiento Defensivo y Resiliencia
- **# AC-5 (Invariante - Tratamiento Defensivo contra Nulos y Sucursales Inactivas):**  
  El sistema debera garantizar la resiliencia en la agregacion relacional:
  * Las variantes que aun no cuenten con registros en la tabla `inventario_sucursal` deberan retornar con existencias 0 (`COALESCE` a 0), sin generar excepciones ni omitir la variante del catalogo general.
  * Las sucursales marcadas con `estado_activo = False` no deberan sumarse al `stock_total_disponible` de la red comercial activa, preservando la veracidad del stock operativo.
  * En caso de prendas sin imagen o descripcion, se retornaran valores nulos o cadenas vacias sin romper el contrato del esquema Pydantic.

- **# AC-6 (Invariante - Validacion Estricta de Parametros y Paginacion):**  
  Si los parametros de paginacion (`pagina < 1` o `limite < 1` o `limite > 100`) o los identificadores numericos son invalidos, el sistema debera responder con HTTP 422 Unprocessable Entity, indicando claramente el campo rechazado.

- **# AC-7 (Por Evento - Consulta de Directorio Logistico de Sedes):**  
  En el desglose de sucursales devuelto por el endpoint o mediante consulta complementaria de sedes activas, el sistema debera proveer los datos de contacto logistico (`direccion`, `telefono` y `ciudad`) de cada boutique para posibilitar la comunicacion inmediata entre tiendas.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en Dashboard Principal y Navegacion
- **# AC-8 (Ubicuo - Tarjeta Boutique en AdminDashboardComponent):**  
  El componente `AdminDashboardComponent` debera incorporar una tarjeta boutique interactiva dentro de la seccion *"Gestion Operativa"*:
  * Titulo oficial: *"Consultar inventario global"*.
  * Descripcion: *"Consolidado multi-sucursal de existencias, balances de red comercial y alertas de stock bajo"*.
  * Icono editorial representativo de red de inventario / boutique global (SVG limpio, sin emojis).
  * Texto del boton: *"Consultar inventario global"*.
  * Enlace de navegacion con `routerLink="/admin/inventario-global"`.

- **# AC-9 (Ubicuo - Arquitectura y Layout de la Vista /admin/inventario-global):**  
  La pagina `InventarioGlobalAdminComponent` debera implementarse bajo las directivas institucionales de arquitectura:
  * Componente Standalone con `ChangeDetectionStrategy.OnPush`.
  * Layout editorial con ancho maximo `max-w-[1440px]`, centrado y fondo institucional Slate 50 (`#F8FAFC`).
  * Boton superior de retorno editorial: `"<- Volver al Panel Principal"` con `routerLink="/admin"`.
  * Encabezado editorial: Titulo H1 principal exacto *"Consultar inventario global"*.
  * Miga de pan (*Breadcrumb*): *"CONSULTAR INVENTARIO GLOBAL"*.
  * Subtitulo explicativo con tipografia Outfit y tono Slate 500.

#### Tarjetas de Metricas Superiores (KPIs de Red)
- **# AC-10 (Ubicuo - Tarjetas de Metricas Superiores):**  
  La vista debera desplegar en la parte superior un panel de 3 tarjetas de indicadores analiticos clave sincronizadas con el Signal de metricas del backend:
  * **Tarjeta 1 - Unidades Totales en Red:** Cantidad global de unidades fisicas disponibles en todas las tiendas de la cadena.
  * **Tarjeta 2 - Variantes Monitoreadas:** Total de combinaciones de SKU/producto activas y bajo seguimiento.
  * **Tarjeta 3 - Alertas de Stock Bajo:** Total de variantes con inventario en o por debajo del umbral de alerta (resaltada con acento ambar/camel de advertencia).
  * Opcionalmente, indicador de Variantes Agotadas con acento sutil carmesi.

#### Barra de Filtros Reactiva
- **# AC-11 (Por Evento - Barra de Filtros Reactiva con Debounce):**  
  La vista debera proveer una barra de herramientas de filtrado reactivo basada en Angular Signals:
  * Campo de busqueda textual (`busquedaTexto`) con retardo (*debounce* de 300 ms) enlazado al parametro `q` (para busqueda por nombre de prenda o SKU).
  * Selector reactivo de Categoria (`categoriaId`) con opciones cargadas desde el catalogo.
  * Selector reactivo de Sucursal (`sucursalId`) para enfocar la consulta en una boutique especifica o consultar *"Todas las sucursales"*.
  * Selector reactivo de Estado de Stock (`estadoStock`) con opciones: *"Todos los estados"*, *"Optimo"*, *"Alerta baja"* y *"Agotado"*.
  * Boton de restablecimiento rapido para limpiar filtros y volver al estado inicial.

#### Tabla Maestra Consolidada Multi-Sede
- **# AC-12 (Ubicuo - Tabla Maestra Consolidada Multi-Sede):**  
  La tabla maestra debera presentar los datos de forma clara y legible con tipografia Outfit:
  * **Prenda & SKU:** Thumbnail o avatar de la prenda, nombre oficial del producto, categoria y codigo SKU en fuente monospace.
  * **Talla & Color:** Badges tipograficos discretos que indiquen la talla y el color de la variante.
  * **Existencias por Sucursal:** Columna visual con chips interactivos para cada boutique activa, exhibiendo el nombre abreviado de la sede y las unidades disponibles, coloreados segun su estado (verde esmeralda para optimo, ambar para stock bajo, rojo para agotado).
  * **Stock Total en Red:** Cifra consolidada destacada con total disponible y desglose de unidades reservadas entre parentesis.
  * **Estado Global:** Insignia visual con estilo editorial: verde esmeralda para *"Optimo"*, ambar para *"Alerta baja"*, rojo para *"Agotado"*.
  * **Acciones:** Boton de accion para abrir el panel/modal de detalle logistico multi-sucursal.

#### Modal de Detalle Logistico por Sede
- **# AC-13 (Por Evento - Modal de Detalle Logistico Multi-Sucursal):**  
  Al hacer clic en el boton de detalle de una fila o sobre un chip de sucursal, el sistema debera desplegar un modal editorial accesible:
  * Titulo con el nombre de la prenda, variante (talla/color) y SKU consultado.
  * Tabla o lista de boutiques con: nombre de la sede, direccion fisica completa, ciudad, telefono de contacto directo y disponibilidad actual (`disponible`, `reservada`, `minimo`, `alerta`).
  * Destacado de las tiendas que cuentan con stock inmediato para agilizar la derivacion telefonica y coordinacion inter-tiendas.
  * Cierre accesible mediante boton de aspa, tecla `Escape` o clic en el fondo oscuro (*backdrop*).

#### Retroalimentacion, Estados de Carga y Resiliencia
- **# AC-14 (Ubicuo - Luxury Banners de Estado y Manejo No Destructivo de Errores):**  
  La vista debera contar con un contenedor de banners contextuales (*Luxury Banners*):
  * **Banner de Error Controlado:** Notificacion no bloqueante en caso de interrupcion del servicio o error HTTP (500, 503), con opcion de reintentar la carga.
  * **Banner Informativo:** Indicadores sobre filtros aplicados o estados de contingencia logistica.

- **# AC-15 (Ubicuo - Estados de Carga, Paginacion y Empty State):**  
  La interfaz debera manejar de manera fluida y reactiva:
  * Estado de carga mediante indicador skeleton o spinner editorial mientras `cargando() = true`.
  * Controles de paginacion inferior (pagina anterior, pagina siguiente, indicador "Pagina X de Y", selector de limite 10/20/50).
  * Estado vacio (*Empty State*) editorial cuando los filtros aplicados no encuentren ninguna variante o no haya registros de inventario en el sistema.

---

## 5. Matriz de Trazabilidad de Requisitos

| Criterio EARS | Capa | Componente / Archivo Proyectado | Metodo / Endpoint / Elemento | Codigo HTTP Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Backend | `cu26_inventario_global/router.py` | Dependencia `require_roles(["administrador", "encargado_sucursal"])` | 401 / 403 |
| **# AC-2** | Backend | `cu26_inventario_global/servicio.py` | Segregacion funcional de consulta por rol | 200 OK |
| **# AC-3** | Backend | `cu26_inventario_global/router.py` | `GET /api/v1/admin/inventario/global` | 200 OK |
| **# AC-4** | Backend | `cu26_inventario_global/servicio.py` | Filtros `q`, `id_categoria`, `id_sucursal`, `estado_stock`, `ordenar_por` | 200 OK |
| **# AC-5** | Backend | `cu26_inventario_global/servicio.py` | Agregacion defensiva con `COALESCE` y exclusion de sedes inactivas | 200 OK |
| **# AC-6** | Backend | `cu26_inventario_global/esquemas.py` | Esquemas Pydantic v2 `InventarioGlobalFiltrosIn`, `PaginacionIn` | 422 Unprocessable |
| **# AC-7** | Backend | `cu26_inventario_global/servicio.py` | Ingestion de datos logisticos de sucursales (direccion, telefono) | 200 OK |
| **# AC-8** | Frontend | `admin-dashboard.component.html` | Tarjeta "Consultar inventario global" en Gestion Operativa | N/A |
| **# AC-9** | Frontend | `inventario-global-admin.component.ts` | Ruta `/admin/inventario-global`, layout `max-w-[1440px]`, OnPush | N/A |
| **# AC-10** | Frontend | `inventario-global-admin.component.html` | Tarjetas de metricas superiores: Unidades en Red, Variantes, Alertas | N/A |
| **# AC-11** | Frontend | `inventario-global-admin.component.ts` | Barra de filtros reactiva con debounce de 300 ms y Signals | N/A |
| **# AC-12** | Frontend | `inventario-global-admin.component.html` | Tabla maestra consolidada con chips de sucursal y stock de red | N/A |
| **# AC-13** | Frontend | `inventario-global-admin.component.ts` | Modal interactivo de detalle logistico y coordinacion inter-tiendas | N/A |
| **# AC-14** | Frontend | `inventario-global-admin.component.html` | Luxury Banners contextuales para manejo no destructivo de errores | N/A |
| **# AC-15** | Frontend | `inventario-global-admin.component.html` | Paginacion reactiva, skeleton loaders y empty state editorial | N/A |

---

## 6. Definicion de Terminado (Definition of Done - DoD) para Fase 1

La Fase 1 (Requisitos EARS) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU26/spec.md` se encuentre debidamente redactado y almacenado en el repositorio local.
2. Se haya ratificado explicitamente la exclusion total de la aplicacion movil (`Ec-mobile`), documentando su justificacion tecnica en la Seccion 2.
3. Todos los criterios de aceptacion (# AC-1 a # AC-15) esten numerados, clasificados segun la sintaxis formal EARS y vinculados a sus capas tecnicas correspondientes.
4. Se haya auditado que el documento carece al 100% de caracteres emoji o lenguaje informal.
5. Se respete estrictamente la prohibicion de modificar codigo productivo en Ec-backend, Ec-frontend o Ec-mobile durante esta fase.
6. El usuario apruebe formalmente esta especificacion para autorizar la transicion a la Fase 2 (Diseno de Arquitectura y Contratos).
