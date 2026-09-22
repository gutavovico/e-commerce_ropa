# Changelog Técnico de Arquitectura y SDD — FashionStore

Todas las modificaciones notables, correcciones de errores de infraestructura y promociones de especificaciones del proyecto se documentan en este archivo.

## [2.7.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU30 - Consultar bitacora (Seguridad, Gobernanza y Auditoria Corporativa):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/seguridad/CU30-consultar-bitacora.md`](.specs/modules/seguridad/CU30-consultar-bitacora.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU30/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU30/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion justificada de la aplicacion movil (`Ec-mobile`). La consulta de bitacora, auditoria forense y analisis de mutaciones de datos del sistema corresponden con exclusividad a la direccion de tecnologia y superadministracion en la consola web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni endpoints.
- **Validacion Completa:**
  - Backend: 312/312 tests en verde en `pytest` (14/14 especificos de CU30 en `test_cu30_bitacora.py`); migracion DDL Alembic `0011_cu30_bitacora.py` en PostgreSQL Neon sobre `fashionstore.bitacora` con indices en `creado_en DESC`, `severidad`, `tabla_modulo`, `id_usuario`; modelo relacional `Bitacora` (`app/modules/seguridad/cu30_bitacora/modelos.py`); esquemas Pydantic v2 defensivos con filtros multicriterio, metricas agregadas y serializacion de payloads JSON; servicio de dominio `ServicioBitacoraAuditoria` con control estricto RBAC (solo `administrador` y alias `admin`, bloqueo 403 para resto de roles); endpoints REST bajo `/api/v1/admin/bitacora`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores, 0 advertencias), 358/358 tests en verde en Vitest / Angular CLI (9/9 en `bitacora-admin.component.spec.ts`, 4/4 en `bitacora-admin.service.spec.ts`, 25/25 en `admin-dashboard.component.spec.ts`); duodecima tarjeta corporativa en `AdminDashboardComponent` ("Consultar bitacora") bajo "Gobernanza y Accesos" con badge "Seguridad y Auditoria", boton `id="btn-consultar-bitacora"`, directiva dual de navegacion (`routerLink="/admin/bitacora"` y `(click)="navegar('/admin/bitacora', $event)"`), conteo de 12 modulos activos para administrador, y prueba unitaria de despacho de evento click real sobre el DOM; componente Standalone `BitacoraAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/bitacora`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs (Total Eventos, Mutaciones Criticas, Alertas / Errores, Operadores Activos); barra reactiva de filtros multicriterio con retardo debounce de 300 ms en busqueda textual; tabla cronologica con timestamps monoespaciados UTC, badges cromaticos de severidad (`INFO`, `WARN`, `ERROR`, `CRITICAL`); modal accesible para inspeccion de JSON diff (`payload_anterior` vs `payload_nuevo`); y Luxury Banners contextuales.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 59. Prevencion de Navegacion Estatica mediante Directiva Dual y roleGuard Permisivo en Rutas Administrativas
- **Causa:** En Angular, las navegaciones pueden resolver silenciosamente en `false` sin disparar captura de error si un guard bloquea o hay desfase de roles (`roleGuard(['administrador'])` rechazando alias como `admin`).
- **Solucion:** Declaracion explicita en `app.routes.ts` de roles compatibles `roleGuard(['administrador', 'admin'])`, adopcion de directiva dual en botones de navegacion del panel administrativo (`routerLink` mas click handler defensivo con reintento) y verificacion unitaria mediante despacho de evento `MouseEvent` nativo sobre el DOM.

#### 60. Alineacion de Instancia FastAPI en Entorno de Pruebas Unitarias y Aislamiento de Red
- **Causa:** La existencia de importaciones disjuntas entre `main` y `app.main` en `conftest.py` provocaba bifurcacion de instancias de la aplicacion FastAPI, saltandose overrides de dependencias como `get_db` y generando llamadas de red concurrentes a PostgreSQL Neon remoto durante la ejecucion de la suite completa.
- **Solucion:** Normalizacion de importaciones en `conftest.py` y `test_health.py` hacia `from main import app`, e implementacion de overrides defensivos en todas las pruebas de seguridad para evitar conexiones no mockeadas a bases de datos remotas.

---

## [2.6.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU29 - Visualizar indicadores empresariales (Inteligencia de Negocios y Analitica Directiva):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU29-visualizar-indicadores-empresariales.md`](.specs/modules/comercial/CU29-visualizar-indicadores-empresariales.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU29/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU29/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion justificada de la aplicacion movil (`Ec-mobile`). La inteligencia de negocios, supervision cuantitativa de rentabilidad agregada, ranking macro de prendas y comparativa de productividad multi-sucursal corresponden exclusivamente a competencias directivas y de back-office corporativo radicadas en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni peticiones HTTP.
- **Validacion Completa:**
  - Backend: 298/298 tests en verde en `pytest` (17/17 especificos de CU29 en `test_cu29_indicadores.py`); modelos declarativos consolidados en esquema `fashionstore` (`VentaORM`, `VentaDetalleORM`, `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `SucursalORM`, `CiudadORM`); esquemas Pydantic v2 defensivos con saneamiento y validador de rangos cronologicos (`fecha_desde <= fecha_hasta`); motor analitico `ServicioIndicadoresEmpresariales` con segregacion forzosa de alcance por sucursal para encargados, calculo relacional de variaciones porcentuales relativas contra periodos precedentes sin division por cero, agrupaciones cronologicas con `date_trunc`, ranking Top N de productos y distribucion multicanal; endpoints REST bajo `/api/v1/admin/indicadores` custodiados por RBAC con roles autorizados (`administrador` y `encargado_sucursal`).
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 338/338 tests en verde en Vitest / Angular CLI (11/11 en `indicadores-admin.component.spec.ts`, 10/10 en `indicadores-admin.service.spec.ts`, 21/21 en `admin-dashboard.component.spec.ts`); undecima tarjeta corporativa en `AdminDashboardComponent` ("Visualizar indicadores empresariales") bajo "Analitica y Reportes" con badge "Business Intelligence", boton `id="btn-visualizar-indicadores-empresariales"`, doble directiva de navegacion (`routerLink="/admin/indicadores"` y `(click)="navegar('/admin/indicadores', $event)"`) y prueba unitaria de despacho de evento click sobre el DOM; componente Standalone `IndicadoresAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/indicadores`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs ejecutivos con flechas de tendencia y color semaforico discreto; conmutador reactivo de periodos ('7d', '30d', 'mes_actual', 'anio_actual', 'personalizado'); selector de sucursales habilitado para administrador y bloqueado con badge para encargado; graficas vectoriales nativas en SVG puro (curva interpolada de ingresos con area sombreada y puntos interactivos con tooltips, barras horizontales relativas de Top 5 productos, barras de progreso segmentadas por canales y categorias) y comparativa de sucursales restringida a administradores; skeletons de carga y Luxury Banners para contingencias no destructivas.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 56. Segregacion Territorial Defensiva en Consultas Analiticas para Encargados
- **Causa:** Un usuario con rol encargado de sucursal podia enviar parametros `id_sucursal` arbitrarios en los query params de los endpoints analiticos o intentar consultar la comparativa corporativa entre sucursales.
- **Solucion:** El servicio `ServicioIndicadoresEmpresariales` sobreescribe forzosamente `id_sucursal` con el identificador asignado al usuario encargado en base de datos, ignorando cualquier parametro externo, y arroja `AccesoComparativaDenegadoError` (HTTP 403) ante cualquier intento de acceso al endpoint de comparativa entre tiendas.

#### 57. Prevencion Determinista de Division por Cero en Variaciones Relativas y Ticket Promedio
- **Causa:** En periodos nuevos o sucursales sin operaciones transaccionales registradas en el periodo actual o precedente, las operaciones de cociente para calcular el ticket promedio o la variacion porcentual generaban errores aritmeticos de division por cero.
- **Solucion:** Implementacion de clausulas condicionales y funciones `NULLIF`/`COALESCE` en agregaciones SQL y evaluacion defensiva en Python devolviendo `0.00` de forma determinista ante denominadores nulos o iguales a cero.

#### 58. Visualizaciones Graficas Vectoriales en SVG Nativo con Cambio de Deteccion OnPush
- **Causa:** El uso de bibliotecas de graficos externas de gran volumen (como Chart.js o D3) incrementa el tamano del bundle y genera dependencias complejas con el arbol de componentes reactivo de Angular.
- **Solucion:** Desarrollo de directivas y trazados SVG nativos puros integrados con Angular Signals (`puntosGraficoCalculados`, `lineaCurvaSvg`, `areaSombreadaSvg`, `lineasGuiaY`), logrando un renderizado fluido, responsive y con zero dependencias externas pesadas.

---

## [2.5.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU28 - Consultar ventas y reservas (Auditoria Comercial y Consolidacion de Ventas y Reservas):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU28-consultar-ventas-reservas.md`](.specs/modules/comercial/CU28-consultar-ventas-reservas.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU28/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU28/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La consulta analitica de comprobantes de ventas, auditoria de reservas multi-sucursal y computo financiero de ticket promedio corresponden exclusivamente a atribuciones de trastienda y back-office corporativo que residen en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin modelos, pantallas ni servicios mutables.
- **Validacion Completa:**
  - Backend: 280/280 tests en verde en `pytest` (16/16 especificos de CU28 en `test_cu28_ventas_reservas.py`); modelos declarativos ORM en `fashionstore` (`VentaORM`, `VentaDetalleORM`, `PagoORM`, `ReservaORM`, `ReservaDetalleORM`); esquemas Pydantic v2 defensivos con saneamiento y validador de consistencia de fechas (`fecha_desde <= fecha_hasta`); servicio transaccional `ServicioConsultarVentasReservas` con segregacion obligatoria por sucursal segun rol (`administrador` vs `encargado_sucursal`), calculo de metricas cuantitativas de red (`monto_total_facturado`, `total_ventas_concluidas`, `reservas_activas`, `ticket_promedio`) y consulta expandida de detalle; endpoints REST unificados bajo `/api/v1/admin/ventas-reservas` protegidos por RBAC con roles autorizados.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 310/310 tests en verde en Vitest / Angular CLI (32/32 en `ventas-reservas-admin.component.spec.ts`, 10/10 en `ventas-reservas-admin.service.spec.ts`, 19/19 en `admin-dashboard.component.spec.ts`); decima tarjeta corporativa en `AdminDashboardComponent` ("Consultar ventas y reservas") dentro de "Gestion Comercial" con badge "Auditoria y Ventas", boton `id="btn-consultar-ventas-reservas"`, doble directiva de navegacion (`routerLink="/admin/ventas-reservas"` y `(click)="navegar('/admin/ventas-reservas', $event)"`) y visibilidad RBAC; componente Standalone `VentasReservasAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/ventas-reservas`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs reactivas; barra reactiva de filtros multicriterio con retardo *debounce* de 300 ms en busqueda textual; tabla maestra unificada de comprobantes con badges cromaticos por tipo y estado; modal accesible de detalle transaccional (`role="dialog"`) con desglose de lineas de prenda y traza de pagos; y Luxury Banners contextuales para retroalimentacion amigable.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 53. Segregacion Territorial Transaccional Estricta para Encargados de Sucursal
- **Causa:** Un encargado de sucursal podia enviar identificadores de otras sucursales en los filtros de consulta o intentar acceder directamente a los comprobantes de venta o reserva de sedes ajenas.
- **Solucion:** El servicio de dominio valida el rol del usuario autenticado e ignora cualquier parametro foraneo de sucursal para `encargado_sucursal`, forzando la consulta unicamente a su sede asignada y arrojando `SucursalNoAutorizadaError` (HTTP 403) ante cualquier intento de acceso foraneo a detalles unitarios.

#### 54. Unificacion Polimorfica y Determinista de Transacciones de Ventas y Reservas
- **Causa:** Las ventas y reservas residen en tablas relacionales disjuntas con esquemas y ciclos de vida diferentes, lo que dificultaba una paginacion y ordenamiento unificados por monto o fecha.
- **Solucion:** Implementacion de consulta unificada en `ServicioConsultarVentasReservas` con mapeo normalizado a `TransaccionResumenItemOut`, admitiendo filtrado conjunto o segmentado por tipo de operacion y ordenamiento determinista sobre el consolidado.

#### 55. Calculo Cuantitativo de Ticket Promedio Libre de Division por Cero
- **Causa:** En rangos de fechas o sucursales con cero transacciones de venta concluidas, el calculo del ticket promedio (`monto_total / cantidad_ventas`) provocaba excepciones de division por cero.
- **Solucion:** Implementacion defensiva en `obtener_metricas` que evalua la cantidad de ventas concluidas y asigna `0.0` de forma segura cuando no existen ventas concluidas en el periodo consultado.

---

## [2.4.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU27 - Gestionar promociones (Marketing, Descuentos y Cupones Comerciales):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU27-gestionar-promociones.md`](.specs/modules/comercial/CU27-gestionar-promociones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU27/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU27/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La definicion de campanas comerciales, parametros financieros de descuento, aprovisionamiento de cupones con topes monetarios y supervision analitica del volumen de canjes corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 264/264 tests en verde en `pytest` para toda la suite acumulada (16/16 especificos de CU27); migracion DDL Alembic `0008_cu27_promociones.py` ejecutada en PostgreSQL Neon; tabla `fashionstore.promociones` con restricciones `CheckConstraint("fecha_fin > fecha_inicio", name="chk_promociones_fechas_orden")`, `CheckConstraint("tipo_descuento IN ('porcentaje', 'monto_fijo')", name="chk_promociones_tipo_descuento")`, `CheckConstraint("valor_descuento > 0", name="chk_promociones_valor_positivo")`, `CheckConstraint("(tipo_descuento != 'porcentaje') OR (valor_descuento >= 1.00 AND valor_descuento <= 100.00)", name="chk_promociones_porcentaje_tope")`, e indice unico funcional lower-case (`Index("uq_promociones_codigo_cupon_lower", func.lower(func.trim(codigo_cupon)), unique=True, postgresql_where=codigo_cupon.isnot(None))`); modelo relacional `PromocionORM` en esquema `fashionstore` con sinonimo `activa = synonym("estado_activo")` y claves foraneas hacia categorias y productos; esquemas Pydantic v2 defensivos con saneamiento y conversion a mayusculas de codigos de cupon; servicio transaccional `ServicioGestionPromociones` con paginacion multicriterio (`q`, `tipo_descuento`, `estado_activo`, `alcance`, `ordenar_por`), calculo de metricas cuantitativas de red (`promociones_activas`, `cupones_vigentes`, `descuento_promedio`, `usos_totales`) y conmutacion atomica de estado logico; y endpoints REST bajo `/api/v1/admin/promociones` custodiados por RBAC con roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 268/268 tests en verde en Vitest / Angular CLI (13/13 en `promociones-admin.component.spec.ts`, 9/9 en `promociones-admin.service.spec.ts`, 15/15 en `admin-dashboard.component.spec.ts`); novena tarjeta corporativa en `AdminDashboardComponent` ("Gestionar promociones") dentro de la categoria "Gestion Comercial" con badge "Marketing y Descuentos", boton `id="btn-gestionar-promociones"`, doble directiva de navegacion (`routerLink="/admin/promociones"` y `(click)="navegar('/admin/promociones', $event)"`) y visibilidad RBAC para administrador y encargado; componente Standalone `PromocionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/promociones`; layout editorial `max-w-[1440px]`; cabecera con H1 "Gestionar promociones" y boton superior `"Volver al Panel Principal"`; grid superior de 4 tarjetas de KPIs cuantitativos; barra reactiva de filtros con retardo *debounce* de 300 ms en busqueda textual; tabla maestra con chips monoespaciados e indicadores de vigencia cromados (`Vigente`, `Proxima`, `Expirada`); modales reactivos con validacion sincronica inline de fechas y rango porcentual; y Luxury Banners para captura no destructiva de colisiones HTTP 409 y validaciones 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 50. Normalizacion Idempotente de Estado y Compatibilidad Retroactiva en Tabla `fashionstore.promociones`
- **Causa:** La base DDL preexistente incluia la columna `activa` de tipo boolean, mientras que los estandares de arquitectura SDD requerian `estado_activo`, junto con constraints CHECK de orden de fechas, rangos porcentuales e indice unico funcional lower-case sobre `codigo_cupon`.
- **Solucion:** Implementacion de la migracion Alembic `0008_cu27_promociones.py` que renombra de forma segura e idempotente `activa` a `estado_activo`, define constraints CHECK y crea el indice `uq_promociones_codigo_cupon_lower` con clausula condicional `WHERE codigo_cupon IS NOT NULL`. Se establecio ademas `activa = synonym("estado_activo")` en `PromocionORM` para garantizar compatibilidad retroactiva total.

#### 51. Control Dinamico de Topes Financieros y Validacion Condicional de Alcance
- **Causa:** Promociones con descuento porcentual requieren opcionalmente un tope maximo monetario para evitar perdidas en compras de alto valor, mientras que promociones por monto fijo no deben parametrizar tope. Asimismo, alcances por categoria o producto exigian validar la presencia y consistencia de las entidades referenciadas.
- **Solucion:** Implementacion de validadores defensivos `@model_validator(mode="after")` en backend y `validadorPromocion` sincronico a nivel de `FormGroup` en frontend, bloqueando anomalías en tiempo real y habilitando o inhabilitando campos condicionalmente segun el tipo de descuento y alcance seleccionado.

#### 52. Preservacion de Notificaciones de Exito y Aislamiento de Errores en Operaciones de Mutacion
- **Causa:** En el servicio reactivo de frontend, refrescar la lista de promociones inmediatamente tras una creacion, edicion o conmutacion de estado podia provocar que el reseteo de variables de estado eliminara de forma prematura el mensaje de exito para el usuario.
- **Solucion:** Desacoplamiento de la limpieza de errores y mensajes de exito en `PromocionesAdminService`, preservando el banner contextual de confirmacion tras el ciclo de recarga de datos en segundo plano.

---

## [2.3.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU24 - Gestionar temporadas y colecciones (Calendario Editorial y Curaduria de Moda):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/catalogo/CU24-gestionar-temporadas-colecciones.md`](.specs/modules/catalogo/CU24-gestionar-temporadas-colecciones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU24/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La planificacion del calendario estacional de moda, la vigencia de campanas y la estructuracion taxonomica de colecciones capsula corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 248/248 tests en verde en `pytest` para toda la suite acumulada (14/14 especificos de CU24); migracion DDL Alembic `0007_cu24_temporadas_colecciones.py` ejecutada en PostgreSQL Neon; modelos relacionales `TemporadaORM` y `ColeccionORM` en esquema `fashionstore` con restricciones `CheckConstraint("fecha_fin > fecha_inicio", name="chk_temporadas_fechas_orden")` y `CheckConstraint("anio >= 2020", name="chk_temporadas_anio_valido")`; indice unico funcional insensible a mayusculas (`Index("uq_temporadas_nombre_anio_lower", func.lower(func.trim(nombre)), anio, unique=True)`); compatibilidad retroactiva mediante `synonym("estado_activo")` preservando atributos heredados; esquemas Pydantic v2 con validacion de rango cronologico y saneamiento de cadenas; servicios de dominio `ServicioGestionTemporadas` y `ServicioGestionColecciones` con soporte para listados paginados multicriterio, baja logica no destructiva (`estado_activo = False`) e integridad referencial forzada; y 10 endpoints REST bajo `/api/v1/admin/temporadas` y `/api/v1/admin/colecciones` custodiados por RBAC con roles `administrador` y `encargado_sucursal` protegiendo contra accesos no autenticados (401) o no autorizados (403).
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 244/244 tests en verde en Vitest / Angular CLI (11/11 en `temporadas-colecciones-admin.component.spec.ts`, 10/10 en `temporadas-colecciones-admin.service.spec.ts`, 13/13 en `admin-dashboard.component.spec.ts`); octava tarjeta corporativa en `AdminDashboardComponent` ("Gestionar temporadas y colecciones") dentro de la categoria "Taxonomia Comercial" con badge "Calendario Editorial", boton `id="btn-gestionar-temporadas-colecciones"` y visibilidad condicionada por RBAC para administrador y encargado; componente Standalone `TemporadasColeccionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/temporadas-colecciones`; sistema de pestanas reactivas (Temporadas / Colecciones); barra reactiva de filtros con retardo *debounce* de 300 ms en busqueda textual; modales reactivos con validacion sincronica de fechas (`fecha_fin > fecha_inicio`), badges cromaticos y Luxury Banners para captura no destructiva de errores HTTP 409 y 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 47. Validacion de Consistencia Cronologica y Coexistencia con Modelos Previos (`chk_temporadas_fechas_orden` y `TemporadaORM.activa`)
- **Causa:** La definicion formal requeria validar que `fecha_fin > fecha_inicio` e indices unicos lower-case sobre nombre y anio. Asimismo, pruebas preexistentes del catalogo invocaban `TemporadaORM` con el atributo booleano `activa` o inicializacion directa `TemporadaORM(nombre=..., activa=True)`, mientras que el nuevo esquema estandarizaba el estado bajo `estado_activo`.
- **Solucion:** Implementacion de `CheckConstraint("fecha_fin > fecha_inicio", name="chk_temporadas_fechas_orden")` e indice compuesto `uq_temporadas_nombre_anio_lower` en PostgreSQL Neon mediante revision Alembic `0007_cu24_temporadas_colecciones.py`. Adicion de `synonym("estado_activo")` y constructor compatible en `TemporadaORM` para asegurar compatibilidad total con tests heredados sin fisuras en base de datos.

#### 48. Validacion Sincronica y Defensiva de Fechas en Formularios Reactivos Web
- **Causa:** La seleccion manual de fechas en la creacion o edicion de temporadas en el cliente web permitia inadvertidamente seleccionar fechas de culminacion anteriores a la fecha de inicio, requiriendo el rechazo en backend con HTTP 422.
- **Solucion:** Implementacion de un validador personalizado a nivel de `FormGroup` en Angular (`validarRangoFechas`) que intercepta la discrepancia cronologica en tiempo real, inhabilita el boton de envio y proyecta alertas contextuales inmediatas en el modal corporativo.

#### 49. Aislamiento de Estado y Debounce Desacoplado en Interfaz Dual de Pestanas
- **Causa:** En una interfaz de administracion compartida con pestanas para temporadas y colecciones, busquedas rapidas con peticiones asincronas en vuelo podian cruzar estados o resetear indebidamente la paginacion de la entidad contigua.
- **Solucion:** Desacoplamiento estricto del estado reactivo mediante Signals independientes por entidad, operadores RxJS `debounceTime(300)` y reinicio focalizado de paginacion al alternar de pestana.

---

## [2.2.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU26 - Consultar inventario global (Vision Panoramica Multi-Sede y Balances de Red):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md`](.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU26/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU26/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La auditoria corporativa analitica, la consolidacion de existencias multi-sucursal y los balances de red comercial corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 234/234 tests en verde en `pytest` para toda la suite acumulada (10/10 especificos de CU26); servicio analitico `ServicioInventarioGlobal` con agregacion relacional uniendo `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `TallaORM`, `ColorORM`, con `LEFT OUTER JOIN` hacia `InventarioSucursalORM` y `SucursalORM` activa; computo de disponibilidad consolidada mediante `func.sum` y `func.coalesce` defensivo; exclusion estricta de sucursales inactivas; metricas cuantitativas de red (`total_unidades_red`, `variantes_monitoreadas`, `alertas_stock_bajo`, `sedes_activas`); semaforizacion automatizada de estado de existencias (`optimo`, `alerta_baja`, `agotado`); filtros multicriterio combinables (`q`, `id_categoria`, `id_sucursal`, `estado_stock`, `ordenar_por`) con paginacion determinista; y endpoint REST analitico `GET /api/v1/admin/inventario/global` custodiado por roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 222/222 tests en verde en Vitest / Angular CLI (23/23 en `inventario-global-admin.component.spec.ts`, 6/6 en `inventario-global-admin.service.spec.ts`, 12/12 en `admin-dashboard.component.spec.ts`); septima tarjeta boutique en `AdminDashboardComponent` ("Consultar inventario global") dentro de "Gestion Operativa" con badge "Consolidado Multi-Sede", boton `id="btn-consultar-inventario-global"` y visibilidad segmentada por RBAC para administrador y encargado; componente Standalone `InventarioGlobalAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/inventario-global`; layout editorial centrado `max-w-[1440px]`; boton superior `"Volver al Panel Principal"`; grid superior de 4 tarjetas de metricas de red; barra de filtros reactiva con retardo *debounce* de 300 ms en busqueda textual; tabla maestra consolidada con chips interactivos de stock por sede, valores en red y badges cromaticos; modal accesible de detalle logistico y coordinacion inter-tiendas con direccion fisica y enlace directo `tel:`; y Luxury Banners para gestion no destructiva de errores de red.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 44. Agregacion Defensiva contra Nulos y Exclusion de Sucursales Inactivas
- **Causa:** Variantes registradas sin existencias previas en `inventario_sucursal` o asociadas a sucursales clausuradas o inactivas podian generar valores `NULL` o distorsionar el stock real disponible de la red.
- **Solucion:** Implementacion de `func.coalesce(func.sum(case(...)), 0)` junto con filtro relacional estricto `SucursalORM.activa.is_(True)`, garantizando que el stock de red refleje unicamente sedes operativas y devuelva 0 de forma segura para prendas sin stock previo.

#### 45. Enlace Logistico Inter-Tiendas con Informacion de Contacto Directo
- **Causa:** Ante alertas de rotura de stock en una tienda, el personal operativo carecia de un mecanismo rapido para ubicar y contactar a boutiques con inventario excedente.
- **Solucion:** Incorporacion matricial de los datos de contacto (`direccion`, `ciudad` y `telefono`) en el desglose de existencias por sucursal y creacion de enlaces directos `tel:` en el modal de detalle logistico para derivaciones telefonicas inmediatas.

#### 46. Optimizacion de Subconsultas Paginadas y Conteo Determinista
- **Causa:** En consultas analiticas con agrupamiento y clausulas `HAVING`, el calculo ingenuo de `total_registros` producia conteos incorrectos o duplicacion de lineas.
- **Solucion:** Encapsulamiento del conteo en una subconsulta estructurada con alias explicito (`conteo_subquery`), asegurando una paginacion y calculo de `total_paginas` matematicamente exacto.

---

## [2.1.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU25 - Gestionar Proveedores (Cadena de Abastecimiento y Talleres Textiles):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md`](.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU25/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU25/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La gestion societaria, contratos de confeccion mayorista, captura de datos tributarios (NIT/RUT) y evaluacion de talleres textiles corresponden a labores exclusivas de trastienda y back-office corporativo web (`Ec-frontend`). La app movil B2C queda formalmente excluida sin pantallas ni modelos mutables.
- **Validacion Completa:**
  - Backend: 224/224 tests en verde en `pytest` para toda la suite acumulada (16/16 especificos de CU25); modelo ORM en esquema `fashionstore` (`ProveedorORM`), revision DDL Alembic `0006_cu25_proveedores_extension.py` en PostgreSQL Neon; restricciones de unicidad estricta sobre `nit_rut` y `razon_social` (insensible a mayusculas); esquemas Pydantic v2 con validadores de sanitizacion obligatoria y correo valido; excepciones semanticas de dominio (`ProveedorNoEncontradoError`, `ProveedorDuplicadoError`, `ProveedorInvalidoError`); servicio de dominio con soporte multicriterio paginado, prevencion de colisiones 409 y baja logica (`estado_activo = False`) preservando integridad historica referencial; y endpoints REST bajo `/api/v1/admin/proveedores` protegidos por roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 192/192 tests en verde en Vitest / Angular CLI (13/13 en `proveedores-admin.component.spec.ts`, 9/9 en `proveedores-admin.service.spec.ts`, 11/11 en `admin-dashboard.component.spec.ts`); sexta tarjeta boutique en `AdminDashboardComponent` ("Proveedores y Fabricantes") dentro de "Gestion de Abastecimiento" con badge "Cadena de Suministro" y control RBAC dinamico (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `ProveedoresAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals; boton superior editorial `"<- Volver al Panel Principal"` con `routerLink="/admin"`; barra reactiva de filtros con busqueda textual con debounce de 300 ms, selector de estado y selector de rubro textil; tabla maestra editorial con NIT/RUT, contacto comercial, ciudad e insignias cromadas de estado (verde esmeralda / slate); modales reactivos con `NonNullableFormBuilder` (Alta, Edicion y Confirmacion de Baja Logica con advertencia de cese de recepcion sin perdida de historico); y Luxury Banners para captura contextual no destructiva de errores HTTP 409 y 422 preservando los datos del formulario.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 41. Prevencion de Duplicidad Tributaria y Societaria Multicapa (`uq_proveedores_nit_rut` y `uq_proveedores_razon_social`)
- **Causa:** La duplicidad inadvertida de registros de un mismo taller textil bajo leves variaciones de razon social o reutilizacion de NIT generaba inconsistencias fiscales y distorsionaba la auditoria de abastecimiento.
- **Solucion:** Validacion previa en capa de servicio con consultas normalizadas y creacion de indices unicos `uq_proveedores_nit_rut` y `uq_proveedores_razon_social` (con funcion `LOWER()` en PostgreSQL Neon), emitiendo de forma determinista la excepcion HTTP 409 Conflict.

#### 42. Trazabilidad e Inmutabilidad Historica mediante Baja Logica (`estado_activo = False`)
- **Causa:** La eliminacion fisica de un proveedor con prendas asociadas en catalogo o recepciones historicas de kardex rompia la integridad referencial de base de datos o dejaba registros huerfanos.
- **Solucion:** Politica estricta de baja logica mediante el flag `estado_activo = False` que cesa inmediatamente la habilitacion para nuevos pedidos pero conserva la totalidad del historico comercial y documental.

#### 43. Captura No Destructiva de Conflictos y Debounce Asincrono en Formularios Reactivos
- **Causa:** La emision de errores de validacion o colision tributaria solia reiniciar los formularios o generar parpadeos en busquedas continuas.
- **Solucion:** Implementacion de retardo *debounce* de 300 ms en el input de busqueda conectado a Signals y contencion no destructiva en Luxury Banners mediante captura en `errorBanner`, preservando integro el estado de los controles en `formCrear` y `formEditar`.

---

## [2.0.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU24 - Gestionar Inventario, Stock y Existencias por Sucursal (Logistica y Existencias Fisicas):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md`](.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU24/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La recepcion de lotes de confeccion, registro de mermas fisicas, transferencias masivas entre boutiques y auditoria contable de kardex son funciones operativas de trastienda y back-office corporativo que residen exclusivamente en el panel web de administracion. La aplicacion movil participa en calidad de consultor pasivo de existencias (`Read-Only`) mediante el endpoint publico `/api/v1/inventario/disponibilidad/{id_variante}`.
- **Validacion Completa:**
  - Backend: 208/208 tests en verde en `pytest` para toda la suite acumulada (17/17 especificos de CU24); modelos ORM en esquema `fashionstore` (`InventarioSucursalORM` y `MovimientoInventarioORM`), migracion Alembic `0005_cu24_inventario_kardex.py` ejecutada en PostgreSQL Neon; restriccion de unicidad compuesta `uq_inventario_sucursal_variante` y `CheckConstraint` de no negatividad (`cantidad_disponible >= 0`); libro de movimientos Kardex inmutable; transaccionalidad ACID con bloqueo exclusivo `with_for_update()` en transferencias inter-sucursales; computo determinista de semaforos de stock (`optimo`, `alerta_baja`, `agotado`); segregacion territorial forzada para rol `encargado_sucursal` bloqueando con HTTP 403 accesos a sedes ajenas; endpoints administrativos bajo `/api/v1/admin/inventario` y vitrina publica `/api/v1/inventario/disponibilidad/{id_variante}`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 168/168 tests en verde en Vitest / Angular CLI (12/12 en `inventario-admin.component.spec.ts`, 9/9 en `inventario-admin.service.spec.ts`, 10/10 en `admin-dashboard.component.spec.ts`); quinta tarjeta boutique en `AdminDashboardComponent` ("Inventario y Existencias") con segmentacion dinamica RBAC (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `InventarioAdminComponent` con `ChangeDetectionStrategy.OnPush` y Signals; barra reactiva de filtros con selector de sucursal fijado y deshabilitado para encargados de boutique; tabla maestra editorial con swatches `#HEX`, miniatura con fallback SVG, desglose de cantidades y badges cromados de umbral; modales reactivos con `NonNullableFormBuilder` (Alta inicial, Ajuste fisico con motivo obligatorio min. 5 caracteres y control de stock, Transferencia inter-sedes excluyendo sede origen y con tope en disponible); panel de Kardex cronologico descendente con variaciones (+/-); y Luxury Banners para captura contextual de errores HTTP 409 y 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 38. Bloqueo Pesimista ACID y Doble Asiento en Transferencias Inter-Sucursales (`with_for_update`)
- **Causa:** En transferencias concurrentes entre boutiques, la lectura no sincronizada del saldo en origen podia ocasionar condiciones de carrera y saldos negativos de inventario.
- **Solucion:** Bloqueo pesimista mediante `with_for_update()` sobre la fila del inventario de origen dentro de una unica transaccion atomica, deduciendo el saldo disponible, acreditando en la sede destino (o creando el registro si no existia) e insertando los dos asientos simetricos de Kardex (`transferencia_salida` y `transferencia_entrada`).

#### 39. Segregacion Territorial Obligatoria y Proteccion RBAC Multinivel
- **Causa:** Personal con rol `encargado_sucursal` podria intentar consultar o mutar existencias de otras tiendas comerciales si el frontend no aplicara restricciones o el backend confiara en los parametros query del cliente.
- **Solucion:** Sobreescritura forzada del parametro de sucursal en el backend validando contra `usuario_sesion.id_sucursal` (HTTP 403 si discrepa), complementada en el frontend mediante bloqueo y deshabilitacion reactiva del selector de sucursal para encargados.

#### 40. Control Reactivo de Umbrales y Validacion de Motivo Obligatorio en Ajustes
- **Causa:** Ajustes manuales por merma o rotura sin justificacion auditable o con cantidades superiores al stock disponible comprometian la fidelidad contable y violaban constraints de base de datos.
- **Solucion:** Validacion Pydantic v2 en `InventarioAjusteIn` exigiendo minimo 5 caracteres no vacios en el motivo, verificacion en servicio de que decrementos no superen `cantidad_disponible` (HTTP 409 `STOCK_INSUFICIENTE`), y reflejo reactivo en interfaz mediante validadores reactivos y Luxury Banners sin perdida de datos.

---
## [1.9.0] - 2026-09-21

### Auditoría Transversal y Corrección de Defectos de Contrato

Diagnóstico completo de `Ec-backend`, `Ec-frontend` y `Ec-mobile` contra la documentación de
`.agents/` y `.specs/`. El hallazgo estructural es que **las tres suites reportaban verde mientras
CU12 (Reservar Prendas) era imposible de completar desde la aplicación móvil**: el backend mockea
la sesión de base de datos en sus tests y el móvil construía sus DTO con constructores sin
ejercitar nunca `fromJson`, de modo que ningún desajuste de nombres de campo era observable.

- **Blindaje de las pruebas contra el contrato real:** los mocks de reserva del web y del móvil se
  reescribieron a partir de payloads literales de `POST /api/v1/reservas`, y se añadió un grupo de
  pruebas de contrato en `test/pantalla_producto_detalle_test.dart` que valida `toJson`/`fromJson`
  frente a los esquemas Pydantic. Se añadieron `registro.component.spec.ts` y una prueba de
  supervivencia del listener de sesión en `widget_test.dart`, los dos archivos con más cambio de
  comportamiento y sin cobertura previa.
- **Reconciliación documental:** actualizada la directriz Hub-and-Spoke (declaraba CU05 pendiente y
  CU36 «en migración de layout en Web»), cerrados los gates de aprobación de
  `change-detalle-producto-reservas.md` y `change-landing-page-publica.md` (afirmaban que no se
  había generado código con 18 y 13 tareas ya marcadas), resuelto el conflicto de rutas de
  `/inicio` y `/colecciones` a favor del enrutamiento vigente, y marcado el Bloque 3 (Mobile) de
  CU07/CU08/CU09/CU12 según el estado real del repositorio.
- **Deriva de esquema entre el ORM y PostgreSQL (2026-09-22):** una segunda pasada, motivada por
  errores HTTP 500 reproducidos en la aplicación en ejecución, reveló que tres modelos mapeaban
  columnas inexistentes en la base de datos real. La trampa de fondo es que
  `alembic/versions/0001_base_ddl.py` **no refleja el esquema desplegado en Neon**: ORM y migración
  coincidían entre sí y discrepaban de la realidad. Se alinearon los modelos con la base de datos
  —sin tocar el esquema— y se añadió `Ec-backend/tests/test_esquema_bd.py` como guardia permanente.
- **Verificación:** `pytest` 123/123 (incluye la guardia de esquema contra Neon) · `ng test`
  108/108 y `ng build` 0 errores · `dart analyze` 0 issues y `flutter test` 104/104. Además,
  verificación end-to-end contra la base real: `/api/v1/catalogo`, `/api/v1/colecciones/activas`,
  `/api/v1/catalogo/filtros-disponibles`, `/api/v1/catalogo/recomendaciones/personalizadas`,
  `/api/v1/sucursales/activas` y `/api/v1/productos` devuelven HTTP 200 con datos de Neon.

### Deuda Técnica Registrada
- **`alembic/versions/0001_base_ddl.py` no describe la base de datos real.** Declara `activa`,
  `activo` y `nit` donde PostgreSQL tiene `estado_activo` y `nit_rut`, y omite columnas que sí
  existen (`actualizado_en`, `anio`, `codigo_cupon`, `alcance`, `limite_usos`, `direccion`,
  `ciudad`, `rubro`, entre otras). Mientras siga así, cualquiera que consulte la migración para
  saber cómo es una tabla obtendrá la respuesta incorrecta, y `alembic revision --autogenerate`
  propondrá cambios destructivos. Reconciliarla implica una decisión sobre el esquema y queda
  pendiente de autorización explícita.

### Registro de Errores Corregidos y Soluciones Aplicadas
34. **HTTP 500 en Catálogo, Búsqueda y Colecciones por Deriva entre el ORM y el Esquema Real de PostgreSQL**:
    - *Causa:* `TemporadaORM`, `PromocionORM` y `ProveedorORM` mapeaban columnas llamadas `activa`, `activo` y `nit`, mientras que en la base de datos de Neon esas columnas se llaman `estado_activo` y `nit_rut`. SQLAlchemy emitía `SELECT temporadas.activa …` y PostgreSQL respondía `UndefinedColumn`, tumbando `GET /api/v1/catalogo` (vía `PromocionORM`), `GET /api/v1/catalogo/filtros-disponibles` y `GET /api/v1/colecciones/activas` (ambos vía `TemporadaORM`).
    - *Agravante que impidió diagnosticarlo:* la migración `alembic/versions/0001_base_ddl.py` **no describe la base de datos realmente desplegada** —declara los nombres antiguos—, de modo que ORM y migración se confirmaban mutuamente mientras producción fallaba. Sumado a que todos los tests mockean la sesión, no existía ningún punto del proyecto donde el desajuste fuese observable.
    - *Solución:* Se pasó el nombre real como primer argumento de `mapped_column("estado_activo", …)` / `mapped_column("nit_rut", …)` en `Ec-backend/app/modules/catalogo/modelos.py`, conservando los atributos de dominio (`activa`, `activo`, `nit`) para no alterar ninguna consulta. No se modificó el esquema de la base de datos. Se añadió `tests/test_esquema_bd.py`, que contrasta `Base.metadata` contra `information_schema` y falla ante cualquier columna mapeada inexistente.
    - *Nota de corrección:* una revisión anterior de este mismo changelog atribuyó el fallo a «un renombrado a `nit_rut`/`estado_activo` sin migración de respaldo» y lo revirtió. El diagnóstico estaba invertido: esos eran los nombres correctos y el revert reintrodujo el error. La fuente de verdad es la base de datos desplegada, no la migración.
35. **HTTP 500 al Reservar la Misma Variante Dos Veces en una Cita**:
    - *Causa:* El servicio de CU12 recorría `payload.items` sin consolidar, descontando el inventario tantas veces como líneas repetidas e insertando detalles duplicados que violaban el `UNIQUE (id_reserva, id_variante)` de `reserva_detalle`. El `IntegrityError` resultante no pertenece al árbol `DomainError`, por lo que escapaba del manejador de errores como un 500. La restricción tampoco estaba declarada en el ORM.
    - *Solución:* Consolidación de líneas por `id_variante` antes de tocar inventario, validación del tope de 5 unidades sobre el total agrupado (`CANTIDAD_MAXIMA_EXCEDIDA`, HTTP 400) y declaración del `UniqueConstraint` en `ReservaDetalleORM`.
36. **HTTP 500 Latente por Consulta de Inventario sobre una Clave No Única**:
    - *Causa:* El repositorio de reservas resolvía el inventario con `scalar_one_or_none()` filtrando por `(id_variante, id_sucursal)`, pero la clave única real de `inventario_sucursal` incluye `id_temporada`. Bastaba con que una variante tuviera existencias de una segunda temporada en la misma boutique para que toda reserva de esa prenda lanzara `MultipleResultsFound`. Permanecía latente solo porque el seed siembra una única temporada.
    - *Solución:* Selección determinista de la fila que cubre la cantidad solicitada (temporada más reciente primero), con fallback a la de mayor stock para que el mensaje de existencias insuficientes informe la disponibilidad real.
37. **HTTP 422 Sistemático al Reservar Cita desde la Aplicación Móvil**:
    - *Causa:* `ReservaCrearInDto.toJson` serializaba `fecha_reserva`, `notas_cliente` y `lineas`, mientras que `ReservaCrearIn` exige `fecha_hora_atencion`, `observacion` e `items` (este último obligatorio). Tres de las cuatro claves eran incorrectas, por lo que CU12 nunca llegó a funcionar en móvil. El DTO de respuesta presentaba el mismo problema, de modo que todos los campos caían en sus valores por defecto y el diálogo de confirmación mostraba datos inventados.
    - *Solución:* Alineación campo a campo de la petición y la respuesta con los esquemas Pydantic, envío explícito de `canal_origen: 'movil'` y derivación de `totalPrendas` a partir de las líneas devueltas.
38. **Listener de Sesión Móvil Autodesactivado tras el Login**:
    - *Causa:* La suscripción a `SesionManager` vivía en el widget montado como ruta `home`. Al navegar al hub mediante `pushReplacement` desde el contexto de ese mismo estado, la ruta se reemplazaba a sí misma, el estado se desmontaba y `dispose()` cancelaba la suscripción. El auto-redirect por HTTP 401 solo escuchaba mientras el usuario permanecía en el login —justo cuando un 401 no puede producirse— y, al cerrar sesión, los callbacks del nuevo login apuntaban a un estado destruido, de modo que volver a autenticarse dejaba la aplicación en el formulario sin mensaje alguno.
    - *Solución:* Reestructuración de `main.dart` para que la gestión de sesión resida por encima del `Navigator`, actuando mediante `navigatorKey` y `scaffoldMessengerKey` globales, y liberación del flag anti-duplicados de `SesionManager` en cada retorno al login.
39. **Ficha de Producto Móvil sin Fotografía Principal ni Galería Multiángulo**:
    - *Causa:* `ProductoDetalleDto.fromJson` leía `imagen_url` y `galeria_angulos`, mientras que `ProductoDetalleOut` emite `imagen_principal` y `galeria`. Ambos resolvían a `null` y lista vacía.
    - *Solución:* Corrección puntual de ambas claves, preservando `imagen_url` en los DTO de listado, donde sí es el nombre correcto.
40. **HTTP 401 al Reservar desde las Pestañas Catálogo y Buscar**:
    - *Causa:* `PantallaCatalogo` y `PantallaBuscarProductos` no declaraban campo `token` ni lo propagaban a `PantallaProductoDetalle`, por lo que la petición de reserva salía sin cabecera `Authorization` aun con el usuario autenticado.
    - *Solución:* Añadido el campo `token` a ambas pantallas y a las de colecciones, propagado desde `PantallaPrincipalHub`.
41. **Confirmación de Reserva Web con Campos en Blanco**:
    - *Causa:* La interfaz `ReservaConfirmacion` declaraba `codigo_confirmacion`, `total_prendas` y `mensaje_cortesia`, campos que `ReservaCreadaOut` no envía. El modal imprimía «CÓDIGO: » sin contenido y la notificación mostraba `Cita confirmada (undefined)`. El spec mockeaba la interfaz del propio frontend, dando por válido un contrato que el servidor nunca produce.
    - *Solución:* Modelo alineado con `ReservaCreadaOut`, total derivado de las líneas mediante `computed()`, y spec reescrito sobre un payload real del backend.
42. **Sesión Anónima tras Completar el Registro en Web**:
    - *Causa:* `RegistroComponent` persistía la sesión con claves propias (`fs_token_acceso`, `fs_usuario`) que ningún servicio consulta, ya que `LoginService`, `PerfilService` e `InicioService` leen `fashionstore_token` y `fashionstore_user`. El usuario recién registrado quedaba sin autenticar, el interceptor no adjuntaba el token y `/perfil` rebotaba a `/login`.
    - *Solución:* El registro delega la persistencia en el nuevo método `LoginService.establecerSesion()`, dejando las claves de almacenamiento bajo un único propietario.
43. **Todo Fallo Interno del Backend Llegaba al Navegador como «Failed to fetch»**:
    - *Causa:* Ante una excepción no controlada, la respuesta 500 la generaba el `ServerErrorMiddleware` de Starlette, que envuelve a todos los middlewares de usuario, incluido el `CORSMiddleware`. La respuesta salía sin `Access-Control-Allow-Origin` y el navegador la descartaba, de modo que la web y la app Flutter mostraban un error de red genérico en lugar del error real. Añadir un `@app.exception_handler(Exception)` no lo resuelve: Starlette monta ese manejador precisamente en el `ServerErrorMiddleware`.
    - *Solución:* Middleware `capturar_errores_no_controlados` registrado **antes** del `CORSMiddleware` (`add_middleware` antepone, así que el primero declarado queda por dentro), que devuelve un 500 JSON estructurado y atraviesa CORS. El traceback se registra en el log del servidor y nunca se envía al cliente. Se conserva el manejador de excepción externo como último recurso para fallos del propio CORSMiddleware.
44. **Landing Page Pública Inalcanzable en la URL Raíz**:
    - *Causa:* La ruta `{ path: '', component: MainLayoutComponent, children: [...] }` introducida con CU05 quedó declarada por delante de `{ path: '', loadComponent: landing, pathMatch: 'full' }`. Angular resuelve las rutas en orden: la URL raíz entraba en el layout y, al no existir ningún hijo con `path: ''`, la landing dejaba de mostrarse. El proyecto seguía compilando sin errores.
    - *Solución:* La landing se declara primero en `app.routes.ts`; su `pathMatch: 'full'` garantiza que solo capture la URL vacía exacta. Se añadió además la ruta comodín `{ path: '**' }` que faltaba —sin ella, cualquier URL desconocida producía un `NG04002` y una pantalla en blanco, agravado porque `vercel.json` reescribe todo a `index.html`— y el guard `src/app/app.routes.spec.ts`, que navega a `/` y verifica el orden de declaración.

## [1.8.0] - 2026-09-21

### Promoción a Baseline Permanente
- **CU05 - Consultar Catálogo de Productos (Colección General, Atelier & Sastrería Femenina):** Promovido oficialmente a especificación técnica permanente del sistema en [`.specs/modules/catalogo_productos/CU05-consultar-catalogo.md`](.specs/modules/catalogo_productos/CU05-consultar-catalogo.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU05-consultar-catalogo/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa en los 3 Bloques:**
  - **Backend (`Ec-backend`):** 107/107 tests en verde en `pytest` (7/7 específicos de catálogo general); modelos ORM `ProductoORM`, `CategoriaORM`, `VarianteProductoORM`, `PromocionORM` y `PromocionProductoORM`; endpoint `GET /api/v1/catalogo` con paginación, filtros de categoría y ordenamiento; cálculo agregado de conteo por categoría sin queries N+1; cálculo dinámico de promociones vigentes y asignación de subtítulos y badges de alta costura.
  - **Frontend Web (`Ec-frontend`):** 86/86 tests pasando en Vitest / Angular CLI (8/8 de catálogo), compilación de producción limpia (`npm run build`, 0 errores); vista `CatalogoComponent` implementada como Pantalla Raíz (Hub) bajo `MainLayoutComponent` (navbar superior visible, sin botón `← Volver`, pestaña activa destacada); carrusel horizontal de chips con unidades; grilla editorial de 4 columnas con selector de densidad (4 vs 2 columnas); tarjetas con badges de atelier, tallas, dots de color y wishlist; paginación editorial y bloque de Conserjería Privada de Fitting.
  - **Mobile Multiplataforma (`Ec-mobile`):** 86/86 tests pasando en `flutter test` (9/9 específicos de CU05), 0 incidencias en `flutter analyze`; `PantallaCatalogo` integrada en el Índice 2 (`Catálogo`) de `PantallaPrincipalHub` con `BottomNavigationBar` visible y `AppBar` con `automaticallyImplyLeading: false`; carrusel horizontal de chips con conteo; selector de 1 o 2 columnas; cuadrícula con `childAspectRatio: 0.58` libre de desbordamientos `RenderFlex`; paginación con botón expansor y sello institucional "ATELIER FLAGSHIP MADRID · PARÍS".

### Registro de Errores Corregidos y Soluciones Aplicadas
31. **Desbordamiento de RenderFlex y Huecos Excesivos en Tarjetas Móviles de Catálogo**:
    - *Causa:* En pantallas móviles de resolución estándar, la proporción de aspecto 0.50 dejaba un espacio inferior desmedido, mientras que proporciones mayores a 0.65 comprimían el bloque de tallas provocando overflow vertical en tarjetas con títulos de 2 líneas.
    - *Solución:* Calibración precisa a `childAspectRatio: 0.58` en `PantallaCatalogo`, asegurando un ajuste armónico de imagen 3:4, badges, títulos, precio, tallas y selector cromático con cero desbordamientos.
32. **Regresión en Expectativa de Placeholder en Suite de Pruebas de Navegación Móvil (`pantalla_principal_hub_test.dart`)**:
    - *Causa:* El test de navegación original comprobaba la presencia de `PantallaCatalogoPlaceholder` en el índice 2, fallando tras la sustitución por la implementación real de CU05.
    - *Solución:* Actualización del test para validar la presencia de `PantallaCatalogo`, garantizando que la navegación bidireccional entre las 4 pestañas raíz mantenga el 100% de aprobación.
33. **Alineación con Linter Dart 3 (`unnecessary_underscores` y `dangling_library_doc_comments`)**:
    - *Causa:* El uso de identificadores múltiples no utilizados (`__`, `___`) en callbacks de constructores y comentarios de librería no vinculados activaron advertencias en `flutter analyze`.
    - *Solución:* Sustitución por comodines simples `_` compatibles con Dart 3 y enlace de la directiva `library;` en modelos DTO, logrando 0 issues en el análisis estático.

## [1.7.0] - 2026-09-21

### Promoción a Baseline Permanente
- **CU36 - Consultar Colecciones (Colecciones Activas y Exploración de Prendas por Colección):** Promovido oficialmente a especificación técnica permanente del sistema en [`.specs/modules/catalogo_productos/CU36-consultar-colecciones.md`](.specs/modules/catalogo_productos/CU36-consultar-colecciones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU36-consultar-colecciones/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa en los 3 Bloques:**
  - **Backend (`Ec-backend`):** 100/100 tests en verde en `pytest` (17/17 específicos de colecciones y prendas); modelos ORM `ColeccionORM`, `TemporadaORM`, `ProductoORM`; endpoints `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id}/productos` (con alias `/api/v1/catalogo/colecciones/...`); resolución de temporada comercial activa por rango de fechas (`CURRENT_DATE`) y fallback a `activa = true`; cálculo dinámico de `precio_desde` (`MIN(precio_base)`) y `total_prendas` sin queries N+1.
  - **Frontend Web (`Ec-frontend`):** 78/78 tests pasando en Vitest / Angular CLI, compilación de producción limpia (`npm run build`, 0 errores); vistas `ColeccionesComponent` y `ColeccionDetalleComponent` estructuradas como pantallas secundarias fuera de `MainLayoutComponent` (sin barra de navegación superior institucional, maximizando inmersión editorial, con botón de retorno obligatorio `← Volver` hacia `/inicio` o `/colecciones`); card completa de "Otras colecciones" interactiva como botón de enlace.
  - **Mobile Multiplataforma (`Ec-mobile`):** 77/77 tests pasando en `flutter test`, 0 incidencias en `flutter analyze`; vistas `ColeccionesScreen` y `DetalleColeccionScreen` ejecutadas a pantalla completa sin `BottomNavigationBar` y con `leading: BackButton()`; calibración visual de tarjetas con `childAspectRatio: 0.65`, contenedores elásticos en `Expanded` y fotos en `Positioned.fill` (eliminando espacios blancos excesivos y previniendo `RenderFlex overflowed`); deserialización tolerante de tipos `num` y `Decimal` (`"310.00"`); tipografía corporativa unificada en `Outfit`; y orquestación del Hub raíz con `PantallaPrincipalHub` (`IndexedStack` de 4 posiciones: Inicio, Buscar, Catálogo en blanco para CU05, Perfil) con saludo dinámico para el usuario autenticado (ej. "Joaquinita Chumacero").

### Registro de Errores Corregidos y Soluciones Aplicadas
26. **Espacio en Blanco Excesivo y Desproporción Fotográfica en Tarjetas Móviles (`ColeccionesScreen`)**:
    - *Causa:* El contenedor de la tarjeta forzaba una altura fija con márgenes rígidos que dejaban un área blanca desproporcionada debajo de la fotografía de la colección.
    - *Solución:* Ajuste de `childAspectRatio: 0.65`, integración de imagen fotográfica en `Expanded` con `Positioned.fill` y `fit: BoxFit.cover`, logrando un encuadre editorial compacto y equilibrado.
27. **Discrepancia Tipográfica en Tarjetas de Colección Móviles**:
    - *Causa:* Ciertas etiquetas y badges utilizaban estilos o fuentes por defecto de Flutter sin aplicar los tokens normativos del Design System.
    - *Solución:* Unificación tipográfica atómica bajo la familia `Outfit`, tracking normativo (`letterSpacing: 0.8-1.1`), pesos `FontWeight.w600/w700` y paleta Obsidian/Camel de `fashionstore-tokens.md`.
28. **Incompatibilidad de Tipos en Deserialización de Precios Monetarios (`TypeError: String is not a subtype of num`)**:
    - *Causa:* FastAPI serializa campos `Decimal` de SQLAlchemy como cadenas JSON (ej. `"310.00"`), produciendo un fallo de conversión directa a `num` en Dart.
    - *Solución:* Implementación de parsing tolerante y robusto mediante `double.tryParse(json['precio_base'].toString()) ?? 0.0`.
29. **Navegación Circular y Corrupción de Pila entre Pestañas Raíz en Flutter**:
    - *Causa:* Cada pantalla (`Inicio`, `Buscar`, `Perfil`) creaba su propio `Scaffold` con `BottomNavigationBar` local y utilizaba `Navigator.push` entre sí, provocando apilamiento de rutas y callbacks desalineados (ej. pulsar Inicio desde Perfil solo ejecutaba un `setState` local).
    - *Solución:* Creación de `PantallaPrincipalHub` con un único `Scaffold` raíz e `IndexedStack` de 4 pestañas (`Inicio`, `Buscar`, `Catálogo`, `Perfil`), permitiendo alternar instantáneamente entre vistas por índice sin duplicar rutas y reservando `Navigator.push` exclusivamente para pantallas secundarias como `ColeccionesScreen`.
30. **Nombre de Usuario Estático en Saludo de Bienvenida en Móvil**:
    - *Causa:* `InicioBloc` inicializaba con `'Ana Valenzuela'` quemado y `main.dart` no transfería los datos del usuario autenticado tras el inicio de sesión.
    - *Solución:* Propagación de `LoginRespuestaDto` desde `PantallaLogin` hacia `PantallaPrincipalHub` y `PantallaInicio`, y consulta asíncrona de perfil con el token activo, mostrando dinámicamente el nombre real (ej. "Joaquinita Chumacero").

## [1.6.0] - 2026-09-21

### Directriz Arquitectónica Global de Navegación y Jerarquía de Vistas (Hub-and-Spoke)
- **Definición Canónica:** Establecimiento formal de la directriz en [`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](.specs/architecture/directriz-navegacion-hub-and-spoke.md).
- **Las 4 Pantallas Principales (Raíz / Hub):** Únicamente `/inicio`, `/buscar`, `/catalogo` y `/perfil` disponen de barra de navegación principal (navbar Web / BottomNavigationBar Mobile) permanentemente visible. Prohibido incluir botón de retroceso (`← Volver`).
- **Pantallas Secundarias (Hojas / Spoke):** Cualquier caso de uso derivado (incluyendo `CU36 Colecciones` y su vista de detalle) debe ocultar la barra de navegación principal y disponer de un botón de regreso obligatorio (`← Volver` / `leading: BackButton()`) hacia la pantalla previa desde la que se accedió.
- **Alineación de CU36:** Actualizadas las especificaciones activas de `CU36` (`spec.md`, `plan.md`, `tasks.md`, `checkpoint.md`, `change-consultar-colecciones.md`) para cumplir estrictamente con el patrón Hub-and-Spoke.

## [1.5.0] - 2026-09-20

### Promoción a Baseline Permanente
- **CU06 - Buscar y Filtrar Productos (Catálogo Omnicanal de Alta Costura Femenina):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/catalogo_productos/CU06-buscar-filtrar-productos.md`](.specs/modules/catalogo_productos/CU06-buscar-filtrar-productos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU06-buscar-filtrar-productos/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 83/83 tests en verde en `pytest` para toda la suite acumulada (20/20 específicos de catálogo); modelos ORM del catálogo (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`), motor de búsqueda con normalización sin tildes/mayúsculas, expansión de singular/plural, búsqueda por palabras sueltas multicriterio, filtros 100% opcionales y endpoints `GET /api/v1/productos`, `GET /api/v1/catalogo/filtros-disponibles` y `POST /api/v1/catalogo/buscar`.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, 0 errores), 41/41 tests pasando en Vitest / Angular CLI (17/17 de catálogo), componente `BuscarProductosComponent` con confirmación diferida mediante botón `BUSCAR` y `Enter`, vaciado automático de input, badge editorial dismissible, paleta de 16 colores textiles, tipografía Outfit estandarizada y alineación pixel-perfect unificada con `/perfil` mediante `scrollbar-gutter: stable` y `max-w-[1440px] px-6`.
  - Mobile: 56/56 tests en verde en `flutter test` (14 de catálogo), 0 incidencias en `flutter analyze`, `CatalogoBloc` con estados sellados inmutables, `PantallaBuscarProductos` con carrusel horizontal de temporadas, filtros refinados con tallas cuadradas y 16 tonalidades, `GridView` de 2 columnas con tarjetas de lujo (`+ CESTA`, badges editoriales, favoritos), modal BottomSheet de rango y orden, y conexión fluida en BottomNavigationBar.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 21. Normalización Morfológica y Coincidencia Flexible en Búsqueda Multicriterio (`Términos sinónimos y palabras sueltas`)
- **Causa:** Las consultas de búsqueda requerían coincidencia exacta o fallaban al buscar categorías directas ("vestido" vs "vestidos", "pantalón" con o sin tilde).
- **Solución:** Implementación de `_normalizar_texto` (remoción de acentos/diacríticos y minúsculas), expansión semántica `_expandir_termino` (singular/plural de prendas y sinónimos de moda) y consultas combinadas con `or_` sobre nombre, descripción, categoría, colección, temporada y color sin error 500.

#### 22. Inconsistencia de Color y Modelo en Catálogo Femenino de Alta Costura
- **Causa:** El producto "Vestido plisado seda" estaba incorrectamente listado como mármol, y existía una fotografía con modelo masculino en el catálogo de una firma exclusivamente orientada a moda femenina.
- **Solución:** Corrección de semilla y registros a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ`, sustitución de imágenes masculinas por modelos femeninas de alta costura, y expansión de la paleta textil a 16 tonalidades de confección real.

#### 23. Confirmación Explícita de Búsqueda y Modo Borrador Diferido (Web y Mobile)
- **Causa:** Los filtros o la escritura en el campo de texto ejecutaban peticiones tempranas innecesarias o generaban discrepancias si el usuario modificaba varios filtros a la vez.
- **Solución:** Implementación de modo borrador diferido en Angular y Flutter, botón explícito `BUSCAR` + tecla `Enter`, vaciado automático del input tras la confirmación y almacenamiento del término activo en badge editorial dismissible.

#### 24. Desalineación Visual de Cabecera y Salto Horizontal entre Páginas Web
- **Causa:** `/perfil` utilizaba `max-w-7xl` (1280px) mientras que `/buscar` utilizaba `max-w-[1440px] px-6`, y la aparición/desaparición de la barra de scroll vertical producía un brinco horizontal de 15px en la barra institucional y avatar.
- **Solución:** Homologación estricta a `max-w-[1440px] px-6` en `perfil.component.html` y adición de la directiva `scrollbar-gutter: stable;` en `styles.scss`, garantizando estabilidad geométrica absoluta.

#### 25. Tipografía No Conforme en Titular "Visto recientemente"
- **Causa:** Se empleaba tipografía cursiva serif en "Visto recientemente", desalineada con el Design System general.
- **Solución:** Sustitución por la tipografía institucional `Outfit` (`font-sans font-semibold tracking-tight`), unificando la identidad visual corporativa en Desktop y Mobile.

---

## [1.4.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU33 - Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU33-recuperar-acceso.md`](.specs/modules/autenticacion_seguridad/CU33-recuperar-acceso.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU33-recuperar-acceso/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 63/63 tests en verde en `pytest` para toda la suite acumulada; modelo relacional `CodigoRecuperacionORM` en esquema `fashionstore` (migración Alembic `0002_codigos_recuperacion.py`), persistencia segura mediante digest SHA-256 (nunca texto plano), política anti-enumeración de usuarios uniforme con `200 OK`, rate limiting de 60s y hashing de clave con **Argon2id**.
  - Servicio SMTP y Entregabilidad: Integración asíncrona mediante `asyncio.to_thread` con Gmail SMTP (`smtp.gmail.com:587` STARTTLS); cabeceras RFC 5322 (`Message-ID`, `Date`) y RFC 3834 (`Auto-Submitted: auto-generated`), eliminando clasificación en spam y garantizando entrada directa a Inbox.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle en 3.7s), 17/17 tests pasando en Vitest / Angular CLI, fidelidad visual exacta con la captura Desktop (badge FS, medidor dinámico de 3 barras horizontales, timer reactivo de reenvío de 60s y botón `ACTUALIZAR Y ACCEDER →`).
  - Mobile: 42/42 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, `RecuperarPasswordBloc` con estados sellados, diseño fiel a la captura Mobile (tarjeta, monograma FS, 3 barras de fuerza dinámicas, escudo inferior) y conexión en login.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 18. Rechazo de Autenticación SMTP por Contraseña Estándar de Gmail (`535 5.7.8 BadCredentials`)
- **Causa:** Google descontinuó el acceso por contraseña básica en junio de 2022 y requiere Contraseña de Aplicación de 16 caracteres generada tras activar 2FA.
- **Solución:** Parametrización en `.env` y `Settings` con contraseña de aplicación de 16 caracteres y diagnóstico activo con `logging.basicConfig(level=logging.INFO)` en `main.py`.

#### 19. Entregabilidad de Correo en Bandeja de Spam por Cabeceras Faltantes y Términos de Phishing
- **Causa:** Falta de cabeceras RFC 5322 (`Message-ID`, `Date`), falta de RFC 3834 (`Auto-Submitted: auto-generated`), codificación sin `Header(..., 'utf-8')` y términos de riesgo heurístico en la plantilla ("Seguridad Criptográfica 256-Bit SSL", emojis en celdas).
- **Solución:** Generación de `Message-ID` y `Date` RFC, adición de metadatos transaccionales y depuración de la plantilla HTML/Text, logrando entrada garantizada en la Bandeja Principal (Inbox).

#### 20. Desbordamiento de Rótulo en Pantallas Móviles Pequeñas (`RenderFlex overflowed`)
- **Causa:** En anchos reducidos, el rótulo de 6 dígitos y el botón de reenvío en la misma fila desbordaban el ancho disponible.
- **Solución:** Aplicación de `Flexible(child: Text(..., overflow: TextOverflow.ellipsis))` para adaptación fluida en cualquier resolución.

---

## [1.3.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU03 - Cerrar Sesión (Logout / Revocación Omnicanal de Token y Purga Segura):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU03-cerrar-sesion.md`](.specs/modules/autenticacion_seguridad/CU03-cerrar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU03-cerrar-sesion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 52/52 tests en verde en `pytest` para toda la suite acumulada; implementación de `TokenBlacklistService` en memoria con indexación SHA-256 y expiración automática; rechazo garantizado con `401 Unauthorized` (`code="TOKEN_REVOCADO"`) ante reuso de token en endpoints protegidos.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle completado en 4.22s), 10/10 tests pasando en Vitest / Angular CLI, purga integral y resiliente de `localStorage` y `sessionStorage` en `finalize()` de `LoginService`, reseteo de Signal reactivo `usuarioActual.set(null)` y etiqueta unificada estricta `CERRAR SESIÓN`.
  - Mobile: 30/30 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, reinicio de `LoginBloc`, blindaje de pila de navegación con `pushAndRemoveUntil(..., (route) => false)` y etiqueta de botón invariable `CERRAR SESIÓN`.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 15. Consistencia Visual y Estabilidad de Texto en Botón de Salida (`CERRAR SESIÓN`)
- **Causa:** Se proponían rótulos extendidos ("CERRAR SESIÓN SEGURA") o textos dinámicos durante el proceso de carga.
- **Solución:** Fijación del texto unificado como `CERRAR SESIÓN` en Frontend y Mobile por especificación estricta de experiencia de usuario.

#### 16. Resolución de Rutas Relativas Profundas en Widgets de Flutter (`Package Imports`)
- **Causa:** Importaciones relativas (`../../cu02_iniciar_sesion/...`) en `pantalla_perfil.dart` fallaban al compilar desde tests debido a la profundidad de tres niveles de subdirectorios en `presentacion/pantallas`.
- **Solución:** Migración a importaciones canónicas de paquete (`import 'package:ec_mobile/src/...'`), garantizando resolución universal en desarrollo y pruebas.

#### 17. Contrato de Interfaz de Repositorio en Mocks de Test (`cerrarSesion`)
- **Causa:** La adición de `cerrarSesion(String token)` a la interfaz abstracta `LoginRepositorio` rompía mocks no actualizados en suites de test de widgets (`MockLoginRepositorio`).
- **Solución:** Implementación del método en todos los mocks de prueba (`test/pantalla_login_test.dart`, etc.), restableciendo 100% de tests en verde.

---

## [1.2.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU04 - Gestionar Perfil del Cliente (Consulta, Actualización y Panel Mi Cuenta):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU04-gestionar-perfil.md`](.specs/modules/autenticacion_seguridad/CU04-gestionar-perfil.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU04-gestionar-perfil/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 45/45 tests en verde en `pytest` para toda la suite acumulada; verificación en vivo de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` sobre Neon PostgreSQL Serverless.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 tests pasando en `ng test`, refresco instantáneo de estado bajo `OnPush` con `ChangeDetectorRef` y sincronización con `sessionStorage`/`localStorage`.
  - Mobile: 28/28 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, inyección de token real desde login y actualización interactiva en tiempo real.
  - Verificación en Vivo: Probado y validado en vivo por el usuario en web y móvil.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 11. Expiración Temprana de Token JWT (`401 Unauthorized: Signature has expired`)
- **Causa:** El tiempo de expiración por defecto de tokens de acceso (`ACCESS_TOKEN_EXPIRE_MINUTES`) era de 60 minutos (o 15 minutos en configuración base), causando desconexiones silenciosas durante pruebas extendidas y edición de perfil.
- **Solución:** Se amplió `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24 horas) en `app/core/config.py` y `.env` para asegurar persistencia durante desarrollo y depuración.

#### 12. Exclusión de Selector de Género por Modelo de Marca de Alta Costura Femenina
- **Causa:** Se incluía selector de género en los formularios de edición de perfil, lo cual no aplica para una firma exclusivamente orientada a indumentaria femenina (ni para cuentas de empleados).
- **Solución:** Retiro completo del selector de género en el HTML/TypeScript de Angular (`PerfilComponent`) y en el bottom sheet modal de Flutter (`PantallaPerfil`), manteniendo en el backend compatibilidad opcional sin forzar su uso.

#### 13. Falta de Persistencia y Refresco Inmediato de Perfil en Frontend Web
- **Causa:** Los cambios confirmados en el modal de edición no actualizaban el storage local de sesión (`fashionstore_user`) y la estrategia `OnPush` no redibujaba los datos sin una recarga manual de página.
- **Solución:** Implementación de `sincronizarSesionStorage(perfilActualizado)` e inyección de `ChangeDetectorRef` con llamada a `this.cdr.markForCheck()` tras la respuesta del backend.

#### 14. Discrepancia de Datos de Cuenta y Persistencia en App Móvil
- **Causa:** `PantallaPerfil` consumía datos con un token mock por defecto en vez del token dinámico emitido por el login en Neon PostgreSQL, mostrando datos de prueba no coincidentes con el usuario real.
- **Solución:** Conexión del callback `alCompletarLoginConToken` en `PantallaLogin` de Flutter hacia `PantallaPerfil(token: token)` y emisión reactiva inmediata de `PerfilCargadoState` en `PerfilBloc` tras el guardado atómico en PostgreSQL.

---

## [1.1.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU02 - Iniciar Sesión (Login / Autenticación Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU02-iniciar-sesion.md`](.specs/modules/autenticacion_seguridad/CU02-iniciar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU02-iniciar-sesion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 28/28 tests en verde en `pytest` y verificación en vivo de autenticación (códigos 200, 401) y actualización atómica de `ultimo_acceso` en Neon PostgreSQL.
  - Frontend Web: Compilación limpia en 5.4s con Angular CLI (`npm run build`) y comunicación proxy verificada (`/api/v1/autenticacion/login`).
  - Mobile: 19/19 tests en verde en `flutter test` y 0 incidencias en `flutter analyze`.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 8. Error: `OPTIONS 400 Bad Request` y `ClientException: Failed to fetch` en Flutter Web
- **Causa:** Al ejecutar Flutter en navegador (`flutter run -d edge` o `chrome`), Flutter Web asigna un puerto efímero dinámico en desarrollo (ej. `http://localhost:50870`). Starlette `CORSMiddleware` evaluaba el origen únicamente contra una lista estática `settings.CORS_ORIGINS`. Al no coincidir el puerto, Starlette rechazaba el preflight `OPTIONS` con `400 Bad Request` (`Disallowed CORS origin`), provocando que el navegador bloqueara la petición `POST`.
- **Solución:** Se implementó `CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"` en `app/core/config.py` y se configuró `allow_origin_regex` en `CORSMiddleware` en `app/main.py` y `Ec-backend/.env`, admitiendo cualquier puerto de depuración local conservando el aislamiento estricto en producción.

#### 9. RenderFlex Overflows en `PantallaLogin` (Flutter)
- **Causa:** En resoluciones móviles estrechas, la fila de contraseña (`CONTRASEÑA` y `¿Olvidaste tu contraseña?`) y la fila de checkbox (`Recordar en este dispositivo`) provocaban desbordamientos horizontales por rigidez de constraints sin `Flexible`/`Expanded`.
- **Solución:** Se envolvieron los textos y componentes en `Flexible` y `Expanded` con manejo de elipsis en textos de seguridad, eliminando desbordamientos en cualquier ancho de pantalla.

#### 10. Flujo y Enrutamiento Bidireccional en Aplicación Móvil
- **Causa:** La aplicación móvil iniciaba en `PantallaRegistro` y el enlace inferior no permitía acceder a la pantalla de login cuando ésta no estaba en la pila de navegación.
- **Solución:** Se estableció `home: const PantallaLogin()` en `Ec-mobile/lib/main.dart` como punto de entrada primario y se configuró un enrutamiento bidireccional inteligente en `PantallaRegistro` que evalúa `Navigator.canPop(context)` para hacer `pop()` o `pushReplacement(...)` hacia `PantallaLogin`.

---

## [1.0.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU01 - Registrarse (Alta Costura & Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU01-registrarse.md`](.specs/modules/autenticacion_seguridad/CU01-registrarse.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU01-autenticacion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 15/15 tests en verde en `Ec-backend`, 7/7 tests unitarios en `Ec-mobile`, build exitoso en `Ec-frontend`, y esquema PostgreSQL migrado a la base de datos en la nube (Neon Serverless).

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 1. Error: `ModuleNotFoundError: No module named 'core'`
- **Causa:** Tras reorganizar los archivos dentro del paquete `app/` (`app/core`, `app/modules`), las rutas de importación directas quedaron desalineadas con respecto a la raíz del proyecto. Al ejecutarse herramientas externas o subprocesos sin tener `app/` en la variable de entorno `PYTHONPATH`, Python intentaba localizar `core` en el directorio de trabajo inmediato y fallaba.
- **Solución:** Se unificaron las importaciones canónicas, se insertó `app/` en `sys.path` al inicio de `app/main.py` y `alembic/env.py`, y se configuró formalmente `pythonpath = ["app", "."]` en el archivo `pyproject.toml`. De este modo, tanto pytest, uvicorn como los scripts CLI resuelven de forma idéntica e inequívoca las rutas de módulos.

#### 2. Error: `ModuleNotFoundError: No module named 'psycopg2'`
- **Causa:** Las cadenas de conexión estándar de PostgreSQL proporcionadas por servicios en la nube (como Neon o Render) comienzan con el prefijo genérico `postgresql://`. Por especificación interna de SQLAlchemy, dicho prefijo invoca automáticamente el driver histórico `psycopg2`. Dado que el proyecto utiliza la versión moderna y asíncrona/síncrona de alto rendimiento `psycopg` (v3, paquete `psycopg[binary]`), la ejecución fallaba por ausencia de `psycopg2`.
- **Solución:** Se implementó una normalización automática y transparente de la URL de conexión en `app/core/database.py` y `alembic/env.py`. Si la variable `DATABASE_URL` comienza por `postgresql://` o `postgres://`, el sistema la transforma en tiempo de ejecución a `postgresql+psycopg://`, forzando el uso exclusivo del driver Psycopg 3 instalado.

#### 3. Error: `ImportError: email-validator is not installed`
- **Causa:** Los esquemas de validación Pydantic (`RegistroClienteIn`) implementan el tipo `EmailStr` para garantizar la conformidad estricta con el estándar RFC 5322. Pydantic delega esta validación en la librería de terceros `email-validator`, la cual no se encontraba declarada en las dependencias base del entorno virtual.
- **Solución:** Se instaló la librería en el entorno virtual (`.venv`) y se añadió formalmente `email-validator>=2.0.0` a la lista de dependencias obligatorias en `pyproject.toml`.

#### 4. Error: Fallos 404 en `tests/test_health.py` (AssertionError en handlers de error)
- **Causa:** Divergencia de instancias de la aplicación en memoria (`sys.modules`). El archivo `tests/test_health.py` importaba la aplicación mediante `from main import app`, mientras que el archivo de fixtures `tests/conftest.py` lo hacía a través de `from app.main import app`. Como consecuencia, Python instanció dos objetos `FastAPI` independientes; las rutas auxiliares de prueba registradas por el test residían en una instancia distinta a la evaluada por el cliente de pruebas `TestClient`, provocando respuestas `404 Not Found`.
- **Solución:** Se homologaron de forma estricta todas las referencias de importación en la suite de pruebas hacia `from app.main import app`, alineando el espacio de nombres, y se eliminaron los directorios residuales de caché compilada (`__pycache__` y `.pyc`).

#### 5. Problema: Metadatos vacíos en Alembic (`Base.metadata` sin tablas)
- **Causa:** SQLAlchemy 2.0 opera mediante un registro declarativo bajo demanda: las tablas solo se agregan a `Base.metadata` cuando el intérprete de Python carga e importa explícitamente las clases ORM que heredan de `Base`. Si `alembic/env.py` solo importa `Base`, `target_metadata` permanece vacío y el comando `alembic revision --autogenerate` no detecta ningún cambio ni tabla a migrar.
- **Solución:** Se implementó un mecanismo de auto-descubrimiento dinámico e introspección de paquetes en `alembic/env.py` utilizando las librerías estándar `pkgutil.walk_packages` e `importlib`. Al inicializarse Alembic, se escanea recursivamente el directorio de paquetes `app/modules` e importa automáticamente cualquier módulo que contenga definiciones ORM (`.modelos`), registrando todas las tablas en `Base.metadata` sin requerir importaciones manuales para cada nuevo caso de uso.

#### 6. Error Adicional Resuelto: Incompatibilidad con PgBouncer en Neon (`unsupported startup parameter: search_path`)
- **Causa:** La cadena de conexión de Neon configurada con *Connection Pooling* (`-pooler`) interactúa a través del proxy PgBouncer en modo transacción. Al pasar `connect_args={"options": "-c search_path=fashionstore,public"}`, PgBouncer rechaza la conexión en el paquete de inicio (*startup packet*) con el error `ERROR: unsupported startup parameter in options: search_path`.
- **Solución:** Se eliminó el parámetro `options` de los argumentos de conexión de arranque en `app/core/database.py` y se reemplazó por un listener de ciclo de vida `@event.listens_for(engine, "connect")` que ejecuta `SET search_path TO fashionstore, public` inmediatamente tras establecerse la conexión física, garantizando compatibilidad total con Neon Serverless.

#### 7. Error Adicional Resuelto: Discordancia de Tipos en Columna `rol` (`DatatypeMismatch`)
- **Causa:** En la base de datos PostgreSQL de Neon, la columna `usuarios.rol` fue creada como tipo `ENUM` nativo (`fashionstore.rol_usuario`). En el modelo `UsuarioORM`, la columna estaba tipada como `String(30)`. Al ejecutar el `INSERT`, SQLAlchemy emitía `%(rol)s::VARCHAR`, lo que provocaba que PostgreSQL abortara la transacción por discordancia de tipo de dato (`column "rol" is of type rol_usuario but expression is of type character varying`).
- **Solución:** Se importó `from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM` en `app/modules/autenticacion_seguridad/modelos.py` y se mapeó la columna con `rol_usuario_enum` configurado con `create_type=False`, asegurando que el driver emita el valor con el cast nativo a `fashionstore.rol_usuario`.
