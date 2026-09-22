# Plan de Tareas: [CU24] Gestionar temporadas y colecciones

**Caso de Uso:** CU24  
**Denominacion Oficial:** Gestionar temporadas y colecciones  
**Modulo:** Catalogo / Taxonomia Comercial (`catalogo_productos`)  
**Metodologia:** Spec-Driven Development (SDD)  
**Estado:** Planificacion Aprobada (Fase 3)  

---

## 1. Estructura de Oleadas de Implementacion

### Oleada 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

- [x] **Tarea 1.1: Migracion Alembic idempotente y modelos ORM en `app/modules/catalogo/cu24_temporadas_colecciones/modelos.py`**
  - **Archivos:**
    - `Ec-backend/alembic/versions/0007_cu24_temporadas_colecciones.py`
    - `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/modelos.py`
    - `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/__init__.py`
  - **Descripcion:**
    * Crear migracion Alembic idempotente `0007_cu24_temporadas_colecciones.py` para anadir columnas faltantes (`anio`, `estado_activo`, `creado_en`, `actualizado_en`), restricciones `CHECK (fecha_fin > fecha_inicio)` y `CHECK (anio >= 2020)`, e indices unicos para nombres en minusculas en `fashionstore.temporadas` y `fashionstore.colecciones`.
    * Modelar `TemporadaORM` y `ColeccionORM` con SQLAlchemy 2.0 y mapeo Mapped.
  - **Criterios Mapeados:** `# AC-4`, `# AC-9`.
  - **Verificacion:** Ejecucion de `alembic upgrade head` sin errores en PostgreSQL Neon.

- [x] **Tarea 1.2: Esquemas Pydantic v2 en `app/modules/catalogo/cu24_temporadas_colecciones/esquemas.py`**
  - **Archivo:** `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/esquemas.py`
  - **Descripcion:**
    * Implementar DTOs de entrada y salida para temporadas: `TemporadaCrearIn`, `TemporadaActualizarIn`, `TemporadaItemOut`, `ListaPaginadaTemporadasOut`.
    * Implementar DTOs para colecciones: `ColeccionCrearIn`, `ColeccionActualizarIn`, `ColeccionItemOut`, `ListaPaginadaColeccionesOut`.
    * Configurar validadores `@model_validator` para garantizar que `fecha_fin > fecha_inicio` y `@field_validator` para sanitizacion `strip()` de nombres.
  - **Criterios Mapeados:** `# AC-4`, `# AC-5`, `# AC-9`.
  - **Verificacion:** Pruebas unitarias de esquemas y rechazo 422 ante fechas invertidas.

- [x] **Tarea 1.3: Jerarquia de excepciones semanticas de dominio en `app/modules/catalogo/cu24_temporadas_colecciones/errores.py`**
  - **Archivo:** `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/errores.py`
  - **Descripcion:**
    * Definir clase base `TemporadaError(HTTPException)`.
    * Implementar `TemporadaNoEncontradaError` (404), `TemporadaDuplicadaError` (409), `TemporadaFechasInvalidasError` (422), `ColeccionNoEncontradaError` (404), `ColeccionDuplicadaError` (409) y `TemporadaInactivaParaColeccionError` (422).
  - **Criterios Mapeados:** `# AC-5`, `# AC-6`, `# AC-10`, `# AC-11`.
  - **Verificacion:** Emision de respuestas HTTP estructuradas con `codigo` y `mensaje`.

- [x] **Tarea 1.4: Capa de servicio transaccional en `app/modules/catalogo/cu24_temporadas_colecciones/servicio.py`**
  - **Archivo:** `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/servicio.py`
  - **Descripcion:**
    * Implementar `ServicioGestionTemporadas`: metodos para listar paginado con filtros, obtener por ID, crear con validacion de no duplicidad, actualizar y conmutar `estado_activo` (baja logica).
    * Implementar `ServicioGestionColecciones`: metodos para listar paginado con join de temporada matriz y conteo de productos, crear con validacion de unicidad por temporada, actualizar y conmutar estado.
  - **Criterios Mapeados:** `# AC-3`, `# AC-6`, `# AC-7`, `# AC-8`, `# AC-10`, `# AC-11`, `# AC-12`, `# AC-13`.
  - **Verificacion:** Insercion, consulta y actualizacion transaccional en sesion de base de datos.

- [x] **Tarea 1.5: Router REST y registro en agregador principal**
  - **Archivos:**
    - `Ec-backend/app/modules/catalogo/cu24_temporadas_colecciones/router.py`
    - `Ec-backend/app/modules/catalogo/router.py`
  - **Descripcion:**
    * Exponer endpoints bajo `/api/v1/admin/temporadas` (GET, POST, GET /{id}, PUT /{id}, PATCH /{id}/estado).
    * Exponer endpoints bajo `/api/v1/admin/colecciones` (GET, POST, GET /{id}, PUT /{id}, PATCH /{id}/estado).
    * Custodiar con dependencias de seguridad `require_roles(["administrador", "encargado_sucursal"])` para lecturas y `require_roles(["administrador"])` para mutaciones.
    * Conectar el router al agregador de catalogo o aplicacion principal.
  - **Criterios Mapeados:** `# AC-1`, `# AC-2`, `# AC-7`, `# AC-8`, `# AC-12`, `# AC-13`.
  - **Verificacion:** Inspeccion de documentacion OpenAPI en `/docs`.

- [x] **Tarea 1.6: Suite de pruebas automatizadas Pytest en `tests/modules/catalogo/test_cu24_temporadas_colecciones.py`**
  - **Archivo:** `Ec-backend/tests/modules/catalogo/test_cu24_temporadas_colecciones.py`
  - **Descripcion:**
    * Crear suite de pruebas cubriendo los 12 casos disenados:
      1. Rechazo de peticion sin token (401).
      2. Bloqueo de rol cajero (403).
      3. Bloqueo de rol cliente (403).
      4. Acceso administrador exitoso (200).
      5. Acceso de lectura de encargado de sucursal (200).
      6. Alta exitosa de temporada (201).
      7. Rechazo de fechas invalidas (422).
      8. Rechazo de nombre de temporada duplicado (409).
      9. Baja logica de temporada (PATCH 200).
      10. Alta exitosa de coleccion vinculada a temporada (201).
      11. Rechazo de coleccion duplicada en misma temporada (409).
      12. Rechazo de alta de coleccion en temporada inactiva (422).
  - **Criterios Mapeados:** `# AC-1` al `# AC-13`.
  - **Verificacion:** 100% de tests en verde con `pytest`.

---

### Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript DTO**
  - **Archivo:** `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/modelos/temporadas-colecciones.dto.ts`
  - **Descripcion:**
    * Declarar interfaces fuertemente tipadas: `TemporadaItem`, `TemporadaCrearPayload`, `TemporadaActualizarPayload`, `FiltrosTemporada`, `RespuestaListaTemporadas`.
    * Declarar interfaces: `ColeccionItem`, `ColeccionCrearPayload`, `ColeccionActualizarPayload`, `FiltrosColeccion`, `RespuestaListaColecciones`.
  - **Criterios Mapeados:** `# AC-18`, `# AC-19`.
  - **Verificacion:** Compilacion de TypeScript sin errores de tipado.

- [x] **Tarea 2.2: Servicio HTTP reactivo con Angular Signals y suite unitaria**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/servicios/temporadas-colecciones-admin.service.ts`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/servicios/temporadas-colecciones-admin.service.spec.ts`
  - **Descripcion:**
    * Crear servicio inyectable en root consumiendo las APIs `/api/v1/admin/temporadas` y `/api/v1/admin/colecciones`.
    * Manejar estado centralizado con Signals: `temporadas`, `totalTemporadas`, `colecciones`, `totalColecciones`, `temporadasActivasParaSelector`, `cargando`, `guardando`, `error`, `mensajeExito`, `pestanaActiva`.
    * Crear suite unitaria con `provideHttpClientTesting()` cubriendo llamadas exitosas y captura de errores 409/422.
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`, `# AC-22`.
  - **Verificacion:** Pruebas unitarias de servicio ejecutandose en verde con `ng test`.

- [x] **Tarea 2.3: Tarjeta en `AdminDashboardComponent` con visibilidad RBAC**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Incorporar la tarjeta boutique bajo la categoria "Taxonomia Comercial":
      - Titulo oficial: `"Gestionar temporadas y colecciones"`.
      - Descripcion: `"Calendario estacional de la moda, vigencias de campana y curaduria de colecciones capsula."`.
      - Badge: `"Calendario de Moda"`.
      - Boton: `id="btn-gestionar-temporadas-colecciones"` con `routerLink="/admin/temporadas-colecciones"`.
      - Icono vectorial SVG limpio (sin emojis).
      - Condicional RBAC: `@if (esAdmin() || esEncargado())`.
    * Actualizar `admin-dashboard.component.spec.ts` verificando el enlace y visibilidad por rol.
  - **Criterios Mapeados:** `# AC-14`.
  - **Verificacion:** Tests del dashboard pasando en verde.

- [x] **Tarea 2.4: Componente Standalone `TemporadasColeccionesAdminComponent` y enrutamiento protegido**
  - **Archivos:**
    - `Ec-frontend/src/app/app.routes.ts`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.ts`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.html`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.scss`
  - **Descripcion:**
    * Registrar ruta `/admin/temporadas-colecciones` en `app.routes.ts` protegida con `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
    * Crear `TemporadasColeccionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y layout editorial `max-w-[1440px]`.
    * Disenar cabecera: H1 "Gestionar temporadas y colecciones", migas de pan y boton "<- Volver al Panel Principal".
  - **Criterios Mapeados:** `# AC-15`.
  - **Verificacion:** Navegacion directa y fluida desde el dashboard principal.

- [x] **Tarea 2.5: Pestanas de navegacion, barras reactivas con debounce y tablas maestras**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.html`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.ts`
  - **Descripcion:**
    * Desarrollar conmutador de pestanas reactivas (Temporadas / Colecciones).
    * Crear barras de filtros reactivas con debounce de 300 ms, selectores de estado/ano/temporada y boton de limpieza.
    * Desarrollar tabla maestra de temporadas (fechas legibles, badge activo/inactivo, conteo de colecciones, botones de edicion y baja logica).
    * Desarrollar tabla maestra de colecciones (concepto capsula, temporada asociada, estado, acciones).
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`, `# AC-18`, `# AC-19`.
  - **Verificacion:** Filtrado reactivo en tiempo real y conmutacion fluida de pestanas.

- [x] **Tarea 2.6: Modales reactivos, Luxury Banners y suite unitaria Vitest**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.html`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.ts`
    - `Ec-frontend/src/app/modules/catalogo/cu24_temporadas_colecciones/paginas/temporadas-colecciones-admin.component.spec.ts`
  - **Descripcion:**
    * Disenar modales reactivos con `NonNullableFormBuilder`:
      - Modal de Temporada con validador sincrono de rango de fechas `fechaFin > fechaInicio`.
      - Modal de Coleccion con selector dinamico de temporada matriz.
    * Disenar Luxury Banners para gestion no destructiva de errores HTTP 409 y 422.
    * Crear suite unitaria `temporadas-colecciones-admin.component.spec.ts` cubriendo los criterios `# AC-14` al `# AC-23`.
  - **Criterios Mapeados:** `# AC-20`, `# AC-21`, `# AC-22`, `# AC-23`.
  - **Verificacion:** 100% de tests de frontend en verde con `ng test`.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada de suites automatizadas locales y auditoria de entorno**
  - **Comandos / Archivos:**
    - Backend: `.venv\Scripts\pytest.exe -v`
    - Frontend: `npm test -- --watch=false`
    - Compilacion: `npm run build`
    - Auditoria lexica: verificacion de 0 emojis en codigo fuente y bitacoras.
  - **Descripcion:**
    * Ejecutar la totalidad de pruebas unitarias y de integracion de backend garantizando cero regresiones.
    * Ejecutar la suite completa de pruebas unitarias de frontend en Vitest.
    * Compilar bundle de produccion de Angular asegurando cero advertencias y cero errores de tipos o plantillas.
    * Realizar escaneo lexico estricto confirmando la ausencia total de emojis.
  - **Verificacion:** 100% de pruebas en verde y cero emojis detectados.

- [x] **Tarea 3.2: Promocion de artefactos hacia `.specs/finalized/CU24/` y modulo permanente**
  - **Archivos:**
    - `.specs/finalized/CU24/spec.md`
    - `.specs/finalized/CU24/design.md`
    - `.specs/finalized/CU24/tasks.md`
    - `.specs/modules/catalogo/CU24-gestionar-temporadas-colecciones.md`
  - **Descripcion:**
    * Promocionar formalmente los artefactos aprobados a `.specs/finalized/CU24/`.
    * Consolidar la especificacion permanente en `.specs/modules/catalogo/CU24-gestionar-temporadas-colecciones.md`.
    * Purgar el directorio temporal `.specs/changes/CU24/` preservando `.specs/changes/.gitkeep`.
  - **Verificacion:** Sincronizacion documental completa en la linea base de especificaciones.

- [x] **Tarea 3.3: Registro formal del incremento funcional en CHANGELOGs (v2.3.0)**
  - **Archivos:**
    - `CHANGELOG.md`
    - `.specs/CHANGELOG.md`
  - **Descripcion:**
    * Registrar el incremento funcional bajo la version 2.3.0 documentando los componentes de temporadas y colecciones.
    * Asentar la ratificacion documental de la exclusion justificada de `Ec-mobile`.
  - **Verificacion:** Bitacoras institucionales actualizadas y auditadas.

---

## 2. Matriz de Trazabilidad Criterios EARS vs. Tareas de Implementacion

| Criterio EARS | Descripcion Sintetica | Capa | Tarea(s) Asignada(s) |
| :--- | :--- | :--- | :--- |
| **# AC-1** | Autenticacion Obligatoria JWT (401) | Backend | Tarea 1.5, Tarea 1.6 |
| **# AC-2** | Control de Acceso RBAC por Rol (403) | Backend | Tarea 1.5, Tarea 1.6 |
| **# AC-3** | Segregacion Funcional de Operacion | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-4** | Estructura de Entidad Temporada | Backend | Tarea 1.1, Tarea 1.2 |
| **# AC-5** | Validacion de Cronograma de Temporada (422) | Backend | Tarea 1.2, Tarea 1.3, Tarea 1.6 |
| **# AC-6** | Validacion de Unicidad de Nombre de Temporada (409) | Backend | Tarea 1.1, Tarea 1.3, Tarea 1.4, Tarea 1.6 |
| **# AC-7** | Listado Paginado y Filtrado de Temporadas (200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-8** | Baja Logica y Reactivacion de Temporada (PATCH 200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-9** | Estructura de Entidad Coleccion | Backend | Tarea 1.1, Tarea 1.2 |
| **# AC-10** | Unicidad de Coleccion por Temporada (409) | Backend | Tarea 1.1, Tarea 1.3, Tarea 1.4, Tarea 1.6 |
| **# AC-11** | Integridad de Temporada Matriz (404 / 422) | Backend | Tarea 1.3, Tarea 1.4, Tarea 1.6 |
| **# AC-12** | Listado Paginado de Colecciones con Join (200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-13** | Baja Logica de Coleccion (PATCH 200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-14** | Tarjeta en AdminDashboardComponent | Frontend | Tarea 2.3 |
| **# AC-15** | Layout Editorial y Cabecera de la Vista | Frontend | Tarea 2.4 |
| **# AC-16** | Sistema de Pestanas Reactivas | Frontend | Tarea 2.2, Tarea 2.5 |
| **# AC-17** | Barra de Filtros con Debounce (300 ms) | Frontend | Tarea 2.2, Tarea 2.5 |
| **# AC-18** | Tabla Maestra de Temporadas | Frontend | Tarea 2.1, Tarea 2.5 |
| **# AC-19** | Tabla Maestra de Colecciones y Capsulas | Frontend | Tarea 2.1, Tarea 2.5 |
| **# AC-20** | Modal Reactivo con Validacion de Fechas | Frontend | Tarea 2.6 |
| **# AC-21** | Modal Reactivo de Coleccion | Frontend | Tarea 2.6 |
| **# AC-22** | Luxury Banners No Destructivos | Frontend | Tarea 2.2, Tarea 2.6 |
| **# AC-23** | Paginacion y Estados de Carga | Frontend | Tarea 2.2, Tarea 2.5, Tarea 2.6 |

---

## 3. Definicion de Terminado (Definition of Done - DoD) para Fase 3

La Fase 3 (Plan de Tareas) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU24/tasks.md` se encuentre debidamente guardado en el repositorio local.
2. Todas las casillas de tareas se encuentren en estado pendiente `[ ]` listas para su ejecucion.
3. Se mantenga estrictamente la denominacion oficial: *"Gestionar temporadas y colecciones"*.
4. Se haya auditado que el documento carece al 100% de caracteres emoji o informales.
5. No se haya generado ni modificado codigo productivo en `Ec-backend`, `Ec-frontend` o `Ec-mobile`.
6. El usuario apruebe formalmente esta planificacion para autorizar el inicio de la ejecucion de la **Oleada 1: Backend**.
