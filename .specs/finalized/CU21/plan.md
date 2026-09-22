# Plan de Tareas y Oleadas de Implementacion: CU21 - Gestionar Sucursales y Ciudades

**ID del Caso de Uso:** CU21  
**Nombre:** Gestionar Sucursales y Ciudades  
**Paquete:** `gestion_operativa`  
**Modulo Backend:** `app/modules/gestion_operativa/cu21_sucursales_ciudades`  
**Referencias:** `.specs/changes/CU21/spec.md` y `.specs/changes/CU21/design.md`  
**Estado:** Completado y Verificado  

---

## 1. Estrategia General de Implementacion

La construccion del caso de uso CU21 se ejecuta secuencialmente a traves de 4 oleadas de trabajo atimicas:

1. **Oleada 1 (Backend):** Persistencia, esquemas, logica de negocio, endpoints y suite de pruebas en `Ec-backend`.
2. **Oleada 2 (Frontend Web):** Modelos, servicio HTTP, administracion reactiva de estado con Signals, componentes Standalone y pruebas en `Ec-frontend`.
3. **Oleada 3 (Aplicacion Movil):** Estructura Feature-First, BLoC inmutable, modelos DTO/dominio, interfaz tactil y pruebas en `Ec-mobile`.
4. **Oleada 4 (Integracion, Verificacion Cruzada y DoD):** Ejecucion integral de suites de prueba, comprobacion de regresiones y promocion hacia baseline permanente.

---

## 2. Oleada 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

### Tarea 1.1: Modelos de Persistencia ORM y Registro Declarativo
- **Archivos:**
  - `Ec-backend/app/modules/gestion_operativa/modelos.py`
  - `Ec-backend/app/modules/gestion_operativa/__init__.py`
- **Descripcion:** Implementar `CiudadORM` y `SucursalORM` utilizando SQLAlchemy 2.0 bajo el esquema `fashionstore`. Declarar `UniqueConstraint("id_ciudad", "nombre")`, llaves foraneas indexadas y relaciones bidireccionales con eliminacion en cascada controlada. Asegurar su importacion en `alembic/env.py` para autodescubrimiento.
- **Criterios Mapeados:** `# AC-2`, `# AC-4`.
- **Verificacion:** `pytest tests/modules/gestion_operativa/ -k test_modelos` o script de inspeccion de metadatos.

### Tarea 1.2: Excepciones de Dominio y Schemas Pydantic v2
- **Archivos:**
  - `Ec-backend/app/modules/gestion_operativa/cu21_sucursales_ciudades/errores.py`
  - `Ec-backend/app/modules/gestion_operativa/cu21_sucursales_ciudades/esquemas.py`
- **Descripcion:**
  - Definir excepciones derivadas de `DomainError` con codigo y status especifico: `CiudadDuplicadaError` (409), `CiudadNoEncontradaError` (404), `CiudadConDependenciasError` (409), `SucursalDuplicadaError` (409), `SucursalNoEncontradaError` (404), `SucursalConOperacionesPendientesError` (409) y `HorarioSucursalInvalidoError` (422).
  - Implementar schemas de entrada y salida con validacion estricta: `CiudadCrearIn`, `CiudadActualizarIn`, `CiudadOut`, `SucursalCrearIn` (con `@field_validator` que garantice `horario_cierre > horario_apertura`), `SucursalActualizarIn`, `SucursalEstadoIn`, `SucursalPublicaOut` y `SucursalAdminOut`.
- **Criterios Mapeados:** `# AC-3`, `# AC-5`.
- **Verificacion:** `pytest tests/modules/gestion_operativa/test_esquemas.py`.

### Tarea 1.3: Servicio de Negocio de Gestion Territorial
- **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu21_sucursales_ciudades/servicio.py`
- **Descripcion:**
  - Implementar `ServicioGestionSucursal(db: Session)` encapsulando todas las reglas de negocio e invariantes.
  - Metodos de ciudades: `crear_ciudad`, `listar_ciudades`, `actualizar_ciudad`, `eliminar_ciudad` (validando ausencia de sucursales asociadas y clientes con esa ciudad preferida antes de borrar; en caso contrario lanzar `CiudadConDependenciasError`).
  - Metodos de sucursales: `crear_sucursal`, `listar_sucursales_admin`, `listar_sucursales_publicas`, `obtener_sucursal`, `actualizar_sucursal`, `cambiar_estado_sucursal`, `eliminar_sucursal`.
  - Invariante de baja/desactivacion (`# AC-7`): Validar si existen reservas activas en `fashionstore.reservas` (`pendiente`, `confirmada`, `en_atencion`) o stock con `cantidad_disponible > 0` en `fashionstore.inventario_sucursal`. De existir, abortar con `SucursalConOperacionesPendientesError`.
- **Criterios Mapeados:** `# AC-2`, `# AC-3`, `# AC-4`, `# AC-6`, `# AC-7`.
- **Verificacion:** `pytest tests/modules/gestion_operativa/test_servicio.py`.

### Tarea 1.4: Routers y Controladores HTTP
- **Archivos:**
  - `Ec-backend/app/modules/gestion_operativa/cu21_sucursales_ciudades/router.py`
  - `Ec-backend/app/modules/gestion_operativa/router.py`
  - `Ec-backend/app/main.py`
- **Descripcion:**
  - Crear endpoints publicos: `GET /api/v1/sucursales` (filtro opcional por `id_ciudad`, solo sucursales activas).
  - Crear endpoints administrativos protegidos con `require_roles("administrador")`:
    - `GET /api/v1/admin/ciudades`, `POST /api/v1/admin/ciudades`, `PUT /api/v1/admin/ciudades/{id}`, `DELETE /api/v1/admin/ciudades/{id}`.
    - `GET /api/v1/admin/sucursales`, `GET /api/v1/admin/sucursales/{id}`, `POST /api/v1/admin/sucursales`, `PUT /api/v1/admin/sucursales/{id}`, `PATCH /api/v1/admin/sucursales/{id}/estado`, `DELETE /api/v1/admin/sucursales/{id}`.
  - Registrar el router modular en la aplicacion principal FastAPI bajo `/api/v1`.
- **Criterios Mapeados:** `# AC-1`, `# AC-8`, `# AC-9`.
- **Verificacion:** `pytest tests/modules/gestion_operativa/test_router.py`.

### Tarea 1.5: Suite de Pruebas Automatizadas Backend
- **Archivo:** `Ec-backend/tests/modules/gestion_operativa/test_cu21_sucursales_ciudades.py`
- **Descripcion:** Implementar suite completa con cobertura para:
  - Autenticacion y RBAC (rechazo 401 si no hay token, rechazo 403 si el rol es cliente o cajero).
  - Creacion exitosa de ciudad y sucursal (201 Created).
  - Rechazo por duplicidad de ciudad o sucursal en misma sede (409 Conflict).
  - Rechazo por horario invalido (422 Unprocessable Entity).
  - Bloqueo de eliminacion de ciudad con dependencias (409 Conflict).
  - Bloqueo de desactivacion de sucursal con reservas pendientes o stock disponible (409 Conflict).
  - Consulta publica filtrada y consulta administrativa con estadisticas.
- **Criterios Mapeados:** `# AC-1` a `# AC-9`.
- **Verificacion:** `pytest tests/modules/gestion_operativa/test_cu21_sucursales_ciudades.py -v`.

---

## 3. Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+)

### Tarea 2.1: Modelos e Interfaces TypeScript
- **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu21_sucursales_ciudades/modelos/sucursal.model.ts`
- **Descripcion:** Definir interfaces estrictas para `Ciudad`, `CiudadCrearPayload`, `CiudadActualizarPayload`, `SucursalPublica`, `SucursalAdmin`, `SucursalCrearPayload`, `SucursalActualizarPayload`, `SucursalEstadoPayload` y `FiltrosSucursalAdmin`.
- **Criterios Mapeados:** `# AC-10`.
- **Verificacion:** Compilacion limpia con `npm run build -- --no-watch`.

### Tarea 2.2: Servicio HTTP de Administracion
- **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu21_sucursales_ciudades/servicios/sucursales-admin.service.ts`
- **Descripcion:** Implementar `SucursalesAdminService` consumiendo `/api/v1/admin/ciudades` y `/api/v1/admin/sucursales` con metodos fuertemente tipados e inyeccion via `inject(HttpClient)`.
- **Criterios Mapeados:** `# AC-10`.
- **Verificacion:** Pruebas unitarias en `sucursales-admin.service.spec.ts`.

### Tarea 2.3: Componente de Gestion Editorial con Signals
- **Archivos:**
  - `Ec-frontend/src/app/modules/gestion_operativa/cu21_sucursales_ciudades/paginas/sucursales-admin.component.ts`
  - `Ec-frontend/src/app/modules/gestion_operativa/cu21_sucursales_ciudades/paginas/sucursales-admin.component.html`
  - `Ec-frontend/src/app/modules/gestion_operativa/cu21_sucursales_ciudades/paginas/sucursales-admin.component.scss`
- **Descripcion:**
  - Componente Standalone con `ChangeDetectionStrategy.OnPush`.
  - Estado reactivo con Signals (`ciudades`, `sucursales`, `filtroCiudad`, `filtroBusqueda`, `sucursalesFiltradas`).
  - Maquetacion en contenedor `max-w-[1440px] px-6` con tokens Base-2 y tipografia Outfit.
  - Pestañas operativas "Boutiques & Sucursales" y "Ciudades Operativas".
  - Tarjetas de boutique con direccion, horarios, total de empleados, stock y badge de estado.
  - Modales reactivos con `NonNullableFormBuilder` para alta/edicion de sucursales y ciudades con validacion en vivo de horarios.
  - Notificaciones Luxury Toast ante confirmacion o error de integridad 409.
- **Criterios Mapeados:** `# AC-10`, `# AC-11`, `# AC-12`, `# AC-13`, `# AC-14`.
- **Verificacion:** `npm test -- --include src/app/modules/gestion_operativa/**/*.spec.ts`.

### Tarea 2.4: Enrutamiento y Proteccion con Guards
- **Archivo:** `Ec-frontend/src/app/app.routes.ts`
- **Descripcion:** Registrar la ruta `/admin/sucursales` protegida con `authGuard` y resolucion lazy-loading del componente.
- **Criterios Mapeados:** `# AC-10`.
- **Verificacion:** Comprobacion de navegacion y compilacion Angular.

---

## 4. Oleada 3: Aplicacion Movil (`Ec-mobile` - Flutter 3.x + Dart)

### Tarea 3.1: Entidades del Dominio y Modelos DTO
- **Archivos:**
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/sucursal_dto.dart`
- **Descripcion:** Declarar entidades inmutables `Ciudad` y `Sucursal` con constructores `const`. Implementar `SucursalDto` con metodos `fromJson` y mapeo de creacion/actualizacion JSON.
- **Criterios Mapeados:** `# AC-15`.
- **Verificacion:** `flutter analyze`.

### Tarea 3.2: Contrato y Repositorio de Infraestructura
- **Archivos:**
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/repositorios/sucursales_repositorio.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/repositorios/sucursales_repositorio_impl.dart`
- **Descripcion:** Implementar `SucursalesRepositorioImpl` consumiendo endpoints administrativos con token JWT proveniente de `flutter_secure_storage`.
- **Criterios Mapeados:** `# AC-15`, `# AC-16`.
- **Verificacion:** Pruebas unitarias del repositorio con cliente mock.

### Tarea 3.3: BLoC con Clases Selladas (`SucursalesBloc`)
- **Archivos:**
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_event.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_state.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_bloc.dart`
- **Descripcion:**
  - Implementar clases selladas `sealed class SucursalesEvent` y `sealed class SucursalesState`.
  - Gestion de estados: `SucursalesInicial`, `SucursalesCargando`, `SucursalesCargadas`, `SucursalesOperacionExitosa` y `SucursalesError`.
  - Manejo de excepciones traduciendo errores HTTP 409 y de conexion a mensajes amigables.
- **Criterios Mapeados:** `# AC-15`, `# AC-16`.
- **Verificacion:** `flutter test test/features/gestion_operativa/sucursales_bloc_test.dart`.

### Tarea 3.4: Interfaz de Usuario Tactil con Tokens de Diseno
- **Archivos:**
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/pantallas/pantalla_sucursales_admin.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/tarjeta_sucursal_admin.dart`
  - `Ec-mobile/lib/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/modal_sucursal_form.dart`
- **Descripcion:**
  - Construir interfaz movil basada en `AppTheme` (`AppColors`, `AppSpacing`, `AppTypography`).
  - Cabecera editorial con avatar y accion de refresco.
  - Barra deslizable de chips de ciudades.
  - Tarjetas de boutique con monograma, badge de estado, horarios e interruptor reactivo con dialogo de confirmacion.
  - BottomSheet modal para registro y edicion rapida de sucursales.
  - Implementacion de los 4 estados de pantalla: inicial, carga con shimmer, lista con datos y Luxury SnackBar ante errores.
- **Criterios Mapeados:** `# AC-16`, `# AC-17`, `# AC-18`.
- **Verificacion:** `flutter test test/features/gestion_operativa/pantalla_sucursales_test.dart`.

---

## 5. Oleada 4: Verificacion Cruzada, Pruebas y Cierre de Ciclo (DoD)

### Tarea 4.1: Ejecucion de Baterias de Pruebas en los 3 Stacks
- **Comandos de Validacion:**
  1. `cd Ec-backend && pytest` (100% pruebas en verde, verificando trazabilidad de `# AC-1` a `# AC-9`).
  2. `cd Ec-frontend && npm test -- --watch=false` (verificando componentes OnPush, Signals y servicios sin regresiones).
  3. `cd Ec-mobile && flutter test` (verificando BLoC, estados y widgets).
  4. `cd Ec-mobile && flutter analyze` (cero incidencias estaticas).

### Tarea 4.2: Procedimiento de Promocion y Archivo
- **Acciones:**
  1. Promover archivos de `.specs/changes/CU21/` hacia `.specs/finalized/CU21/`.
  2. Crear o actualizar la especificacion permanente en `.specs/modules/gestion_operativa/CU21-gestionar-sucursales.md`.
  3. Registrar la entrada formal en `CHANGELOG.md` detallando version, nuevas capacidades y correcciones.
  4. Limpiar el directorio activo `.specs/changes/CU21/`.
