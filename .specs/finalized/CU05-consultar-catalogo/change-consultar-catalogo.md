# Propuesta de Cambio Técnico: CU05 - Consultar Catálogo de Productos

**ID del Cambio:** `CU05-consultar-catalogo`  
**Caso de Uso:** CU05 - Consultar Catálogo de Productos  
**Paquete de Dominio:** `catalogo` (`catalogo_productos`)  
**Actores:** Cliente Autenticado y Visitante Anónimo  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 1 (Exploración pública de catálogo, consultas agregadas y navegación institucional raíz)  
**Estado:** 🟢 IMPLEMENTADO Y PROMOVIDO A BASELINE PERMANENTE (`.specs/modules/catalogo_productos/CU05-consultar-catalogo.md`)  

> **Nota de reconciliación (2026-09-21):** este documento conservaba el encabezado y las casillas
> del momento de la propuesta (20 tareas sin marcar y 16 checkpoints en ⏳), contradiciendo a su
> propio `checkpoint.md`, que da los 18 puntos de control por aprobados, y a la entrada 1.8.0 del
> `CHANGELOG.md`, que documenta la promoción a especificación permanente. Se sincroniza con el
> estado real.  
**Fecha de Creación:** 2026-09-21  

---

## Índice de Contenidos
1. [A. Especificación Técnica Formal (`spec`)](#a-especificación-técnica-formal-spec)
   - [1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)](#1-bloque-1-backend-ec-backend---fastapi--sqlalchemy-20--postgresql-neon)
   - [2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)](#2-bloque-2-frontend-web-ec-frontend---angular-19-standalone-con-signals)
   - [3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)](#3-bloque-3-mobile-multiplataforma-ec-mobile---flutter-3x--dart)
2. [B. Plan de Ejecución Secuencial (`plan`)](#b-plan-de-ejecución-secuencial-plan)
3. [C. Lista de Tareas Atómicas (`tasks`)](#c-lista-de-tareas-atómicas-tasks)
4. [D. Puntos de Control y Verificación (`checkpoints`)](#d-puntos-de-control-y-verificación-checkpoints)

---

## A. Especificación Técnica Formal (`spec`)

### 1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

#### 1.1 Propósito y Reglas de Negocio
Permitir a clientes registrados y visitantes anónimos consultar el catálogo general de prendas de alta costura de FashionStore, obteniendo el listado de productos activos paginado, el desglose dinámico de categorías con conteo de prendas, variantes disponibles (tallas y colores) y precios con verificación de promociones activas.

1. **Jerarquía y Agregación de Categorías:**
   - Consulta sobre `fashionstore.categorias` calculando de forma agregada `total_prendas` (`COUNT(DISTINCT productos.id_producto)`) para aquellas categorías con productos activos (`activo = true`).
   - El payload incluye el resumen de categorías para alimentar la barra de chips en los clientes web y móviles, más el conteo consolidado de "Todos los productos".
2. **Filtrado Rápido por Categoría (Chips):**
   - Parámetro opcional `categoria_id`. Si no se especifica, se retorna el catálogo general ordenado por novedad (`recientes`).
   - Si se especifica `categoria_id`, se filtran los productos pertenecientes a dicha categoría y sus subcategorías.
3. **Cálculo de Existencias, Variantes y Precios:**
   - Se obtienen las variantes asociadas (`fashionstore.variantes_producto`) consolidando tallas disponibles (`tallas.codigo` ordenadas por `tallas.orden`) y colores disponibles (`colores.nombre`, `colores.codigo_hex`).
   - Se calcula el stock total disponible (`SUM(inventario_sucursal.cantidad_disponible)`) y la disponibilidad física `tiene_stock`.
   - Se consulta `fashionstore.promociones` para determinar si el producto goza de un descuento vigente, calculando `precio_final`, `tiene_descuento` y `porcentaje_descuento`.
4. **Metadatos Editoriales de Alta Costura:**
   - Atributos requeridos: `subtitulo_atelier` (*"ALTA COSTURA"*, *"SASTRERÍA ATELIER"*, *"BÁSICOS DE LUJO"*, *"ABRIGOS DE AUTOR"*), `etiqueta_badge` (*"EDICIÓN LIMITADA"*, *"EN SERRANO"*, *"SEDA PURA"*, *"LANA & SEDA"*, *"NOVEDAD"*, *"PRODUCCIÓN LIMITADA"*, *"DISPONIBLE"* o *"ÚLTIMAS UNIDADES"*) y `rating_promedio`.
5. **REGLA DE NEGOCIO GLOBAL INQUEBRANTABLE (MODA EXCLUSIVAMENTE FEMENINA):**
   - Catálogo 100% femenino. Prohibido cualquier contenido, prenda o modelo masculino.
6. **INTEGRIDAD DE DATOS REALES (CERO HARDCODING):**
   - Todos los datos provienen de la base de datos real PostgreSQL Neon (`fashionstore.productos`).
7. **CONSULTAS ÓPTIMAS (CERO N+1):**
   - Precarga con `joinedload` / `selectinload` para variantes, tallas, colores e inventarios.

#### 1.2 Contrato de API REST
- **Ruta:** `GET /api/v1/catalogo`
- **Query Parameters:**
  - `categoria_id` (Optional[int]): ID de categoría para filtrado por chip.
  - `ordenar_por` (str, default="recientes"): Criterio de ordenación (`recientes`, `precio_asc`, `precio_desc`, `nombre_asc`, `rating`).
  - `pagina` (int, default=1, ge=1): Número de página.
  - `limite` (int, default=8, ge=1, le=50): Tamaño de página (8 en Web, 6 en Mobile).
- **Payload de Salida (`CatalogoOut`):**
  - `resumen_categorias`: `List[CategoriaResumenOut]` (`id_categoria`, `nombre`, `total_prendas`).
  - `total_articulos`: int (total de productos en la consulta actual).
  - `pagina_actual`: int.
  - `limite`: int.
  - `total_paginas`: int.
  - `tiene_siguiente`: bool.
  - `tiene_anterior`: bool.
  - `categoria_seleccionada_id`: Optional[int].
  - `items`: `List[ProductoCatalogoOut]`:
    - `id_producto`: int
    - `nombre`: str
    - `descripcion`: Optional[str]
    - `precio_base`: Decimal
    - `precio_final`: Decimal
    - `tiene_descuento`: bool
    - `porcentaje_descuento`: Optional[int]
    - `imagen_url`: Optional[str]
    - `categoria_id`: int
    - `categoria_nombre`: str
    - `subtitulo_atelier`: str
    - `etiqueta_badge`: Optional[str]
    - `rating_promedio`: float
    - `tallas_disponibles`: List[str]
    - `colores_disponibles`: List[ColorItemOut] (`id_color`, `nombre`, `codigo_hex`)
    - `stock_total_disponible`: int
    - `tiene_stock`: bool
    - `es_favorito`: bool

#### 1.3 Criterios de Aceptación (Gherkin)
- Escenario: Carga inicial del catálogo activo con paginación y resumen de categorías.
- Escenario: Filtrado dinámico por chip de categoría (`categoria_id = 2`).
- Escenario: Consulta de categoría vacía (Empty state editorial con `total_articulos: 0` y `items: []`).
- Escenario: Paginación determinista con cálculo de `total_paginas` y banderas de navegación.

---

### 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

#### 2.1 Jerarquía de Navegación y Scaffolding (Hub-and-Spoke)
- **Ruta:** `/catalogo` declarada como ruta hija en `MainLayoutComponent` en `app.routes.ts`.
- **Barra de Navegación Institucional (Header): SIEMPRE VISIBLE.** Pestaña `CATÁLOGO` destacada activamente.
- **Botón de regreso (`← Volver`): ESTRICTAMENTE PROHIBIDO.** Al constituir una pantalla principal (Hub), no lleva flecha ni botón de retroceso.

#### 2.2 Componentes & UI Editorial Desktop
- **Breadcrumbs:** `FASHION STORE / CATÁLOGO / TODAS LAS PRENDAS` con badge `STOCK SINCRONIZADO EN TIEMPO REAL CON FLAGSHIP SERRANO & SAINT-HONORÉ`.
- **Cabecera:** `H1` *"CATÁLOGO DE PRENDAS"* en tipografía `Outfit`, subtítulo de confección y sello *"CERTIFICACIÓN ARTESANAL · MADRID · PARÍS"*.
- **Chips de Categorías:** Barra deslizable con contadores numéricos interactivos: *"TODOS LOS PRODUCTOS (24)"* (activo), *"SASTRERÍA & TRAJES (8)"*, *"VESTIDOS DE GALA (6)"*, *"BLUSAS & TOPS DE SEDA (5)"*, *"PUNTO & ABRIGOS (5)"*.
- **Selector de Cuadrícula:** Iconos interactivos para alternar entre vista de 4 columnas y 2 columnas.
- **Botón "Filtrar y Ordenar":** Acceso directo y fluido hacia la búsqueda avanzada de CU06 (`/buscar`).
- **Grilla de 4 Columnas:** Tarjetas de lujo con badges superiores (*"EDICIÓN LIMITADA"*, *"EN SERRANO"*, *"SEDA PURA"*, *"LANA & SEDA"*, *"NOVEDAD"*, *"DISPONIBLE"*), botón de wishlist/favoritos, subtítulos de atelier en mayúsculas, tallas disponibles y círculos de color textil. Clic en tarjeta navega hacia el detalle de prenda (CU07).
- **Paginación Editorial:** Barra de progreso *"MOSTRANDO 1 – 8 DE 24 PRENDAS"*, botones numéricos y botón *"SIGUIENTE >"*.
- **Bloque de Conserjería:** *"CONSERJERÍA PRIVADA DE TALLAS & FITTING"* con botón CTA *"SOLICITAR ASESORÍA"*.
- **Footer Completo:** Pie institucional de FashionStore.

---

### 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

#### 3.1 Integración en `PantallaPrincipalHub`
- **Pestaña de Catálogo (Índice 2):** Se sustituye el `PantallaCatalogoPlaceholder` en blanco por la implementación real de `PantallaCatalogo`.
- **BottomNavigationBar: SIEMPRE VISIBLE** en el índice 2 con el icono de Catálogo activo y en negrita.
- **AppBar sin botón de retroceso:** `automaticallyImplyLeading: false`.

#### 3.2 Arquitectura BLoC & Componentes UI Mobile
- **BLoC:** `CatalogoBloc` con eventos `CargarCatalogoIniciado`, `FiltrarPorCategoriaChip`, `CambiarModoVistaColumnas`, `CargarMasProductosCatalogo`, `ToggleFavoritoPrenda` y estados sellados inmutables (`CatalogoCargando`, `CatalogoCargado`, `CatalogoVacio`, `CatalogoError`).
- **AppBar Móvil:** Título "Catálogo de Prendas" y conmutador de vista (2 columnas vs lista).
- **Chips Horizontales con Conteo:** Deslizables con unidades entre paréntesis (*"Todos (24)"*, *"Sastrería & Trajes (8)"*, *"Vestidos (6)"*).
- **Botón "Filtrar y Ordenar":** Conmuta a la pestaña 1 (Buscar) o abre modal de filtros.
- **GridView en 2 Columnas:** Tarjetas de alta costura con badges textiles superiores, botón de wishlist circular, subtítulo de autor, tallas y precio en EUR.
- **Controles de Paginación Dual:** Botón expansor central *"CARGAR MÁS PRENDAS (18) ⌵"* y paginación numerada inferior `[1] [2] [3] [Siguiente →]`.
- **Sello Editorial Inferior:** Monograma *"ATELIER FLAGSHIP MADRID · PARÍS - Edición Limitada · Confección Artesanal en Tejidos Naturales"*.

---

## B. Plan de Ejecución Secuencial (`plan`)

1. **Fase 1: Backend (`Ec-backend`)**:
   - Creación de módulo `app/modules/catalogo/cu05_consultar_catalogo/`.
   - Definición de esquemas Pydantic `CatalogoOut`, `ProductoCatalogoOut`, `CategoriaResumenOut`.
   - Consultas SQL optimizadas en SQLAlchemy con cálculo de resumen de categorías y verificación de promociones.
   - Endpoint `GET /api/v1/catalogo` y montaje en router central.
   - Suite completa de pruebas en Pytest (`tests/modules/catalogo/test_cu05_catalogo.py`) pasando al 100%.

2. **Fase 2: Frontend Web (`Ec-frontend`)**:
   - Creación de `CatalogoService` y modelos en Angular.
   - Creación de componente standalone `CatalogoComponent` con Signals reactivos.
   - Registro en `app.routes.ts` dentro de `MainLayoutComponent` (`/catalogo`).
   - Maquetación con Tailwind CSS de la vista completa de escritorio (breadcrumbs, chips con unidades, cuadrícula 4 columnas, selector de vista, paginación con barra de progreso y conserjería de fitting).
   - Pruebas unitarias en Vitest pasando al 100% y `npm run build` sin errores.

3. **Fase 3: Mobile Multiplataforma (`Ec-mobile`)**:
   - DTOs, datasource HTTP y repositorio en Flutter.
   - `CatalogoBloc` con manejo de estados inmutables y parsing tolerante de `Decimal`.
   - `PantallaCatalogo` en Flutter con fidelidad visual exacta a la captura móvil (chips horizontales, GridView 2 columnas, botón cargar más y paginación numerada).
   - Integración en `PantallaPrincipalHub` (índice 2) manteniendo navegación fluida sin recargas ni duplicación de rutas.
   - Pruebas unitarias/widgets en Flutter pasando al 100% y `flutter analyze` con 0 advertencias.

---

## C. Lista de Tareas Atómicas (`tasks`)

### Tareas de Backend
- [x] `T-BE-01`: Crear estructura de paquetes `app/modules/catalogo/cu05_consultar_catalogo/`.
- [x] `T-BE-02`: Definir esquemas Pydantic en `esquemas.py`.
- [x] `T-BE-03`: Implementar consultas relacionales y conteo por categoría en `repositorio.py`.
- [x] `T-BE-04`: Implementar lógica de promociones y enriquecimiento en `servicio.py`.
- [x] `T-BE-05`: Implementar endpoint `GET /api/v1/catalogo` en `router.py`.
- [x] `T-BE-06`: Conectar router en `app/modules/catalogo/router.py`.
- [x] `T-BE-07`: Escribir y ejecutar suite de tests en `tests/modules/catalogo/test_cu05_catalogo.py`.

### Tareas de Frontend Web
- [x] `T-FE-01`: Crear modelos y servicio `CatalogoService` en Angular.
- [x] `T-FE-02`: Crear componente standalone `CatalogoComponent` con Signals.
- [x] `T-FE-03`: Maquetar vista de catálogo completa con Tailwind CSS según captura Desktop.
- [x] `T-FE-04`: Registrar `/catalogo` dentro de `MainLayoutComponent` en `app.routes.ts`.
- [x] `T-FE-05`: Conectar interacciones de chips, selector de cuadrícula, paginación y enlace a `/buscar`.
- [x] `T-FE-06`: Escribir suite de pruebas unitarias en `catalogo.component.spec.ts`.
- [x] `T-FE-07`: Validar compilación con `npm run build`.

### Tareas de Mobile
- [x] `T-MO-01`: Crear DTOs, cliente HTTP y repositorio de catálogo en Flutter.
- [x] `T-MO-02`: Implementar `CatalogoBloc`, eventos y estados sellados.
- [x] `T-MO-03`: Crear `PantallaCatalogo` con diseño fiel a la captura móvil.
- [x] `T-MO-04`: Integrar en `PantallaPrincipalHub` en el índice 2 sustituyendo el placeholder.
- [x] `T-MO-05`: Escribir suite de pruebas en `test/pantalla_catalogo_test.dart`.
- [x] `T-MO-06`: Validar con `flutter analyze` y `flutter test`.

---

## D. Puntos de Control y Verificación (`checkpoints`)

| ID | Criterio de Verificación | Método de Validación | Estado |
| :--- | :--- | :--- | :--- |
| **CP-01** | `GET /api/v1/catalogo` responde 200 con estructura `CatalogoOut` completa. | Tests de integración Pytest | ✅ Superado |
| **CP-02** | `resumen_categorias` calcula correctamente los conteos de prendas activas. | Consulta SQL directa y tests | ✅ Superado |
| **CP-03** | Filtrado por `categoria_id` retorna únicamente prendas de la categoría seleccionada. | Test unitario en Pytest | ✅ Superado |
| **CP-04** | Paginación determinista calcula total de páginas y banderas de avance. | Tests de paginación Pytest | ✅ Superado |
| **CP-05** | Vista Web `/catalogo` renderizada dentro de `MainLayoutComponent` con navbar visible. | Inspección visual y tests | ✅ Superado |
| **CP-06** | Ausencia estricta de botón `← Volver` en Web y Mobile (Regla Hub-and-Spoke). | Aserción en tests unitarios | ✅ Superado |
| **CP-07** | Fila de chips de categorías filtra reactivamente las tarjetas mediante Signals. | Tests en Vitest | ✅ Superado |
| **CP-08** | Botón "Filtrar y Ordenar" enlaza correctamente con la vista de búsqueda de CU06. | Test de router en Angular | ✅ Superado |
| **CP-09** | Grilla de 4 columnas en Web reproduce la captura Desktop: badges, tallas, dots y precio. | Validación visual y estilos | ✅ Superado |
| **CP-10** | Compilación de producción en Angular limpia sin errores (`npm run build`). | Build en Angular CLI | ✅ Superado |
| **CP-11** | Pestaña Catálogo en Mobile mantiene visible el `BottomNavigationBar` en índice 2. | Tests de widget en Flutter | ✅ Superado |
| **CP-12** | GridView móvil en 2 columnas reproduce la captura Mobile con shimmers y badges. | Tests de widget en Flutter | ✅ Superado |
| **CP-13** | Botón expansor "CARGAR MÁS PRENDAS" y paginación numerada en Mobile funcionales. | Tests de BLoC y widgets | ✅ Superado |
| **CP-14** | Análisis estático de Flutter limpio (`flutter analyze` 0 issues). | CLI `flutter analyze` | ✅ Superado |
| **CP-15** | Suite de pruebas en Flutter pasando al 100% (`flutter test`). | CLI `flutter test` | ✅ Superado |
| **CP-16** | Catálogo 100% de moda femenina exclusiva y datos provenientes de PostgreSQL real. | Auditoría de assets y BD | ✅ Superado |
