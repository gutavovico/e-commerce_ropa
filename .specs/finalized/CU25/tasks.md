# Plan de Tareas y Oleadas de Implementacion: CU25 - Gestionar Proveedores

**ID del Caso de Uso:** CU25  
**Nombre:** Gestionar Proveedores  
**Paquete Arquitectonico:** `gestion_operativa` / `abastecimiento`  
**Modulo Backend:** `app/modules/gestion_operativa/cu25_proveedores`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu25_proveedores`  
**Referencias:** `.specs/changes/CU25/spec.md` y `.specs/changes/CU25/design.md`  
**Estado:** Planificado (Fase 3 - Plan de Tareas)  

---

## 1. Estrategia General de Implementacion

El caso de uso CU25 implementa el subsistema de **Gestion y Administracion de Proveedores y Fabricantes Textiles** en FashionStore. Provee administracion centralizada de socios comerciales mayoristas, validacion estricta de unicidad tributaria (NIT/RUT) y denominacion legal (Razon Social), clasificacion por rubros de alta costura, y preservacion historica de la trazabilidad comercial mediante baja logica.

### 1.1 Exclusion Formal Ratificada de la Aplicacion Movil (Ec-mobile)
Se ratifica de manera formal e irrevocable la exclusion tecnica de desarrollo en `Ec-mobile`. La aplicacion movil en Flutter 3.x esta concebida exclusivamente para el cliente de vitrina B2C y experiencias de probador virtual (AR). Las tareas de registro de proveedores, negociacion mayorista, auditoria de identificacion fiscal y contratos corporativos son exclusivas del panel de administracion web (`Ec-frontend`). Por tanto, no se contemplan tareas para la plataforma movil en este plan.

### 1.2 Secuenciacion de Oleadas
El plan de tareas se estructura en tres (3) oleadas de ejecucion estrictamente secuenciales:
1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon):**
   Modelado ORM de `ProveedorORM`, migracion Alembic `0006_cu25_proveedores_extension.py`, DTOs Pydantic v2, jerarquia de excepciones semanticas, servicio transaccional con prevencion de colisiones de NIT/RUT y razon social, endpoints administrativos protegidos por RBAC (`administrador` y `encargado_sucursal`), y suite de pruebas automatizadas Pytest al 100% en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Contratos DTO en TypeScript, servicio reactivo `ProveedoresAdminService` con Angular Signals, integracion de la tarjeta boutique *"Proveedores y Fabricantes"* en `AdminDashboardComponent` dentro de la categoria *"Gestion de Abastecimiento"*, componente `ProveedoresAdminComponent` con estetica editorial Atelier, tabla maestra con badges cromados de estado, modales reactivos tipados (`NonNullableFormBuilder`), modal confirmatorio de baja logica, Luxury Banners de feedback contextual y suite de pruebas unitarias Vitest al 100% en verde.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y DoD:**
   Revalidacion cruzada de ambas suites automatizadas (`pytest`, `ng test`, `ng build`, `audit_emojis.py`), promocion formal hacia baseline permanente en `.specs/finalized/CU25/` y `.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md`, actualizacion formal de `CHANGELOG.md` y `.specs/CHANGELOG.md` (version 2.1.0) y limpieza del directorio temporal.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- [x] **Tarea 1.1: Mapeo y revision del modelo ProveedorORM en esquema fashionstore y migracion Alembic**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/modelos.py`
    - `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/__init__.py`
    - `Ec-backend/alembic/versions/0006_cu25_proveedores_extension.py`
  - **Descripcion:**
    * Crear el paquete `app/modules/gestion_operativa/cu25_proveedores`.
    * Modelar `ProveedorORM` en `fashionstore.proveedores`:
      - `id_proveedor`: Integer primary key autoincremental.
      - `id_usuario`: BigInteger FK a `fashionstore.usuarios.id_usuario` nullable e indexado.
      - `razon_social`: String(150) no nulo, unico e indexado.
      - `nit_rut`: String(30) no nulo, unico e indexado.
      - `contacto_nombre`: String(120) no nulo.
      - `telefono`: String(30) no nulo.
      - `email`: String(120) no nulo e indexado.
      - `direccion`: String(255) no nulo.
      - `ciudad`: String(80) no nulo e indexado.
      - `rubro`: String(80) no nulo e indexado.
      - `estado_activo`: Boolean no nulo con default True e indexado.
      - `creado_en`: DateTime UTC no nulo con default now.
      - `actualizado_en`: DateTime UTC no nulo con default now y onupdate.
      - Restricciones de unicidad: `UniqueConstraint('nit_rut', name='uq_proveedores_nit_rut')` y `UniqueConstraint('razon_social', name='uq_proveedores_razon_social')`.
      - CheckConstraints de longitud minima: `length(trim(razon_social)) >= 3`, `length(trim(nit_rut)) >= 5`, `length(trim(contacto_nombre)) >= 3`.
    * Generar y aplicar la migracion Alembic `0006_cu25_proveedores_extension.py` de forma idempotente para sincronizar las columnas de la tabla existente en PostgreSQL Neon (`nit` -> `nit_rut`, `activo` -> `estado_activo`, agregar `direccion`, `ciudad`, `rubro`, `actualizado_en`).
  - **Criterios Mapeados:** `# AC-1`, `# AC-4`, `# AC-5`, `# AC-6`, `# AC-8`, `# AC-9`.
  - **Verificacion:** Inspeccion de metadatos de SQLAlchemy 2.0 y ejecucion de `alembic upgrade head` sin errores.

- [x] **Tarea 1.2: DTOs Pydantic v2 y validadores de sanitizacion y formato**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/esquemas.py`
  - **Descripcion:**
    * Declarar los esquemas de entrada (Requests):
      - `ProveedorCrearIn`: campos `razon_social` (min 3, max 150), `nit_rut` (min 5, max 30), `contacto_nombre` (min 3, max 120), `telefono` (min 7, max 30), `email` (`EmailStr`), `direccion` (min 5, max 255), `ciudad` (min 2, max 80), `rubro` (min 3, max 80), con `@field_validator` de sanitizacion obligatoria (strip y no solo espacios).
      - `ProveedorActualizarIn`: campos opcionales con las mismas restricciones de formato y longitud.
      - `ProveedorEstadoIn`: campo booleano `estado_activo` para conmutacion de baja logica o reactivacion.
      - `ProveedorFiltrosIn`: parametros de consulta `q` (max 100), `estado_activo` (bool opcional), `rubro` (str opcional), `pagina` (default 1) y `limite` (default 20, max 100).
    * Declarar los esquemas de salida (Responses):
      - `ProveedorItemOut`: representacion publica completa con `ConfigDict(from_attributes=True)`.
      - `ListaPaginadaProveedoresOut`: contenedor paginado con `items`, `total`, `pagina`, `limite` y `total_paginas`.
  - **Criterios Mapeados:** `# AC-2`, `# AC-3`, `# AC-5`, `# AC-7`.
  - **Verificacion:** Pruebas de serializacion/deserializacion y validaciones sintacticas en Pydantic v2.

- [x] **Tarea 1.3: Jerarquia de excepciones semanticas de dominio**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/errores.py`
  - **Descripcion:**
    * Implementar las excepciones de dominio integradas con `core.errors`:
      - `ProveedorNoEncontradoError`: hereda de `NotFoundError` (HTTP 404), emitiendo mensaje descriptivo con el `id_proveedor`.
      - `ProveedorDuplicadoError`: hereda de `ConflictError` (HTTP 409), detallando si el conflicto ocurrio por `NIT/RUT` o `Razon Social`.
      - `ProveedorInvalidoError`: hereda de `DomainError` (HTTP 422), detallando la regla comercial incumplida.
  - **Criterios Mapeados:** `# AC-4`, `# AC-6`, `# AC-7`.
  - **Verificacion:** Pruebas unitarias de instanciacion confirmando codigos de estado HTTP y formatos de respuesta JSON.

- [x] **Tarea 1.4: Servicio de dominio ServicioGestionProveedores con reglas transaccionales**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/servicio.py`
  - **Descripcion:**
    * Implementar la clase `ServicioGestionProveedores`:
      - `listar_proveedores(db, filtros, usuario_sesion)`: consulta paginada aplicando filtros `estado_activo`, `rubro` e `ILIKE` multicriterio sobre `razon_social`, `nit_rut` y `contacto_nombre`. Ordenamiento descendente por `id_proveedor` y calculo determinista de `total_paginas`.
      - `obtener_proveedor_por_id(db, id_proveedor, usuario_sesion)`: localizacion por PK con verificacion de existencia (404).
      - `crear_proveedor(db, payload, usuario_sesion)`: sanitizacion de textos, validacion previa de no duplicidad de `nit_rut` y `razon_social` (409), persistencia de `ProveedorORM` con `estado_activo = True` y commit transaccional.
      - `actualizar_proveedor(db, id_proveedor, payload, usuario_sesion)`: comprobacion de existencia, validacion de no colision con otros registros si `nit_rut` o `razon_social` cambian (409), actualizacion de campos suministrados y refresco de `actualizado_en`.
      - `cambiar_estado_proveedor(db, id_proveedor, estado_activo, usuario_sesion)`: baja logica (`estado_activo = False`) o reactivacion (`estado_activo = True`), actualizando `actualizado_en` y preservando la fila para mantener integridad historica.
  - **Criterios Mapeados:** `# AC-2`, `# AC-3`, `# AC-4`, `# AC-5`, `# AC-6`, `# AC-8`, `# AC-9`, `# AC-10`.
  - **Verificacion:** Ejecucion de pruebas unitarias sobre metodos del servicio simulando sesiones y persistencia.

- [x] **Tarea 1.5: Router REST bajo /api/v1/admin/proveedores e integracion en gestion operativa**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu25_proveedores/router.py`
    - `Ec-backend/app/modules/gestion_operativa/router.py`
  - **Descripcion:**
    * Definir el `APIRouter` con prefijo `/admin/proveedores` y tag `"Gestion Operativa - Proveedores y Fabricantes (Admin)"`.
    * Configurar la dependencia de seguridad `require_roles(["administrador", "encargado_sucursal"])` en todos los endpoints:
      - `GET /api/v1/admin/proveedores`: consulta paginada con parametros opcionales `q`, `estado_activo`, `estado` ('activos', 'inactivos', 'todos'), `rubro`, `pagina`, `limite`.
      - `GET /api/v1/admin/proveedores/{id_proveedor}`: obtencion de ficha por ID.
      - `POST /api/v1/admin/proveedores`: alta de nuevo proveedor (HTTP 201).
      - `PUT /api/v1/admin/proveedores/{id_proveedor}`: actualizacion de ficha comercial (HTTP 200).
      - `PATCH /api/v1/admin/proveedores/{id_proveedor}/estado`: conmutacion de estado operativo (HTTP 200).
    * Incluir el sub-router de proveedores en el router principal de gestion operativa (`app/modules/gestion_operativa/router.py`).
  - **Criterios Mapeados:** `# AC-1`, `# AC-2`, `# AC-4`, `# AC-5`, `# AC-8`, `# AC-9`, `# AC-10`.
  - **Verificacion:** Inspeccion de OpenAPI en `/docs` verificando prefijos, esquemas de entrada/salida y codigos de error.

- [x] **Tarea 1.6: Suite de pruebas automatizadas Pytest para CU25**
  - **Archivo:** `Ec-backend/tests/modules/gestion_operativa/test_cu25_proveedores.py`
  - **Descripcion:**
    * Implementar 16 pruebas unitarias y de integracion con TestClient:
      - Seguridad RBAC: rechazo 401 sin token (# AC-1).
      - Seguridad RBAC: rechazo 403 para cajero y cliente (# AC-1).
      - Permisos concedidos para administrador y encargado_sucursal (# AC-1).
      - Listado paginado con metadatos (# AC-2).
      - Filtro por busqueda textual `q` (# AC-3).
      - Filtro por `estado_activo` (# AC-3).
      - Filtro por `rubro` (# AC-3).
      - Consulta de ficha por ID existente 200 OK (# AC-4).
      - Consulta de ficha por ID inexistente 404 Not Found (# AC-4).
      - Alta de proveedor exitosa 201 Created (# AC-5).
      - Rechazo de alta por NIT/RUT duplicado 409 Conflict (# AC-6).
      - Rechazo de alta por Razon Social duplicada 409 Conflict (# AC-6).
      - Rechazo de alta por formato de correo o campos invalidos 422 (# AC-7).
      - Actualizacion de proveedor exitosa 200 OK (# AC-8).
      - Rechazo de actualizacion por colision con NIT de otro proveedor 409 (# AC-8).
      - Baja logica (`estado_activo=False`) 200 OK (# AC-9).
      - Reactivacion (`estado_activo=True`) 200 OK (# AC-10).
  - **Criterios Mapeados:** `# AC-1` al `# AC-10`.
  - **Verificacion:** Ejecucion de `pytest tests/modules/gestion_operativa/test_cu25_proveedores.py` obteniendo 100% de tests en verde.

---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript para el dominio de proveedores**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/modelos/proveedor.dto.ts`
  - **Descripcion:**
    * Crear las interfaces tipadas:
      - `ProveedorItemAdmin`: interfaz completa con `id_proveedor`, `id_usuario`, `razon_social`, `nit_rut`, `contacto_nombre`, `telefono`, `email`, `direccion`, `ciudad`, `rubro`, `estado_activo`, `creado_en`, `actualizado_en`.
      - `ProveedorCrearPayload`: contrato para formulario de alta.
      - `ProveedorActualizarPayload`: contrato con propiedades opcionales para edicion.
      - `FiltrosProveedores`: parametros reactivos de filtrado (`q`, `estado_activo`, `estado`, `rubro`, `pagina`, `limite`).
      - `ListaPaginadaProveedores`: respuesta paginada con items y metadatos.
  - **Criterios Mapeados:** `# AC-12`, `# AC-14`.
  - **Verificacion:** Compilacion TypeScript sin errores de tipado.

- [x] **Tarea 2.2: Servicio HTTP reactivo ProveedoresAdminService con Angular Signals**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/servicios/proveedores-admin.service.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/servicios/proveedores-admin.service.spec.ts`
  - **Descripcion:**
    * Implementar `ProveedoresAdminService` con `providedIn: 'root'`:
      - Signals de estado: `proveedores`, `totalRegistros`, `paginaActual`, `totalPaginas`, `cargando`, `guardando`, `error`, `mensajeExito`, `filtros`.
      - Metodo `obtenerHeaders()` que inyecta `Authorization: Bearer <token>` persistido en `localStorage` / `sessionStorage`.
      - Metodo `cargarProveedores(filtros?)`: gestion de `HttpParams` saneados (omitiendo claves vacias o 'todos') y actualizacion de Signals.
      - Metodo `crearProveedor(payload)`: peticion `POST` y actualizacion reactiva de la lista.
      - Metodo `actualizarProveedor(id, payload)`: peticion `PUT` y actualizacion puntual en Signal.
      - Metodo `cambiarEstadoProveedor(id, estado_activo)`: peticion `PATCH` para conmutar estado.
      - Metodo `limpiarMensajes()`: reseteo de `error` y `mensajeExito`.
      - Manejo robusto y defensivo de errores HTTP (401, 403, 404, 409, 422, 500).
    * Desarrollar suite de pruebas unitarias en Vitest para todas las operaciones y manejo de errores.
  - **Criterios Mapeados:** `# AC-12`, `# AC-13`, `# AC-15`, `# AC-16`, `# AC-17`, `# AC-18`.
  - **Verificacion:** Ejecucion de `ng test` sobre el archivo de pruebas del servicio al 100% pasando.

- [x] **Tarea 2.3: Actualizacion de AdminDashboardComponent para integracion en navegacion**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Anadir tarjeta boutique *"Proveedores y Fabricantes"* dentro de la seccion *"Gestion de Abastecimiento"*.
    * Configurar icono editorial SVG de abastecimiento logistico (sin emojis).
    * Configurar ruta interactiva `routerLink="/admin/proveedores"`.
    * Asegurar que la tarjeta sea visible unicamente para los roles autorizados (`administrador` y `encargado_sucursal`).
    * Actualizar pruebas unitarias del dashboard para validar el renderizado de la nueva tarjeta.
  - **Criterios Mapeados:** `# AC-11`.
  - **Verificacion:** Pruebas unitarias de `admin-dashboard.component.spec.ts` en verde e inspeccion de navegacion.

- [x] **Tarea 2.4: Pagina administrativa ProveedoresAdminComponent y configuracion de rutas**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.scss`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Crear el componente Standalone con `ChangeDetectionStrategy.OnPush`.
    * En `app.routes.ts`, registrar la ruta protegida:
      `{ path: 'admin/proveedores', loadComponent: () => import('./modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component').then(m => m.ProveedoresAdminComponent), canActivate: [RoleGuard], data: { roles: ['administrador', 'encargado_sucursal'] } }`.
    * Maquetar el layout editorial de lujo con contenedor `max-w-[1440px]`, fondo claro Slate 50 y tipografia Outfit.
    * Incorporar boton superior de retorno: `<- Volver al Panel Principal` con navegacion hacia `/admin`.
    * Maquetar el encabezado con titulo *"Gestion de Proveedores y Talleres"* y subtitulo descriptivo del padron comercial.
  - **Criterios Mapeados:** `# AC-12`, `# AC-19`.
  - **Verificacion:** Compilacion limpia con `ng build` y validacion de navegacion en navegador.

- [x] **Tarea 2.5: Barra de herramientas con filtros reactivos, debounce y tabla maestra editorial**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.ts`
  - **Descripcion:**
    * Implementar barra de herramientas:
      - Input de busqueda conectado a Signal `busquedaTexto` con retardo *debounce* de 300 ms aplicado sobre parametro `q`.
      - Selector reactivo de estado con opciones: *"Todos los estados"*, *"Solo activos"* y *"Solo inactivos"*.
      - Selector reactivo de rubros predefinidos de alta costura (*"Sastreria de Lujo"*, *"Calzado Artesanal"*, *"Marroquineria y Cuero"*, *"Tejidos Naturales"*, *"Confeccion Denim"*, etc.).
      - Boton de accion principal `+ Nuevo Proveedor` con estilos Obsidian y acento Camel.
    * Implementar tabla maestra:
      - Columnas: Razon Social y Rubro (con badge), NIT/RUT (en monospace), Contacto y Telefono, Email y Ciudad, Insignia de Estado (verde esmeralda *"Activo"* / gris Slate *"Inactivo"*), y columna de Acciones.
      - Acciones: Boton de edicion (lapiz SVG) y boton de alternancia de estado (desactivar/reactivar).
      - Paginacion inferior: indicador de registros, controles pagina anterior/siguiente y selector de limite (10, 20, 50).
      - Skeletons de carga durante peticiones HTTP y Empty State cuando no existan coincidencias.
  - **Criterios Mapeados:** `# AC-13`, `# AC-14`, `# AC-19`.
  - **Verificacion:** Pruebas de filtrado reactivo y verificacion visual de la tabla maestra.

- [x] **Tarea 2.6: Modales reactivos, Luxury Banners de feedback y suite de pruebas Vitest**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu25_proveedores/paginas/proveedores-admin.component.spec.ts`
  - **Descripcion:**
    * Implementar modales reactivos utilizando `NonNullableFormBuilder`:
      - `formCrear`: campos obligatorios con validadores de longitud minima y formato email.
      - `formEditar`: formulario tipado sincronizado con los datos del proveedor seleccionado.
      - Modal de confirmacion para baja logica: alerta contextual previa a desactivar el proveedor.
      - Accesibilidad modal: soporte de tecla `Escape`, bloqueo de backdrop y gestion de foco.
    * Implementar contenedor superior de Luxury Banners:
      - Banner de Exito: confirmacion tras creacion, edicion o cambio de estado.
      - Banner de Conflicto (409): advertencia clara si el NIT/RUT o la Razon Social ya existen.
      - Banner de Validacion (422): notificacion de datos incompletos o formatos erroneos.
      - Banner de Error Inesperado: gestion de fallos de red.
    * Desarrollar suite de pruebas unitarias en `proveedores-admin.component.spec.ts` con Vitest cubriendo los criterios `# AC-11` al `# AC-19`.
  - **Criterios Mapeados:** `# AC-15`, `# AC-16`, `# AC-17`, `# AC-18`, `# AC-19`.
  - **Verificacion:** Ejecucion de `ng test --watch=false` logrando 100% de tests pasando en el frontend.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada de suites automatizadas locales y auditoria lexica**
  - **Descripcion:**
    * Ejecutar suite completa de backend: `pytest` (208 tests previos + 16 nuevos de CU25 = 224 tests pasando).
    * Ejecutar suite completa de frontend: `ng test --watch=false` (169 tests previos + tests nuevos de CU25 pasando).
    * Ejecutar compilacion de produccion: `npm run build` en `Ec-frontend` con 0 errores y 0 advertencias de compilador.
    * Ejecutar auditoria lexica con `audit_emojis.py` garantizando 0 emojis en todo el repositorio.
  - **Verificacion:** Registro en logs de 0 fallos en backend, frontend y compilacion.

- [x] **Tarea 3.2: Promocion de artefactos y consolidacion de documentacion permanente**
  - **Descripcion:**
    * Crear el directorio permanente `.specs/finalized/CU25/`.
    * Promover los artefactos validados:
      - `.specs/changes/CU25/spec.md` -> `.specs/finalized/CU25/spec.md`.
      - `.specs/changes/CU25/design.md` -> `.specs/finalized/CU25/design.md`.
      - `.specs/changes/CU25/tasks.md` -> `.specs/finalized/CU25/tasks.md`.
    * Consolidar la especificacion permanente del modulo en `.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md`.
  - **Verificacion:** Comprobacion de rutas y enlaces markdown cruzados en la documentacion permanente.

- [x] **Tarea 3.3: Registro formal del incremento en CHANGELOGs y limpieza temporal**
  - **Descripcion:**
    * Actualizar `CHANGELOG.md` en la raiz del proyecto documentando la version 2.1.0 con los componentes agregados de CU25.
    * Actualizar `.specs/CHANGELOG.md` registrando la finalizacion del caso de uso.
    * Eliminar de forma segura el directorio de trabajo temporal `.specs/changes/CU25/`.
  - **Verificacion:** Inspeccion de git status y confirmacion de que el entorno queda limpio y listo para el siguiente incremento.
