# Especificacion Formal de Requisitos: CU20 - Gestionar Usuarios y Roles (RBAC)

**ID del Caso de Uso:** CU20  
**Nombre:** Gestionar Usuarios y Roles  
**Paquete Arquitectonico:** `autenticacion_seguridad` / `gestion_operativa`  
**Modulo Backend:** `app/modules/autenticacion_seguridad/cu20_usuarios_roles`  
**Modulo Frontend Web:** `src/app/modules/autenticacion_seguridad/cu20_usuarios_roles`  
**Actor Principal:** Administrador (Superusuario)  
**Actores Secundarios (Sujetos de Gobierno):** Encargado de Sucursal, Cajero, Cliente  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 1 (Riesgo Critico: Nucleo de Seguridad, Identidad y Control de Acceso Basado en Roles)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

En la cadena omnicanal de moda y alta costura **FashionStore**, el gobierno corporativo de identidades, credenciales y niveles de autorizacion constituye la columna vertebral de la seguridad y operatividad del negocio. Con la expansion de la cadena en multiples sedes fisicas y vitrina digital, coexisten perfiles con responsabilidades, alcances y limitaciones operativas estrictamente diferenciadas.

El caso de uso **CU20 - Gestionar Usuarios y Roles** establece formalmente el modelo de **Control de Acceso Basado en Roles (RBAC - Role-Based Access Control)** multi-rol de FashionStore, permitiendo al Administrador Corporativo:
1. Centralizar el ciclo de vida completo de las cuentas de usuario: alta, consulta, edicion de datos personales, asignacion/cambio de rol, conmutacion de estado de activacion y baja logica.
2. Garantizar la segregacion rigurosa de funciones entre la direccion corporativa (Superusuario), los lideres de trastienda de cada boutique (Encargados de Sucursal), el personal de caja en punto de venta (Cajeros) y los compradores de vitrina web (Clientes).
3. Vincular de manera obligatoria y relacional a los operadores fisicos (Encargados y Cajeros) con una sucursal determinada (`id_sucursal`), asegurando que las operaciones de inventario, recepcion de mercancia y facturacion queden ancladas a su sede correspondiente.
4. Preservar la continuidad operativa y la resiliencia del sistema mediante salvaguardas que impiden la auto-desactivacion o auto-eliminacion del ultimo administrador activo de la plataforma.
5. Proveer una experiencia de administracion web fluida, sobria y de estetica premium (Editorial Luxury), permitiendo la parametrizacion dinamica de accesos sin fricciones tecnicas.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada con Flutter 3.x y Dart, esta concebida de forma exclusiva para:
- La experiencia de compra, seleccion de estilo, pasarela de pagos y vestidor de Realidad Aumentada (AR) para clientes finales.
- Herramientas agiles de consulta de catalogo y asistencia rapida en piso de venta.

El aprovisionamiento de cuentas de personal, la asignacion de contrasenas temporales o iniciales, la administracion de privilegios de seguridad y la auditoria de perfiles institucionales son responsabilidades sensibles de back-office y gobernanza empresarial. Estas funciones requieren un entorno seguro de escritorio, autenticacion institucional rigurosa y vistas tabulares de alta densidad de datos.

### 2.2 Delimitacion de Alcance
Por consiguiente, el caso de uso CU20 **queda formalmente excluido de desarrollo e implementacion en Ec-mobile**:
- No se crearan pantallas, vistas, dialogos, formularios, BLoCs, servicios ni rutas de gestion de usuarios o roles dentro de `Ec-mobile`.
- La aplicacion movil participa en el modulo de autenticacion unicamente a traves del inicio de sesion de clientes (`CU02`) y la visualizacion/edicion de su propio perfil de cliente (`CU04`).
- Todo el esfuerzo de especificacion, diseno, implementacion y pruebas de CU20 se focaliza exclusivamente en `Ec-backend` (API REST FastAPI) y `Ec-frontend` (Panel de Administracion Web en Angular 19+).

---

## 3. Matriz de Roles y Niveles de Acceso (RBAC)

El sistema soporta y gobierna cuatro (4) roles canonicos definidos en la enumeracion `fashionstore.rol_usuario`:

| Rol | Denominacion Comercial | Ambito Operativo | Sucursal Fisica (`id_sucursal`) | Casos de Uso Autorizados | Restricciones y Prohibiciones |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`administrador`** | Administrador Corporativo (Superusuario) | Toda la cadena (Nivel Central) | No aplica (`NULL` / No requerida) | Acceso irrestricto a todos los modulos actuales (CU20, CU21, CU22, CU23) y futuros del sistema. | Ninguna restriccion de modulo; sujeto unicamente a la regla anti-bloqueo del ultimo admin activo. |
| **`encargado_sucursal`** | Encargado de Sucursal (admin/ES) | Trastienda y gestion operativa de sucursal asignada | **Obligatoria** (FK hacia `fashionstore.sucursales`) | CU22 (Prendas y Variantes), CU23 (Categorias y Atributos). Proyectados: CU25 (Proveedores), CU28 (Ventas y Reservas de sede), CU29 (Indicadores). | **Bloqueo estricto** a CU20 (Gestion de usuarios) y CU21 (Gestion de sucursales). No puede alterar la estructura societaria ni crear otros usuarios. |
| **`cajero`** | Cajero / Terminal POS | Punto de venta presencial en boutique | **Obligatoria** (FK hacia `fashionstore.sucursales`) | Proyectados: CU31 (Registrar venta presencial), CU32 (Procesar cobro y comprobante). | **Bloqueo estricto** a todo el panel administrativo corporativo (`/admin/*`) y catalogos maestros. Acceso exclusivo a interfaz POS. |
| **`cliente`** | Cliente Final (B2C) | Tienda digital / Comercio electronico | No aplica (`NULL`) | Catalogo publico (CU06), Perfil propio (CU04), Carrito de compras, Checkout de pagos, Probador AR. | **Bloqueo estricto** a todas las rutas administrativas `/admin/*`. No posee permisos operativos ni de trastienda. |

---

## 4. Alcance y Trazabilidad Documental

1. **Documento Maestro de Requisitos:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md)
   - Modulo de Seguridad y Usuarios: "Gestionar usuarios y roles: permitir al administrador central registrar empleados, asignar perfiles de acceso (encargados, cajeros, administradores) y asociar operadores a sucursales fisicas".
   - Control de Acceso RBAC, hashing seguro de contrasenas y tokens JWT.
2. **Esquema Relacional DDL (PostgreSQL Neon / Alembic):**
   - Tabla `fashionstore.usuarios`:
     * `id_usuario`: `BIGINT`, Primary Key, autoincremental.
     * `email`: `VARCHAR(255)`, Unique, Not Null, con indice de busqueda.
     * `password_hash`: `VARCHAR(255)`, Not Null (Argon2 / bcrypt).
     * `nombres`: `VARCHAR(100)`, Not Null.
     * `apellidos`: `VARCHAR(100)`, Not Null.
     * `telefono`: `VARCHAR(30)`, Nullable.
     * `rol`: `fashionstore.rol_usuario` (`administrador`, `encargado_sucursal`, `cajero`, `cliente`), Not Null, Default `'cliente'`, con indice.
     * `id_sucursal`: `INTEGER`, Foreign Key hacia `fashionstore.sucursales(id_sucursal)`, Nullable (obligatoria segun logica de negocio para `encargado_sucursal` y `cajero`).
     * `activo`: `BOOLEAN`, Not Null, Default `TRUE`.
     * `fecha_registro`: `TIMESTAMPTZ`, Not Null, Default `NOW()`.
     * `ultimo_acceso`: `TIMESTAMPTZ`, Nullable.
   - Tabla referencial vinculada:
     * `fashionstore.sucursales`: `id_sucursal`, `nombre`, `id_ciudad`, `activa`.
3. **Referencias de Dominio y Arquitectura:**
   - `.agents/skills/fashionstore-backend-sdd/references/dominio.md`: Politicas de seguridad, hashing Argon2, ciclo de vida de tokens Bearer.
   - `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md`: Tokens de disenador, paleta Obsidian/Slate/Camel, tipografia Outfit.

---

## 5. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC para CU20):**  
  El sistema debera exigir autenticacion JWT valida con rol estricto `administrador` (`require_roles(["administrador"])`) para acceder a todos los endpoints administrativos del modulo de gestion de usuarios (`/api/v1/admin/usuarios`). Cualquier peticion de usuarios no autenticados sera rechazada con HTTP `401 Unauthorized`, y de usuarios con roles distintos (`encargado_sucursal`, `cajero`, `cliente`) sera rechazada con HTTP `403 Forbidden`.

- **# AC-2 (Por Evento - Alta de Usuario Administrativo u Operativo):**  
  Cuando el administrador envie una solicitud para registrar un nuevo usuario especificando `email`, `password`, `nombres`, `apellidos`, `rol`, y opcionalmente `telefono` e `id_sucursal`, el sistema debera:
  1. Normalizar el `email` a minusculas y sin espacios marginales.
  2. Validar que el formato de `email` cumpla con el estandar RFC 5322.
  3. Validar que la contrasena cumpla con la politica de complejidad corporativa (longitud minima de 8 caracteres, al menos una mayuscula, una minuscula, un digito numerico y un caracter especial).
  4. Generar el hash criptografico seguro mediante Argon2 / bcrypt antes de la persistencia.
  5. Validar la regla de sucursal segun el rol asignado (obligatoria para `encargado_sucursal` y `cajero`).
  6. Crear el registro en `fashionstore.usuarios` con `activo = True` y `fecha_registro = UTC_NOW`.
  7. Retornar codigo HTTP `201 Created` con la entidad de usuario generada (omitiendo de forma estricta el `password_hash`).

- **# AC-3 (Conducta No Deseada - Correo Duplicado o Formato Invalido):**  
  Si el correo electronico ya se encuentra registrado en `fashionstore.usuarios` (comparacion insensible a mayusculas/minusculas), o si el formato del correo no es valido, entonces el sistema debera abortar la operacion y responder con codigo HTTP `409 Conflict` (`EMAIL_DUPLICADO`) o HTTP `422 Unprocessable Entity`.

- **# AC-4 (Conducta No Deseada - Sucursal Obligatoria para Encargados y Cajeros):**  
  Si se intenta registrar o actualizar un usuario con rol `encargado_sucursal` o `cajero` sin especificar un `id_sucursal` valido (`id_sucursal IS NULL` o `<= 0`), entonces el sistema debera rechazar la operacion con codigo HTTP `422 Unprocessable Entity` indicando que los roles operativos de sede requieren obligatoriamente la vinculacion a una sucursal fisica (`SUCURSAL_REQUERIDA`).

- **# AC-5 (Conducta No Deseada - Sucursal Inexistente o Inactiva):**  
  Si el `id_sucursal` especificado no existe en `fashionstore.sucursales` o pertenece a una sucursal marcada como inactiva, entonces el sistema debera rechazar la operacion con codigo HTTP `422 Unprocessable Entity` (`SUCURSAL_INEXISTENTE_O_INACTIVA`).

- **# AC-6 (Por Evento - Listado Paginado con Filtros Administrativos Multi-criterio):**  
  Cuando el administrador solicite consultar el catalogo de usuarios (`GET /api/v1/admin/usuarios`), admitiendo parametros opcionales de busqueda `q` (coincidencia parcial en nombres, apellidos o email), `rol` (`administrador`, `encargado_sucursal`, `cajero`, `cliente`), `id_sucursal`, `activo` (booleano), `pagina` (default 1) y `limite` (default 50, maximo 100), el sistema debera retornar codigo HTTP `200 OK` con la coleccion enriquecida con el nombre de la sucursal asignada (si aplica), metadatos de paginacion y fecha de ultimo acceso.

- **# AC-7 (Por Evento - Consulta de Ficha Detallada de Usuario):**  
  Cuando el administrador consulte el detalle de un usuario por su identificador (`GET /api/v1/admin/usuarios/{id_usuario}`), el sistema debera validar su existencia y retornar codigo HTTP `200 OK` con sus datos completos (id, email, nombres, apellidos, telefono, rol, id_sucursal, nombre de sucursal, activo, fecha_registro, ultimo_acceso). Si el usuario no existe, retornara HTTP `404 Not Found`.

- **# AC-8 (Por Evento - Actualizacion de Datos Personales, Rol y Sucursal):**  
  Cuando el administrador modifique los datos de un usuario existente (`PUT /api/v1/admin/usuarios/{id_usuario}`), especificando campos actualizables (`nombres`, `apellidos`, `telefono`, `rol`, `id_sucursal`), el sistema debera aplicar las mismas validaciones de sucursal y persistir los cambios, retornando codigo HTTP `200 OK`.

- **# AC-9 (Conducta No Deseada - Colision de Correo Electronico en Actualizacion):**  
  Si en una actualizacion se envia un nuevo `email` que ya le pertenece a otro usuario distinto (`id_usuario != actual`), entonces el sistema debera abortar el guardado y responder con codigo HTTP `409 Conflict` (`EMAIL_DUPLICADO`).

- **# AC-10 (Por Evento - Conmutacion de Estado Logico de Cuenta):**  
  Cuando el administrador solicite activar o suspender el acceso de un usuario (`PATCH /api/v1/admin/usuarios/{id_usuario}/estado`, con `{ "activo": boolean }`), el sistema debera actualizar el campo `activo` en la base de datos y responder con codigo HTTP `200 OK` y el estado actualizado. Si un usuario inactivo intenta autenticarse o enviar peticiones con un token previo, el sistema denegara el acceso.

- **# AC-11 (Conducta No Deseada - Proteccion Anti-Bloqueo del Ultimo Administrador Activo):**  
  Si se solicita desactivar (`activo = False`), cambiar de rol a no-administrador o eliminar al unico usuario con rol `administrador` y estado activo que existe en el sistema, entonces el sistema debera rechazar la peticion con codigo HTTP `409 Conflict` o `422 Unprocessable Entity` bajo el codigo `ULTIMO_ADMINISTRADOR_BLOQUEADO`, preservando de forma inviolable la gobernanza de la plataforma.

- **# AC-12 (Conducta No Deseada - Bloqueo de Auto-Desactivacion del Administrador en Sesion):**  
  Si el administrador actualmente autenticado intenta desactivar su propia cuenta (`id_usuario == token.sub` con `activo = False`) o degradar su propio rol, entonces el sistema debera rechazar la operacion con codigo HTTP `409 Conflict` (`AUTO_DESACTIVACION_NO_PERMITIDA`), exigiendo que la modificacion sea efectuada por otro administrador activo.

- **# AC-13 (Por Evento - Restablecimiento de Credenciales por Administrador):**  
  Cuando el administrador solicite resetear la contrasena de un usuario (`POST /api/v1/admin/usuarios/{id_usuario}/reset-password`, con `{ "nuevo_password": str }`), el sistema debera validar la complejidad de la nueva clave, hashearla con Argon2/bcrypt, actualizar `password_hash`, revocar los tokens previos si estuvieran en cache/blacklist, y responder con codigo HTTP `200 OK`.

- **# AC-14 (Conducta No Deseada - Eliminacion Destructiva de Usuarios con Dependencias):**  
  Si se solicita eliminar fisicamente un usuario (`DELETE /api/v1/admin/usuarios/{id_usuario}`) que posee registros dependientes historicos (pedidos, ventas presenciales, registros de auditoria, movimientos de caja o carritos activos), el sistema debera bloquear la eliminacion fisica con codigo HTTP `409 Conflict` (`USUARIO_CON_DEPENDENCIAS`) e instruir al administrador a efectuar la baja logica (`activo = False`).

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- **# AC-15 (Ubicuo - Arquitectura y Estado Reactivo OnPush con Signals):**  
  El componente `UsuariosAdminComponent` debera implementarse como Standalone Component con `ChangeDetectionStrategy.OnPush`, tipado estricto en TypeScript sin `any`, y gobernanza reactiva pura mediante Angular Signals (`signal()`, `computed()`) para la lista de usuarios, estados de carga (`cargando`), guardado (`guardando`), filtros y modales.

- **# AC-16 (Por Evento - Integracion en el Panel Central /admin y Boton de Retorno):**  
  El panel general `AdminDashboardComponent` debera incorporar una 4ta tarjeta boutique corporativa ("Usuarios y Roles"), visualizable para el rol `administrador`, con navegacion hacia `/admin/usuarios`. Asimismo, la vista de usuarios debera contar en su cabecera superior con el enlace de retorno sobrio `"<- Volver al Panel Principal"` direccionado a `/admin`.

- **# AC-17 (Ubicuo - Presentacion Editorial en Tabla con Monogramas y Badges):**  
  La tabla de gestion de usuarios debera presentar:
  1. Monograma circular con las iniciales del usuario en fondo Slate/Camel.
  2. Nombre completo (`nombres` + `apellidos`) con tipografia Outfit font-semibold, acompanado de su email y telefono.
  3. Badge corporativo estilizado segun el rol:
     * `administrador`: Fondo Slate oscuro (`#0F172A`), texto blanco, borde sutil Camel (`#AD8C63`).
     * `encargado_sucursal`: Fondo Indigo tenue (`bg-indigo-50`), texto Indigo (`text-indigo-900`), borde indigo.
     * `cajero`: Fondo Ambar tenue (`bg-amber-50`), texto Ambar calido (`text-amber-900`), borde ambar.
     * `cliente`: Fondo Slate neutro (`bg-slate-100`), texto Slate (`text-slate-700`).
  4. Columna de Sucursal Asignada con nombre comercial de la sede, o etiqueta "— Corporativo" para administradores.
  5. Badge de estado activo (`Activo` en Emerald) o inactivo (`Suspendido` en Slate/Rose).
  6. Menu de acciones directas: boton "Editar", conmutador rapido de estado "Activar/Suspender" y opcion "Resetear Clave".

- **# AC-18 (Ubicuo - Filtrado Reactivo Multicriterio en Tiempo Real):**  
  La interfaz debera ofrecer controles reactivos de busqueda en vivo:
  1. Input de texto con debounce para buscar por nombre, apellido o email.
  2. Selector de filtro por Rol (`Todos los roles`, `Administrador`, `Encargado de Sucursal`, `Cajero`, `Cliente`).
  3. Selector de filtro por Sucursal (alimentado por `SucursalesAdminService`).
  4. Selector de filtro por Estado (`Todos`, `Solo Activos`, `Solo Inactivos`).  
  El computo reactivo derivado (`computed()`) debera refrescar la visualizacion tabular de forma instantanea sin recargas de pagina.

- **# AC-19 (Por Evento - Modal Reactivo de Alta con Selector Dinamico de Sucursales):**  
  Cuando el usuario haga clic en `+ NUEVO USUARIO`, se abrira un modal reactivo (`formUsuario`). Si el administrador selecciona en el dropdown de roles `encargado_sucursal` o `cajero`, la interfaz debera desplegar y marcar como obligatorio el selector de sucursales (cargado desde `SucursalesAdminService`). Si selecciona `administrador` o `cliente`, el selector de sucursal se ocultara o deshabilitara automaticamente, limpiando su valor.

- **# AC-20 (Por Evento - Modal de Edicion y Cambio de Rol/Sucursal):**  
  Al pulsar "Editar" en una fila de la tabla, se abrira el modal precargado con los datos del usuario. El administrador podra modificar nombres, apellidos, telefono, rol y sucursal. Al confirmar, el servicio `UsuariosAdminService` emitira la peticion `PUT` y actualizara optimisticamente la signal local de usuarios tras recibir respuesta HTTP `200 OK`.

- **# AC-21 (Por Evento - Conmutacion Rapida de Estado Logico desde Tabla):**  
  El administrador podra pulsar sobre la accion de conmutar estado de un usuario; la interfaz invocara el endpoint de conmutacion logica (`PATCH /estado`) y reflejara de inmediato el nuevo badge de estado sin necesidad de refrescar todo el catalogo.

- **# AC-22 (Conducta No Deseada - Captura de Conflictos 409/422 y Luxury Banners):**  
  Si el backend responde con error HTTP `409 Conflict` (ej. correo duplicado, ultimo administrador) o HTTP `422 Unprocessable Entity`, el componente debera interceptar el error y renderizar un Luxury Banner contextual de alerta en tonos rose/slate dentro del modal o cabecera, preservando de manera intacta todos los datos ingresados por el operador sin resetear el formulario.

- **# AC-23 (Ubicuo - Segmentacion de Navegacion y Guards por Rol para Encargados de Sucursal):**  
  El guard de autorizacion del frontend (`roleGuard` / `authGuard`) y el panel `AdminDashboardComponent` deberan adaptar su comportamiento segun el rol del usuario autenticado:
  1. Si el usuario tiene rol `encargado_sucursal`, en el dashboard solo se mostraran las tarjetas operativas a las que tiene acceso (Prendas y Variantes - CU22; Categorias y Atributos - CU23). Las tarjetas de "Sucursales" (CU21) y "Usuarios" (CU20) no seran visibles.
  2. Si un `encargado_sucursal` intenta navegar directamente por URL a `/admin/usuarios` o `/admin/sucursales`, el guard interceptara la navegacion, bloqueando el acceso y redirigiendolo a `/admin` con notificacion de privilegio insuficiente.
  3. Si un usuario con rol `cliente` intenta ingresar a cualquier ruta `/admin/*`, sera redirigido a `/catalogo` o `/login`.

---

## 6. Criterios de Aceptacion y Verificacion (DoD - Definition of Done)

Para considerar formalmente completado el caso de uso CU20 en sus fases subsecuentes, se debera cumplir de forma irrestricta:

1. **Backend (`Ec-backend`):**
   - Modelos ORM, esquemas Pydantic v2 y servicios desacoplados bajo arquitectura limpia en `app/modules/autenticacion_seguridad/cu20_usuarios_roles`.
   - Cobertura de pruebas unitarias y de integracion al 100% con `pytest` emulando creacion, actualizacion, colision de emails (409), obligatoriedad de sucursal (422), conmutacion logica y bloqueo de degradacion/desactivacion del ultimo administrador.
   - Cero advertencias ni fallos en la suite completa de backend.

2. **Frontend Web (`Ec-frontend`):**
   - Componentes Standalone en Angular 19+ (`UsuariosAdminComponent`), servicios reactivos (`UsuariosAdminService`) y adaptacion de `AdminDashboardComponent` y guards.
   - Diseno de estetica editorial premium conforme a la guia de estilos (Outfit, paleta Slate/Camel/Obsidian, bordes rounded-xl/2xl, microinteracciones).
   - Cobertura de pruebas unitarias automatizadas con Vitest / Angular CLI (`ng test --watch=false`) al 100% verde.
   - Compilacion de produccion limpia (`ng build`) con 0 errores y 0 advertencias de tipo TypeScript.

3. **Gobernanza y Calidad:**
   - Prohibicion absoluta de emojis en codigo, plantillas, comentarios, pruebas y documentacion.
   - Entorno 100% local sin comandos hacia repositorios remotos.
   - Aprobacion formal de la presente Fase 1 previa al inicio del diseno tecnico (Fase 2).
