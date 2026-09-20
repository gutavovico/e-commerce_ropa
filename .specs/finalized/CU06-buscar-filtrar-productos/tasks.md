# Lista de Tareas Atómicas: CU06 - Buscar y Filtrar Productos

**ID del Cambio:** `CU06-buscar-filtrar-productos`  
**Estado General:** 🟢 Implementado y Verificado al 100% (Promovido a Permanente)  

---

## Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy + PostgreSQL)
- [x] **B1.1**: Crear `app/modules/catalogo/modelos.py` con mapeo ORM completo de catálogo (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`).
- [x] **B1.2**: Implementar esquemas Pydantic en `app/modules/catalogo/cu06_buscar_filtrar/esquemas.py` (`VarianteResumenOut`, `ProductoItemOut`, `PaginacionMetaOut`, `ProductoPaginadoOut`, `FiltrosDisponiblesOut`).
- [x] **B1.3**: Implementar `ServicioBuscarFiltro` en `app/modules/catalogo/cu06_buscar_filtrar/servicio.py` con consultas dinámicas SQLAlchemy 2.0, coincidencia difusa trigram y conteo eficiente.
- [x] **B1.4**: Crear endpoints en `app/modules/catalogo/cu06_buscar_filtrar/router.py`:
  - `GET /api/v1/productos`
  - `GET /api/v1/catalogo/filtros-disponibles`
  - `POST /api/v1/catalogo/buscar`
- [x] **B1.5**: Registrar router en `app/main.py`.
- [x] **B1.6**: Escribir pruebas unitarias e integración en `tests/modules/catalogo/test_cu06_buscar_filtrar.py` y validar con `pytest` (100% pasando: 20/20 tests de CU06, 83/83 suite completa).
- [x] **B1.7**: Implementar búsqueda flexible multimodal en `ServicioBuscarFiltro` normalizando a minúsculas y buscando en simultáneo sobre `nombre`, `descripcion`, `categoria` y `coleccion`.
- [x] **B1.8**: Actualizar semilla y base de datos con catálogo exclusivamente femenino (sustituyendo modelo masculino por modelo femenina en blusa de satén) y expandiendo la tabla de colores a 16 tonalidades de confección textil.
- [x] **B1.9**: Corrección cromática de "Vestido plisado seda": actualización en BD y migración a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ` y descripción textil en seda carmín.
- [x] **B1.10**: Motor de búsqueda morfológico y semántico por palabras sueltas (`_normalizar_texto`, `_expandir_termino`, sinónimos de moda, singular/plural e insensibilidad a tildes/mayúsculas) para reconocimiento exacto de categorías ("vestidos", "pantalones", "faldas", "chaquetas", "camisas") y atributos cruzados sin error 500.

---

## Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)
- [x] **F2.1**: Crear modelos e interfaces TypeScript en `src/app/modules/catalogo/modelos/catalogo.modelos.ts`.
- [x] **F2.2**: Implementar servicio `CatalogoService` en `src/app/modules/catalogo/servicios/catalogo.service.ts`.
- [x] **F2.3**: Crear componente `BuscarProductosComponent` maquetando con Tailwind CSS según la captura Desktop:
  - Header de exploración y breadcrumbs.
  - Barra de búsqueda con debounce de 300ms y botón `✕`.
  - Selector superior de temporadas (chips horizontales).
  - Sidebar izquierdo de filtros (Colecciones, Tallas, Colores, Rango de inversión).
  - Selector de orden y limpiador de historial.
  - Grilla de 4 columnas de tarjetas de producto con badges y botón `+ CESTA`.
  - Paginador atelier y píldoras de búsquedas frecuentes.
  - Footer editorial completo.
- [x] **F2.4**: Integrar sincronización bidireccional con Query Params (`ActivatedRoute` / `Router`).
- [x] **F2.5**: Configurar ruta `/buscar` en `app.routes.ts` y enlazar en navegación principal.
- [x] **F2.6**: Escribir tests unitarios `buscar-productos.component.spec.ts` y `catalogo.service.spec.ts`, validando `ng test` (100% pasando: 17/17 tests de catálogo, 41/41 suite completa) y `npm run build` sin errores.
- [x] **F2.7**: Configurar filtros como 100% opcionales por defecto (carga íntegra del catálogo sin preselección restrictiva de colección, talla o color).
- [x] **F2.8**: Integrar paleta textil de colores de confección extendida (16 tonalidades dinámicas con scroll suave y muestras circulares).
- [x] **F2.9**: Estandarización de tipografía en "Visto recientemente" según el Design System (Outfit `font-sans font-semibold tracking-tight` en lugar de `font-serif italic`).
- [x] **F2.10**: Botón de confirmación de búsqueda `BUSCAR` y soporte Enter en el input: diferimiento de ejecución de filtros hasta confirmación explícita (modo borrador), botón `APLICAR FILTROS` en sidebar y limpieza automática de la barra de búsqueda preservando el término activo en badge editorial.
- [x] **F2.11**: Estandarización de cabecera institucional y ancho de contenedor (`max-w-[1440px] px-6`) en `perfil.component.html` y regla `scrollbar-gutter: stable` en `styles.scss` para eliminar saltos visuales de alineación y discrepancias tipográficas en la barra superior al navegar entre `/buscar` y `/perfil`.

---

## Bloque 3: Mobile (`Ec-mobile` - Flutter 3.x + BLoC)
- [x] **M3.1**: Definir DTOs y modelos de datos inmutables en `lib/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/`:
  - `ProductoItemDto` y `VarianteResumenDto` en `producto_item_dto.dart`.
  - `PaginacionDto` en `paginacion_dto.dart`.
  - `FiltrosDisponiblesDto` con temporadas, colecciones, tallas, colores y rango de precios en `filtros_disponibles_dto.dart`.
  - `ProductoPaginadoDto` en `producto_paginado_dto.dart`.
- [x] **M3.2**: Implementar `CatalogoRemotoDatasource` consumiendo `GET /api/v1/productos` y `GET /api/v1/catalogo/filtros-disponibles` con manejo robusto de excepciones tipadas (`CatalogoExcepcion`), e implementar `CatalogoRepositorio` en `dominio/repositorios/`.
- [x] **M3.3**: Crear `CatalogoBloc` con estados sellados (`CatalogoInicial`, `CatalogoCargando`, `CatalogoCargado`, `CatalogoError`), filtros en borrador, confirmación explícita con botón `BUSCAR` o teclado, limpieza de input, favoritos reactivos y búsquedas frecuentes.
- [x] **M3.4**: Maquetar `PantallaBuscarProductos` según la captura Mobile y el Design System:
  - Cabecera institucional `FASHION STORE / Buscar` con avatar circular de cliente.
  - Barra de búsqueda con icono de lupa, input con limpieza automática al confirmar, botón `BUSCAR` explícito, soporte de tecla buscar de teclado y botón de filtros con badge indicador.
  - Fila horizontal deslizable de temporadas (`TODAS LAS TEMPORADAS`, `OTOÑO / INVIERNO`, etc.).
  - Sección `FILTROS REFINADOS` con `RESTABLECER`, fila de colecciones, fila de tallas cuadradas y muestrario de 16 colores textiles.
  - Cabecera de resultados `Visto recientemente` en tipografía Outfit y botón `LIMPIAR HISTORIAL`.
  - `GridView` de 2 columnas con tarjetas de alta costura femenina, badges editoriales, botón circular flotante de favoritos con corazón, precio y botón `+ CESTA`.
  - Píldoras inferiores de `BÚSQUEDAS MÁS FRECUENTES` con icono de lupa y confirmación directa.
  - Modal BottomSheet para filtros avanzados (doble slider de rango de inversión `0 € - 2.500 €` y dropdown de ordenamiento).
- [x] **M3.5**: Conectar destino `Buscar` en el `BottomNavigationBar` de `pantalla_perfil.dart` permitiendo navegación fluida a `PantallaBuscarProductos`.
- [x] **M3.6**: Escribir tests unitarios y de widgets (`catalogo_bloc_test.dart`, `pantalla_buscar_test.dart`) y verificar `flutter test` (100% pasando: 56/56 tests) y `flutter analyze` (0 issues encontrados).
