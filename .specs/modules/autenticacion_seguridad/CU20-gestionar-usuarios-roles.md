# Especificacion Tecnica Permanente: CU20 - Gestionar Usuarios y Roles (RBAC)

**Codigo:** CU20  
**Nombre:** Gestionar Usuarios y Roles (RBAC)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional Backend:** `app/modules/autenticacion_seguridad/cu20_usuarios_roles`  
**Directorio Funcional Frontend:** `src/app/modules/autenticacion_seguridad/cu20_usuarios_roles`  
**Directorio Funcional Mobile:** Excluido formalmente (Back-office administrativo exclusivo web)  
**Actores Primarios:** Administrador (Acceso total de administracion y gobernanza)  
**Actores Secundarios:** Encargado de Sucursal, Cajero, Cliente (Cuentas gestionadas e identidades de acceso)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 1.0.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentacion Funcional: `SI2-Parcial1.md` (Seccion 1.2.2 Objetivo 1, Seccion 1.4 Alcance, Seccion 2.1.1.1 Administrador, Seccion 2.1.1.2 CU20).
- Arquitectura de Referencia: `.agents/skills/fashionstore-backend-sdd/references/arquitectura.md` (Paquete Autenticacion y Seguridad: `UsuarioORM`, `ServicioGestionUsuarios`, `RouterUsuariosAdmin`).
- Modelo de Dominio: `.agents/skills/fashionstore-backend-sdd/references/dominio.md` (Invariantes de usuarios, roles RBAC, relaciones foraneas e integridad referencial).
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush, Angular Signals).

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU20 establece la infraestructura integral de gobernanza, administracion de identidades y Control de Acceso Basado en Roles (RBAC) para FashionStore. Permite al administrador registrar, consultar, editar, conmutar estado operativo, restablecer contrasenas y gobernar los privilegios de los colaboradores y usuarios del sistema, garantizando la asociacion territorial estricta a boutiques fisicas para roles operativos y blindando la plataforma contra bloqueos accidentales.

### 1.2 Reglas de Negocio Estrictas

1. **RB-1: Modelo de Roles RBAC Multi-Rol:**
   - Se reconocen cuatro roles formales en la plataforma: `administrador`, `encargado_sucursal`, `cajero` y `cliente`.
   - El acceso al panel administrativo y a los endpoints `/api/v1/admin/usuarios` esta estrictamente reservado al rol `administrador`.
   - El rol `encargado_sucursal` tiene acceso restringido en el back-office exclusivamente a la gestion de inventario y catalogo (CU22 y CU23), con exclusion absoluta de gobernanza de usuarios (CU20) y sucursales (CU21).

2. **RB-2: Asociacion Territorial Condicional y Obligatoria:**
   - Todo usuario con rol `encargado_sucursal` o `cajero` debe estar obligatoriamente vinculado a una sucursal valida y activa (`id_sucursal` no nulo, existente y con `activa = True`). Si no se provee `id_sucursal` o la sucursal esta inactiva, se rechaza la solicitud con HTTP 422 Unprocessable Entity.
   - Los usuarios con rol `administrador` o `cliente` tienen alcance corporativo global y no deben poseer asignacion de boutique fija (`id_sucursal` forzado a `None`).

3. **RB-3: Salvaguarda Anti-Bloqueo del Ultimo Administrador Activo:**
   - El sistema impide suspender (`activo = False`) o degradar a un rol no administrativo a un usuario si este constituye el unico administrador activo registrado en la base de datos.
   - Cualquier intento de suspender o degradar al ultimo administrador devuelve HTTP 409 Conflict (`ULTIMO_ADMINISTRADOR_ACTIVO`).

4. **RB-4: Proteccion Anti Auto-Bloqueo del Administrador en Sesion:**
   - Un administrador autenticado no puede suspender su propia cuenta ni degradar su propio rol administrativo durante la sesion activa.
   - La contravencion de esta regla genera HTTP 409 Conflict (`AUTO_MODIFICACION_ADMIN_BLOQUEADA`).

5. **RB-5: Unicidad e Insensibilidad de Credenciales:**
   - El correo electronico (`email`) debe ser unico en el sistema, validado de forma insensible a mayusculas/minusculas (`email.strip().lower()`). Intentos de colision devuelven HTTP 409 Conflict (`EMAIL_YA_REGISTRADO`).

6. **RB-6: Politica Criptografica y Complejidad de Contrasenas:**
   - Toda credencial se almacena hasheada mediante algoritmos robustos (Argon2 / bcrypt via `get_password_hash()`).
   - Las contrasenas deben cumplir con una longitud minima de 8 caracteres, alfanumericos y con inclusion de caracteres especiales.

7. **RB-7: Forzado de Baja Logica y Proteccion de Integridad Referencial:**
   - La eliminacion fisica (`DELETE`) de una cuenta de usuario se rechaza con HTTP 409 Conflict (`USUARIO_CON_DEPENDENCIAS_ACTIVAS`) si el usuario registra transacciones dependientes historicas (pedidos, ventas en POS, reservas asignadas o auditoria en bitacora).
   - En dicho escenario, se instruye la baja logica conmutando `activo = False`.

8. **RB-8: Exclusion Formal e Irrevocable de Ec-mobile:**
   - La aplicacion movil (`Ec-mobile` - Flutter) esta destinada exclusivamente a clientes finales (catalogo, carrito, checkout, perfil y vestidor AR). Cero pantallas o modulos administrativos de CU20 son desplegados en la aplicacion movil.

---

## 2. Arquitectura de Endpoints Backend (FastAPI)

Prefijo Base: `/api/v1/admin/usuarios`  
Proteccion General: `require_roles(["administrador"])`

| Metodo | Ruta Relativa | Descripcion | Respuestas |
|---|---|---|---|
| `GET` | `/` | Listado paginado con filtros (`q`, `rol`, `id_sucursal`, `activo`, `pagina`, `limite`) | 200 OK |
| `POST` | `/` | Alta de nuevo colaborador o usuario con validacion RBAC y hashing | 201 Created, 409 Conflict, 422 Unprocessable |
| `GET` | `/{id_usuario}` | Consulta de ficha tecnica detallada del usuario | 200 OK, 404 Not Found |
| `PUT` | `/{id_usuario}` | Actualizacion de datos de perfil, rol y asignacion de sucursal con salvaguardas | 200 OK, 409 Conflict, 422 Unprocessable, 404 Not Found |
| `PATCH` | `/{id_usuario}/estado` | Conmutacion rapida de activacion / suspension con salvaguardas | 200 OK, 409 Conflict, 404 Not Found |
| `POST` | `/{id_usuario}/reset-password` | Restablecimiento administrativo de credencial con re-hashing seguro | 200 OK, 404 Not Found, 422 Unprocessable |
| `DELETE` | `/{id_usuario}` | Verificacion transaccional y eliminacion fisica o requerimiento de baja logica | 204 No Content, 409 Conflict, 404 Not Found |

---

## 3. Arquitectura Frontend (Angular 19+ Standalone)

- **Ruta:** `/admin/usuarios`
- **Guard:** `[authGuard, adminOnlyGuard]`
- **Estrategia:** `ChangeDetectionStrategy.OnPush`
- **Estado Reactivo:** Angular Signals en `UsuariosAdminService`:
  * `usuarios: Signal<UsuarioAdmin[]>`
  * `totalUsuarios: Signal<number>`
  * `usuarioSeleccionado: Signal<UsuarioAdmin | null>`
  * `cargando: Signal<boolean>`
  * `guardando: Signal<boolean>`
  * `error: Signal<string | null>`
  * `mensajeExito: Signal<string | null>`
- **Dashboard Central (`AdminDashboardComponent`):**
  * Rejilla adaptativa: `grid-cols-1 md:grid-cols-2 lg:grid-cols-4`.
  * Tarjeta boutique: "Usuarios y Privilegios" (Gobernanza y Accesos).
  * Segmentacion dinamica por rol: si el usuario posee rol `encargado_sucursal`, se ocultan estrictamente CU20 y CU21, permitiendo unicamente CU22 y CU23.
- **Formularios Reactivos y Validaciones Dinamicas:**
  * `NonNullableFormBuilder` para edicion y alta.
  * Selector condicional de sucursal: se muestra y requiere unicamente ante seleccion de roles `encargado_sucursal` o `cajero`.
  * Luxury Banners: despliegue contextual y no destructivo ante errores HTTP 409 y HTTP 422.

---

## 4. Matriz de Trazabilidad y Criterios de Aceptacion (EARS)

| Criterio | Descripcion Breve | Componente Backend | Componente Frontend | Verificacion Automatizada |
|---|---|---|---|---|
| AC-1 | Restriccion RBAC estricta (Solo Admin) | `require_roles(["administrador"])` | `adminOnlyGuard`, `roleGuard` | Pytest `test_cu20_rbac_acceso` / Jasmine `role.guard.spec` |
| AC-2 | Alta de usuario con hash seguro | `ServicioGestionUsuarios.crear_usuario` | `UsuariosAdminComponent.guardarUsuario` | Pytest `test_crear_usuario_exitoso` / `usuarios-admin.component.spec` |
| AC-3 | Deteccion de colision de email (409) | `EmailYaRegistradoError` | Luxury Banner de conflicto | Pytest `test_crear_usuario_email_duplicado_409` |
| AC-4 | Sucursal obligatoria en roles operativos (422) | Pydantic `@model_validator` | Validacion dinamica en formulario | Pytest `test_crear_usuario_operativo_sin_sucursal_422` |
| AC-5 | Sucursal debe ser activa y valida (422) | `SucursalInvalidaOInactivaError` | Selector reactivo de sucursales activas | Pytest `test_crear_usuario_sucursal_inactiva_422` |
| AC-6 | Listado paginado y filtros multicriterio | `ServicioGestionUsuarios.listar_usuarios_admin` | Barra de filtros interactiva con debounce | Pytest `test_listar_usuarios_paginado` / `usuarios-admin.service.spec` |
| AC-7 | Consulta detallada de ficha tecnica | `ServicioGestionUsuarios.obtener_usuario_por_id` | Modal de visualizacion/edicion | Pytest `test_obtener_usuario_detalle` |
| AC-8 | Actualizacion de datos y roles | `ServicioGestionUsuarios.actualizar_usuario` | Formulario de edicion | Pytest `test_actualizar_usuario_exitoso` |
| AC-9 | Deteccion de colision de correo en edicion | `EmailYaRegistradoError` | Luxury Banner contextual | Pytest `test_actualizar_usuario_email_duplicado_409` |
| AC-10 | Conmutacion de estado activo/inactivo | `ServicioGestionUsuarios.cambiar_estado_usuario` | Toggle interactivo de estado | Pytest `test_cambiar_estado_usuario` |
| AC-11 | Salvaguarda anti-bloqueo del ultimo admin | `UltimoAdministradorActivoError` | Luxury Banner de salvaguarda 409 | Pytest `test_salvaguarda_ultimo_admin_409` |
| AC-12 | Bloqueo de auto-suspension del admin en sesion | `AutoModificacionAdminError` | Luxury Banner de auto-bloqueo 409 | Pytest `test_auto_desactivacion_admin_bloqueada_409` |
| AC-13 | Reseteo administrativo de credenciales | `ServicioGestionUsuarios.reset_password` | Modal reactivo de reseteo de clave | Pytest `test_reset_password_exitoso` |
| AC-14 | Bloqueo transaccional de borrado de usuario | `UsuarioConDependenciasError` | Modal de confirmacion con forzado a baja logica | Pytest `test_eliminar_usuario_con_dependencias_409` |
| AC-15 | Tipado estricto en Angular sin any | N/A | `usuario.dto.ts` | `npx ng build` limpio (0 errores) |
| AC-16 | Segmentacion dinamica en Dashboard Central | N/A | `AdminDashboardComponent` (`esAdmin`, `esEncargado`) | `admin-dashboard.component.spec` |
| AC-17 | Presentacion editorial y monogramas | N/A | `UsuariosAdminComponent` (Avatar de iniciales) | Inspeccion visual y snapshot testing |
| AC-18 | Filtrado reactivo en vivo | N/A | Debounce time en campo de busqueda | `usuarios-admin.component.spec` |
| AC-19 | Modal reactivo de alta y edicion | N/A | `NonNullableFormBuilder` con reactividad de sucursal | `usuarios-admin.component.spec` |
| AC-20 | Modal de reseteo de contrasena | N/A | Modal con validacion de longitud | `usuarios-admin.component.spec` |
| AC-21 | Toggle directo de estado operativo | N/A | Boton conmutador en fila de tabla | `usuarios-admin.component.spec` |
| AC-22 | Preservacion de formularios ante error 409/422 | N/A | Luxury Banners sin reseteo de campos | `usuarios-admin.component.spec` |
| AC-23 | Blindaje de rutas de navegacion | N/A | `roleGuard(['administrador'])` | `role.guard.spec` |
