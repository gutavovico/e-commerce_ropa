# Especificación Técnica Permanente: CU06 - Buscar y Filtrar Productos

**Código:** CU06  
**Nombre:** Buscar y Filtrar Productos (Catálogo Omnicanal de Alta Costura Femenina)  
**Paquete de Dominio:** `catalogo_productos`  
**Directorio Funcional:** `cu06_buscar_filtrar`  
**Actores:** Cliente (Registrado y Visitante Anónimo)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Línea Base Permanente)  
**Estado:** 🟢 Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Líneas 509-510, 969-985, 2942-3028: Catálogo, prendas, variantes, temporadas, colecciones, stock por sucursal).
- Referencia Visual y UX Web: Captura de referencia Desktop Haute Couture Atelier (sidebar de filtros refinados, grilla de 4 columnas, chips de temporadas, botón `BUSCAR` con Enter y borrador diferido, badge editorial dismissible).
- Referencia Visual y UX Mobile: Captura de referencia Mobile Atelier (carrusel de temporadas horizontal, chips de línea/talla/color, `GridView` de 2 columnas, modal BottomSheet de rango y orden, búsqueda con botón `BUSCAR` y vaciado de barra).
- Design System: Tipografía corporativa `Outfit` (`font-sans font-semibold tracking-tight`), paleta cromática textil de 16 tonalidades y catálogo exclusivamente femenino.

---

## 1. Definición Funcional y Reglas de Negocio

### 1.1 Propósito y Alcance
Proporcionar a los clientes de FashionStore (tanto usuarios anónimos como clientes VIP registrados) un motor de búsqueda y exploración omnicanal ágil, flexible y visualmente refinado, capaz de consultar el catálogo completo de prendas de alta costura, filtrar por atributos textiles (temporada, colección, talla, color, rango de inversión y disponibilidad) y preservar la fidelidad estética de la marca en entornos Web y Mobile.

### 1.2 Reglas de Negocio Estrictas

1. **Filtros 100% Opcionales (Exploración Abierta):**
   - El acceso inicial al catálogo no fuerza ningún filtro preseleccionado (colección, temporada, talla o color).
   - Una petición sin parámetros o con parámetros vacíos retorna el catálogo completo paginado ordenado por piezas más recientes.

2. **Búsqueda Flexible y Multicriterio por Palabras Sueltas:**
   - Normalización insensible a mayúsculas, minúsculas y tildes (`_normalizar_texto`).
   - Lematización morfológica y reconocimiento de variantes singular/plural y sinónimos textiles ("vestido" ↔ "vestidos", "pantalon" ↔ "pantalones", "chaqueta" ↔ "blazer", "seda", etc.).
   - Reconocimiento morfológico de categorías completas: escribir el nombre de una categoría devuelve todos los productos asociados a ella.
   - Búsqueda simultánea sobre `nombre`, `descripcion`, nombre de `categoria`, nombre de `coleccion`, nombre de `temporada` y nombre de `color`.
   - Tolerancia a errores de tipeo y coincidencia difusa vía extensión `pg_trgm` en PostgreSQL.

3. **Catálogo Exclusivamente Femenino:**
   - La totalidad de las prendas, fotografías de modelos y piezas de sastrería corresponden estrictamente a indumentaria y alta costura femenina.
   - Cualquier referencia o fotografía masculina queda excluida del catálogo público.

4. **Paleta Textil Extendida de 16 Tonalidades:**
   - El catálogo textil utiliza una paleta estandarizada de 16 colores reales de confección:
     1. Marfil (`#FDFBF7`)
     2. Blanco Puro (`#FFFFFF`)
     3. Camel (`#C19A6B`)
     4. Beige Arena (`#E8DCC4`)
     5. Ébano (`#1A1A1A`)
     6. Champagne (`#F7E7CE`)
     7. Borgoña (`#800020`)
     8. Terracota (`#E2725B`)
     9. Azul Marino (`#000080`)
     10. Verde Oliva (`#556B2F`)
     11. Esmeralda (`#50C878`)
     12. Rosa Palo (`#D8BCAB`)
     13. Malva (`#E0B0FF`)
     14. Rojo Carmín (`#991B1B`)
     15. Gris Perla (`#E5E5E5`)
     16. Ocre (`#CC7722`)
   - Prenda icónica "Vestido plisado seda" asignada con precisión a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ`.

5. **Modo Borrador Diferido y Confirmación Explícita:**
   - La selección de opciones de filtrado en el sidebar/carrusel o la escritura de caracteres en el input de búsqueda **no** dispara peticiones HTTP automáticas en caliente.
   - La búsqueda y aplicación de filtros se ejecuta única y formalmente mediante:
     a) Clic en el botón explícito `BUSCAR`.
     b) Pulsación de la tecla `Enter` en Web o acción de búsqueda del teclado táctil en Mobile.
     c) Clic en el botón `APLICAR FILTROS` del sidebar o BottomSheet.
     d) Clic en cualquiera de las píldoras de búsquedas frecuentes.
   - **Vaciado Automático del Input:** Al confirmar la búsqueda, el campo de texto se limpia automáticamente para permitir nuevas búsquedas sin fricción.
   - **Preservación en Badge Editorial:** El término activo se retiene en el estado, se refleja en los Query Params de la URL y se visualiza en un badge editorial dismissible (con botón `✕` para descarte rápido).

6. **Estandarización Tipográfica del Design System:**
   - El titular de la sección de resultados "Visto recientemente" utiliza obligatoriamente la tipografía institucional `Outfit` (`font-sans font-semibold tracking-tight`), eliminando discrepancias o estilos cursivos no corporativos.

7. **Alineación Visual y Estabilidad de Viewport:**
   - El contenedor principal en Web se unifica estrictamente a `max-w-[1440px] px-6` tanto en `/buscar` como en `/perfil`, garantizando que la barra superior institucional, avatar y enlaces mantengan una alineación milimétrica constante sin saltos laterales.
   - Adopción de la regla CSS global `scrollbar-gutter: stable;` en `styles.scss` para anular el desplazamiento horizontal de 15px derivado de la presencia o ausencia de scroll vertical.

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 2.1 Modelos ORM (`app/modules/catalogo/modelos.py`)
Mapeo sobre esquema `fashionstore`:
- `CategoriaORM`: `id_categoria`, `nombre`, `id_categoria_padre`.
- `TemporadaORM`: `id_temporada`, `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `activa`.
- `ColeccionORM`: `id_coleccion`, `id_temporada`, `nombre`, `descripcion`.
- `TallaORM`: `id_talla`, `codigo`, `orden`.
- `ColorORM`: `id_color`, `nombre`, `codigo_hex`.
- `ProductoORM`: `id_producto`, `id_categoria`, `id_coleccion`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `modelo_ar_url`, `activo`, `creado_en`.
- `VarianteProductoORM`: `id_variante`, `id_producto`, `id_talla`, `id_color`, `sku`, `precio_extra`.
- `InventarioSucursalORM`: `id_inventario`, `id_variante`, `id_sucursal`, `cantidad_disponible`, `cantidad_reservada`, `estado`.

### 2.2 Esquemas Pydantic (`app/modules/catalogo/cu06_buscar_filtrar/esquemas.py`)
- `VarianteResumenOut`: Resumen de variante con SKU, talla, color, código hex y disponibilidad en stock.
- `ProductoItemOut`: DTO del producto con atributos editoriales (`badge_editorial`, `subtitulo_atelier`, `talla_sugerida`, `color_sugerido`) y lista de variantes.
- `PaginacionMetaOut`: Metadatos de paginación (`total_registros`, `pagina_actual`, `limite`, `total_paginas`, `tiene_siguiente`, `tiene_anterior`).
- `ProductoPaginadoOut`: Envoltorio con `items`, `paginacion` y `filtros_aplicados`.
- `FiltrosDisponiblesOut`: Metadatos de opciones activas (temporadas, colecciones con conteo, tallas, 16 colores y rango min/max de precio).

### 2.3 Servicio de Búsqueda y Filtrado (`app/modules/catalogo/cu06_buscar_filtrar/servicio.py`)
- Motor de normalización `_normalizar_texto`: conversión a minúsculas y eliminación de diacríticos/tildes.
- Expansor semántico `_expandir_termino`: desglose en palabras sueltas, extracción de singular/plural para términos clave ("vestido" ↔ "vestidos", "pantalon" ↔ "pantalones", "falda" ↔ "faldas", "chaqueta" ↔ "chaquetas", "camisa" ↔ "camisas", "abrigo" ↔ "abrigos", "blazer" ↔ "blazers") y sinónimos textiles.
- Construcción de filtros SQLAlchemy con operador `and_` entre diferentes dimensiones y `or_` entre atributos del mismo término para búsqueda multicriterio.
- Paginación atómica mediante `offset` y `limit` sobre subconsultas indexadas.

### 2.4 Endpoints HTTP (`app/modules/catalogo/cu06_buscar_filtrar/router.py`)
1. `GET /api/v1/productos`
   - Parámetros: `q`, `temporada_id`, `coleccion_id`, `categoria_id`, `talla`, `color`, `precio_min`, `precio_max`, `solo_en_stock`, `ordenar_por`, `pagina`, `limite`.
   - Respuesta: `ProductoPaginadoOut` (200 OK).
2. `GET /api/v1/catalogo/filtros-disponibles`
   - Respuesta: `FiltrosDisponiblesOut` (200 OK).
3. `POST /api/v1/catalogo/buscar`
   - Body: `{"termino_busqueda": str, "filtros": {...}}`.
   - Endpoint de compatibilidad directa con las pruebas formales PUDS de `SI2-Parcial1.md`.

---

## 3. Arquitectura de Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Modelos y Servicios
- `src/app/modules/catalogo/modelos/catalogo.modelos.ts`: Interfaces tipadas para producto, variante, filtros y paginación.
- `src/app/modules/catalogo/servicios/catalogo.service.ts`: Cliente HTTP inyectable que invoca `/api/v1/productos` y `/api/v1/catalogo/filtros-disponibles`.

### 3.2 Componente `BuscarProductosComponent`
- Ruta: `/buscar` (asociada en `app.routes.ts` y enlazada en la cabecera principal).
- **Barra de Búsqueda de Alto Rendimiento:**
  - Input estilizado con botón `✕` para limpiar campo.
  - Botón explícito `BUSCAR` con icono de flecha.
  - Evento `(keyup.enter)` y `(click)="ejecutarBusquedaPorBoton()"`.
  - Vaciado automático del input tras la confirmación, preservando el término activo en el badge editorial.
- **Filtros en Modo Borrador:**
  - Sidebar con checkboxes de colecciones, botones cuadrados de tallas, swatches de 16 colores y slider de rango de inversión.
  - La selección actualiza el borrador local sin consultar la API hasta pulsar `APLICAR FILTROS` o `BUSCAR`.
  - Botón `RESTABLECER` para retornar al estado de catálogo abierto.
- **Grilla de 4 Columnas:**
  - Cabecera editorial con tipografía Outfit para "Visto recientemente", contador de prendas y badge dismissible de búsqueda activa.
  - Tarjetas con fotografía femenina de alta costura, badges editoriales (`EDICIÓN LIMITADA`, `EN SERRANO`), botón wishlist (corazón), tallas/colores sugeridos y botón interactivo `+ CESTA`.
- **Sincronización Bidireccional de URL:**
  - Los filtros confirmados se serializan en los Query Params (`ActivatedRoute`), permitiendo compartir búsquedas o recargar la página sin perder el contexto.

---

## 4. Arquitectura de Mobile (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Modelos y Capa de Datos
- `producto_item_dto.dart`, `variante_resumen_dto.dart`, `paginacion_dto.dart`, `filtros_disponibles_dto.dart`, `producto_paginado_dto.dart`.
- `CatalogoRemotoDatasource`: Cliente HTTP con manejo de errores y transformación de JSON a DTOs inmutables.
- `CatalogoRepositorio` / `CatalogoRepositorioImpl`: Abstracción de dominio para desacoplamiento de fuentes de datos.

### 4.2 BLoC Reactivo (`CatalogoBloc`)
- Estados sellados (`sealed class CatalogoEstado`): `CatalogoInicial`, `CatalogoCargando`, `CatalogoCargado`, `CatalogoError`.
- Eventos: `CargarCatalogoInicialEvent`, `ConfirmarBusquedaEvent`, `ModificarBorradorFiltroEvent`, `AplicarFiltrosEvent`, `LimpiarFiltrosEvent`, `AlternarFavoritoEvent`.
- Modo borrador: los cambios en filtros no disparan redibujados costosos ni peticiones HTTP hasta su confirmación explícita.
- Vaciado automático del `TextEditingController` de búsqueda tras confirmar.

### 4.3 Pantalla y Widgets (`PantallaBuscarProductos`)
- **AppBar de Lujo:** `FASHION STORE / Buscar` con avatar circular VIP.
- **Barra de Búsqueda Táctil:** Input estilizado con botón `✕` de limpieza rápida, botón `BUSCAR` explícito, soporte de teclado (`TextInputAction.search`) y botón de filtros con indicador badge.
- **Carrusel Horizontal de Temporadas:** Chips deslizables con alta costura (`TODAS LAS TEMPORADAS`, `OTOÑO / INVIERNO`, etc.).
- **Filtros Refinados:** Fila horizontal de colecciones, tallas cuadradas y 16 muestras circulares de colores textiles con botón `RESTABLECER`.
- **Cabecera de Resultados:** "Visto recientemente" en tipografía corporativa Outfit (sin cursiva) con contador de prendas y botón `LIMPIAR HISTORIAL`.
- **GridView de 2 Columnas:** Tarjetas de prendas con proporción editorial, badge superior, botón de favoritos flotante con icono de corazón, precio y botón `+ CESTA`.
- **BottomSheet Modal:** Filtros avanzados con doble deslizador de rango de inversión (`0 € - 2.500 €`), selector de ordenamiento y botones de acción rápida.
- **Búsquedas Frecuentes:** Chips inferiores con icono de lupa que confirman y ejecutan la búsqueda directamente.
- **BottomNavigationBar:** Integración en la barra de navegación de la app (`Buscar` activo).

---

## 5. Matriz de Validación y Cobertura de Pruebas

| Capa | Herramienta | Pruebas Ejecutadas | Resultado |
| :--- | :--- | :--- | :--- |
| **Backend** | `pytest` | 20 pruebas específicas de catálogo (83 acumuladas en suite) | 🟢 100% Pasando (0 fallos) |
| **Frontend Web** | Vitest / Angular CLI | 17 pruebas de catálogo (41 acumuladas en suite) | 🟢 100% Pasando (0 fallos) |
| **Frontend Build**| `npm run build` | Bundle completo compilado en modo producción | 🟢 Exitoso (0 errores, chunk perezoso generado) |
| **Mobile Tests** | `flutter test` | 14 pruebas de catálogo (56 acumuladas en suite) | 🟢 100% Pasando (0 fallos) |
| **Mobile Linter** | `flutter analyze` | Análisis estático completo de la base de código Dart | 🟢 0 incidencias (No issues found) |

---

## 6. Historial de Decisiones de Diseño y Refinamientos

1. **Apertura Inicial sin Filtros Forzados:**
   - La especificación original contemplaba filtros por defecto restrictivos; se corrigió para que el catálogo sea 100% opcional, permitiendo visualizar la totalidad de prendas sin barreras de entrada.
2. **Reconocimiento Morfológico y Semántico:**
   - Búsquedas por términos generales o categorías ("vestido", "vestidos", "chaqueta", etc.) resuelven morfológicamente contra nombres, descripciones y tablas maestras de categorías simultáneamente sin fallar por coincidencia literal estricta.
3. **Corrección de Color Vestido Plisado:**
   - El producto "Vestido plisado seda" se corrigió de tono mármol a "Rojo Carmín" (`#991B1B`), con actualización en base de datos, SKU e imágenes de referencia.
4. **Paleta Textil de 16 Colores:**
   - Se extendió el muestrario de colores a 16 tonalidades de confección textil real, eliminando paletas sintéticas genéricas.
5. **Tipografía Unificada Outfit:**
   - Se estandarizó la tipografía del titular "Visto recientemente" al Design System corporativo (`Outfit font-sans font-semibold tracking-tight`), erradicando variantes cursivas o fuentes serif no conformes.
6. **Búsqueda Confirmada y Barra Limpia:**
   - Adopción del botón `BUSCAR` con Enter y vaciado automático de la barra, mostrando el término confirmado en un badge editorial dismissible.
7. **Alineación Visual Web:**
   - Unificación de contenedores a `max-w-[1440px] px-6` y adopción de `scrollbar-gutter: stable;` en `styles.scss` para eliminar saltos de ancho o desalineación de la cabecera al navegar entre `/buscar` y `/perfil`.
