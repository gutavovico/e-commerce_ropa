# Propuesta de Cambio Técnico: CU06 - Buscar y Filtrar Productos

**ID del Cambio:** `CU06-buscar-filtrar-productos`  
**Caso de Uso:** CU06 - Buscar y Filtrar Productos  
**Paquete de Dominio:** `catalogo` (Catálogo y Exploración)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo (PUDS)  
**Estado:** 🟢 IMPLEMENTADO Y PROMOVIDO A BASELINE PERMANENTE (`.specs/modules/catalogo_productos/CU06-buscar-filtrar-productos.md`)

> **Nota de reconciliación (2026-09-21):** el encabezado y las 12 casillas de tareas seguían
> congelados en el momento de la propuesta, contradiciendo a su propio `checkpoint.md` (8 puntos de
> control superados) y al `CHANGELOG.md`. Se sincroniza con el estado real.  
**Fecha:** 2026-09-20  

---

## Índice de Contenidos
1. [A. Especificación Formal (`spec`)](#a-especificación-formal-spec)
   - [1. Backend (`Ec-backend`)](#1-bloque-1-backend-ec-backend---fastapi--sqlalchemy-20--postgresql)
   - [2. Frontend Web (`Ec-frontend`)](#2-bloque-2-frontend-web-ec-frontend---angular-19-standalone)
   - [3. Mobile (`Ec-mobile`)](#3-bloque-3-mobile-ec-mobile---flutter-3x--bloc)
2. [B. Plan de Ejecución Secuencial (`plan`)](#b-plan-de-ejecución-secuencial-plan)
3. [C. Lista de Tareas Atómicas (`tasks`)](#c-lista-de-tareas-atómicas-tasks)
4. [D. Puntos de Control y Verificación (`checkpoints`)](#d-puntos-de-control-y-verificación-checkpoints)

---

## A. Especificación Formal (`spec`)

### 1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL)

#### 1.1 Propósito y Alcance del Caso de Uso
Permitir a clientes registrados y visitantes anónimos localizar prendas comercializadas por FashionStore aplicando términos de búsqueda difusa sobre nombres y descripciones (`pg_trgm` / `ILIKE`) combinados con filtros estructurados de catálogo (categoría, colección/línea, temporada, tallas, colores, disponibilidad de stock y rangos de precio), con ordenamiento flexible y paginación determinista de alto rendimiento.

#### 1.2 Fuentes de Verdad de Datos (`SI2-Parcial1.md`)
- **Documento del Proyecto:** `SI2-Parcial1.md` (Líneas 509-510, 969-985 y 2942-3028).
- **Esquema Relacional (`fashionstore`):**
  - `categorias`: `id_categoria`, `nombre`, `id_categoria_padre`.
  - `temporadas`: `id_temporada`, `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `activa`.
  - `colecciones`: `id_coleccion`, `id_temporada`, `nombre`, `descripcion`.
  - `tallas`: `id_talla`, `codigo`, `orden`.
  - `colores`: `id_color`, `nombre`, `codigo_hex`.
  - `productos`: `id_producto`, `id_categoria`, `id_coleccion`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `modelo_ar_url`, `activo`.
  - `variantes_producto`: `id_variante`, `id_producto`, `id_talla`, `id_color`, `sku`, `precio_extra`.
  - `inventario_sucursal`: `id_inventario`, `id_variante`, `id_sucursal`, `cantidad_disponible`, `cantidad_reservada`, `estado`.
  - **Índice Trigram:** Ya existente en Neon DB: `CREATE INDEX idx_productos_nombre_trgm ON fashionstore.productos USING gin (nombre gin_trgm_ops)`.

#### 1.3 Contratos de API REST

##### Endpoint Principal (Idiomático REST para Web y Mobile):
`GET /api/v1/productos` (o alias `GET /api/v1/catalogo/productos`)

- **Query Parameters:**
  - `q` / `search` (opcional, `str`): Término de búsqueda textual (ej. `"vestido"`, `"blazer"`, `"seda"`). Normalizado (trim, lowercase).
  - `categoria_id` (opcional, `int`): ID de categoría. Incluye productos de subcategorías si aplica.
  - `coleccion_id` (opcional, `int`): ID de colección/línea (ej. Sastrería Atelier, Alta Costura).
  - `temporada_id` (opcional, `int`): ID de temporada (ej. Otoño / Invierno 2024).
  - `talla` (opcional, `str`): Código de talla exacto (ej. `"36"`, `"38"`, `"40"`, `"Única"`).
  - `color` (opcional, `str`): Nombre del color (ej. `"Marfil"`, `"Camel"`, `"Ébano"`, `"Champagne"`).
  - `precio_min` (opcional, `Decimal`, `>= 0`): Precio mínimo base.
  - `precio_max` (opcional, `Decimal`, `>= 0`): Precio máximo base. Debe ser `>= precio_min`.
  - `solo_en_stock` (opcional, `bool`, default `true`): Solo prendas con stock disponible (`cantidad_disponible > 0`).
  - `ordenar_por` (opcional, `str`, default `"recientes"`):
    - `"recientes"`: `productos.creado_en DESC`
    - `"precio_asc"`: `productos.precio_base ASC`
    - `"precio_desc"`: `productos.precio_base DESC`
    - `"nombre_asc"`: `productos.nombre ASC`
    - `"relevancia"`: `similarity(productos.nombre, :q) DESC` cuando `q` esté presente.
  - `pagina` (opcional, `int`, default `1`, `>= 1`): Número de página.
  - `limite` (opcional, `int`, default `12`, `1 <= limite <= 50`): Elementos por página.

##### Endpoint Complementario (Compatibilidad con la prueba de `SI2-Parcial1.md` línea 2950):
`POST /api/v1/catalogo/buscar`
- **Body JSON:**
  ```json
  {
    "termino_busqueda": "camisa",
    "filtros": {
      "id_categoria": 1,
      "id_talla": 3,
      "id_color": 2,
      "precio_min": 50.00,
      "precio_max": 300.00
    },
    "pagina": 1,
    "limite": 12
  }
  ```

##### Endpoint de Metadatos de Filtros:
`GET /api/v1/catalogo/filtros-disponibles`
- Retorna la lista de categorías, colecciones, temporadas activas, tallas ordenadas, colores con sus valores hexadecimales y el rango global de precios (`min_global`, `max_global`), permitiendo pintar dinámicamente el sidebar y chips de filtros tanto en Web como en Mobile.

#### 1.4 Esquemas Pydantic (`app/modules/catalogo/cu06_buscar_filtrar/esquemas.py`)

```python
class VarianteResumenOut(BaseModel):
    id_variante: int
    sku: str
    talla: str
    color: str
    codigo_hex: Optional[str] = None
    precio_extra: Decimal = Decimal("0.00")
    disponible: bool = True

class ProductoItemOut(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    categoria: str
    coleccion: Optional[str] = None
    temporada: Optional[str] = None
    precio_base: Decimal
    imagen_url: Optional[str] = None
    modelo_ar_url: Optional[str] = None
    activo: bool
    badge_editorial: Optional[str] = None  # "ED. LIMITADA 12/50", "EN SERRANO", "SEDA PURA"
    subtitulo_atelier: Optional[str] = None # "ALTA COSTURA", "SASTRERÍA ATELIER"
    talla_sugerida: Optional[str] = None   # "Talla 38"
    color_sugerido: Optional[str] = None   # "Marfil"
    variantes: List[VarianteResumenOut] = []

class PaginacionMetaOut(BaseModel):
    total_registros: int
    pagina_actual: int
    limite: int
    total_paginas: int
    tiene_siguiente: bool
    tiene_anterior: bool

class ProductoPaginadoOut(BaseModel):
    items: List[ProductoItemOut]
    paginacion: PaginacionMetaOut
    filtros_aplicados: dict
```

#### 1.5 Optimización y Consultas SQLAlchemy 2.0
1. **Construcción Modular de Consulta:**
   ```python
   stmt = (
       select(ProductoORM)
       .join(ProductoORM.categoria)
       .outerjoin(ProductoORM.coleccion)
       .outerjoin(ProductoORM.variantes)
       .where(ProductoORM.activo == True)
       .distinct()
   )
   ```
2. **Coincidencia Difusa Textual:**
   - Cuando se suministra `q`, se normaliza y se busca mediante `or_(ProductoORM.nombre.ilike(f"%{q}%"), ProductoORM.descripcion.ilike(f"%{q}%"), func.similarity(ProductoORM.nombre, q) > 0.15)`.
3. **Filtros por Variantes (Talla / Color):**
   - Se realiza `join(VarianteProductoORM)` filtrando por `tallas.codigo == talla` o `colores.nombre.ilike(color)`.
4. **Filtro por Existencias (Stock):**
   - Cuando `solo_en_stock=True`, se une con `InventarioSucursalORM` exigiendo `InventarioSucursalORM.cantidad_disponible > 0`.
5. **Cálculo de Conteo Total:**
   - Se genera una consulta de conteo separada y ligera usando `select(func.count(distinct(ProductoORM.id_producto)))` con las mismas cláusulas `WHERE`.

#### 1.6 Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Búsqueda de productos por término clave existente
  Dado que existen productos activos en el catálogo ("Vestido plisado seda", "Blazer estructurado")
  Cuando el cliente envía una petición "GET /api/v1/productos?q=vestido"
  Entonces el sistema responde con código HTTP 200 OK
  Y la lista "items" contiene al menos "Vestido plisado seda"
  Y "paginacion.total_registros" es mayor o igual a 1

Escenario: Filtrado multicriterio simultáneo (Colección + Talla + Color + Rango de Precios)
  Dado un catálogo con prendas de diversas colecciones y variantes
  Cuando el cliente consulta "GET /api/v1/productos?coleccion_id=1&talla=38&color=Marfil&precio_min=300&precio_max=1200"
  Entonces el sistema responde 200 OK
  Y todas las prendas devueltas pertenecen a la colección 1, tienen variante talla 38 color Marfil y precio entre 300 y 1200

Escenario: Búsqueda sin coincidencias en catálogo
  Dado que no existen productos que coincidan con "astronave extraterrestre"
  Cuando el cliente envía "GET /api/v1/productos?q=astronave extraterrestre"
  Entonces el sistema responde 200 OK
  Y el arreglo "items" está vacío ([])
  Y "total_registros" es 0

Escenario: Validación de rangos de precio erróneos
  Cuando el cliente envía "GET /api/v1/productos?precio_min=500&precio_max=200"
  Entonces el sistema responde 422 Unprocessable Entity
  Y el detalle del error indica que precio_max no puede ser menor que precio_min
```

---

### 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### 2.1 Análisis Visual de UI (Fidelidad Estricta con la Captura Web)
La captura de pantalla provista define una experiencia boutique atelier de alta costura:
1. **Navegación Superior:**
   - Brand: `FASHION STORE` con tipografía con serif editorial o sans tracking amplio.
   - Enlaces: `INICIO`, `BUSCAR` (activo/subrayado), `CATÁLOGO`, `PERFIL`.
   - Utilidades: Campana con punto de notificación, bolsa/cesta con contador (`2`), avatar circular.
2. **Breadcrumb & Rótulo Atelier:**
   - `FASHION STORE / BÚSQUEDA & EXPLORACIÓN / PRENDAS`.
   - Lado derecho: `• Atelier Serrano Online · Citas Disponibles Hoy` y badge pill `ACCESO CLIENTE VIP`.
3. **Barra de Búsqueda y Filtros de Cabecera:**
   - Campo amplio con fondo gris perla suave (`#F5F5F5` o `#FAFAFA`), borde sutil, icono de lupa, texto guía: `Vestidos, sastrería y sedas nobles`, botón de limpiar `✕` y rótulo derecho `24 sugerencias`.
   - Fila de Temporadas:
     - Etiqueta: `TEMPORADA:`.
     - Pills deslizables: `Todas las temporadas`, `Otoño / Invierno 2024 •` (píldora negra activa con punto blanco), `Primavera / Verano 2025`, `Cápsula Edición Limitada`.
   - Control de Vista:
     - Selector `Vista: Cuadrícula Cuádruple` con iconos de grilla 4 columnas y 2 columnas.
4. **Sidebar Izquierdo de Filtros Refinados:**
   - Encabezado: Icono de ajustes `Filtros Refinados` y enlace `RESTABLECER` a la derecha.
   - **Colección & Línea (4 opciones):**
     - Checkboxes con conteo: `[x] Sastrería Atelier (12)`, `[ ] Esenciales Minimalistas (8)`, `[ ] Alta Costura (5)`, `[ ] Seda Natural Pura (6)`.
   - **Tallas Disponibles:**
     - Enlace superior `GUÍA ATELIER`.
     - Botones cuadrados de talla: `36`, `38` (activo negro con texto blanco), `40`, `42`, `44`, `Única`.
   - **Color & Textura:**
     - Swatches interactivos circulares con nombre y código hex:
       - `Marfil (#FCFBFR)`
       - `Camel (#C2A688)`
       - `Ébano (#1A1A1A)` (seleccionado)
       - `Champagne (#E8DFCF)`
   - **Inversión (€):**
     - Rótulo `INVERSIÓN (€)` y visor de rango `300 € - 1.200 €`.
     - Dual Range Slider estilizado con pistas negras.
5. **Grilla Central de Prendas (4 Columnas):**
   - Título: `Visto recientemente` con pill `4 PRENDAS`, botón `LIMPIAR HISTORIAL` y selector `ORDENAR: Más recientes ▾`.
   - Tarjetas de Producto:
     - Badge superior izquierdo: `ED. LIMITADA 12/50` o `EN SERRANO` o `SEDA PURA` o `LANA & SEDA`.
     - Botón Wishlist (icono de corazón) circular flotante superior derecho.
     - Imagen editorial vertical (aspect ratio 3:4) con zoom suave al hover.
     - Subtítulo superior en mayúsculas: `ALTA COSTURA`, `SASTRERÍA ATELIER`, `BÁSICOS DE LUJO` + talla (`Talla 38`).
     - Título de la prenda: `Vestido plisado seda`, `Blazer estructurado`, `Blusa satén 22mm`, `Pantalón tiro alto`.
     - Fila inferior: Precio en euros (`890 €`, `740 €`, `310 €`, `420 €`) y punto de color correspondiente.
     - Botón de compra rápida: `+ CESTA` (fondo claro con borde sutil o contraste sobrio).
6. **Paginador Atelier:**
   - Indicador: `Mostrando 4 de 32 piezas de sastrería seleccionadas`.
   - Controles: `ANTERIOR`, `1` (caja negra activa), `2`, `3`, `SIGUIENTE`.
7. **Búsquedas Más Frecuentes:**
   - Cabecera: `↗ BÚSQUEDAS MÁS FRECUENTES`.
   - Píldoras con flecha oblicua: `Vestidos de seda ↗`, `Blazers camel ↗`, `Cashmere 100% ↗`, `Colección Cápsula FW24 ↗`, `Trajes sastre fluídos ↗`.
8. **Footer Editorial Haute Couture:**
   - Secciones: Atención al Cliente, Boutiques (Madrid, París), Sostenibilidad & Oficio (Manifiesto Circular 2025), Boletín Editorial con input de suscripción y avisos legales.

#### 2.2 Arquitectura y Componentes Angular 19+
- **Componentes Standalone:**
  - `BuscarProductosComponent` (`src/app/modules/catalogo/cu06_buscar_filtrar/paginas/buscar-productos.component.ts`): Componente principal contenedor de búsqueda y filtros.
  - `FiltrosSidebarComponent`: Subcomponente desacoplado para el sidebar de colecciones, tallas, colores y slider.
  - `TarjetaPrendaComponent`: Componente reutilizable para cada tarjeta de producto.
- **Servicio `CatalogoService`:**
  - Inyección de `HttpClient`.
  - Métodos: `buscarProductos(params: FiltrosPeticion): Observable<ProductoPaginadoOut>`, `obtenerFiltrosDisponibles(): Observable<FiltrosDisponiblesOut>`.
- **Manejo de Estado con Signals y RxJS:**
  - Input reactivo conectado a `FormControl` con pipe:
    `debounceTime(300)`, `distinctUntilChanged()`, actualizando el Signal `terminoBusqueda`.
  - Signals: `productos = signal<ProductoItemOut[]>([])`, `cargando = signal<boolean>(false)`, `totalResultados = signal<number>(0)`, `filtrosActivos = signal<FiltrosState>(defaultFilters)`.
- **Sincronización Bidireccional con Query Params en la URL:**
  - Los filtros activos se reflejan en la barra de direcciones del navegador: `?q=vestido&coleccion=1&talla=38&color=Marfil&precioMin=300&precioMax=1200&pagina=1`.
  - Si el usuario recarga la página, comparte el enlace o usa el botón "Atrás" del navegador, `ActivatedRoute.queryParams` restaura fielmente el estado de la búsqueda y ejecuta la consulta automáticamente.

---

### 3. Bloque 3: Mobile (`Ec-mobile` - Flutter 3.x + BLoC)

#### 3.1 Análisis Visual de UI (Fidelidad Estricta con la Captura Mobile)
La captura de pantalla móvil traslada la misma sobriedad y refinamiento a pantallas táctiles:
1. **Barra Superior (AppBar):**
   - Título sobrio: `FASHION STORE / Buscar` con avatar de usuario a la derecha.
2. **Barra de Búsqueda Táctil:**
   - Caja redondeada con icono de lupa, placeholder `Buscar vestidos, blazers, tejidos...`, botón `✕` para limpiar texto y botón de filtros avanzados (`tune` icon con punto indicador de filtros aplicados).
3. **Barra Horizontal de Temporadas:**
   - Chips deslizables horizontalmente: `TODAS LAS TEMPORADAS`, `OTOÑO / INVIERNO` (píldora negra activa), `PRIMAVERA / ...`.
4. **Sección `FILTROS REFINADOS` con `RESTABLECER`:**
   - **Línea:** Fila de chips horizontales: `[ Sastrería Atelier ]` (seleccionado en negro), `[ Esenciales ]`, `[ Alta Costura ]`, `[ Seda ... ]`.
   - **Tallas:** Fila horizontal de botones cuadrados: `[ 36 ] [ 38 ] [ 40 ] [ 42 ] [ Única ]` con el `38` en fondo negro.
   - **Colores:** Chips con circulo de muestra: `[ O Marfil ] [ O Camel ] [ • Ébano ] [ O Champagne ]`.
5. **Modal BottomSheet de Filtros Detallados:**
   - Al pulsar el botón de ajustes de la barra de búsqueda, se despliega un BottomSheet con:
     - Selector de rango de precios (Dual Range Slider).
     - Switch de "Solo disponibles en mi sucursal".
     - Selector de ordenamiento (precio, fecha, relevancia).
     - Botones `Limpiar Todo` y `Aplicar Filtros`.
6. **Grilla de Resultados (2 Columnas - `GridView`):**
   - Header: `Visto recientemente (4 prendas)` y `LIMPIAR HISTORIAL`.
   - Tarjetas:
     - Badges superiores (`EDICIÓN LIMITADA`, `EN SERRANO`).
     - Botón flotante circular de favoritos (corazón).
     - Fotografía de prenda.
     - Subtítulo en mayúsculas (`ALTA COSTURA`, `SASTRERÍA ATELIER`).
     - Nombre de la prenda (`Vestido plisado seda`, `Blazer lana virgen`, `Blusa satén 22mm`, `Pantalón tiro alto`).
     - Especificaciones de variante seleccionada (`Talla 38 · Marfil`, `Talla 40 · Camel`).
     - Precio en euros (`890 €`, `740 €`, `310 €`, `420 €`).
     - Botón interactivo `+ CESTA`.
7. **Búsquedas Más Frecuentes:**
   - Título: `↗ BÚSQUEDAS MÁS FRECUENTES`.
   - Chips táctiles: `🔍 Vestidos de seda`, `🔍 Blazers camel`, `🔍 Cashmere 100%`, `🔍 Colección Cápsula FW24`, `🔍 Trajes sastre fluídos`.
8. **Navegación Inferior (BottomNavigationBar):**
   - 4 destinos: `Inicio`, `Buscar` (activo), `Catálogo`, `Perfil`.

#### 3.2 Clean Architecture & BLoC en Flutter
- **Capa de Dominio:**
  - Entidades: `Producto`, `VarianteProducto`, `FiltroCatalogo`, `PaginacionCatalogo`.
  - Repositorio abstracto: `CatalogoRepositorio`.
- **Capa de Datos:**
  - `CatalogoRemotoDatasource`: Llamadas HTTP a `/api/v1/productos` y `/api/v1/catalogo/filtros-disponibles`.
  - `ProductoDto` y `FiltrosDto`: Serialización/deserialización robusta.
- **Capa de Presentación (BLoC / ChangeNotifier):**
  - **Eventos:**
    - `BuscarTerminoEvent(String query)` (con debouncing interno de 350ms).
    - `SeleccionarTemporadaEvent(int? temporadaId)`.
    - `SeleccionarColeccionEvent(int? coleccionId)`.
    - `SeleccionarTallaEvent(String? talla)`.
    - `SeleccionarColorEvent(String? color)`.
    - `AjustarRangoPreciosEvent(double min, double max)`.
    - `RestablecerFiltrosEvent()`.
    - `CargarSiguientePaginaEvent()`.
  - **Estados Sellados:**
    - `CatalogoInicial`: Estado previo a la carga.
    - `CatalogoCargando`: Mostrando shimmers de carga en grilla.
    - `CatalogoCargado`: Grilla poblada con items y metadata de paginación.
    - `CatalogoVacio`: Pantalla amigable "No se encontraron prendas con los filtros aplicados" con botón de limpiar.
    - `CatalogoError`: Fallo de conexión con opción de reintentar.

---

## B. Plan de Ejecución Secuencial (`plan`)

El desarrollo se organizará en 3 bloques secuenciales, cada uno con su correspondiente verificación y compuerta de calidad:

```
┌─────────────────────────────────────────────────────────────┐
│ FASE 1: BACKEND (FastAPI + SQLAlchemy + PostgreSQL Neon)   │
│ - Modelos ORM de Catálogo (Categorías, Variantes, Productos)│
│ - Servicio con queries dinámicas e índice pg_trgm           │
│ - Endpoints GET /api/v1/productos y filtros disponibles    │
│ - Tests en pytest (Búsqueda, Filtros, Paginación, Límites)  │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 2: FRONTEND WEB (Angular 19+ Standalone)               │
│ - Servicio HTTP de Catálogo y modelos TypeScript            │
│ - Componente de búsqueda y sidebar de filtros refinados     │
│ - Grilla de 4 columnas, debounce reactivo y sync con URL   │
│ - Tests en Vitest y bundle limpio en npm run build          │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ FASE 3: MOBILE (Flutter 3.x + BLoC)                         │
│ - Datasource y Repositorio de Catálogo                      │
│ - CatalogoBloc con eventos, estados y debouncing            │
│ - UI fiel: Barra búsqueda, chips horizontales, GridView 2col│
│ - Tests en flutter test y flutter analyze sin advertencias  │
└─────────────────────────────────────────────────────────────┘
```

---

## C. Lista de Tareas Atómicas (`tasks`)

### Bloque 1: Backend (`Ec-backend`)
- [x] **B1.1**: Definir modelos ORM en `app/modules/catalogo/modelos.py` (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`).
- [x] **B1.2**: Implementar esquemas Pydantic de entrada y salida en `app/modules/catalogo/cu06_buscar_filtrar/esquemas.py`.
- [x] **B1.3**: Crear `ServicioBuscarFiltro` en `app/modules/catalogo/cu06_buscar_filtrar/servicio.py` con construcción dinámica de consultas SQLAlchemy 2.0 (`ILIKE`, `pg_trgm`, filtros relacionales y conteo).
- [x] **B1.4**: Implementar endpoints en `app/modules/catalogo/cu06_buscar_filtrar/router.py`:
  - `GET /api/v1/productos`
  - `GET /api/v1/catalogo/filtros-disponibles`
  - `POST /api/v1/catalogo/buscar` (compatibilidad informe)
- [x] **B1.5**: Registrar router en `app/main.py` bajo el prefijo `/api/v1`.
- [x] **B1.6**: Escribir suite de pruebas `tests/modules/catalogo/test_cu06_buscar_filtrar.py` y validar 100% de tests en verde con `pytest` (16/16 tests de CU06 pasando, 79/79 suite completa).

### Bloque 2: Frontend Web (`Ec-frontend`)
- [x] **F2.1**: Crear modelos e interfaces TypeScript en `src/app/modules/catalogo/modelos/catalogo.modelos.ts`.
- [x] **F2.2**: Implementar `CatalogoService` en `src/app/modules/catalogo/servicios/catalogo.service.ts`.
- [x] **F2.3**: Diseñar componente `BuscarProductosComponent` maquetando fielmente la captura Web:
  - Barra de búsqueda con debounce y botón `✕`.
  - Selector superior de temporadas (chips horizontales).
  - Sidebar izquierdo de filtros (Colecciones, Tallas, Colores, Rango de inversión).
  - Selector de orden y limpiador de historial.
  - Grilla de 4 columnas de tarjetas de prenda con badges, tallas y botón `+ CESTA`.
  - Paginador atelier y píldoras de búsquedas frecuentes.
- [x] **F2.4**: Integrar sincronización bidireccional con Query Params (`ActivatedRoute` / `Router`).
- [x] **F2.5**: Configurar ruta `/buscar` en `app.routes.ts` y enlazar en navegación principal.
- [x] **F2.6**: Escribir tests unitarios `buscar-productos.component.spec.ts` y validar `ng test` y `npm run build`.

### Bloque 3: Mobile (`Ec-mobile`)
- [x] **M3.1**: Definir DTOs y modelos de datos en `lib/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/`.
- [x] **M3.2**: Implementar `CatalogoRemotoDatasource` y `CatalogoRepositorio`.
- [x] **M3.3**: Crear `CatalogoBloc` con estados sellados, debounce de búsqueda y control de paginación.
- [x] **M3.4**: Maquetar `PantallaBuscarProductos` según la captura Mobile:
  - Barra de búsqueda con botón de filtros rápidos.
  - Fila horizontal de temporadas (`OTOÑO / INVIERNO`).
  - Filas de chips para Línea, Tallas cuadradas y Colores con muestra visual.
  - `GridView` de 2 columnas para prendas con badges editoriales y botón `+ CESTA`.
  - Píldoras inferiores de búsquedas más frecuentes.
  - Modal BottomSheet para filtros avanzados (slider de precios).
- [x] **M3.5**: Conectar destino `Buscar` en la barra inferior de navegación.
- [x] **M3.6**: Escribir tests unitarios y de widgets (`catalogo_bloc_test.dart`, `pantalla_buscar_test.dart`) y verificar `flutter test` y `flutter analyze`.

---

## D. Puntos de Control y Verificación (`checkpoints`)

| Checkpoint | Criterio de Aprobación | Método de Verificación |
| :--- | :--- | :--- |
| **CP-01 (Backend API)** | Búsqueda por palabra clave, filtrado combinado y paginación responden en menos de 100ms sobre PostgreSQL Neon. | `pytest tests/modules/catalogo/test_cu06_buscar_filtrar.py` (100% pasando: 16/16 tests). | 🟢 Superado |
| **CP-02 (Backend Validación)** | Filtros con datos inconsistentes (ej. `precio_min > precio_max`, `pagina < 1`) devuelven `422 Unprocessable Entity`. | Tests específicos de validación de esquemas Pydantic y router. | 🟢 Superado |
| **CP-03 (Frontend UX & Debounce)** | El input de búsqueda no genera peticiones por cada pulsación, sino tras 300ms de inactividad, cancelando peticiones en vuelo anteriores. | Inspección de Network Tab en Angular DevTools y tests con `fakeAsync`. |
| **CP-04 (Frontend URL State)** | Al refrescar el navegador con filtros activos (ej. `?coleccion=1&talla=38`), la vista se recupera íntegra con las casillas marcadas. | Prueba de navegación y recarga manual en navegador. |
| **CP-05 (Mobile Táctil & Scroll)** | Grilla fluida a 60 fps sin desbordamientos (`RenderFlex overflowed`) ni parpadeos al alternar chips. | `flutter test` y ejecución en emulador/dispositivo. |
| **CP-06 (Fidelidad Visual)** | Ambas aplicaciones reproducen con exactitud tipográfica, espaciado, colores de swatches y badges las imágenes de referencia provistas. | Comparación visual pixel a pixel contra las capturas Web y Mobile. |
