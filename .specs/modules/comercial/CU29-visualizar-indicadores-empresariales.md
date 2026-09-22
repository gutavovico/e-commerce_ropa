# Especificacion Tecnica Permanente: CU29 - Visualizar indicadores empresariales

**Codigo:** CU29  
**Nombre:** Visualizar indicadores empresariales  
**Paquete de Dominio:** `comercial` / `analitica_reportes`  
**Directorio Funcional Backend:** `app/modules/comercial/cu29_indicadores`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/cu29_indicadores`  
**Directorio Funcional Mobile:** Excluido formalmente (inteligencia de negocios y consolidacion analitica directiva reservada exclusivamente al back-office web corporativo)  
**Actores Primarios:**  
- Administrador (Acceso global directivo irrestricto a indicadores consolidados, comparativas de sucursales y tendencias corporativas)  
- Encargado de Sucursal (Acceso analitico segregado estrictamente a los indicadores de rendimiento de su propia sucursal asignada)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por confidencialidad comercial - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.6.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Analitica y Reportes).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush, Angular Signals y visualizaciones nativas en SVG).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU29 centraliza la inteligencia de negocios (Business Intelligence) y la analitica directiva cuantitativa de FashionStore. Permite evaluar en tiempo real la salud financiera de la cadena mediante el calculo de ingresos brutos, volumen transaccional, margen comercial estimado, ticket promedio, variaciones porcentuales relativas contra periodos precedentes, series cronologicas interpoladas, ranking de prendas de mayor rotacion, distribucion multicanal y comparativas de red inter-sucursal bajo estricto control de acceso basado en roles (RBAC).

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), disenada con Flutter 3.x, tiene como proposito exclusivo la experiencia de compra y probador inmersivo B2C orientada al consumidor final (exploracion de catalogo, vestidor virtual en Realidad Aumentada, configuracion de bolsa de compras y pago digital).  
La inteligencia de negocios, la comparativa de productividad inter-sucursales y la interpretacion de margenes brutos son competencias estrategicas confidenciales de la direccion corporativa y administracion de tiendas.  
Por tanto, se ratifica formalmente la exclusion justificada de `Ec-mobile`: cero modelos, pantallas o servicios en Flutter para este caso de uso.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Los endpoints base `/api/v1/admin/indicadores` exigen JWT valido (HTTP 401 si ausente). Roles `cajero` o `cliente` son rechazados con HTTP 403 Forbidden. `administrador` tiene visibilidad global o filtrable por sede, mientras que `encargado_sucursal` esta estrictamente confinado a las transacciones de su sucursal asignada.

2. **RB-2: Segregacion Territorial de Metricas por Sede:**
   - Si el usuario autenticado tiene el rol `encargado_sucursal`, el backend ignora cualquier parametro `id_sucursal` externo y fuerza obligatoriamente el calculo analitico hacia su propia sucursal. Los intentos de acceder a comparativas de sucursales ajenas son bloqueados con HTTP 403 Forbidden.

3. **RB-3: Consistencia Cronologica de Rango de Fechas:**
   - En periodos personalizados, la `fecha_hasta` debe ser mayor o igual a `fecha_desde` (`fecha_desde <= fecha_hasta`). En caso contrario, se rechaza la operacion con HTTP 422 Unprocessable Entity en backend y con validacion sincrona inline en frontend.

4. **RB-4: Calculo Defensivo sin Division por Cero:**
   - En el calculo de variaciones porcentuales relativas y ticket promedio, si el divisor es cero (0 transacciones o 0 ingresos en el periodo base), el sistema retorna 0.00 de manera determinista previniendo excepciones de ejecucion.

5. **RB-5: Comparativa Inter-Sucursales Exclusiva de Administrador:**
   - El endpoint `GET /api/v1/admin/indicadores/comparativa-sucursales` es de consumo exclusivo para usuarios con rol `administrador` o `admin`. La solicitud por parte de un encargado de sucursal es rechazada con HTTP 403 Forbidden.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/comercial/cu29_indicadores`
- **Servicio:** `ServicioIndicadoresEmpresariales`:
  * `obtener_dashboard_completo`: Resolucion consolidada de resumen, serie temporal, top productos, distribucion y comparativa de sucursales en una sola operacion atomica.
  * `obtener_resumen_ejecutivo`: Agregacion SQL de ingresos, ordenes pagadas, ticket promedio, margen bruto estimado y variacion porcentual contra periodo anterior.
  * `obtener_serie_temporal`: Agrupacion por intervalo temporal (`date_trunc`) diaria, semanal o mensual.
  * `obtener_top_productos`: Ranking agregado de prendas mas comercializadas con parametro `limite`.
  * `obtener_distribucion_ventas`: Clasificacion agregada por categoria taxonomica y por canal comercial (`presencial`, `digital_web`, `digital_movil`).
  * `obtener_comparativa_sucursales`: Agrupacion de rendimiento por sede activa para administradores.
- **Excepciones Semanticas:** `IndicadoresError`, `RangoTemporalInvalidoError` (422), `AccesoComparativaDenegadoError` (403), `SucursalNoAutorizadaError` (403).

### 2.2 Modelos Persistentes ORM
- Mapeo declarativo SQLAlchemy 2.0 bajo el esquema `fashionstore`:
  * `VentaORM` (`fashionstore.ventas`, estado='pagada')
  * `VentaDetalleORM` (`fashionstore.venta_detalle`)
  * `VarianteProductoORM` (`fashionstore.variantes_producto`)
  * `ProductoORM` (`fashionstore.productos`)
  * `CategoriaORM` (`fashionstore.categorias`)
  * `SucursalORM` (`fashionstore.sucursales`, activa=True)
  * `CiudadORM` (`fashionstore.ciudades`)

### 2.3 Endpoints REST Expuestos
- `GET /api/v1/admin/indicadores/dashboard`: Consolidado analitico completo.
- `GET /api/v1/admin/indicadores/resumen`: Resumen ejecutivo con variaciones porcentuales.
- `GET /api/v1/admin/indicadores/serie-temporal`: Puntos de serie temporal de ingresos.
- `GET /api/v1/admin/indicadores/top-productos`: Top de prendas comercializadas.
- `GET /api/v1/admin/indicadores/distribucion`: Desglose por canal y categoria.
- `GET /api/v1/admin/indicadores/comparativa-sucursales`: Comparativa de sedes para administradores.

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Componentes y Rutas
- **Ruta:** `/admin/indicadores` custodiada por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
- **Componente Principal:** `IndicadoresAdminComponent` (Standalone, `ChangeDetectionStrategy.OnPush`, Angular Signals).
- **Servicio:** `IndicadoresAdminService` (estado reactivo centralizado con Signals y cliente HTTP fuertemente tipado).

### 3.2 Interfaz de Usuario y Diseno Editorial
- Layout editorial `max-w-[1440px] px-6 py-8 mx-auto`, fondo Slate 50, tipografia Outfit, acentos Camel (`#AD8C63`) y Obsidian (`#0F172A`).
- Tarjeta corporativa en `AdminDashboardComponent` bajo la categoria "Analitica y Reportes" con badge "Business Intelligence", identificador `#btn-visualizar-indicadores-empresariales` y directiva dual de navegacion (`routerLink` y `(click)`).
- Rejilla superior de 4 tarjetas de KPIs ejecutivos:
  1. Ingresos Totales (con porcentaje de variacion respecto al periodo anterior y color discretamente semaforico).
  2. Transacciones Concluidas.
  3. Margen Comercial Estimado.
  4. Ticket Promedio.
- Conmutador reactivo de periodos: `7d`, `30d`, `mes_actual`, `anio_actual`, `personalizado` con selectores de fecha sincronizados y validacion inline.
- Selector de sucursal: Habilitado con lista completa para rol administrador; bloqueado con badge institucional para encargado de sucursal.
- Graficas en SVG nativo puro (cero librerias externas pesadas):
  * Serie temporal de ingresos: curva SVG interpolada con puntos interactivos (`<circle>`), area sombreada y tooltips informativos.
  * Ranking de Top 5 prendas: barras horizontales proporcionales en SVG con SKU y monto.
  * Distribucion por canal y categoria: barras de progreso segmentadas.
  * Comparativa de sucursales: tabla de sedes visible exclusivamente para administradores.
- Luxury Banners contextuales y skeletons de carga para contingencias no destructivas.
