# Especificacion Formal de Requisitos: CU22 - Gestionar Prendas, Productos y Variantes (SKUs)

**ID del Caso de Uso:** CU22  
**Nombre:** Gestionar Prendas, Productos y Variantes (SKUs)  
**Paquete Arquitectonico:** `gestion_operativa` / `catalogo`  
**Modulo Backend:** `app/modules/gestion_operativa/cu22_prendas_productos`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu22_prendas_productos`  
**Actor Principal:** Administrador  
**Actores Secundarios (Lectura):** Cliente, Empleado, Sistema (Catalogo publico y variantes comerciales)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Riesgo Alto: Nucleo de definicion de productos, inventario, precios y variantes de venta)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

En la cadena omnicanal de alta costura **FashionStore**, una prenda o producto representa una pieza de vestuario de diseno (ej. "Vestido Plisado Seda Atelier", "Blazer Cruzado Lana Fina", "Camisa Sastrera Cuello Italiano"). Cada prenda se define con caracteristicas base: denominacion comercial unica, descripcion editorial de su confeccion, precio base, estado de publicacion (activo/inactivo) y su obligatoria clasificacion jerarquica en una categoria del arbol taxonomico estructurado en CU23.

Sin embargo, en el comercio textil de alta gama, las piezas no se venden ni se gestionan en inventario como entes abstractos, sino a traves de sus especificaciones fisicas tangibles: **Variantes de Producto (SKUs)**. Una variante resulta de la combinatoria exacta entre una prenda base, una talla comercial (XS, S, M, L, XL, 38, etc.) y un color textil definido con su muestra cromatica #HEX.

El caso de uso **CU22 - Gestionar Prendas, Productos y Variantes (SKUs)** proporciona al administrador las capacidades operativas y de gobierno para:
1. Dar de alta, consultar, actualizar y gestionar el ciclo de vida de las prendas y modelos de coleccion.
2. Construir interactivamente la matriz fisica de variantes por lote combinando tallas y colores maestros.
3. Generar y controlar el identificador unico de almacenamiento y venta (**SKU - Stock Keeping Unit**) bajo un formato normalizado.
4. Establecer precios especificos o recargos por variante (ej. tallas especiales o acabados textiles premium).
5. Proteger la integridad referencial y financiera impidiendo la eliminacion fisica destructiva de productos o variantes que registren stock en inventario, movimientos de almacen, items en carrito o reservas activas de probador virtual, canalizando el retiro a traves de baja logica (`activo = False`).

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta concebida exclusivamente para:
- La experiencia de compra y exploracion del cliente final (vitrina editorial, busqueda facetada, probador virtual con Realidad Aumentada AR, bolsa de compra y pasarela de pagos).
- La consulta rapida de disponibilidad y asistencia en piso de venta por dependientes de boutique.

La creacion, configuracion, parametrizacion de precios, edicion taxonomica y generacion de matrices de SKUs son responsabilidades administrativas y operativas de back-office que demandan interfaces de escritorio complejas, formularios de alta densidad de datos y flujos de control empresarial. Por tanto, esta operativa pertenece con exclusividad al panel de administracion web (`Ec-frontend`).

### 2.2 Consumo en Modo Lectura (Read-Only) por la Aplicacion Movil
La aplicacion movil participa en este dominio funcional unicamente como consumidor pasivo en modo lectura (`Read-Only`), consultando los productos y sus variantes activas mediante los endpoints publicos del catalogo (`GET /api/v1/productos`, `GET /api/v1/productos/{id_producto}`). 

Por consiguiente, el caso de uso CU22 **queda formalmente excluido de desarrollo en Ec-mobile**: no se implementaran pantallas de administracion, formularios, controladores BLoC ni repositorios de mutacion en la aplicacion movil, concentrando el desarrollo en `Ec-backend` y `Ec-frontend`.

---

## 3. Alcance y Trazabilidad Documental

1. **Documento Maestro de Requisitos:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md)
   - Seccion 2.1.2 CU22 Lineas 825-840: "CU22. Gestionar productos: permitir al administrador registrar, consultar, modificar y eliminar las prendas comercializadas por la empresa".
   - Lineas 1314-1316, 2542-2545 y 3156-3165 (Matriz de trazabilidad y casos de prueba).
2. **Esquema Relacional DDL (PostgreSQL / Alembic):**
   - Tabla `fashionstore.productos`: `id_producto`, `id_categoria` (FK NOT NULL), `id_coleccion` (FK NULL), `id_proveedor` (FK NULL), `nombre` (VARCHAR 200, NOT NULL, INDEX), `descripcion` (TEXT), `precio_base` (NUMERIC 10,2 > 0), `imagen_url` (VARCHAR 500), `modelo_ar_url` (VARCHAR 500), `activo` (BOOLEAN DEFAULT TRUE), `creado_en` (TIMESTAMPTZ).
   - Tabla `fashionstore.variantes_producto`: `id_variante`, `id_producto` (FK CASCADE), `id_talla` (FK NOT NULL), `id_color` (FK NOT NULL), `sku` (VARCHAR 50, UNIQUE, NOT NULL), `precio_extra` (NUMERIC 10,2 DEFAULT 0), constraint `UNIQUE (id_producto, id_talla, id_color)`.
   - Tablas dependientes de integridad: `fashionstore.inventario_sucursal`, `fashionstore.movimientos_inventario`, `fashionstore.detalles_pedido`, `fashionstore.items_carrito`, `fashionstore.reservas_probador`.
3. **Referencias de Dominio y Arquitectura:**
   - `.agents/skills/fashionstore-backend-sdd/references/dominio.md`: Invariantes de prendas, combinatorias de variantes y reglas de inventario.
   - `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md`: Tokens de disenador, paleta Obsidian/Slate/Camel, tipografia Outfit.

---

## 4. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL)

- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema debera exigir autenticacion JWT valida con rol `administrador` (`require_roles(["administrador"])`) para todas las operaciones de mutacion (creacion, edicion, cambio de estado y eliminacion) sobre productos (`/api/v1/admin/productos`) y variantes (`/api/v1/admin/productos/{id}/variantes`).

- **# AC-2 (Por Evento - Creacion de Prenda / Producto Base):**  
  Cuando el administrador solicite el alta de un nuevo producto especificando `nombre`, `descripcion`, `precio_base`, `id_categoria` y opcionalmente `id_coleccion`, `imagen_url`, `modelo_ar_url`, el sistema debera:
  1. Normalizar el nombre removiendo espacios iniciales, finales y redundantes.
  2. Verificar que `precio_base` sea estrictamente mayor que cero (`precio_base > 0`).
  3. Verificar que no exista otro producto con el mismo nombre comercial (insensible a mayusculas/minusculas).
  4. Validar la existencia de la categoria en `fashionstore.categorias`.
  5. Si se proporciona `id_coleccion`, validar su existencia en `fashionstore.colecciones`.
  6. Registrar el producto con `activo = True` y retornar codigo HTTP `201 Created` con la entidad completa.

- **# AC-3 (Conducta No Deseada - Nombre de Producto Duplicado o Invalido):**  
  Si el nombre comercial del producto ya se encuentra registrado en el sistema, o si el nombre tiene una longitud inferior a 3 caracteres, entonces el sistema debera rechazar la solicitud respondiendo con codigo HTTP `409 Conflict` (`PRODUCTO_DUPLICADO`) o HTTP `422 Unprocessable Entity`.

- **# AC-4 (Conducta No Deseada - Categoria Inexistente o Invalida):**  
  Si el `id_categoria` suministrado no corresponde a ningun registro activo en la tabla `fashionstore.categorias`, entonces el sistema debera rechazar la operacion con codigo HTTP `404 Not Found` o `422 Unprocessable Entity` bajo el codigo `CATEGORIA_NO_ENCONTRADA`.

- **# AC-5 (Por Evento - Generacion y Registro de Matriz de Variantes / SKUs):**  
  Cuando el administrador envie una lista de variantes fisicas para un producto existente, especificando para cada combinacion `id_talla`, `id_color` y opcionalmente `precio_extra` o `sku` personalizado, el sistema debera:
  1. Validar que cada `id_talla` exista en `fashionstore.tallas`.
  2. Validar que cada `id_color` exista en `fashionstore.colores`.
  3. Generar automaticamente el SKU estandarizado si no se suministra uno manual, siguiendo el patron canonico: `[COD_CATEGORIA]-[ID_PRODUCTO]-[COD_TALLA]-[HEX_COLOR]` (o formato textil normalizado `PREFIX-TALLA-COLOR` en mayusculas).
  4. Validar que la tupla compuesta `(id_producto, id_talla, id_color)` sea estrictamente unica.
  5. Verificar que el `sku` resultante no exista en `fashionstore.variantes_producto`.
  6. Persistir las variantes asociadas y responder con codigo HTTP `201 Created` con el detalle de las variantes creadas.

- **# AC-6 (Conducta No Deseada - Colision de SKU o Variante Duplicada):**  
  Si durante el registro de variantes se intenta insertar una combinacion `(id_producto, id_talla, id_color)` ya existente para dicho producto, o si un SKU generado/suministrado ya esta asignado a otra variante en el sistema, entonces el sistema debera abortar la transaccion y responder con codigo HTTP `409 Conflict` con el detalle `VARIANTE_DUPLICADA` o `SKU_DUPLICADO`.

- **# AC-7 (Por Evento - Sobreescritura Opcional de Precio por Variante):**  
  Cuando una variante comercial requiera un recargo o sobreescritura de precio por motivo textil o de patronaje, el sistema debera admitir el campo `precio_extra >= 0`. El precio final calculado de venta para esa variante sera `precio_base + precio_extra`.

- **# AC-8 (Por Evento - Actualizacion Editorial de Producto):**  
  Cuando el administrador modifique los datos de una prenda existente (nombre, descripcion, precio base, categoria, coleccion, imagenes), el sistema debera validar que el nuevo nombre no colisione con otro producto distinto (`id_producto != actual`) y persistir los cambios respondiendo con codigo HTTP `200 OK`.

- **# AC-9 (Por Estado - Bloqueo de Eliminacion Fisica por Integridad Referencial):**  
  Mientras un producto o cualquiera de sus variantes posea registros vinculados en inventario (`fashionstore.inventario_sucursal`), movimientos de kardex (`fashionstore.movimientos_inventario`), pedidos historicos (`fashionstore.detalles_pedido`), carritos de compra (`fashionstore.items_carrito`) o reservas de probador (`fashionstore.reservas_probador`), si el administrador solicita la eliminacion fisica (`DELETE`), entonces el sistema debera denegar la eliminacion y responder con codigo HTTP `409 Conflict` bajo el codigo `PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS` o `VARIANTE_CON_DEPENDENCIAS_OPERATIVAS`.

- **# AC-10 (Por Evento - Baja Logica y Desactivacion de Prenda o Variante):**  
  Cuando un producto no deba seguir disponible para venta en vitrina pero mantenga historial transaccional, el administrador podra cambiar su estado a `activo = False`. El sistema debera actualizar la bandera, ocultar el producto del catalogo de cara al cliente y retornar HTTP `200 OK` confirmando la desactivacion sin destruir datos historicos.

- **# AC-11 (Por Evento - Consultas Administrativas y Publicas):**  
  - Para usuarios publicos: `GET /api/v1/productos` y `GET /api/v1/productos/{id}` responderan exclusivamente productos con `activo = True`, incluyendo sus variantes activas, precios calculados e imagenes.
  - Para administradores: `GET /api/v1/admin/productos` soportara paginacion, filtros por categoria, coleccion, estado (activos/inactivos) y termino de busqueda, retornando ademas la cuenta de variantes asociadas y el stock consolidado total.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- **# AC-12 (Ubicuo - Componente Standalone con OnPush y Signals):**  
  El modulo de gestion de productos se implementara como componente Standalone (`standalone: true`), con deteccion de cambios `ChangeDetectionStrategy.OnPush`, enrutamiento en `/admin/productos` bajo proteccion de `authGuard` y gestion de estado reactivo mediante **Angular Signals** (`signal()`, `computed()`).

- **# AC-13 (Ubicuo - Tokens Institucionales y Consistencia Atelier):**  
  La interfaz utilizara el contenedor editorial `max-w-[1440px] px-6 py-8 mx-auto`, fondo claro `bg-slate-50`, tarjetas boutique blancas `bg-white border-slate-200`, acentos corporativos Camel (`#AD8C63`), botones Obsidian (`bg-[#0F172A] hover:bg-black text-white`) y tipografia **Outfit**.

- **# AC-14 (Por Evento - Integracion en el Hub Central /admin):**  
  El Hub Central de Administracion (`AdminDashboardComponent` en `/admin`) debera incorporar una tercera tarjeta boutique de acceso directo:
  - Titulo: *"Prendas y Variantes"*
  - Categoria/Subtitulo: *"Catalogo Maestro de Articulos"*
  - Descripcion: *"Gestion integral de prendas de alta costura, precios base, asignacion de categorias y parametrizacion de matrices de SKUs."*
  - Badge: *"Gestion de Catalogo"*
  - Boton de accion: *"Gestionar Prendas"*, enlazando con `routerLink="/admin/productos"`.

- **# AC-15 (Por Evento - Boton Editorial de Retorno al Panel Principal):**  
  En la parte superior de la vista `/admin/productos`, sobre el titulo principal, se ubicara el boton vectorial minimalista:
  - Diseno: Flecha SVG con desplazamiento sutil (`group-hover:-translate-x-1`) y texto `"Volver al Panel Principal"`.
  - Accion: Enlace `routerLink="/admin"`, permitiendo el retorno fluido al panel central.

- **# AC-16 (Por Evento - Formulario Reactivo y Selector Jerarquico de Categoria):**  
  Cuando el administrador seleccione `+ NUEVA PRENDA` o editar una existente, se desplegara un modal o vista de formulario tipado con `NonNullableFormBuilder` que incluya:
  - Nombre comercial de la prenda.
  - Selector en arbol jerarquico de categorias (alimentado desde CU23, diferenciando visualmente categorias principales y subcategorias).
  - Precio base en euros/moneda local (validacion de valor positivo).
  - Descripcion editorial de la pieza textil.
  - Conmutador de publicacion (Activo / Inactivo).

- **# AC-17 (Por Evento - Generador Interactivo de Matriz de Variantes por Lote):**  
  Dentro de la gestion de la prenda, el administrador dispondra de un generador reactivo de variantes:
  1. Seleccion multiple de tallas disponibles (chips o checkboxes basados en las tallas registradas en CU23).
  2. Seleccion multiple de colores textiles (swatches interactivos con representacion visual del codigo `#HEX` provenientes de CU23).
  3. Boton *"Generar Combinaciones"*: computa en memoria el producto cartesiano `(Tallas Seleccionadas x Colores Seleccionados)`.
  4. Tabla editable de variantes generadas: permite previsualizar cada SKU propuesto, ingresar un recargo o sobreescritura de precio individual (`precio_extra`) y remover combinaciones no deseadas antes de confirmar el guardado.

- **# AC-18 (Conducta No Deseada - Captura Visual de Conflictos 409 y Preservacion de Estado):**  
  Si el backend rechaza una operacion debido a colision de SKU, producto duplicado o restriccion de dependencias (HTTP 409), la aplicacion web desplegara un Luxury Banner de error explicativo sin cerrar el modal ni purgar los campos completados, permitiendo al administrador corregir el conflicto inmediatamente.

---

## 5. Matriz de Cobertura de Criterios de Aceptacion

| ID Criterio | Nombre del Criterio | Tipo EARS | Plataforma | Codigo HTTP / Regla |
|:---|:---|:---:|:---:|:---:|
| **AC-1** | Seguridad y Control de Acceso RBAC | Ubicuo | Backend | HTTP 401 / 403 (Rol admin) |
| **AC-2** | Alta de Prenda / Producto Base | Por Evento | Backend | HTTP 201 (`precio_base > 0`) |
| **AC-3** | Prevencion de Producto Duplicado | No Deseada | Backend | HTTP 409 `PRODUCTO_DUPLICADO` / 422 |
| **AC-4** | Validacion de Categoria Existente | No Deseada | Backend | HTTP 404 / 422 `CATEGORIA_NO_ENCONTRADA` |
| **AC-5** | Generacion y Alta de Matriz de Variantes | Por Evento | Backend | HTTP 201 (SKU normalizado) |
| **AC-6** | Prevencion de Colision de SKU / Variante | No Deseada | Backend | HTTP 409 `VARIANTE_DUPLICADA` / `SKU_DUPLICADO` |
| **AC-7** | Sobreescritura Opcional de Precio | Por Evento | Backend | `precio_extra >= 0` |
| **AC-8** | Actualizacion Editorial de Producto | Por Evento | Backend | HTTP 200 OK |
| **AC-9** | Bloqueo por Integridad Referencial | Por Estado | Backend | HTTP 409 `DEPENDENCIAS_OPERATIVAS` |
| **AC-10** | Baja Logica y Desactivacion de Prenda | Por Evento | Backend | HTTP 200 OK (`activo = False`) |
| **AC-11** | Consultas Publicas y Administrativas | Por Evento | Backend | HTTP 200 OK (Filtros y conteos) |
| **AC-12** | Componente Standalone y Signals | Ubicuo | Frontend Web | Angular 19+ / OnPush |
| **AC-13** | Tokens de Diseno y Estetica Atelier | Ubicuo | Frontend Web | Slate/Camel/Obsidian / Outfit |
| **AC-14** | Integracion en Hub Central /admin | Por Evento | Frontend Web | Tarjeta 3 en AdminDashboard |
| **AC-15** | Boton Editorial de Retorno a /admin | Por Evento | Frontend Web | `routerLink="/admin"` |
| **AC-16** | Formulario y Selector Jerarquico | Por Evento | Frontend Web | NonNullableFormBuilder / Arbol CU23 |
| **AC-17** | Generador de Matriz de Variantes Lote | Por Evento | Frontend Web | Matriz Tallas x Colores |
| **AC-18** | Luxury Banners ante Conflictos 409 | No Deseada | Frontend Web | Preservacion reactiva de estado |

---

## 6. Proximos Pasos en el Ciclo SDD
Una vez aprobada formalmente esta especificacion de requisitos (Fase 1), se continuara con la **Fase 2: Diseno Tecnico**, donde se formalizaran:
- Los esquemas Pydantic v2 de entrada y salida (`ProductoCrear`, `ProductoDetalle`, `VarianteLoteCrear`, etc.).
- El servicio de dominio con generador de SKU estandarizado y logica de bloqueo por dependencias de inventario.
- Los contratos de endpoints administrativos y publicos en FastAPI.
- El arbol de componentes Angular, servicio HTTP y generador matricial reactivo para `Ec-frontend`.
