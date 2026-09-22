# Especificacion Formal de Requisitos: CU24 - Gestionar Inventario, Stock y Existencias por Sucursal

**ID del Caso de Uso:** CU24  
**Nombre:** Gestionar Inventario, Stock y Existencias por Sucursal  
**Paquete Arquitectonico:** `gestion_operativa` / `inventario`  
**Modulo Backend:** `app/modules/gestion_operativa/cu24_inventario_stock`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu24_inventario_stock`  
**Actores Principales:**  
- **Administrador:** Control total, global y transversal de inventario sobre todas las boutiques, almacenes y sedes comerciales de la cadena.  
- **Encargado de Sucursal:** Control operativo y de existencias acotado estrictamente a la boutique fisica que tiene asignada.  
**Actores Secundarios (Consulta / Consumo Pasivo):**  
- **Cajero:** Consulta de stock disponible en la sede propia para despacho y venta presencial en Punto de Venta (POS).  
- **Cliente:** Consulta de disponibilidad de prendas en tiendas fisicas a traves del catalogo web y movil.  
- **Sistema:** Validacion y reserva automatica de inventario en procesos de checkout digital y reservas en probador virtual.  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Riesgo Alto: Consistencia transaccional de stock fisico, prevencion de sobreventa y auditoria contable de mercaderia)  
**Estado:** En Revision de Requisitos (Fase 1 - EARS)  

---

## 1. Proposito y Contexto de Negocio

En la cadena omnicanal de alta costura **FashionStore**, la comercializacion de prendas exclusivas requiere una gestion precisa y en tiempo real de las existencias fisicas distribuidas a lo largo de su red de boutiques metropolitanas (CU21). Cada prenda de diseno se manifiesta fisicamente en el punto de venta a traves de sus variantes comerciales (SKUs de CU22), compuestas por una combinatoria rigurosa de modelo, talla y color textil (CU23).

El inventario de una boutique no es una cifra estatica; constituye una entidad dinamica sujeta a recepcion de lotes de confeccion, ventas presenciales en caja, despachos digitales para pedidos con retiro en tienda, retencion por reservas en probador virtual (AR) y movimientos internos de mercaderia entre diferentes plazas comerciales.

El caso de uso **CU24 - Gestionar Inventario, Stock y Existencias por Sucursal** proporciona la infraestructura operativa, transaccional y de gobernanza para:
1. Parametrizar y registrar las existencias fisicas (`cantidad_disponible` y `cantidad_reservada`) de cada variante (SKU) por boutique.
2. Definir umbrales de operacion segura mediante politicas de `stock_minimo` y `stock_alerta`, activando senalizadores visuales de reposicion inmediata.
3. Registrar de forma inmutable, transaccional y auditable todo movimiento de inventario (Kardex: entradas por proveedor, salidas, mermas por defecto textil o ajuste fisico de inventario, y traspasos entre sucursales), vinculando al usuario responsable y el motivo operativo.
4. Ejecutar transferencias inter-sucursales garantizando la consistencia ACID (descuento atomico en la sucursal de origen y acreditacion sincronizada en la sucursal de destino).
5. Garantizar la segregacion de privilegios mediante Control de Acceso Basado en Roles (RBAC): mientras el administrador supervisa y gestiona la red completa de boutiques, el encargado de sucursal opera exclusivamente el inventario de su sede asignada.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Tecnica y Funcional de la Exclusion
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta orientada a los canales de cara al cliente final y la experiencia de piso de boutique:
- Navegacion del catalogo editorial, probador virtual mediante Realidad Aumentada (AR), reservas de citas de prueba y compras moviles directas.
- Consulta agil y liviana de disponibilidad de tallas y colores por sucursal cercana.

Las tareas de gobernanza de existencias, recepcion formal de mercaderia con comprobantes de entrega, ejecucion de ajustes por mermas fisicas, transferencias masivas entre boutiques y auditoria de kardex son procesos netamente corporativos y de trastienda operativa. Estas actividades requieren interfaces de alta densidad de datos, monitores de escritorio, reportes comparativos y controles de seguridad administrativos que residen exclusivamente en el panel web (`Ec-frontend`).

### 2.2 Consumo en Modo Solo Lectura (Read-Only)
La aplicacion movil participa en el dominio de inventario unicamente como consultor pasivo de disponibilidad (`Read-Only`), accediendo a traves de endpoints publicos de consulta (ej. `GET /api/v1/productos/{id}/disponibilidad`) para informar al cliente final si una prenda especifica dispone de existencias para retiro o prueba en la tienda fisica de su eleccion.

Por consiguiente, el caso de uso CU24 **queda formalmente excluido de desarrollo e implementacion en Ec-mobile**. No se crearan pantallas de gestion de inventario, formularios de ajuste, controladores BLoC ni repositorios mutables en la aplicacion movil, concentrando el desarrollo en `Ec-backend` y `Ec-frontend`.

---

## 3. Alcance y Trazabilidad Documental

1. **Documento Maestro de Requisitos:** [SI2-Parcial1.md](file:///c:/Users/tonyv/.gemini/antigravity-ide/scratch/e-commerce_ropa/SI2-Parcial1.md)
   - Seccion 1.2.2 Objetivo 1: "Desarrollar una plataforma inteligente de comercio electronico omnicanal que integre gestion de sucursales, inventario y puntos de venta".
   - Seccion 1.4 Alcance - Seguridad y Auditoria: "Registro trazable de movimientos de stock, auditoria de inventarios y control de mermas".
   - Seccion 2.1.2 CU26 Lineas 897-915 y 2795: "Consultar y Gestionar Inventario Global: permitir al administrador y encargados supervisar las existencias por tienda y mantener la consistencia operativa".
   - Seccion 2.3 Modelo de Base de Datos relacional: Tablas `fashionstore.inventario_sucursal` y `fashionstore.movimientos_inventario`.
2. **Esquema Relacional DDL (PostgreSQL / Alembic):**
   - Tabla `fashionstore.inventario_sucursal`:
     * `id_inventario` (BIGSERIAL PRIMARY KEY).
     * `id_variante` (BIGINT NOT NULL REFERENCES `fashionstore.variantes_producto(id_variante)`).
     * `id_sucursal` (INTEGER NOT NULL REFERENCES `fashionstore.sucursales(id_sucursal)`).
     * `id_temporada` (INTEGER NOT NULL REFERENCES `fashionstore.temporadas(id_temporada)`).
     * `cantidad_disponible` (INTEGER NOT NULL DEFAULT 0, CHECK `cantidad_disponible >= 0`).
     * `cantidad_reservada` (INTEGER NOT NULL DEFAULT 0, CHECK `cantidad_reservada >= 0`).
     * `stock_minimo` (INTEGER NOT NULL DEFAULT 0, CHECK `stock_minimo >= 0`).
     * `stock_alerta` (INTEGER NOT NULL DEFAULT 5, CHECK `stock_alerta >= 0`).
     * `estado` (ENUM `disponible`, `reservada`, `agotada`, `proxima_ingreso`).
     * `actualizado_en` (TIMESTAMPTZ NOT NULL DEFAULT now()).
     * Restriccion `UNIQUE (id_variante, id_sucursal, id_temporada)`.
   - Tabla `fashionstore.movimientos_inventario`:
     * `id_movimiento` (BIGSERIAL PRIMARY KEY).
     * `id_inventario` (BIGINT NOT NULL REFERENCES `fashionstore.inventario_sucursal(id_inventario)`).
     * `tipo_movimiento` (ENUM `ingreso_proveedor`, `reserva`, `liberacion_reserva`, `venta`, `devolucion`, `ajuste`, `transferencia_salida`, `transferencia_entrada`).
     * `cantidad` (INTEGER NOT NULL CHECK `cantidad <> 0`).
     * `id_usuario_responsable` (BIGINT REFERENCES `fashionstore.usuarios(id_usuario)`).
     * `referencia_documento` (VARCHAR(100)).
     * `observacion` (TEXT).
     * `creado_en` (TIMESTAMPTZ NOT NULL DEFAULT now()).
3. **Referencias de Dominio y Diseno:**
   - `.agents/skills/fashionstore-backend-sdd/references/dominio.md`: Invariantes de inventario por sucursal, kardex y reglas de transaccion.
   - `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md`: Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals.

---

## 4. Requisitos del Sistema (Notacion EARS)

### Bloque A: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

#### Control de Acceso y Segregacion RBAC
- **# AC-1 (Ubicuo - Seguridad y Control de Acceso RBAC):**  
  El sistema debera exigir autenticacion JWT valida con rol `administrador` o `encargado_sucursal` para acceder a los endpoints administrativos de inventario bajo `/api/v1/admin/inventario`.
  * Si el usuario no presenta token o este es invalido, el sistema rechazara la peticion con HTTP 401 Unauthorized.
  * Si el usuario autenticado posee rol `cajero` o `cliente`, el sistema rechazara el acceso con HTTP 403 Forbidden.

- **# AC-2 (Ubicuo - Segregacion Territorial de Inventario por Rol):**  
  El sistema debera aplicar un filtro forzoso de alcance territorial basado en los claims del usuario autenticado:
  * Si el usuario tiene rol `administrador`, podra consultar, inicializar, ajustar y transferir inventario de cualquier sucursal del sistema.
  * Si el usuario tiene rol `encargado_sucursal`, el sistema forzara de manera estricta que todas las consultas y mutaciones operen exclusivamente sobre su `id_sucursal` asignada en su perfil institucional. Cualquier intento explicito de consultar o alterar el inventario de otra sucursal sera bloqueado con HTTP 403 Forbidden (`ACCESO_A_SUCURSAL_NO_AUTORIZADO`).

#### Consulta y Filtros de Inventario Consolidado
- **# AC-3 (Por Evento - Listado Paginado de Existencias por Sucursal):**  
  Cuando un usuario autorizado solicite consultar el inventario mediante `GET /api/v1/admin/inventario`, el sistema debera retornar una coleccion paginada de registros que incluya:
  * Identificador de inventario (`id_inventario`).
  * Datos de la sucursal (`id_sucursal`, `nombre_sucursal`, `ciudad`).
  * Datos de la prenda y variante (`id_producto`, `nombre_prenda`, `id_variante`, `sku`, `talla`, `color_nombre`, `color_hex`, `precio_final`, `imagen_url`).
  * Cantidades fisicas: `cantidad_disponible`, `cantidad_reservada` y stock total (`cantidad_disponible + cantidad_reservada`).
  * Umbrales operativos: `stock_minimo`, `stock_alerta`.
  * Estado computado de stock: `disponible`, `alerta_baja`, `agotado`.
  * Fecha de ultima actualizacion (`actualizado_en`).
  * Metadatos de paginacion: `total_items`, `pagina_actual`, `total_paginas`, `limite`.

- **# AC-4 (Opcional - Filtros Multicriterio de Inventario):**  
  Donde se especifiquen parametros opcionales de busqueda en la consulta de inventario:
  * `id_sucursal`: Filtrar estrictamente por la sede indicada (restringido a la propia para encargados).
  * `id_categoria`: Filtrar por el identificador de la categoria taxonomica de la prenda o sus subcategorias.
  * `estado_stock`: Filtrar por clasificacion de disponibilidad (`todos`, `disponible`, `alerta_baja`, `agotado`).
  * `q`: Busqueda textual con operador `ILIKE` sobre el nombre de la prenda, el codigo `sku` o el nombre del color.  
  El sistema debera aplicar los filtros combinados mediante conjuncion logica (`AND`).

#### Asignacion Inicial y Recepcion de Mercaderia
- **# AC-5 (Por Evento - Registro de Stock Inicial para Variante en Sucursal):**  
  Cuando el usuario solicite registrar stock inicial para una variante en una sucursal mediante `POST /api/v1/admin/inventario`, especificando `id_sucursal`, `id_variante`, `id_temporada`, `cantidad_inicial` (Entero >= 0), `stock_minimo` (Entero >= 0) y `stock_alerta` (Entero >= 0), el sistema debera:
  * Validar que la sucursal exista y tenga `activa = True`.
  * Validar que la variante de producto exista y su prenda base tenga `activo = True`.
  * Validar que la temporada exista y se encuentre vigente o activa.
  * Comprobar que no exista previamente un registro de inventario para la combinacion `(id_variante, id_sucursal, id_temporada)`.
  * Persistir la entidad `InventarioSucursalORM` con `cantidad_disponible = cantidad_inicial` y `cantidad_reservada = 0`.
  * Generar automaticamente un registro en `movimientos_inventario` con `tipo_movimiento = 'ingreso_proveedor'`, `cantidad = cantidad_inicial`, `id_usuario_responsable` del usuario en sesion y observacion `"Carga inicial de inventario"`.
  * Responder con HTTP 201 Created y el detalle del inventario registrado.

- **# AC-6 (Invariante - Rechazo de Duplicidad de Inventario):**  
  Si se intenta registrar un inventario inicial para una combinacion `(id_variante, id_sucursal, id_temporada)` que ya existe en la base de datos, el sistema debera rechazar la operacion con HTTP 409 Conflict (`INVENTARIO_YA_EXISTENTE`), instruyendo al usuario a utilizar la operacion de ajuste o reabastecimiento.

- **# AC-7 (Invariante - Validacion de Entidades Activas en Inventario):**  
  Si en una operacion de inventario se indica una sucursal inactiva o una variante perteneciente a una prenda desactivada (`activo = False`), el sistema debera rechazar la transaccion con HTTP 422 Unprocessable Entity (`ENTIDAD_INACTIVA_PARA_INVENTARIO`).

#### Ajustes Fisicos de Inventario (Entradas, Salidas y Mermas)
- **# AC-8 (Por Evento - Ajuste Manual de Existencias):**  
  Cuando el usuario solicite ajustar las existencias de un inventario existente mediante `POST /api/v1/admin/inventario/{id_inventario}/ajuste`, especificando `tipo_ajuste` (`incremento` o `decremento`), `cantidad` (Entero > 0), `motivo` (Texto obligatorio no vacio de minimo 5 caracteres) y opcionalmente `referencia_documento`, el sistema debera ejecutar de manera atomica:
  * Si es `incremento`: Adicionar la cantidad a `cantidad_disponible`.
  * Si es `decremento`: Deducir la cantidad de `cantidad_disponible`.
  * Actualizar el campo `actualizado_en` con la marca temporal actual.
  * Registrar un movimiento inmutable en `movimientos_inventario` con `tipo_movimiento = 'ajuste'`, la cantidad con su respectivo signo algebraico (+ o -), el `id_usuario_responsable` del usuario autenticado, la observacion con el motivo y la referencia documental.
  * Retornar HTTP 200 OK con el nuevo balance de inventario.

- **# AC-9 (Invariante - Proteccion de Saldo No Negativo en Ajustes):**  
  Si un ajuste de tipo `decremento` pretende deducir una cantidad superior a la `cantidad_disponible` actual del inventario, el sistema debera abortar la transaccion y rechazar la solicitud con HTTP 409 Conflict (`STOCK_INSUFICIENTE_PARA_AJUSTE`), impidiendo en todo momento saldos negativos.

- **# AC-10 (Invariante - Obligatoriedad de Justificacion en Ajustes):**  
  Si el payload de un ajuste manual omite el campo `motivo` o este contiene menos de 5 caracteres significativos, el sistema debera rechazar la solicitud con HTTP 422 Unprocessable Entity (`MOTIVO_AJUSTE_REQUERIDO`).

#### Transferencias Inter-Sucursales
- **# AC-11 (Por Evento - Transferencia de Mercaderia entre Sucursales):**  
  Cuando un usuario autorizado solicite transferir mercaderia mediante `POST /api/v1/admin/inventario/transferir`, especificando `id_sucursal_origen`, `id_sucursal_destino`, `id_variante`, `id_temporada`, `cantidad` (Entero > 0) y `motivo`, el sistema debera ejecutar de forma atomica bajo una sola transaccion de base de datos:
  * Validar que la sucursal de origen y la de destino sean distintas (`id_sucursal_origen != id_sucursal_destino`).
  * Validar que ambas sucursales existan y esten activas.
  * Si el usuario es `encargado_sucursal`, validar que `id_sucursal_origen == usuario.id_sucursal`.
  * Comprobar que en la sucursal origen exista inventario para la variante con `cantidad_disponible >= cantidad`.
  * Descontar `cantidad` de `cantidad_disponible` en el inventario origen.
  * Localizar o crear el registro de inventario en la sucursal destino para la variante y temporada, adicionando `cantidad` a su `cantidad_disponible`.
  * Insertar dos registros de auditoria en `movimientos_inventario`:
    1. Para el inventario origen: `tipo_movimiento = 'transferencia_salida'`, cantidad negativa (`-cantidad`), referencia `"Hacia sucursal [id_destino]"`.
    2. Para el inventario destino: `tipo_movimiento = 'transferencia_entrada'`, cantidad positiva (`+cantidad`), referencia `"Desde sucursal [id_origen]"`.
  * Confirmar la transaccion (commit) y responder con HTTP 200 OK y el comprobante del traspaso.

- **# AC-12 (Invariante - Rechazo de Auto-Transferencia):**  
  Si se solicita una transferencia donde `id_sucursal_origen == id_sucursal_destino`, el sistema debera rechazar la solicitud con HTTP 422 Unprocessable Entity (`TRANSFERENCIA_MISMA_SUCURSAL_NO_PERMITIDA`).

- **# AC-13 (Invariante - Stock Insuficiente en Origen para Transferencias):**  
  Si la cantidad a transferir excede la `cantidad_disponible` en la boutique de origen, el sistema debera abortar la transaccion con HTTP 409 Conflict (`STOCK_ORIGEN_INSUFICIENTE`).

#### Kardex y Auditoria de Movimientos
- **# AC-14 (Por Evento - Consulta del Historial de Movimientos / Kardex):**  
  Cuando el usuario solicite consultar el historial de movimientos mediante `GET /api/v1/admin/inventario/{id_inventario}/movimientos`, el sistema debera retornar la lista cronologica descendente de transacciones asociadas, conteniendo: `id_movimiento`, `tipo_movimiento`, `cantidad`, `fecha`, `observacion`, `referencia_documento` y el nombre completo del colaborador responsable (`id_usuario_responsable`).

#### Endpoint Publico de Disponibilidad para Clientes
- **# AC-15 (Por Evento - Consulta Abierta de Disponibilidad por Prenda y Sucursal):**  
  Cuando cualquier cliente o aplicacion consulte `GET /api/v1/inventario/disponibilidad?id_producto={id}&id_ciudad={id_ciudad}`, el sistema debera retornar sin requerir autenticacion la matriz consolidada de sucursales activas en dicha ciudad que poseen existencias disponibles (`cantidad_disponible > 0`) para cada una de las variantes de la prenda consultada.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en Dashboard Central
- **# AC-16 (Ubicuo - Tarjeta Boutique en AdminDashboardComponent):**  
  El panel central `/admin` debera incorporar una tarjeta boutique dedicada:
  * Titulo: "Inventario y Stock"
  * Categoria: "Logistica y Existencias"
  * Descripcion: "Monitoreo de existencias fisicas, control de mermas, reposicion y traspasos entre sedes."
  * Badge: "Control Operativo"
  * Boton de accion: "Gestionar Inventario", con identificador `id="btn-gestionar-inventario"`, `routerLink="/admin/inventario"` y `(click)="navegar('/admin/inventario')"`.
  * Visibilidad RBAC: La tarjeta debera ser visible tanto para usuarios con rol `administrador` como para `encargado_sucursal`.

#### Enrutamiento Protegido y Layout Institucional
- **# AC-17 (Ubicuo - Vista Standalone y Proteccion de Ruta):**  
  El modulo de inventario debera implementarse en `InventarioAdminComponent` como componente Standalone con `ChangeDetectionStrategy.OnPush`, montado en la ruta protegida `/admin/inventario` bajo los guards `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
  * La vista debera enmarcarse en el contenedor institucional `max-w-[1440px] px-6 py-8 mx-auto`.
  * En la parte superior izquierda debera presentar el boton editorial `"<- Volver al Panel Principal"` con enlace a `/admin`.

#### Barra de Filtros Reactiva y Segmentacion de Encargado
- **# AC-18 (Ubicuo - Barra de Filtros Multicriterio):**  
  La vista debera proporcionar una barra interactiva de control reactivo con Angular Signals:
  * **Selector de Sucursal:** Dropdown alimentado reactivamente por `SucursalesAdminService`. Si el usuario autenticado es `encargado_sucursal`, el selector debera quedar fijado en su sucursal y bloqueado (`disabled`) para impedir la consulta de sedes ajenas. Si es `administrador`, mostrara la opcion "Todas las sucursales" y cada una de las boutiques activas.
  * **Selector de Categoria:** Dropdown alimentado por `AtributosAdminService` (CU23).
  * **Selector de Estado de Stock:** Opciones `Todos los estados`, `Solo Disponibles`, `Alerta de Stock Bajo`, `Agotados`.
  * **Campo de Busqueda `q`:** Input reactivo con `debounceTime(300)` para filtrado en vivo por nombre de prenda o SKU.

#### Tabla Maestra de Existencias e Indicadores Visuales
- **# AC-19 (Ubicuo - Tabla Maestra Editorial con Indicadores de Alerta):**  
  La tabla maestra debera presentar:
  * Miniatura visual de la prenda (52x52px, `rounded-xl`, `border-slate-200`) o placeholder editorial sobrio con iniciales.
  * Informacion de la prenda y variante: nombre del modelo, SKU corporativo normalizado, talla y muestra visual cromatica swatch (#HEX).
  * Boutique fisica asignada o badge de sede.
  * Balance de existencias: columna destacada con `cantidad_disponible` y detalle sutil de `cantidad_reservada`.
  * **Insignia Visual de Estado de Stock:**
    - `Optimo` (Verde Esmeralda / Slate): cuando `cantidad_disponible > stock_alerta`.
    - `Alerta de Reposicion` (Ambar / Camel con indicador pulsante): cuando `cantidad_disponible <= stock_alerta` y `cantidad_disponible > 0`.
    - `Agotado` (Rojo Carmesi / Slate-200): cuando `cantidad_disponible == 0`.
  * Columna de Acciones: Boton "Ajustar", Boton "Transferir" (solo disponible si hay existencias) y Boton "Kardex".

#### Modales Reactivos y Validaciones Sincronas
- **# AC-20 (Por Evento - Modal de Asignacion Inicial / Recepcion de Mercaderia):**  
  Cuando el usuario pulse el boton institucional `"+ INGRESAR MERCADERIA"`, el sistema debera desplegar un modal reactivo gestionado con `NonNullableFormBuilder` que permita seleccionar la prenda, la variante (talla y color), la sucursal (fijada para encargados), la cantidad a ingresar, el stock minimo y el umbral de alerta.

- **# AC-21 (Por Evento - Modal de Ajuste de Inventario con Justificacion):**  
  Al pulsar "Ajustar" sobre una fila de la tabla, se abrira un modal contextual que visualice la prenda, sucursal y stock actual, solicitando:
  * Tipo de operacion: `Ingreso / Sobrante (+)` o `Salida / Merma (-)`.
  * Cantidad a ajustar (con validacion para no superar el disponible en caso de merma).
  * Motivo justificado obligatorio (textarea con validador de longitud minima de 5 caracteres).
  * Campo opcional de numero de acta o remision.

- **# AC-22 (Por Evento - Modal de Transferencia Inter-Sucursal):**  
  Al pulsar "Transferir", se abrira un modal que muestre la sucursal origen y la variante seleccionada, solicitando:
  * Sucursal destino: Dropdown de boutiques activas excluyendo automaticamente la sucursal de origen.
  * Cantidad a transferir: Input numerico acotado con validacion reactiva al maximo disponible en origen (`1 <= cantidad <= cantidad_disponible`).
  * Motivo del traslado (ej. "Rebalanceo de coleccion", "Demanda en boutique destino").

- **# AC-23 (Por Evento - Panel Lateral o Modal de Historial Kardex):**  
  Al pulsar "Kardex", la aplicacion desplegara un panel o modal con la cronologia de movimientos del SKU en esa boutique, indicando tipo de movimiento, variacion de unidades, fecha/hora y colaborador responsable.

#### Experiencia de Usuario y Manejo No Destructivo de Errores
- **# AC-24 (Ubicuo - Luxury Banners ante Conflictos 409 y 422):**  
  Ante cualquier rechazo del backend por saldo insuficiente (409) o error de validacion territorial (422), la interfaz debera presentar de inmediato un Luxury Banner contextual de alerta sin cerrar el modal y preservando intactos los valores digitados por el usuario.

- **# AC-25 (Ubicuo - Tipado TypeScript Estricto y Estado Reactivo con Signals):**  
  La logica de comunicacion y estado debera residir en `InventarioAdminService`, gobernada al 100% por Angular Signals (`inventario: Signal<ItemInventarioAdmin[]>`, `totalItems`, `cargando`, `guardando`, `error`, `mensajeExito`), consumiendo DTOs fuertemente tipados definidos en `inventario.dto.ts` sin recurrir a tipos `any`.

---

## 5. Matriz de Trazabilidad y Casos de Prueba

| Criterio EARS | Requisito / Escenario | Componente Backend | Componente Frontend | Verificacion Automatizada |
|---|---|---|---|---|
| **# AC-1** | Seguridad RBAC (`admin` y `encargado_sucursal`) | `require_roles(["administrador", "encargado_sucursal"])` | `roleGuard` en `app.routes.ts` | Pytest `test_cu24_seguridad_rbac` / Vitest `role.guard.spec` |
| **# AC-2** | Segregacion territorial forzosa para encargados | Inyeccion de `admin_sesion.id_sucursal` en servicio | Selector de sede deshabilitado/fijo | Pytest `test_cu24_segregacion_encargado` / Vitest `inventario-admin.component.spec` |
| **# AC-3** | Listado paginado de existencias por sucursal | `ServicioGestionInventario.listar_inventario` | Tabla maestra con Signals | Pytest `test_cu24_listar_inventario_paginado` / Vitest `inventario-admin.service.spec` |
| **# AC-4** | Filtros multicriterio (sucursal, categoria, estado, q) | Parametros query y clausulas `where()` dinámicas | Barra de filtros con `debounce` | Pytest `test_cu24_filtros_combinados` / Vitest `inventario-admin.component.spec` |
| **# AC-5** | Registro de stock inicial con kardex de entrada | `ServicioGestionInventario.crear_inventario_inicial` | Modal `FormularioIngresoMercaderia` | Pytest `test_cu24_alta_inventario_inicial` / Vitest `inventario-admin.component.spec` |
| **# AC-6** | Rechazo HTTP 409 ante duplicidad de inventario | `InventarioYaExisteError` | Luxury Banner de conflicto 409 | Pytest `test_cu24_duplicado_409` |
| **# AC-7** | Rechazo HTTP 422 ante sucursal o variante inactiva | `EntidadInactivaError` | Validacion previa y Luxury Banner | Pytest `test_cu24_entidad_inactiva_422` |
| **# AC-8** | Ajuste manual (incremento/decremento) con kardex | `ServicioGestionInventario.ajustar_inventario` | Modal de ajuste contextual | Pytest `test_cu24_ajuste_exitoso` / Vitest `inventario-admin.component.spec` |
| **# AC-9** | Rechazo HTTP 409 ante decremento que supere stock | `StockInsuficienteError` | Validacion síncrona y banner 409 | Pytest `test_cu24_saldo_negativo_409` |
| **# AC-10** | Rechazo HTTP 422 por motivo de ajuste ausente o corto | Pydantic `@field_validator("motivo")` | Validador `Validators.minLength(5)` | Pytest `test_cu24_motivo_invalido_422` |
| **# AC-11** | Transferencia inter-sucursales atomica ACID | `ServicioGestionInventario.transferir_mercaderia` | Modal de transferencia | Pytest `test_cu24_transferencia_atomica` / Vitest `inventario-admin.component.spec` |
| **# AC-12** | Rechazo HTTP 422 si origen y destino son la misma sede | `TransferenciaMismaSedeError` | Exclusion de sede origen en select | Pytest `test_cu24_auto_transferencia_422` |
| **# AC-13** | Rechazo HTTP 409 si stock origen es insuficiente | `StockInsuficienteError` | Validacion `max(disponible)` en form | Pytest `test_cu24_transferencia_sin_stock_409` |
| **# AC-14** | Consulta de historial de movimientos (Kardex) | `ServicioGestionInventario.listar_movimientos` | Modal/Panel Kardex cronologico | Pytest `test_cu24_kardex_movimientos` |
| **# AC-15** | Endpoint publico de disponibilidad por tienda | `RouterInventarioPublico.get_disponibilidad` | Consumo por catalogo cliente | Pytest `test_cu24_disponibilidad_publica` |
| **# AC-16** | Tarjeta en AdminDashboard para admin y encargado | N/A | `AdminDashboardComponent` | Vitest `admin-dashboard.component.spec` |
| **# AC-17** | Vista administrativa y proteccion de rutas | N/A | `InventarioAdminComponent` | Vitest `inventario-admin.component.spec` |
| **# AC-18** | Boton superior editorial de retorno | N/A | Boton `"<- Volver al Panel Principal"` | Vitest `inventario-admin.component.spec` |
| **# AC-19** | Insignias visuales de umbral (Optimo, Alerta, Agotado)| N/A | Badges cromaticos en tabla | Vitest `inventario-admin.component.spec` |
| **# AC-20** | Selector fijado y bloqueado para encargado_sucursal | N/A | Control reactivo con `esEncargado()` | Vitest `inventario-admin.component.spec` |
| **# AC-21** | Modal de ajuste con justificacion obligatoria | N/A | `NonNullableFormBuilder` | Vitest `inventario-admin.component.spec` |
| **# AC-22** | Modal de transferencia con selectores dinamicos | N/A | Dropdown excluyente de destino | Vitest `inventario-admin.component.spec` |
| **# AC-23** | Modal de kardex historico | N/A | Tabla de movimientos en modal | Vitest `inventario-admin.component.spec` |
| **# AC-24** | Luxury Banners ante errores 409 y 422 | N/A | Banners preservando formulario | Vitest `inventario-admin.component.spec` |
| **# AC-25** | Tipado TypeScript estricto y Angular Signals | N/A | `inventario.dto.ts` y Service | Compilacion limpia `ng build` (0 errores) |
