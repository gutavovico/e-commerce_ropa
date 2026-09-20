# Plan de Ejecución Secuencial: CU06 - Buscar y Filtrar Productos

**ID del Cambio:** `CU06-buscar-filtrar-productos`  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estrategia:** Ejecución en 3 Bloques Secuenciales con Gate de Aprobación Previo  
**Estado General:** 🟢 Completado y Verificado al 100% (Promovido a Permanente)  

---

## 1. Estrategia General y Dependencias
El flujo de desarrollo se estructuró de abajo hacia arriba en la pila arquitectónica:
1. **Bloque 1: Backend** estableció la verdad de los datos, las consultas dinámicas en PostgreSQL Neon, el motor semántico de búsqueda y los endpoints REST estables.
2. **Bloque 2: Frontend Web** implementó el servicio HTTP, maquetación exacta según la captura Desktop, confirmación explícita con botón `BUSCAR` y Enter, limpieza de input, sincronización de query params en URL y unificación de cabeceras.
3. **Bloque 3: Mobile** implementó la capa de datos en Flutter, BLoC reactivo sellado y los widgets adaptados a la captura Mobile con BottomSheet, 16 colores textiles y GridView de 2 columnas.

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: BACKEND (FastAPI + SQLAlchemy + PostgreSQL Neon)   │
│ - Modelos ORM del Catálogo en app/modules/catalogo/         │
│ - Esquemas Pydantic y ServicioBuscarFiltro normalizado      │
│ - Router con endpoints GET /productos y filtros-disponibles │
│ - Suite completa de pruebas en Pytest (83/83 pasando)       │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: FRONTEND WEB (Angular 19+ Standalone)               │
│ - Servicio CatalogoService y modelos TypeScript             │
│ - Componente de búsqueda y filtros refinados según captura  │
│ - Sincronización bidireccional con Query Params en URL      │
│ - Botón BUSCAR + Enter con vaciado y borrador diferido      │
│ - Tests en Vitest (41/41 pasando) y bundle limpio en build  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: MOBILE (Flutter 3.x + BLoC)                         │
│ - Datasource remoto y repositorio de catálogo               │
│ - CatalogoBloc con estados sellados y modo borrador         │
│ - PantallaBuscarProductos según captura Mobile (GridView)   │
│ - Modal BottomSheet de filtros, 16 colores y tests widgets  │
│ - Tests en flutter test (56/56 pasando) y 0 linter issues   │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Detalle de Bloques de Ejecución

### Bloque 1: Backend (`Ec-backend`)
1. **Modelos ORM:**
   - Creado `app/modules/catalogo/modelos.py` mapeando `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `ProductoORM`, `VarianteProductoORM`, `InventarioSucursalORM`.
2. **Esquemas Pydantic:**
   - Creado `app/modules/catalogo/cu06_buscar_filtrar/esquemas.py` con validaciones de rango y schemas de paginación.
3. **Lógica de Negocio y Persistencia:**
   - Creado `ServicioBuscarFiltro` en `app/modules/catalogo/cu06_buscar_filtrar/servicio.py` con queries dinámicas optimizadas (`ILIKE`, `pg_trgm`, joins y conteos independientes), soporte para palabras sueltas, reconocimiento de categorías y normalización sin tildes ni mayúsculas.
4. **Capa HTTP y Rutas:**
   - Creado `app/modules/catalogo/cu06_buscar_filtrar/router.py` y registrado en `app/main.py`.
5. **Verificación Automatizada:**
   - Creado `tests/modules/catalogo/test_cu06_buscar_filtrar.py` cubriendo todos los escenarios (20/20 tests de catálogo, 83/83 suite completa).

### Bloque 2: Frontend Web (`Ec-frontend`)
1. **Modelos y Servicio HTTP:**
   - Creadas interfaces y `CatalogoService` en `src/app/modules/catalogo/`.
2. **Componente de Búsqueda y Filtros:**
   - Creado `BuscarProductosComponent` maquetando con Tailwind CSS:
     - Header de exploración y breadcrumbs con tags VIP.
     - Barra de búsqueda con botón de confirmación `BUSCAR`, soporte para tecla `Enter`, botón `✕` para limpiar texto y limpieza automática de la barra tras confirmar.
     - Tipografía estandarizada del Design System en "Visto recientemente" (Outfit `font-sans font-semibold tracking-tight` en lugar de cursiva).
     - Chips de temporadas.
     - Sidebar de filtros refinados (línea/colección, tallas cuadradas, swatches de 16 colores textiles, slider de precios y botón `APLICAR FILTROS`).
     - Grilla de 4 columnas de tarjetas de producto con badges y botón `+ CESTA`.
     - Paginador con botones de navegación.
     - Píldoras de búsquedas frecuentes con ejecución directa.
     - Footer Haute Couture.
3. **Sincronización con URL y Estado Diferido (Modo Borrador):**
   - Lectura y escritura de `ActivatedRoute.queryParams` para persistencia del estado de filtros.
   - **Filtros 100% Opcionales:** Al ingresar sin query params, se despliega el catálogo completo sin restricciones de colección, talla o color preseleccionadas.
   - **Filtros Diferidos (Modo Borrador):** Antes de confirmar la búsqueda, la selección de temporadas, colecciones, tallas o colores no ejecuta consultas ni altera la URL hasta pulsar `BUSCAR` (o presionar `Enter`).
   - **Paleta Textil Extendida:** Exposición de 16 tonalidades de confección femenina (Marfil, Blanco Puro, Camel, Beige Arena, Ébano, Champagne, Borgoña, Terracota, Azul Marino, Verde Oliva, Esmeralda, Rosa Palo, Malva, Rojo Carmín, Gris Perla, Ocre).
   - **Estilismo Femenino Exclusivo:** Sustitución de cualquier imagen masculina por modelos de alta costura femenina.
   - **Alineación Visual Web:** Unificación de contenedor a `max-w-[1440px] px-6` en `/perfil` y `/buscar`, y regla `scrollbar-gutter: stable;` en `styles.scss` para suprimir saltos visuales.
4. **Verificación:**
   - `ng test` (41/41 pruebas pasando, 17/17 de CU06) y `npm run build` completado limpiamente (0 errores).

### Bloque 3: Mobile (`Ec-mobile`)
1. **Modelos y Datasource:**
   - Creados DTOs inmutables (`ProductoItemDto`, `VarianteResumenDto`, `PaginacionDto`, `FiltrosDisponiblesDto`, `ProductoPaginadoDto`).
   - Implementado `CatalogoRemotoDatasource` consumiendo `GET /api/v1/productos` y `GET /api/v1/catalogo/filtros-disponibles` con cliente `http` y mapeo de excepciones `CatalogoExcepcion`.
   - Implementado `CatalogoRepositorio` y `CatalogoRepositorioImpl`.
2. **BLoC de Catálogo:**
   - Implementado `CatalogoBloc` con estados sellados (`CatalogoInicial`, `CatalogoCargando`, `CatalogoCargado`, `CatalogoError`).
   - Sincronización de filtros diferidos en borrador y confirmación explícita mediante botón `BUSCAR` o teclado.
   - Limpieza automática del input al confirmar, preservando el término activo en badge editorial.
   - Paleta textil de 16 colores, gestión de favoritos reactiva y búsquedas frecuentes.
3. **Pantalla y Widgets:**
   - Creada `PantallaBuscarProductos` reproduciendo pixel-perfect la captura Mobile:
     - Cabecera institucional `FASHION STORE / Buscar` con avatar circular.
     - Barra de búsqueda táctil con botón de confirmación `BUSCAR` y botón de filtros con indicador de estado.
     - Carrusel horizontal de temporadas con píldora activa negra.
     - Sección `FILTROS REFINADOS` con botón `RESTABLECER`, chips de colecciones, tallas cuadradas y 16 muestras circulares de colores textiles.
     - Cabecera de resultados `Visto recientemente` en tipografía Outfit estándar del Design System (sin cursiva) con contador `(X prendas)` y botón `LIMPIAR HISTORIAL`.
     - `GridView` de 2 columnas con tarjetas de prendas de alta costura, badges editoriales, botón circular de favoritos con corazón, subtítulo atelier, precio y botón `+ CESTA`.
     - Píldoras inferiores de búsquedas más frecuentes con icono de lupa.
     - Modal BottomSheet para filtros avanzados (slider de rango de precios `0 € - 2.500 €` y ordenamiento).
     - Conexión del tab `Buscar` en el `BottomNavigationBar`.
4. **Verificación:**
   - `flutter test` (56/56 pruebas pasando, 10 unitarias de bloc + 4 de widgets) y `flutter analyze` (0 issues encontrados).
