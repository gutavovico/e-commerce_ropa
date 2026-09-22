# Especificacion Tecnica Permanente: CU23 - Gestionar Categorias, Tallas y Colores

**Codigo:** CU23  
**Nombre:** Gestionar Categorias, Tallas y Colores  
**Paquete de Dominio:** `gestion_operativa`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu23_categorias_tallas_colores`  
**Directorio Funcional Mobile:** Excluido formalmente (operacion editorial exclusiva de back-office; consumo de solo lectura a traves de endpoints publicos de catalogo)  
**Actores Primarios:** Administrador (Control total de configuracion y taxonomia)  
**Actores Secundarios:** Cliente, Empleado, Sistema (Consulta publica de filtros y navegacion)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 1.0.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentacion Funcional: `SI2-Parcial1.md` (Seccion 2.1.3 CU23 Lineas 841-856: "CU23. Gestionar categorias, tallas y colores").
- Arquitectura de Referencia: `.agents/skills/fashionstore-backend-sdd/references/arquitectura.md` (Paquete Gestion Operativa: `RouterAtributos`, `ServicioGestionAtributos`, `CategoriaORM`, `TallaORM`, `ColorORM`).
- Modelo de Dominio: `.agents/skills/fashionstore-backend-sdd/references/dominio.md` (Invariantes de integridad relacional sobre variantes y productos).
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Tokens Base-2, tipografia Outfit, paleta Slate/Camel/Obsidian).

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU23 centraliza la definicion, parametrizacion y mantenimiento de los atributos maestros de catalogacion textil de la cadena FashionStore. Permite estructurar el arbol taxonomico de categorias (principales y subcategorias), la escala comercial de tallas numeradas secuencialmente, y la paleta cromatica textil con codigos `#HEX` para la representacion visual precisa de muestras (swatches).

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta orientada exclusivamente a la experiencia de cara al cliente (vitrina editorial, vestidor de Realidad Aumentada, carrito y checkout) y tareas de consulta rapida por dependientes de boutique. La administracion y parametrizacion taxonomica es una funcion editorial estrategica de back-office que se ejecuta exclusivamente en el panel de administracion web (`Ec-frontend`). La aplicacion movil participa en calidad de consumidor de solo lectura mediante los endpoints publicos (`GET /api/v1/categorias`, `GET /api/v1/tallas`, `GET /api/v1/colores`).

### 1.3 Reglas de Negocio Estrictas

1. **RB-1: Seguridad y Control de Acceso RBAC:**
   - Toda operacion de mutacion (creacion, actualizacion y eliminacion) en categorias, tallas y colores exige token JWT con rol `administrador` verificado mediante `require_roles(["administrador"])`.
   - Las consultas de solo lectura (`/api/v1/categorias`, `/api/v1/tallas`, `/api/v1/colores`) son publicas y abiertas.

2. **RB-2: Arbol Jerarquico de Categorias y Prevencion de Ciclos (DAG):**
   - Una categoria puede ser raiz (`id_categoria_padre = null`) o subcategoria (`id_categoria_padre > 0`).
   - El sistema previene estrictamente referencias circulares directas (`id_categoria == id_categoria_padre`) o indirectas (ciclos en el grafo jerarquico) mediante el algoritmo de recorrido ascendente `_verificar_ciclo_jerarquico`, respondiendo con HTTP 422 `REFERENCIA_CIRCULAR_NO_PERMITIDA`.

3. **RB-3: Proteccion de Integridad Relacional en Eliminacion de Categorias:**
   - Una categoria no puede eliminarse si posee subcategorias dependientes (`CategoriaORM.id_categoria_padre == id_categoria`) o si cuenta con productos asociados en el catalogo (`ProductoORM.id_categoria == id_categoria`).
   - El sistema rechaza la eliminacion con HTTP 409 `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS`.

4. **RB-4: Estandarizacion y Orden Secuencial de Tallas:**
   - Todo codigo de talla debe ser unico (insensible a mayusculas/minusculas) y se normaliza a mayusculas sin espacios perimetrales.
   - El campo `orden` debe ser un entero positivo o cero (`orden >= 0`), garantizando la presentacion predecible en filtros y selectores de compra.

5. **RB-5: Proteccion de Integridad Relacional en Eliminacion de Tallas:**
   - Una talla no puede eliminarse si se encuentra asignada a una o mas variantes de producto en inventario (`VarianteProductoORM.id_talla == id_talla`).
   - El sistema bloquea la transaccion con HTTP 409 `TALLA_EN_USO_EN_VARIANTES`.

6. **RB-6: Denominacion Textil y Codificacion Hexadecimal #HEX de Colores:**
   - La denominacion textil debe ser unica en el sistema (ej. "Negro Ebano", "Rojo Carmin", "Blanco Marfil").
   - El codigo de color debe cumplir estrictamente con la expresion regular `^#[0-9A-Fa-f]{6}$` (longitud fija de 7 caracteres iniciando con `#`), normalizandose a mayusculas.

7. **RB-7: Proteccion de Integridad Relacional en Eliminacion de Colores:**
   - Un color textil no puede eliminarse si se encuentra asignado a una o mas variantes de prendas (`VarianteProductoORM.id_color == id_color`).
   - El sistema bloquea la operacion con HTTP 409 `COLOR_EN_USO_EN_VARIANTES`.

8. **RB-8: Consistencia Reactiva y Experiencia de Usuario (Luxury Banners):**
   - La aplicacion web captura errores HTTP 409 y 422 desplegando banners de alerta contextuales sin perder ni reiniciar los datos digitados por el usuario en los formularios modales.

---

## 2. Contratos de API REST (FastAPI)

### 2.1 Endpoints Publicos
- `GET /api/v1/categorias`: Lista de categorias ordenadas alfabeticamente.
- `GET /api/v1/tallas`: Lista de tallas comerciales ordenadas por `orden ASC`.
- `GET /api/v1/colores`: Lista de colores textiles con representacion hexadecimal.

### 2.2 Endpoints Administrativos (Rol: Administrador)
- `GET /api/v1/admin/categorias`: Categorias con `total_productos` y `total_subcategorias`.
- `POST /api/v1/admin/categorias`: Crear categoria (HTTP 201).
- `PUT /api/v1/admin/categorias/{id_categoria}`: Actualizar categoria con verificacion anti-ciclos (HTTP 200).
- `DELETE /api/v1/admin/categorias/{id_categoria}`: Eliminar categoria libre de dependencias (HTTP 204).
- `GET /api/v1/admin/tallas`: Tallas con `total_variantes`.
- `POST /api/v1/admin/tallas`: Crear talla (HTTP 201).
- `PUT /api/v1/admin/tallas/{id_talla}`: Actualizar talla (HTTP 200).
- `DELETE /api/v1/admin/tallas/{id_talla}`: Eliminar talla libre de variantes (HTTP 204).
- `GET /api/v1/admin/colores`: Colores con `total_variantes`.
- `POST /api/v1/admin/colores`: Crear color con `#HEX` (HTTP 201).
- `PUT /api/v1/admin/colores/{id_color}`: Actualizar color (HTTP 200).
- `DELETE /api/v1/admin/colores/{id_color}`: Eliminar color libre de variantes (HTTP 204).

---

## 3. Arquitectura Frontend Web (Angular 19+ Standalone)

- **Componente:** `CategoriasTallasColoresAdminComponent` (`standalone: true`, `OnPush`).
- **Ruta:** `/admin/atributos` protegida con `authGuard`.
- **Estado Reactivo:** 100% gobernado por **Angular Signals** (`signal()`, `computed()`).
- **Servicio:** `AtributosAdminService` con inyeccion de `HttpClient` y cabeceras Bearer JWT.
- **Formularios:** Construidos con `NonNullableFormBuilder`. Sincronizacion bidireccional entre `<input type="color">` y el campo de texto `#HEX`.
- **Layout:** Contenedor institucional `max-w-[1440px] px-6 mx-auto` con tokens Atelier y tipografia corporativa Outfit.

---

## 4. Matriz de Cobertura de Criterios de Aceptacion

| ID Criterio | Descripcion | Plataforma | Codigo HTTP / Validacion |
|:---|:---|:---:|:---:|
| **AC-1** | Seguridad RBAC en endpoints administrativos | Backend | HTTP 401 / 403 |
| **AC-2** | Creacion de categoria taxonomica normalizada | Backend | HTTP 201 |
| **AC-3** | Prevencion de categoria duplicada | Backend | HTTP 409 `CATEGORIA_DUPLICADA` |
| **AC-4** | Prevencion de referencias circulares en categorias | Backend | HTTP 422 `REFERENCIA_CIRCULAR_NO_PERMITIDA` |
| **AC-5** | Proteccion de integridad en baja de categoria | Backend | HTTP 409 `CATEGORIA_CON_PRODUCTOS_O_SUBCATEGORIAS` |
| **AC-6** | Creacion y secuenciacion comercial de tallas | Backend | HTTP 201 (`orden ASC`) |
| **AC-7** | Unicidad y validacion de codigo de talla | Backend | HTTP 409 `TALLA_DUPLICADA` / 422 |
| **AC-8** | Proteccion de integridad en baja de talla | Backend | HTTP 409 `TALLA_EN_USO_EN_VARIANTES` |
| **AC-9** | Creacion de color textil con formato #HEX | Backend | HTTP 201 (`^#[0-9A-Fa-f]{6}$`) |
| **AC-10** | Unicidad y validacion regex de color | Backend | HTTP 409 `COLOR_DUPLICADO` / 422 |
| **AC-11** | Proteccion de integridad en baja de color | Backend | HTTP 409 `COLOR_EN_USO_EN_VARIANTES` |
| **AC-12** | Consultas publicas y enriquecidas con metricas | Backend | HTTP 200 |
| **AC-13** | Componente Standalone y Angular Signals | Frontend Web | Angular 19+ OnPush |
| **AC-14** | Tokens de diseno, Base-2 y tipografia Outfit | Frontend Web | Tailwind CSS institucional |
| **AC-15** | Panel editorial con 3 pestanas de trabajo | Frontend Web | Tabs Categorias / Tallas / Colores |
| **AC-16** | Formularios reactivos con selector de swatch | Frontend Web | NonNullableFormBuilder / Input Color |
| **AC-17** | Captura y visualizacion de conflictos 409/422 | Frontend Web | Luxury Banners sin perdida de datos |
