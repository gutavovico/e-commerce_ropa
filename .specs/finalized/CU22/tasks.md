# Plan de Tareas y Oleadas de Implementacion: CU22 - Gestionar Prendas, Productos y Variantes (SKUs)

**ID del Caso de Uso:** CU22  
**Nombre:** Gestionar Prendas, Productos y Variantes (SKUs)  
**Paquete Arquitectonico:** `gestion_operativa` / `catalogo`  
**Modulo Backend:** `app/modules/gestion_operativa/cu22_prendas_productos`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu22_prendas_productos`  
**Referencias:** `.specs/changes/CU22/spec.md` y `.specs/changes/CU22/design.md`  
**Estado:** En Revision de Planificacion (Fase 3 - Plan de Tareas)  

---

## 1. Estrategia General de Implementacion

El caso de uso CU22 centraliza el catalogo maestro de prendas textiles de alta gama y la parametrizacion de sus matrices tangibles de venta (SKUs por combinatoria de tallas y colores).

### 1.1 Exclusion Ratificada de la Aplicacion Movil (Ec-mobile)
Se ratifica formalmente la exclusion de desarrollo de componentes de gestion en `Ec-mobile`. La aplicacion movil participa en este dominio exclusivamente en modo lectura (`Read-Only`) consumiendo los endpoints publicos del catalogo (`GET /api/v1/productos`, `GET /api/v1/productos/{id}`). Por consiguiente, no se programan tareas para la plataforma movil en este plan.

### 1.2 Secuenciacion de Oleadas
El trabajo se estructura en 3 oleadas secuenciales estrictas:
1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + Pydantic v2):**
   Modelos ORM, esquemas de validacion Pydantic v2, funcion pura de generacion determinista de SKUs corporativos, jerarquia de excepciones de dominio tipadas, servicios transaccionales con producto cartesiano atomico y comprobacion previa de dependencias operativas (inventario, pedidos, reservas) antes de borrado fisico, routers publicos y administrativos con proteccion RBAC, y suite de pruebas automatizadas Pytest al 100% en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Modelos DTO en TypeScript, servicio `ProductosAdminService` con Angular Signals, integracion de la 3ra tarjeta boutique en `AdminDashboardComponent` adaptando la rejilla a `grid-cols-1 md:grid-cols-3`, componente Standalone `ProductosAdminComponent` (OnPush, contenedor institucional `max-w-[1440px] px-6`, boton editorial de retorno al panel central `/admin`), modales interactivos para alta/edicion con selector jerarquico de categorias de CU23 y generador matricial interactivo con swatches #HEX y calculo de precio final, captura de errores 409/422 con Luxury Banners sin perdida de datos, y suite de pruebas unitarias Jasmine/Karma cubriendo criterios `# AC-12` al `# AC-18`.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD):**
   Verificacion de suites completas locales en verde (`pytest`, `ng test`, `ng build`), promocion formal de artefactos hacia `.specs/finalized/CU22/`, consolidacion permanente en `.specs/modules/gestion_operativa/CU22-gestionar-productos.md`, y actualizacion de `CHANGELOG.md`.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + Pydantic v2)

- [x] **Tarea 1.1: Modelos ORM (ProductoORM con relacion a categorias y VarianteProductoORM con constraint uq_variante_producto_talla_color) y verificacion de tablas en esquema fashionstore**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/modelos.py`
    - `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/__init__.py`
  - **Descripcion:** Implementar el mapeo ORM de las entidades sobre el esquema `fashionstore` en PostgreSQL:
    * `ProductoORM`: Mapeo de `fashionstore.productos` con clave foranea `id_categoria` (ForeignKey a `fashionstore.categorias.id_categoria`, ondelete="RESTRICT"), `id_coleccion` (ForeignKey a `fashionstore.colecciones.id_coleccion`, ondelete="SET NULL", opcional), `nombre` unico e indexado (VARCHAR 200), `descripcion` (TEXT), `precio_base` (NUMERIC 10,2 > 0), `imagen_url` (VARCHAR 500), `modelo_ar_url` (VARCHAR 500), `activo` (BOOLEAN, default True), `creado_en` (TIMESTAMPTZ con valor por defecto UTC). Relaciones con `CategoriaORM`, `ColeccionORM` y coleccion en cascada con `VarianteProductoORM`.
    * `VarianteProductoORM`: Mapeo de `fashionstore.variantes_producto` con `id_producto` (ForeignKey a `fashionstore.productos.id_producto`, ondelete="CASCADE"), `id_talla` (ForeignKey a `fashionstore.tallas.id_talla`, ondelete="RESTRICT"), `id_color` (ForeignKey a `fashionstore.colores.id_color`, ondelete="RESTRICT"), `sku` (VARCHAR 64, unique, not null, indexado), `precio_extra` (NUMERIC 10,2, default 0.00), `activo` (BOOLEAN, default True), `creado_en`. Restriccion compuesta explicita: `UniqueConstraint("id_producto", "id_talla", "id_color", name="uq_variante_producto_talla_color")`. Relaciones con `ProductoORM`, `TallaORM` y `ColorORM`.
  - **Criterios Mapeados:** `# AC-2`, `# AC-5`, `# AC-6`.
  - **Verificacion:** Inspeccion de metadatos de SQLAlchemy 2.0 y compatibilidad DDL con esquema PostgreSQL.

- [x] **Tarea 1.2: Schemas Pydantic v2 (ProductoCrearIn, ProductoActualizarIn, VarianteItemIn, MatrizGenerarIn, DTOs de salida) y funcion pura del generador determinista de SKU**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/esquemas.py`
    - `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/utilidades.py`
  - **Descripcion:**
    * Schemas de Producto:
      - `ProductoBaseIn`: Campos base con validadores de limpieza de espacios redundantes y longitud minima de 3 caracteres en `nombre`, `id_categoria > 0`, `precio_base > 0`.
      - `ProductoCrearIn`: Extiende `ProductoBaseIn` con `activo: bool = True`.
      - `ProductoActualizarIn`: Campos opcionales para edicion parcial con validador de nombre.
      - `ProductoEstadoIn`: Payload para conmutacion logica de visibilidad (`activo: bool`).
      - `ProductoResumenOut`: DTO para listados administrativos con campos agregados `total_variantes` y `stock_total`.
      - `ProductoDetalleOut`: DTO enriquecido que incluye la coleccion anidada de `variantes: List[VarianteOut]`.
    * Schemas de Variantes y Matriz:
      - `VarianteItemIn`: `id_talla`, `id_color`, `sku` opcional, `precio_extra >= 0`.
      - `MatrizGenerarIn`: `ids_tallas: List[int]`, `ids_colores: List[int]`, `precio_extra_defecto: Decimal >= 0`.
      - `VarianteActualizarIn`: Edicion de `sku`, `precio_extra` y estado `activo`.
      - `VarianteOut`: DTO con codigos/nombres de talla y color, `sku`, `precio_extra`, `precio_final = precio_base + precio_extra` y `stock_disponible`.
    * Utilidades y Generador Corporativo de SKU:
      - Funcion `slugify_text(texto: str, max_len: int)` para conversion a mayusculas alfanumericas purgadas de tildes y caracteres especiales mediante descomposicion Unicode.
      - Funcion pura `generar_sku_corporativo(nombre_producto, codigo_talla, nombre_color, id_producto)` produciendo el patron determinista `FS-[SLUG_PROD]-[COD_TALLA]-[SLUG_COLOR]` truncado a 64 caracteres maximo.
  - **Criterios Mapeados:** `# AC-2`, `# AC-5`, `# AC-7`.
  - **Verificacion:** Pruebas unitarias de esquemas y validacion del algoritmo generador de SKUs con cadenas complejas, acentos y simbolos.

- [x] **Tarea 1.3: Jerarquia de excepciones de dominio (ProductoDuplicadoError, SkuDuplicadoError, VarianteDuplicadaError, ProductoConDependenciasError, VarianteConDependenciasError)**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/errores.py`
  - **Descripcion:** Implementar las clases de error tipadas derivadas de `DomainError`:
    * `ProductoNoEncontradoError` (HTTP 404, `PRODUCTO_NO_ENCONTRADO`).
    * `ProductoDuplicadoError` (HTTP 409, `PRODUCTO_DUPLICADO`).
    * `CategoriaInexistenteError` (HTTP 422, `CATEGORIA_INEXISTENTE`).
    * `VarianteNoEncontradaError` (HTTP 404, `VARIANTE_NO_ENCONTRADA`).
    * `SkuDuplicadoError` (HTTP 409, `SKU_DUPLICADO`).
    * `VarianteDuplicadaError` (HTTP 409, `VARIANTE_DUPLICADA`).
    * `ProductoConDependenciasError` (HTTP 409, `PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS`).
    * `VarianteConDependenciasError` (HTTP 409, `VARIANTE_CON_DEPENDENCIAS_OPERATIVAS`).
  - **Criterios Mapeados:** `# AC-3`, `# AC-4`, `# AC-6`, `# AC-9`.
  - **Verificacion:** Pruebas de instanciacion confirmando que cada excepcion exponga codigo y status code correctos.

- [x] **Tarea 1.4: Servicios de dominio (ServicioGestionProductos y ServicioGestionVariantes) con generador de producto cartesiano atomico y comprobacion de dependencias operativas previo a borrado fisico**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/servicio.py`
  - **Descripcion:** Construir la logica transaccional del catalogo:
    * `ServicioGestionProductos`:
      - `crear_producto`: Validar unicidad del nombre comercial insensible a mayusculas/minusculas, verificar existencia de categoria en `fashionstore.categorias` y coleccion opcional, persistir con `activo = True`.
      - `listar_productos_publicos`: Consulta paginada/filtrada devolviendo unicamente prendas con `activo = True` y sus variantes activas.
      - `listar_productos_admin`: Soporte para filtros por categoria, coleccion, estado activo/inactivo, busqueda por nombre, calculando el recuento de variantes y agregacion de stock desde `fashionstore.inventario_sucursal`.
      - `obtener_producto_por_id`: Retorna la ficha completa con variantes y detalles asociados.
      - `actualizar_producto`: Chequeo de colision de nombre con otros registros (`id_producto != actual`) y actualizacion atómica.
      - `cambiar_estado_producto`: Conmutacion logica de `activo` (baja/alta logica sin destruccion de datos).
      - `eliminar_producto`: Verificacion rigurosa de dependencias operacionales. Si existen registros con cantidad > 0 o existencias en `fashionstore.inventario_sucursal`, `fashionstore.detalles_pedido`, `fashionstore.items_carrito`, `fashionstore.reservas_probador` o `fashionstore.movimientos_inventario`, se interrumpe lanzando `ProductoConDependenciasError` (HTTP 409). Si no existen dependencias, ejecuta borrado fisico (`session.delete`).
    * `ServicioGestionVariantes`:
      - `generar_matriz_variantes`: Recibe lista de tallas y colores, valida su existencia, calcula el producto cartesiano `(Tallas x Colores)`, detecta combinaciones ya existentes para omitirlas o alertarlas, genera SKUs unicos via `generar_sku_corporativo`, valida colisiones globales de SKU y tupla `(id_producto, id_talla, id_color)`, y persiste en lote (`session.add_all`).
      - `crear_variante_individual`: Alta puntual de variante con validacion de constraint unico.
      - `actualizar_variante`: Modificacion de SKU, `precio_extra` o estado de publicacion.
      - `cambiar_estado_variante`: Conmutacion logica de `activo`.
      - `eliminar_variante`: Comprobacion de dependencias operativas en inventario, pedidos y reservas para esa variante especifica previo al borrado fisico. Lanza `VarianteConDependenciasError` (HTTP 409) ante bloqueos.
  - **Criterios Mapeados:** `# AC-2`, `# AC-5`, `# AC-6`, `# AC-7`, `# AC-8`, `# AC-9`, `# AC-10`.
  - **Verificacion:** Pruebas unitarias de servicios simulando transacciones exitosas, colisiones y deteccion de dependencias.

- [x] **Tarea 1.5: Endpoints publicos (/api/v1/productos) y endpoints administrativos (/api/v1/admin/productos/*, /api/v1/admin/variantes/*) con proteccion RBAC (require_roles(["administrador"]))**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu22_prendas_productos/router.py`
    - `Ec-backend/app/modules/gestion_operativa/router.py`
    - `Ec-backend/app/main.py`
  - **Descripcion:** Implementar y registrar los controladores FastAPI:
    * Endpoints Publicos (sin token):
      - `GET /api/v1/productos`: Consulta de catalogo abierto de productos activos.
      - `GET /api/v1/productos/{id_producto}`: Ficha publica de la prenda y sus variantes disponibles.
    * Endpoints Administrativos (protegidos con `require_roles(["administrador"])`):
      - `GET /api/v1/admin/productos`: Listado con filtros y agregaciones.
      - `POST /api/v1/admin/productos`: Alta de prenda base (retorna HTTP 201).
      - `GET /api/v1/admin/productos/{id_producto}`: Detalle de gestion con variantes.
      - `PUT /api/v1/admin/productos/{id_producto}`: Modificacion editorial (HTTP 200).
      - `PATCH /api/v1/admin/productos/{id_producto}/estado`: Conmutacion de `activo`.
      - `DELETE /api/v1/admin/productos/{id_producto}`: Baja fisica protegida (HTTP 204).
      - `POST /api/v1/admin/productos/{id_producto}/variantes/matriz`: Generador cartesiano en lote (HTTP 201).
      - `POST /api/v1/admin/productos/{id_producto}/variantes`: Alta puntual de variante (HTTP 201).
      - `GET /api/v1/admin/productos/{id_producto}/variantes`: Listado de variantes de la prenda.
      - `PUT /api/v1/admin/variantes/{id_variante}`: Modificacion de variante.
      - `PATCH /api/v1/admin/variantes/{id_variante}/estado`: Conmutacion de visibilidad de variante.
      - `DELETE /api/v1/admin/variantes/{id_variante}`: Eliminacion de variante con chequeo de dependencias (HTTP 204).
    * Integracion del router en `modules/gestion_operativa/router.py` y verificacion de montaje en `main.py`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-11`.
  - **Verificacion:** Pruebas de acceso con token admin, rechazo 401 sin token, rechazo 403 con rol cliente e inspeccion de documentacion OpenAPI en `/docs`.

- [x] **Tarea 1.6: Suite de pruebas automatizadas en tests/modules/catalogo/test_cu22_productos_variantes.py verificando los criterios # AC-1 al # AC-11 con pytest al 100% en verde**
  - **Archivo:** `Ec-backend/tests/modules/catalogo/test_cu22_productos_variantes.py`
  - **Descripcion:** Implementar una suite exhaustiva cubriendo todos los criterios de aceptacion de backend:
    * `# AC-1`: Rechazo 401 sin credenciales y 403 para usuarios con rol cliente en rutas `/admin/*`.
    * `# AC-2`: Alta correcta de producto (HTTP 201) con `precio_base > 0` y normalizacion de espacios en nombre.
    * `# AC-3`: Rechazo 409 (`PRODUCTO_DUPLICADO`) ante nombres repetidos y 422 si nombre < 3 caracteres.
    * `# AC-4`: Rechazo 422/404 (`CATEGORIA_INEXISTENTE`) ante `id_categoria` inexistente.
    * `# AC-5`: Generacion masiva de variantes mediante matriz cartesiana con SKU estandarizado `FS-[PROD]-[TALLA]-[COLOR]` (HTTP 201).
    * `# AC-6`: Rechazo 409 ante SKU duplicado o combinacion repetida `(id_producto, id_talla, id_color)`.
    * `# AC-7`: Sobreescritura de precio con `precio_extra >= 0` y verificacion de `precio_final = precio_base + precio_extra`.
    * `# AC-8`: Modificacion editorial de producto validando colision de nombres contra terceros.
    * `# AC-9`: Bloqueo de eliminacion fisica (HTTP 409 `PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS`) cuando existen dependencias operacionales; borrado fisico exitoso (HTTP 204) cuando esta libre.
    * `# AC-10`: Desactivacion comercial mediante baja logica (`activo = False`) retornando HTTP 200 y ocultando el item del catalogo publico.
    * `# AC-11`: Consultas de catalogo publico (solo activos) y panel administrativo (con filtros, busqueda y conteos).
  - **Criterios Mapeados:** `# AC-1` al `# AC-11`.
  - **Verificacion:** Ejecucion de `pytest tests/modules/catalogo/test_cu22_productos_variantes.py` con 100% de aserciones en verde.

---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript para productos, variantes y payloads de matriz en productos.dto.ts**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/modelos/producto.dto.ts`
  - **Descripcion:** Definir los contratos tipados para la capa visual y de transporte:
    * `ProductoResumenAdmin`: Entidad para listado con conteos de variantes y stock global.
    * `VarianteAdmin`: Entidad de variante con codigo de talla, nombre y color #HEX, SKU, recargo y precio final.
    * `ProductoDetalleAdmin`: Entidad completa que extiende el resumen e incluye la coleccion de variantes.
    * `ProductoCrearPayload` y `ProductoActualizarPayload`: Payloads para mutaciones de prendas.
    * `MatrizVariantesPayload`: Payload con listas de `ids_tallas` e `ids_colores` para generacion en lote.
    * `VarianteEdicionItem`: Modelo de fila para la tabla editable de la matriz generada.
  - **Criterios Mapeados:** `# AC-12`.
  - **Verificacion:** Validacion de tipos con `npx tsc --noEmit`.

- [x] **Tarea 2.2: Servicio HTTP ProductosAdminService con inyeccion de HttpClient y senales reactivas (Signals)**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/servicios/productos-admin.service.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/servicios/productos-admin.service.spec.ts`
  - **Descripcion:** Desarrollar el servicio Angular `ProductosAdminService`:
    * Inyeccion de dependencias moderna con `inject(HttpClient)` y lectura de token Bearer.
    * Estado reactivo expuesto con **Angular Signals**: `productos = signal<ProductoResumenAdmin[]>([])`, `productoSeleccionado = signal<ProductoDetalleAdmin | null>(null)`, `variantes = signal<VarianteAdmin[]>([])`, `cargando = signal<boolean>(false)`, `guardando = signal<boolean>(false)`, `error = signal<string | null>(null)`, `mensajeExito = signal<string | null>(null)`.
    * Metodos de persistencia de productos: `cargarProductos`, `cargarProductoPorId`, `crearProducto`, `actualizarProducto`, `cambiarEstadoProducto`, `eliminarProducto`.
    * Metodos de persistencia de variantes: `generarMatrizVariantes`, `actualizarVariante`, `eliminarVariante`, `limpiarMensajes`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-12`.
  - **Verificacion:** Pruebas unitarias de servicio utilizando `HttpTestingController`.

- [x] **Tarea 2.3: Actualizacion de AdminDashboardComponent para incorporar la 3ra tarjeta boutique "Prendas y Variantes (SKUs)" adaptando la rejilla a grid-cols-1 md:grid-cols-3**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Actualizar el contenedor de tarjetas en `AdminDashboardComponent` adaptando la disposicion a `grid-cols-1 md:grid-cols-3` para albergar con equilibrio visual los tres modulos operativos.
    * Incorporar la 3ra tarjeta boutique:
      - Titulo: *"Prendas y Variantes (SKUs)"*.
      - Categoria superior: *"Catalogo Maestro de Articulos"*.
      - Descripcion: *"Gestion integral de prendas de alta costura, precios base, asignacion de categorias y parametrizacion de matrices de SKUs."*.
      - Badge: *"Prendas y Variantes"* con acento `#AD8C63`.
      - Icono vectorial SVG de alta costura (percha/prenda).
      - Puntos clave: *"Alta comercial de modelos, descripciones y precios"* y *"Generador interactivo de matriz de variantes y SKUs"*.
      - Boton de accion: *"Gestionar Prendas"*, enlazando con `routerLink="/admin/productos"`.
    * Actualizar las pruebas unitarias de `AdminDashboardComponent` para verificar el renderizado y enlaces de las 3 tarjetas operativas.
  - **Criterios Mapeados:** `# AC-14`.
  - **Verificacion:** Renderizado visual equilibrado de las 3 tarjetas y ejecucion limpia de la suite de pruebas del dashboard.

- [x] **Tarea 2.4: Componente Standalone ProductosAdminComponent con OnPush, max-w-[1440px] px-6, boton de retorno al panel principal y registro de ruta protegida /admin/productos en app.routes.ts**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.scss`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Crear componente Standalone `ProductosAdminComponent` configurado con `ChangeDetectionStrategy.OnPush`.
    * Registrar la ruta protegida `/admin/productos` con `canActivate: [authGuard]` en `app.routes.ts`.
    * Disenar la interfaz en contenedor `max-w-[1440px] px-6 py-8 mx-auto` con tokens institucionales (fondo `bg-slate-50`, tarjetas blancas, bordes `slate-200`, acentos Camel `#AD8C63` y tipografia Outfit).
    * Barra superior minimalista corporativa con identificador institucional y enlaces a `PANEL PRINCIPAL` y `MI CUENTA`.
    * Boton vectorial de retorno superior con enlace `routerLink="/admin"` y texto `"Volver al Panel Principal"` con animacion sutil `group-hover:-translate-x-1`.
    * Barra de herramientas con buscador reactivo, filtro desplegable de categorias, selector de estado (todos, activos, inactivos) y boton principal Obsidian `+ NUEVA PRENDA`.
    * Tabla principal de prendas que presenta: miniatura, denominacion comercial, categoria, precio base, estado de publicacion, total de variantes registradas, stock global agregado y botones de accion (Gestionar Variantes, Editar Prenda, Conmutar Estado, Eliminar).
  - **Criterios Mapeados:** `# AC-12`, `# AC-13`, `# AC-15`.
  - **Verificacion:** Compilacion de componente y verificacion de navegacion a `/admin/productos`.

- [x] **Tarea 2.5: Modal de Prenda (alta/edicion con selector de categoria jerarquica de CU23) y Modal de Matriz de Variantes (seleccion multiple con chips/swatches, calculo cartesiano reactivo, previsualizacion de SKU y sobreescritura de precio)**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.ts`
  - **Descripcion:**
    * Modal de Prenda:
      - Formulario tipado con `NonNullableFormBuilder`.
      - Campos para denominacion, precio base, descripcion y conmutador de publicacion.
      - Selector jerarquico de categorias alimentado reactivamente mediante `AtributosAdminService` de CU23, discriminando visualmente categorias principales y subcategorias subordinadas.
    * Modal de Generacion de Matriz de Variantes:
      - Paso 1: Seleccion interactiva de tallas disponibles (chips seleccionables) y colores (swatches con muestra cromatica real del codigo `#HEX`).
      - Paso 2: Boton *"Generar Combinaciones"* que calcula en memoria el producto cartesiano `(Tallas x Colores)`.
      - Paso 3: Tabla reactiva de variantes generadas con previsualizacion del SKU normalizado `FS-...`, input editable para sobreescritura de recargo `precio_extra`, calculo dinamico de `precio_final = precio_base + precio_extra` y boton individual para remover combinaciones no deseadas.
      - Paso 4: Boton de confirmacion para registrar el lote mediante `POST /api/v1/admin/productos/{id}/variantes/matriz`.
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`.
  - **Verificacion:** Pruebas interactivas de modales, seleccion multiple de atributos y generacion matricial reactiva.

- [x] **Tarea 2.6: Manejo de errores 409 y 422 mediante Luxury Banners sin perdida de datos del formulario y pruebas unitarias con Jasmine/Karma verificando # AC-12 al # AC-18**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/productos-admin.component.spec.ts`
  - **Descripcion:**
    * Implementacion de Luxury Banners explicativos (`bg-rose-50 border-rose-200 text-rose-800`) desplegados en la cabecera del modal o de la tabla cuando el backend retorne respuestas 409 (colision de SKU, producto duplicado, bloqueo por dependencias de inventario) o 422 (campos invalidos), manteniendo intactos los datos capturados en el formulario.
    * Suite exhaustiva de pruebas unitarias con Jasmine/Karma:
      - `# AC-12`: Inicializacion con OnPush y Signals reactivas.
      - `# AC-13` y `# AC-15`: Renderizado del contenedor institucional y boton de retorno a `/admin`.
      - `# AC-14`: Navegacion e integracion desde el hub central.
      - `# AC-16`: Apertura de modal de prenda, inicializacion de formulario reactivo y selector de categoria.
      - `# AC-17`: Generador de variantes por lote, computo de producto cartesiano y reactividad del precio final.
      - `# AC-18`: Captura visual de conflictos 409 y preservacion de valores digitados.
  - **Criterios Mapeados:** `# AC-12` al `# AC-18`.
  - **Verificacion:** Ejecucion de `ng test --watch=false` logrando 100% de pruebas en verde.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y DoD

- [x] **Tarea 3.1: Ejecucion de suites completas (pytest en Ec-backend, ng test y ng build en Ec-frontend)**
  - **Descripcion:**
    * Ejecutar suite completa de `Ec-backend` con `pytest` y confirmar que todos los tests pasen en verde sin regresiones.
    * Ejecutar suite completa de `Ec-frontend` con `ng test --watch=false` y confirmar el 100% de pruebas en verde.
    * Ejecutar compilacion productiva de Angular con `ng build` verificando cero errores y cero advertencias criticas de TypeScript.
  - **Criterios Mapeados:** Calidad integral, estabilidad y no regresion.
  - **Verificacion:** Retorno exitoso (codigo 0) en las ejecuciones de pytest, ng test y ng build.

- [x] **Tarea 3.2: Promocion de artefactos desde .specs/changes/CU22/ hacia .specs/finalized/CU22/ y consolidacion en .specs/modules/gestion_operativa/CU22-gestionar-productos.md**
  - **Descripcion:**
    * Promover `spec.md`, `design.md` y `tasks.md` desde `.specs/changes/CU22/` hacia `.specs/finalized/CU22/`.
    * Consolidar la documentacion permanente del modulo en `.specs/modules/gestion_operativa/CU22-gestionar-productos.md`.
    * Limpiar el directorio temporal de trabajo `.specs/changes/CU22/`.
  - **Criterios Mapeados:** Conformidad con el ciclo de gobernanza SDD.
  - **Verificacion:** Verificacion de persistencia de archivos en `.specs/finalized/CU22/`.

- [x] **Tarea 3.3: Registro formal del incremento en CHANGELOG.md y limpieza del directorio temporal**
  - **Descripcion:**
    * Registrar el incremento de version correspondiente a CU22 en `CHANGELOG.md` y `.specs/CHANGELOG.md`.
    * Documentar endpoints implementados, vistas de administracion web, algoritmo determinista de SKUs corporativos, generador matricial interactivo y reglas de integridad referencial.
    * Emitir reporte de Definicion de Terminado (DoD) para aprobacion final.
  - **Criterios Mapeados:** Trazabilidad documental y cierre formal del caso de uso.
  - **Verificacion:** Auditoria de texto sin emojis, sin comandos remotos de Git y consistencia de enlaces.

---

## 3. Matriz de Dependencias entre Tareas

```
[Oleada 1: Backend]
  Tarea 1.1 (Modelos ORM)
       │
       ▼
  Tarea 1.2 (Schemas Pydantic + SkuGen) ──► Tarea 1.3 (Excepciones Dominio)
       │                                              │
       └──────────────────────┬───────────────────────┘
                              ▼
                    Tarea 1.4 (Servicios Dominio)
                              │
                              ▼
                    Tarea 1.5 (Routers HTTP RBAC)
                              │
                              ▼
                    Tarea 1.6 (Pytest Suite Backend)

[Oleada 2: Frontend Web]
  Tarea 2.1 (Modelos TypeScript)
       │
       ▼
  Tarea 2.2 (Servicio HTTP Signals) ──► Tarea 2.3 (Tarjeta 3 en AdminDashboard)
       │                                              │
       └──────────────────────┬───────────────────────┘
                              ▼
                    Tarea 2.4 (Componente Standalone y Rutas)
                              │
                              ▼
                    Tarea 2.5 (Modales de Prenda y Matriz)
                              │
                              ▼
                    Tarea 2.6 (Luxury Banners y Jasmine/Karma)

[Oleada 3: Cierre y DoD]
  Tarea 3.1 (Verificacion Cruzada) ──► Tarea 3.2 (Promocion SDD) ──► Tarea 3.3 (Changelog y Cierre)
```

---

## 4. Matriz de Trazabilidad Requisitos vs. Tareas

| ID Requisito | Descripcion del Requisito | Tarea Backend | Tarea Frontend | Tarea Cierre |
|:---|:---|:---:|:---:|:---:|
| **AC-1** | Seguridad y Control de Acceso RBAC | Tarea 1.5, 1.6 | Tarea 2.2 | Tarea 3.1 |
| **AC-2** | Alta de Prenda / Producto Base | Tarea 1.1, 1.2, 1.4, 1.6 | Tarea 2.2, 2.5 | Tarea 3.1 |
| **AC-3** | Prevencion de Producto Duplicado | Tarea 1.3, 1.4, 1.6 | Tarea 2.6 | Tarea 3.1 |
| **AC-4** | Validacion de Categoria Existente | Tarea 1.3, 1.4, 1.6 | Tarea 2.5 | Tarea 3.1 |
| **AC-5** | Generacion y Alta de Matriz de Variantes | Tarea 1.1, 1.2, 1.4, 1.6 | Tarea 2.2, 2.5 | Tarea 3.1 |
| **AC-6** | Prevencion de Colision de SKU / Variante | Tarea 1.1, 1.3, 1.4, 1.6 | Tarea 2.6 | Tarea 3.1 |
| **AC-7** | Sobreescritura Opcional de Precio | Tarea 1.2, 1.4, 1.6 | Tarea 2.5 | Tarea 3.1 |
| **AC-8** | Actualizacion Editorial de Producto | Tarea 1.4, 1.6 | Tarea 2.2, 2.5 | Tarea 3.1 |
| **AC-9** | Bloqueo por Integridad Referencial Pre-Eliminacion | Tarea 1.3, 1.4, 1.6 | Tarea 2.6 | Tarea 3.1 |
| **AC-10** | Baja Logica y Desactivacion de Prenda | Tarea 1.4, 1.6 | Tarea 2.2, 2.4 | Tarea 3.1 |
| **AC-11** | Consultas Publicas y Administrativas | Tarea 1.5, 1.6 | Tarea 2.2, 2.4 | Tarea 3.1 |
| **AC-12** | Componente Standalone con Signals y OnPush | - | Tarea 2.1, 2.2, 2.4, 2.6 | Tarea 3.1 |
| **AC-13** | Tokens de Diseno y Estetica Atelier | - | Tarea 2.4, 2.6 | Tarea 3.1 |
| **AC-14** | Integracion en el Hub Central /admin | - | Tarea 2.3 | Tarea 3.1 |
| **AC-15** | Boton Editorial de Retorno a /admin | - | Tarea 2.4, 2.6 | Tarea 3.1 |
| **AC-16** | Formulario Reactivo y Selector Jerarquico | - | Tarea 2.5, 2.6 | Tarea 3.1 |
| **AC-17** | Generador de Matriz de Variantes por Lote | - | Tarea 2.5, 2.6 | Tarea 3.1 |
| **AC-18** | Luxury Banners ante Conflictos 409 | - | Tarea 2.6 | Tarea 3.1 |

---

## 5. Criterios de Aceptacion y Definicion de Terminado (DoD)

Para considerar formalmente cerrado el caso de uso CU22, se deben satisfacer al 100% las siguientes condiciones:
1. **Modelado y Persistencia:** Tablas `fashionstore.productos` y `fashionstore.variantes_producto` correctamente mapeadas e integradas en SQLAlchemy 2.0 con restricciones de unicidad activas.
2. **Generador Corporativo de SKU:** Formato canonico `FS-[PROD]-[TALLA]-[COLOR]` determinista, sin acentos ni caracteres especiales, asegurando unicidad en base de datos.
3. **Integridad Referencial:** Bloqueo estricto con HTTP 409 ante intentos de eliminar fisicamente prendas o variantes con existencias en inventario, movimientos de almacen, pedidos o reservas de probador.
4. **Seguridad RBAC:** Todas las mutaciones y consultas administrativas restringidas al rol `administrador`.
5. **Experiencia Web Editorial:** Interfaz Standalone en `/admin/productos` alineada a los tokens Atelier (fondo claro, Camel `#AD8C63`, Obsidian `#0F172A`, Slate y tipografia Outfit), con boton de retorno hacia `/admin`, integracion de la 3ra tarjeta en `AdminDashboardComponent`, selector jerarquico de categorias y generador interactivo matricial.
6. **Captura Visual de Errores:** Errores 409 y 422 presentados con Luxury Banners sin perdida del estado del formulario ni cierres destructivos de modal.
7. **Pruebas Automatizadas al 100% en Verde:**
   - Backend: Suite `test_cu22_productos_variantes.py` pasando al 100% sin regresiones en las suites existentes (CU21, CU23).
   - Frontend: Pruebas unitarias de componentes y servicios en Jasmine/Karma pasando al 100% con `ng test --watch=false`.
   - Compilacion de produccion web (`ng build`) completada con cero errores.
8. **Gobernanza y Cero Emojis:** Artefactos promovidos a `.specs/finalized/CU22/`, documentacion consolidada en `.specs/modules/gestion_operativa/CU22-gestionar-productos.md`, registro en `CHANGELOG.md` y verificacion absoluta de cero emojis y cero comandos de Git remoto.

---

## 6. Estado de Ejecucion y Checkpoint

- **Oleada 1: Backend (Ec-backend):** Completada al 100% (`[x]`). Modelos ORM, esquemas Pydantic v2, generador determinista de SKU corporativo, excepciones de dominio, servicios transaccionales con matriz cartesiana y endpoints RBAC validados con 23/23 tests en verde (156/156 tests globales pasando sin regresiones).
- **Oleada 2: Frontend Web (Ec-frontend):** Completada al 100% (`[x]`). DTOs tipados, servicio HTTP con Signals, incorporacion de la 3ra tarjeta en `AdminDashboardComponent`, componente `ProductosAdminComponent` Standalone con OnPush, selector jerarquico de categorias, generador matricial interactivo con computo de SKU y precio final, Luxury Banners para conflictos 409/422 y suite unitaria al 100% (110/110 tests globales pasando en verde, compilacion de produccion AOT con cero errores).
- **Oleada 3: Cierre y DoD:** Completada al 100% (`[x]`). Verificacion cruzada automatizada, promocion de artefactos a `.specs/finalized/CU22/`, consolidacion de modulo permanente en `.specs/modules/gestion_operativa/CU22-gestionar-productos.md` y registro exhaustivo en `CHANGELOG.md` y `.specs/CHANGELOG.md` bajo la version 1.8.0.


