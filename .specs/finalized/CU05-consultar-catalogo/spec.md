# Especificación Técnica Formal: CU05 - Consultar Catálogo de Productos

**Código:** CU05  
**Nombre:** Consultar Catálogo de Productos (Colección General, Atelier & Sastrería Femenina)  
**Paquete de Dominio:** `catalogo` (`catalogo_productos`)  
**Directorio Funcional:** `cu05_consultar_catalogo`  
**Actores:** Cliente (Registrado y Visitante Anónimo)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Propuesta de Cambio Inicial)  
**Estado:** 🟡 EN FASE DE ESPECIFICACIÓN Y PLANIFICACIÓN (Gate de Aprobación Activo)  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1_terminado.pdf` / `SI2-Parcial1.md` (Líneas 957-974: Propósito, actores, precondiciones, flujo principal de consulta del catálogo activo, tablas `productos`, `categorias`, `variantes_producto`, `inventario_sucursal` y `promociones`).
- Referencia Visual y UX Web: Captura de referencia Desktop Haute Couture Atelier (Breadcrumbs editoriales, cabecera "CATÁLOGO DE PRENDAS", selector horizontal de categorías con contadores numéricos, cuadrícula de 4 columnas con badges como *"EDICIÓN LIMITADA"*, *"EN SERRANO"*, *"SEDA PURA"*, *"LANA & SEDA"*, *"NOVEDAD"*, *"DISPONIBLE"*, tallas, dots de color, paginación con barra de progreso y bloque editorial de Conserjería Privada de Fitting).
- Referencia Visual y UX Mobile: Captura de referencia Mobile Atelier (AppBar "Catálogo de Prendas", chips horizontales con unidades *"Todos (24)"*, *"Sastrería & Trajes (8)"*, *"Vestidos (6)"*, selector de vista de cuadrícula, tarjetas en 2 columnas con botón de wishlist, botón expansor *"CARGAR MÁS PRENDAS (18) ⌵"*, paginación numerada y sello editorial de atelier).
- Directriz Arquitectónica Global: Jerarquía de Vistas (Hub-and-Spoke) ([`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/architecture/directriz-navegacion-hub-and-spoke.md)).
- Design System: Tipografía corporativa `Outfit`, paleta textil Obsidian/Camel/Marfil de `fashionstore-tokens.md`, y catálogo estrictamente femenino.

---

## 1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 1.1 Propósito y Reglas de Negocio

Proporcionar la API principal de catálogo omnicanal para que clientes registrados y visitantes anónimos exploren la colección general de prendas de alta costura de FashionStore, obteniendo el catálogo paginado, el desglose dinámico de categorías activas con conteo de prendas, variantes disponibles (tallas y colores) y precios con verificación de promociones activas.

1. **Jerarquía y Clasificación de Categorías:**
   - Cada producto activo pertenece a una categoría (`productos.id_categoria -> categorias.id_categoria`).
   - El endpoint debe calcular de manera agregada y sin queries N+1 el conteo de prendas activas (`COUNT(DISTINCT productos.id_producto)`) para cada categoría existente con stock disponible.
   - Debe incluirse el conteo global consolidado para el chip virtual "Todos los productos".

2. **Filtrado Rápido por Categoría (Chips):**
   - El parámetro `categoria_id` es opcional.
   - Si `categoria_id` es `null`, se retornan los productos de todas las categorías ordenados por piezas recientes.
   - Si se especifica `categoria_id`, se filtran estrictamente los productos de dicha categoría y sus posibles subcategorías hijas.

3. **Cálculo de Existencias, Variantes y Precios:**
   - Solo se exponen prendas con `activo = true`.
   - Se consolidan las tallas disponibles (`tallas.codigo` ordenadas por `tallas.orden`) y los colores disponibles (`colores.nombre`, `colores.codigo_hex`) a partir de `variantes_producto`.
   - Se calcula el stock total disponible (`SUM(inventario_sucursal.cantidad_disponible)`) y la bandera booleana `tiene_stock`.
   - Se evalúa si la prenda cuenta con un descuento o promoción activa en `fashionstore.promociones` para calcular `precio_final`, `tiene_descuento` y `porcentaje_descuento`.

4. **Metadatos Editoriales de Alta Costura:**
   - Cada producto expone:
     - `subtitulo_atelier`: Familia o línea de confección (ej. *"ALTA COSTURA"*, *"SASTRERÍA ATELIER"*, *"BÁSICOS DE LUJO"*, *"ABRIGOS DE AUTOR"*).
     - `etiqueta_badge`: Badge editorial contextual (ej. *"EDICIÓN LIMITADA"*, *"NOVEDAD"*, *"EN SERRANO"*, *"SEDA PURA"*, *"LANA & SEDA"*, *"PRODUCCIÓN LIMITADA"*, *"DISPONIBLE"* o *"ÚLTIMAS UNIDADES"*).
     - `rating_promedio`: Calificación de atelier (ej. 4.9).

5. **REGLA DE NEGOCIO GLOBAL INQUEBRANTABLE (MODA EXCLUSIVAMENTE FEMENINA):**
   - FashionStore es un comercio de alta costura **EXCLUSIVAMENTE PARA MUJERES**.
   - Queda estrictamente prohibida la presencia de modelos masculinos, prendas de hombre o sastrería masculina. Todo activo visual y prenda corresponde a indumentaria femenina.

6. **INTEGRIDAD DE DATOS REALES (CERO HARDCODING):**
   - Todos los productos provienen estrictamente de la base de datos PostgreSQL Neon (`fashionstore.productos`).
   - Cero productos ficticios o quemados en cliente.

---

### 1.2 Contratos de API REST (FastAPI)

#### Endpoint Principal: Catálogo General
- **Ruta:** `GET /api/v1/catalogo`
- **Método:** `GET`
- **Autenticación:** Pública (no requiere token; si se envía token, permite asociar el estado de favoritos del cliente).
- **Parámetros Query:**
  - `categoria_id` (Optional[int], default=None): ID de categoría para filtrado directo por chip.
  - `ordenar_por` (str, default="recientes"): Criterio de ordenación (`recientes`, `precio_asc`, `precio_desc`, `nombre_asc`, `rating`).
  - `pagina` (int, default=1, ge=1): Número de página solicitado.
  - `limite` (int, default=8, ge=1, le=50): Cantidad de artículos por página (por defecto 8 para Web Desktop; 6 en Mobile mediante override).
- **Códigos de Respuesta:**
  - `200 OK`: Catálogo paginado con resumen de categorías y lista de productos.
  - `400 Bad Request`: Parámetros de paginación u orden inválidos.
  - `500 Internal Server Error`: Error no controlado del servidor.

---

### 1.3 Esquemas Pydantic (`app/modules/catalogo/cu05_consultar_catalogo/esquemas.py`)

```python
class ColorItemOut(BaseModel):
    id_color: int
    nombre: str
    codigo_hex: str

class CategoriaResumenOut(BaseModel):
    id_categoria: int
    nombre: str
    total_prendas: int

class ProductoCatalogoOut(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    precio_final: Decimal
    tiene_descuento: bool = False
    porcentaje_descuento: Optional[int] = None
    imagen_url: Optional[str] = None
    categoria_id: int
    categoria_nombre: str
    subtitulo_atelier: str
    etiqueta_badge: Optional[str] = None
    rating_promedio: float = 5.0
    tallas_disponibles: List[str] = []
    colores_disponibles: List[ColorItemOut] = []
    stock_total_disponible: int = 0
    tiene_stock: bool = True
    es_favorito: bool = False

class CatalogoOut(BaseModel):
    resumen_categorias: List[CategoriaResumenOut]
    total_articulos: int
    pagina_actual: int
    limite: int
    total_paginas: int
    tiene_siguiente: bool
    tiene_anterior: bool
    categoria_seleccionada_id: Optional[int] = None
    items: List[ProductoCatalogoOut]
```

---

### 1.4 Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Carga inicial del catálogo activo
  Dado que existen 24 prendas activas distribuidas en diversas categorías
  Cuando un cliente envía una petición GET a "/api/v1/catalogo" con pagina=1 y limite=8
  Entonces el código de respuesta debe ser 200 OK
  Y el payload debe contener "resumen_categorias" con el conteo de prendas por categoría
  Y "total_articulos" debe ser igual a 24
  Y la lista "items" debe contener exactamente 8 productos ordenados por novedad
  Y cada producto debe incluir "precio_base", "tallas_disponibles" y "colores_disponibles"

Escenario: Filtrado por chip de categoría
  Dado que existen 6 prendas activas en la categoría "Vestidos" (id_categoria = 2)
  Cuando el cliente envía una petición GET a "/api/v1/catalogo?categoria_id=2"
  Entonces el código de respuesta debe ser 200 OK
  Y "categoria_seleccionada_id" debe ser igual a 2
  Y "total_articulos" debe ser igual a 6
  Y todos los productos en "items" deben pertenecer a "Vestidos"

Escenario: Catálogo sin existencias en una categoría vacía (Empty State)
  Dado que existe una categoría "Alta Costura Nupcial" sin prendas registradas o activas
  Cuando el cliente envía una petición GET a "/api/v1/catalogo?categoria_id=99"
  Entonces el código de respuesta debe ser 200 OK
  Y "total_articulos" debe ser igual a 0
  Y la lista "items" debe estar vacía []

Escenario: Paginación correcta hacia la segunda página
  Dado que el catálogo cuenta con 24 artículos en total
  Cuando el cliente solicita GET a "/api/v1/catalogo?pagina=2&limite=8"
  Entonces el código de respuesta debe ser 200 OK
  Y "pagina_actual" debe ser 2
  Y "total_paginas" debe ser 3
  Y "tiene_anterior" debe ser verdadero
  Y "tiene_siguiente" debe ser verdadero
```

---

## 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

### 2.1 Estructura, Layout y Jerarquía de Navegación (Hub-and-Spoke)

- **Ruta:** `/catalogo`
- **Integración:** Declarada como ruta hija dentro de `MainLayoutComponent` en `app.routes.ts`:
  ```typescript
  {
    path: '',
    component: MainLayoutComponent,
    children: [
      { path: 'inicio', ... },
      { path: 'buscar', ... },
      { 
        path: 'catalogo', 
        loadComponent: () => import('./modules/catalogo/cu05_consultar_catalogo/paginas/catalogo.component')
          .then(m => m.CatalogoComponent) 
      },
      { path: 'perfil', ... },
    ]
  }
  ```
- **Regla Inviolable:**
  - **Barra de Navegación Institucional (Header): SIEMPRE VISIBLE.** La pestaña `CATÁLOGO` se destaca con estilo activo (`border-b-2 border-black` o enlace activo).
  - **Botón de regreso (`← Volver`): ESTRICTAMENTE PROHIBIDO.** Al ser una pantalla raíz (Hub), no contiene flecha ni botón de retroceso hacia rutas anteriores.

### 2.2 Componente y Manejo Reactivo (`CatalogoComponent`)

- **Signals de Estado:**
  - `resumenCategorias = signal<CategoriaResumenItem[]>([])`
  - `categoriaSeleccionada = signal<number | null>(null)`
  - `productos = signal<ProductoCatalogoItem[]>([])`
  - `totalArticulos = signal<number>(0)`
  - `paginaActual = signal<number>(1)`
  - `limitePorPagina = signal<number>(8)`
  - `totalPaginas = signal<number>(1)`
  - `vistaColumnas = signal<'grid4' | 'grid2'>('grid4')`
  - `cargando = signal<boolean>(false)`
  - `favoritos = signal<Set<number>>(new Set())`

- **Secciones Visuales Fieles a la Captura Desktop:**
  1. **Breadcrumbs & Badge de Sincronización:**
     - `FASHION STORE / CATÁLOGO / TODAS LAS PRENDAS`
     - Badge superior derecho: `STOCK SINCRONIZADO EN TIEMPO REAL CON FLAGSHIP SERRANO & SAINT-HONORÉ`.
  2. **Cabecera Editorial:**
     - Titular `H1`: *"CATÁLOGO DE PRENDAS"* en tipografía `Outfit` (`font-bold tracking-tight text-3xl`).
     - Subtítulo: *"Colección General & Atelier · Siluetas arquitectónicas creadas con materiales nobles y acabados artesanos."*
     - Etiqueta derecha: *"CERTIFICACIÓN ARTESANAL · MADRID · PARÍS"*.
  3. **Fila Deslizable de Chips de Categorías con Contador:**
     - Chip activo *"TODOS LOS PRODUCTOS (24)"* (fondo negro, texto blanco, bordes redondeados `rounded-full`).
     - Chips de categorías *"SASTRERÍA & TRAJES (8)"*, *"VESTIDOS DE GALA (6)"*, *"BLUSAS & TOPS DE SEDA (5)"*, *"PUNTO & ABRIGOS (5)"*.
     - Al hacer clic en un chip, actualiza reactivamente `categoriaSeleccionada` y recarga los productos sin recargar la página.
     - Extremo derecho: Selector de cuadrícula interactivo (icono de 4 columnas y 2 columnas).
     - Botón de acceso directo *"Filtrar y Ordenar"* con navegación hacia `/buscar` (CU06).
  4. **Grilla Editorial de Productos (4 Columnas):**
     - Tarjetas de prenda con relación de aspecto armónica.
     - Badge superior izquierdo en la fotografía: *"EDICIÓN LIMITADA"*, *"EN SERRANO"*, *"SEDA PURA"*, *"LANA & SEDA"*, *"NOVEDAD"*, *"DISPONIBLE"*.
     - Botón de Wishlist / Favorito en la esquina superior derecha de la foto (círculo blanco con icono de corazón interactivo).
     - Subtítulo de atelier en mayúsculas (`text-[10px] text-gray-500 font-semibold tracking-wider`): *"ALTA COSTURA"*, *"SASTRERÍA ATELIER"*, *"BÁSICOS DE LUJO"*.
     - Nombre de la prenda: tipografía `Outfit` semibold en color negro.
     - Precio en EUR (ej. `890 €`).
     - Lista horizontal de tallas disponibles (`36 · 38 · 40`).
     - Círculos de color textil en el extremo derecho de las tallas.
     - Clic en la tarjeta navega al detalle de prenda `/catalogo/:id` (CU07).
  5. **Paginación Editorial:**
     - Línea con indicador de progreso: *"MOSTRANDO 1 – 8 DE 24 PRENDAS"*.
     - Botones numéricos `[1]`, `[2]`, `[3]`, y botón `[SIGUIENTE >]`.
  6. **Bloque de Conserjería Privada de Fitting:**
     - Contenedor con fondo atelier neutro y bordes sutiles:
       - Título: *"CONSERJERÍA PRIVADA DE TALLAS & FITTING"*.
       - Descripción: *"¿Dudas sobre el patrón arquitectónico o drapeado de las sedas? Reserve cita de fitting privado o solicite asesoramiento textil con nuestros directores de atelier."*
       - Botón negro elegante: *"SOLICITAR ASESORÍA"*.
  7. **Footer Institucional Completo:**
     - Pie de página institucional estándar de FashionStore.

---

## 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

### 3.1 Integración en `PantallaPrincipalHub` y Jerarquía de Navegación

- **Ubicación:** Reemplaza la vista placeholder en blanco en el **Índice 2 (`Catálogo`)** de [`PantallaPrincipalHub`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/navegacion/pantalla_principal_hub.dart).
- **Regla Inviolable:**
  - **Barra de navegación inferior visible (`BottomNavigationBar` en índice 2):** El icono de Catálogo se muestra destacado/activo en negrita.
  - **Botón de regreso (`← Volver`): ESTRICTAMENTE PROHIBIDO en AppBar (`automaticallyImplyLeading: false`).**

### 3.2 Arquitectura BLoC (`CatalogoBloc`)

- **Ubicación:** `lib/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/bloc/`
- **Eventos (`CatalogoEvento`):**
  - `CargarCatalogoIniciado`: Carga inicial con categoría opcional y límite móvil (6 productos).
  - `FiltrarPorCategoriaChip(int? categoriaId)`: Cambio inmediato de categoría al tocar un chip.
  - `CambiarModoVistaColumnas(int columnas)`: Alterna entre cuadrícula de 2 columnas y lista de 1 columna.
  - `CargarMasProductosCatalogo`: Paginación infinita o mediante botón expansor.
  - `ToggleFavoritoPrenda(int idProducto)`: Alterna el estado de wishlist.
- **Estados (`CatalogoEstado`):**
  - `CatalogoCargando`: Shimmers o spinners de carga inicial.
  - `CatalogoCargado`: Estado con lista de productos, resumen de categorías, página actual y categoría seleccionada.
  - `CatalogoVacio`: Estado vacío con mensaje editorial atelier cuando una categoría no contiene prendas.
  - `CatalogoError(String mensaje)`: Mensaje de error con opción de reintento.

### 3.3 Pantalla y Componentes Mobile (`PantallaCatalogo`)

- **Ubicación:** `lib/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart`
- **Componentes Visuales Fieles a la Captura Mobile:**
  1. **AppBar Institucional:**
     - Icono de menú lateral / drawer en la izquierda.
     - Logo centrado `FASHION STORE`.
     - `automaticallyImplyLeading: false` (sin botón de retorno).
  2. **Cabecera "Catálogo de Prendas":**
     - Título `Catálogo de Prendas` en tipografía `Outfit` semibold.
  3. **Fila Horizontal Deslizable de Chips de Categorías:**
     - Chip activo *"Todos (24)"* (negro con texto blanco).
     - Chips de categorías *"Sastrería & Trajes (8)"*, *"Vestidos (6)"*, *"Blusas & Tops (5)"*.
     - Indicador numérico integrado entre paréntesis.
  4. **Barra de Control de Vista:**
     - Etiqueta *"VISTA:"* con botones conmutadores de cuadrícula (2 columnas vs 1 columna).
     - Botón de acceso directo hacia búsqueda avanzada *"Filtrar y Ordenar"* que conmuta a la pestaña 1 (Buscar).
  5. **Cuadrícula de Tarjetas de Producto (GridView 2 Columnas):**
     - Badges textiles en esquina superior izquierda (`EDICIÓN LIMITADA`, `EN SERRANO`, `SEDA PURA`, `LANA & SEDA`, `NOVEDAD`, `DISPONIBLE`).
     - Botón de wishlist interactivo en la esquina superior derecha.
     - Subtítulo de autor en mayúsculas (`ALTA COSTURA`, `SASTRERÍA ATELIER`, `BÁSICOS DE LUJO`).
     - Título de prenda legible con elipsis en 1 o 2 líneas.
     - Precio en EUR (`890 €`).
     - Tallas disponibles (`36 · 38 · 40` o `Talla Única`).
     - Relación de aspecto calibrada (`childAspectRatio: 0.62-0.65`) sin huecos blancos excesivos ni desbordamientos `RenderFlex`.
  6. **Controles de Paginación:**
     - Texto de progreso: *"MOSTRANDO 1 – 6 DE 24 PRENDAS"*.
     - Botón expansor central: *"CARGAR MÁS PRENDAS (18) ⌵"*.
     - Paginación numerada inferior: `[1]`, `[2]`, `[3]`, `[Siguiente →]`.
  7. **Sello Editorial Inferior:**
     - Monograma / Sello dorado de Atelier.
     - *"ATELIER FLAGSHIP MADRID · PARÍS"*.
     - *"Edición Limitada · Confección Artesanal en Tejidos Naturales"*.
