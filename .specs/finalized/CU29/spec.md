# Especificacion de Requisitos: [CU29] Visualizar indicadores empresariales

**Codigo del Caso de Uso:** CU29  
**Denominacion Oficial:** Visualizar indicadores empresariales  
**Modulo Funcional:** Analitica y Reportes / Inteligencia Empresarial (`analitica_reportes` / `comercial`)  
**Actores Primarios:**  
- Administrador Corporativo (Acceso irrestricto a indicadores globales consolidados, comparativas de red multi-sucursal y proyecciones directivas)  
- Encargado de Sucursal (Acceso acotado exclusivamente a los indicadores analiticos de rendimiento de su propia sucursal asignada)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC de segregacion de responsabilidades - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica de seguridad y confidencialidad comercial - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Entorno de Implementacion:** Web corporativa exclusiva (`Ec-backend` FastAPI y `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal de Plataforma:** `Ec-mobile` (Flutter 3.x) 100% excluida  

---

## 1. Vision General del Caso de Uso

### 1.1 Proposito y Justificacion de Negocio
El caso de uso "Visualizar indicadores empresariales" constituye el nucleo de Inteligencia de Negocios (Business Intelligence) y apoyo a la toma de decisiones directivas de la cadena FashionStore.  
En una organizacion omnicanal de retail de alta gama, la direccion general y las jefaturas de sede requieren herramientas analiticas de alta precision para evaluar el desempeno financiero, identificar tendencias de consumo estacional, optimizar margenes comerciales y comparar la productividad transaccional entre puntos de venta fisicos y canales digitales.

Este modulo permite:
1. Examinar el resumen ejecutivo de salud financiera: ingresos brutos y netos facturados, volumen de ordenes concluidas, ticket promedio consolidado, margen comercial estimado y variacion porcentual contra periodos inmediatos precedentes.
2. Analizar series temporales de recaudacion con agrupaciones dinamicas (diaria, semanal, mensual) para detectar estacionalidades, picos de demanda y caidas de rendimiento en campanas especificas.
3. Conocer el ranking de las prendas y variantes de mayor rotacion (Top N productos mas vendidos) desglosando volumen de piezas comercializadas y recaudacion monetaria atribuida.
4. Evaluar la distribucion de ingresos por categoria taxonomica y canal de venta (tienda fisica boutique, canal web y canal movil) para calibrar estrategias de inventario y mercadotecnia.
5. Comparar de forma grafica y cuantitativa el rendimiento entre todas las sucursales activas de la red (facultad exclusiva de la direccion corporativa).

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Arquitectonica y de Negocio
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada sobre el framework Flutter 3.x, esta concebida con un proposito exclusivo de cara al cliente final (B2C): exploracion interactiva de prendas, probador virtual inmersivo mediante Realidad Aumentada, configuracion de bolsa de compras, reserva de articulos para probador fisico y pasarela de pago digital integrada.

El analisis directivo de inteligencia empresarial, el seguimiento de volumenes macroeconomicos de facturacion, la comparativa de productividad inter-sucursales y la interpretacion de margenes brutos son competencias estrategicas confidenciales de la presidencia corporativa, gerencia financiera y administradores de tienda. Dichas funciones se ejecutan estrictamente en puestos de trabajo de oficina a traves de la plataforma web de escritorio `Ec-frontend`.

### 2.2 Ratificacion de Alcance Tecnico
1. Cero pantallas en `Ec-mobile`: No se desarrollara ninguna vista, grafico, tarjeta ni reporte analitico de indicadores empresariales en el proyecto Flutter.
2. Cero servicios analiticos en `Ec-mobile`: No se definira ninguna peticion HTTP hacia `/api/v1/admin/indicadores` dentro de la aplicacion movil.
3. Generacion pasiva de metricas: La aplicacion movil unicamente actua como generadora transaccional de ventas digitales (`tipo_venta = 'digital_movil'`), las cuales son contabilizadas de forma agregada por el motor analitico del backend y consumidas en el frontend web.

---

## 3. Especificacion de Requisitos Funcionales bajo Sintaxis EARS

### Bloque A: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

#### Seguridad, Autenticacion y Gobernanza RBAC
- **# AC-1 (Ubicuo - Autenticacion Obligatoria):**  
  El sistema debera requerir un token JWT valido y vigente en la cabecera `Authorization: Bearer <token>` para todos los endpoints expuestos bajo el prefijo `/api/v1/admin/indicadores`. Si el token esta ausente, expirado o malformado, el sistema debera rechazar la peticion con HTTP 401 Unauthorized (`CREDENCIALES_INVALIDAS`).

- **# AC-2 (Condicional - Control de Acceso RBAC por Rol):**  
  Si un usuario con rol `cajero` o `cliente` intenta acceder a cualquiera de las rutas de indicadores bajo `/api/v1/admin/indicadores`, el sistema debera denegar el acceso de forma determinista retornando HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

- **# AC-3 (Ubicuo - Segregacion Territorial de Metricas por Sede):**  
  El sistema debera aplicar gobernanza estricta en el alcance analitico segun el rol del usuario autenticado:
  * Usuario con rol `administrador`: Podra consultar metricas consolidadas globales de toda la red o filtrar voluntariamente por cualquier sucursal activa.
  * Usuario con rol `encargado_sucursal`: Podra consultar unicamente las metricas correspondientes a su sucursal de asignacion (`usuarios.id_sucursal`). Si en la peticion se envia un parametro `id_sucursal` foraneo o nulo, el sistema debera ignorarlo y forzar el calculo exclusivamente para su sucursal asignada.

- **# AC-4 (Condicional - Restriccion de Comparativa Inter-Sucursales):**  
  Si un usuario con rol `encargado_sucursal` solicita el endpoint analitico de comparativa de sucursales (`GET /api/v1/admin/indicadores/sucursales-comparativa`), el sistema debera bloquear la solicitud respondiendo con HTTP 403 Forbidden (`SUCURSAL_COMPARATIVA_RESTRINGIDA_ADMIN`).

#### Parametros Temporales y Validaciones
- **# AC-5 (Ubicuo - Normalizacion de Filtros Temporales):**  
  El sistema debera admitir el parametro de periodo predeterminado `periodo` con las opciones: `'7d'` (ultimos 7 dias), `'30d'` (ultimos 30 dias), `'mes_actual'` (desde el primer dia del mes en curso hasta la fecha actual), `'anio_actual'` (desde el primer dia del ano en curso hasta la fecha actual) y `'personalizado'`.

- **# AC-6 (Condicional - Validacion de Rango Cronologico Personalizado):**  
  Si el periodo es `'personalizado'`, el sistema debera exigir los parametros `fecha_desde` y `fecha_hasta`. Si `fecha_desde > fecha_hasta`, el sistema debera rechazar la operacion respondiendo con HTTP 422 Unprocessable Entity (`RANGO_FECHAS_INVALIDO`).

#### Endpoints Analiticos y Agregaciones SQL
- **# AC-7 (Por Evento - Consulta de Resumen Ejecutivo y Tendencias):**  
  Cuando un usuario autorizado invoque `GET /api/v1/admin/indicadores/resumen`, el sistema debera retornar un objeto estructurado con los indicadores clave del periodo seleccionado y su comparativa con el periodo inmediatamente precedente de igual duracion:
  * `ingresos_totales`: Sumatoria monetaria de ventas en estado `'pagada'`.
  * `ingresos_variacion_porcentaje`: Variacion porcentual relativa calculada contra el periodo anterior.
  * `total_transacciones`: Cantidad de ventas pagadas registradas.
  * `transacciones_variacion_porcentaje`: Variacion porcentual de transacciones.
  * `ticket_promedio`: Cociente entre ingresos totales y total de transacciones (0.00 si transacciones = 0).
  * `ticket_promedio_variacion_porcentaje`: Variacion relativa del ticket promedio.
  * `margen_bruto_estimado`: Porcentaje estimado de margen comercial global (determinado parametricamente o por costeo de inventario).
  * `unidades_vendidas`: Cantidad agregada de prendas despachadas.

- **# AC-8 (Por Evento - Serie Temporal de Ingresos y Ordenes):**  
  Cuando un usuario autorizado invoque `GET /api/v1/admin/indicadores/serie-temporal`, el sistema debera calcular la serie temporal de ingresos agrupando los datos mediante truncamiento de fecha (`date_trunc` diario, semanal o mensual segun la duracion del intervalo):
  * Lista ordenada cronologicamente de puntos conteniendo: `etiqueta_tiempo` (formato ISO o YYYY-MM-DD), `monto_ingresos` y `cantidad_ordenes`.

- **# AC-9 (Por Evento - Top Prendas Mas Vendidas):**  
  Cuando un usuario autorizado invoque `GET /api/v1/admin/indicadores/top-productos`, el sistema debera retornar el ranking ordenado descendentemente de las prendas con mayor exito comercial, admitiendo un parametro `limite` (por defecto 5, maximo 20):
  * Cada item del ranking contendra: `id_producto`, `nombre_producto`, `sku_referencia`, `categoria_nombre`, `unidades_vendidas`, `monto_total_generado` y `porcentaje_contribucion`.

- **# AC-10 (Por Evento - Desglose por Categoria Taxonomica):**  
  Cuando un usuario autorizado invoque `GET /api/v1/admin/indicadores/distribucion-categorias`, el sistema debera retornar la distribucion de ingresos agregada por categoria primaria de prenda:
  * Cada registro contendra: `id_categoria`, `nombre_categoria`, `monto_facturado`, `unidades_vendidas` y `participacion_porcentual`.

- **# AC-11 (Por Evento - Desglose por Canal de Comercializacion):**  
  Cuando un usuario autorizado invoque `GET /api/v1/admin/indicadores/distribucion-canales`, el sistema debera retornar la participacion monetaria y volumen de ordenes clasificadas por canal:
  * Canales soportados: Boutique Fisica (`tipo_venta = 'presencial'`), Tienda Web (`tipo_venta = 'digital_web'`) y Canal Movil (`tipo_venta = 'digital_movil'`).
  * Cada canal reportara: `canal_codigo`, `canal_nombre`, `monto_facturado`, `total_ordenes` y `porcentaje_total`.

- **# AC-12 (Por Evento - Comparativa de Rendimiento entre Sucursales):**  
  Cuando un administrador corporativo invoque `GET /api/v1/admin/indicadores/sucursales-comparativa`, el sistema debera retornar la lista comparativa de todas las sucursales activas de la red:
  * Cada sucursal presentara: `id_sucursal`, `nombre_sucursal`, `ciudad`, `monto_facturado`, `total_ventas`, `ticket_promedio` y `porcentaje_red`.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en AdminDashboardComponent
- **# AC-13 (Ubicuo - Tarjeta Boutique Decima en Dashboard):**  
  El sistema debera presentar en `AdminDashboardComponent` la tarjeta oficial de inteligencia directiva con las siguientes especificaciones:
  * Categoria institucional: "Analitica y Reportes".
  * Badge editorial: "Business Intelligence".
  * Titulo formal: "Visualizar indicadores empresariales".
  * Descripcion: "Monitoreo analitico de ingresos, tendencias comerciales, ranking de productos y rendimiento multi-sucursal".
  * Boton de accion: Texto "Visualizar indicadores empresariales", identificador `id="btn-visualizar-indicadores-empresariales"`.
  * Directiva dual anti-botones estaticos: Atributo `routerLink="/admin/indicadores"` acompanado del evento de clic `(click)="navegar('/admin/indicadores', $event)"`.
  * Control de visualizacion RBAC: Tarjeta visible unicamente para usuarios con rol `administrador` o `encargado_sucursal`.

#### Arquitectura de la Vista Principal `/admin/indicadores`
- **# AC-14 (Ubicuo - Diseno Editorial Atelier y Componente Standalone):**  
  La vista `/admin/indicadores` debera implementarse como componente Angular Standalone (`IndicadoresAdminComponent`) con estrategia `ChangeDetectionStrategy.OnPush` y gestion reactiva mediante Signals:
  * Envoltorio centrado `max-w-[1440px] px-6 py-8 mx-auto`, paleta cromatica basada en tokens Slate 50, Obsidian (`#0F172A`), Camel (`#AD8C63`) y acentos discretos esmeralda y carmin para tendencias.
  * Jerarquia tipografica formal con fuente Outfit, encabezado H1 "Visualizar indicadores empresariales", breadcrumbs corporativos y enlace superior de retorno "<- Volver al Panel Principal".

- **# AC-15 (Ubicuo - Barra Superior de Seleccion Temporal y Filtro de Sede):**  
  La interfaz debera proveer una barra interactiva de configuracion temporal:
  * Botones conmutadores de periodo rapido: `7D`, `30D`, `Mes Actual`, `Ano Actual` y `Personalizado`.
  * Selectores de fecha sincronizados para rango personalizado con validacion visual inmediata.
  * Selector de sucursal: Habilitado con lista completa para rol `administrador`; bloqueado o fijo en la sucursal propia para rol `encargado_sucursal`.
  * Boton de actualizacion manual o refresco analitico.

- **# AC-16 (Ubicuo - Rejilla Superior de Tarjetas de KPIs Ejecutivos):**  
  La vista debera desplegar una rejilla de 4 tarjetas de indicadores ejecutivos:
  1. Ingresos Totales: Cifra monetaria formateada con badge de variacion porcentual (verde si positivo, rojo si negativo, gris si neutro) comparado con el periodo anterior.
  2. Total de Transacciones: Conteo de ventas pagadas y su indicador de variacion.
  3. Ticket Promedio: Promedio monetario por compra con su tendencia porcentual.
  4. Unidades Vendidas: Total de articulos despachados en el periodo.

- **# AC-17 (Ubicuo - Visualizaciones Graficas Nativas en SVG Puro):**  
  El sistema debera renderizar las graficas analiticas empleando exclusivamente componentes nativos de Angular y SVG semantico escalable, sin librerias externas pesadas ni plugins de terceros:
  * Grafico de Serie Temporal: Grafico de lineas y areas o columnas SVG reactivo con ejes temporales, cuadricula sutil de fondo y etiquetas numericas formateadas.
  * Ranking de Top Prendas: Grafica de barras horizontales SVG escalonadas por volumen de ingresos, indicando SKU, nombre y porcentaje.
  * Distribucion por Canal: Grafica de anillo o barras de segmento porcentual mostrando boutique fisica, web y movil.
  * Tabla/Grafico Comparativo de Sucursales: Visualizacion comparativa de participacion por sede (oculta para encargados de tienda).

- **# AC-18 (Respuesta a Inconvenientes - Luxury Banners y Manejo No Destructivo):**  
  Si ocurre una falla en el calculo analitico o una desconexion de red, el sistema debera desplegar un Luxury Banner no intrusivo con mensaje de explicacion claro y opcion de reintento, sin destruir el estado general ni la estructura de la pagina.

---

## 4. Matriz de Trazabilidad de Requisitos

| Requisito | Descripcion Breve | Componente Backend | Componente Frontend |
|---|---|---|---|
| # AC-1 | Autenticacion obligatoria JWT | `require_authenticated_user` | `authGuard`, `interceptor` |
| # AC-2 | Control de acceso por rol RBAC | `require_roles(["administrador", "encargado_sucursal"])` | `roleGuard`, `esAdmin`, `esEncargado` |
| # AC-3 | Segregacion territorial por sede | `ServicioIndicadoresEmpresariales` | Selector de sucursal bloqueado |
| # AC-4 | Restriccion comparativa sucursales | Endpoint `GET /sucursales-comparativa` | `esAdmin()` condicional |
| # AC-5 | Parametros temporales estandar | `IndicadoresFiltrosIn` | Botonera de periodos (`7D`, `30D`, etc.) |
| # AC-6 | Validacion cronologica defensiva | Validador Pydantic v2 en `esquemas.py` | Validacion reactiva de formularios |
| # AC-7 | Resumen ejecutivo y variaciones | `obtener_resumen_ejecutivo` | Tarjetas de KPIs con indicadores de tendencia |
| # AC-8 | Serie temporal de recaudacion | `obtener_serie_temporal` | Grafico interactivo SVG nativo |
| # AC-9 | Ranking de prendas mas vendidas | `obtener_top_productos` | Grafico de barras horizontales SVG |
| # AC-10 | Desglose por categorias | `obtener_distribucion_categorias` | Tarjetas con barras de progreso |
| # AC-11 | Distribucion por canales | `obtener_distribucion_canales` | Grafica de anillos/barras de distribucion |
| # AC-12 | Comparativa inter-sucursales | `obtener_comparativa_sucursales` | Seccion de comparativa global |
| # AC-13 | Tarjeta boutique decima en dashboard | Registro de rutas | Tarjeta 10 con directiva dual y test |
| # AC-14 | Diseno editorial Atelier OnPush | N/A | `IndicadoresAdminComponent` |
| # AC-15 | Barra superior de filtros | Parámetros de query | Barra reactiva de control con Signals |
| # AC-16 | Rejilla de 4 KPIs ejecutivos | Respuesta consolidada | Grid de 4 tarjetas de KPIs |
| # AC-17 | Graficos nativos en SVG puro | Datos serializados JSON | Plantillas SVG integradas en Angular |
| # AC-18 | Manejo no destructivo de fallos | Excepciones estructuradas | Luxury Banners de alerta y reintento |
