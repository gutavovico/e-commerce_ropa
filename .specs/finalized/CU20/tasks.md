# Plan de Tareas y Oleadas de Implementacion: CU20 - Gestionar Usuarios y Roles (RBAC)

**ID del Caso de Uso:** CU20  
**Nombre:** Gestionar Usuarios y Roles  
**Paquete Arquitectonico:** `autenticacion_seguridad` / `gestion_operativa`  
**Modulo Backend:** `app/modules/autenticacion_seguridad/cu20_usuarios_roles`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu20_usuarios_roles`  
**Referencias:** `.specs/changes/CU20/spec.md` y `.specs/changes/CU20/design.md`  
**Estado:** En Revision de Planificacion (Fase 3 - Plan de Tareas)  

---

## 1. Estrategia General de Implementacion

El caso de uso CU20 implementa la arquitectura de **Control de Acceso Basado en Roles (RBAC)** en FashionStore, gobernando las identidades, credenciales seguras, niveles de autorizacion y asignacion de sucursales fisicas para los 4 roles del sistema (`administrador`, `encargado_sucursal`, `cajero`, `cliente`).

### 1.1 Exclusion Formal Ratificada de la Aplicacion Movil (Ec-mobile)
Se ratifica de manera formal e irrevocable la exclusion tecnica de desarrollo en `Ec-mobile`. La aplicacion movil en Flutter 3.x esta concebida exclusivamente para el cliente de vitrina B2C y consulta agil de catalogo. Las tareas de provisionamiento de cuentas corporativas, modificacion de privilegios RBAC y auditoria de seguridad son exclusivas de back-office en la aplicacion web (`Ec-frontend`). Por tanto, no se contemplan tareas para la plataforma movil en este plan.

### 1.2 Secuenciacion de Oleadas
El plan de tareas se divide en tres (3) oleadas de ejecucion estrictamente secuenciales:
1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon):**
   Mapeo ORM, esquemas Pydantic v2 con validaciones condicionales de sucursal, excepciones semanticas de dominio, servicio transaccional con proteccion del ultimo administrador y hashing Argon2, endpoints administrativos protegidos por RBAC, y suite de pruebas unitarias/integracion Pytest al 100% en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Contratos DTO en TypeScript, servicio `UsuariosAdminService` con Angular Signals, adaptacion de rejilla y segmentacion dinamica en `AdminDashboardComponent` (ocultando CU20 y CU21 para `encargado_sucursal`), componente `UsuariosAdminComponent` con estetica editorial, barra de filtros reactiva, tabla maestra, modales reactivos con `NonNullableFormBuilder`, Luxury Banners y suite de pruebas unitarias Jasmine/Vitest al 100% en verde.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y DoD:**
   Revalidacion cruzada de ambas suites automatizadas (`pytest`, `ng test`, `ng build`), promocion formal hacia baseline permanente en `.specs/finalized/CU20/` y `.specs/modules/autenticacion_seguridad/CU20-gestionar-usuarios-roles.md`, actualizacion formal de `CHANGELOG.md` (version 1.9.0) y limpieza del directorio temporal.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- [x] **Tarea 1.1: Verificacion de esquema relacional y modelos ORM (UsuarioORM en fashionstore.usuarios con soporte para enumeracion de 4 roles, FK nullable id_sucursal hacia fashionstore.sucursales e indices)**
  - **Archivos:**
    - `Ec-backend/app/modules/autenticacion_seguridad/modelos.py`
    - `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/modelos.py`
    - `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/__init__.py`
  - **Descripcion:**
    * Verificar y consolidar en `UsuarioORM` el mapeo de la tabla `fashionstore.usuarios`:
      - `id_usuario`: BigInteger primary key con autoincremento.
      - `email`: VARCHAR(255) unico, no nulo e indexado.
      - `password_hash`: VARCHAR(255) no nulo.
      - `nombres` y `apellidos`: VARCHAR(100) no nulos.
      - `telefono`: VARCHAR(30) nullable.
      - `rol`: Enumeracion nativa PostgreSQL `rol_usuario` ('administrador', 'encargado_sucursal', 'cajero', 'cliente').
      - `id_sucursal`: Integer nullable con clave foranea indexada hacia `fashionstore.sucursales.id_sucursal`.
      - `activo`: Boolean no nulo con default `True` e indice.
      - `fecha_registro` y `ultimo_acceso`: TIMESTAMPTZ con manejo UTC.
    * Establecer la relacion bidireccional Many-to-One con `SucursalORM` utilizando `joinedload` para consultas optimizadas.
  - **Criterios Mapeados:** `# AC-2`, `# AC-4`, `# AC-5`.
  - **Verificacion:** Inspeccion de metadatos de SQLAlchemy 2.0 y compatibilidad de relaciones con la base de datos PostgreSQL Neon.

- [x] **Tarea 1.2: DTOs Pydantic v2 (UsuarioCrearIn, UsuarioActualizarIn, UsuarioEstadoIn, ResetPasswordIn, UsuarioResumenOut, UsuarioDetalleOut, ListaPaginadaUsuariosOut) con validacion RFC 5322, politicas de password y @model_validator condicional para id_sucursal**
  - **Archivo:** `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/esquemas.py`
  - **Descripcion:**
    * Implementar la enumeracion `RolUsuarioEnum`.
    * Desarrollar funcion de validacion de contrasenas robustas `validar_complejidad_password` (minimo 8 caracteres, al menos una mayuscula, minuscula, numero y caracter especial).
    * `UsuarioCrearIn`: validacion RFC 5322 de `email` con normalizacion a minusculas, limpieza de espacios en `nombres` y `apellidos`, y `@model_validator(mode="after")` que exige `id_sucursal > 0` si `rol` es `encargado_sucursal` o `cajero`, nulificando el campo si el rol es `administrador` o `cliente`.
    * `UsuarioActualizarIn`: actualizacion parcial opcional de nombres, apellidos, telefono, rol y sucursal, aplicando la misma regla condicional para `id_sucursal`.
    * `UsuarioEstadoIn`: payload de mutacion para conmutacion logica del campo booleano `activo`.
    * `ResetPasswordIn`: payload para nuevo password administrativo con validacion de complejidad.
    * `UsuarioResumenOut` y `UsuarioDetalleOut`: DTOs de salida enriquecidos con `nombre_completo`, `sucursal_nombre` y `sucursal_ciudad`, omitiendo estrictamente cualquier rastro de `password_hash`.
    * `ListaPaginadaUsuariosOut`: contenedor estandar de paginacion con `items`, `total`, `pagina`, `limite` y `total_paginas`.
  - **Criterios Mapeados:** `# AC-2`, `# AC-4`, `# AC-5`, `# AC-8`.
  - **Verificacion:** Pruebas unitarias de schemas validando casos limite: emails invalidos, passwords debiles, roles operativos sin sucursal y auto-nulificacion en roles administrativos.

- [x] **Tarea 1.3: Jerarquia de excepciones semanticas de dominio (UsuarioNoEncontradoError, EmailDuplicadoError, SucursalRequeridaError, SucursalInvalidaError, UltimoAdministradorError, AutoModificacionBloqueadaError, UsuarioConDependenciasError)**
  - **Archivo:** `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/errores.py`
  - **Descripcion:**
    * Definir las excepciones tipadas del modulo heredando de la jerarquia base de `core.errors.DomainError`:
      - `UsuarioNoEncontradoError` (HTTP 404, `USUARIO_NO_ENCONTRADO`).
      - `EmailDuplicadoError` (HTTP 409, `EMAIL_DUPLICADO`).
      - `SucursalRequeridaError` (HTTP 422, `SUCURSAL_REQUERIDA`).
      - `SucursalInvalidaError` (HTTP 422, `SUCURSAL_INEXISTENTE_O_INACTIVA`).
      - `UltimoAdministradorError` (HTTP 409, `ULTIMO_ADMINISTRADOR_BLOQUEADO`).
      - `AutoModificacionBloqueadaError` (HTTP 409, `AUTO_DESACTIVACION_NO_PERMITIDA`).
      - `UsuarioConDependenciasError` (HTTP 409, `USUARIO_CON_DEPENDENCIAS`).
  - **Criterios Mapeados:** `# AC-3`, `# AC-4`, `# AC-5`, `# AC-9`, `# AC-11`, `# AC-12`, `# AC-14`.
  - **Verificacion:** Pruebas unitarias de instanciacion comprobando que cada excepcion retorne el codigo semantico y el status code HTTP correspondiente.

- [x] **Tarea 1.4: Servicio de dominio ServicioGestionUsuarios (hashing seguro con Argon2/bcrypt, listado paginado con filtros multicriterio, proteccion transaccional anti-bloqueo del ultimo administrador, bloqueo de auto-desactivacion en sesion y verificacion de integridad pre-eliminacion)**
  - **Archivo:** `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/servicio.py`
  - **Descripcion:**
    * `crear_usuario`: verificar unicidad insensible a mayusculas/minusculas de `email`, comprobar que la sucursal asignada exista y este marcada como `activa = True`, hashear la contrasena con `get_password_hash()` y persistir la entidad.
    * `listar_usuarios_admin`: consulta paginada con `joinedload` de sucursales y ciudades, aplicando filtros opcionales de busqueda por texto `q` (`or_` sobre nombres, apellidos y email), `rol`, `id_sucursal` y `activo`. Calcular `total` y `total_paginas`.
    * `obtener_usuario_por_id`: consulta por ID retornando DTO enriquecido o lanzando `UsuarioNoEncontradoError`.
    * `actualizar_usuario`: validar existencia, verificar colisiones de correo electronico con terceros (`id_usuario != actual`), validar estado de la sucursal, y aplicar salvaguarda anti-bloqueo impidiendo degradar al unico administrador activo o al propio usuario en sesion.
    * `cambiar_estado_usuario`: conmutar estado `activo` impidiendo suspender al unico administrador activo o al usuario actualmente autenticado.
    * `reset_password`: actualizar `password_hash` con nuevo hash criptografico.
    * `eliminar_usuario`: verificar salvaguardas de administrador, comprobar integridad referencial contra historial de pedidos o ventas (lanzando `UsuarioConDependenciasError` si registra transacciones previas), y ejecutar borrado fisico si no posee dependencias.
  - **Criterios Mapeados:** `# AC-2` al `# AC-14`.
  - **Verificacion:** Pruebas unitarias con mocks de base de datos testeando flujos felices, excepciones de conflicto y conteos de administradores.

- [x] **Tarea 1.5: Router REST administrativo /api/v1/admin/usuarios protegido bajo require_roles(["administrador"])**
  - **Archivos:**
    - `Ec-backend/app/modules/autenticacion_seguridad/cu20_usuarios_roles/router.py`
    - `Ec-backend/app/modules/autenticacion_seguridad/router.py`
  - **Descripcion:**
    * Declarar el router con prefijo `/admin/usuarios` y dependencias de rol:
      - `GET /api/v1/admin/usuarios`: Paginado con filtros `q`, `rol`, `id_sucursal`, `activo`.
      - `POST /api/v1/admin/usuarios`: Alta de usuario (HTTP 201 Created).
      - `GET /api/v1/admin/usuarios/{id_usuario}`: Consulta detallada (HTTP 200 OK).
      - `PUT /api/v1/admin/usuarios/{id_usuario}`: Actualizacion de datos y rol (HTTP 200 OK), extrayendo `admin_sesion.id_usuario` para proteccion anti-autobloqueo.
      - `PATCH /api/v1/admin/usuarios/{id_usuario}/estado`: Toggle de activacion/suspension (HTTP 200 OK).
      - `POST /api/v1/admin/usuarios/{id_usuario}/reset-password`: Reseteo de credencial (HTTP 200 OK).
      - `DELETE /api/v1/admin/usuarios/{id_usuario}`: Eliminacion fisica o requerimiento de baja logica (HTTP 204 No Content).
    * Incluir el sub-router en el router agregador de `autenticacion_seguridad`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-6` al `# AC-13`.
  - **Verificacion:** Inspeccion de rutas en FastAPI OpenAPI docs y respuestas de cabecera HTTP.

- [x] **Tarea 1.6: Suite de pruebas automatizadas en tests/modules/autenticacion_seguridad/test_cu20_usuarios_roles.py al 100% en verde**
  - **Archivo:** `Ec-backend/tests/modules/autenticacion_seguridad/test_cu20_usuarios_roles.py`
  - **Descripcion:**
    * Desarrollar pruebas unitarias y de integracion con `TestClient` cubriendo:
      - Seguridad RBAC: rechazo HTTP 401 si no hay token; rechazo HTTP 403 para usuarios con rol `encargado_sucursal`, `cajero` o `cliente` (`# AC-1`).
      - Alta exitosa de administrador, encargado y cajero con hash comprobado (`# AC-2`).
      - Rechazo HTTP 409 ante email duplicado (`# AC-3`).
      - Rechazo HTTP 422 si falta sucursal en roles operativos o si la sucursal no existe/esta inactiva (`# AC-4`, `# AC-5`).
      - Listado paginado con filtros combinados y busqueda textual (`# AC-6`).
      - Consulta individual de ficha tecnica (`# AC-7`).
      - Actualizacion de datos y deteccion de colision de correo (`# AC-8`, `# AC-9`).
      - Conmutacion de estado activo/inactivo (`# AC-10`).
      - Salvaguarda del ultimo administrador activo: rechazo HTTP 409 al intentar suspenderlo o degradarlo (`# AC-11`).
      - Bloqueo de auto-desactivacion del administrador en sesion (`# AC-12`).
      - Reseteo exitoso de contrasena comprobando actualizacion de hash (`# AC-13`).
      - Bloqueo HTTP 409 ante borrado fisico de usuarios con dependencias (`# AC-14`).
  - **Criterios Mapeados:** `# AC-1` al `# AC-14`.
  - **Verificacion:** Ejecucion de `pytest -q` certificando que la suite completa pase al 100% sin advertencias.

---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript en usuario.dto.ts**
  - **Archivo:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/modelos/usuario.dto.ts`
  - **Descripcion:**
    * Definir el tipo literal union `RolUsuario = 'administrador' | 'encargado_sucursal' | 'cajero' | 'cliente'`.
    * Modelar interfaces estrictas sin `any`:
      - `UsuarioAdmin`: DTO completo de usuario devuelto por la API.
      - `UsuarioCrearPayload`: Datos para registro de nuevo usuario.
      - `UsuarioActualizarPayload`: Datos para modificacion editorial.
      - `ResetPasswordPayload`: Payload con `nuevo_password`.
      - `ParametrosFiltroUsuario`: Parametros de busqueda y filtrado.
      - `ListaPaginadaUsuarios`: Respuesta paginada con items y contadores.
  - **Criterio Mapeado:** `# AC-15`.
  - **Verificacion:** Compilacion limpia con `npx tsc --noEmit`.

- [x] **Tarea 2.2: Servicio HTTP reactivo UsuariosAdminService con Angular Signals**
  - **Archivo:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/servicios/usuarios-admin.service.ts`
  - **Descripcion:**
    * Inyectar `HttpClient` y configurar endpoint base `/api/v1/admin/usuarios`.
    * Signals de estado reactivo: `usuarios`, `totalUsuarios`, `usuarioSeleccionado`, `cargando`, `guardando`, `error`, `mensajeExito`.
    * Metodos reactivos con transmision de Bearer token: `cargarUsuarios(filtros)`, `crearUsuario(payload)`, `actualizarUsuario(id, payload)`, `cambiarEstado(id, activo)`, `resetPassword(id, payload)`, `eliminarUsuario(id)` y `limpiarMensajes()`.
  - **Criterios Mapeados:** `# AC-15`, `# AC-18`.
  - **Verificacion:** Pruebas unitarias en `usuarios-admin.service.spec.ts` con `provideHttpClientTesting()`.

- [x] **Tarea 2.3: Actualizacion de AdminDashboardComponent y segmentacion dinamica por rol**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
  - **Descripcion:**
    * Actualizar la rejilla del dashboard a cuatro columnas responsivas (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`).
    * Incorporar la 4ta tarjeta boutique corporativa:
      - Titulo: "Usuarios y Privilegios"
      - Categoria: "Gobernanza y Accesos"
      - Descripcion: "Alta de cuentas corporativas, asignacion de credenciales y gobierno de roles RBAC."
      - Badge: "Seguridad y RBAC"
      - Boton: "GESTIONAR USUARIOS" (`routerLink="/admin/usuarios"`).
    * Segmentacion dinamica por rol:
      - Declarar computed signals `esAdmin` y `esEncargado`.
      - Condicionar en la plantilla: si el usuario es `encargado_sucursal`, ocultar completamente las tarjetas de CU20 (Usuarios) y CU21 (Sucursales), mostrando exclusivamente CU22 (Prendas) y CU23 (Atributos).
  - **Criterios Mapeados:** `# AC-16`, `# AC-23`.
  - **Verificacion:** Pruebas en `admin-dashboard.component.spec.ts` verificando que un usuario encargado de sucursal solo visualice 2 tarjetas y un administrador visualice las 4.

- [x] **Tarea 2.4: Componente Standalone UsuariosAdminComponent y proteccion de rutas con roleGuard**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.ts`
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.html`
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.scss`
    - `Ec-frontend/src/app/core/guards/role.guard.ts`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Crear componente con `ChangeDetectionStrategy.OnPush`, integrando contenedor editorial `max-w-[1440px] px-6 py-8` con paleta institucional Slate/Camel/Obsidian.
    * Incorporar boton superior `"<- Volver al Panel Principal"` con enlace a `/admin`.
    * Implementar guard funcional `roleGuard(rolesPermitidos)` comprobando claims del usuario actual.
    * Registrar la ruta `/admin/usuarios` en `app.routes.ts` protegida con `authGuard` y `roleGuard(['administrador'])`.
    * Actualizar las protecciones de `/admin/sucursales` (solo admin) y permitir acceso a `/admin/productos`, `/admin/atributos` y `/admin` a administradores y encargados de sucursal.
  - **Criterios Mapeados:** `# AC-15`, `# AC-16`, `# AC-23`.
  - **Verificacion:** Pruebas de enrutamiento y guard verificando redireccion contextual ante roles insuficientes.

- [x] **Tarea 2.5: Barra de filtros interactiva y tabla maestra editorial con monogramas y badges de rol**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.html`
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.ts`
  - **Descripcion:**
    * Desarrollar la barra de filtros con Angular Signals:
      - Input de busqueda `q` en vivo con debounce.
      - Dropdown de seleccion de Rol (`Todos los roles`, `Administrador`, `Encargado de Sucursal`, `Cajero`, `Cliente`).
      - Dropdown reactivo de seleccion de Sucursal (cargado via `SucursalesAdminService.sucursales()`).
      - Dropdown de Estado (`Todos`, `Solo Activos`, `Solo Inactivos`).
    * Disenar la tabla editorial de usuarios:
      - Monograma circular con iniciales del nombre en fondo Slate/Camel.
      - Nombre completo, correo electronico y telefono.
      - Badges cromados por rol (Obsidian para Admin, Indigo para Encargado, Ambar para Cajero, Slate para Cliente).
      - Sucursal asignada o etiqueta "— Corporativo".
      - Badge de estado con indicador visual de pulsacion (Verde para Activo, Gris/Rojo para Suspendido).
      - Columna de acciones con botones de "Editar", conmutador de estado "Activar/Suspender" y boton "Clave".
  - **Criterios Mapeados:** `# AC-17`, `# AC-18`, `# AC-21`.
  - **Verificacion:** Renderizado visual sobrio, sin emojis, con estados vacios y de carga.

- [x] **Tarea 2.6: Modales reactivos con NonNullableFormBuilder, Luxury Banners de conflicto 409/422 y pruebas unitarias**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.html`
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.ts`
    - `Ec-frontend/src/app/modules/autenticacion_seguridad/cu20_usuarios_roles/paginas/usuarios-admin.component.spec.ts`
  - **Descripcion:**
    * Construir modal reactivo de alta / edicion:
      - Control dinamico sobre `rol`: cuando se elija `encargado_sucursal` o `cajero`, desplegar el selector obligatorio de sucursales; al elegir `administrador` o `cliente`, ocultarlo y limpiar su valor.
      - Input de contrasena con indicador visual de requisitos de fortaleza.
    * Modal dedicado para restablecimiento de contrasena (`ResetPassword`).
    * Incorporar Luxury Banners ante errores HTTP 409 (correo duplicado, ultimo admin) y HTTP 422, mostrando el mensaje contextual de error sin resetear el formulario ni perder la digitacion del usuario.
    * Desarrollar suite de pruebas unitarias en `usuarios-admin.component.spec.ts` cubriendo apertura de modales, envio de formularios, filtrado reactivo, proteccion de ultimo administrador y segmentacion.
  - **Criterios Mapeados:** `# AC-15` al `# AC-23`.
  - **Verificacion:** Ejecucion de `ng test --watch=false` certificando 100% de tests en verde y `ng build` con 0 errores.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada integral de suites locales**
  - **Descripcion:**
    * Ejecutar suite de pruebas de backend con `pytest` en `Ec-backend` (asegurar 170+ tests en verde).
    * Ejecutar suite de pruebas de frontend con `ng test --watch=false` en `Ec-frontend` (asegurar 130+ tests en verde).
    * Ejecutar compilacion productiva de Angular con `ng build` certificando 0 errores y 0 advertencias de tipo.
    * Ejecutar `audit_emojis.py` garantizando la ausencia total de emojis en todo el repositorio.
  - **Verificacion:** Consolas limpias, 100% verde en ambas plataformas.

- [x] **Tarea 3.2: Promocion formal de artefactos hacia baseline definitivo**
  - **Descripcion:**
    * Copiar y promover los artefactos aprobados desde `.specs/changes/CU20/` hacia `.specs/finalized/CU20/` (`spec.md`, `design.md`, `tasks.md`).
    * Consolidar la especificacion permanente en `.specs/modules/autenticacion_seguridad/CU20-gestionar-usuarios-roles.md`.
    * Limpiar los archivos temporales de `.specs/changes/CU20/`.
  - **Verificacion:** Archivos archivados con enlaces cruzados y estructura sincronizada.

- [x] **Tarea 3.3: Registro formal de version en CHANGELOG.md y actualizacion de trazabilidad**
  - **Descripcion:**
    * Documentar formalmente la version `[1.9.0] - 2026-09-21` en `CHANGELOG.md` y `.specs/CHANGELOG.md`.
    * Resumir la introduccion del modelo RBAC multi-rol, salvaguardas de seguridad del ultimo administrador, segmentacion dinamica del dashboard y eliminacion de dependencias destructivas.
  - **Verificacion:** Trazabilidad completa con SI2-Parcial1.md y estado final limpio.
