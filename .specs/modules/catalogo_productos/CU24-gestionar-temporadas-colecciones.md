# Especificacion Tecnica Permanente: CU24 - Gestionar temporadas y colecciones

**Codigo:** CU24  
**Nombre:** Gestionar temporadas y colecciones  
**Paquete de Dominio:** `catalogo` / `taxonomia_comercial`  
**Directorio Funcional Backend:** `app/modules/catalogo/cu24_temporadas_colecciones`  
**Directorio Funcional Frontend:** `src/app/modules/catalogo/cu24_temporadas_colecciones`  
**Directorio Funcional Mobile:** Excluido formalmente (gestion de calendario editorial, temporadas y curaduria capsula exclusiva de trastienda web corporativa)  
**Actores Primarios:**  
- Administrador (Acceso total: creacion, modificacion, conmutacion de vigencias y baja logica)  
- Encargado de Sucursal (Acceso de consulta operativa para planificacion de mercadeo y escaparates)  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Version:** 2.3.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Catalogo e Indumentaria de Alta Costura).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush y Angular Signals).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU24 centraliza la estructuracion temporal y tematica del catalogo de moda de lujo de FashionStore. Permite planificar temporadas anuales con fechas formales de inicio y fin, anos comerciales, y curar colecciones capsula subordinadas, garantizando la trazabilidad historica de prendas mediante bajas logicas controladas y preservacion de integridad referencial.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, tiene como proposito exclusivo la experiencia de compra B2C orientada al consumidor final (exploracion de catalogo, probador con Realidad Aumentada, carrito y pasarela Stripe).  
La definicion del calendario estacional de la moda, la apertura o cierre de temporadas y la creacion de colecciones capsula constituyen labores analiticas y estrategicas reservadas exclusivamente al panel corporativo de escritorio (`Ec-frontend`).  
Por tanto, se ratifica formalmente la exclusion total de `Ec-mobile`: cero modelos, pantallas o servicios en Flutter.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Rutas base `/api/v1/admin/temporadas` y `/api/v1/admin/colecciones` exigen JWT valido (HTTP 401 si ausente). Roles `cajero` o `cliente` son rechazados con HTTP 403 Forbidden. `administrador` posee control irrestricto y `encargado_sucursal` opera en modo de solo lectura.

2. **RB-2: Consistencia Cronologica de Temporadas:**
   - La `fecha_fin` debe ser estrictamente posterior a la `fecha_inicio` (`fecha_fin > fecha_inicio`). Cualquier inconsistencia cronologica es rechazada con HTTP 422 Unprocessable Entity en backend y prevenida con validacion sincronica inline en frontend.

3. **RB-3: Unicidad Insensible a Mayusculas (Case-Insensitive):**
   - El nombre de cada temporada debe ser unico en todo el sistema (`LOWER(TRIM(nombre))`).
   - El nombre de cada coleccion debe ser unico dentro de la misma temporada matriz. Se permite el mismo nombre en temporadas distintas. Colisiones son rechazadas con HTTP 409 Conflict.

4. **RB-4: Integridad de Temporada Matriz en Colecciones:**
   - Toda coleccion debe asociarse obligatoriamente a una temporada existente (HTTP 404 si no existe) y activa (HTTP 422 si la temporada se encuentra inactiva).

5. **RB-5: Baja Logica Conmutativa:**
   - La desactivacion de temporadas o colecciones se realiza mediante `estado_activo = False`, inhabilitando nuevas asignaciones pero preservando intacta la integridad de productos, inventarios y ventas historicas.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/catalogo/cu24_temporadas_colecciones`
- **Servicios:**
  * `ServicioGestionTemporadas`: CRUD de temporadas, filtros multicriterio (`q`, `anio`, `estado_activo`, `ordenar_por`), conteo agregado de colecciones y conmutacion de estado.
  * `ServicioGestionColecciones`: CRUD de colecciones, join con temporada matriz, conteo agregado de prendas (`total_productos`), validacion de temporada activa y conmutacion de estado.
- **Excepciones de Dominio:** `TemporadaNoEncontradaError` (404), `TemporadaDuplicadaError` (409), `TemporadaFechasInvalidasError` (422), `ColeccionNoEncontradaError` (404), `ColeccionDuplicadaError` (409), `TemporadaInactivaParaColeccionError` (422).

### 2.2 Modelos Persistentes ORM
- `TemporadaORM` (`fashionstore.temporadas`): `id_temporada`, `nombre` (UNIQUE), `anio` (CHECK >= 2020), `fecha_inicio`, `fecha_fin` (CHECK fecha_fin > fecha_inicio), `estado_activo`, timestamps.
- `ColeccionORM` (`fashionstore.colecciones`): `id_coleccion`, `id_temporada` (FK), `nombre`, `descripcion`, `id_proveedor`, `estado_activo`, timestamps.

### 2.3 Endpoints REST Expuestos
- `GET /api/v1/admin/temporadas`: Listado paginado con filtros.
- `POST /api/v1/admin/temporadas`: Registro de nueva temporada.
- `GET /api/v1/admin/temporadas/{id}`: Detalle por identificador.
- `PUT /api/v1/admin/temporadas/{id}`: Actualizacion parcial.
- `PATCH /api/v1/admin/temporadas/{id}/estado`: Conmutacion de baja logica / reactivacion.
- `GET /api/v1/admin/colecciones`: Listado paginado con join de temporada matriz.
- `POST /api/v1/admin/colecciones`: Registro de coleccion capsula.
- `GET /api/v1/admin/colecciones/{id}`: Detalle de coleccion.
- `PUT /api/v1/admin/colecciones/{id}`: Actualizacion de coleccion.
- `PATCH /api/v1/admin/colecciones/{id}/estado`: Conmutacion de estado de coleccion.

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Componente y Rutas
- **Ruta:** `/admin/temporadas-colecciones` protegida por `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
- **Componente:** `TemporadasColeccionesAdminComponent` (Standalone, `ChangeDetectionStrategy.OnPush`, Angular Signals).
- **Servicio:** `TemporadasColeccionesAdminService` (manejo de estado reactivo con Signals y comunicacion HTTP tipada).

### 3.2 Interfaz de Usuario y Fidelidad Editorial
- Layout institucional `max-w-[1440px] px-6 py-8 mx-auto`, fondo Slate 50, tipografia Outfit, acentos Camel (`#AD8C63`) y Obsidian (`#0F172A`).
- Tarjeta corporativa en `AdminDashboardComponent` bajo "Taxonomia Comercial" con badge "Calendario Editorial" y acceso RBAC.
- Conmutador de pestanas reactivas (Temporadas / Colecciones).
- Barra de herramientas reactiva con debounce de 300 ms y filtros por anio, temporada y estado.
- Modales accesibles con `NonNullableFormBuilder` y validacion sincronica cruzada de fechas (`fecha_fin > fecha_inicio`).
- Luxury Banners no destructivos ante contingencias HTTP 409 y 422.

---

## 4. Matriz de Trazabilidad y Verificacion

| Criterio | Capa | Descripcion | Verificacion Automatizada |
| :--- | :--- | :--- | :--- |
| **# AC-1 a # AC-3** | Backend | Autenticacion JWT y control RBAC (401/403) | `test_cu24_temporadas_colecciones.py` |
| **# AC-4 a # AC-8** | Backend | CRUD, fechas, unicidad y baja logica de Temporadas | `test_cu24_temporadas_colecciones.py` |
| **# AC-9 a # AC-13** | Backend | CRUD, integridad matriz, unicidad y baja logica de Colecciones | `test_cu24_temporadas_colecciones.py` |
| **# AC-14** | Frontend | Tarjeta corporativa en AdminDashboardComponent | `admin-dashboard.component.spec.ts` |
| **# AC-15 a # AC-17** | Frontend | Layout editorial, pestanas reactivas y debounce | `temporadas-colecciones-admin.component.spec.ts` |
| **# AC-18 a # AC-21** | Frontend | Tablas maestras y modales con validacion de fechas | `temporadas-colecciones-admin.component.spec.ts` |
| **# AC-22 a # AC-23** | Frontend | Luxury Banners, paginacion y estados de carga | `temporadas-colecciones-admin.component.spec.ts` |
