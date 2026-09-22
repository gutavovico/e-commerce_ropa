# Especificacion de Requisitos: [CU24] Gestionar temporadas y colecciones

**Codigo del Caso de Uso:** CU24  
**Denominacion Oficial:** Gestionar temporadas y colecciones  
**Modulo Funcional:** Catalogo / Taxonomia Comercial (`catalogo_productos`)  
**Actores Primarios:**  
- Administrador Corporativo (Acceso irrestricto: creacion, modificacion, conmutacion de vigencias y baja logica)  
- Encargado de Sucursal (Acceso de consulta operativa para planificacion de mercadeo y escaparates)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Entorno de Implementacion:** Web corporativa exclusiva (`Ec-backend` FastAPI y `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal de Plataforma:** `Ec-mobile` (Flutter) 100% excluida  

---

## 1. Vision General del Caso de Uso

### 1.1 Proposito y Justificacion de Negocio
El caso de uso "Gestionar temporadas y colecciones" dota a la cadena comercial FashionStore de los mecanismos de estructuracion temporal y tematica de su catalogo de indumentaria de alta gama.  
En la industria textil y de retail de lujo, las prendas no operan como articulos estaticos o aislados; se articulan alrededor de ciclos estacionales (temporadas de moda con vigencias de calendario definidas) y narrativas de estilo (colecciones o capsulas tematicas creadas por disenadores o talleres asociados).

Este modulo centraliza:
1. La planificacion de temporadas comerciales (ej. "Primavera - Verano 2026", "Otono - Invierno 2026", "Crucero 2027"), con fechas formales de inicio y fin que gobiernan el calendario comercial, su ano de vigencia y su conmutacion activa/inactiva.
2. La curaduria de colecciones capsula asociadas a cada temporada (ej. "Capsula Lino Natural", "Gala Seda Obsidian", "Resort Minimal"), vinculando cada linea de prendas a su concepto creativo y temporada matriz.
3. El soporte de integridad relacional hacia el catalogo de productos (`ProductoORM`), permitiendo clasificar y agrupar las prendas de la marca segun su lanzamiento comercial sin comprometer la persistencia historica de ventas o inventario mediante bajas logicas controladas.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Arquitectonica y de Negocio
La aplicacion movil de FashionStore (`Ec-mobile`), construida sobre Flutter 3.x, tiene como proposito exclusivo la experiencia de compra B2C orientada al consumidor final (navegacion fluida por vitrinas de moda, probador virtual inmersivo mediante Realidad Aumentada, configuracion de bolsa de compras y pago digital).

La definicion del calendario comercial de la moda, la apertura o cierre de temporadas estacionales, el establecimiento de fechas de vigencia comercial y el alta o parametrizacion de colecciones capsula constituyen labores analiticas, gerenciales y de mercadeo que pertenecen con exclusividad a la trastienda corporativa de administracion. Estas tareas se llevan a cabo en estaciones de trabajo de escritorio a traves del portal web `Ec-frontend`.

### 2.2 Ratificacion de Alcance Tecnico
1. Cero pantallas en `Ec-mobile`: No se desarrollara ninguna vista, modal ni formulario de administracion de temporadas o colecciones en la aplicacion Flutter.
2. Cero servicios mutables en Flutter: No se implementaran llamadas de creacion, actualizacion ni cambio de estado hacia `/api/v1/admin/temporadas` o `/api/v1/admin/colecciones` en la app movil.
3. Consumo pasivo futuro: La aplicacion movil interactua con las temporadas de forma indirecta y de solo lectura a traves del endpoint publico del catalogo (`/api/v1/productos` o `/api/v1/filtros/catalogo`), sin capacidad alguna de alterar la parametrizacion comercial.

---

## 3. Especificacion de Requisitos Funcionales bajo Sintaxis EARS

### Bloque A: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

#### Seguridad, Autenticacion y Control de Acceso RBAC
- **# AC-1 (Ubicuo - Autenticacion Obligatoria):**  
  El sistema debera exigir un token de acceso JWT valido en la cabecera `Authorization: Bearer <token>` para cualquier solicitud dirigida a las rutas base `/api/v1/admin/temporadas` y `/api/v1/admin/colecciones`. Si la cabecera no se provee o el token es invalido o ha expirado, el sistema debera rechazar la operacion con HTTP 401 Unauthorized.

- **# AC-2 (Condicional - Control de Acceso RBAC por Rol):**  
  Si un usuario autenticado con rol `cajero` o `cliente` intenta acceder a cualquier operacion de consulta, creacion, modificacion o conmutacion de estado bajo `/api/v1/admin/temporadas` o `/api/v1/admin/colecciones`, el sistema debera rechazar la peticion de forma determinista con HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

- **# AC-3 (Ubicuo - Segregacion Funcional de Operacion):**  
  El sistema debera admitir las solicitudes segun el rol autenticado:
  * Rol `administrador`: Control total (consulta paginada, creacion de temporadas y colecciones, edicion de metadatos, baja logica y reactivacion).
  * Rol `encargado_sucursal`: Acceso a la consulta paginada y detalle de temporadas y colecciones para coordinacion de producto en tienda, sin facultades destructivas.

#### Entidades del Dominio y Reglas de Negocio de Temporadas
- **# AC-4 (Ubicuo - Estructura de Entidad Temporada):**  
  El sistema debera persistir la entidad `TemporadaORM` en la tabla `fashionstore.temporadas` conteniendo los campos:
  * `id_temporada`: Identificador clave primaria entero autoincremental.
  * `nombre`: Cadena de texto no nula (longitud minima 3, maxima 100 caracteres), unica en el sistema (insensible a mayusculas/minusculas).
  * `anio`: Entero no nulo que representa el ano comercial de la temporada (valor minimo admitido: 2020).
  * `fecha_inicio`: Fecha de inicio formal de la temporada comercial (`DATE`), obligatoria.
  * `fecha_fin`: Fecha de finalizacion formal de la temporada comercial (`DATE`), obligatoria.
  * `estado_activo`: Booleano no nulo, con valor predeterminado `True`.
  * `creado_en`: Marca temporal UTC con zona horaria de creacion del registro.
  * `actualizado_en`: Marca temporal UTC con zona horaria de ultima modificacion.

- **# AC-5 (Condicional - Validacion de Cronograma de Temporada):**  
  Si en una solicitud de creacion o actualizacion de temporada la `fecha_inicio` es posterior o igual a la `fecha_fin`, el sistema debera rechazar la operacion respondiendo con HTTP 422 Unprocessable Entity, especificando el error semantico `FECHAS_TEMPORADA_INVALIDAS` ("La fecha de inicio debe ser anterior a la fecha de finalizacion").

- **# AC-6 (Condicional - Validacion de Unicidad de Nombre de Temporada):**  
  Si se intenta crear o renombrar una temporada utilizando un nombre que coincida con una temporada existente (normalizado mediante conversion a minusculas y eliminacion de espacios en los extremos), el sistema debera abortar la transaccion y responder con HTTP 409 Conflict (`TEMPORADA_NOMBRE_DUPLICADO`).

- **# AC-7 (Por Evento - Listado Paginado y Filtrado de Temporadas):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/temporadas`, el sistema debera retornar la lista paginada de temporadas aplicando filtros opcionales:
  * `q`: Busqueda textual parcial (operador `ILIKE`) sobre el nombre de la temporada.
  * `anio`: Filtrado entero para restringir temporadas de un ano especifico.
  * `estado_activo`: Filtrado booleano (`true`, `false` o `todos`).
  * `ordenar_por`: Criterio de ordenacion (`anio_desc`, `anio_asc`, `nombre_asc`, `nombre_desc`, `fecha_desc`). Por defecto: `anio_desc`.
  * `pagina` (default 1) y `limite` (default 10, maximo 100).
  La respuesta debera incluir la lista de items, total de registros, pagina actual, limite y total de paginas.

- **# AC-8 (Por Evento - Baja Logica y Reactivacion de Temporada):**  
  Cuando el usuario administrador envie una solicitud `PATCH /api/v1/admin/temporadas/{id_temporada}/estado` con el cuerpo `{"estado_activo": boolean}`, el sistema debera:
  * Si `estado_activo = False`, inhabilitar la temporada para nuevas asociaciones de prendas en catalogo, preservando intacta la integridad referencial de los productos ya asignados historicamente.
  * Si `estado_activo = True`, reactivar la temporada habilitandola para nuevas campanas.
  * Retornar la entidad actualizada con HTTP 200 OK.

#### Entidades del Dominio y Reglas de Negocio de Colecciones
- **# AC-9 (Ubicuo - Estructura de Entidad Coleccion):**  
  El sistema debera persistir la entidad `ColeccionORM` en la tabla `fashionstore.colecciones` conteniendo los campos:
  * `id_coleccion`: Identificador clave primaria entero autoincremental.
  * `id_temporada`: Clave foranea entera no nula referenciando `fashionstore.temporadas(id_temporada)`.
  * `nombre`: Cadena de texto no nula (minimo 3, maximo 150 caracteres), unica dentro de la misma temporada.
  * `descripcion`: Texto descriptivo opcional del concepto creativo o capsula.
  * `estado_activo`: Booleano no nulo, con valor predeterminado `True`.
  * `creado_en`: Marca temporal UTC con zona horaria de creacion del registro.
  * `actualizado_en`: Marca temporal UTC con zona horaria de ultima modificacion.

- **# AC-10 (Condicional - Validacion de Unicidad de Coleccion por Temporada):**  
  Si se intenta crear o renombrar una coleccion utilizando un nombre que ya exista dentro de la misma temporada, el sistema debera rechazar la operacion con HTTP 409 Conflict (`COLECCION_NOMBRE_DUPLICADO`). Se admitira el mismo nombre de coleccion si pertenece a temporadas distintas.

- **# AC-11 (Condicional - Integridad de Temporada Matriz):**  
  Si se intenta crear una coleccion referenciando un `id_temporada` inexistente, el sistema debera rechazar la operacion con HTTP 404 Not Found (`TEMPORADA_NO_ENCONTRADA`). Si la temporada matriz se encuentra en estado inactivo (`estado_activo = False`), el sistema debera rechazar el alta de nuevas colecciones bajo dicha temporada con HTTP 422 Unprocessable Entity (`TEMPORADA_INACTIVA_NO_PERMITE_COLECCIONES`).

- **# AC-12 (Por Evento - Listado Paginado y Filtrado de Colecciones):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/colecciones`, el sistema debera retornar la lista paginada de colecciones con su objeto de temporada anidado (`temporada_nombre`, `temporada_anio`), permitiendo filtrar por:
  * `q`: Busqueda textual sobre el nombre o descripcion de la coleccion.
  * `id_temporada`: Filtrado por temporada matriz.
  * `estado_activo`: Filtrado booleano (`true`, `false` o `todos`).
  * `pagina` y `limite`.

- **# AC-13 (Por Evento - Baja Logica de Coleccion):**  
  Cuando un usuario administrador envie una solicitud `PATCH /api/v1/admin/colecciones/{id_coleccion}/estado`, el sistema debera conmutar su `estado_activo` sin eliminar fisicamente el registro, preservando la trazabilidad de los productos asociados en `fashionstore.productos`.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en Dashboard Principal y Navegacion
- **# AC-14 (Ubicuo - Tarjeta en AdminDashboardComponent):**  
  El componente `AdminDashboardComponent` debera exhibir una tarjeta boutique dentro de la seccion *"Taxonomia Comercial"*:
  * Titulo oficial: *"Gestionar temporadas y colecciones"*.
  * Descripcion: *"Calendario estacional de la moda, vigencias de campana y curaduria de colecciones capsula"*.
  * Badge: *"Calendario de Moda"*.
  * Boton de navegacion con `id="btn-gestionar-temporadas-colecciones"` y `routerLink="/admin/temporadas-colecciones"`.
  * Icono vectorial SVG limpio representativo de calendario / diseno editorial (sin emojis).
  * Visibilidad condicionada por RBAC para `administrador` y `encargado_sucursal`.

#### Arquitectura de la Vista `/admin/temporadas-colecciones`
- **# AC-15 (Ubicuo - Layout Editorial y Cabecera):**  
  La vista `TemporadasColeccionesAdminComponent` debera implementarse bajo las directivas institucionales:
  * Componente Standalone con `ChangeDetectionStrategy.OnPush`.
  * Contenedor institucional con ancho maximo `max-w-[1440px] px-6 py-8 mx-auto` y fondo Slate 50.
  * Encabezado H1 principal exacto: *"Gestionar temporadas y colecciones"*.
  * Miga de pan (*Breadcrumb*): *"FASHION STORE / ADMINISTRACION CORPORATIVA / GESTIONAR TEMPORADAS Y COLECCIONES"*.
  * Boton superior de navegacion: *"Volver al Panel Principal"* con `routerLink="/admin"`.

#### Sistema de Pestanas Reactivas y Barras de Filtros
- **# AC-16 (Por Evento - Sistema de Pestanas Reactivas):**  
  La vista debera disponer de un conmutador de pestanas (*Tabs*) gobernado por Signals:
  * Pestana 1: *"Temporadas Comerciales"* (Gestion de periodos de moda, anos y cronogramas).
  * Pestana 2: *"Colecciones y Capsulas"* (Curaduria de lineas tematicas y asociacion a temporadas).
  Al alternar de pestana, la interfaz debera actualizar fluidamente la tabla activa y su barra de filtros correspondiente.

- **# AC-17 (Por Evento - Barra de Filtros con Debounce):**  
  Cada pestana debera proveer su respectiva barra de herramientas reactiva:
  * Campo de busqueda textual con retardo (*debounce* de 300 ms).
  * Selectores desplegables de Estado (*"Todos los estados"*, *"Activas"*, *"Inactivas"*).
  * En pestana Colecciones: selector reactivo de Temporada matriz para filtrar capsulas pertenecientes a una campana especifica.
  * Boton de limpieza rapida de filtros.

#### Tablas Maestras y Acciones de Gestion
- **# AC-18 (Ubicuo - Tabla Maestra de Temporadas):**  
  La tabla de temporadas debera presentar:
  * Nombre de la temporada y ano estacional.
  * Rango de vigencia formal (`fecha_inicio` a `fecha_fin`) en formato legible.
  * Badge de estado activo/inactivo (verde esmeralda para activo, slate para inactivo).
  * Conteo de colecciones asociadas.
  * Acciones: Boton de edicion para abrir modal y boton conmutador de baja logica / reactivacion.

- **# AC-19 (Ubicuo - Tabla Maestra de Colecciones):**  
  La tabla de colecciones debera presentar:
  * Nombre de la coleccion y concepto/descripcion resumida.
  * Temporada asignada con indicacion de ano.
  * Insignia de estado cromada.
  * Acciones: Boton de edicion y boton de conmutacion de estado.

#### Formularios Reactivos y Modales Accesibles
- **# AC-20 (Por Evento - Modal de Alta y Edicion de Temporada):**  
  Al presionar *"Nueva Temporada"* o *"Editar"*, el sistema debera desplegar un modal accesible con `NonNullableFormBuilder`:
  * Campos: `nombre`, `anio`, `fecha_inicio`, `fecha_fin`.
  * Validador sincrono de rango de fechas que verifique en tiempo real que `fecha_fin` sea estrictamente posterior a `fecha_inicio`.
  * Bloqueo del boton de confirmacion mientras el formulario sea invalido o este guardando.

- **# AC-21 (Por Evento - Modal de Alta y Edicion de Coleccion):**  
  Al presionar *"Nueva Coleccion"* o *"Editar"*, el sistema debera desplegar un modal accesible con:
  * Selector obligatorio de Temporada matriz (cargado dinamicamente con temporadas activas).
  * Campos: `nombre` (minimo 3 caracteres) y `descripcion` (opcional).
  * Validacion de obligatoriedad y bloqueo ante envios duplicados.

#### Resiliencia, Luxury Banners y Notificaciones
- **# AC-22 (Ubicuo - Luxury Banners No Destructivos):**  
  En caso de presentarse una respuesta HTTP 409 Conflict (nombre duplicado) o HTTP 422 Unprocessable Entity (fechas inconsistentes), la interfaz debera mostrar un Luxury Banner contextual de alerta en la parte superior sin cerrar el modal ni limpiar los campos ingresados por el operador.

- **# AC-23 (Ubicuo - Paginacion y Estados de Carga):**  
  Las listas de ambas pestanas deberan exhibir skeleton loaders durante `cargando() = true`, mensajes claros de estado vacio (*Empty State*) cuando no existan coincidencias y controles de paginacion inferior (*"Anterior"*, *"Siguiente"*, *"Pagina X de Y"*).

---

## 4. Matriz de Trazabilidad de Requisitos

| Criterio EARS | Capa | Componente / Archivo | Metodo / Endpoint | Codigo HTTP Esperado |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Backend | `cu24_temporadas_colecciones/router.py` | Dependencia `get_current_user` | 401 Unauthorized |
| **# AC-2** | Backend | `cu24_temporadas_colecciones/router.py` | `require_roles(["administrador", "encargado_sucursal"])` | 403 Forbidden |
| **# AC-3** | Backend | `cu24_temporadas_colecciones/servicio.py` | Segregacion funcional por rol | 200 OK |
| **# AC-4** | Backend | `cu24_temporadas_colecciones/modelos.py` | Entidad `TemporadaORM` en PostgreSQL | N/A |
| **# AC-5** | Backend | `cu24_temporadas_colecciones/esquemas.py` | Validador Pydantic `@model_validator` de fechas | 422 Unprocessable |
| **# AC-6** | Backend | `cu24_temporadas_colecciones/servicio.py` | Verificacion de nombre unico de temporada | 409 Conflict |
| **# AC-7** | Backend | `cu24_temporadas_colecciones/router.py` | `GET /api/v1/admin/temporadas` | 200 OK |
| **# AC-8** | Backend | `cu24_temporadas_colecciones/router.py` | `PATCH /api/v1/admin/temporadas/{id}/estado` | 200 OK |
| **# AC-9** | Backend | `cu24_temporadas_colecciones/modelos.py` | Entidad `ColeccionORM` en PostgreSQL | N/A |
| **# AC-10** | Backend | `cu24_temporadas_colecciones/servicio.py` | Verificacion de unicidad por temporada | 409 Conflict |
| **# AC-11** | Backend | `cu24_temporadas_colecciones/servicio.py` | Validacion de temporada activa para nueva coleccion | 404 / 422 |
| **# AC-12** | Backend | `cu24_temporadas_colecciones/router.py` | `GET /api/v1/admin/colecciones` | 200 OK |
| **# AC-13** | Backend | `cu24_temporadas_colecciones/router.py` | `PATCH /api/v1/admin/colecciones/{id}/estado` | 200 OK |
| **# AC-14** | Frontend | `admin-dashboard.component.html` | Tarjeta boutique bajo "Taxonomia Comercial" | N/A |
| **# AC-15** | Frontend | `temporadas-colecciones-admin.component.ts` | Layout editorial OnPush `max-w-[1440px]` | N/A |
| **# AC-16** | Frontend | `temporadas-colecciones-admin.component.html` | Selector de pestanas reactivas (Temporadas / Colecciones) | N/A |
| **# AC-17** | Frontend | `temporadas-colecciones-admin.component.ts` | Barra de filtros con debounce de 300 ms y Signals | N/A |
| **# AC-18** | Frontend | `temporadas-colecciones-admin.component.html` | Tabla maestra de temporadas con badges y acciones | N/A |
| **# AC-19** | Frontend | `temporadas-colecciones-admin.component.html` | Tabla maestra de colecciones y capsulas | N/A |
| **# AC-20** | Frontend | `temporadas-colecciones-admin.component.ts` | Modal reactivo de temporada con validacion de fechas | N/A |
| **# AC-21** | Frontend | `temporadas-colecciones-admin.component.ts` | Modal reactivo de coleccion vinculado a temporada | N/A |
| **# AC-22** | Frontend | `temporadas-colecciones-admin.component.html` | Luxury Banners para contingencias no destructivas | N/A |
| **# AC-23** | Frontend | `temporadas-colecciones-admin.component.html` | Skeletons de carga, empty states y paginacion | N/A |

---

## 5. Definicion de Terminado (Definition of Done - DoD) para Fase 1

La Fase 1 (Requisitos EARS) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU24/spec.md` se encuentre guardado en el repositorio local.
2. Se haya ratificado explicitamente la exclusion total de la aplicacion movil (`Ec-mobile`), documentando su justificacion tecnica en la Seccion 2.
3. Todos los criterios de aceptacion (# AC-1 a # AC-23) esten numerados, clasificados segun la sintaxis formal EARS y vinculados a sus capas tecnicas correspondientes.
4. Se haya auditado que el documento carece al 100% de caracteres emoji o lenguaje informal.
5. Se respete estrictamente la prohibicion de modificar codigo productivo en `Ec-backend`, `Ec-frontend` o `Ec-mobile` durante esta fase.
