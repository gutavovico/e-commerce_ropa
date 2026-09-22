# Plan de Tareas y Oleadas de Implementacion: CU24 - Gestionar Inventario, Stock y Existencias por Sucursal

**ID del Caso de Uso:** CU24  
**Nombre:** Gestionar Inventario, Stock y Existencias por Sucursal  
**Paquete Arquitectonico:** `gestion_operativa` / `inventario`  
**Modulo Backend:** `app/modules/gestion_operativa/cu24_inventario_stock`  
**Modulo Frontend Web:** `src/app/modules/gestion_operativa/cu24_inventario_stock`  
**Referencias:** `.specs/changes/CU24/spec.md` y `.specs/changes/CU24/design.md`  
**Estado:** Completado y Promovido (Definicion de Terminado - DoD Cumplida)  

---

## 1. Estrategia General de Implementacion

El caso de uso CU24 implementa el subsistema de **Gestion de Inventario, Stock Fisico y Auditoria por Sucursal** en FashionStore. Provee control atomico de saldos, politicas de umbrales seguros (`stock_minimo`, `stock_alerta`), transferencias inter-sucursales transaccionales ACID y trazabilidad inmutable mediante un libro de movimientos tipo Kardex.

### 1.1 Exclusion Formal Ratificada de la Aplicacion Movil (Ec-mobile)
Se ratifica de manera formal e irrevocable la exclusion tecnica de desarrollo en `Ec-mobile`. La aplicacion movil en Flutter 3.x esta concebida exclusivamente para el cliente de vitrina B2C y consulta de disponibilidad de piezas. Las tareas de recepcion de mercaderia, ajustes manuales por merma, transferencias entre sucursales y auditoria contable de kardex son exclusivas del panel de administracion web (`Ec-frontend`). Por tanto, no se contemplan tareas para la plataforma movil en este plan.

### 1.2 Secuenciacion de Oleadas
El plan de tareas se estructura en tres (3) oleadas de ejecucion estrictamente secuenciales:
1. **Oleada 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon):**
   Modelos ORM con constraints de no negatividad y unicidad, DTOs Pydantic v2, jerarquia de excepciones semanticas, servicio transaccional con bloqueos ACID y doble kardex, endpoints administrativos y publicos protegidos por RBAC, y suite de pruebas automatizadas Pytest al 100% en verde.
2. **Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone):**
   Contratos DTO en TypeScript, servicio `InventarioAdminService` con Angular Signals, integracion de la 5ta tarjeta boutique en `AdminDashboardComponent` visible para administrador y encargado, componente `InventarioAdminComponent` con estetica editorial Atelier, selector de sede bloqueado para encargados, tabla maestra con indicadores de umbral, modales reactivos (`NonNullableFormBuilder`), panel de Kardex, Luxury Banners y suite de pruebas unitarias Vitest al 100% en verde.
3. **Oleada 3: Cierre, Verificacion Cruzada Integral y DoD:**
   Revalidacion cruzada de ambas suites automatizadas (`pytest`, `ng test`, `ng build`, `audit_emojis.py`), promocion formal hacia baseline permanente en `.specs/finalized/CU24/` y `.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md`, actualizacion formal de `CHANGELOG.md` (version 2.0.0) y limpieza del directorio temporal.

---

## 2. Desglose Detallado de Tareas por Oleada

### Oleada 1: Backend (Ec-backend - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

- [x] **Tarea 1.1: Verificacion y mapeo de modelos ORM en esquema fashionstore (InventarioSucursalORM y MovimientoInventarioORM)**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/modelos.py`
    - `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/__init__.py`
  - **Descripcion:**
    * Declarar los tipos enumerados de PostgreSQL `estado_prenda_stock` ('disponible', 'reservada', 'vendida', 'agotada', 'proxima_ingreso', 'devuelta') y `tipo_movimiento_inv` ('ingreso_proveedor', 'ajuste_positivo', 'ajuste_negativo', 'transferencia_salida', 'transferencia_entrada', 'venta_confirmada', 'cancelacion_pedido').
    * Modelar `InventarioSucursalORM` en `fashionstore.inventario_sucursal`:
      - `id_inventario`: BigInteger primary key autoincremental.
      - `id_sucursal`: Integer FK a `fashionstore.sucursales.id_sucursal` no nulo e indexado.
      - `id_variante`: BigInteger FK a `fashionstore.variantes_producto.id_variante` no nulo e indexado.
      - `id_temporada`: Integer FK a `fashionstore.temporadas.id_temporada` no nulo con default 1.
      - `cantidad_disponible`: Integer no nulo con default 0 y `CheckConstraint('cantidad_disponible >= 0')`.
      - `cantidad_reservada`: Integer no nulo con default 0 y `CheckConstraint('cantidad_reservada >= 0')`.
      - `stock_minimo`: Integer no nulo con default 0 y `CheckConstraint('stock_minimo >= 0')`.
      - `stock_alerta`: Integer no nulo con default 5 y `CheckConstraint('stock_alerta >= 0')`.
      - `estado`: Enumeracion `estado_prenda_stock` indexada.
      - `actualizado_en`: DateTime UTC con `onupdate`.
      - Restriccion de unicidad compuesta: `UniqueConstraint('id_sucursal', 'id_variante', name='uq_inventario_sucursal_variante')`.
      - Relaciones lazy='joined' hacia `SucursalORM` y `VarianteProductoORM`.
    * Modelar `MovimientoInventarioORM` en `fashionstore.movimientos_inventario`:
      - `id_movimiento`: BigInteger primary key autoincremental.
      - `id_inventario`: BigInteger FK a `fashionstore.inventario_sucursal.id_inventario` no nulo e indexado.
      - `tipo_movimiento`: Enumeracion `tipo_movimiento_inv` indexada.
      - `cantidad`: Integer no nulo con `CheckConstraint('cantidad <> 0')`.
      - `saldo_anterior`: Integer no nulo con default 0.
      - `saldo_nuevo`: Integer no nulo con default 0.
      - `motivo`: Text no nulo.
      - `id_usuario`: BigInteger FK a `fashionstore.usuarios.id_usuario` nullable e indexado.
      - `referencia_documento`: String(100) nullable.
      - `creado_en`: DateTime UTC no nulo con valor por defecto now.
      - Relaciones hacia `InventarioSucursalORM` y `UsuarioORM`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-5`, `# AC-6`, `# AC-8`, `# AC-11`.
  - **Verificacion:** Inspeccion de metadatos de SQLAlchemy 2.0 y compatibilidad DDL con PostgreSQL Neon.

- [x] **Tarea 1.2: DTOs Pydantic v2 y funciones utilitarias de validacion**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/esquemas.py`
  - **Descripcion:**
    * Declarar enumeraciones Pydantic: `TipoMovimientoEnum`, `EstadoStockCalculadoEnum` ('optimo', 'alerta_baja', 'agotado'), `TipoAjusteManualEnum` ('incremento', 'decremento').
    * `InventarioCrearIn`: campos `id_sucursal`, `id_variante`, `id_temporada`, `cantidad_inicial` (>= 0), `stock_minimo`, `stock_alerta`, `referencia_documento`, `observacion`.
    * `InventarioAjusteIn`: campos `tipo_ajuste`, `cantidad` (> 0), `motivo` (con `@field_validator` que exige `len(saneado) >= 5`), `referencia_documento`.
    * `TransferenciaInterSucursalIn`: campos `id_sucursal_origen`, `id_sucursal_destino`, `id_variante`, `cantidad` (> 0), `motivo`, con `@model_validator(mode="after")` que exige `id_sucursal_origen != id_sucursal_destino`.
    * `InventarioFiltrosIn`: parametros query `id_sucursal`, `id_categoria`, `estado_stock`, `q`, `pagina` y `limite`.
    * `InventarioItemOut`, `ListaPaginadaInventarioOut`, `KardexItemOut`, `HistorialKardexOut`, `ComprobanteTransferenciaOut` y `DisponibilidadPublicaOut`.
  - **Criterios Mapeados:** `# AC-3`, `# AC-4`, `# AC-7`, `# AC-10`, `# AC-12`, `# AC-15`.
  - **Verificacion:** Pruebas de serializacion/deserializacion y validacion sintactica en Pydantic v2.

- [x] **Tarea 1.3: Jerarquia de excepciones semanticas de dominio**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/errores.py`
  - **Descripcion:**
    * Crear la jerarquia de excepciones heredando de `AppError`:
      - `InventarioError`: base general (500).
      - `InventarioNoEncontradoError`: status 404, codigo `INVENTARIO_NO_ENCONTRADO`.
      - `InventarioDuplicadoError`: status 409, codigo `INVENTARIO_DUPLICADO`.
      - `StockInsuficienteError`: status 409, codigo `STOCK_INSUFICIENTE`.
      - `AutoTransferenciaError`: status 422, codigo `TRANSFERENCIA_MISMA_SUCURSAL`.
      - `MotivoInvalidoError`: status 422, codigo `MOTIVO_OPERACION_INVALIDO`.
      - `SucursalNoAutorizadaError`: status 403, codigo `SUCURSAL_NO_AUTORIZADA`.
      - `EntidadInactivaError`: status 422, codigo `ENTIDAD_INACTIVA_PARA_INVENTARIO`.
  - **Criterios Mapeados:** `# AC-2`, `# AC-6`, `# AC-7`, `# AC-9`, `# AC-10`, `# AC-12`, `# AC-13`.
  - **Verificacion:** Pruebas unitarias de instanciacion confirmando status HTTP y codigos semanticos.

- [x] **Tarea 1.4: Servicio transaccional ServicioGestionInventario con bloqueos ACID y doble kardex**
  - **Archivo:** `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/servicio.py`
  - **Descripcion:**
    * `_calcular_estado_stock`: funcion determinista que computa `optimo`, `alerta_baja` o `agotado` comparando disponible vs `stock_alerta`.
    * `_validar_acceso_sucursal`: si `usuario_sesion.rol == 'encargado_sucursal'`, verificar que `id_sucursal_solicitada == usuario_sesion.id_sucursal`, lanzando `SucursalNoAutorizadaError` en caso contrario.
    * `listar_inventario`: forzar filtrado de sede para encargados, aplicar joins optimizados con prendas, categorias y sucursales, filtrar por `q`, categoria y estado computado, calculando paginacion.
    * `crear_inventario_inicial`: comprobar sucursal y variante activas, validar no duplicidad, persistir `InventarioSucursalORM` y generar el primer movimiento en `movimientos_inventario` (`ingreso_proveedor`).
    * `ajustar_inventario`: validar permisos, conmutar saldo positivo o negativo (bloqueando con `StockInsuficienteError` si el decremento supera el disponible), actualizar timestamp y asentar movimiento en Kardex con saldos anterior y nuevo.
    * `transferir_mercaderia`: validar sedes distintas y activas, aplicar `with_for_update()` en inventario de origen, verificar stock suficiente, deducir disponible en origen, acreditar en destino (creando registro si no existia) e insertar los dos movimientos espejo en Kardex (`transferencia_salida` y `transferencia_entrada`) en la misma transaccion atomica.
    * `obtener_kardex`: consultar el historial cronologico descendente de movimientos de una variante en una sede.
    * `consultar_disponibilidad_publica`: consulta abierta de tiendas fisicas activas con stock para una variante.
  - **Criterios Mapeados:** `# AC-2` al `# AC-14`.
  - **Verificacion:** Pruebas unitarias con mocks de base de datos testeando transacciones, bloqueos y excepciones.

- [x] **Tarea 1.5: Router REST administrativo /api/v1/admin/inventario y router publico de disponibilidad**
  - **Archivos:**
    - `Ec-backend/app/modules/gestion_operativa/cu24_inventario_stock/router.py`
    - `Ec-backend/app/modules/gestion_operativa/router.py`
    - `Ec-backend/app/main.py`
  - **Descripcion:**
    * Declarar `router_admin` con prefijo `/admin/inventario` y dependencias `require_roles(["administrador", "encargado_sucursal"])`:
      - `GET /api/v1/admin/inventario`: Consulta paginada con filtros.
      - `POST /api/v1/admin/inventario`: Alta de stock inicial (HTTP 201).
      - `POST /api/v1/admin/inventario/{id}/ajuste`: Ajuste manual fisico (HTTP 200).
      - `POST /api/v1/admin/inventario/transferencia`: Traspaso inter-sucursales (HTTP 200).
      - `GET /api/v1/admin/inventario/{id}/kardex`: Bitacora de movimientos (HTTP 200).
    * Declarar `router_publico` con prefijo `/inventario`:
      - `GET /api/v1/inventario/disponibilidad/{id_variante}`: Consulta de tiendas con existencias (HTTP 200).
    * Integrar routers en el agregador `app/modules/gestion_operativa/router.py` y montar en `app/main.py`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-3`, `# AC-5`, `# AC-8`, `# AC-11`, `# AC-14`, `# AC-15`.
  - **Verificacion:** Inspeccion de endpoints en OpenAPI docs (`/docs`).

- [x] **Tarea 1.6: Suite de pruebas automatizadas en test_cu24_inventario_stock.py al 100% en verde**
  - **Archivo:** `Ec-backend/tests/modules/gestion_operativa/test_cu24_inventario_stock.py`
  - **Descripcion:**
    * Desarrollar pruebas unitarias y de integracion con `TestClient` cubriendo:
      - Seguridad RBAC: rechazo 401 si no hay token; rechazo 403 para cajero/cliente; acceso para administrador y encargado (`# AC-1`).
      - Segregacion territorial forzosa: rechazo 403 cuando un encargado intenta consultar o mutar otra sucursal (`# AC-2`).
      - Consulta paginada y filtros combinados (`# AC-3`, `# AC-4`).
      - Registro exitoso de stock inicial con kardex de entrada (`# AC-5`).
      - Rechazo 409 ante duplicidad de inventario (`# AC-6`).
      - Rechazo 422 ante sucursal o variante inactiva (`# AC-7`).
      - Ajuste manual positivo y negativo con trazabilidad de kardex (`# AC-8`).
      - Rechazo 409 si el ajuste reduce el stock por debajo de cero (`# AC-9`).
      - Rechazo 422 si el motivo de ajuste es vacio o menor a 5 caracteres (`# AC-10`).
      - Transferencia inter-sucursal atomica con doble asiento en kardex (`# AC-11`).
      - Rechazo 422 ante auto-transferencia (`# AC-12`).
      - Rechazo 409 ante saldo insuficiente en origen para transferencias (`# AC-13`).
      - Consulta de historial de movimientos de kardex (`# AC-14`).
      - Consulta publica de disponibilidad (`# AC-15`).
  - **Criterios Mapeados:** `# AC-1` al `# AC-15`.
  - **Verificacion:** Ejecucion de `pytest` en `Ec-backend` certificando que la suite completa pase al 100% sin fallos.

---

### Oleada 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript en inventario.dto.ts**
  - **Archivo:** `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/modelos/inventario.dto.ts`
  - **Descripcion:**
    * Definir tipos literales union: `EstadoStockCalculado = 'optimo' | 'alerta_baja' | 'agotado'` y `TipoAjusteManual = 'incremento' | 'decremento'`.
    * Modelar interfaces estrictas sin `any`:
      - `DatosVarianteInventario`, `DatosSucursalInventario`.
      - `ItemInventarioAdmin`: entidad de inventario enriquecida con datos de producto, SKU, color #HEX, talla y estado computado.
      - `InventarioCrearPayload`: datos para alta inicial.
      - `InventarioAjustePayload`: datos para ajuste de existencias.
      - `TransferenciaInterSucursalPayload`: datos para traspaso inter-sedes.
      - `KardexItem` e `HistorialKardex`: estructura de la bitacora auditable.
      - `ParametrosFiltroInventario` y `ListaPaginadaInventario`.
  - **Criterio Mapeado:** `# AC-17`.
  - **Verificacion:** Compilacion limpia con `npx tsc --noEmit`.

- [x] **Tarea 2.2: Servicio HTTP reactivo InventarioAdminService con Angular Signals**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/servicios/inventario-admin.service.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/servicios/inventario-admin.service.spec.ts`
  - **Descripcion:**
    * Inyectar `HttpClient` y `LoginService`, configurando el endpoint `/api/v1/admin/inventario`.
    * Declarar Signals de estado reactivo: `inventario`, `totalRegistros`, `paginaActual`, `totalPaginas`, `cargando`, `guardando`, `kardexActual`, `error`, `mensajeExito`, `filtros`.
    * Metodos reactivos con cabeceras Bearer JWT: `cargarInventario(filtros)`, `crearStockInicial(payload)`, `ajustarStock(id, payload)`, `transferirMercaderia(payload)`, `cargarKardex(id)` y `limpiarMensajes()`.
  - **Criterios Mapeados:** `# AC-17`, `# AC-25`.
  - **Verificacion:** Pruebas unitarias en `inventario-admin.service.spec.ts` con `provideHttpClientTesting()`.

- [x] **Tarea 2.3: Actualizacion de AdminDashboardComponent y visibilidad RBAC de la 5ta tarjeta**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Adaptar la rejilla del dashboard central para soportar de manera balanceada 5 tarjetas boutique.
    * Incorporar la 5ta tarjeta boutique corporativa:
      - Titulo: "Inventario y Stock"
      - Categoria: "Logistica y Existencias"
      - Descripcion: "Monitoreo de existencias fisicas, control de mermas, reposicion y traspasos entre sedes."
      - Badge: "Control de Stock"
      - Boton: "Gestionar Inventario", con identificador `id="btn-gestionar-inventario"`, `routerLink="/admin/inventario"` y `(click)="navegar('/admin/inventario')"`.
    * Segmentacion RBAC dinamica:
      - La tarjeta de inventario debe ser plenamente visible tanto para `administrador` como para `encargado_sucursal`.
      - Actualizar computed signals de modulos activos en el dashboard.
  - **Criterio Mapeado:** `# AC-16`.
  - **Verificacion:** Pruebas en `admin-dashboard.component.spec.ts` verificando que un `administrador` y un `encargado_sucursal` visualicen el boton de inventario.

- [x] **Tarea 2.4: Componente Standalone InventarioAdminComponent y proteccion de ruta con roleGuard**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.scss`
    - `Ec-frontend/src/app/app.routes.ts`
  - **Descripcion:**
    * Crear `InventarioAdminComponent` con `ChangeDetectionStrategy.OnPush` y layout editorial Atelier `max-w-[1440px] px-6 py-8 mx-auto`.
    * Incorporar el boton superior institucional `"<- Volver al Panel Principal"` con enlace a `/admin`.
    * Registrar la ruta protegida `/admin/inventario` en `app.routes.ts` custodiada por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
  - **Criterios Mapeados:** `# AC-17`, `# AC-18`.
  - **Verificacion:** Pruebas de enrutamiento y guard verificando acceso concedido a ambos roles y bloqueo ante clientes.

- [x] **Tarea 2.5: Barra de filtros interactiva con fijacion de sede y tabla maestra con indicadores de umbral**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.ts`
  - **Descripcion:**
    * Desarrollar barra de filtros reactiva con Angular Signals:
      - Input de busqueda `q` con `debounceTime(300)` para SKU y prenda.
      - Selector reactivo de sucursales alimentado por `SucursalesAdminService`: si el usuario es `encargado_sucursal`, fijar el valor en su sede y deshabilitar el selector (`disabled = true`); si es `administrador`, permitir conmutar entre sedes.
      - Selector de categorias alimentado por `AtributosAdminService` (CU23).
      - Selector de estado de existencias (`Todos`, `Optimo`, `Alerta de Reposicion`, `Agotados`).
    * Disenar tabla maestra editorial:
      - Miniatura de prenda cuadrada con bordes redondeados (`rounded-xl`, 52x52px).
      - Prenda, SKU corporativo, talla y swatch visual `#HEX` del color.
      - Sede asignada.
      - Columnas de saldo: `cantidad_disponible` destacada y `cantidad_reservada` en tono neutro.
      - Badges cromaticos de estado: `Optimo` (Verde Esmeralda), `Alerta de Reposicion` (Ambar pulsante), `Agotado` (Rojo Carmesi).
      - Botones de accion: "Ajustar", "Transferir" (deshabilitado si disponible == 0) y "Kardex".
  - **Criterios Mapeados:** `# AC-19`, `# AC-20`.
  - **Verificacion:** Renderizado sobrio sin emojis, estados de carga y feedback responsivo.

- [x] **Tarea 2.6: Modales reactivos con NonNullableFormBuilder, panel de Kardex, Luxury Banners y pruebas unitarias**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.html`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.ts`
    - `Ec-frontend/src/app/modules/gestion_operativa/cu24_inventario_stock/paginas/inventario-admin.component.spec.ts`
  - **Descripcion:**
    * Modal de Alta Inicial (`+ INGRESAR MERCADERIA`): seleccion de producto, variante, sucursal (fijada para encargados), cantidad inicial y umbrales.
    * Modal de Ajuste Fisico: seleccion de incremento/decremento, cantidad (validada contra stock disponible) y textarea con justificacion obligatoria (minimo 5 caracteres).
    * Modal de Transferencia: dropdown de sede destino excluyendo la sede de origen, cantidad limitada al maximo disponible y motivo del traslado.
    * Panel o Modal de Kardex: tabla cronologica descendente mostrando variacion (+/-), saldos anterior y nuevo, y colaborador responsable.
    * Luxury Banners: captura de errores HTTP 409 y 422 preservando los datos del formulario sin recargas forzadas.
    * Pruebas unitarias en `inventario-admin.component.spec.ts` cubriendo inicializacion, filtrado reactivo, apertura de modales, envio de formularios, bloqueo de sede para encargados y Luxury Banners.
  - **Criterios Mapeados:** `# AC-21` al `# AC-25`.
  - **Verificacion:** Ejecucion de `ng test --watch=false` certificando 100% en verde y `ng build` con 0 errores.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada integral de suites locales**
  - **Descripcion:**
    * Ejecutar suite de backend con `pytest` en `Ec-backend` asegurando 200+ tests en verde (100% de la suite acumulada).
    * Ejecutar suite de frontend con `ng test --watch=false` en `Ec-frontend` asegurando 160+ tests en verde.
    * Ejecutar compilacion productiva de Angular con `ng build` certificando 0 errores de tipo o plantilla.
    * Ejecutar `audit_emojis.py` garantizando la ausencia total de emojis en todo el repositorio.
  - **Verificacion:** Consolas limpias, 100% verde en ambas plataformas.

- [x] **Tarea 3.2: Promocion formal de artefactos hacia baseline permanente**
  - **Descripcion:**
    * Copiar y promover los artefactos aprobados desde `.specs/changes/CU24/` hacia `.specs/finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`).
    * Consolidar la especificacion permanente en `.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md`.
    * Limpiar los archivos temporales de `.specs/changes/CU24/`.
  - **Verificacion:** Archivos archivados con enlaces cruzados y estructura sincronizada.

- [x] **Tarea 3.3: Registro formal de version en CHANGELOG.md y actualizacion de trazabilidad**
  - **Descripcion:**
    * Documentar formalmente la version `[2.0.0] - 2026-09-21` en `CHANGELOG.md` y `.specs/CHANGELOG.md`.
    * Resumir la introduccion de la gestion de inventario por sucursal, libro de movimientos Kardex, transferencias inter-sucursales atomicas, integracion de tarjeta en dashboard y exclusion justificada de Ec-mobile.
  - **Verificacion:** Trazabilidad completa con SI2-Parcial1.md y estado final limpio.
