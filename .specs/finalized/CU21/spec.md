# Especificación Formal de Requisitos: CU21 - Gestionar Sucursales y Ciudades

**ID del Caso de Uso:** CU21  
**Nombre:** Gestionar Sucursales y Ciudades  
**Paquete Arquitectónico:** `gestion_operativa`  
**Módulo Backend:** `app/modules/gestion_operativa/cu21_sucursales_ciudades`  
**Actor Principal:** Administrador  
**Actores Secundarios (Lectura):** Cliente, Encargado de Sucursal, Cajero, Sistema  
**Metodología:** Spec-Driven Development (SDD) & PUDS  
**Nivel de Riesgo:** Nivel 3 (Alto Riesgo: Afecta la infraestructura territorial, integridad de inventario por sucursal, asignación de usuarios y reservas de probador)  
**Estado:** Aprobado y Promovido a Permanente  

---

## 1. Propósito y Contexto de Negocio

El sistema **FashionStore** opera bajo un modelo de comercio omnicanal de alta costura femenina que integra la venta digital con la experiencia física en boutiques exclusivas. Cada boutique física (sucursal) está localizada en una ciudad específica, cuenta con un horario de atención para reservas de probador y retiro de compras, y constituye el nodo central donde se custodia el inventario físico (`inventario_sucursal`) y donde operan los empleados (encargados de sucursal y cajeros).

El **CU21 - Gestionar Sucursales y Ciudades** proporciona las herramientas administrativas para:
1. Registrar, consultar, actualizar y dar de baja ciudades de operación comercial.
2. Registrar, consultar, actualizar y dar de baja sucursales físicas (nombre de boutique, dirección, teléfono corporativo, horarios de apertura y cierre, y estado operativo).
3. Salvaguardar la integridad del inventario, ventas, reservas activas y empleados asociados ante intentos de desactivación o eliminación de sucursales y ciudades.

---

## 2. Alcance y Trazabilidad Documental

1. **Documento Maestro de Requisitos:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md) (Sección 1.2.2 Objetivo 2, Sección 1.4 Alcance, Sección 2.1.1.1 Administrador, Sección 2.1.1.2 CU21, Sección 2.1.3 CU21 Líneas 807-823).
2. **Esquema Relacional DDL:** `fashionstore.ciudades` y `fashionstore.sucursales` definidos en `0001_base_ddl.py`.
3. **Referencias de Arquitectura y Dominio:**
   - [references/arquitectura.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-backend-sdd/references/arquitectura.md) (Paquete Gestión Operativa: `RouterSucursal`, `ServicioGestionSucursal`, `SucursalORM`, `CiudadORM`).
   - [references/dominio.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-backend-sdd/references/dominio.md) (Invariantes de sucursales, unicidad `UNIQUE(id_ciudad, nombre)` y relaciones foráneas).
   - [references/fashionstore-tokens.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md) (Design System multi-plataforma: potencias de 2 Base-2, tipografía Outfit, paleta Slate/Camel/Obsidian).

---

## 3. Requisitos del Sistema (Notación EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema deberá exigir autenticación JWT válida con rol `administrador` para cualquier operación de creación, actualización, desactivación o eliminación en los endpoints administrativos de ciudades (`/api/v1/admin/ciudades`) y sucursales (`/api/v1/admin/sucursales`).

- **# AC-2 (Por Evento - Creación de Ciudad):**  
  Cuando el administrador envíe una solicitud de registro de ciudad con nombre y país, el sistema deberá validar que el nombre no exista previamente en `fashionstore.ciudades` (insensible a mayúsculas/minúsculas y tildes), persistir el registro con marca de tiempo UTC y responder con código HTTP `201 Created`.

- **# AC-3 (Conducta No Deseada - Ciudad Duplicada):**  
  Si el nombre de la ciudad ya se encuentra registrado en el sistema, entonces el sistema deberá rechazar la solicitud, abortar la transacción y responder con código HTTP `409 Conflict` indicando el código de dominio `CIUDAD_DUPLICADA`.

- **# AC-4 (Por Evento - Creación de Sucursal con Invariantes de Negocio):**  
  Cuando el administrador registre una nueva sucursal vinculada a una ciudad existente, el sistema deberá verificar:
  1. Que la ciudad especificada exista y esté activa.
  2. Que la combinación `(id_ciudad, nombre)` sea única en el sistema.
  3. Que `horario_cierre` sea cronológicamente posterior a `horario_apertura`.
  4. Que la dirección no esté vacía y el teléfono cumpla el formato telefónico válido.  
  Cumplidas las validaciones, el sistema deberá persistir la sucursal con `activa = true` y responder con código HTTP `201 Created`.

- **# AC-5 (Conducta No Deseada - Horarios Inconsistentes o Datos Inválidos en Sucursal):**  
  Si el `horario_cierre` es menor o igual al `horario_apertura`, o si los datos obligatorios presentan formato erróneo, entonces el sistema deberá responder con código HTTP `422 Unprocessable Entity` con el detalle descriptivo del campo observado.

- **# AC-6 (Por Estado - Protección de Integridad en Baja de Ciudad):**  
  Mientras una ciudad tenga sucursales físicas asociadas (`fashionstore.sucursales`) o clientes con esa ciudad asignada como preferida (`fashionstore.clientes`), si el administrador intenta eliminar la ciudad, entonces el sistema deberá bloquear la eliminación y responder con código HTTP `409 Conflict` bajo el código de error `CIUDAD_CON_DEPENDENCIAS_ACTIVAS`.

- **# AC-7 (Por Estado - Baja Lógica y Restricción de Integridad en Desactivación de Sucursal):**  
  Mientras una sucursal posea reservas activas pendientes de atención (`estado_reserva IN ('pendiente', 'confirmada', 'en_atencion')`) o mantenga inventario físico con stock disponible (`cantidad_disponible > 0`), si el administrador solicita desactivar la sucursal (`activa = false`), entonces el sistema deberá rechazar la desactivación inmediata y responder con código HTTP `409 Conflict` (`SUCURSAL_CON_OPERACIONES_PENDIENTES`), requiriendo la previa atención/cancelación de reservas o el traslado del inventario.

- **# AC-8 (Por Evento - Consulta Pública y Filtrado de Sucursales):**  
  Cuando un cliente, visitante anónimo o empleado solicite el listado de sucursales a través del endpoint `/api/v1/sucursales`, el sistema deberá retornar únicamente aquellas sucursales con `activa = true`, agrupadas o filtrables por ciudad, incluyendo nombre de boutique, dirección, teléfono de contacto y horarios de atención.

- **# AC-9 (Por Evento - Consulta Administrativa Consolidada):**  
  Cuando el administrador consulte el catálogo de sucursales desde `/api/v1/admin/sucursales`, el sistema deberá retornar el listado íntegro (activas e inactivas) enriquecido con el nombre de la ciudad asociada, el total de empleados asignados y el indicador de existencias globales de la sede.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- **# AC-10 (Ubicuo - Arquitectura y Principios de Diseño Web):**  
  El módulo web de gestión de sucursales y ciudades deberá construirse mediante componentes 100% Standalone (`standalone: true`), con estrategia de detección de cambios `ChangeDetectionStrategy.OnPush`, gestión de estado reactivo mediante **Angular Signals** (`signal()`, `computed()`), inyección con `inject()`, enrutamiento protegido bajo `authGuard` y `roleGuard` (exclusivo `administrador`), y maquetación alojada dentro del contenedor institucional `max-w-[1440px] px-6` con `scrollbar-gutter: stable`.

- **# AC-11 (Ubicuo - Sistema de Tokens y Estilo Normativo):**  
  La interfaz deberá emplear rigurosamente los tokens Base-2 de FashionStore (`space-1` a `space-7`), tipografía institucional **Outfit** (`font-sans font-semibold tracking-tight`), paleta Slate/Camel/Obsidian (`primary-900`, `secondary-500`, `surface-container-lowest`), sin clases arbitrarias en corchetes (`p-[10px]` prohibido).

- **# AC-12 (Por Evento - Interfaz de Gestión con Tabs y Tablas Editoriales):**  
  Cuando el administrador acceda a `/admin/sucursales`, el sistema deberá presentar una vista editorial con dos pestañas de trabajo:
  1. **Boutiques & Sucursales:** Tabla con filtro reactivo por ciudad, buscador por nombre/dirección, tarjetas de boutique con insignia de estado (`ACTIVA` en verde esmeralda / `INACTIVA` en tono slate), horario y botón de acción rápida para editar o alternar estado.
  2. **Ciudades Operativas:** Panel lateral o sub-vista para añadir ciudades y visualizar el conteo de boutiques por ciudad.

- **# AC-13 (Por Evento - Formulario Reactivo y Modales de Alta/Edición):**  
  Cuando el administrador pulse `+ NUEVA BOUTIQUE` o `EDITAR`, el sistema deberá desplegar un modal o drawer lateral construido con `FormGroup` fuertemente tipado (`NonNullableFormBuilder`), que permita seleccionar la ciudad mediante dropdown reactivo, ingresar nombre, dirección, teléfono y selectores de hora (`HH:mm`), aplicando validación en vivo que impida confirmar si el horario de cierre no supera al de apertura.

- **# AC-14 (Conducta No Deseada - Notificación Visual de Restricciones):**  
  Si el backend responde con un código de conflicto `409` (ej. intento de desactivar sucursal con reservas o stock cautivo), entonces el componente web deberá capturar el error y desplegar un Luxury Banner o Toast de advertencia con el mensaje explicativo sin cerrar el formulario ni perder los datos digitados.

---

### Bloque C: Aplicación Móvil (`Ec-mobile` - Flutter 3.x + BLoC)

- **# AC-15 (Ubicuo - Arquitectura Feature-First y BLoC Inmutable):**  
  El módulo móvil de administración territorial deberá implementarse bajo la estructura estricta:
  `lib/src/features/gestion_operativa/cu21_sucursales_ciudades/` conteniendo:
  - `datos/`: Modelos DTO (`CiudadModelo`, `SucursalModelo`), datasources HTTP y repositorios.
  - `dominio/`: Entidades inmutables (`Ciudad`, `Sucursal`) y casos de uso.
  - `presentacion/`: `SucursalesBloc` con estados sellados inmutables (`SucursalesInicial`, `SucursalesCargando`, `SucursalesCargado`, `SucursalesError`), widgets atómicos y pantalla principal.

- **# AC-16 (Ubicuo - Tokens Centralizados y Estándar de Interfaz Móvil):**  
  Todas las pantallas y widgets deberán consumir exclusivamente los tokens de `AppTheme` (`AppSpacing`, `AppColors`, `AppTypography`, `AppRadius`), garantizando widgets sin estado con constructores `const`, uso de `Flexible`/`Expanded` para prevenir `RenderFlex overflow`, almacenamiento seguro de tokens en `flutter_secure_storage` y visualización de los 4 estados de pantalla (Inicial, Shimmer de carga, Éxito y Luxury SnackBar ante errores).

- **# AC-17 (Por Evento - Vista de Supervisión Móvil de Boutiques):**  
  Cuando el administrador ingrese a la sección de administración de sucursales en la aplicación móvil, el sistema deberá desplegar un selector horizontal de ciudades en chips de lujo, un listado de tarjetas de boutiques con monograma editorial, dirección, horario de atención y un switch interactivo de activación/desactivación que solicite diálogo de confirmación antes de impactar el backend.

- **# AC-18 (Por Evento - Alta y Edición Ágil en BottomSheet):**  
  Cuando el administrador pulse el botón de acción flotante `+` en la pantalla móvil, el sistema deberá abrir un Modal BottomSheet adaptado a pantalla táctil, con campos validados para ciudad, nombre, dirección y horarios, enviando la solicitud mediante `SucursalesBloc` y actualizando el listado en tiempo real tras la confirmación exitosa.

---

## 4. Matriz de Errores y Excepciones de Dominio

| Código HTTP | Código Dominio | Condición Disparadora | Mensaje al Usuario |
|---|---|---|---|
| `400 Bad Request` | `DATOS_INVALIDOS` | Payload JSON malformado o campos con tipos incorrectos | "Los datos ingresados no cumplen con el formato requerido." |
| `401 Unauthorized` | `NO_AUTENTICADO` | Token JWT ausente, expirado o revocado en lista negra | "Sesión no válida o expirada. Por favor, inicie sesión nuevamente." |
| `403 Forbidden` | `ACCESO_DENEGADO` | El usuario autenticado no posee el rol `administrador` | "Acceso restringido: se requieren permisos de administrador corporativo." |
| `404 Not Found` | `SUCURSAL_NO_ENCONTRADA` | El identificador de sucursal (`id_sucursal`) no existe | "La sucursal solicitada no se encuentra registrada." |
| `404 Not Found` | `CIUDAD_NO_ENCONTRADA` | El identificador de ciudad (`id_ciudad`) no existe | "La ciudad seleccionada no existe en el catálogo territorial." |
| `409 Conflict` | `CIUDAD_DUPLICADA` | Se intenta crear una ciudad con nombre ya existente | "Ya existe una ciudad registrada con el nombre especificado." |
| `409 Conflict` | `SUCURSAL_DUPLICADA` | Ya existe una sucursal con el mismo nombre en esa ciudad | "Ya existe una boutique con este nombre registrada en la misma ciudad." |
| `409 Conflict` | `CIUDAD_CON_DEPENDENCIAS_ACTIVAS` | Intento de borrado de ciudad con sucursales o clientes asociados | "No se puede eliminar la ciudad porque cuenta con sucursales o clientes asignados." |
| `409 Conflict` | `SUCURSAL_CON_OPERACIONES_PENDIENTES` | Desactivación de sucursal con reservas pendientes o stock disponible | "No se puede desactivar la sucursal: mantiene reservas activas o inventario en custodia." |
| `422 Unprocessable` | `HORARIO_INVALIDO` | `horario_cierre <= horario_apertura` | "El horario de cierre debe ser posterior a la hora de apertura." |

---

## 5. Fuera de Alcance (Out of Scope para CU21)

1. **Gestión de Stock Físico:** La asignación, traslado o recuento de prendas dentro de la sucursal corresponde a `CU26` (Inventario Global) y `movimientos_inventario`.
2. **Asignación de Personal:** La vinculación de cajeros y encargados a las sucursales creadas se gestiona en `CU20` (Gestionar Usuarios y Roles).
3. **Puntos de Venta (Cajas Físicas):** La apertura de terminales de cobro POS corresponde a `CU31` y `CU32`.
4. **Geolocalización GPS Dinámica / Mapas Satelitales en Vivo:** En esta fase se gestionan coordenadas y direcciones textuales normalizadas; la integración con Google Maps SDK queda fuera del alcance del MVP de CU21.

---

## 6. Decisiones Técnicas y Preguntas para Revisión Humana

1. **Eliminación Física vs. Baja Lógica Exclusiva:**  
   Dado que `fashionstore.sucursales` es clave foránea en múltiples tablas históricas (`ventas`, `reservas`, `inventario_sucursal`, `usuarios`), se propone que la eliminación física (`DELETE`) solo sea admisible si la sucursal nunca registró movimientos transaccionales. Si ya tiene historial, el sistema aplicará obligatoriamente **baja lógica** (`activa = false`).
2. **Formato de Horarios:**  
   Se estandariza el formato en ISO TIME `HH:mm` (24 horas, e.g. `"09:00"`, `"20:00"`), compatible nativamente con la columna `TIME` de PostgreSQL y los selectores nativos de Angular y Flutter.
