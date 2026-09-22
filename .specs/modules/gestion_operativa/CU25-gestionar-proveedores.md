# Especificacion Tecnica Permanente: CU25 - Gestionar Proveedores

**Codigo:** CU25  
**Nombre:** Gestionar Proveedores  
**Paquete de Dominio:** `gestion_operativa` / `abastecimiento`  
**Directorio Funcional Backend:** `app/modules/gestion_operativa/cu25_proveedores`  
**Directorio Funcional Frontend:** `src/app/modules/gestion_operativa/cu25_proveedores`  
**Directorio Funcional Mobile:** Excluido formalmente (gestion societaria y negociacion mayorista corporativa; exclusivo panel web de administracion)  
**Actores Primarios:**  
- Administrador (Control total del padron corporativo, alta de proveedores, edicion de contratos y baja logica)  
- Encargado de Sucursal (Consulta de talleres, recepcion de mercaderia y coordinacion de abastecimiento)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 2.1.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Seccion 1.4 Alcance - Modulo de Compras y Proveedores, Seccion 2.3 Esquema Relacional de Base de Datos).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU25 centraliza el padron corporativo de talleres textiles, fabricantes y distribuidores mayoristas de FashionStore. Garantiza la consistencia fiscal (NIT/RUT y razon social unicos), la categorizacion por rubros textiles, la preservacion de la trazabilidad historica mediante baja logica y la integracion segura con recepciones de mercaderia en inventario (CU24) y prendas/colecciones (CU22).

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta concebida de forma exclusiva para la experiencia B2C del cliente final (exploracion editorial, probador virtual en Realidad Aumentada, bolsa y checkout).
Las negociaciones comerciales, la auditoria de albaranes, la captura de datos fiscales societarios (NIT/RUT) y el registro formal de fabricantes textiles constituyen labores operativas de oficina y trastienda corporativa que se ejecutan exclusivamente en la plataforma web de administracion (`Ec-frontend`).
Por consiguiente, se ratifica la exclusion formal de `Ec-mobile` de este caso de uso: no existen endpoints, modelos Dart ni pantallas en Flutter asociadas a la administracion de proveedores.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Todo endpoint bajo `/api/v1/admin/proveedores` exige token JWT valido con rol `administrador` o `encargado_sucursal`. Peticiones anonimas devuelven HTTP 401 Unauthorized; roles `cajero` o `cliente` reciben HTTP 403 Forbidden.

2. **RB-2: Unicidad Fiscal e Invarianza Tributaria:**
   - No pueden existir dos proveedores con el mismo `nit_rut` ni con la misma `razon_social` (insensible a mayusculas/minusculas). La colision produce HTTP 409 Conflict (`NIT_RUT_DUPLICADO` o `RAZON_SOCIAL_DUPLICADA`).

3. **RB-3: Sanitizacion y Validacion Obligatoria de Datos:**
   - Todos los campos textuales son saneados eliminando espacios en blanco redundantes. Campos como razon social (min 3), nit_rut (min 5), contacto (min 3), telefono (min 7), direccion (min 5) y correo con sintaxis valida son de cumplimiento obligatorio (HTTP 422 si incumplen).

4. **RB-4: Trazabilidad e Inmutabilidad Historica (Baja Logica Obligatoria):**
   - Se prohibe el borrado fisico (`DELETE`) de registros en `fashionstore.proveedores`. La desactivacion se realiza mediante `estado_activo = False`, inhabilitando al proveedor para nuevos ingresos de inventario o contrataciones, pero preservando intactos sus vinculos historicos con prendas, colecciones e informes de kardex.

5. **RB-5: Reactivacion Controlada:**
   - Un proveedor inactivo puede ser reactivado (`estado_activo = True`), restaurando de inmediato su disponibilidad para compras y recepciones en todas las sucursales de la cadena.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Modelo ORM (`fashionstore.proveedores`)
- **Archivo:** `app/modules/gestion_operativa/cu25_proveedores/modelos.py`
  * `id_proveedor`: Integer Primary Key autoincremental.
  * `id_usuario`: BigInteger FK a `fashionstore.usuarios(id_usuario)` (opcional).
  * `razon_social`: String(150) no nulo, unico, indexado.
  * `nit_rut`: String(30) no nulo, unico, indexado.
  * `contacto_nombre`: String(120) no nulo.
  * `telefono`: String(30) no nulo.
  * `email`: String(120) no nulo, indexado.
  * `direccion`: String(255) no nulo.
  * `ciudad`: String(80) no nulo, indexado.
  * `rubro`: String(80) no nulo, indexado.
  * `estado_activo`: Boolean no nulo, default True, indexado.
  * `creado_en`: DateTime(timezone=True) UTC default now().
  * `actualizado_en`: DateTime(timezone=True) UTC default now(), onupdate now().
  * Restricciones DDL: `UniqueConstraint('nit_rut')`, `UniqueConstraint('razon_social')`, `CheckConstraint` de longitudes minimas.

### 2.2 Migracion Alembic
- **Revision:** `alembic/versions/0006_cu25_proveedores_extension.py` (idempotente, compatibilidad con esquemas base).

### 2.3 Capa de Dominio y Servicios
- **Servicio:** `ServicioGestionProveedores` (`servicio.py`)
  * `listar_proveedores(db, filtros, usuario)`: consulta paginada multicriterio con ordenamiento descendente y calculo exacto de paginas.
  * `obtener_proveedor_por_id(db, id_proveedor, usuario)`: resolucion de ficha o HTTP 404.
  * `crear_proveedor(db, payload, usuario)`: validacion de unicidad previa y persistencia transaccional.
  * `actualizar_proveedor(db, id_proveedor, payload, usuario)`: validacion de no colision y refresco de `actualizado_en`.
  * `cambiar_estado_proveedor(db, id_proveedor, estado_activo, usuario)`: alternancia de estado preservando registros.

### 2.4 Router REST Endpoints
- `GET /api/v1/admin/proveedores`: consulta paginada (`q`, `estado_activo`, `estado`, `rubro`, `pagina`, `limite`).
- `GET /api/v1/admin/proveedores/{id_proveedor}`: obtencion de ficha tecnica por ID.
- `POST /api/v1/admin/proveedores`: alta de proveedor (HTTP 201 Created).
- `PUT /api/v1/admin/proveedores/{id_proveedor}`: actualizacion de ficha comercial (HTTP 200 OK).
- `PATCH /api/v1/admin/proveedores/{id_proveedor}/estado`: baja logica / reactivacion (HTTP 200 OK).

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Integracion en Dashboard Corporativo
- **Componente:** `AdminDashboardComponent` (`/admin`)
  * Tarjeta boutique interactiva: *"Proveedores y Fabricantes"*.
  * Categoria: *"Gestion de Abastecimiento"*.
  * Badge: *"Cadena de Suministro"*.
  * Boton: `id="btn-gestionar-proveedores"`, ruta `/admin/proveedores`.
  * Control RBAC: visible exclusivamente para `administrador` y `encargado_sucursal`.

### 3.2 Vista Administrativa Principal
- **Componente:** `ProveedoresAdminComponent` (`/admin/proveedores`)
  * Standalone Component con `ChangeDetectionStrategy.OnPush`.
  * Estado reactivo con Angular Signals: `proveedores`, `totalRegistros`, `paginaActual`, `totalPaginas`, `cargando`, `guardando`, `error`, `mensajeExito`, `filtros`.
  * Boton superior de navegacion: `<- Volver al Panel Principal` con `routerLink="/admin"`.
  * Barra de herramientas: buscador en tiempo real con debounce de 300 ms, selector de estado y selector de rubro.
  * Tabla maestra: razon social, rubro, identificacion tributaria, contacto comercial, ciudad, insignia cromada de estado y botones de accion (edicion y baja logica).
  * Modales reactivos con `NonNullableFormBuilder`: modal de alta, modal de edicion y dialogo de confirmacion de baja logica con advertencia de cese de recepcion de mercaderia.
  * Luxury Banners contextuales: captura no destructiva de errores HTTP 409 y 422 preservando los datos del formulario.

---

## 4. Matriz de Trazabilidad de Requisitos

| Criterio EARS | Capa | Componente / Archivo | Codigo HTTP Esperado | Estado de Verificacion |
| :--- | :--- | :--- | :--- | :--- |
| **# AC-1** | Backend | `cu25_proveedores/router.py` | 401 / 403 | Verificado (pytest) |
| **# AC-2** | Backend | `cu25_proveedores/router.py` | 200 OK | Verificado (pytest) |
| **# AC-3** | Backend | `cu25_proveedores/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-4** | Backend | `cu25_proveedores/router.py` | 200 OK / 404 | Verificado (pytest) |
| **# AC-5** | Backend | `cu25_proveedores/servicio.py` | 201 Created | Verificado (pytest) |
| **# AC-6** | Backend | `cu25_proveedores/servicio.py` | 409 Conflict | Verificado (pytest) |
| **# AC-7** | Backend | `cu25_proveedores/esquemas.py` | 422 Unprocessable | Verificado (pytest) |
| **# AC-8** | Backend | `cu25_proveedores/servicio.py` | 200 OK / 409 | Verificado (pytest) |
| **# AC-9** | Backend | `cu25_proveedores/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-10** | Backend | `cu25_proveedores/servicio.py` | 200 OK | Verificado (pytest) |
| **# AC-11** | Frontend | `admin-dashboard.component.html` | N/A | Verificado (vitest) |
| **# AC-12** | Frontend | `proveedores-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-13** | Frontend | `proveedores-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-14** | Frontend | `proveedores-admin.component.html` | N/A | Verificado (vitest) |
| **# AC-15** | Frontend | `proveedores-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-16** | Frontend | `proveedores-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-17** | Frontend | `proveedores-admin.component.ts` | N/A | Verificado (vitest) |
| **# AC-18** | Frontend | `proveedores-admin.component.html` | N/A | Verificado (vitest) |
| **# AC-19** | Frontend | `proveedores-admin.component.html` | N/A | Verificado (vitest) |

---

## 5. Criterios de Calidad y Definicion de Terminado (DoD)
1. Suites automatizadas: 224/224 tests de backend pasando en verde; 192/192 tests de frontend pasando en verde.
2. Compilacion AOT: `ng build` en `Ec-frontend` ejecutada con 0 errores y 0 advertencias de compilacion.
3. Auditoria lexica: CERO emojis en plantillas HTML, codigo TypeScript, hojas SCSS, modelos Python o documentacion markdown.
4. Gobernanza: Exclusion justificada de `Ec-mobile` ratificada formalmente.
