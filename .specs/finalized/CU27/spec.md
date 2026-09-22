# Especificacion de Requisitos: [CU27] Gestionar promociones

**Codigo del Caso de Uso:** CU27  
**Denominacion Oficial:** Gestionar promociones  
**Modulo Funcional:** Gestion Comercial / Marketing y Descuentos (`gestion_comercial` / `gestion_operativa`)  
**Actores Primarios:**  
- Administrador Corporativo (Acceso irrestricto: creacion, modificacion, conmutacion de vigencias y baja logica)  
- Encargado de Sucursal (Acceso de consulta informativa de promociones y cupones vigentes para asesoramiento al cliente)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Entorno de Implementacion:** Web corporativa exclusiva (`Ec-backend` FastAPI y `Ec-frontend` Angular 19+ Standalone)  
**Exclusion Formal de Plataforma:** `Ec-mobile` (Flutter) 100% excluida  

---

## 1. Vision General del Caso de Uso

### 1.1 Proposito y Justificacion de Negocio
El caso de uso "Gestionar promociones" centraliza la definicion, gobierno y trazabilidad de las campanas de incentivo comercial, politicas de descuento y codigos de cupon en la red de tiendas de FashionStore.  
En el modelo comercial de retail de moda contemporaneo, las estrategias promocionales deben conciliar dinamismo publicitario con estricto control de margenes financieros. Esto exige parametrizar esquemas de reduccion de precio tanto porcentuales como de monto fijo, aplicar topes maximos de beneficio, delimitar vigencias temporales infranqueables y definir cupos maximos de redencion.

Este modulo proporciona:
1. La creacion y parametrizacion de promociones comerciales de catalogo o cupones de canje alfanumericos unicos (insensibles a mayusculas/minusculas).
2. La configuracion de reglas de negocio: tipos de descuento (`porcentaje` o `monto_fijo`), valores nominales con validacion de topes y validaciones de no negatividad.
3. Delimitacion del alcance promocional: aplicabilidad global a la orden, segmentacion por categoria comercial (ej. "Vestidos de Noche") o aplicabilidad a prendas/modelos especificos.
4. Gobernanza temporal rigurosa: consistencia cronologica forzada (`fecha_fin > fecha_inicio`), control de cupos de uso (`limite_usos` vs. `usos_actuales`) y conmutacion de vigencia mediante baja logica sin perdida de datos historicos.

---

## 2. Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)

### 2.1 Justificacion Arquitectonica y de Negocio
La aplicacion movil de FashionStore (`Ec-mobile`), construida sobre Flutter 3.x, tiene como mision exclusiva brindar la experiencia de compra B2C orientada al consumidor final (exploracion de catalogo de moda, probador virtual inmersivo mediante Realidad Aumentada, configuracion de bolsa de compras y checkout digital con pasarela Stripe).

La creacion de campanas comerciales corporativas, la definicion de algoritmos de descuento, el aprovisionamiento de cupones promocionales con topes financieros y la supervision analitica del volumen de canjes son facultades exclusivas de la direccion comercial, mercadeo y back-office corporativo. Estas labores se ejecutan de manera reservada en estaciones de escritorio a traves del portal web `Ec-frontend`.

### 2.2 Ratificacion de Alcance Tecnico
1. Cero pantallas en `Ec-mobile`: No se construira ninguna vista, modal ni formulario de administracion de promociones en la aplicacion Flutter.
2. Cero servicios mutables en Flutter: No se implementaran llamadas de creacion, actualizacion ni conmutacion de estado hacia `/api/v1/admin/promociones` en la app movil.
3. Consumo pasivo futuro: La aplicacion movil consumira las promociones y cupones de forma estrictamente pasiva en el flujo transaccional de checkout mediante endpoints publicos de cotizacion o validacion de carrito, sin capacidad alguna de alterar la parametrizacion comercial.

---

## 3. Especificacion de Requisitos Funcionales bajo Sintaxis EARS

### Bloque A: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

#### Seguridad, Autenticacion y Control de Acceso RBAC
- **# AC-1 (Ubicuo - Autenticacion Obligatoria):**  
  El sistema debera exigir un token de acceso JWT valido en la cabecera `Authorization: Bearer <token>` para cualquier solicitud dirigida a las rutas base `/api/v1/admin/promociones`. Si la cabecera no se provee o el token es invalido o ha expirado, el sistema debera rechazar la operacion con HTTP 401 Unauthorized.

- **# AC-2 (Condicional - Control de Acceso RBAC por Rol):**  
  Si un usuario autenticado con rol `cajero` o `cliente` intenta acceder a cualquier operacion de consulta, creacion, modificacion o conmutacion de estado bajo `/api/v1/admin/promociones`, el sistema debera rechazar la peticion de forma determinista con HTTP 403 Forbidden (`ACCESO_DENEGADO_ROL_NO_AUTORIZADO`).

- **# AC-3 (Ubicuo - Segregacion Funcional de Operacion):**  
  El sistema debera admitir las solicitudes segun el rol autenticado:
  * Rol `administrador`: Control total (consulta paginada, creacion de promociones y cupones, edicion de metadatos, baja logica y reactivacion).
  * Rol `encargado_sucursal`: Acceso a la consulta paginada y detalle de promociones vigentes para verificacion y atencion comercial, sin facultades mutables ni destructivas.

#### Entidad del Dominio y Reglas de Negocio de Promociones
- **# AC-4 (Ubicuo - Estructura de Entidad Promocion):**  
  El sistema debera persistir la entidad `PromocionORM` en la tabla `fashionstore.promociones` conteniendo los campos:
  * `id_promocion`: Identificador clave primaria entero autoincremental.
  * `nombre`: Cadena de texto no nula (minimo 3, maximo 150 caracteres), descriptiva de la campana comercial.
  * `descripcion`: Texto explicativo opcional sobre los terminos de la promocion.
  * `codigo_cupon`: Cadena alfanumerica opcional (maximo 50 caracteres). Si se proporciona, debera ser unica en el sistema (insensible a mayusculas/minusculas) y almacenar el codigo en mayusculas sin espacios. Si es nulo, la promocion actua como descuento automatico de catalogo.
  * `tipo_descuento`: Cadena no nula con restriccion de tipo enum (`'porcentaje'` o `'monto_fijo'`).
  * `valor_descuento`: Valor numerico (`Numeric(10, 2)`) estrictamente mayor a 0. Si `tipo_descuento` es `'porcentaje'`, debera situarse en el rango de 1.00 a 100.00.
  * `fecha_inicio`: Marca temporal UTC (`TIMESTAMPTZ`) de inicio de vigencia de la campana.
  * `fecha_fin`: Marca temporal UTC (`TIMESTAMPTZ`) de culminacion de vigencia.
  * `tope_descuento`: Valor numerico opcional (`Numeric(10, 2) >= 0`) que limita el descuento maximo acumulable en moneda base cuando el tipo es `'porcentaje'`.
  * `limite_usos`: Entero opcional estrictamente mayor a 0 que restringe el total de canjes admitidos en la red. Si es nulo, se asume canje ilimitado.
  * `usos_actuales`: Entero no nulo con valor inicial por defecto en 0, que computa los canjes realizados.
  * `alcance`: Cadena no nula con restriccion de valor (`'global'`, `'categoria'`, `'producto'`), por defecto `'global'`.
  * `id_categoria`: Clave foranea entera opcional referenciando `fashionstore.categorias(id_categoria)`. Obligatoria si `alcance == 'categoria'`.
  * `id_producto`: Clave foranea bigint opcional referenciando `fashionstore.productos(id_producto)`. Obligatoria si `alcance == 'producto'`.
  * `estado_activo`: Booleano no nulo, con valor predeterminado `True`.
  * `creado_en`: Marca temporal UTC con zona horaria de creacion del registro.
  * `actualizado_en`: Marca temporal UTC con zona horaria de modificacion.

- **# AC-5 (Condicional - Validacion de Consistencia Cronologica):**  
  Si en una solicitud de creacion o actualizacion de promocion la `fecha_inicio` es posterior o igual a la `fecha_fin`, el sistema debera rechazar la transaccion con HTTP 422 Unprocessable Entity, emitiendo el codigo semantico `FECHAS_PROMOCION_INVALIDAS` ("La fecha de culminacion debe ser estrictamente posterior a la fecha de inicio").

- **# AC-6 (Condicional - Validacion de Rango y Tipo de Descuento):**  
  Si `tipo_descuento` es `'porcentaje'` y `valor_descuento` no se encuentra entre 1.00 y 100.00, o si `tipo_descuento` es `'monto_fijo'` y `valor_descuento <= 0`, el sistema debera rechazar la peticion respondiendo con HTTP 422 Unprocessable Entity (`VALOR_DESCUENTO_INVALIDO`).

- **# AC-7 (Condicional - Validacion de Unicidad de Codigo de Cupon):**  
  Si se proporciona un `codigo_cupon` que coincide (normalizado en mayusculas y sin espacios) con una promocion existente en el sistema, el sistema debera abortar la operacion respondiendo de manera determinista con HTTP 409 Conflict (`CODIGO_CUPON_DUPLICADO`).

- **# AC-8 (Condicional - Validacion de Integridad de Alcance Promocional):**  
  Si `alcance == 'categoria'` y no se especifica un `id_categoria` valido, o si la categoria referenciada no existe, el sistema debera rechazar la operacion con HTTP 422 Unprocessable Entity (`CATEGORIA_PROMOCION_INVALIDA`).  
  Si `alcance == 'producto'` y no se especifica un `id_producto` valido, o si el producto no existe, el sistema debera responder con HTTP 422 Unprocessable Entity (`PRODUCTO_PROMOCION_INVALIDO`).

- **# AC-9 (Por Evento - Listado Paginado y Filtrado de Promociones):**  
  Cuando un usuario autorizado envie una solicitud `GET /api/v1/admin/promociones`, el sistema debera retornar el listado paginado aplicando filtros opcionales:
  * `q`: Busqueda textual insensible a mayusculas sobre `nombre` y `codigo_cupon`.
  * `tipo_descuento`: Filtrado por `'porcentaje'`, `'monto_fijo'` o `'todos'`.
  * `estado_activo`: Filtrado booleano (`true`, `false` o `'todos'`).
  * `alcance`: Filtrado por `'global'`, `'categoria'`, `'producto'` o `'todos'`.
  * `ordenar_por`: Criterio de ordenacion (`fecha_inicio_desc`, `fecha_fin_asc`, `nombre_asc`, `valor_desc`, `usos_desc`). Por defecto: `fecha_inicio_desc`.
  * `pagina` (default 1) y `limite` (default 10, maximo 100).  
  La respuesta debera incluir metadatos de paginacion (`total`, `pagina`, `limite`, `total_paginas`) y metricas consolidadas de campanas.

- **# AC-10 (Por Evento - Detalle Individual de Promocion):**  
  Cuando un usuario autorizado solicite `GET /api/v1/admin/promociones/{id_promocion}`, el sistema debera retornar los datos completos de la promocion incluyendo los nombres descriptivos de la categoria o producto asociado si aplica. Si no existe, debera responder con HTTP 404 Not Found (`PROMOCION_NO_ENCONTRADA`).

- **# AC-11 (Por Evento - Creacion de Promocion Comercial):**  
  Cuando un administrador envie `POST /api/v1/admin/promociones` con un cuerpo valido, el sistema debera persistir el registro, normalizar el `codigo_cupon` a mayusculas (si se define), asignar `usos_actuales = 0`, `estado_activo = True` y retornar HTTP 201 Created con la entidad generada.

- **# AC-12 (Por Evento - Modificacion de Promocion):**  
  Cuando un administrador envie `PUT /api/v1/admin/promociones/{id_promocion}` con datos modificados, el sistema debera validar que la promocion exista, revalidar unicidad de codigo de cupon (excluyendo el propio registro), revalidar coherencia de fechas y retornar HTTP 200 OK.

- **# AC-13 (Por Evento - Conmutacion de Estado y Baja Logica):**  
  Cuando un administrador envie `PATCH /api/v1/admin/promociones/{id_promocion}/estado` con `{"estado_activo": boolean}`, el sistema debera actualizar el indicador. La baja logica (`estado_activo = False`) cesa inmediatamente la aplicacion del descuento en nuevos pedidos, conservando intactos los historicos de ventas y auditoria contable previa. Retorna HTTP 200 OK.

---

### Bloque B: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

#### Integracion en el Hub Administrativo
- **# AC-14 (Ubicuo - Tarjeta Corporativa en AdminDashboardComponent):**  
  El panel corporativo `/admin` debera presentar una tarjeta boutique para el modulo:
  * Categoria: "Gestion Comercial".
  * Titulo oficial: "Gestionar promociones".
  * Descripcion institucional: "Parametrizacion de campanas comerciales, descuentos porcentuales, cupones y limites de canje.".
  * Badge visual: "Marketing y Descuentos" con estilo Atelier.
  * Boton de navegacion: `id="btn-gestionar-promociones"` con directiva `routerLink="/admin/promociones"` y manejador `(click)="navegar('/admin/promociones', $event)"`.
  * Visibilidad RBAC: visible exclusivamente para roles `administrador` y `encargado_sucursal` (`@if (esAdmin() || esEncargado())`).
  * Iconografia: vector SVG corporativo limpio, sin caracteres emoji.

#### Layout Editorial y Metricas Consolidadas
- **# AC-15 (Ubicuo - Cabecera y Layout Editorial de la Vista):**  
  La vista en `/admin/promociones` debera estructurarse bajo un contenedor centrado `max-w-[1440px]`, patron arquitectonico `ChangeDetectionStrategy.OnPush`, paleta Slate/Camel/Obsidian y tipografia corporativa Outfit.
  * Cabecera con titulo H1: "Gestionar promociones".
  * Breadcrumbs: `ADMINISTRACION CORPORATIVA / GESTION COMERCIAL / GESTIONAR PROMOCIONES`.
  * Boton de retorno: `"<- Volver al Panel Principal"` con `routerLink="/admin"`.
  * Boton de accion primaria (visible unicamente para `administrador`): `id="btn-abrir-modal-crear-promocion"` con texto `"+ NUEVA PROMOCION"`.

- **# AC-16 (Ubicuo - Tarjetas de Metricas Comerciales Superiores):**  
  La interfaz debera desplegar una rejilla superior de 4 tarjetas de KPIs calculadas en tiempo real:
  1. *Promociones Activas*: conteo de campanas con `estado_activo == true`.
  2. *Cupones Vigentes*: total de promociones con `codigo_cupon != null` vigentes a la fecha.
  3. *Descuento Promedio*: media porcentual o monetaria de las campanas activas.
  4. *Usos Acumulados*: suma total de redenciones (`usos_actuales`) registradas en la red.

#### Barra de Filtros Reactiva y Tabla Maestra
- **# AC-17 (Por Evento - Barra de Filtros con Debounce de 300 ms):**  
  La interfaz debera proveer una barra de busqueda y filtros conectada a Angular Signals:
  * Campo de busqueda textual con retardo *debounce* de 300 ms para buscar por nombre o codigo de cupon.
  * Selector de tipo de descuento (`todos`, `porcentaje`, `monto_fijo`).
  * Selector de estado comercial (`todos`, `activas`, `inactivas`).
  * Selector de alcance (`todos`, `global`, `categoria`, `producto`).
  * Boton de restablecimiento inmediato de filtros con reinicio a la primera pagina.

- **# AC-18 (Ubicuo - Tabla Maestra de Promociones con Badges Cromaticos):**  
  La tabla maestra corporativa debera listar los registros con paginacion y columnas legibles:
  * *Campana*: nombre comercial, descripcion sintetica e insignia de alcance (`Global`, `Categoria`, `Producto`).
  * *Cupon*: codigo en chip monoespaciado en mayusculas, o badge dorado `Automatico` si no requiere cupon.
  * *Descuento*: valor resaltado (`-20%` o `-$50.000`), con indicacion de tope maximo si aplica.
  * *Vigencia*: rango cronologico formateado y semaforo de vigencia (`Vigente` en verde esmeralda, `Proxima` en azul cobalto, `Expirada` en ambar).
  * *Canjes*: barra de progreso o fraccion de uso (`15 / 100` o `Ilimitado`).
  * *Estado*: badge interactivo `Activo` / `Inactivo`.
  * *Acciones*: botones para `Editar` y `Conmutar Estado` (baja logica) con confirmacion modal.

#### Modales Reactivos y Captura Contextual No Destructiva
- **# AC-19 (Por Evento - Modal Reactivo de Creacion y Edicion):**  
  Al presionar `"+ NUEVA PROMOCION"` o el boton de edicion de una fila, el sistema abrira un modal reactivo basado en `NonNullableFormBuilder`:
  * Campos obligatorios: Nombre, Tipo de Descuento, Valor de Descuento, Fecha Inicio, Fecha Fin, Alcance.
  * Campos condicionales: Codigo de Cupon, Tope de Descuento, Limite de Usos, Selector de Categoria (si alcance es Categoria), Selector de Producto (si alcance es Producto).
  * Validacion sincronica inline de rango de fechas (`fecha_fin > fecha_inicio`), impidiendo la emision si la fecha final es menor o igual a la inicial.
  * Validacion de valor de descuento segun tipo seleccionado (maximo 100% si es porcentaje).

- **# AC-20 (Por Evento - Modal de Confirmacion de Conmutacion de Estado):**  
  Al hacer clic en el boton de conmutar estado de una fila, se abrira un modal de confirmacion con advertencia explicita de que la baja logica inhabilita la promocion de inmediato sin eliminar el historico de transacciones previas.

- **# AC-21 (Condicional - Luxury Banners No Destructivos):**  
  Si el backend responde con errores de validacion HTTP 422 o colision de cupon HTTP 409, el componente no debera destruir el formulario ni cerrar el modal; debera proyectar un Luxury Banner contextual de alerta (`errorBanner`), permitiendo al usuario corregir el codigo de cupon o las fechas sin perder los datos ya introducidos.

- **# AC-22 (Ubicuo - Estados de Carga y Vacio):**  
  La interfaz debera contemplar spinners de carga elegantes tipo esqueleto durante peticiones asincronas y paneles informativos de estado vacio si no existen campanas registradas o los filtros no devuelven coincidencias.

---

## 4. Matriz de Trazabilidad de Requisitos

| Codigo EARS | Descripcion Breve | Capa | Rol Minimo | Codigo HTTP |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Autenticacion Obligatoria JWT | Backend | Autenticado | 401 |
| **# AC-2** | Bloqueo RBAC a Roles Cajero y Cliente | Backend | Administrador / Encargado | 403 |
| **# AC-3** | Segregacion de Operaciones por Rol | Backend | Administrador / Encargado | 200 / 403 |
| **# AC-4** | Estructura de Entidad PromocionORM | Backend | Sistema | 200 / 201 |
| **# AC-5** | Validacion Cronologica de Fechas | Backend | Administrador | 422 |
| **# AC-6** | Validacion de Rango de Descuento | Backend | Administrador | 422 |
| **# AC-7** | Validacion de Unicidad de Codigo Cupon | Backend | Administrador | 409 |
| **# AC-8** | Integridad de Alcance Promocional | Backend | Administrador | 422 |
| **# AC-9** | Listado Paginado con Filtros Multicriterio | Backend | Encargado de Sucursal | 200 |
| **# AC-10** | Detalle Individual de Promocion | Backend | Encargado de Sucursal | 200 / 404 |
| **# AC-11** | Alta de Promocion Comercial | Backend | Administrador | 201 |
| **# AC-12** | Modificacion de Promocion | Backend | Administrador | 200 |
| **# AC-13** | Baja Logica y Conmutacion de Estado | Backend | Administrador | 200 |
| **# AC-14** | Tarjeta Corporativa en AdminDashboardComponent | Frontend | Encargado de Sucursal | N/A |
| **# AC-15** | Layout Editorial y Cabecera de la Vista | Frontend | Encargado de Sucursal | N/A |
| **# AC-16** | Tarjetas de KPIs Comerciales de Red | Frontend | Encargado de Sucursal | N/A |
| **# AC-17** | Barra de Filtros con Debounce (300 ms) | Frontend | Encargado de Sucursal | N/A |
| **# AC-18** | Tabla Maestra con Badges Cromaticos | Frontend | Encargado de Sucursal | N/A |
| **# AC-19** | Modal Reactivo con Validacion Sincronica | Frontend | Administrador | N/A |
| **# AC-20** | Modal de Confirmacion de Baja Logica | Frontend | Administrador | N/A |
| **# AC-21** | Luxury Banners No Destructivos | Frontend | Administrador | N/A |
| **# AC-22** | Estados de Carga y Vacio | Frontend | Encargado de Sucursal | N/A |
