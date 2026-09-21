# Plan de Tareas y Oleadas de Implementacion: CU23 - Gestionar Categorias, Tallas y Colores

**ID del Caso de Uso:** CU23  
**Nombre:** Gestionar Categorias, Tallas y Colores  
**Paquete Arquitectonico:** `gestion_operativa`  
**Modulo Backend:** `app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Referencias:** `.specs/changes/CU23/spec.md` y `.specs/changes/CU23/design.md`  
**Estado:** En Revision de Planificacion (Fase 3 - Plan de Tareas)  

---

## 1. Estrategia General de Implementacion

Dado que la aplicacion movil (`Ec-mobile`) esta formalmente excluida de la implementacion activa de CU23 por ser una operacion de parametrizacion editorial exclusiva del panel de administracion web, el plan de trabajo se organiza de forma atomica en 3 oleadas secuenciales:

1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + Pydantic v2):**
   Modelos ORM, esquemas Pydantic v2, excepciones de dominio tipadas, servicio transaccional con deteccion de ciclos aciclicos (DAG) en categorias y validacion de integridad referencial, endpoints publicos y administrativos RBAC, y suite de pruebas unitarias/integracion con Pytest en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Modelos e interfaces TypeScript, servicio `AtributosAdminService` con inyeccion de `HttpClient` y exposicion reactiva, componente Standalone `CategoriasTallasColoresAdminComponent` (Signals, OnPush, contenedor institucional `max-w-[1440px] px-6`), implementacion de 3 pestañas independientes ("Categorias", "Tallas", "Colores"), formularios reactivos con `NonNullableFormBuilder` y selector interactivo de color, gestion de errores 409/422 con Luxury Banners, y suite de pruebas unitarias verificando criterios `# AC-13` al `# AC-17`.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD):**
   Comprobacion de suites completas en verde (`pytest` en Ec-backend, `ng test` y `ng build` en Ec-frontend), promocion formal de especificaciones desde `.specs/changes/CU23/` hacia `.specs/finalized/CU23/`, y registro consolidado del incremento funcional en `CHANGELOG.md`.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + Pydantic v2)

- [x] **Tarea 1.1: Modelos ORM (CategoriaORM con id_categoria_padre, TallaORM con orden, ColorORM con codigo_hex) y migracion/verificacion de tablas**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/modelos.py`
    - `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/__init__.py`
  - **Descripcion:** Implementar o verificar el mapeo ORM sobre las tablas del esquema `fashionstore` en PostgreSQL Neon:
    * `CategoriaORM`: Mapeo de `fashionstore.categorias` con clave foranea auto-referencial `id_categoria_padre` (ondelete="RESTRICT"), relacion bidireccional `categoria_padre` y `subcategorias`, y constraint de unicidad en `nombre`.
    * `TallaORM`: Mapeo de `fashionstore.tallas` con `codigo` unico (hasta 10 caracteres) y campo `orden` (SmallInteger, >= 0) para secuenciacion comercial.
    * `ColorORM`: Mapeo de `fashionstore.colores` con `nombre` unico (hasta 50 caracteres) y columna `codigo_hex` (String de 7 caracteres).
  - **Criterios Mapeados:** `# AC-2`, `# AC-6`, `# AC-9`.
  - **Verificacion:** Verificacion de metadatos de SQLAlchemy 2.0 e inspeccion de tablas existentes sin errores de definicion.

- [x] **Tarea 1.2: Schemas Pydantic v2 de entrada y salida con validaciones regex y normalizacion**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/esquemas.py`
  - **Descripcion:** Construir DTOs fuertemente tipados con Pydantic v2:
    * **Categorias:** `CategoriaBaseIn`, `CategoriaCrearIn`, `CategoriaActualizarIn`, `CategoriaOut`, `CategoriaAdminOut` (enriquecido con `total_productos` y `total_subcategorias`), aplicando validador de limpieza de espacios redundantes y longitud minima de 2 caracteres.
    * **Tallas:** `TallaBaseIn`, `TallaCrearIn`, `TallaActualizarIn`, `TallaOut`, `TallaAdminOut` (con `total_variantes`), normalizando el `codigo` a mayusculas sin espacios perimetrales y validando `orden >= 0`.
    * **Colores:** `ColorBaseIn`, `ColorCrearIn`, `ColorActualizarIn`, `ColorOut`, `ColorAdminOut` (con `total_variantes`), aplicando validacion estricta mediante regex `^#[0-9A-Fa-f]{6}$` sobre `codigo_hex` y normalizacion a mayusculas.
  - **Criterios Mapeados:** `# AC-2`, `# AC-6`, `# AC-7`, `# AC-9`, `# AC-10`.
  - **Verificacion:** Pruebas unitarias de esquemas validando casos limites, cadenas invalidas y formateo correcto.

- [x] **Tarea 1.3: Jerarquia de excepciones de dominio (errores 404, 409 y 422 tipados)**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/errores.py`
  - **Descripcion:** Definir la taxonomia de excepciones de dominio derivadas de las clases base de la aplicacion (`DomainError`, `ConflictError`, `NotFoundError`):
    * Categorias:
      - `CategoriaNoEncontradaError` (HTTP 404, `CATEGORIA_NO_ENCONTRADA`).
      - `CategoriaDuplicadaError` (HTTP 409, `CATEGORIA_DUPLICADA`).
      - `ReferenciaCircularError` (HTTP 422, `REFERENCIA_CIRCULAR_NO_PERMITIDA`).
      - `CategoriaConDependenciasError` (HTTP 409, `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS`).
    * Tallas:
      - `TallaNoEncontradaError` (HTTP 404, `TALLA_NO_ENCONTRADA`).
      - `TallaDuplicadaError` (HTTP 409, `TALLA_DUPLICADA`).
      - `TallaEnUsoError` (HTTP 409, `TALLA_EN_USO_EN_VARIANTES`).
    * Colores:
      - `ColorNoEncontradoError` (HTTP 404, `COLOR_NO_ENCONTRADO`).
      - `ColorDuplicadoError` (HTTP 409, `COLOR_DUPLICADO`).
      - `ColorEnUsoError` (HTTP 409, `COLOR_EN_USO_EN_VARIANTES`).
  - **Criterios Mapeados:** `# AC-3`, `# AC-4`, `# AC-5`, `# AC-7`, `# AC-8`, `# AC-10`, `# AC-11`.
  - **Verificacion:** Pruebas unitarias de inicializacion de excepciones confirmando codigos y mensajes descriptivos.

- [x] **Tarea 1.4: Servicio de aplicacion ServicioGestionAtributos con deteccion de ciclos en arbol de categorias y validaciones de integridad referencial**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/servicio.py`
  - **Descripcion:** Implementar la logica de dominio en `ServicioGestionAtributos`:
    * `_verificar_ciclo_jerarquico(id_categoria, nuevo_id_padre)`: Algoritmo de recorrido ascendente en grafo jerarquico para detectar auto-referencias directas y bucles de orden superior, lanzando `ReferenciaCircularError` (HTTP 422).
    * CRUD de Categorias: `crear_categoria`, `listar_categorias_publicas`, `listar_categorias_admin` (con subqueries para conteo de productos en `fashionstore.productos` y subcategorias dependientes), `actualizar_categoria`, `eliminar_categoria` (verificando que no posea subcategorias ni productos asociados antes de eliminar, emitiendo 409).
    * CRUD de Tallas: `crear_talla`, `listar_tallas_publicas` (ordenadas por `orden ASC`, `codigo ASC`), `listar_tallas_admin` (con conteo de variantes asociadas), `actualizar_talla`, `eliminar_talla` (verificando ausencia de variantes en `fashionstore.variantes_producto`, emitiendo 409).
    * CRUD de Colores: `crear_color`, `listar_colores_publicos`, `listar_colores_admin` (con conteo de variantes asociadas), `actualizar_color`, `eliminar_color` (verificando ausencia de variantes en `fashionstore.variantes_producto`, emitiendo 409).
  - **Criterios Mapeados:** `# AC-2`, `# AC-3`, `# AC-4`, `# AC-5`, `# AC-6`, `# AC-7`, `# AC-8`, `# AC-9`, `# AC-10`, `# AC-11`, `# AC-12`.
  - **Verificacion:** Pruebas de servicio con sesiones de prueba en SQLite/PostgreSQL simulando arboles, colisiones y dependencias.

- [x] **Tarea 1.5: Endpoints publicos (/api/v1/categorias, /api/v1/tallas, /api/v1/colores) y endpoints administrativos (/api/v1/admin/*) con proteccion RBAC**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu23_categorias_tallas_colores/router.py`
    - `Ec-backend/app/modules/gestion_operativa/router.py`
    - `Ec-backend/app/main.py`
  - **Descripcion:** Configurar y registrar las rutas FastAPI:
    * Endpoints publicos de lectura (sin token requerido):
      - `GET /api/v1/categorias`
      - `GET /api/v1/tallas`
      - `GET /api/v1/colores`
    * Endpoints administrativos protegidos con `dependencies=[Depends(require_roles(["administrador"]))]`:
      - Categorias: `GET /api/v1/admin/categorias`, `POST /api/v1/admin/categorias` (201), `PUT /api/v1/admin/categorias/{id}`, `DELETE /api/v1/admin/categorias/{id}` (204).
      - Tallas: `GET /api/v1/admin/tallas`, `POST /api/v1/admin/tallas` (201), `PUT /api/v1/admin/tallas/{id}`, `DELETE /api/v1/admin/tallas/{id}` (204).
      - Colores: `GET /api/v1/admin/colores`, `POST /api/v1/admin/colores` (201), `PUT /api/v1/admin/colores/{id}`, `DELETE /api/v1/admin/colores/{id}` (204).
    * Integrar router en `modules/gestion_operativa/router.py` y validar su inclusion en `app/main.py`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-12`.
  - **Verificacion:** Inspeccion en OpenAPI Swagger (`/docs`) y pruebas de autorizacion RBAC (401/403).

- [x] **Tarea 1.6: Suite de pruebas unitarias y de integracion en tests/modules/catalogo/test_cu23_atributos.py verificando los criterios # AC-1 al # AC-12 con pytest en verde**
  - **Archivo:** `Ec-backend/tests/modules/catalogo/test_cu23_atributos.py`
  - **Descripcion:** Construir suite exhaustiva con al menos 20 casos de prueba:
    * `# AC-1`: Rechazo 401 sin token y 403 con usuario rol cliente en endpoints `/admin/*`.
    * `# AC-2`: Creacion exitosa de categorias raiz y subcategorias (HTTP 201).
    * `# AC-3`: Rechazo 409 (`CATEGORIA_DUPLICADA`) ante nombres duplicados.
    * `# AC-4`: Rechazo 422 (`REFERENCIA_CIRCULAR_NO_PERMITIDA`) por auto-referencia directa e indirecta.
    * `# AC-5`: Rechazo 409 (`CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS`) al intentar borrar categorias con productos o subcategorias; borrado 204 cuando esta libre.
    * `# AC-6` & `# AC-7`: Creacion de tallas (201), orden secuencial, rechazo 409 (`TALLA_DUPLICADA`) y rechazo 422 por longitud o campos invalidos.
    * `# AC-8`: Rechazo 409 (`TALLA_EN_USO_EN_VARIANTES`) al borrar talla asociada a variantes; borrado 204 libre de dependencias.
    * `# AC-9` & `# AC-10`: Creacion de colores (201), validacion regex `#HEX`, rechazo 422 (`FORMATO_HEX_INVALIDO`), rechazo 409 (`COLOR_DUPLICADO`).
    * `# AC-11`: Rechazo 409 (`COLOR_EN_USO_EN_VARIANTES`) al borrar color en uso en variantes; borrado 204 libre.
    * `# AC-12`: Consultas publicas y administrativas enriquecidas con metricas de uso.
  - **Criterios Mapeados:** `# AC-1` al `# AC-12`.
  - **Verificacion:** Ejecucion de `pytest tests/modules/catalogo/test_cu23_atributos.py` con 100% de tests pasando en verde.


---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript para Categorias, Tallas y Colores**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/modelos/atributos.dto.ts`
  - **Descripcion:** Declarar interfaces tipadas para el flujo editorial:
    * `CategoriaAdmin`, `CategoriaCrearPeticion`, `CategoriaActualizarPeticion`.
    * `TallaAdmin`, `TallaCrearPeticion`, `TallaActualizarPeticion`.
    * `ColorAdmin`, `ColorCrearPeticion`, `ColorActualizarPeticion`.
  - **Criterios Mapeados:** `# AC-13`.
  - **Verificacion:** Validacion de tipos con el compilador TypeScript (`npx tsc --noEmit`).

- [x] **Tarea 2.2: Servicio AtributosAdminService con inyeccion de HttpClient y exposicion reactiva**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/servicios/atributos-admin.service.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/servicios/atributos-admin.service.spec.ts`
  - **Descripcion:** Implementar el servicio Angular `AtributosAdminService`:
    * Inyeccion moderna mediante `inject(HttpClient)`.
    * Inclusion de token Bearer desde `localStorage` (`fashionstore_token`).
    * Metodos CRUD completos para Categorias (`obtenerCategorias`, `crearCategoria`, `actualizarCategoria`, `eliminarCategoria`).
    * Metodos CRUD completos para Tallas (`obtenerTallas`, `crearTalla`, `actualizarTalla`, `eliminarTalla`).
    * Metodos CRUD completos para Colores (`obtenerColores`, `crearColor`, `actualizarColor`, `eliminarColor`).
  - **Criterios Mapeados:** `# AC-1`, `# AC-13`.
  - **Verificacion:** Pruebas unitarias de servicio simulando peticiones HTTP con mocks.

- [x] **Tarea 2.3: Componente Standalone CategoriasTallasColoresAdminComponent (Signals, OnPush, contenedor max-w-[1440px] px-6)**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.scss`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Crear el componente Standalone `CategoriasTallasColoresAdminComponent` con `ChangeDetectionStrategy.OnPush`.
    * Gestion de estado reactivo mediante **Angular Signals**: `pestanaActiva = signal<'categorias' | 'tallas' | 'colores'>('categorias')`, `categorias`, `tallas`, `colores`, `terminoBusqueda`, `cargando`, `guardando`, `errorMensaje`, `exitoMensaje`.
    * Registrar la ruta `/admin/atributos` protegida bajo `authGuard` en `app.routes.ts`.
    * Maquetar la interfaz dentro del contenedor maestro `max-w-[1440px] px-6 mx-auto` con `scrollbar-gutter: stable`, aplicando tokens Base-2 y tipografia corporativa Outfit.
  - **Criterios Mapeados:** `# AC-13`, `# AC-14`.
  - **Verificacion:** Compilacion de plantilla y carga de la vista en ruta `/admin/atributos`.

- [x] **Tarea 2.4: Implementacion de las 3 pestanas independientes (arbol jerarquico de categorias, tabla de tallas con orden, rejilla de swatches de colores #HEX)**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.ts`
  - **Descripcion:** Maquetar las tres vistas conmutadas dinamicamente segun la señal `pestanaActiva()`:
    * **Pestaña Categorias:** Tabla/arbol jerarquico que distingue categorias raiz y subcategorias mediante sangria o badges de nivel, visualiza el nombre del padre, total de productos vinculados y botones de accion (Editar, Eliminar).
    * **Pestaña Tallas:** Tabla ordenada ascendentemente por el campo `orden`, mostrando insignias de codigo en mayusculas, total de variantes asociadas y acciones de gestion.
    * **Pestaña Colores:** Rejilla editorial tipo swatch que presenta una muestra cromatica real (`background-color: codigo_hex`), codigo visible `#HEX`, nombre textil de la tonalidad, total de variantes asociadas y acciones.
    * Barra de herramientas superior con buscador reactivo (`computed()`) y boton de accion contextual (`+ NUEVA CATEGORIA`, `+ NUEVA TALLA`, `+ NUEVO COLOR`).
  - **Criterios Mapeados:** `# AC-15`.
  - **Verificacion:** Pruebas visuales de conmutacion de pestañas, filtrado reactivo y renderizado de swatches.

- [x] **Tarea 2.5: Formularios reactivos (NonNullableFormBuilder) con selector interactivo de color y captura de errores 409/422 via Luxury Banners**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.ts`
  - **Descripcion:**
    * Modales interactivos fuertemente tipados con `NonNullableFormBuilder`:
      - Categorias: Selector reactivo de categoria padre que en modo edicion excluye la propia categoria seleccionada para impedir auto-referencias desde el cliente.
      - Tallas: Campo de codigo con auto-mayusculas y campo numerico de orden secuencial (`orden >= 0`).
      - Colores: Selector visual interactivo `<input type="color">` sincronizado bidireccionalmente con el campo de texto `#HEX` y validacion regex.
    * Captura de errores 409 y 422: Despliegue de Luxury Banners explicativos en la cabecera del modal o de la tabla ante respuestas de conflicto (ej. categoria con productos vinculados o tallas/colores en uso en variantes), preservando el formulario y la vista intactos sin perdida de datos ni recargas.
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`.
  - **Verificacion:** Pruebas interactivas de modales, sincronizacion de muestras de color y verificacion de banners ante errores 409.

- [x] **Tarea 2.6: Pruebas unitarias de componentes y servicios con Jasmine/Karma verificando los criterios # AC-13 al # AC-17**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu23_categorias_tallas_colores/paginas/categorias-tallas-colores-admin.component.spec.ts`
  - **Descripcion:** Construir suite exhaustiva de pruebas unitarias ejecutadas mediante el test runner de Angular (`ng test`):
    * `# AC-13`: Inicializacion del componente Standalone y verificacion de senales reactivas.
    * `# AC-14`: Uso de tokens corporativos y contenedor institucional.
    * `# AC-15`: Alternancia fluida de pestañas ("categorias", "tallas", "colores") y filtrado reactivo.
    * `# AC-16`: Apertura de modales, envio de formularios y sincronizacion bidireccional del selector de color `#HEX`.
    * `# AC-17`: Manejo de errores 409 Conflict simulados, verificando la presentacion de Luxury Banners sin perdida de datos.
  - **Criterios Mapeados:** `# AC-13` al `# AC-17`.
  - **Verificacion:** Ejecucion de `ng test --watch=false` verificando que toda la suite frontend se complete al 100% en verde.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y DoD

- [x] **Tarea 3.1: Verificacion de suites completas (pytest en Ec-backend y ng test / ng build en Ec-frontend)**
  - **Descripcion:**
    * Ejecutar suite de pruebas de `Ec-backend` con `pytest` y confirmar que todos los tests pasen en verde sin regresiones.
    * Ejecutar pruebas de `Ec-frontend` con `ng test --watch=false` y confirmar el 100% de tests pasando en verde.
    * Ejecutar compilacion de produccion web mediante `ng build` verificando cero errores y cero advertencias criticas de TypeScript.
  - **Criterios Mapeados:** Aseguramiento integral de calidad tecnica y ausencia de regresiones.
  - **Verificacion:** Salida exitosa (codigo 0) en las ejecuciones locales de pytest, ng test y ng build.

- [x] **Tarea 3.2: Promocion de artefactos desde .specs/changes/CU23/ hacia .specs/finalized/CU23/**
  - **Descripcion:**
    * Mover los artefactos de propuesta desde `.specs/changes/CU23/` hacia la ruta definitiva `.specs/finalized/CU23/`.
    * Consolidar la especificacion permanente del modulo en `.specs/modules/gestion_operativa/CU23-gestionar-atributos.md`.
    * Limpiar el directorio temporal de trabajo `.specs/changes/CU23/`.
  - **Criterios Mapeados:** Conformidad con el ciclo de vida de la metodologia Spec-Driven Development.
  - **Verificacion:** Verificacion de existencia de los archivos en `.specs/finalized/CU23/`.

- [x] **Tarea 3.3: Registro consolidado del incremento funcional en CHANGELOG.md**
  - **Descripcion:**
    * Registrar el incremento de version correspondiente a CU23 en `CHANGELOG.md` y `.specs/CHANGELOG.md`.
    * Documentar endpoints implementados, vistas de administracion web, reglas de prevencion de ciclos en categorias y solucion de proteccion de integridad relacional.
    * Presentar el informe de Definicion de Terminado (DoD) para aprobacion final.
  - **Criterios Mapeados:** Trazabilidad documental corporativa.
  - **Verificacion:** Auditoria de formato sin emojis y consistencia de enlaces relativos.

---

## 3. Matriz de Dependencias entre Tareas

```
[Oleada 1: Backend]
  Tarea 1.1 (Modelos ORM)
       │
       ▼
  Tarea 1.2 (Schemas Pydantic) ──► Tarea 1.3 (Excepciones Dominio)
       │                                     │
       └──────────────┬──────────────────────┘
                      ▼
            Tarea 1.4 (Servicio Dominio)
                      │
                      ▼
            Tarea 1.5 (Routers HTTP)
                      │
                      ▼
            Tarea 1.6 (Pytest Suite Backend)

[Oleada 2: Frontend Web]
  Tarea 2.1 (Modelos TypeScript)
       │
       ▼
  Tarea 2.2 (Servicio HTTP Signals)
       │
       ▼
  Tarea 2.3 (Componente Standalone y Rutas)
       │
       ▼
  Tarea 2.4 (3 Pestañas Editoriales)
       │
       ▼
  Tarea 2.5 (Formularios y Luxury Banners)
       │
       ▼
  Tarea 2.6 (Pruebas Unitarias Web)

[Oleada 3: Cierre y DoD]
  Tarea 3.1 (Verificacion Cruzada) ──► Tarea 3.2 (Promocion SDD) ──► Tarea 3.3 (Changelog y Cierre)
```

---

## 4. Estado de Ejecucion y Checkpoint

Todas las tareas de las Oleadas 1, 2 y 3 han sido completadas satisfactoriamente (`[x]`).  
El caso de uso CU23 se encuentra promovido a permanente en `.specs/modules/gestion_operativa/CU23-gestionar-atributos.md`, archivado en `.specs/finalized/CU23/` y documentado en el registro de versiones.

