# Especificacion Tecnica Permanente: CU22 - Gestionar Prendas, Productos y Variantes (SKUs)

**Codigo:** CU22  
**Nombre:** Gestionar Prendas, Productos y Variantes (SKUs)  
**Paquete de Dominio:** `gestion_operativa`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu22_prendas_productos`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu22_prendas_productos`  
**Directorio Funcional Mobile:** Excluido formalmente (operacion editorial y de gestion de inventario exclusiva de back-office; consumo de solo lectura a traves de los endpoints publicos del catalogo)  
**Actores Primarios:** Administrador (Alta de prendas, parametrizacion de precios base y generacion de matrices de variantes)  
**Actores Secundarios:** Cliente, Empleado, Sistema (Consulta publica de catalogo, seleccion de talla y color en tienda)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 1.0.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentacion Funcional: `SI2-Parcial1.md` (Seccion 2.1.3 CU22: "CU22. Gestionar prendas, productos y variantes").
- Arquitectura de Referencia: `.agents/skills/fashionstore-backend-sdd/references/arquitectura.md` (Paquete Gestion Operativa: `RouterProductos`, `ServicioGestionProductos`, `ServicioGestionVariantes`, `ProductoORM`, `VarianteProductoORM`).
- Modelo de Dominio: `.agents/skills/fashionstore-backend-sdd/references/dominio.md` (Restricciones de unicidad compuesta `(id_producto, id_talla, id_color)`, SKU canonico y bloqueo relacional de dependencias operativas).
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Tokens Base-2, tipografia Outfit, paleta Slate/Camel/Obsidian, `ChangeDetectionStrategy.OnPush` y Angular Signals).

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU22 centraliza la gestion del catalogo maestro de prendas comerciales, parametrizacion de precios base y generacion masiva de variantes fisicas (SKUs) resultantes de la combinacion de atributos de talla y color. Garantiza la consistencia dimensional de los productos a traves de toda la cadena omnicanal, estableciendo codigos unicos de identificacion corporativa e integridad relacional rigurosa para evitar inconsistencias en inventario, ventas y pedidos.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), construida en Flutter 3.x, tiene como proposito exclusivo la experiencia de cara al cliente (vitrina editorial, probador de Realidad Aumentada, carrito y checkout) y tareas de consulta rapida para el personal de piso de venta. La creacion y edicion de prendas, definicion de precios base y parametrizacion de matrices de SKUs es una responsabilidad de back-office exclusiva del panel de administracion web (`Ec-frontend`). La aplicacion movil participa exclusivamente como consumidor en modo lectura (Read-Only) a traves de los endpoints publicos del catalogo (`GET /api/v1/productos`, `GET /api/v1/productos/{id_producto}`).

### 1.3 Reglas de Negocio Estrictas

1. **RB-1: Seguridad y Control de Acceso RBAC:**
   - Toda operacion de mutacion (creacion, actualizacion, conmutacion de estado o eliminacion) sobre productos o variantes requiere un token JWT con rol `administrador` verificado mediante `require_roles(["administrador"])`.
   - Las solicitudes no autenticadas retornan HTTP 401 Unauthorized y las realizadas por usuarios con rol cliente retornan HTTP 403 Forbidden.
   - Las consultas de catalogo abierto (`GET /api/v1/productos`, `GET /api/v1/productos/{id_producto}`) son publicas y accesibles sin credenciales.

2. **RB-2: Integridad y Unicidad de Prenda Comercial:**
   - Cada prenda debe poseer un nombre unico insensible a mayusculas/minusculas y libre de espacios redundantes.
   - La longitud minima del nombre es de 3 caracteres y maxima de 200 caracteres.
   - El precio base debe ser estrictamente mayor a cero (`precio_base > 0`).
   - El `id_categoria` debe corresponder a un registro existente en `fashionstore.categorias`. Si la categoria no existe, se rechaza la solicitud con HTTP 422 `CATEGORIA_INEXISTENTE`.
   - Intentos de registrar un producto con un nombre ya existente son rechazados con HTTP 409 `PRODUCTO_DUPLICADO`.

3. **RB-3: Generador Determinista de SKU Corporativo:**
   - Toda variante fisica debe poseer un codigo SKU unico globalmente en la tabla `fashionstore.variantes_producto`.
   - El SKU corporativo se genera de forma determinista y pura mediante la formula:
     `FS-[SLUG_PROD]-[COD_TALLA]-[SLUG_COLOR]`
   - Los componentes alfanumericos se procesan removiendo acentos y caracteres especiales mediante descomposicion canonica Unicode (NFD), convirtiendo a mayusculas y truncando a un maximo global de 64 caracteres.

4. **RB-4: Unicidad Compuesta de Variante (Tupla Producto-Talla-Color):**
   - Una prenda comercial no puede tener mas de una variante activa o registrada para la misma tupla `(id_producto, id_talla, id_color)`.
   - La restriccion esta garantizada a nivel de base de datos mediante la restriccion unica `uq_variante_producto_talla_color`.
   - Intentos de registrar variantes duplicadas se rechazan con HTTP 409 `VARIANTE_DUPLICADA` o `SKU_DUPLICADO`.

5. **RB-5: Sobreescritura Opcional de Precio:**
   - Una variante puede heredar el precio base de la prenda (`precio_extra = 0`) o definir un recargo comercial (`precio_extra > 0`).
   - El precio final efectivo se calcula reactiva y transparentemente como `precio_final = precio_base + precio_extra`.

6. **RB-6: Bloqueo de Eliminacion Fisica por Integridad Referencial:**
   - Antes de ejecutar cualquier eliminacion fisica (`DELETE`), el sistema comprueba la existencia de dependencias operacionales en:
     * `fashionstore.inventario_sucursal` (existencias o registros asociados).
     * `fashionstore.detalles_pedido` (pedidos historicos o en curso).
     * `fashionstore.items_carrito` (carritos activos de clientes).
     * `fashionstore.reservas_probador` (sesiones de probador programadas).
     * `fashionstore.movimientos_inventario` (kardex de almacen).
   - Si existen dependencias, la eliminacion se bloquea categoricamente retornando HTTP 409 `PRODUCTO_CON_DEPENDENCIAS_OPERATIVAS` o `VARIANTE_CON_DEPENDENCIAS_OPERATIVAS`, preservando la integridad referencial historica.

7. **RB-7: Conmutacion de Estado Logico (Baja / Alta Logica):**
   - Para descontinuar temporal o permanentemente una prenda o variante con transacciones previas, el administrador debe utilizar la conmutacion logica (`activo = False`).
   - Las prendas y variantes inactivas son inmediatamente ocultadas del catalogo publico de clientes, manteniendose visibles y auditables en el panel administrativo.

8. **RB-8: Consistencia Reactiva y Luxury Banners:**
   - En el frontend web, cualquier respuesta HTTP 409 (colisiones o dependencias) o HTTP 422 es capturada mediante Luxury Banners contextuales, preservando intactos los datos digitados por el usuario en el formulario para evitar retrabajos.

---

## 2. Contratos de API REST (FastAPI)

### 2.1 Endpoints Publicos (Catalogo Abierto)
- `GET /api/v1/productos`: Catalogo de prendas activas con soporte para filtros de texto, categoria y coleccion.
- `GET /api/v1/productos/{id_producto}`: Ficha de detalle de producto con sus variantes activas disponibles.

### 2.2 Endpoints Administrativos (Rol: Administrador)
- `GET /api/v1/admin/productos`: Listado integral de prendas con agregacion de variantes registradas y stock global.
- `POST /api/v1/admin/productos`: Alta de prenda comercial base (HTTP 201 Created).
- `GET /api/v1/admin/productos/{id_producto}`: Detalle administrativo con coleccion completa de variantes (activas e inactivas).
- `PUT /api/v1/admin/productos/{id_producto}`: Actualizacion editorial de la prenda (HTTP 200 OK).
- `PATCH /api/v1/admin/productos/{id_producto}/estado`: Conmutacion logica de visibilidad (`activo: bool`).
- `DELETE /api/v1/admin/productos/{id_producto}`: Eliminacion fisica protegida de la prenda (HTTP 204 No Content).
- `POST /api/v1/admin/productos/{id_producto}/variantes/matriz`: Generador de matriz cartesiana masiva (HTTP 201 Created).
- `POST /api/v1/admin/productos/{id_producto}/variantes`: Alta puntual individual de variante (HTTP 201 Created).
- `GET /api/v1/admin/productos/{id_producto}/variantes`: Listado de variantes de la prenda.
- `PUT /api/v1/admin/variantes/{id_variante}`: Modificacion de variante (SKU, recargo, visibilidad).
- `PATCH /api/v1/admin/variantes/{id_variante}/estado`: Conmutacion logica de visibilidad de variante.
- `DELETE /api/v1/admin/variantes/{id_variante}`: Eliminacion fisica protegida de variante (HTTP 204 No Content).

---

## 3. Arquitectura Frontend Web (Angular 19+ Standalone)

- **Componente Principal:** `ProductosAdminComponent` en `src/app/modules/gestion_operativa/cu22_prendas_productos/paginas/`.
- **Estrategia de Renderizado:** `ChangeDetectionStrategy.OnPush` combinada con **Angular Signals** (`signal()`, `computed()`).
- **Enrutamiento:** Ruta protegida `/admin/productos` vinculada a `authGuard` en `app.routes.ts`.
- **Servicio Reactivo:** `ProductosAdminService` inyectando `HttpClient` con senales para productos, detalle, variantes, estados de carga y notificaciones.
- **Integracion con CU23:** Consumo directo de `AtributosAdminService` para poblar el selector jerarquico de categorias y los selectores cromaticos y de tallas.
- **Generador de Matriz Cartesiana:**
  - Seleccion interactiva mediante chips de tallas y swatches de colores con codigo `#HEX`.
  - Computo reactivo del producto cartesiano `(Tallas x Colores)`.
  - Previsualizacion del SKU corporativo sugerido.
  - Sobreescritura individual o masiva del recargo `precio_extra` con calculo automatico de `precio_final`.
- **Diseno Editorial:** Contenedor institucional `max-w-[1440px] px-6 py-8 mx-auto`, tipografia Outfit, paleta Slate/Camel/Obsidian, barra superior minimalista y boton de navegacion `"<- Volver al Panel Principal"`.

---

## 4. Matriz de Cobertura de Criterios de Aceptacion

| Criterio | Descripcion del Criterio | Validacion Backend | Validacion Frontend |
|:---|:---|:---:|:---:|
| **AC-1** | Seguridad y Control de Acceso RBAC (401/403) | `test_cu22_productos_variantes.py` | `authGuard` / `app.routes.ts` |
| **AC-2** | Alta de Prenda Comercial con Precio Base > 0 | `test_cu22_productos_variantes.py` | Formulario Reactivo / Unit Tests |
| **AC-3** | Prevencion de Nombres Duplicados (HTTP 409) | `test_cu22_productos_variantes.py` | Luxury Banners / Unit Tests |
| **AC-4** | Validacion de Categoria Existente (HTTP 422) | `test_cu22_productos_variantes.py` | Selector Jerarquico CU23 |
| **AC-5** | Generador Determinista de Matriz Cartesiana | `test_cu22_productos_variantes.py` | Generador Matricial Reactivo |
| **AC-6** | Prevencion de Colisiones de SKU / Tupla Unica | `test_cu22_productos_variantes.py` | Luxury Banners / Unit Tests |
| **AC-7** | Sobreescritura de Precio (precio_base + precio_extra) | `test_cu22_productos_variantes.py` | Computo en Vivo de Precio Final |
| **AC-8** | Actualizacion Editorial con Validacion Anti-Colision | `test_cu22_productos_variantes.py` | Formulario de Edicion / Unit Tests |
| **AC-9** | Bloqueo Relacional 409 ante Dependencias de Inventario | `test_cu22_productos_variantes.py` | Modal de Confirmacion y Banner |
| **AC-10** | Baja Logica y Ocultamiento de Catalogo Publico | `test_cu22_productos_variantes.py` | Conmutador de Estado / Signals |
| **AC-11** | Consultas Publicas y Administrativas | `test_cu22_productos_variantes.py` | Filtros y Buscador en Vivo |
| **AC-12** | Arquitectura Standalone, OnPush y Signals | - | `productos-admin.component.ts` |
| **AC-13** | Tokens de Diseno Editorial Atelier | - | `productos-admin.component.scss` |
| **AC-14** | Integracion en Hub Central (Tercera Tarjeta Boutique) | - | `admin-dashboard.component.html` |
| **AC-15** | Boton Editorial de Retorno a /admin | - | Plantilla y Unit Tests |
| **AC-16** | Formulario Reactivo y Selector Jerarquico de Categoria | - | Integracion con `AtributosAdminService` |
| **AC-17** | Generacion Masiva y Swatches Cromaticos #HEX | - | Modal Matriz y Chips Interactivos |
| **AC-18** | Luxury Banners ante Conflictos HTTP 409 / 422 | - | Captura Contextual en Modales |
