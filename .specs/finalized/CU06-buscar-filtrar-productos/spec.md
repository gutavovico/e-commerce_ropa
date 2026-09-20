# Especificación Formal: CU06 - Buscar y Filtrar Productos

**ID del Caso de Uso:** CU06  
**Nombre:** Buscar y Filtrar Productos  
**Paquete:** `catalogo` (Catálogo y Exploración)  
**Actores:** Cliente (Registrado y Visitante Anónimo)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Feature Típica de Catálogo con Optimización Trigram)  
**Estado:** 🟢 Aprobado y Promovido a Permanente  

---

## 1. Alcance y Fuentes de Verdad
1. **Documento de Requisitos y Análisis:** `SI2-Parcial1.md` (Líneas 509-510, 969-985, 101-105 y 2942-3028).
2. **Fuente Visual Frontend Web:** Imagen adjunta de referencia Desktop (Haute Couture Atelier, grilla de 4 columnas, sidebar de filtros refinados, chips de temporadas y búsquedas frecuentes).
3. **Fuente Visual Mobile:** Imagen adjunta de referencia Mobile (Fila deslizable de temporadas, chips de línea/talla/color, GridView de 2 columnas, modal BottomSheet y búsqueda táctil).

---

## 2. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 2.1 Modelo Relacional y de Persistencia
Mapeo sobre esquema `fashionstore` (tablas ya existentes en Neon DB generadas por `0001_base_ddl.py`):
- `CategoriaORM` (`fashionstore.categorias`): `id_categoria`, `nombre`, `id_categoria_padre`.
- `TemporadaORM` (`fashionstore.temporadas`): `id_temporada`, `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `activa`.
- `ColeccionORM` (`fashionstore.colecciones`): `id_coleccion`, `id_temporada`, `nombre`, `descripcion`.
- `TallaORM` (`fashionstore.tallas`): `id_talla`, `codigo`, `orden`.
- `ColorORM` (`fashionstore.colores`): `id_color`, `nombre`, `codigo_hex`.
- `ProductoORM` (`fashionstore.productos`): `id_producto`, `id_categoria`, `id_coleccion`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `modelo_ar_url`, `activo`, `creado_en`.
- `VarianteProductoORM` (`fashionstore.variantes_producto`): `id_variante`, `id_producto`, `id_talla`, `id_color`, `sku`, `precio_extra`.
- `InventarioSucursalORM` (`fashionstore.inventario_sucursal`): `id_inventario`, `id_variante`, `id_sucursal`, `cantidad_disponible`, `cantidad_reservada`, `estado`.
- **Índice de Rendimiento:** `idx_productos_nombre_trgm` (GIN sobre `nombre gin_trgm_ops`).

### 2.2 Contratos de Endpoints HTTP

#### 1. `GET /api/v1/productos`
- **Propósito:** Búsqueda flexible multimodal y paginada de productos con filtros combinables 100% opcionales.
- **Normalización y Búsqueda Multicriterio (`q`):**
  - Insensible a mayúsculas y minúsculas (`func.lower(...)`).
  - Coincidencia difusa (`pg_trgm`) y por subcadenas (`LIKE %q%`).
  - Cobertura integral: busca simultáneamente en `nombre`, `descripcion`, `categoria`, `coleccion` y `temporada`.
- **Enfoque de Catálogo:**
  - Moda femenina de alta costura exclusiva.
- **Parámetros Query (Todos Opcionales):**
  - `q`: Término de búsqueda libre o palabras sueltas (insensible a mayúsculas/minúsculas, tildes, variantes morfológicas singular/plural y sinónimos textiles; coteja sobre nombre, descripción, categoría, colección, temporada y colores).
  - `temporada_id`: Entero positivo (opcional).
  - `coleccion_id`: Entero positivo (opcional).
  - `categoria_id`: Entero positivo (opcional).
  - `talla`: Código de talla (e.g. `"38"`, `"40"`).
  - `color`: Nombre de color de ropa dentro de la paleta textil extendida de 16 tonalidades.
  - `precio_min`: Decimal no negativo (opcional).
  - `precio_max`: Decimal no negativo (`precio_max >= precio_min`) (opcional).
  - `solo_en_stock`: Booleano (default `false` para visualización íntegra de catálogo).
  - `ordenar_por`: `"recientes" | "precio_asc" | "precio_desc" | "nombre_asc" | "relevancia"`.
  - `pagina`: Entero `>= 1` (default `1`).
  - `limite`: Entero entre `1` y `50` (default `12`).
- **Respuesta 200 OK:**
  ```json
  {
    "items": [
      {
        "id_producto": 1,
        "nombre": "Vestido plisado seda",
        "descripcion": "Vestido de alta costura largo plisado confeccionado en pura seda rojo carmín.",
        "categoria": "Vestidos",
        "coleccion": "Alta Costura",
        "temporada": "Otoño / Invierno 2024",
        "precio_base": "890.00",
        "imagen_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop&q=80",
        "modelo_ar_url": null,
        "activo": true,
        "badge_editorial": "ED. LIMITADA 12/50",
        "subtitulo_atelier": "ALTA COSTURA",
        "talla_sugerida": "Talla 38",
        "color_sugerido": "Rojo Carmín",
        "variantes": [
          {
            "id_variante": 1,
            "sku": "VES-PLI-38-ROJ",
            "talla": "38",
            "color": "Rojo Carmín",
            "codigo_hex": "#991B1B",
            "precio_extra": "0.00",
            "disponible": true
          }
        ]
      }
    ],
    "paginacion": {
      "total_registros": 32,
      "pagina_actual": 1,
      "limite": 12,
      "total_paginas": 3,
      "tiene_siguiente": true,
      "tiene_anterior": false
    },
    "filtros_aplicados": {
      "q": "vestido",
      "talla": "38"
    }
  }
  ```

#### 2. `GET /api/v1/catalogo/filtros-disponibles`
- **Propósito:** Entrega el árbol de opciones de filtrado disponible para inicializar sidebar y chips en frontends.
- **Respuesta 200 OK:** Lista de temporadas activas, colecciones con conteo de prendas, tallas disponibles, colores con código hex y rango de precios mínimo/máximo existente.

#### 3. `POST /api/v1/catalogo/buscar`
- **Propósito:** Endpoint de compatibilidad directa con las pruebas formales documentadas en `SI2-Parcial1.md` (Línea 2950).
- **Body:** `{"termino_busqueda": str, "filtros": {...}}`.

### 2.3 Criterios de Aceptación (Gherkin)
- Coincidencia difusa con tolerancia a errores ortográficos menores vía `pg_trgm`.
- Filtrado simultáneo de múltiples criterios con operador `AND`.
- Paginación exacta sin duplicación de filas.
- Manejo de excepciones: `422 Unprocessable Entity` si los filtros contienen valores ilegales.

---

## 3. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Estructura Visual
- **Barra de Navegación:** Enlace activo `BUSCAR`.
- **Cabecera y Breadcrumb:** `FASHION STORE / BÚSQUEDA & EXPLORACIÓN / PRENDAS` + `• Atelier Serrano Online • Citas Disponibles Hoy` + `ACCESO CLIENTE VIP`.
- **Search Input con Botón de Confirmación:** Input con icono de lupa, placeholder dinámico `Vestidos, sastrería y sedas nobles` (o recordatorio de filtro activo), botón `✕` para limpiar campo, y botón explícito `BUSCAR` con icono de flecha. Soporte para tecla `Enter`.
- **Selector de Temporadas:** Pills horizontales: `Todas las temporadas`, `Otoño / Invierno 2024 •` (activo), `Primavera / Verano 2025`, `Cápsula Edición Limitada`.
- **Sidebar de Filtros Refinados:**
  - Botón de acción rápida `RESTABLECER`.
  - Checkboxes de Colección & Línea con contador individual (`Sastrería Atelier (12)`, etc.).
  - Selector de Tallas tipo botón cuadrado con enlace `GUÍA ATELIER`.
  - Muestrario de Colores con círculo de tono y código hexadecimal (paleta extendida de 16 tonalidades).
  - Slider de Inversión (`0 € - 2.500 €`).
  - Botón de confirmación `APLICAR FILTROS` en la base del sidebar.
- **Grilla de Prendas (4 Columnas):**
  - Titular `Visto recientemente` en tipografía estándar del Design System (Outfit `font-sans font-semibold tracking-tight`), acompañado del contador de prendas y badge de búsqueda activa con opción de descarte `✕`.
  - Tarjetas estilizadas con foto de alta costura femenina, tags editoriales (`ED. LIMITADA 12/50`, `EN SERRANO`, `SEDA PURA`), botón flotante de wishlist (corazón), subtítulo en mayúsculas, título, precio, color sugerido y botón `+ CESTA`.
- **Paginador:** `Mostrando X de Y piezas de sastrería seleccionadas`, botones `ANTERIOR`, `1`, `2`, `3`, `SIGUIENTE`.
- **Píldoras de Tendencias:** `↗ BÚSQUEDAS MÁS FRECUENTES` (`Vestidos de seda ↗`, etc.) que confirman y ejecutan la búsqueda de forma directa.
- **Footer Completo:** Boutiques, sostenibilidad y boletín editorial.

### 3.2 Lógica Reactiva y Confirmación Diferida (Modo Borrador)
- Inyección de `CatalogoService` consumiendo `/api/v1/productos`.
- **Diferimiento de filtros:** La selección de temporadas, colecciones, tallas, colores, precio o texto de búsqueda NO dispara peticiones HTTP inmediatamente; se mantienen en estado de borrador reactivo hasta que el usuario confirma.
- **Mecanismos de Confirmación:** Clic en botón `BUSCAR` de la barra, tecla `Enter` en el input o clic en `APLICAR FILTROS` del sidebar.
- **Ejecución por Confirmación:** Búsqueda bajo demanda (sin disparos automáticos mientras se escribe) accionada por botón `BUSCAR` o tecla `Enter`.
- **Limpieza de Barra al Confirmar:** Al confirmar, el texto de la barra de búsqueda se limpia automáticamente, guardando el término activo en el estado y en los Query Params de la URL, y mostrándolo como badge editorial en los resultados con botón de descarte `✕`.
- Sincronización continua de filtros con los Query Params de la URL para persistencia de estado ante recarga o navegación hacia atrás.

---

## 4. Bloque 3: Mobile (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Experiencia Móvil Adaptada
- **AppBar:** Cabecera institucional de lujo `FASHION STORE / Buscar` con avatar circular de cliente a la derecha.
- **Búsqueda Táctil con Confirmación:** Input redondeado con icono de lupa, placeholder `Buscar vestidos, blazers, tejidos...`, botón `✕` para limpiar texto, botón explícito `BUSCAR` con estilo de alto contraste, soporte de confirmación por teclado (`TextInputAction.search`), limpieza automática de la barra tras confirmar y botón de filtros con indicador reactivo si hay filtros aplicados.
- **Carrusel Horizontal de Temporadas:** Desplazamiento horizontal con chips de alta costura: `TODAS LAS TEMPORADAS`, `OTOÑO / INVIERNO` (activo en negro con texto blanco), etc.
- **Sección `FILTROS REFINADOS`:**
  - Botón de acción rápida `RESTABLECER`.
  - Fila de Línea/Colección (`Sastrería Atelier`, `Esenciales`, `Alta Costura`, `Seda Natural Pura`).
  - Fila de Tallas cuadradas (`36`, `38`, `40`, `42`, `44`, `Única`).
  - Fila de Colores con muestras circulares bordeadas (paleta textil de 16 tonalidades).
- **Cabecera de Resultados:** `Visto recientemente (X prendas)` en tipografía estándar Outfit del Design System (sin cursiva), botón `LIMPIAR HISTORIAL` y badge editorial del término de búsqueda activo con botón de descarte `✕`.
- **GridView (2 Columnas):** Tarjetas verticales editoriales con foto de alta costura femenina, badge superior (`EDICIÓN LIMITADA`, `EN SERRANO`), botón circular flotante de favoritos con icono de corazón, subtítulo de atelier en mayúsculas, título de prenda en negrita, talla/color y fila con precio en negrita y botón `+ CESTA`.
- **Modal BottomSheet:** Filtros avanzados con doble deslizador de rango de inversión (`0 € - 2.500 €`), dropdown de ordenamiento y botones `APLICAR FILTROS` y `LIMPIAR TODO`.
- **Búsquedas Frecuentes:** Chips inferiores con icono de lupa que ejecutan y confirman la búsqueda directamente.
- **BottomNavigationBar:** Barra institucional inferior con 4 destinos (`Inicio`, `Buscar` activo, `Catálogo`, `Perfil`).

### 4.2 Arquitectura BLoC
- `CatalogoBloc`: Manejo inmutable y reactivo con estados sellados (`CatalogoInicial`, `CatalogoCargando`, `CatalogoCargado`, `CatalogoError`).
- Modo de confirmación explícita (modo borrador): los filtros y términos no disparan peticiones prematuras hasta que el usuario confirma con `BUSCAR`, tecla de teclado o selección directa.
- Limpieza automática del input preservando el término activo en badge editorial.
- Gestión de favoritos y catálogo 100% opcional por defecto.
