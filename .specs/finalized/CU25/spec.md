# Especificacion Formal de Requisitos: CU25 - Gestionar Proveedores

**ID del Caso de Uso:** CU25  
**Nombre:** Gestionar Proveedores  
**Paquete Arquitectonico:** `gestion_operativa` / `abastecimiento`  
**Modulo Backend:** `app/modules/gestion_operativa/cu25_proveedores`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu25_proveedores`  
**Actores Principales:**  
- **Administrador:** Control total sobre el padron corporativo de proveedores, alta de socios comerciales, edicion de fichas fiscales y baja logica.  
- **Encargado de Sucursal:** Consulta del catalogo de proveedores para coordinacion logistica, recepcion de albaranes de mercaderia y registro de contactos comerciales.  
**Actores Bloqueados:**  
- **Cajero:** Bloqueo estricto por politica RBAC (HTTP 403 Forbidden).  
- **Cliente:** Bloqueo estricto por politica RBAC (HTTP 403 Forbidden).  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Riesgo Medio-Alto: Integridad fiscal, no duplicidad de NIT/RUT y trazabilidad en la cadena de abastecimiento textil)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

En el modelo omnicanal de alta costura de **FashionStore**, el aprovisionamiento de prendas, colecciones de temporada (CU22) y tejidos de confeccion exclusiva depende de una red calificada de proveedores, talleres textiles y distribuidores mayoristas nacionales e internacionales.

Cada lote de mercaderia que ingresa al inventario de una boutique o centro de distribucion (CU24) a traves del movimiento operativo de Kardex `ingreso_proveedor` requiere una referencia inequivoca a una entidad comercial legalmente constituida. Asimismo, las colecciones de diseno (`fashionstore.colecciones`) y los productos base (`fashionstore.productos`) mantienen una clave foranea opcional hacia el proveedor de origen (`id_proveedor`).

El caso de uso **CU25 - Gestionar Proveedores** proporciona los mecanismos de control, gobernanza y administracion para:
1. Registrar y mantener un padron centralizado de proveedores con informacion fiscal fidedigna: Razon Social, Identificacion Tributaria (NIT/RUT unico), representante comercial de contacto, canales directos de comunicacion (telefono, email corporativo) y radicacion geografica (direccion fisica y ciudad).
2. Categorizar a los proveedores por su rubro textil o especialidad comercial (sastreria de lujo, calzado artesanal, marroquineria, alta costura femenina, tejidos naturales de seda y lino, accesorios y avios metalicos).
3. Prevenir conflictos de duplicidad tributaria o societaria mediante validaciones de unicidad estricta sobre el NIT/RUT y la Razon Social en la capa de persistencia.
4. Administrar el ciclo de vida comercial del proveedor mediante politicas de baja logica (`estado_activo = False`) y reactivacion controlada, preservando la integridad referencial historica de todas las colecciones, prendas e ingresos de inventario previamente asociados.
5. Brindar una experiencia de gestion administrativa optimizada en entorno web de escritorio para los roles `administrador` y `encargado_sucursal`, protegiendo la confidencialidad de los acuerdos comerciales frente a roles no autorizados como cajeros o clientes finales.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Tecnica y Funcional de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada con Flutter 3.x, tiene como proposito exclusivo ofrecer un canal de cara al cliente final (B2C) centrado en:
- Exploracion visual y dinamica del catalogo editorial de moda.
- Experiencia de probador virtual con Realidad Aumentada (AR).
- Reserva de prendas en boutiques y compras personales en linea.

La negociacion comercial con talleres textiles, la evaluacion de proveedores mayoristas, la gestion de datos fiscales societarios (NIT/RUT) y el registro formal de fabricantes corresponden a funciones estrictamente corporativas, contables y de administracion estrategica. Estos procesos se ejecutan desde estaciones de trabajo de oficina a traves del panel de administracion web (`Ec-frontend`), donde se dispone de pantallas de alta densidad de datos, teclados extendidos y monitores de escritorio apropiados para la manipulacion de registros fiscales.

### 2.2 Exclusion Completa y Definitiva
Por consiguiente, el caso de uso CU25 **queda formalmente excluido en su totalidad de Ec-mobile**:
- No se creara ningun endpoint publico orientado a la app movil para la entidad proveedor.
- No se implementaran modelos Dart, servicios HTTP, controladores de estado (BLoC/Riverpod) ni vistas Flutter en el directorio `Ec-mobile`.
- Todos los esfuerzos de implementacion se concentraran exclusivamente en la arquitectura desacoplada de `Ec-backend` (FastAPI + PostgreSQL Neon) y `Ec-frontend` (Angular 19+ Standalone).

---

## 3. Alcance y Trazabilidad Documental

1. **Documento Maestro del Sistema:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md)
   - Seccion 1.4 Alcance - Modulo de Compras y Proveedores: "Registro de proveedores, recepcion de mercaderia y trazabilidad comercial".
   - Seccion 2.3 Esquema Relacional de Base de Datos: Tabla `fashionstore.proveedores`.
   - Vinculacion referencial:
     * `fashionstore.colecciones.id_proveedor` -> `fashionstore.proveedores.id_proveedor`.
     * `fashionstore.productos.id_proveedor` -> `fashionstore.proveedores.id_proveedor`.
     * Movimientos de Kardex (`fashionstore.movimientos_inventario`) con `tipo_movimiento = 'ingreso_proveedor'`.
2. **Esquema Relacional en PostgreSQL Neon (Alembic `0001_base_ddl.py` y extension):**
   - Tabla `fashionstore.proveedores`:
     * `id_proveedor`: INTEGER / SERIAL PRIMARY KEY.
     * `id_usuario`: BIGINT REFERENCES `fashionstore.usuarios(id_usuario)` (Opcional, para futuros accesos de portal externo).
     * `razon_social`: VARCHAR(200) NOT NULL.
     * `nit_rut`: VARCHAR(30) NOT NULL UNIQUE (Mapeado o extendido sobre la columna `nit`).
     * `contacto_nombre`: VARCHAR(150) NOT NULL.
     * `telefono`: VARCHAR(30) NOT NULL.
     * `email`: CITEXT / VARCHAR(255) NOT NULL.
     * `direccion`: VARCHAR(255) NOT NULL.
     * `ciudad`: VARCHAR(100) NOT NULL.
     * `rubro`: VARCHAR(100) NOT NULL.
     * `estado_activo`: BOOLEAN NOT NULL DEFAULT TRUE (Mapeado sobre `activo`).
     * `creado_en`: TIMESTAMPTZ NOT NULL DEFAULT now().
     * `actualizado_en`: TIMESTAMPTZ NOT NULL DEFAULT now().
   - Restricciones DDL e Indices:
     * `uq_proveedores_nit_rut`: `UNIQUE (nit_rut)`.
     * `uq_proveedores_razon_social`: `UNIQUE (razon_social)`.
     * `idx_proveedores_estado`: Index sobre `estado_activo`.
     * `idx_proveedores_rubro`: Index sobre `rubro`.
3. **Estandares de Diseno y Codigo:**
   - Skills operativas: `fashionstore-backend-sdd` y `fashionstore-frontend-sdd`.
   - Paleta de tokens de diseno editorial Atelier: Fondo Slate 50 (`#F8FAFC`), Contenedores White (`#FFFFFF`), Acento Primario Obsidian (`#0F172A`), Acento Secundario Camel (`#AD8C63`), Bordes Slate 200 (`#E2E8F0`).
   - Paradigma reactivo web: Angular 19+, Standalone Components, ChangeDetectionStrategy.OnPush, Angular Signals y NonNullableFormBuilder.

---

## 4. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

#### Control de Acceso y Autorizacion RBAC
- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema debera exigir autenticacion valida mediante token Bearer JWT con rol `administrador` o `encargado_sucursal` para consumir cualquier endpoint bajo la ruta base `/api/v1/admin/proveedores`.
  * Si la peticion carece de token o este ha expirado/es invalido, el sistema debera responder con HTTP 401 Unauthorized (`CREDENCIALES_INVALIDAS`).
  * Si el usuario autenticado posee rol `cajero` o `cliente`, el sistema debera rechazar la peticion con HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

#### Consulta Paginada y Filtros Multicriterio
- **# AC-2 (Por Evento - Listado Paginado de Proveedores):**  
  Cuando un usuario con rol `administrador` o `encargado_sucursal` envie una solicitud `GET /api/v1/admin/proveedores`, el sistema debera retornar una respuesta estructurada con la lista paginada de proveedores y sus metadatos de control:
  * Coleccion de elementos (`items`): `id_proveedor`, `razon_social`, `nit_rut`, `contacto_nombre`, `telefono`, `email`, `direccion`, `ciudad`, `rubro`, `estado_activo`, `creado_en`, `actualizado_en`.
  * Metadatos de paginacion: `total` (total de registros coincidentes), `pagina` (pagina actual), `limite` (registros solicitados), `total_paginas` (total calculado de paginas).
  * Ordenamiento por defecto: `id_proveedor` descendente.

- **# AC-3 (Opcional - Filtros Multicriterio de Proveedores):**  
  Donde se especifiquen parametros opcionales de filtrado en la peticion `GET /api/v1/admin/proveedores`:
  * `q`: Busqueda textual no sensible a mayusculas (operador `ILIKE`) aplicada sobre `razon_social`, `nit_rut` o `contacto_nombre`.
  * `estado_activo`: Booleano para filtrar exclusivamente proveedores activos (`True`) o inactivos (`False`). Si el parametro no se suministra o recibe el valor `'todos'`, se deberan devolver ambos estados.
  * `rubro`: Cadena de texto para filtrar proveedores de una especialidad comercial especifica (ej. "Sastreria", "Calzado", "Tejidos").  
  El sistema debera combinar las condiciones activas mediante conjuncion logica (`AND`).

- **# AC-4 (Por Evento - Consulta de Proveedor por Identificador):**  
  Cuando un usuario autorizado solicite consultar la ficha detallada de un proveedor mediante `GET /api/v1/admin/proveedores/{id_proveedor}`, el sistema debera retornar el objeto completo del proveedor con HTTP 200 OK.
  * Si el `id_proveedor` no existe en la base de datos, el sistema debera responder con HTTP 404 Not Found (`PROVEEDOR_NO_ENCONTRADO`).

#### Registro de Nuevo Proveedor (Alta)
- **# AC-5 (Por Evento - Alta de Proveedor):**  
  Cuando un usuario autorizado envie una solicitud `POST /api/v1/admin/proveedores` con el payload de creacion que contenga:
  * `razon_social`: Texto obligatorio de entre 3 y 200 caracteres.
  * `nit_rut`: Texto obligatorio de entre 5 y 30 caracteres.
  * `contacto_nombre`: Texto obligatorio de entre 3 y 150 caracteres.
  * `telefono`: Texto obligatorio de entre 7 y 30 caracteres.
  * `email`: Correo electronico con formato sintactico valido.
  * `direccion`: Texto obligatorio de entre 5 y 255 caracteres.
  * `ciudad`: Texto obligatorio de entre 2 y 100 caracteres.
  * `rubro`: Texto obligatorio de entre 3 y 100 caracteres.  
  El sistema debera sanitizar las cadenas (eliminando espacios redundantes), persistir el registro con `estado_activo = True` y marcas temporales `creado_en` y `actualizado_en` sincronizadas en UTC, y responder con HTTP 201 Created junto a la entidad completa creada.

- **# AC-6 (Invariante - Prevencion de Duplicidad de NIT/RUT o Razon Social):**  
  Si en una operacion de alta o edicion se proporciona un `nit_rut` que ya pertenece a otro proveedor registrado, el sistema debera abortar la transaccion y responder con HTTP 409 Conflict (`NIT_RUT_DUPLICADO`). De igual forma, si la `razon_social` ya existe de manera identica (insensible a mayusculas/minusculas), el sistema debera responder con HTTP 409 Conflict (`RAZON_SOCIAL_DUPLICADA`).

- **# AC-7 (Invariante - Validacion de Formato y Reglas de Integridad):**  
  Si los datos suministrados en la creacion o actualizacion incumplen las restricciones de longitud, contienen valores vacios en campos obligatorios o presentan un formato de correo electronico invalido, el sistema debera rechazar la solicitud con HTTP 422 Unprocessable Entity, detallando el campo causante en el arreglo de errores.

#### Modificacion de Ficha Comercial (Edicion)
- **# AC-8 (Por Evento - Actualizacion de Datos de Proveedor):**  
  Cuando un usuario autorizado envie una solicitud `PUT /api/v1/admin/proveedores/{id_proveedor}` con los datos actualizados de contacto, fiscales o de ubicacion, el sistema debera:
  * Verificar la existencia previa del proveedor (de lo contrario, responder con HTTP 404).
  * Validar que el nuevo `nit_rut` o la nueva `razon_social` no colisionen con otro proveedor existente diferente al que se esta modificando (HTTP 409).
  * Aplicar los cambios sobre las columnas correspondientes.
  * Actualizar automaticamente el campo `actualizado_en` con la marca temporal actual en UTC.
  * Retornar la entidad modificada con HTTP 200 OK.

#### Gestion del Estado Operativo (Baja Logica y Reactivacion)
- **# AC-9 (Por Evento - Baja Logica de Proveedor):**  
  Cuando un usuario autorizado solicite desactivar un proveedor mediante `PATCH /api/v1/admin/proveedores/{id_proveedor}/estado` con `estado_activo = False` (o `DELETE /api/v1/admin/proveedores/{id_proveedor}`), el sistema debera:
  * Comprobar la existencia del proveedor (HTTP 404 si no existe).
  * Establecer `estado_activo = False` y refrescar `actualizado_en`.
  * Preservar intacta la fila en la tabla `fashionstore.proveedores` para mantener la integridad referencial historica de compras, albaranes, productos y colecciones previas.
  * Responder con HTTP 200 OK y un mensaje confirmatorio de desactivacion.

- **# AC-10 (Por Evento - Reactivacion de Proveedor Inactivo):**  
  Cuando un usuario autorizado envie `PATCH /api/v1/admin/proveedores/{id_proveedor}/estado` con `estado_activo = True`, el sistema debera restaurar el estado activo del proveedor, permitiendo su seleccion inmediata en recepcion de compras y vinculacion de prendas, respondiendo con HTTP 200 OK.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en Panel Principal y Navegacion
- **# AC-11 (Ubicuo - Acceso desde Dashboard Administrativo):**  
  El componente `AdminDashboardComponent` debera incorporar una tarjeta boutique interactiva dentro de la categoria *"Gestion de Abastecimiento"*:
  * Titulo: *"Proveedores y Fabricantes"*.
  * Descripcion: *"Padron de talleres textiles, identificacion tributaria y contactos directos de abastecimiento"*.
  * Icono editorial representativo de aprovisionamiento logistico (SVG limpio, sin emojis).
  * Enlace de navegacion hacia la ruta protegida `/admin/proveedores`.

- **# AC-12 (Ubicuo - Estructura de la Vista /admin/proveedores):**  
  La pagina `ProveedoresAdminComponent` debera implementarse bajo las directivas institucionales:
  * Componente Standalone con `ChangeDetectionStrategy.OnPush`.
  * Gestion reactiva mediante Angular `Signals` (`proveedores`, `cargando`, `guardando`, `error`, `mensajeExito`, `filtros`, `proveedorSeleccionado`).
  * Boton superior de navegacion: `<- Volver al Panel Principal`, que redirige hacia `/admin`.
  * Encabezado editorial de lujo: Titulo *"Gestion de Proveedores y Talleres"* con subtitulo informativo del padron comercial.

#### Barra de Herramientas, Busqueda y Filtros
- **# AC-13 (Por Evento - Filtrado Reactivo con Debounce):**  
  La vista debera incluir una barra de herramientas superior con:
  * Campo de busqueda textual (`busquedaTexto`) con retardo controlado (*debounce* de 300 ms) conectado al parametro `q` para buscar por Razon Social, NIT o Contacto.
  * Selector reactivo de estado con opciones: *"Todos los estados"*, *"Solo activos"* y *"Solo inactivos"*.
  * Selector reactivo de rubro con opciones comerciales cargadas dinamicamente o predefinidas.
  * Boton de accion principal: `+ Nuevo Proveedor`, estilizado con acento Obsidian y Camel.

#### Tabla Maestra Editorial de Proveedores
- **# AC-14 (Ubicuo - Visualizacion en Tabla Maestra):**  
  La tabla debera presentar la informacion estructurada con tipografia Outfit y bordes sutiles Slate:
  * **Razon Social y Rubro:** Nombre legal de la empresa con badge tipografico del rubro textil.
  * **NIT / RUT:** Identificacion tributaria destacada en monospace o formato distintivo.
  * **Contacto:** Nombre del representante y telefono de contacto directo.
  * **Email y Ciudad:** Correo electronico y ciudad de origen.
  * **Estado:** Insignia visual de lujo: verde esmeralda con texto *"Activo"* para proveedores habilitados; gris Slate con texto *"Inactivo"* para dados de baja.
  * **Acciones:** Boton de edicion (icono lapiz SVG) y boton de conmutacion de estado (icono alternador o baja logica SVG).

#### Formularios Reactivos de Alta y Edicion (Modales)
- **# AC-15 (Por Evento - Modal Reactivo de Alta de Proveedor):**  
  Al hacer clic en `+ Nuevo Proveedor`, el sistema debera desplegar un modal reactivo basado en `NonNullableFormBuilder`:
  * Campos del formulario: `razon_social`, `nit_rut`, `contacto_nombre`, `telefono`, `email`, `direccion`, `ciudad`, `rubro`.
  * Validadores sincronos: obligatoriedad en todos los campos, formato de correo valido (`Validators.email`) y longitudes minimas estipuladas.
  * Deshabilitacion reactiva del boton de guardado mientras el formulario sea invalido o el Signal `guardando()` sea verdadero.
  * Cierre accesible mediante boton de aspa, tecla `Escape` o clic en backdrop.

- **# AC-16 (Por Evento - Modal Reactivo de Edicion de Proveedor):**  
  Al presionar el boton de edicion en una fila, el sistema debera cargar los datos del proveedor en el formulario reactivo y abrir el modal en modo modificacion:
  * Muestra claramente el identificador del proveedor en el encabezado del modal.
  * Permite actualizar la totalidad de los datos comerciales y de contacto.
  * Al guardar exitosamente, actualiza reactivamente la lista en memoria y emite feedback visual.

- **# AC-17 (Por Evento - Confirmacion de Desactivacion / Baja Logica):**  
  Al presionar la accion de desactivar proveedor, el sistema debera presentar un dialogo modal de confirmacion con estilo editorial que advierta que el proveedor quedara inhabilitado para futuras recepciones de mercaderia. Al confirmar, enviara la solicitud `PATCH` y actualizara el badge de estado en tiempo real.

#### Retroalimentacion Contextual y Manejo de Errores
- **# AC-18 (Ubicuo - Luxury Banners de Estado y Feedback):**  
  La pantalla debera incluir un contenedor superior de banners contextuales:
  * **Banner de Exito:** Fondo suave verde/camel con mensaje confirmatorio tras alta, edicion o cambio de estado.
  * **Banner de Conflicto (409):** Alerta clara si el NIT/RUT o la Razon Social ya estan registrados en el sistema.
  * **Banner de Validacion (422):** Notificacion explicativa si algun dato no cumple con las reglas fiscales o de formato.
  * **Banner de Error Inesperado:** Mensaje controlado que orienta al usuario si ocurre un fallo de red o caida de servicio.

- **# AC-19 (Ubicuo - Estados de Carga, Paginacion y Estado Vacio):**  
  La interfaz debera manejar:
  * Indicador de carga sutil durante la peticion HTTP (`cargando() = true`).
  * Controles de paginacion inferior (pagina anterior, pagina siguiente, indicador "Pagina X de Y" y selector de limite 10/20/50).
  * Estado vacio (*Empty State*) editorial cuando no existan proveedores registrados o la busqueda no arroje coincidencias, invitando a registrar el primer proveedor o limpiar los filtros.

---

## 5. Matriz de Trazabilidad de Requisitos

| Criterio EARS | Capa | Componente / Archivo Proyectado | Metodo / Endpoint | Codigo HTTP Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Backend | `cu25_proveedores/router.py` | Dependencia `require_roles(["administrador", "encargado_sucursal"])` | 401 / 403 |
| **# AC-2** | Backend | `cu25_proveedores/router.py` | `GET /api/v1/admin/proveedores` | 200 OK |
| **# AC-3** | Backend | `cu25_proveedores/servicio.py` | `listar_proveedores(db, filtros)` | 200 OK |
| **# AC-4** | Backend | `cu25_proveedores/router.py` | `GET /api/v1/admin/proveedores/{id}` | 200 OK / 404 |
| **# AC-5** | Backend | `cu25_proveedores/servicio.py` | `POST /api/v1/admin/proveedores` | 201 Created |
| **# AC-6** | Backend | `cu25_proveedores/servicio.py` | Validacion de unicidad NIT / Razon Social | 409 Conflict |
| **# AC-7** | Backend | `cu25_proveedores/esquemas.py` | Validadores Pydantic v2 en `ProveedorCrearIn` | 422 Unprocessable |
| **# AC-8** | Backend | `cu25_proveedores/servicio.py` | `PUT /api/v1/admin/proveedores/{id}` | 200 OK / 409 |
| **# AC-9** | Backend | `cu25_proveedores/servicio.py` | `PATCH /api/v1/admin/proveedores/{id}/estado` | 200 OK |
| **# AC-10** | Backend | `cu25_proveedores/servicio.py` | Reactivacion `estado_activo = True` | 200 OK |
| **# AC-11** | Frontend | `admin-dashboard.component.html` | Tarjeta "Proveedores y Fabricantes" en Abastecimiento | N/A |
| **# AC-12** | Frontend | `proveedores-admin.component.ts` | Ruta `/admin/proveedores`, OnPush, boton volver | N/A |
| **# AC-13** | Frontend | `proveedores-admin.component.ts` | Input busqueda con debounce y filtros Signals | N/A |
| **# AC-14** | Frontend | `proveedores-admin.component.html` | Tabla maestra con badges y acciones | N/A |
| **# AC-15** | Frontend | `proveedores-admin.component.ts` | Modal alta con `NonNullableFormBuilder` | N/A |
| **# AC-16** | Frontend | `proveedores-admin.component.ts` | Modal edicion de ficha comercial | N/A |
| **# AC-17** | Frontend | `proveedores-admin.component.ts` | Modal confirmacion de baja logica | N/A |
| **# AC-18** | Frontend | `proveedores-admin.component.html` | Luxury Banners de estado contextual | N/A |
| **# AC-19** | Frontend | `proveedores-admin.component.html` | Paginacion, loading skeleton y empty state | N/A |

---

## 6. Definicion de Terminado (Definition of Done - DoD) para Fase 1

La Fase 1 (Requisitos EARS) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU25/spec.md` se encuentre debidamente redactado y almacenado en el repositorio local.
2. Se haya ratificado explicitamente la exclusion total de la aplicacion movil (`Ec-mobile`).
3. Todos los criterios de aceptacion (# AC-1 a # AC-19) esten enumerados, clasificados segun la sintaxis EARS y vinculados a sus capas tecnicas correspondientes.
4. Se haya auditado que el documento carece al 100% de caracteres emoji o informales.
5. El usuario apruebe formalmente esta especificacion para autorizar la transicion a la Fase 2 (Diseno de Arquitectura y Contratos).
