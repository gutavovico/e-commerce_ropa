# Especificacion Formal de Requisitos: CU23 - Gestionar Categorias, Tallas y Colores

**ID del Caso de Uso:** CU23  
**Nombre:** Gestionar Categorias, Tallas y Colores  
**Paquete Arquitectonico:** `gestion_operativa`  
**Modulo Backend:** `app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Actor Principal:** Administrador  
**Actores Secundarios (Lectura):** Cliente, Empleado, Sistema (Catalogo publico y variantes)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Riesgo Medio-Alto: Afecta la taxonomia completa del catalogo, clasificacion jerarquica, generacion de SKUs y variantes de inventario)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

La plataforma omnicanal **FashionStore** comercializa colecciones exclusivas de alta costura femenina que demandan una clasificacion taxonomica precisa y una parametrizacion estricta de atributos textiles. Las prendas se estructuran mediante una jerarquia de categorias (ej. Prendas Superiores -> Blusas, Blazers; Vestidos -> Vestidos de Noche, Vestidos Midi), y se comercializan fisicamente y digitalmente a traves de variantes de producto parametrizadas por talla y color.

El caso de uso **CU23 - Gestionar Categorias, Tallas y Colores** proporciona a los administradores corporativos las herramientas de gestion para:
1. Definir, actualizar y organizar el arbol taxonomico de categorias de producto, soportando categorias principales y subcategorias con prevencion estricta de ciclos jerarquicos.
2. Estandarizar la escala de tallas comerciales (ej. XS, S, M, L, XL, o numericas 36, 38, 40) garantizando un orden secuencial numerico predecible para su despliegue en filtros y selectores de compra.
3. Configurar la paleta cromatica textil corporativa con denominaciones de diseno unicas y codigos hexadecimales estandarizados (`#HEX`) para la representacion visual precisa de muestras de color (swatches) en tienda web y aplicaciones moviles.
4. Salvaguardar la integridad referencial del catalogo comercial, impidiendo la eliminacion destructiva de categorias con prendas vinculadas, o de tallas y colores asignados a variantes de producto activas.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta orientada exclusivamente a los perfiles de cara al cliente final (Customer Experience, Catalogo Editorial, Vestidor Virtual con Realidad Aumentada, Carrito y Checkout) y a los operarios de boutique fisica en tareas de consulta rapida.

La administracion y configuracion de atributos maestros del catalogo (categorias jerarquicas, parametrizacion de tallas comerciales y codificacion hexadecimal de paletas textiles) constituye una funcion estrictamente editorial, estrategica y de back-office que se ejecuta con exclusividad a traves del panel de administracion web (`Ec-frontend`).

### 2.2 Consumo Pasivo por la Aplicacion Movil
La aplicacion movil participa en este dominio exclusivamente en calidad de consumidor de solo lectura (`Read-Only`), accediendo a los atributos ya persistidos a traves de los endpoints publicos existentes del catalogo (`GET /api/v1/catalogo/filtros-disponibles`, `GET /api/v1/productos`, etc.). Por consiguiente, el caso de uso CU23 **no tendra implementacion de pantallas, BLoC, widgets ni repositorios en el proyecto Ec-mobile**, concentrando el esfuerzo tecnico en Backend (`Ec-backend`) y Frontend Web (`Ec-frontend`).

---

## 3. Alcance y Trazabilidad Documental

1. **Documento Maestro de Requisitos:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md) (Seccion 2.1.3 CU23 Lineas 841-856: "CU23. Gestionar categorias, tallas y colores").
2. **Esquema Relacional DDL:** Tablas `fashionstore.categorias`, `fashionstore.tallas`, `fashionstore.colores`, `fashionstore.productos` y `fashionstore.variantes_producto` definidas en migracion Alembic `0001_base_ddl.py`.
3. **Referencias Arquitectonicas del Backend:**
   - [references/arquitectura.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-backend-sdd/references/arquitectura.md) (Paquete Gestion Operativa: `RouterAtributos`, `ServicioGestionAtributos`, modelos `CategoriaORM`, `TallaORM`, `ColorORM`).
   - [references/dominio.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-backend-sdd/references/dominio.md) (Invariantes de integridad relacional sobre variantes y productos).
4. **Design System Multiplataforma:**
   - [references/fashionstore-tokens.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md) (Tokens de espaciado Base-2, tipografia Outfit, paleta Slate/Camel/Obsidian, muestras visuales Swatches).

---

## 4. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema debera exigir autenticacion JWT valida con rol `administrador` para cualquier operacion de mutacion (creacion, actualizacion y eliminacion) en los endpoints administrativos de categorias (`/api/v1/admin/categorias`), tallas (`/api/v1/admin/tallas`) y colores (`/api/v1/admin/colores`).

- **# AC-2 (Por Evento - Creacion de Categoria Jerarquica):**  
  Cuando el administrador envie una solicitud de registro de categoria indicando el nombre y opcionalmente el identificador de categoria padre (`id_categoria_padre`), el sistema debera:
  1. Normalizar el nombre eliminando espacios redundantes en extremos e interior.
  2. Verificar que el nombre no exista previamente en `fashionstore.categorias` (insensible a mayusculas, minusculas y tildes).
  3. Si se proporciona `id_categoria_padre`, validar que la categoria padre exista en la base de datos.
  4. Persistir el registro y retornar codigo HTTP `201 Created` con el DTO detallado de la categoria.

- **# AC-3 (Conducta No Deseada - Categoria Duplicada):**  
  Si el nombre de la categoria ya se encuentra registrado en el sistema, entonces el sistema debera rechazar la operacion, abortar la transaccion y responder con codigo HTTP `409 Conflict` indicando el codigo de error `CATEGORIA_DUPLICADA`.

- **# AC-4 (Conducta No Deseada - Referencia Circular en Categorias):**  
  Si durante la creacion o actualizacion de una categoria se especifica un `id_categoria_padre` que coincida con la propia categoria (`id_categoria_padre == id_categoria`) o que constituya un descendiente en el arbol jerarquico (generando un bucle infinito de dependencias), entonces el sistema debera rechazar la solicitud con codigo HTTP `422 Unprocessable Entity` o `400 Bad Request` bajo el codigo `REFERENCIA_CIRCULAR_NO_PERMITIDA`.

- **# AC-5 (Por Estado - Proteccion de Integridad en Eliminacion de Categoria):**  
  Mientras una categoria posea subcategorias hijas dependientes (`id_categoria_padre == id_categoria`) o mantenga productos asociados en el catalogo (`fashionstore.productos.id_categoria == id_categoria`), si el administrador intenta eliminar dicha categoria, entonces el sistema debera bloquear la eliminacion fisica y responder con codigo HTTP `409 Conflict` indicando `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS`.

- **# AC-6 (Por Evento - Creacion y Secuenciacion Comercial de Talla):**  
  Cuando el administrador registre una nueva talla indicando codigo (ej. "XS", "S", "M", "L", "XL", "38") y orden secuencial numerico (`orden >= 0`), el sistema debera:
  1. Normalizar el codigo a mayusculas sin espacios perimetrales.
  2. Verificar que el codigo sea unico en `fashionstore.tallas`.
  3. Validar que el valor de orden sea un entero positivo o cero.
  4. Persistir la talla y retornar codigo HTTP `201 Created`.

- **# AC-7 (Conducta No Deseada - Talla Duplicada o Codigo Invalido):**  
  Si el codigo de talla ya existe o si no cumple con la longitud estipulada (1 a 10 caracteres), entonces el sistema debera rechazar la operacion con codigo HTTP `409 Conflict` (`TALLA_DUPLICADA`) o HTTP `422 Unprocessable Entity` segun corresponda.

- **# AC-8 (Por Estado - Proteccion de Integridad en Eliminacion de Talla):**  
  Mientras una talla se encuentre asignada a una o mas variantes fisicas de prendas (`fashionstore.variantes_producto.id_talla == id_talla`), si el administrador solicita eliminar la talla, entonces el sistema debera impedir la eliminacion y responder con codigo HTTP `409 Conflict` bajo el codigo `TALLA_EN_USO_EN_VARIANTES`.

- **# AC-9 (Por Evento - Creacion de Color con Validacion Cromatica #HEX):**  
  Cuando el administrador registre un color especificando nombre textil (ej. "Rojo Carmin", "Negro Ebano", "Marfil") y codigo hexadecimal `#HEX`, el sistema debera:
  1. Validar que el nombre no exista en `fashionstore.colores` (insensible a mayusculas/minusculas).
  2. Validar que el codigo hexadecimal cumpla estrictamente con la expresion regular `^#[0-9A-Fa-f]{6}$` (longitud de 7 caracteres iniciando con `#`).
  3. Persistir el registro y retornar codigo HTTP `201 Created`.

- **# AC-10 (Conducta No Deseada - Color Duplicado o Codigo Hexadecimal Invalido):**  
  Si el nombre del color ya existe en el sistema, o si el codigo `#HEX` carece del formato valido (ej. `#FFF`, `123456`, `#GGGGGG`), entonces el sistema debera rechazar la peticion con codigo HTTP `409 Conflict` (`COLOR_DUPLICADO`) o HTTP `422 Unprocessable Entity` (`FORMATO_HEX_INVALIDO`).

- **# AC-11 (Por Estado - Proteccion de Integridad en Eliminacion de Color):**  
  Mientras un color este vinculado a una o mas variantes de prendas en `fashionstore.variantes_producto`, si el administrador intenta eliminar el registro, entonces el sistema debera bloquear la eliminacion y responder con codigo HTTP `409 Conflict` bajo el codigo `COLOR_EN_USO_EN_VARIANTES`.

- **# AC-12 (Por Evento - Consultas Publicas y Administrativas Enriquecidas):**  
  - Para usuarios publicos: El sistema expondra `GET /api/v1/categorias`, `GET /api/v1/tallas` (ordenadas por `orden ASC`) y `GET /api/v1/colores` para alimentacion abierta del catalogo y filtros.
  - Para administradores: El sistema expondra `GET /api/v1/admin/categorias`, `GET /api/v1/admin/tallas` y `GET /api/v1/admin/colores` enriquecidos con metricas de uso comercial (total de productos asociados por categoria, total de variantes por talla y total de variantes por color).

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- **# AC-13 (Ubicuo - Arquitectura Standalone y Reactividad con Signals):**  
  El modulo de gestion de atributos taxonomicos se construira como componente 100% Standalone (`standalone: true`), con deteccion de cambios `ChangeDetectionStrategy.OnPush`, administracion de estado reactivo mediante **Angular Signals** (`signal()`, `computed()`), consumo de servicios mediante `inject()`, enrutamiento en `/admin/atributos` protegido bajo `authGuard` y maquetacion dentro del contenedor institucional `max-w-[1440px] px-6` con `scrollbar-gutter: stable`.

- **# AC-14 (Ubicuo - Sistema de Tokens y Paleta Atelier):**  
  La interfaz utilizara la escala de espaciado Base-2 (`space-1` a `space-7`), la tipografia institucional **Outfit** (`font-sans font-semibold tracking-tight`), bordes curvos estandarizados y los tonos Slate/Camel/Obsidian del Design System, evitando valores arbitrarios en clases CSS.

- **# AC-15 (Por Evento - Panel Editorial con 3 Pestanas Independientes):**  
  Cuando el administrador acceda a `/admin/atributos`, el sistema presentara un panel de control con 3 pestanas de trabajo fluidas:
  1. **Pestana "Categorias":** Vista en tabla o arbol jerarquico que distingue categorias raiz y subcategorias con sangria visual o badges de nivel, nombre de la categoria padre, conteo de productos vinculados y botones de accion (Editar, Eliminar).
  2. **Pestana "Tallas":** Tabla ordenada cronologicamente por el campo `orden`, mostrando la insignia visual de la talla, su valor de orden comercial, total de variantes que la usan y acciones de gestion.
  3. **Pestana "Colores":** Rejilla editorial tipo swatch que muestra para cada color un circulo o recuadro con la muestra cromatica real derivada de su `#HEX`, el codigo hexadecimal legible, el nombre comercial de la tonalidad, el conteo de variantes asociadas y acciones.

- **# AC-16 (Por Evento - Modales Reactivos y Validacion en Vivo):**  
  Cuando el administrador pulse `+ NUEVA CATEGORIA`, `+ NUEVA TALLA` o `+ NUEVO COLOR` (o sus respectivos botones de edicion), el sistema debera desplegar un modal reactivo construido con `NonNullableFormBuilder`:
  - En Categorias: Campo de nombre y selector opcional de categoria padre (que excluye la propia categoria en modo edicion para evitar referencias circulares).
  - En Tallas: Campo de codigo con auto-mayusculas y campo numerico de orden.
  - En Colores: Campo de nombre textil y selector visual de color (`<input type="color">`) sincronizado bidireccionalmente con el campo de texto del codigo `#HEX`.

- **# AC-17 (Conducta No Deseada - Captura y Visualizacion de Conflictos 409):**  
  Si el backend responde con codigo HTTP `409 Conflict` (ej. intento de borrar una categoria con productos o una talla/color en uso en variantes de inventario), entonces la interfaz debera capturar el error, desplegar un Luxury Banner o Toast explicativo detallando la restriccion y mantener el formulario y la vista intactos sin perdida de datos ni recargas de pagina.

---

## 5. Matriz de Cobertura de Criterios de Aceptacion

| ID Criterio | Nombre del Criterio | Tipo EARS | Plataforma | Codigo HTTP / Regla |
|:---|:---|:---:|:---:|:---:|
| **AC-1** | Seguridad y Control de Acceso RBAC | Ubicuo | Backend | 401 / 403 (Rol admin) |
| **AC-2** | Creacion de Categoria Jerarquica | Por Evento | Backend | 201 Created |
| **AC-3** | Prevencion de Categoria Duplicada | No Deseada | Backend | 409 `CATEGORIA_DUPLICADA` |
| **AC-4** | Prevencion de Referencias Circulares | No Deseada | Backend | 422 `REFERENCIA_CIRCULAR_NO_PERMITIDA` |
| **AC-5** | Integridad Relacional en Baja de Categoria | Por Estado | Backend | 409 `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS` |
| **AC-6** | Creacion y Secuenciacion de Tallas | Por Evento | Backend | 201 Created (`orden ASC`) |
| **AC-7** | Unicidad y Validacion de Codigo de Talla | No Deseada | Backend | 409 `TALLA_DUPLICADA` / 422 |
| **AC-8** | Integridad Relacional en Baja de Talla | Por Estado | Backend | 409 `TALLA_EN_USO_EN_VARIANTES` |
| **AC-9** | Creacion de Color con Formato #HEX | Por Evento | Backend | 201 Created (`^#[0-9A-Fa-f]{6}$`) |
| **AC-10** | Unicidad y Validacion Regex de Color | No Deseada | Backend | 409 `COLOR_DUPLICADO` / 422 |
| **AC-11** | Integridad Relacional en Baja de Color | Por Estado | Backend | 409 `COLOR_EN_USO_EN_VARIANTES` |
| **AC-12** | Consultas Publicas y Administrativas | Por Evento | Backend | 200 OK (Metricas de uso) |
| **AC-13** | Arquitectura Standalone y Signals | Ubicuo | Frontend Web | Angular 19+ / Signals |
| **AC-14** | Tokens de Diseno y Tipografia Outfit | Ubicuo | Frontend Web | Base-2 / Slate/Camel/Obsidian |
| **AC-15** | Panel Editorial con 3 Pestanas | Por Evento | Frontend Web | Tabs: Categorias / Tallas / Colores |
| **AC-16** | Formularios Reactivos con Swatch | Por Evento | Frontend Web | NonNullableFormBuilder / Input Color |
| **AC-17** | Manejo Visual de Conflictos 409 | No Deseada | Frontend Web | Luxury Banner / Preservar Estado |

---

## 6. Proximos Pasos en el Ciclo SDD
Una vez obtenida la aprobacion formal de esta especificacion de requisitos (Fase 1), se continuara con la **Fase 2: Diseno Tecnico**, donde se detallaran los contratos OpenAPI, esquemas Pydantic v2, servicios de dominio con deteccion de grafos aciclicos (DAG) para categorias, arbol de componentes Angular y pruebas unitarias planificadas.
