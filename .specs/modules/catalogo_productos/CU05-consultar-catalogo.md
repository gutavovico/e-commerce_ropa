# Especificación Técnica Permanente: CU05 - Consultar Catálogo de Productos

**Código:** CU05  
**Nombre:** Consultar Catálogo de Productos (Colección General, Atelier & Sastrería Femenina)  
**Paquete de Dominio:** `catalogo_productos`  
**Directorio Funcional:** `cu05_consultar_catalogo`  
**Actores:** Cliente (Registrado y Visitante Anónimo)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Línea Base Permanente Consolidada)  
**Estado:** 🟢 Aprobado y Promovido a Especificación Permanente  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1_terminado.pdf` / `SI2-Parcial1.md` (Líneas 957-974: Propósito, actores, precondiciones, flujo principal de consulta del catálogo activo, tablas `productos`, `categorias`, `variantes_producto`, `inventario_sucursal` y `promociones`).
- Referencia Visual y UX Web: Captura de referencia Desktop Haute Couture Atelier (Breadcrumbs editoriales, cabecera "CATÁLOGO DE PRENDAS", selector horizontal de categorías con contadores numéricos, cuadrícula de 4 columnas con badges como *"EDICIÓN LIMITADA"*, *"NOVEDAD"*, *"ÚLTIMAS UNIDADES"*, selector de tallas, dots de color, paginación con barra de progreso y bloque de Conserjería Privada de Fitting).
- Referencia Visual y UX Mobile: Captura de referencia Mobile Atelier (AppBar institucional "Catálogo de Prendas", carrusel horizontal de chips con unidades *"Todos (20)"*, *"Vestidos (5)"*, selector de 1 vs 2 columnas, tarjetas con wishlist interactiva, botón expansor *"CARGAR MÁS PRENDAS"* y sello editorial de pie de página).
- Directriz Arquitectónica Global: Jerarquía de Vistas (Hub-and-Spoke) ([`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/architecture/directriz-navegacion-hub-and-spoke.md)).
- Design System: Tipografía corporativa `Outfit`, paleta textil Obsidian/Camel/Marfil de `fashionstore-tokens.md`, y catálogo estrictamente femenino.

---

## 1. Definición Funcional y Reglas de Negocio

### 1.1 Propósito y Alcance
Proporcionar a los clientes de FashionStore (tanto usuarios registrados como visitantes anónimos) una experiencia omnicanal inmersiva para consultar el catálogo de prendas de alta costura femenina, garantizando la navegación rápida por categorías mediante chips interactivos con contadores de unidades, cálculo de precios y promociones activas, visualización de variantes de talla y color, y paginación fluida tanto en Web como en Mobile.

### 1.2 Reglas de Negocio Estrictas

1. **Jerarquía y Agregación de Categorías:**
   - Cada producto activo pertenece a una categoría (`productos.id_categoria -> categorias.id_categoria`).
   - El catálogo calcula de manera agregada mediante SQL directo y sin queries N+1 el número de prendas activas (`COUNT(DISTINCT productos.id_producto)`) por cada categoría existente.
   - Se incluye el conteo consolidado total para el chip *"Todos los productos"*.

2. **Filtrado Rápido por Categoría (Chips):**
   - El parámetro `categoria_id` es opcional.
   - Si `categoria_id` es nulo, se retornan los artículos de todas las categorías ordenados cronológicamente por piezas recientes.
   - Si se envía `categoria_id`, se restringe la consulta estrictamente a las prendas de dicha categoría.

3. **Cálculo de Existencias, Descuentos y Variantes:**
   - Solo se exponen prendas con `activo = true`.
   - Se extraen las tallas disponibles ordenadas normativamente (`tallas.orden`) y los colores disponibles (`colores.nombre`, `colores.codigo_hex`) a partir de `variantes_producto`.
   - Se evalúan las promociones vigentes en `fashionstore.promociones` y `fashionstore.promociones_producto` para calcular `precio_final`, `tiene_descuento` y `porcentaje_descuento`.
   - Se calcula el stock total acumulado (`SUM(inventario_sucursal.cantidad_disponible)`) y la bandera booleana `tiene_stock`.

4. **Metadatos Editoriales de Alta Costura:**
   - Cada producto expone:
     - `subtitulo_atelier`: Familia o línea de confección (ej. *"ALTA COSTURA"*, *"SASTRERÍA ATELIER"*, *"BÁSICOS DE LUJO"*, *"ABRIGOS DE AUTOR"*).
     - `etiqueta_badge`: Badge editorial contextual (ej. *"EDICIÓN LIMITADA"*, *"NOVEDAD"*, *"ÚLTIMAS UNIDADES"* o *"DISPONIBLE"*).
     - `rating_promedio`: Calificación de atelier (ej. 4.9).

5. **Regla de Negocio Global: Catálogo Exclusivamente Femenino:**
   - Toda la indumentaria, prendas y piezas de sastrería son estrictamente para mujeres.
   - Queda totalmente excluida cualquier referencia, prenda o modelo masculino.

6. **Integridad de Datos Reales (Cero Hardcoding):**
   - Todos los productos y categorías provienen estrictamente de la base de datos PostgreSQL Neon (`fashionstore.productos`).
   - Cero productos ficticios o quemados en cliente.

7. **Directriz Arquitectónica Global: Jerarquía Hub-and-Spoke (Pantalla Raíz / Hub):**
   - `CU05` (`Catálogo`) está clasificada normativamente como una de las **4 Pantallas Raíz (Hub)** del sistema (`Inicio`, `Buscar`, `Catálogo`, `Perfil`).
   - **Barra de navegación principal (Navbar Web / BottomNavigationBar Mobile): SIEMPRE VISIBLE Y ACTIVA.**
   - **Botón de regreso (`← Volver` / `leading: BackButton()`): ESTRICTAMENTE PROHIBIDO.**

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 2.1 Modelos ORM (`app/modules/catalogo/modelos.py`)
Mapeo sobre esquema `fashionstore`:
- `ProductoORM`: `id_producto`, `id_categoria`, `id_coleccion`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `activo`.
- `CategoriaORM`: `id_categoria`, `nombre`, `descripcion`, `activo`.
- `VarianteProductoORM`: `id_variante`, `id_producto`, `id_talla`, `id_color`, `sku`.
- `TallaORM`: `id_talla`, `codigo`, `nombre`, `orden`.
- `ColorORM`: `id_color`, `nombre`, `codigo_hex`.
- `InventarioSucursalORM`: `id_inventario`, `id_variante`, `id_sucursal`, `cantidad_disponible`.
- `PromocionORM` y `PromocionProductoORM`: Mapeo de promociones y porcentajes de descuento aplicables a productos.

### 2.2 Esquemas Pydantic (`app/modules/catalogo/cu05_consultar_catalogo/esquemas.py`)
- `ColorItemOut`: `id_color`, `nombre`, `codigo_hex`.
- `CategoriaResumenOut`: `id_categoria`, `nombre`, `total_prendas`.
- `ProductoCatalogoOut`: `id_producto`, `nombre`, `descripcion`, `precio_base`, `precio_final`, `tiene_descuento`, `porcentaje_descuento`, `imagen_url`, `categoria_id`, `categoria_nombre`, `subtitulo_atelier`, `etiqueta_badge`, `rating_promedio`, `tallas_disponibles`, `colores_disponibles`, `stock_total_disponible`, `tiene_stock`.
- `CatalogoOut`: `items`, `total_articulos`, `pagina_actual`, `limite_por_pagina`, `total_paginas`, `tiene_siguiente`, `tiene_anterior`, `resumen_categorias`, `categoria_seleccionada_id`.

### 2.3 Capa de Datos y Dominio (`repositorio.py` y `servicio.py`)
- `CatalogoRepositorio`:
  - `obtener_resumen_categorias(db)`: Consulta agregada agrupada por `id_categoria` que cuenta productos activos y calcula el total global.
  - `consultar_catalogo(db, ...)`: Carga optimizada con `selectinload(ProductoORM.categoria)` y variantes, paginación con `LIMIT` y `OFFSET`, y cálculo de promociones activas.
- `CatalogoServicio`:
  - Reglas de negocio para asignación de badges y subtítulos editoriales.
  - Validación y serialización matemática de descuentos sobre `precio_base`.

### 2.4 Endpoints REST (`app/modules/catalogo/cu05_consultar_catalogo/router.py`)
- `GET /api/v1/catalogo`: Endpoint público con parámetros `categoria_id`, `ordenar_por`, `pagina` y `limite`.
- Montado en el enrutador central `app/modules/catalogo/router.py`.

---

## 3. Arquitectura Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

### 3.1 Componente y Layout Hub (`CatalogoComponent`)
- **Ubicación:** `src/app/modules/catalogo/cu05_consultar_catalogo/paginas/catalogo.component.ts`
- **Ruta:** `/catalogo` dentro de `MainLayoutComponent` en `app.routes.ts`.
- **Navegación:**
  - Navbar superior institucional visible, destacando el enlace de Catálogo.
  - Sin botón `← Volver`.
- **Estado Reactivo con Signals:**
  - `resumenCategorias = signal<CategoriaResumenItem[]>([])`
  - `categoriaSeleccionada = signal<number | null>(null)`
  - `productos = signal<ProductoCatalogoItem[]>([])`
  - `totalArticulos = signal<number>(0)`
  - `paginaActual = signal<number>(1)`
  - `vistaColumnas = signal<'grid4' | 'grid2'>('grid4')`
  - `favoritos = signal<Set<number>>(new Set())`
- **Secciones Visuales Fieles a la Referencia:**
  1. Breadcrumbs: `FASHION STORE / CATÁLOGO / ATELIER FEMENINO`.
  2. Titular H1: *"CATÁLOGO DE PRENDAS"* con tipografía `Outfit`.
  3. Fila de chips de categorías con contadores (*"TODOS LOS PRODUCTOS (20)"*, *"VESTIDOS (5)"*, etc.).
  4. Selector de columnas (4 columnas vs 2 columnas grandes) y botón *"Filtrar y Ordenar"* enlazado a `/buscar`.
  5. Grilla de tarjetas con imagen 3:4, badges editoriales en esquina superior, botón flotante de wishlist, tallas y paleta cromática.
  6. Paginación editorial con barra de progreso y botones numéricos.
  7. Bloque editorial *"CONSERJERÍA PRIVADA DE TALLAS & FITTING"*.

---

## 4. Arquitectura Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

### 4.1 Pantalla y Componentes Mobile (`PantallaCatalogo`)
- **Ubicación:** `lib/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart`
- **Integración:** Ubicada en el **Índice 2 (`Catálogo`)** de `PantallaPrincipalHub`.
- **Navegación Hub-and-Spoke:**
  - `BottomNavigationBar` persistente visible con icono activo.
  - `AppBar` con `automaticallyImplyLeading: false` (sin botón de retroceso).
- **Gestión de Estado BLoC ([catalogo_bloc.dart](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/bloc/catalogo_bloc.dart)):**
  - Estados sellados: `CatalogoGeneralInicial`, `CatalogoGeneralCargando`, `CatalogoGeneralCargado`, `CatalogoGeneralVacio`, `CatalogoGeneralError`.
  - Deserialización segura y tolerante de tipos numéricos y cadenas `Decimal`.
- **Componentes Visuales:**
  1. AppBar con título *"Catálogo de Prendas"*.
  2. Carrusel horizontal deslizable de chips de categorías con unidades (*"Todos (20)"*, *"Vestidos (5)"*, etc.).
  3. Barra de herramientas con selector de vista (2 columnas vs 1 columna) y botón *"FILTRAR Y ORDENAR"* hacia búsqueda.
  4. Cuadrícula de 2 columnas con tarjetas de prendas, `childAspectRatio: 0.58` para evitar desbordamientos `RenderFlex`.
  5. Badges superiores, botón de wishlist con feedback táctil, tallas y paleta de colores.
  6. Paginación con botón expansor *"CARGAR MÁS PRENDAS"* y paginador numérico.
  7. Sello editorial de pie de página: *"ATELIER FLAGSHIP MADRID · PARÍS"*.

---

## 5. Matriz de Puntos de Control y Verificación (Checkpoints CP-01 a CP-18)

| ID | Capa / Módulo | Criterio de Verificación | Estado |
| :--- | :--- | :--- | :--- |
| **CP-01** | Backend API | Endpoint `GET /api/v1/catalogo` retorna código 200 con payload `CatalogoOut` estructurado. | 🟢 Superado |
| **CP-02** | Backend Conteo | `resumen_categorias` calcula con precisión prendas activas por categoría y total global sin queries N+1. | 🟢 Superado |
| **CP-03** | Backend Filtrado | Filtrado por `categoria_id` restringe los productos únicamente a la categoría solicitada. | 🟢 Superado |
| **CP-04** | Backend Empty State | Consulta con categoría sin prendas retorna 200 con lista vacía y metadatos consistentes. | 🟢 Superado |
| **CP-05** | Backend Paginación | Paginación calcula correctamente `total_paginas`, `tiene_siguiente` y `tiene_anterior`. | 🟢 Superado |
| **CP-06** | Frontend Layout | `/catalogo` se renderiza dentro de `MainLayoutComponent` con barra de navegación superior visible. | 🟢 Superado |
| **CP-07** | Frontend Nav Hub | Prohibido cualquier botón de regreso (`← Volver`) en `/catalogo`, cumpliendo la directriz Hub-and-Spoke. | 🟢 Superado |
| **CP-08** | Frontend Chips | Chips superiores con contadores numéricos filtran reactivamente las prendas mediante Signals. | 🟢 Superado |
| **CP-09** | Frontend Botón Filtro | Botón "Filtrar y Ordenar" redirige a `/buscar` (CU06). | 🟢 Superado |
| **CP-10** | Frontend Tarjetas | Grilla reproduce diseño editorial: badges, wishlist, tallas, dots de color y precio en EUR. | 🟢 Superado |
| **CP-11** | Frontend Build | Compilación de producción limpia sin errores TypeScript (`npm run build`). | 🟢 Superado |
| **CP-12** | Mobile Hub | Pestaña Catálogo en `PantallaPrincipalHub` mantiene visible el `BottomNavigationBar` en el índice 2. | 🟢 Superado |
| **CP-13** | Mobile Nav Hub | AppBar de `PantallaCatalogo` tiene `automaticallyImplyLeading: false` (sin botón de retroceso). | 🟢 Superado |
| **CP-14** | Mobile Chips & Grid | Chips móviles filtran reactivamente la cuadrícula de 2 columnas con tarjetas y badges editoriales. | 🟢 Superado |
| **CP-15** | Mobile Paginación | Botón expansor "CARGAR MÁS PRENDAS" y paginación numerada funcionan fluidamente. | 🟢 Superado |
| **CP-16** | Mobile Static Analysis | Código Flutter estricto, sin advertencias (`flutter analyze` 0 issues). | 🟢 Superado |
| **CP-17** | Catálogo Femenino | 100% prendas y modelos de moda femenina exclusiva en todas las capas; cero contenido masculino. | 🟢 Superado |
| **CP-18** | Integridad de BD Real | Todas las prendas provienen estrictamente de `fashionstore.productos` en Neon PostgreSQL. | 🟢 Superado |

---

## 6. Registro de Métricas y Aprobación de Pruebas

| Capa | Comando | Cobertura / Resultado |
| :--- | :--- | :--- |
| **Backend** | `pytest tests/modules/catalogo/test_cu05_catalogo.py` | **7/7 PASSED** (107/107 en suite global) |
| **Frontend Web** | `ng test --watch=false` | **86/86 PASSED** (14 suites unitarias) |
| **Frontend Build** | `npm run build` | **0 errores** (Bundle de producción listo) |
| **Mobile Tests** | `flutter test` | **86/86 PASSED** (9 tests de CU05) |
| **Mobile Linter** | `flutter analyze` | **0 issues** (Análisis estático limpio) |
