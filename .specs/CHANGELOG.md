# Changelog Técnico de Arquitectura y SDD — FashionStore

Ver documento principal en [../../CHANGELOG.md](../../CHANGELOG.md).

## [2.1.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU25 - Gestionar Proveedores (Cadena de Abastecimiento y Talleres Textiles):** Promovido oficialmente a especificacion permanente del sistema en [`modules/gestion_operativa/CU25-gestionar-proveedores.md`](modules/gestion_operativa/CU25-gestionar-proveedores.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU25/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `changes/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La gestion societaria, contratos de confeccion mayorista, captura de datos tributarios (NIT/RUT) y evaluacion de talleres textiles corresponden a labores exclusivas de trastienda y back-office corporativo web (`Ec-frontend`). La app movil B2C queda formalmente excluida sin pantallas ni modelos mutables.
- **Validacion Completa:**
  - Backend: 224/224 tests en verde en `pytest` para toda la suite acumulada (16/16 especificos de CU25); modelo ORM en esquema `fashionstore` (`ProveedorORM`), revision DDL Alembic `0006_cu25_proveedores_extension.py` en PostgreSQL Neon; restricciones de unicidad estricta sobre `nit_rut` y `razon_social` (insensible a mayusculas); esquemas Pydantic v2 con validadores de sanitizacion obligatoria y correo valido; excepciones semanticas de dominio (`ProveedorNoEncontradoError`, `ProveedorDuplicadoError`, `ProveedorInvalidoError`); servicio de dominio con soporte multicriterio paginado, prevencion de colisiones 409 y baja logica (`estado_activo = False`) preservando integridad historica referencial; y endpoints REST bajo `/api/v1/admin/proveedores` protegidos por roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 192/192 tests en verde en Vitest / Angular CLI (13/13 en `proveedores-admin.component.spec.ts`, 9/9 en `proveedores-admin.service.spec.ts`, 11/11 en `admin-dashboard.component.spec.ts`); sexta tarjeta boutique en `AdminDashboardComponent` ("Proveedores y Fabricantes") dentro de "Gestion de Abastecimiento" con badge "Cadena de Suministro" y control RBAC dinamico (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `ProveedoresAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals; boton superior editorial `"<- Volver al Panel Principal"` con `routerLink="/admin"`; barra reactiva de filtros con busqueda textual con debounce de 300 ms, selector de estado y selector de rubro textil; tabla maestra editorial con NIT/RUT, contacto comercial, ciudad e insignias cromadas de estado (verde esmeralda / slate); modales reactivos con `NonNullableFormBuilder` (Alta, Edicion y Confirmacion de Baja Logica con advertencia de cese de recepcion sin perdida de historico); y Luxury Banners para captura contextual no destructiva de errores HTTP 409 y 422 preservando los datos del formulario.

### Registro de Errores Corregidos y Soluciones Aplicadas
41. **Prevencion de Duplicidad Tributaria y Societaria Multicapa (`uq_proveedores_nit_rut` y `uq_proveedores_razon_social`)**:
    - *Causa:* La duplicidad inadvertida de registros de un mismo taller textil bajo leves variaciones de razon social o reutilizacion de NIT generaba inconsistencias fiscales y distorsionaba la auditoria de abastecimiento.
    - *Solucion:* Validacion previa en capa de servicio con consultas normalizadas y creacion de indices unicos `uq_proveedores_nit_rut` y `uq_proveedores_razon_social` (con funcion `LOWER()` en PostgreSQL Neon), emitiendo de forma determinista la excepcion HTTP 409 Conflict.
42. **Trazabilidad e Inmutabilidad Historica mediante Baja Logica (`estado_activo = False`)**:
    - *Causa:* La eliminacion fisica de un proveedor con prendas asociadas en catalogo o recepciones historicas de kardex rompia la integridad referencial de base de datos o dejaba registros huerfanos.
    - *Solucion:* Politica estricta de baja logica mediante el flag `estado_activo = False` que cesa inmediatamente la habilitacion para nuevos pedidos pero conserva la totalidad del historico comercial y documental.
43. **Captura No Destructiva de Conflictos y Debounce Asincrono en Formularios Reactivos**:
    - *Causa:* La emision de errores de validacion o colision tributaria solia reiniciar los formularios o generar parpadeos en busquedas continuas.
    - *Solucion:* Implementacion de retardo *debounce* de 300 ms en el input de busqueda conectado a Signals y contencion no destructiva en Luxury Banners mediante captura en `errorBanner`, preservando integro el estado de los controles en `formCrear` y `formEditar`.

## [2.0.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU24 - Gestionar Inventario, Stock y Existencias por Sucursal (Logistica y Existencias Fisicas):** Promovido oficialmente a especificacion permanente del sistema en [`modules/gestion_operativa/CU24-gestionar-inventario-stock.md`](modules/gestion_operativa/CU24-gestionar-inventario-stock.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `changes/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La recepcion de lotes de confeccion, registro de mermas fisicas, transferencias masivas entre boutiques y auditoria contable de kardex son funciones operativas de trastienda y back-office corporativo que residen exclusivamente en el panel web de administracion. La aplicacion movil participa en calidad de consultor pasivo de existencias (`Read-Only`) mediante el endpoint publico `/api/v1/inventario/disponibilidad/{id_variante}`.
- **Validacion Completa:**
  - Backend: 208/208 tests en verde en `pytest` para toda la suite acumulada (17/17 especificos de CU24); modelos ORM en esquema `fashionstore` (`InventarioSucursalORM` y `MovimientoInventarioORM`), migracion Alembic `0005_cu24_inventario_kardex.py` ejecutada en PostgreSQL Neon; restriccion de unicidad compuesta `uq_inventario_sucursal_variante` y `CheckConstraint` de no negatividad (`cantidad_disponible >= 0`); libro de movimientos Kardex inmutable; transaccionalidad ACID con bloqueo exclusivo `with_for_update()` en transferencias inter-sucursales; computo determinista de semaforos de stock (`optimo`, `alerta_baja`, `agotado`); segregacion territorial forzada para rol `encargado_sucursal` bloqueando con HTTP 403 accesos a sedes ajenas; endpoints administrativos bajo `/api/v1/admin/inventario` y vitrina publica `/api/v1/inventario/disponibilidad/{id_variante}`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 168/168 tests en verde en Vitest / Angular CLI (12/12 en `inventario-admin.component.spec.ts`, 9/9 en `inventario-admin.service.spec.ts`, 10/10 en `admin-dashboard.component.spec.ts`); quinta tarjeta boutique en `AdminDashboardComponent` ("Inventario y Existencias") con segmentacion dinamica RBAC (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `InventarioAdminComponent` con `ChangeDetectionStrategy.OnPush` y Signals; barra reactiva de filtros con selector de sucursal fijado y deshabilitado para encargados de boutique; tabla maestra editorial con swatches `#HEX`, miniatura con fallback SVG, desglose de cantidades y badges cromados de umbral; modales reactivos con `NonNullableFormBuilder` (Alta inicial, Ajuste fisico con motivo obligatorio min. 5 caracteres y control de stock, Transferencia inter-sedes excluyendo sede origen y con tope en disponible); panel de Kardex cronologico descendente con variaciones (+/-); y Luxury Banners para captura contextual de errores HTTP 409 y 422.

### Registro de Errores Corregidos y Soluciones Aplicadas
38. **Bloqueo Pesimista ACID y Doble Asiento en Transferencias Inter-Sucursales (`with_for_update`)**:
    - *Causa:* En transferencias concurrentes entre boutiques, la lectura no sincronizada del saldo en origen podia ocasionar condiciones de carrera y saldos negativos de inventario.
    - *Solucion:* Bloqueo pesimista mediante `with_for_update()` sobre la fila del inventario de origen dentro de una unica transaccion atomica, deduciendo el saldo disponible, acreditando en la sede destino (o creando el registro si no existia) e insertando los dos asientos simetricos de Kardex (`transferencia_salida` y `transferencia_entrada`).
39. **Segregacion Territorial Obligatoria y Proteccion RBAC Multinivel**:
    - *Causa:* Personal con rol `encargado_sucursal` podria intentar consultar o mutar existencias de otras tiendas comerciales si el frontend no aplicara restricciones o el backend confiara en los parametros query del cliente.
    - *Solucion:* Sobreescritura forzada del parametro de sucursal en el backend validando contra `usuario_sesion.id_sucursal` (HTTP 403 si discrepa), complementada en el frontend mediante bloqueo y deshabilitacion reactiva del selector de sucursal para encargados.
40. **Control Reactivo de Umbrales y Validacion de Motivo Obligatorio en Ajustes**:
    - *Causa:* Ajustes manuales por merma o rotura sin justificacion auditable o con cantidades superiores al stock disponible comprometian la fidelidad contable y violaban constraints de base de datos.
    - *Solucion:* Validacion Pydantic v2 en `InventarioAjusteIn` exigiendo minimo 5 caracteres no vacios en el motivo, verificacion en servicio de que decrementos no superen `cantidad_disponible` (HTTP 409 `STOCK_INSUFICIENTE`), y reflejo reactivo en interfaz mediante validadores reactivos y Luxury Banners sin perdida de datos.

## [1.9.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU20 - Gestionar Usuarios y Roles (RBAC) (Gobernanza Corporativa y Control de Accesos):** Promovido oficialmente a especificacion permanente del sistema en [`modules/autenticacion_seguridad/CU20-gestionar-usuarios-roles.md`](modules/autenticacion_seguridad/CU20-gestionar-usuarios-roles.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU20/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `changes/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada formalmente la exclusion de la aplicacion movil (`Ec-mobile`). La gobernanza de cuentas corporativas, creacion de accesos para colaboradores, reseteo administrativo de claves y asignacion de roles RBAC constituyen facultades exclusivas de trastienda y administracion general ejecutadas en el panel web. La aplicacion movil Flutter participa estrictamente como plataforma comercial de cara al cliente final (autenticacion, perfil, catalogo, pedidos y vestidor AR).
- **Validacion Completa:**
  - Backend: 186/186 tests en verde en `pytest` para toda la suite acumulada (24/24 especificos de CU20); modelo ORM en esquema `fashionstore` (`UsuarioORM`) con soporte exhaustivo para 4 roles ('administrador', 'encargado_sucursal', 'cajero', 'cliente'), clave foranea nullable `id_sucursal` indexada con relacion `joinedload` hacia `fashionstore.sucursales`, esquemas Pydantic v2 con `@model_validator` para validacion condicional territorial (sucursal obligatoria para roles operativos de boutique y forzada a `None` para administrador y cliente), hashing criptografico robusto con Argon2/bcrypt (`get_password_hash()`), servicio de dominio con salvaguarda transaccional anti-bloqueo del ultimo administrador activo (`ULTIMO_ADMINISTRADOR_ACTIVO`), proteccion anti auto-bloqueo del administrador en sesion (`AUTO_MODIFICACION_ADMIN_BLOQUEADA`), bloqueo HTTP 409 con forzado a baja logica (`activo = False`) ante intentos de borrado fisico con transacciones dependientes (`USUARIO_CON_DEPENDENCIAS_ACTIVAS`), y router administrativo bajo `/api/v1/admin/usuarios` blindado con dependencia `require_roles(["administrador"])`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 143/143 tests en verde en Vitest / Angular CLI (10/10 en `usuarios-admin.component.spec.ts`, 7/7 en `usuarios-admin.service.spec.ts`, 7/7 en `admin-dashboard.component.spec.ts`, 4/4 en `role.guard.spec.ts`); componente Standalone `UsuariosAdminComponent` con `ChangeDetectionStrategy.OnPush`, estado reactivo 100% gobernado por Angular Signals (`usuarios`, `totalUsuarios`, `usuarioSeleccionado`, `cargando`, `guardando`, `error`, `mensajeExito`), actualizacion de `AdminDashboardComponent` a cuatro columnas (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`) incorporando la 4ta tarjeta boutique "Usuarios y Privilegios", segmentacion dinamica RBAC (ocultamiento reactivo estricto de CU20 y CU21 cuando el rol es `encargado_sucursal`), boton superior editorial `"<- Volver al Panel Principal"` con `routerLink="/admin"`, tabla maestra con monogramas circulares, badges cromaticos de rol y estado, conmutador directo de activacion/suspension, modal reactivo de alta/edicion con `NonNullableFormBuilder` y reactividad condicional de sucursal, modal de reseteo de contrasena, guard funcional `roleGuard(['administrador'])` para blindaje de rutas y captura de conflictos 409 y 422 con Luxury Banners preservando los datos digitados por el usuario.

### Registro de Errores Corregidos y Soluciones Aplicadas
35. **Salvaguarda Transaccional Anti-Bloqueo del Ultimo Administrador Activo (`_verificar_salvaguarda_ultimo_administrador` y `_verificar_auto_modificacion_admin`)**:
    - *Causa:* La suspension o degradacion inadvertida del unico administrador activo del sistema o de la propia cuenta en sesion provocaria la perdida irrecuperable de la capacidad de gestion y gobernanza del sistema.
    - *Solucion:* Implementacion de validaciones atomicas en `ServicioGestionUsuarios` previas a la conmutacion de estado o actualizacion de rol, consultando el conteo de administradores activos y verificando el ID del usuario en sesion, emitiendo excepciones tipadas HTTP 409 Conflict ante cualquier intento de desproteccion corporativa.
36. **Validacion Condicional Pydantic y Asignacion Territorial Obligatoria para Roles Operativos**:
    - *Causa:* La asignacion de roles operativos ('encargado_sucursal', 'cajero') sin asociacion a una sucursal fisica, o vinculados a boutiques inexistentes o inactivas, violaba la integridad territorial del punto de venta y de la custodia de inventario.
    - *Solucion:* Implementacion de `@model_validator(mode="after")` en `UsuarioCrearEsquema` y `UsuarioActualizarEsquema` validando que `id_sucursal` este presente y no sea nulo para roles de tienda, comprobando en base de datos que la sucursal exista y tenga `activa = True`, forzando `id_sucursal = None` para los roles corporativos (`administrador`, `cliente`).
37. **Blindaje de Rutas y Segmentacion RBAC Dinamica en Angular (`roleGuard` y `AdminDashboardComponent`)**:
    - *Causa:* El acceso irrestricto por URL a vistas operativas privilegiadas y la exposicion de tarjetas de administracion de usuarios o sucursales a encargados de boutique contravenia el principio de menor privilegio.
    - *Solucion:* Implementacion del guard funcional `roleGuard(rolesPermitidos)` y `adminOnlyGuard` redirigiendo a `/admin` ante accesos no autorizados, actualizacion del layout del panel a 4 columnas responsivas (`grid-cols-1 md:grid-cols-2 lg:grid-cols-4`), y evaluacion computada en el dashboard para ocultar completamente las tarjetas de CU20 y CU21 al rol `encargado_sucursal`.

## [1.8.0] - 2026-09-20

### Promocion a Baseline Permanente
- **CU22 - Gestionar Prendas, Productos y Variantes (SKUs) (Catalogo Maestro de Articulos y Matriz Comercial):** Promovido oficialmente a especificacion permanente del sistema en [`modules/gestion_operativa/CU22-gestionar-productos.md`](modules/gestion_operativa/CU22-gestionar-productos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU22/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `changes/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada la exclusion tecnica de la aplicacion movil (`Ec-mobile`). La creacion editorial de prendas, fijacion de precios base y parametrizacion de matrices de variantes constituyen operaciones exclusivas de administracion corporativa y trastienda ejecutadas en el panel web. La aplicacion movil participa en modo solo lectura (`Read-Only`) mediante los endpoints publicos del catalogo (`GET /api/v1/productos`, `GET /api/v1/productos/{id_producto}`).
- **Validacion Completa:**
  - Backend: 156/156 tests en verde en `pytest` para toda la suite acumulada (23/23 especificos de CU22); modelos ORM en esquema `fashionstore` (`ProductoORM`, `VarianteProductoORM`), restriccion de unicidad compuesta `uq_variante_producto_talla_color`, algoritmo determinista de SKU corporativo `FS-[PROD]-[TALLA]-[COLOR]`, esquemas Pydantic v2 con validacion estricta de nombres y precios > 0, jerarquia de excepciones de dominio (`ProductoDuplicadoError`, `SkuDuplicadoError`, `VarianteDuplicadaError`, `ProductoConDependenciasError`, `VarianteConDependenciasError`), servicios de dominio con generador de producto cartesiano en lote y bloqueo de eliminacion fisica HTTP 409 ante dependencias de inventario, kardex, pedidos, carritos o reservas forzando baja logica (`activo = False`), y endpoints publicos y administrativos protegidos por rol `administrador`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 110/110 tests en verde en Vitest / Angular CLI (16/16 especificos de CU22); componente Standalone `ProductosAdminComponent` con `ChangeDetectionStrategy.OnPush`, estado reactivo 100% gobernado por Angular Signals (`signal()`, `computed()`), actualizacion de `AdminDashboardComponent` a tres columnas (`grid-cols-1 md:grid-cols-3`) con la 3ra tarjeta boutique "Prendas y Variantes (SKUs)", boton editorial de navegacion `"<- Volver al Panel Principal"` con `routerLink="/admin"`, modal de prenda con selector jerarquico de categorias integrado con `AtributosAdminService` (CU23), generador reactivo de matriz de variantes con seleccion multiple de chips de talla y muestras cromaticas (#HEX), calculo reactivo de combinaciones con previsualizacion de SKU y precio final (`precio_base + precio_extra`), y captura de conflictos 409 y 422 con Luxury Banners preservando intacto el estado del formulario.

### Registro de Errores Corregidos y Soluciones Aplicadas
32. **Generador Determinista de SKU Corporativo sin Colisiones ni Caracteres Especiales (`slugify_text` y `generar_sku_corporativo`)**:
    - *Causa:* La generacion manual o no normalizada de codigos de inventario para prendas de alta costura con tildes, espacios o simbolos generaba identificadores inconsistentes o propensos a colisiones globales.
    - *Solucion:* Implementacion de normalizacion con descomposicion canonica Unicode (NFD), purga de diacriticos, saneamiento alfanumerico con guiones y patron riguroso `FS-[SLUG_PROD]-[COD_TALLA]-[SLUG_COLOR]` truncado a 64 caracteres maximo.
33. **Blindaje de Integridad Relacional ante Borrado Fisico de Prendas y SKUs en Uso**:
    - *Causa:* Intentar eliminar prendas o variantes que cuentan con existencias en bodegas, ventas historicas o reservas generaba caidas de base de datos o perdida de trazabilidad contable.
    - *Solucion:* Verificacion transversal en `ServicioGestionProductos` y `ServicioGestionVariantes` comprobando existencias previas en `inventario_sucursal`, `detalles_pedido`, `items_carrito`, `reservas_probador` y `movimientos_inventario`, rechazando con HTTP 409 e instruyendo la desactivacion mediante baja logica (`activo = False`).
34. **Computo Cartesiano Reactivo de Variantes y Sobreescritura Dinamica de Precio en Angular Signals**:
    - *Causa:* La definicion manual de decenas de variantes por talla y color resultaba lenta y propensa a errores de digitacion en trastienda.
    - *Solucion:* Generador matricial interactivo en Angular que computa el producto cartesiano en vivo a partir de chips y swatches `#HEX`, ofreciendo campo editable de `precio_extra` que recalcula inmediatamente `precio_final = precio_base + precio_extra` antes de la persistencia masiva en lote.

## [1.7.0] - 2026-09-20

### Promocion a Baseline Permanente
- **CU23 - Gestionar Categorias, Tallas y Colores (Taxonomia Maestros y Atributos Textiles):** Promovido oficialmente a especificacion permanente del sistema en [`modules/gestion_operativa/CU23-gestionar-atributos.md`](modules/gestion_operativa/CU23-gestionar-atributos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU23/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `changes/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada la exclusion tecnica de la aplicacion movil (`Ec-mobile`). La configuracion taxonomica, ordenacion de tallas y codificacion cromatica constituyen operaciones editoriales exclusivas de back-office ejecutadas en el panel administrativo web. La aplicacion movil participa exclusivamente como consumidor de solo lectura (`Read-Only`) mediante los endpoints publicos existentes.
- **Validacion Completa:**
  - Backend: 133/133 tests en verde en `pytest` para toda la suite acumulada (30/30 especificos de CU23); modelos ORM en esquema `fashionstore` (`CategoriaORM`, `TallaORM`, `ColorORM`), soporte de jerarquia auto-referencial (`id_categoria_padre`), restriccion de orden numerico en tallas y codificacion `#HEX` en colores; esquemas Pydantic v2 con validacion estricta y normalizacion; jerarquia de excepciones tipadas con codigos de error semanticos; servicio de dominio con algoritmo de deteccion de ciclos aciclicos (DAG) en categorias (`_verificar_ciclo_jerarquico`) y validacion de dependencias relacionales previo a eliminacion (`CategoriaConDependenciasError`, `TallaEnUsoError`, `ColorEnUsoError`); endpoints publicos `/api/v1/categorias`, `/api/v1/tallas` y `/api/v1/colores`, y endpoints administrativos `/api/v1/admin/*` protegidos por rol `administrador`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 81/81 tests en verde en Vitest / Angular CLI (19/19 especificos de CU23); componente Standalone `CategoriasTallasColoresAdminComponent` con `ChangeDetectionStrategy.OnPush`, reactividad 100% gobernada por Angular Signals (`signal()`, `computed()`), panel de 3 pestanas independientes ('Categorias', 'Tallas', 'Colores'), modales interactivos con `NonNullableFormBuilder`, exclusion automatica de la categoria propia en el selector de padre para prevenir ciclos jerarquicos en la interfaz, sincronizacion bidireccional reactiva entre `<input type="color">` y el campo de texto `#HEX`, y captura de errores 409 y 422 con Luxury Banners preservando intactos los datos del formulario.

### Registro de Errores Corregidos y Soluciones Aplicadas
29. **Deteccion Ascendente de Ciclos Jerarquicos en Arbol de Categorias (`_verificar_ciclo_jerarquico`)**:
    - *Causa:* En modelos auto-referenciales, la asignacion de un descendiente como padre o la auto-referencia directa genera un bucle infinito que rompe la navegacion taxonomica y las consultas recursivas.
    - *Solucion:* Implementacion del algoritmo `_verificar_ciclo_jerarquico` en `ServicioGestionAtributos` que recorre la cadena de ancestros del nuevo padre propuesto hacia la raiz, verificando que no coincida con el identificador de la categoria a modificar y emitiendo `ReferenciaCircularError` (HTTP 422, `REFERENCIA_CIRCULAR_NO_PERMITIDA`).
30. **Blindaje de Integridad Relacional Previo a Eliminaciones Fisicas**:
    - *Causa:* La eliminacion accidental de una categoria con productos asociados o de una talla/color asignados a variantes de producto activas ocasionaria inconsistencias criticas en el catalogo e inventario de boutiques.
    - *Solucion:* Comprobacion proactiva de claves foraneas en `ServicioGestionAtributos` consultando `fashionstore.productos` y `fashionstore.variantes_producto` previo a la emision de la sentencia `DELETE`, bloqueando la transaccion y emitiendo excepciones tipadas de conflicto (HTTP 409) acompañadas de mensajes explicativos.
31. **Sincronizacion Bidireccional de Muestras Cromaticas (#HEX y Color Picker) en Angular**:
    - *Causa:* La integracion de `<input type="color">` con formularios reactivos de Angular puede generar discordancia si el usuario escribe manualmente un codigo hexadecimal o si el valor no incluye el prefijo '#'.
    - *Solucion:* Implementacion de manejadores reactivos bidireccionales `actualizarHexDesdePicker` y `onHexTextInput`, asegurando anteposicion automatica del caracter '#', transformacion a mayusculas y actualizacion sincronizada de la muestra visual swatch.

## [1.6.0] - 2026-09-20

### Promoción a Baseline Permanente
- **CU21 - Gestionar Sucursales y Ciudades (Gestión Operativa y Administración Territorial):** Promovido oficialmente a especificación permanente del sistema en [`modules/gestion_operativa/CU21-gestionar-sucursales.md`](modules/gestion_operativa/CU21-gestionar-sucursales.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU21/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 103/103 tests en verde en `pytest` para toda la suite acumulada (20/20 específicos de gestión operativa y territorial); modelos ORM en esquema `fashionstore` (`CiudadORM`, `SucursalORM`), restricción de unicidad relacional `UniqueConstraint("id_ciudad", "nombre")`, schemas Pydantic v2 con validación cronológica (`horario_cierre > horario_apertura`), servicio de dominio con protección de dependencias (`CIUDAD_CON_DEPENDENCIAS_ACTIVAS`) y prevención de desactivación ante inventario cautivo o reservas pendientes (`SUCURSAL_CON_OPERACIONES_PENDIENTES`), y endpoints administrativos bajo `/api/v1/admin/ciudades` y `/api/v1/admin/sucursales`, junto con endpoints públicos `/api/v1/ciudades` y `/api/v1/sucursales`.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, 0 errores), 62/62 tests pasando en Vitest / Angular CLI (21/21 de sucursales y ciudades), componente `SucursalesAdminComponent` Standalone con `ChangeDetectionStrategy.OnPush`, estado reactivo 100% gobernado con Angular Signals (`signal()`, `computed()`), pestañas de trabajo 'Boutiques' y 'Ciudades', filtros en tiempo real por ciudad y término de búsqueda, formularios fuertemente tipados con validación síncrona de horas, modales accesibles y Luxury Alerts con auto-dismiss.
  - Mobile: 73/73 tests en verde en `flutter test` (17/17 de gestión operativa), 0 incidencias en `flutter analyze`, arquitectura Feature-First en `lib/src/features/gestion_operativa/cu21_sucursales_ciudades/` (`datos/`, `dominio/`, `presentacion/`), `SucursalesBloc` gobernado por estados sellados inmutables (`SucursalesInicial`, `SucursalesCargando`, `SucursalesCargado`, `SucursalesError`, `SucursalOperacionExitosa`), pantalla `SucursalesAdminPantalla` con cabecera editorial Atelier, carrusel horizontal de chips de ciudad, tarjetas de boutique con toggle Switch interactivo con diálogo de confirmación, y formulario modal BottomSheet con selectores nativos de hora en formato 24h.

### Registro de Errores Corregidos y Soluciones Aplicadas
26. **Resolución Estática de Módulos para Analizador de Lenguaje en Antigravity IDE (`fashionstore_paths.pth`)**:
    - *Causa:* El analizador estático Pyrefly/Pylance señalaba 26 errores de resolución de importaciones relativas a la carpeta `Ec-backend/app` debido a que la raíz del espacio de trabajo es el directorio contenedor del monorepo.
    - *Solución:* Inclusión del archivo `fashionstore_paths.pth` en `Ec-backend/.venv/Lib/site-packages/` conteniendo las rutas absolutas normalizadas al backend y a la subcarpeta app, complementado con `extraPaths` en `.vscode/settings.json`, resolviendo limpiamente la resolución estática sin modificar el código fuente.
27. **Sincronización Reactiva de BLoC en Alternancia de Estado Operativo de Sucursal Móvil**:
    - *Causa:* Al confirmar el cambio de estado operativo en el diálogo modal de la aplicación Flutter, la llamada a `cambiarEstado` emitía un nuevo estado cargado pero la vista local requería actualización explícita del estado de montaje para reflejar de inmediato la animación del Switch.
    - *Solución:* Implementación de callback de sincronización con refresco de montaje tras la confirmación del diálogo, garantizando reactividad visual inmediata sin retrasos de renderizado.
28. **Validación Cruzada Síncrona de Invariantes Horarias en Formularios Web y Mobile**:
    - *Causa:* La captura manual de horarios de boutique permitía introducir combinaciones inconsistentes donde la hora de cierre precedía a la de apertura, delegando la detección únicamente al backend.
    - *Solución:* Incorporación de validadores síncronos cruzados en Angular (`validarHorarios`) y en Flutter (`_validarHorarios`), bloqueando la confirmación de formularios en el cliente y desplegando mensajes contextuales antes de efectuar la petición de red.

## [1.5.0] - 2026-09-20

### Promoción a Baseline Permanente
- **CU06 - Buscar y Filtrar Productos (Catálogo Omnicanal de Alta Costura Femenina):** Promovido oficialmente a especificación permanente del sistema en [`modules/catalogo_productos/CU06-buscar-filtrar-productos.md`](modules/catalogo_productos/CU06-buscar-filtrar-productos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU06-buscar-filtrar-productos/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 83/83 tests en verde en `pytest` para toda la suite acumulada (20/20 específicos de catálogo); modelos ORM del catálogo (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`), motor de búsqueda con normalización sin tildes/mayúsculas, expansión de singular/plural, búsqueda por palabras sueltas multicriterio, filtros 100% opcionales y endpoints `GET /api/v1/productos`, `GET /api/v1/catalogo/filtros-disponibles` y `POST /api/v1/catalogo/buscar`.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, 0 errores), 41/41 tests pasando en Vitest / Angular CLI (17/17 de catálogo), componente `BuscarProductosComponent` con confirmación diferida mediante botón `BUSCAR` y `Enter`, vaciado automático de input, badge editorial dismissible, paleta de 16 colores textiles, tipografía Outfit estandarizada y alineación pixel-perfect unificada con `/perfil` mediante `scrollbar-gutter: stable` y `max-w-[1440px] px-6`.
  - Mobile: 56/56 tests en verde en `flutter test` (14 de catálogo), 0 incidencias en `flutter analyze`, `CatalogoBloc` con estados sellados inmutables, `PantallaBuscarProductos` con carrusel horizontal de temporadas, filtros refinados con tallas cuadradas y 16 tonalidades, `GridView` de 2 columnas con tarjetas de lujo (`+ CESTA`, badges editoriales, favoritos), modal BottomSheet de rango y orden, y conexión fluida en BottomNavigationBar.

### Registro de Errores Corregidos y Soluciones Aplicadas
21. **Normalización Morfológica y Coincidencia Flexible en Búsqueda Multicriterio (`Términos sinónimos y palabras sueltas`)**:
    - *Causa:* Las consultas de búsqueda requerían coincidencia exacta o fallaban al buscar categorías directas ("vestido" vs "vestidos", "pantalón" con o sin tilde).
    - *Solución:* Implementación de `_normalizar_texto` (remoción de acentos/diacríticos y minúsculas), expansión semántica `_expandir_termino` (singular/plural de prendas y sinónimos de moda) y consultas combinadas con `or_` sobre nombre, descripción, categoría, colección, temporada y color sin error 500.
22. **Inconsistencia de Color y Modelo en Catálogo Femenino de Alta Costura**:
    - *Causa:* El producto "Vestido plisado seda" estaba incorrectamente listado como mármol, y existía una fotografía con modelo masculino en el catálogo de una firma exclusivamente orientada a moda femenina.
    - *Solución:* Corrección de semilla y registros a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ`, sustitución de imágenes masculinas por modelos femeninas de alta costura, y expansión de la paleta textil a 16 tonalidades de confección real.
23. **Confirmación Explícita de Búsqueda y Modo Borrador Diferido (Web y Mobile)**:
    - *Causa:* Los filtros o la escritura en el campo de texto ejecutaban peticiones tempranas innecesarias o generaban discrepancias si el usuario modificaba varios filtros a la vez.
    - *Solución:* Implementación de modo borrador diferido en Angular y Flutter, botón explícito `BUSCAR` + tecla `Enter`, vaciado automático del input tras la confirmación y almacenamiento del término activo en badge editorial dismissible.
24. **Desalineación Visual de Cabecera y Salto Horizontal entre Páginas Web**:
    - *Causa:* `/perfil` utilizaba `max-w-7xl` (1280px) mientras que `/buscar` utilizaba `max-w-[1440px] px-6`, y la aparición/desaparición de la barra de scroll vertical producía un brinco horizontal de 15px en la barra institucional y avatar.
    - *Solución:* Homologación estricta a `max-w-[1440px] px-6` en `perfil.component.html` y adición de la directiva `scrollbar-gutter: stable;` en `styles.scss`, garantizando estabilidad geométrica absoluta.
25. **Tipografía No Conforme en Titular "Visto recientemente"**:
    - *Causa:* Se empleaba tipografía cursiva serif en "Visto recientemente", desalineada con el Design System general.
    - *Solución:* Sustitución por la tipografía institucional `Outfit` (`font-sans font-semibold tracking-tight`), unificando la identidad visual corporativa en Desktop y Mobile.

## [1.4.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU33 - Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU33-recuperar-acceso.md`](modules/autenticacion_seguridad/CU33-recuperar-acceso.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU33-recuperar-acceso/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 63/63 tests en verde en `pytest` para toda la suite acumulada; modelo relacional `CodigoRecuperacionORM` en esquema `fashionstore` (migración Alembic `0002_codigos_recuperacion.py`), persistencia segura mediante digest SHA-256 (nunca texto plano), política anti-enumeración de usuarios uniforme con `200 OK`, rate limiting de 60s y hashing de clave con **Argon2id**.
  - Servicio SMTP y Entregabilidad: Integración asíncrona mediante `asyncio.to_thread` con Gmail SMTP (`smtp.gmail.com:587` STARTTLS); cabeceras RFC 5322 (`Message-ID`, `Date`) y RFC 3834 (`Auto-Submitted: auto-generated`), eliminando clasificación en spam y garantizando entrada directa a Inbox.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle en 3.7s), 17/17 tests pasando en Vitest / Angular CLI, fidelidad visual exacta con la captura Desktop (badge FS, medidor dinámico de 3 barras horizontales, timer reactivo de reenvío de 60s y botón `ACTUALIZAR Y ACCEDER →`).
  - Mobile: 42/42 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, `RecuperarPasswordBloc` con estados sellados, diseño fiel a la captura Mobile (tarjeta, monograma FS, 3 barras de fuerza dinámicas, escudo inferior) y conexión en login.

### Registro de Errores Corregidos y Soluciones Aplicadas
18. **Rechazo de Autenticación SMTP por Contraseña Estándar de Gmail (`535 5.7.8 BadCredentials`)**:
    - *Causa:* Google descontinuó el acceso por contraseña básica en junio de 2022 y requiere Contraseña de Aplicación de 16 caracteres generada tras activar 2FA.
    - *Solución:* Parametrización en `.env` y `Settings` con contraseña de aplicación de 16 caracteres y diagnóstico activo con `logging.basicConfig(level=logging.INFO)` en `main.py`.
19. **Entregabilidad de Correo en Bandeja de Spam por Cabeceras Faltantes y Términos de Phishing**:
    - *Causa:* Falta de cabeceras RFC 5322 (`Message-ID`, `Date`), falta de RFC 3834 (`Auto-Submitted: auto-generated`), codificación sin `Header(..., 'utf-8')` y términos de riesgo heurístico en la plantilla ("Seguridad Criptográfica 256-Bit SSL", emojis en celdas).
    - *Solución:* Generación de `Message-ID` y `Date` RFC, adición de metadatos transaccionales y depuración de la plantilla HTML/Text, logrando entrada garantizada en la Bandeja Principal (Inbox).
20. **Desbordamiento de Rótulo en Pantallas Móviles Pequeñas (`RenderFlex overflowed`)**:
    - *Causa:* En anchos reducidos, el rótulo de 6 dígitos y el botón de reenvío en la misma fila desbordaban el ancho disponible.
    - *Solución:* Aplicación de `Flexible(child: Text(..., overflow: TextOverflow.ellipsis))` para adaptación fluida en cualquier resolución.

## [1.3.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU03 - Cerrar Sesión (Logout / Revocación Omnicanal de Token y Purga Segura):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU03-cerrar-sesion.md`](modules/autenticacion_seguridad/CU03-cerrar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU03-cerrar-sesion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 52/52 tests en verde en `pytest` para toda la suite acumulada; implementación de `TokenBlacklistService` en memoria con indexación SHA-256 y expiración automática; rechazo garantizado con `401 Unauthorized` (`code="TOKEN_REVOCADO"`) ante reuso de token en endpoints protegidos.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle completado en 4.22s), 10/10 tests pasando en Vitest / Angular CLI, purga integral y resiliente de `localStorage` y `sessionStorage` en `finalize()` de `LoginService`, reseteo de Signal reactivo `usuarioActual.set(null)` y etiqueta unificada estricta `CERRAR SESIÓN`.
  - Mobile: 30/30 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, reinicio de `LoginBloc`, blindaje de pila de navegación con `pushAndRemoveUntil(..., (route) => false)` y etiqueta de botón invariable `CERRAR SESIÓN`.

### Registro de Errores Corregidos y Soluciones Aplicadas
15. **Consistencia Visual y Estabilidad de Texto en Botón de Salida (`CERRAR SESIÓN`)**:
    - *Causa:* Se proponían rótulos extendidos ("CERRAR SESIÓN SEGURA") o textos dinámicos durante el proceso de carga.
    - *Solución:* Fijación del texto unificado como `CERRAR SESIÓN` en Frontend y Mobile por especificación estricta de experiencia de usuario.
16. **Resolución de Rutas Relativas Profundas en Widgets de Flutter (`Package Imports`)**:
    - *Causa:* Importaciones relativas (`../../cu02_iniciar_sesion/...`) en `pantalla_perfil.dart` fallaban al compilar desde tests debido a la profundidad de tres niveles de subdirectorios en `presentacion/pantallas`.
    - *Solución:* Migración a importaciones canónicas de paquete (`import 'package:ec_mobile/src/...'`), garantizando resolución universal en desarrollo y pruebas.
17. **Contrato de Interfaz de Repositorio en Mocks de Test (`cerrarSesion`)**:
    - *Causa:* La adición de `cerrarSesion(String token)` a la interfaz abstracta `LoginRepositorio` rompía mocks no actualizados en suites de test de widgets (`MockLoginRepositorio`).
    - *Solución:* Implementación del método en todos los mocks de prueba (`test/pantalla_login_test.dart`, etc.), restableciendo 100% de tests en verde.

## [1.2.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU04 - Gestionar Perfil del Cliente (Consulta, Actualización y Panel Mi Cuenta):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU04-gestionar-perfil.md`](modules/autenticacion_seguridad/CU04-gestionar-perfil.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU04-gestionar-perfil/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 45/45 tests en verde en `pytest` para toda la suite acumulada; verificación en vivo de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` sobre Neon PostgreSQL Serverless.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 tests pasando en `ng test`, refresco instantáneo de estado bajo `OnPush` con `ChangeDetectorRef` y sincronización con `sessionStorage`/`localStorage`.
  - Mobile: 28/28 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, inyección de token real desde login y actualización interactiva en tiempo real.
  - Verificación en Vivo: Probado y validado en vivo por el usuario en web y móvil.

### Registro de Errores Corregidos y Soluciones Aplicadas
11. **Expiración Temprana de Token JWT (`401 Unauthorized: Signature has expired`)**:
    - *Causa:* El tiempo de expiración por defecto de tokens de acceso (`ACCESS_TOKEN_EXPIRE_MINUTES`) era corto (15-60 min), causando desconexiones silenciosas durante pruebas extendidas y edición de perfil.
    - *Solución:* Se amplió `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24 horas) en `app/core/config.py` y `.env` para asegurar persistencia durante desarrollo y depuración.
12. **Exclusión de Selector de Género por Modelo de Marca de Alta Costura Femenina**:
    - *Causa:* Se incluía selector de género en los formularios de edición de perfil, lo cual no aplica para una firma exclusivamente orientada a indumentaria femenina (ni para cuentas de empleados).
    - *Solución:* Retiro completo del selector de género en el HTML/TypeScript de Angular (`PerfilComponent`) y en el bottom sheet modal de Flutter (`PantallaPerfil`), manteniendo en el backend compatibilidad opcional sin forzar su uso.
13. **Falta de Persistencia y Refresco Inmediato de Perfil en Frontend Web**:
    - *Causa:* Los cambios confirmados en el modal de edición no actualizaban el storage local de sesión (`fashionstore_user`) y la estrategia `OnPush` no redibujaba los datos sin una recarga manual de página.
    - *Solución:* Implementación de `sincronizarSesionStorage(perfilActualizado)` e inyección de `ChangeDetectorRef` con llamada a `this.cdr.markForCheck()` tras la respuesta del backend.
14. **Discrepancia de Datos de Cuenta y Persistencia en App Móvil**:
    - *Causa:* `PantallaPerfil` consumía datos con un token mock por defecto en vez del token dinámico emitido por el login en Neon PostgreSQL, mostrando datos de prueba no coincidentes con el usuario real.
    - *Solución:* Conexión del callback `alCompletarLoginConToken` en `PantallaLogin` de Flutter hacia `PantallaPerfil(token: token)` y emisión reactiva inmediata de `PerfilCargadoState` en `PerfilBloc` tras el guardado atómico en PostgreSQL.

## [1.1.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU02 - Iniciar Sesión (Login / Autenticación Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU02-iniciar-sesion.md`](modules/autenticacion_seguridad/CU02-iniciar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU02-iniciar-sesion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 28/28 tests en verde en `pytest` y verificación en vivo de autenticación (200 OK, 401 Unauthorized) con actualización atómica de `ultimo_acceso` en Neon PostgreSQL.
  - Frontend Web: Compilación limpia en 5.4s con Angular CLI (`npm run build`) y comunicación proxy verificada.
  - Mobile: 19/19 tests en verde en `flutter test` y 0 incidencias en `flutter analyze`.

### Registro de Errores Corregidos y Soluciones Aplicadas
8. **`OPTIONS 400 Bad Request` y `ClientException: Failed to fetch` en Flutter Web**:
   - *Causa:* Flutter Web corre en puertos efímeros dinámicos (`http://localhost:*`). Starlette `CORSMiddleware` rechazaba los preflights al no estar el puerto dinámico en `CORS_ORIGINS`.
   - *Solución:* Adición de `CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"` en `core/config.py` y `main.py`, permitiendo cualquier puerto local de depuración.
9. **Desbordamientos RenderFlex en `PantallaLogin` de Flutter**:
   - *Causa:* Rótulos de contraseña y checkbox desbordaban en viewports móviles reducidos.
   - *Solución:* Adaptación con `Flexible`, `Expanded` y `TextOverflow.ellipsis`.
10. **Ajuste de Ruta de Entrada y Enrutamiento Bidireccional en Mobile**:
   - *Causa:* La app iniciaba en registro y el enlace inferior no resolvía hacia login cuando era raíz.
   - *Solución:* `home: const PantallaLogin()` en `main.dart` y navegación bidireccional inteligente en `pantalla_registro.dart` con `canPop`/`pushReplacement`.

## [1.0.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU01 - Registrarse (Alta Costura & Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU01-registrarse.md`](modules/autenticacion_seguridad/CU01-registrarse.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU01-autenticacion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 15/15 tests en verde en `Ec-backend`, 7/7 tests unitarios en `Ec-mobile`, build exitoso en `Ec-frontend`, y esquema PostgreSQL migrado a la base de datos en la nube (Neon Serverless).

### Registro de Errores Corregidos y Soluciones Aplicadas
1. **`ModuleNotFoundError: No module named 'core'`**:
   - *Causa:* Desalineación de imports tras mover módulos a `app/`.
   - *Solución:* Inserción de `app/` en `sys.path` y configuración de `pythonpath = ["app", "."]` en `pyproject.toml`.
2. **`ModuleNotFoundError: No module named 'psycopg2'`**:
   - *Causa:* Prefijo `postgresql://` invoca `psycopg2` por defecto en SQLAlchemy en lugar de `psycopg` (v3).
   - *Solución:* Normalización automática de URL a `postgresql+psycopg://` en `database.py` y `alembic/env.py`.
3. **`ImportError: email-validator is not installed`**:
   - *Causa:* Pydantic requiere `email-validator` para validar el tipo `EmailStr`.
   - *Solución:* Instalación y adición formal de `email-validator>=2.0.0` a `pyproject.toml`.
4. **Fallos 404 en `tests/test_health.py`**:
   - *Causa:* Doble instancia de FastAPI en memoria (`main` vs `app.main`).
   - *Solución:* Homologación estricta de imports a `from app.main import app` y limpieza de `.pyc`.
5. **Metadatos vacíos en Alembic (`Base.metadata` sin tablas)**:
   - *Causa:* SQLAlchemy requiere importar los modelos para registrar las tablas.
   - *Solución:* Auto-descubrimiento dinámico e introspección de paquetes con `pkgutil.walk_packages` e `importlib` en `alembic/env.py`.
6. **Incompatibilidad con PgBouncer en Neon (`unsupported startup parameter in options: search_path`)**:
   - *Causa:* El endpoint con connection pooling (`-pooler`) de Neon rechaza el parámetro `search_path` en el paquete de inicio.
   - *Solución:* Eliminación de `options` en `connect_args` y adopción del hook `@event.listens_for(engine, "connect")` para ejecutar `SET search_path TO fashionstore, public`.
7. **Discordancia de tipos en columna `rol` (`DatatypeMismatch`)**:
   - *Causa:* La columna `rol` es tipo `ENUM` nativo (`fashionstore.rol_usuario`), pero en el modelo `UsuarioORM` estaba tipada como `String(30)`, enviando `VARCHAR`.
   - *Solución:* Mapeo con `rol_usuario_enum = PG_ENUM(..., name="rol_usuario", schema="fashionstore", create_type=False)`.
