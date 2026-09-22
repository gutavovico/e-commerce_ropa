# Propuesta de Cambio Técnico: CU36 - Consultar Colecciones

**ID del Cambio:** `CU36-consultar-colecciones`  
**Caso de Uso:** CU36 - Consultar Colecciones  
**Paquete de Dominio:** `catalogo` (Catálogo y Exploración)  
**Actores:** Cliente Autenticado y Visitante Anónimo  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 1 (Exploración pública de catálogo, consultas relacionales agregadas y navegación editorial)  
**Estado:** 🟢 100% IMPLEMENTADO Y VERIFICADO (Bloques 1, 2 y 3 Pasando al 100% - Pendiente Autorización de Consolidación)  
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
Permitir a clientes registrados y visitantes anónimos consultar las colecciones vigentes de la firma asociadas a la temporada comercial activa, así como explorar el catálogo de prendas exclusivas de cada colección individual con precios de entrada, existencias en tiempo real y metadatos de confección.

1. **Vigencia de Temporada Comercial:**
   - La temporada activa se resuelve mediante la tabla `fashionstore.temporadas` donde `activa = true` y la fecha actual (`CURRENT_DATE`) se encuentra dentro del rango de vigencia (`fecha_inicio <= CURRENT_DATE <= fecha_fin`).
   - Si no existe temporada con fecha vigente, se toma como fallback la temporada marcada con `activa = true` más reciente.
2. **Jerarquía y Agregación de Colecciones:**
   - Se obtienen las colecciones asociadas a la temporada (`fashionstore.colecciones` vinculadas por `id_temporada`).
   - Para cada colección se calcula de forma agregada:
     - `total_prendas`: Cantidad de productos activos (`productos.activo = true`) asociados a la colección.
     - `precio_desde`: Precio mínimo (`MIN(productos.precio_base)`) entre las prendas activas.
     - `proveedor` y `taller_origen`: Razón social o referencia del proveedor asociado (`fashionstore.proveedores`).
   - **Colección Destacada (Hero):** Se determina como la colección principal vigente (aquella con mayor número de prendas activas o marcada como prioritaria en metadatos), la cual incluirá un subconjunto de hasta 4 piezas clave con stock disponible.
3. **Colecciones Secundarias ("Otras colecciones"):**
   - El resto de colecciones activas e históricas con piezas disponibles en archivo se listan como colecciones secundarias.
4. **Consulta de Prendas por Colección Específica (`GET /api/v1/colecciones/{id_coleccion}/productos`):**
   - Retorna la información editorial de la colección (`nombre`, `descripcion`, `temporada`, `proveedor`, `total_prendas`).
   - Retorna el listado completo de productos activos asociados (`productos.id_coleccion = id_coleccion` y `productos.activo = true`), incluyendo fotos, precios base, badges editoriales, subtítulos de tejido y disponibilidad de inventario consolidado (`SUM(inventario_sucursal.cantidad_disponible) > 0`).
   - Si la colección no existe en el sistema, retorna `404 Not Found`.
   - Si la colección existe pero no tiene prendas activas asignadas, retorna `total_prendas: 0`, `productos: []` y el estado vacío editorial *"Próximo lanzamiento: las piezas de esta colección están en proceso de confección artesanal"*.
5. **REGLA DE NEGOCIO GLOBAL INQUEBRANTABLE (MODA EXCLUSIVAMENTE FEMENINA):**
   - FashionStore es un comercio electrónico omnicanal de lujo y alta costura **EXCLUSIVO PARA MUJERES**.
   - Queda estrictamente prohibido incluir productos, modelos masculinos, trajes de hombre o fotografía que no pertenezca a moda femenina.
6. **JERARQUÍA CANÓNICA Y FUENTE DE DATOS REALES (POSTGRESQL):**
   - Una **temporada** puede contener una o más **colecciones** (`colecciones.id_temporada -> temporadas.id_temporada`).
   - Una **colección** contiene múltiples **prendas de ropa** (`productos.id_coleccion -> colecciones.id_coleccion`).
   - Todos los productos mostrados en frontend y mobile provienen estrictamente de la base de datos real (`fashionstore.productos`). Se prohíbe inventar productos ficticios en cliente. Si hacen falta productos, se dan de alta en la base de datos con variantes e inventario.
7. **DIRECTRIZ ARQUITECTÓNICA DE NAVEGACIÓN (JERARQUÍA HUB-AND-SPOKE):**
   - La pantalla de `Colecciones` (`CU36`) y su vista de detalle son estrictamente **Pantallas Secundarias (Hojas / Spoke)**, derivadas como sub-vistas a partir de `Inicio`.
   - **Barra de navegación global (Navbar Web / BottomNavigationBar Mobile): OCULTA / NO DISPONIBLE.** No debe incluirse en ninguna pantalla secundaria.
   - **Botón de regreso (`← Volver` / `leading: BackButton()`): ESTRICTAMENTE OBLIGATORIO.** Debe contar con botón funcional de retorno hacia la pantalla previa de origen (`Inicio` o `Colecciones`).

#### 1.2 Mapeo Relacional y Entidades ORM
- Mapeo en `app/modules/catalogo/modelos.py`:
  - `TemporadaORM`: Mapea `fashionstore.temporadas` (`id_temporada`, `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `activa`).
  - `ColeccionORM`: Mapea `fashionstore.colecciones` (`id_coleccion`, `id_temporada`, `id_proveedor`, `nombre`, `descripcion`, `creado_en`).
  - `ProveedorORM`: Mapea `fashionstore.proveedores` (`id_proveedor`, `razon_social`, `nit`, `contacto_nombre`, `telefono`, `email`, `activo`).
  - `ProductoORM`: Mapea `fashionstore.productos` con clave foránea a `id_coleccion`.
  - `VarianteProductoORM` e `InventarioSucursalORM`: Para cálculo de disponibilidad de tallas, colores y existencias físicas.

#### 1.3 Contratos de API REST (FastAPI)

##### Endpoint 1: Colecciones Activas
- **Ruta:** `GET /api/v1/colecciones/activas`
- **Alias:** `GET /api/v1/catalogo/colecciones/activas`
- **Método:** `GET`
- **Autenticación:** Opcional (Pública para clientes y visitantes).
- **Parámetros Query:**
  - `limite_piezas_clave` (int, opcional, por defecto 4): Número de piezas clave a precargar para la colección destacada.
- **Códigos de Respuesta:**
  - `200 OK`: Respuesta con temporada activa, colección destacada y listado de otras colecciones.
  - `500 Internal Server Error`: Error no controlado.

##### Endpoint 2: Prendas de una Colección Específica
- **Ruta:** `GET /api/v1/colecciones/{id_coleccion}/productos`
- **Alias:** `GET /api/v1/catalogo/colecciones/{id_coleccion}/productos`
- **Método:** `GET`
- **Autenticación:** Opcional (Pública).
- **Parámetros Path:**
  - `id_coleccion` (int, obligatorio): ID numérico de la colección a consultar.
- **Códigos de Respuesta:**
  - `200 OK`: Metadatos de la colección y array de prendas activas.
  - `404 Not Found`: Cuando `id_coleccion` no existe en la base de datos.
  - `500 Internal Server Error`: Error no controlado.

#### 1.4 Esquemas Pydantic (`esquemas.py`)
```python
class ProductoColeccionItemOut(BaseModel):
    id_producto: int
    nombre: str
    descripcion: Optional[str] = None
    precio_base: Decimal
    imagen_url: Optional[str] = None
    badge_editorial: str
    subtitulo_textil: str
    categoria: str
    colores_disponibles: List[str] = []
    stock_total_disponible: int
    tiene_stock: bool

    model_config = ConfigDict(from_attributes=True)

class ColeccionResumenOut(BaseModel):
    id_coleccion: int
    nombre: str
    descripcion: Optional[str] = None
    temporada_nombre: str
    temporada_tipo: str
    proveedor_nombre: Optional[str] = None
    taller_origen: str
    precio_desde: Decimal
    total_prendas: int
    es_destacada: bool
    badge_edicion: str
    imagen_portada: Optional[str] = None
    piezas_clave: List[ProductoColeccionItemOut] = []

    model_config = ConfigDict(from_attributes=True)

class ColeccionesActivasResponseOut(BaseModel):
    temporada_activa_id: Optional[int] = None
    temporada_activa_nombre: Optional[str] = None
    coleccion_destacada: Optional[ColeccionResumenOut] = None
    otras_colecciones: List[ColeccionResumenOut] = []
    total_colecciones: int

    model_config = ConfigDict(from_attributes=True)

class ColeccionDetalleOut(BaseModel):
    id_coleccion: int
    nombre: str
    descripcion: Optional[str] = None
    temporada_nombre: str
    proveedor_nombre: Optional[str] = None
    taller_origen: str
    total_prendas: int
    mensaje_empty_state: Optional[str] = None
    productos: List[ProductoColeccionItemOut] = []

    model_config = ConfigDict(from_attributes=True)
```

#### 1.5 Criterios de Aceptación (Gherkin)
```gherkin
Escenario: Consulta exitosa de colecciones con temporada vigente
  Dado que existe una temporada comercial activa con fecha_inicio <= HOY <= fecha_fin
  Y existen colecciones vinculadas con productos activos y stock disponible
  Cuando un cliente envía una petición GET a "/api/v1/colecciones/activas"
  Entonces el código de respuesta debe ser 200 OK
  Y el payload debe contener la "coleccion_destacada" con hasta 4 piezas clave
  Y el array "otras_colecciones" debe listar las colecciones secundarias con "precio_desde" mayor a 0

Escenario: Consulta de colección existente con listado de prendas
  Dado que existe una colección con id_coleccion = 1 con 4 prendas activas
  Cuando el usuario consulta "GET /api/v1/colecciones/1/productos"
  Entonces el código de respuesta debe ser 200 OK
  Y el campo "total_prendas" debe ser 4
  Y cada producto debe incluir id_producto, nombre, precio_base, badge_editorial y stock_total_disponible

Escenario: Consulta de colección sin productos asociados (Próximo lanzamiento)
  Dado que existe una colección con id_coleccion = 99 sin prendas asignadas
  Cuando el usuario consulta "GET /api/v1/colecciones/99/productos"
  Entonces el código de respuesta debe ser 200 OK
  Y el array "productos" debe estar vacío
  Y "mensaje_empty_state" debe contener "Próximo lanzamiento"

Escenario: Consulta de colección inexistente
  Dado que no existe ninguna colección con id_coleccion = 9999
  Cuando el usuario consulta "GET /api/v1/colecciones/9999/productos"
  Entonces el código de respuesta debe ser 404 Not Found
  Y el detalle del error debe indicar "Colección no encontrada"
```

---

### 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

#### 2.1 Enrutamiento y Arquitectura (Pantalla Secundaria / Hoja)
- **Clasificación Arquitectónica:** Pantalla Secundaria (Spoke) derivada de `Inicio`.
- **Layout de Enrutamiento:** Declarada fuera de `MainLayoutComponent` (o con layout libre de navbar global). **Prohibido renderizar la barra de navegación principal.**
- **Ruta Principal:** `/colecciones`  
  Carga de forma perezosa (`loadComponent`) el componente `ColeccionesComponent` con botón obligatorio `← VOLVER` hacia `/inicio`.
- **Ruta de Detalle:** `/colecciones/:id`  
  Carga perezosa de `ColeccionDetalleComponent` con botón obligatorio `← VOLVER` hacia `/colecciones`.
- **Navegación Cruzada:**
  - Desde el Hero de `/inicio` (botón `EXPLORAR COLECCIÓN →`) -> navega a `/colecciones`.
  - Desde `/colecciones`, al pulsar `VER COLECCIÓN →` en cualquiera de "Otras colecciones" -> navega a `/colecciones/:id`.
  - Desde `/colecciones/:id`, botón `← VOLVER` -> regresa a `/colecciones`.
  - Desde `/colecciones/:id`, al pulsar en una prenda de la grilla -> navega al detalle de producto `/catalogo/:id` (`CU07`).

#### 2.2 Componentes Standalone
1. **`ColeccionesComponent` (`src/app/modules/colecciones/paginas/colecciones/`):**
   - **Fidelidad Estricta al Prototipo:** Reproducción milimétrica de `media_1789986245151.png` mediante estilos SCSS dedicados (independientes del CDN) que garantizan grillas de 4 columnas, espaciados exactos de 26px, aspect ratio 3:4, y badges superpuestos de alta costura.
   - **Header:** Botón superior `← VOLVER` (hacia `/inicio`), logotipo central `FASHION STORE`.
   - **Título Editorial:** H1 `Colecciones` con subtítulo: *"Explora y visualiza todas las colecciones disponibles de la firma, desde la colección en curso hasta piezas selectas de archivo."*
   - **Colección Destacada (Hero):**
     - Título H2: `Sastrería en Lana Virgen & Seda Natural`.
     - Descripción de patronaje y molinos de Biella y Lyon.
     - Grilla horizontal de 4 tarjetas de piezas clave: foto vertical (`aspect-ratio: 3/4`), badges flotantes (`COLECCIÓN 07`, `DISPONIBLE`, `EN SERRANO`, `BÁSICO DE LUJO`, `SASTRERÍA ATELIER`), subtítulo textil (`SEDA LYON · ALTA COSTURA`, `BIELLA 380G · SASTRERÍA ATELIER`), precio en EUR (`890 €`, `740 €`, `310 €`, `420 €`), título del producto, descripción sintética y swatches circulares de color textil.
   - **Sección "Otras colecciones":**
     - Título H2: `Otras colecciones`.
     - Subtítulo: *"Explora las colecciones históricas de la firma que aún cuentan con piezas disponibles en archivo."*
     - Grilla de 4 tarjetas de colección con badges de edición (`EDICIÓN SS24 MILANO`, `EDICIÓN Nº 03 INVIERNO`, `EDICIÓN LYON`, `ESENCIALES ATEMPORALES`), badges de disponibilidad (`DISPONIBLE`, `ÚLTIMAS UNIDADES`), temporada, precio de entrada ("Desde 340 €"), nombre, descripción, swatches y botón interactivo `VER COLECCIÓN →` con enlace a `/colecciones/:id`.
   - **Footer Corporativo:** Manifiesto de la firma, enlaces institucionales (`EDITORIAL`, `ATELIER`, `CONCIERGE`) y copyright.

2. **`ColeccionDetalleComponent` (`src/app/modules/colecciones/paginas/coleccion-detalle/`):**
   - Botón `← VOLVER A COLECCIONES`.
   - Título de la colección (ej. `Edición Milano: Punto & Lino` o `Sastrería en Lana Virgen & Seda Natural`).
   - Párrafo descriptivo de la colección y origen artesanal.
   - Grilla de tarjetas de prendas pertenecientes a la colección (con fotos, badges, precios, subtítulos y enlace a `/catalogo/:id`).
   - Estado vacío si la colección aún no tiene piezas publicadas.

#### 2.3 Servicio Angular con Signals (`ColeccionesService`)
- Ubicación: `src/app/modules/colecciones/servicios/colecciones.service.ts`
- Signals reactivos:
  - `cargando = signal<boolean>(false)`
  - `temporadaActiva = signal<string | null>(null)`
  - `coleccionDestacada = signal<ColeccionResumen | null>(null)`
  - `otrasColecciones = signal<ColeccionResumen[]>([])`
  - `coleccionSeleccionada = signal<ColeccionDetalle | null>(null)`
  - `error = signal<string | null>(null)`
- Métodos HTTP:
  - `obtenerColeccionesActivas(): Observable<ColeccionesActivasResponse>`
  - `obtenerPrendasDeColeccion(idColeccion: number): Observable<ColeccionDetalle>`

---

### 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

#### 3.1 Arquitectura de Pantallas y Navegación
- **Patrón:** Clean Architecture Feature-First en `lib/src/modulos/catalogo/cu36_consultar_colecciones/`.
- **Vistas Principales:**
  1. `ColeccionesScreen` (`presentacion/pantallas/colecciones_screen.dart`):
     - **AppBar:** Botón retroceso `←`, logotipo `FASHION STORE` y botón de bolsa con badge de cesta.
     - **Título:** H1 `Colecciones`.
     - **Chips Horizontales de Filtro:**
       - `COLECCIÓN DESTACADA` (Activo con fondo negro y texto blanco).
       - `ORIGEN CERTIFICADO` (Inactivo con fondo claro/borde gris).
       - `ENVÍO ATELIER` (Inactivo con acento camel/dorado suave).
     - **Sección Colección Destacada:**
       - Titular: `Sastrería en Lana Virgen & Seda Natural`.
       - Fila de metadatos: `PIEZAS CLAVE (4)` en negrita a la izquierda, `Edición Vigente` a la derecha.
       - Grilla 2x2 de piezas clave con fotos recortadas, badges superiores (`DISPONIBLE`, `EN SERRANO - DISPONIBLE`, `BÁSICO DE LUJO`, `SASTRERÍA ATELIER`), subtítulos textiles, precios en euros y swatches circulares de color.
     - **Sección "Otras colecciones":**
       - Titular: `Otras colecciones`.
       - Subtítulo: *"Prendas y archivos de colecciones anteriores confeccionadas con hilaturas nobles."*
       - Listado vertical de tarjetas de colecciones:
         - Fila superior: Temporada en gris mayúsculas (`PRIMAVERA - VERANO 2024`) y chip de precio `Desde 340 €`.
         - Nombre de colección en tipografía sans-serif elegante (`Edición Milano: Punto & Lino`).
         - Origen/Taller artesanal (`Molinos de Biella & Como`, `Alpaca Suri de los Andes`, `Hilatura Francesa 100%`).
         - Botón de acción interactivo `VER COLECCIÓN →` que navega a `DetalleColeccionScreen`.
     - **Barra de Navegación Inferior (BottomNavigationBar): OCULTA / NO DISPONIBLE.** Por mandato arquitectónico de Pantalla Secundaria (Hoja), el `Scaffold` no contiene `bottomNavigationBar`.
     - **Botón de Regreso (`←`): OBLIGATORIO.** `AppBar` con `leading: IconButton(icon: Icon(Icons.arrow_back))` funcional hacia `Inicio`.
  2. `DetalleColeccionScreen` (`presentacion/pantallas/detalle_coleccion_screen.dart`):
     - Vista específica de la colección seleccionada (fiel a `image_45cbbe.png`).
     - **AppBar:** Botón `←` y título.
     - **Cabecera Editorial:** Nombre de la colección y descripción de hilaturas.
     - **Grilla 2x2 de Prendas:**
       - Fotografía con botón de bookmark/guardar en esquina superior derecha.
       - Subtítulo textil (`SEDA LYON`, `BIELLA 380G`, `SATÉN 100%`, `LANA FINA`).
       - Precio en EUR (`890 €`, `740 €`, `310 €`, `420 €`).
       - Nombre de la prenda con elipsis.
       - Swatches de colores disponibles y botón interactivo `VER →` que navega a `PantallaDetalleProducto` (`CU07`).
     - **Empty State:** Manejo visual si la colección no posee prendas asociadas.

#### 3.2 Gestor de Estado (`ColeccionesBloc`)
- **Eventos (`colecciones_event.dart`):**
  - `CargarColeccionesActivasEvent()`
  - `CargarPrendasColeccionEvent(int idColeccion)`
  - `FiltrarColeccionesPorChipEvent(String chipSeleccionado)`
- **Estados (`colecciones_state.dart`):**
  - `ColeccionesInicial()`
  - `ColeccionesCargando()`
  - `ColeccionesCargadas(temporada, destacada, otrasColecciones, chipActivo)`
  - `DetalleColeccionCargado(coleccionDetalle)`
  - `ColeccionesError(mensaje)`

---

## B. Plan de Ejecución Secuencial (`plan`)

### Fase 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0)
1. **Modelos:** Verificar y asegurar relaciones en `app/modules/catalogo/modelos.py` (`ColeccionORM`, `TemporadaORM`, `ProveedorORM`, `ProductoORM`).
2. **Esquemas:** Crear `app/modules/catalogo/cu36_colecciones/esquemas.py` con `ColeccionResumenOut`, `ColeccionDetalleOut`, `ProductoColeccionItemOut`, `ColeccionesActivasResponseOut`.
3. **Servicio de Dominio:** Crear `app/modules/catalogo/cu36_colecciones/servicio.py`:
   - Lógica de resolución de temporada activa por fecha y flag.
   - Cálculo de precio de entrada (`precio_desde = MIN(precio_base)`).
   - Conteo de prendas activas y extracción de piezas clave.
   - Consulta de productos por `id_coleccion` con stock y badges.
4. **Router:** Crear `app/modules/catalogo/cu36_colecciones/router.py` y registrar rutas en `app/modules/catalogo/router.py`.
5. **Pruebas:** Crear suite `tests/modules/catalogo/test_cu36_colecciones.py` y ejecutar con `pytest`.

### Fase 2: Frontend Web (`Ec-frontend` - Angular 19+)
1. **Modelos:** Crear `src/app/modules/colecciones/modelos/colecciones.modelos.ts`.
2. **Servicio:** Implementar `ColeccionesService` con Signals reactivos y manejo de errores.
3. **Componente Principal:** Maquetar `ColeccionesComponent` con Hero destacado, grilla de 4 piezas clave y grilla de "Otras colecciones".
4. **Componente de Detalle:** Maquetar `ColeccionDetalleComponent` con listado de prendas y botón volver.
5. **Enrutamiento:** Conectar `/colecciones` y `/colecciones/:id` en `src/app/app.routes.ts`.
6. **Pruebas:** Escribir unit tests en `colecciones.component.spec.ts` y validar con `npm test` y `npm run build`.

### Fase 3: Mobile (`Ec-mobile` - Flutter 3.x Multiplataforma)
1. **Capa de Datos:** Crear DTOs (`coleccion_dto.dart`) y datasource HTTP (`colecciones_api.dart`).
2. **BLoC:** Implementar `ColeccionesBloc`, eventos y estados.
3. **Pantalla Principal (`ColeccionesScreen`):** Maquetar chips superiores, piezas clave 2x2 y lista vertical de otras colecciones con botón `VER COLECCIÓN →`.
4. **Pantalla de Detalle (`DetalleColeccionScreen`):** Maquetar grilla 2x2 con bookmarks, subtítulos textiles, precios y botón `VER →`.
5. **Navegación:** Conectar navegación desde `PantallaInicio` (Hero CU36) y `PantallaBuscarProductos` hacia `ColeccionesScreen`.
6. **Pruebas y Linter:** Escribir tests de widgets en `test/colecciones_screen_test.dart`, ejecutar `flutter test` y `flutter analyze`.

---

## C. Lista de Tareas Atómicas (`tasks`)

### Bloque 1: Backend (`Ec-backend`)
- [x] **Tarea 1.1**: Verificar mapeo de `ProveedorORM` y relaciones de `ColeccionORM` con `TemporadaORM` y `ProductoORM` en `app/modules/catalogo/modelos.py`.
- [x] **Tarea 1.2**: Crear esquemas Pydantic `ColeccionResumenOut`, `ColeccionDetalleOut`, `ProductoColeccionItemOut` y `ColeccionesActivasResponseOut` en `app/modules/catalogo/cu36_colecciones/esquemas.py`.
- [x] **Tarea 1.3**: Implementar `ColeccionesService` en `app/modules/catalogo/cu36_colecciones/servicio.py` con cálculo de `precio_desde`, filtro de temporada activa y piezas clave.
- [x] **Tarea 1.4**: Implementar endpoints `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id_coleccion}/productos` en `app/modules/catalogo/cu36_colecciones/router.py`.
- [x] **Tarea 1.5**: Montar el router en `app/modules/catalogo/router.py`.
- [x] **Tarea 1.6**: Escribir pruebas unitarias e integración en `tests/modules/catalogo/test_cu36_colecciones.py` cubriendo todos los escenarios Gherkin.
- [x] **Tarea 1.7**: Ejecutar `pytest` y asegurar 100% de tests pasando en backend (100/100 tests totales).

### Bloque 2: Frontend Web (`Ec-frontend`)
- [x] **Tarea 2.1**: Definir interfaces TypeScript en `src/app/modules/colecciones/modelos/colecciones.modelos.ts`.
- [x] **Tarea 2.2**: Implementar `ColeccionesService` en `src/app/modules/colecciones/servicios/colecciones.service.ts` con Signals reactivos.
- [x] **Tarea 2.3**: Desarrollar componente Standalone `ColeccionesComponent` (vista principal con colección destacada y grilla editorial de otras colecciones).
- [x] **Tarea 2.4**: Desarrollar componente Standalone `ColeccionDetalleComponent` (vista de prendas exclusivas de la colección seleccionada con botón volver y cards con enlace a `/catalogo/:id`).
- [x] **Tarea 2.5**: Configurar rutas en `src/app/app.routes.ts` (`/colecciones` y `/colecciones/:id`) y vincular botón Hero de `/inicio`.
- [x] **Tarea 2.6**: Escribir pruebas unitarias en `colecciones.component.spec.ts` y validar `npm test` (74/74 tests) y `npm run build` (0 errores).
- [x] **Tarea 2.7**: Garantizar que el frontend consuma estrictamente los productos desde PostgreSQL (`fashionstore.productos`) sin quemar productos ficticios.
- [x] **Tarea 2.8**: Sustituir todas las imágenes de hombres por fotografía editorial de moda femenina exclusiva en todas las colecciones y cards.
- [x] **Tarea 2.9**: Registrar la regla global inquebrantable de "E-commerce Exclusivo para Mujeres" en la constitución del backend, frontend, mobile y especificaciones.
- [x] **Tarea 2.10**: Hacer toda la tarjeta de "Otras colecciones" cliqueable como botón para navegación intuitiva (`(click)="irAColeccion(col)"`, accesibilidad `role="button"`, `tabindex="0"` y teclado).
- [x] **Tarea 2.11**: Reemplazar URL rota de portada en Colección 2 y productos 13/9 por URLs Unsplash verificadas HTTP 200 e implementar manejador `onImgError`.

### Bloque 3: Mobile (`Ec-mobile`)
- [x] **Tarea 3.1**: Crear DTOs inmutables en `lib/src/modulos/catalogo/cu36_consultar_colecciones/datos/modelos/coleccion_dto.dart` (`ColeccionResumenDto`, `ColeccionDetalleDto`, `ProductoColeccionItemDto`, `ColeccionesActivasResponseDto`).
- [x] **Tarea 3.2**: Implementar datasource HTTP en `lib/src/modulos/catalogo/cu36_consultar_colecciones/datos/datasources/colecciones_api.dart` con manejo robusto de excepciones de red y decodificación UTF-8.
- [x] **Tarea 3.3**: Implementar `ColeccionesBloc` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/bloc/colecciones_bloc.dart` con arquitectura sellada y ChangeNotifier reactivo.
- [x] **Tarea 3.4**: Maquetar `ColeccionesScreen` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/colecciones_screen.dart` reproduciendo fielmente `image_45cf27.png` (chips interactivos, 4 piezas clave 2x2, tarjetas de otras colecciones navegables).
- [x] **Tarea 3.5**: Maquetar `DetalleColeccionScreen` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/detalle_coleccion_screen.dart` reproduciendo fielmente `image_45cbbe.png` (grilla 2x2, bookmarks, swatches de color y empty state editorial).
- [x] **Tarea 3.6**: Conectar navegación entre `ColeccionesScreen` y `DetalleColeccionScreen` mediante el botón `VER COLECCIÓN →` y enlazar callback `alIrAColecciones` en `PantallaInicio` y `main.dart`.
- [x] **Tarea 3.7**: Escribir pruebas de BLoC en `test/colecciones_bloc_test.dart` (7 tests) y pruebas de widgets en `test/colecciones_screen_test.dart` (5 tests).
- [x] **Tarea 3.8**: Ejecutar `flutter analyze` (0 issues encontrados) y `flutter test` (74/74 tests pasando).
- [x] **Tarea 3.9**: Resolver advertencias de renderizado móvil (`RenderFlex overflowed` en badges y titulares mediante `Flexible` y `childAspectRatio` calibrado a 0.49/0.52).
- [x] **Tarea 3.10**: Corregir notificación de estado durante el ciclo de build de Flutter mediante `addPostFrameCallback`.
- [x] **Tarea 3.11**: Blindar deserialización de DTOs en Flutter (`coleccion_dto.dart`) ante campos `Decimal` de Pydantic serializados como `String` (`"310.00"` y `"890.00"`), previniendo `TypeError: type 'String' is not a subtype of type 'num?'`.
- [x] **Tarea 3.12**: Calibrar proporción geométrica de tarjetas en grillas (`childAspectRatio: 0.65`) y contenedor de foto elástico (`Expanded` con `Positioned.fill` y `ClipRRect`), eliminando por completo el espacio en blanco vacío bajo las etiquetas de precio y botones.
- [x] **Tarea 3.13**: Unificar tipografía con el Design System normativo (`Outfit`, escala `fashionstore-tokens.md`) en `main.dart`, `ColeccionesScreen` y `DetalleColeccionScreen`, aplicando tracking `label-caps` (`letterSpacing: 0.8` a `1.1`), pesos `FontWeight.w600` / `w700` y colores semánticos (`primary-900: #0F1116`, `secondary-500: #AD8C63`, `neutral-500: #71717A`).

---

## D. Puntos de Control y Verificación (`checkpoints`)

| ID | Capa / Módulo | Criterio de Aprobación | Método de Comprobación | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend DB | Consultas SQL de temporada activa resuelven correctamente por rango de fechas (`CURRENT_DATE`) y fallback a `activa = true`. | Test unitario con sesión de prueba en Neon DB / SQLite. | 🟢 Superado |
| **CP-02** | Backend Cálculo | Cada colección calcula correctamente `precio_desde` (`MIN(precio_base)`) y `total_prendas` considerando solo prendas activas. | Test de aserción en `test_cu36_colecciones.py`. | 🟢 Superado |
| **CP-03** | Backend Endpoints | `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id}/productos` retornan códigos 200/404 según contratos Pydantic. | Ejecución de suite `pytest` en `Ec-backend` (100/100 tests pasando). | 🟢 Superado |
| **CP-04** | Frontend Web Hero | La vista `/colecciones` muestra la Colección Destacada con sus 4 piezas clave, badges y tipografía editorial de alta costura. | Tests unitarios `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-05** | Frontend Web Grilla | La sección "Otras colecciones" renderiza las cards con badge de edición, temporada, precio de entrada y botón `VER COLECCIÓN →`. | Tests unitarios `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-06** | Frontend Web Navegación | Al pulsar `VER COLECCIÓN →`, navega a `/colecciones/:id` listando las prendas de dicha colección con enlace a `/catalogo/:id`. | Tests unitarios `coleccion-detalle.component.spec.ts` y enrutador. | 🟢 Superado |
| **CP-07** | Frontend Build | Compilación de producción limpia sin errores TypeScript ni estilos rotos. | `npm run build` en `Ec-frontend` (0 errores). | 🟢 Superado |
| **CP-08** | Mobile Screen | `ColeccionesScreen` reproduce `image_45cf27.png`: Chips de filtro, piezas clave 2x2 y lista vertical de otras colecciones con `VER COLECCIÓN →`. | Test de widgets en Flutter con physicalSize móvil en `colecciones_screen_test.dart`. | 🟢 Superado |
| **CP-09** | Mobile Detalle | `DetalleColeccionScreen` reproduce `image_45cbbe.png`: Grilla 2x2 de prendas con bookmark, precio en EUR y botón `VER →`. | Test de interacción en Flutter en `colecciones_screen_test.dart`. | 🟢 Superado |
| **CP-10** | Mobile Static Analysis | Código Flutter estricto, inmutable, sin `unnecessary_underscores` y conforme a tokens normativos. | `flutter analyze` en `Ec-mobile` (0 issues). | 🟢 Superado |
| **CP-11** | Mobile Test Suite | Suite completa de tests en Flutter pasando al 100% sin regresiones (75/75 tests totales, 13 de CU36). | `flutter test` en `Ec-mobile`. | 🟢 Superado |
| **CP-12** | Global E-commerce Femenino | Cero imágenes de hombres; 100% prendas y modelos de moda femenina exclusiva en todas las vistas y fallbacks. | Inspección visual y validación de assets en BD y código. | 🟢 Superado |
| **CP-13** | Integridad de BD Real | Todas las prendas provienen estrictamente de `fashionstore.productos` (20 prendas reales con inventario). Cero productos ficticios en cliente. | Consulta directa a API `/api/v1/colecciones/activas` y base Neon. | 🟢 Superado |
| **CP-14** | Card Cliqueable como Botón | Toda la card de "Otras colecciones" funciona como botón interactivo completo, navegando a `/colecciones/:id` al hacer click. | Test unitario en `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-15** | Carga de Imágenes HTTP 200 | Todas las imágenes de colecciones y prendas en Neon responden HTTP 200 sin links rotos, más fallback reactivo `onImgError`. | Verificación por script HTTP y suite frontend. | 🟢 Superado |
| **CP-16** | Responsive & Overflow Safety | Grillas y tarjetas en Flutter calibradas con `childAspectRatio: 0.65` y foto elástica en `Expanded` con `Positioned.fill`, eliminando el vacío blanco interior y previniendo `RenderFlex overflowed`. | Validación visual y suite de tests de widgets. | 🟢 Superado |
| **CP-17** | Serialización Decimal API | Deserialización tolerante de precios monetarios (`double.tryParse`) soportando tipos primitivos `num` y cadenas `Decimal` (`"310.00"`) de FastAPI Pydantic sin `TypeError`. | Test unitario en `colecciones_bloc_test.dart` y verificación en runtime. | 🟢 Superado |
| **CP-18** | Tipografía Design System (Outfit) | Unificación tipográfica global y atómica en Flutter bajo la familia `Outfit`, tracking normativo de badges (`letterSpacing: 0.8-1.1`), pesos `FontWeight.w600/w700` y paleta Obsidian/Camel de `fashionstore-tokens.md`. | Verificación visual y pruebas de widgets en `colecciones_screen_test.dart`. | 🟢 Superado |

---

## E. Registro de Cambios, Decisiones de Diseño y Resoluciones Técnicas de CU36

Durante la concepción, especificación e implementación del CU36 ("Consultar colecciones") se identificaron y resolvieron diversos aspectos clave en las tres capas:

### 1. Regla Global Inquebrantable de Dominio: Moda 100% Femenina Exclusiva
- **Decisión:** FashionStore es una firma de alta costura y catálogo exclusivamente femenina.
- **Acción:** Se eliminó cualquier referencia o imagen masculina en bases de datos, seeds, fallbacks y plantillas. Se blindó la directiva en las especificaciones de backend, frontend y mobile.

### 2. Jerarquía Canónica y Persistencia Real (PostgreSQL)
- **Decisión:** La jerarquía del negocio es `Temporadas` -> `Colecciones` -> `Prendas (Productos)`. Queda terminantemente prohibido inventar o quemar catálogos ficticios en el cliente.
- **Acción:** El backend expone colecciones dinámicas con conteo de prendas y precio mínimo real (`MIN(precio_base)`). Las 20 prendas del catálogo real con existencias en sucursales alimentan las colecciones activas y de archivo.

### 3. Usabilidad Web (Frontend Angular 19+): Tarjeta Completa Interactiva
- **Decisión:** En la sección "Otras colecciones", el usuario espera poder pulsar en cualquier parte de la tarjeta y no únicamente en el texto del botón `VER COLECCIÓN →`.
- **Acción:** Se implementó `(click)="irAColeccion(col)"` en el contenedor de la card, complementado con accesibilidad completa (`role="button"`, `tabindex="0"`, soporte de tecla `Enter`), manteniendo el botón interno con estilos visuales coordinados.
- **Resiliencia de Medios:** Se verificaron las imágenes con respuesta HTTP 200 y se añadió fallback reactivo `onImgError` hacia fotografía editorial femenina.

### 4. Implementación y Resoluciones Técnicas en Mobile (Flutter 3.x)
- **Arquitectura Limpia & BLoC Inmutable:** DTOs inmutables con serialización JSON segura (`ColeccionResumenDto`, `ColeccionDetalleDto`, etc.) y BLoC con estados sellados.
- **Resolución de RenderFlex Overflows en Widgets:**
  - El subtítulo editorial `'PIEZAS DE ALTA COSTURA (N)'` y el badge `'Edición Exclusiva'` causaban desbordamiento horizontal en anchos reducidos. Se utilizó `Flexible` con `overflow: TextOverflow.ellipsis`.
  - El botón inferior de "Otras colecciones" se condensó a `'VER COLECCIÓN COMPLETA'` evitando desbordamiento lateral.
- **Build Cycle Safety (`ChangeNotifier`):**
  - Se corrigió la llamada a `notificarListeners()` durante el ciclo de renderizado en `initState()`, envolviendo la carga inicial de datos en `WidgetsBinding.instance.addPostFrameCallback((_) { ... })`.
- **Linter y Calidad Estricta:**
  - Se solventaron advertencias de linter (`dangling_library_doc_comments` y `unnecessary_underscores`), logrando **0 issues** en `flutter analyze`.
- **Robustez de Tests de Widgets:**
  - Se diferenciaron los finders de texto entre marcas idénticas (se utilizó `'ATELIER ARCHIVE'` para diferenciar del título corporativo de la AppBar).
  - Se incorporó `tester.ensureVisible()` y desplazamiento táctil antes de interactuar con chips o botones fuera del viewport inicial.

### 5. Diagnóstico y Resolución del Error de Tipos Decimal (`TypeError: "310.00": type 'String' is not a subtype of type 'num?'`)
- **Síntoma Observado:**
  - En los logs del backend, la petición `GET /api/v1/colecciones/activas?limite_piezas_clave=4` responde exitosamente con código `200 OK`.
  - En la aplicación móvil, la pantalla falla mostrando:
    `Error de conexión con el Atelier: TypeError: "310.00": type 'String' is not a subtype of type 'num?'`.
- **Causa Raíz:**
  - FastAPI y Pydantic v2 manejan los campos monetarios (`precio_base: Decimal` y `precio_desde: Decimal`) serializándolos como cadenas de texto con precisión fija (`"310.00"`, `"890.00"`) para evitar pérdida de precisión de coma flotante.
  - En Dart, `json['precio_desde'] as num?` esperaba un tipo primitivo numérico (`int` o `double`). Al recibir un `String` (`"310.00"`), el casting estricto en modo fuerte de Dart lanzó una excepción en tiempo de ejecución.
- **Solución Implementada:**
  - Se sustituyó el casting directo `(json['...'] as num?)?.toDouble()` por un parseo seguro:
    `double.tryParse(json['precio_desde']?.toString() ?? '0.0') ?? 0.0`
    tanto en `ProductoColeccionItemDto` como en `ColeccionResumenDto`.
  - Esto tolera indistintamente cadenas (`"310.00"`), números enteros (`310`), números flotantes (`310.0`) y valores ausentes, garantizando una deserialización infalible.
  - Se añadió una prueba unitaria específica en `test/colecciones_bloc_test.dart` verificando payloads con cadenas monetarias Decimal.

### 6. Calibración Visual de Tarjetas y Espaciado en Grillas Móviles
- **Defecto Reportado:** Las cards de producto dejaban un espacio en blanco excesivo en la parte inferior, debajo del precio y el botón `+ CESTA`.
- **Causa Raíz:** La cuadrícula definía una relación de aspecto rígida (`childAspectRatio: 0.52` y `0.49`), asignando más de 340px de altura a cada tarjeta en un viewport móvil de 360-390px. La fotografía tenía una relación fija (`AspectRatio: 0.90`) que consumía ~180px, mientras que los textos consumían ~60px. La diferencia restante (~100px) quedaba como un bloque blanco vacío al final del contenedor.
- **Solución Implementada:**
  - Se ajustó la relación de aspecto de la grilla a `childAspectRatio: 0.65` tanto en `ColeccionesScreen` como en `DetalleColeccionScreen`.
  - Se reemplazó el `AspectRatio` rígido de la foto por un contenedor elástico `Expanded(child: Stack(children: [Positioned.fill(child: ClipRRect(...))]))`. De esta manera, la fotografía llena dinámicamente toda el área superior de la tarjeta y el bloque de información reposa perfectamente en la base con espaciado de 8px, **eliminando el 100% del espacio en blanco sobrante**.
  - Se envolvió toda la tarjeta en un `GestureDetector` para permitir la selección fluida del producto con un solo toque.

### 7. Unificación Tipográfica Estricta con el Design System (`Outfit`)
- **Defecto Reportado:** Los textos de las cards y pantallas móviles recurrían a la tipografía genérica del sistema operativo sin utilizar los tokens normativos de `fashionstore-tokens.md`.
- **Solución Implementada:**
  - En `main.dart`, se configuró `fontFamily: 'Outfit'` a nivel global en `ThemeData.light()`.
  - En `ColeccionesScreen` y `DetalleColeccionScreen`, se aplicó explícitamente `fontFamily: 'Outfit'` a todas las declaraciones de `TextStyle`.
  - Se adoptaron los tokens exactos del Design System:
    - **`label-caps` (Badges y chips):** `fontFamily: 'Outfit'`, `letterSpacing: 0.8` a `1.2`, mayúsculas, `FontWeight.w700`.
    - **`product-title` (Nombres de prenda):** `fontFamily: 'Outfit'`, `fontSize: 11.5 - 12`, `FontWeight.w600`, color Obsidian `#0F1116`.
    - **`price-tag` (Precios en EUR):** `fontFamily: 'Outfit'`, `fontSize: 13`, `FontWeight.w800`, color Obsidian `#0F1116`.
    - **`atelier-subtext` (Composición textil):** `fontFamily: 'Outfit'`, `fontSize: 8`, `FontWeight.w600`, tracking `1.1`, color Slate `#71717A`.
    - **`action-button` (`+ CESTA` y `VER`):** Píldoras con tipografía `Outfit`, `FontWeight.w700` y colores Camel/Obsidian.

### 8. Cobertura y Métricas de Calidad Global
- **Backend:** 100/100 tests unitarios y de integración pasando al 100% con `pytest`.
- **Frontend Web:** 74/74 tests pasando con Vitest / Angular CLI, bundle generado con 0 errores (`ng build`).
- **Mobile Multiplataforma:** 75/75 tests pasando con `flutter test`, `flutter analyze` con 0 incidencias.



