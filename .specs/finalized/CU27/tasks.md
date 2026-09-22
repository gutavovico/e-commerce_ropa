# Plan de Tareas: [CU27] Gestionar promociones

**Caso de Uso:** CU27  
**Denominacion Oficial:** Gestionar promociones  
**Modulo:** Gestion Comercial / Marketing y Descuentos (`gestion_operativa` / `gestion_comercial`)  
**Metodologia:** Spec-Driven Development (SDD)  
**Estado:** Planificacion Completada (Fase 3)  

---

## 1. Estructura de Oleadas de Implementacion

### Oleada 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

- [x] **Tarea 1.1: Migracion Alembic idempotente y modelo ORM en `app/modules/comercial/cu27_promociones/modelos.py`**
  - **Archivos:**
    - `Ec-backend/alembic/versions/0008_cu27_promociones.py`
    - `Ec-backend/app/modules/comercial/cu27_promociones/modelos.py`
    - `Ec-backend/app/modules/comercial/cu27_promociones/__init__.py`
    - `Ec-backend/app/modules/comercial/modelos.py`
  - **Descripcion:**
    * Crear la migracion Alembic `0008_cu27_promociones.py` para la tabla `fashionstore.promociones` con columnas de vigencia, tipo de descuento, topes, limites de uso, alcance relacional hacia categorias y productos, restricciones `CHECK` (`fecha_fin > fecha_inicio`, tipos validos, porcentaje entre 1 y 100) e indice unico funcional insensible a mayusculas sobre `codigo_cupon`.
    * Modelar `PromocionORM` en SQLAlchemy 2.0 con mapeo `Mapped` y relaciones a `CategoriaORM` y `ProductoORM`.
  - **Criterios Mapeados:** `# AC-4`, `# AC-5`, `# AC-6`, `# AC-7`, `# AC-8`.
  - **Verificacion:** Ejecucion de `alembic upgrade head` sin errores en PostgreSQL Neon.

- [x] **Tarea 1.2: Esquemas Pydantic v2 en `app/modules/comercial/cu27_promociones/esquemas.py`**
  - **Archivo:** `Ec-backend/app/modules/comercial/cu27_promociones/esquemas.py`
  - **Descripcion:**
    * Implementar DTOs de entrada y salida: `PromocionCrearIn`, `PromocionActualizarIn`, `EstadoConmutarIn`, `PromocionItemOut`, `MetricasPromocionesOut`, `RespuestaPaginadaPromocionesOut` y `PromocionFiltrosIn`.
    * Implementar `@field_validator` para normalizacion automatica de `codigo_cupon` en mayusculas y recorte de espacios en `nombre`.
    * Implementar `@model_validator(mode="after")` para asegurar consistencia de fechas (`fecha_fin > fecha_inicio`), rango porcentual (1 a 100) y consistencia de IDs segun el `alcance`.
  - **Criterios Mapeados:** `# AC-4`, `# AC-5`, `# AC-6`, `# AC-7`, `# AC-8`.
  - **Verificacion:** Pruebas unitarias de esquemas y rechazo 422 ante fechas invertidas o porcentajes anomalos.

- [x] **Tarea 1.3: Jerarquia de excepciones semanticas de dominio en `app/modules/comercial/cu27_promociones/errores.py`**
  - **Archivo:** `Ec-backend/app/modules/comercial/cu27_promociones/errores.py`
  - **Descripcion:**
    * Definir clase base `PromocionError(DomainError)`.
    * Implementar `PromocionNoEncontradaError` (404), `CodigoCuponDuplicadoError` (409), `FechasPromocionInvalidasError` (422), `ValorDescuentoInvalidoError` (422) y `AlcancePromocionInvalidoError` (422).
  - **Criterios Mapeados:** `# AC-5`, `# AC-6`, `# AC-7`, `# AC-8`, `# AC-10`.
  - **Verificacion:** Emision de respuestas HTTP estructuradas con `detail` y `code`.

- [x] **Tarea 1.4: Capa de servicio transaccional en `app/modules/comercial/cu27_promociones/servicio.py`**
  - **Archivo:** `Ec-backend/app/modules/comercial/cu27_promociones/servicio.py`
  - **Descripcion:**
    * Implementar `ServicioGestionPromociones` con metodos:
      - `listar_promociones`: consulta paginada con filtros multicriterio (`q`, `tipo_descuento`, `estado_activo`, `alcance`, `ordenar_por`) y subconsulta determinista de conteo.
      - `obtener_promocion_por_id`: recuperacion detallada con relaciones.
      - `crear_promocion`: validacion de unicidad de cupon, verificacion de entidad referenciada por alcance y persistencia.
      - `actualizar_promocion`: modificacion integral excluyendo el propio ID en la validacion de cupon.
      - `conmutar_estado`: baja logica o reactivacion conmutando `estado_activo`.
      - `obtener_metricas`: calculo cuantitativo de campanas activas, cupones vigentes, descuento promedio y usos totales.
  - **Criterios Mapeados:** `# AC-3`, `# AC-7`, `# AC-9`, `# AC-10`, `# AC-11`, `# AC-12`, `# AC-13`.
  - **Verificacion:** Pruebas de integracion transaccionales en base de datos.

- [x] **Tarea 1.5: Router REST y montaje en el agregador comercial**
  - **Archivos:**
    - `Ec-backend/app/modules/comercial/cu27_promociones/router.py`
    - `Ec-backend/app/modules/comercial/router.py`
    - `Ec-backend/app/main.py`
  - **Descripcion:**
    * Exponer endpoints bajo `/api/v1/admin/promociones`:
      - `GET /`: Listado paginado y metricas.
      - `GET /{id}`: Detalle individual.
      - `POST /`: Creacion de promocion o cupon.
      - `PUT /{id}`: Modificacion de campana.
      - `PATCH /{id}/estado`: Conmutacion de estado (baja logica).
    * Custodiar rutas de lectura con `require_roles(["administrador", "encargado_sucursal"])` y rutas de mutacion con `require_roles(["administrador"])`.
    * Incluir el router en `app/modules/comercial/router.py` y registrarlo en `app/main.py`.
  - **Criterios Mapeados:** `# AC-1`, `# AC-2`, `# AC-3`, `# AC-9`, `# AC-10`, `# AC-11`, `# AC-12`, `# AC-13`.
  - **Verificacion:** Verificacion de endpoints y esquemas en documentacion OpenAPI (`/docs`).

- [x] **Tarea 1.6: Suite de pruebas automatizadas Pytest en `tests/modules/comercial/test_cu27_promociones.py`**
  - **Archivo:** `Ec-backend/tests/modules/comercial/test_cu27_promociones.py`
  - **Descripcion:**
    * Crear suite de pruebas exhaustiva cubriendo 16 escenarios criticos:
      1. Rechazo sin token de acceso (HTTP 401).
      2. Bloqueo de usuario con rol cajero (HTTP 403).
      3. Bloqueo de usuario con rol cliente (HTTP 403).
      4. Acceso de consulta exitoso para encargado de sucursal (HTTP 200).
      5. Bloqueo de mutacion POST para encargado de sucursal (HTTP 403).
      6. Alta de promocion global porcentual con tope maximo (HTTP 201).
      7. Alta de cupon promocional con monto fijo y normalizacion a mayusculas (HTTP 201).
      8. Rechazo de codigo de cupon duplicado case-insensitive (HTTP 409).
      9. Rechazo de fechas incongruentes `fecha_fin <= fecha_inicio` (HTTP 422).
      10. Rechazo de porcentaje de descuento superior al 100% o menor/igual a 0 (HTTP 422).
      11. Rechazo de alcance por categoria sin asociar categoria valida (HTTP 422).
      12. Listado paginado con filtros multicriterio y calculo de metricas (HTTP 200).
      13. Detalle individual de promocion existente (HTTP 200).
      14. Detalle individual de promocion inexistente (HTTP 404).
      15. Actualizacion completa de promocion (HTTP 200).
      16. Conmutacion de estado y baja logica no destructiva (PATCH HTTP 200).
  - **Criterios Mapeados:** `# AC-1` al `# AC-13`.
  - **Verificacion:** 100% de tests en verde con `pytest`.

---

### Oleada 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- [x] **Tarea 2.1: Modelos e interfaces TypeScript DTO en `src/app/modules/comercial/cu27_promociones/modelos/promociones.dto.ts`**
  - **Archivo:** `Ec-frontend/src/app/modules/comercial/cu27_promociones/modelos/promociones.dto.ts`
  - **Descripcion:**
    * Definir tipos e interfaces TypeScript fuertemente tipados: `TipoDescuento`, `AlcancePromocion`, `EstadoVigencia`, `PromocionItem`, `MetricasPromociones`, `RespuestaPaginadaPromociones`, `PromocionCrearDto`, `PromocionActualizarDto`, `FiltrosPromociones` y `EstadoConmutarDto`.
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`, `# AC-18`.
  - **Verificacion:** Compilacion limpia sin errores de tipado en TypeScript.

- [x] **Tarea 2.2: Servicio HTTP reactivo con Angular Signals y suite unitaria en `promociones-admin.service.ts`**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/servicios/promociones-admin.service.ts`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/servicios/promociones-admin.service.spec.ts`
  - **Descripcion:**
    * Implementar servicio inyectable en root consumiendo la API `/api/v1/admin/promociones`.
    * Gestionar estado reactivo centralizado con Signals: `promociones`, `metricas`, `totalPromociones`, `totalPaginas`, `cargando`, `guardando`, `error`, `mensajeExito`, `filtros`.
    * Desarrollar suite unitaria con `provideHttpClientTesting()` validando llamadas HTTP, paso de tokens JWT y captura no destructiva de errores 409 y 422.
  - **Criterios Mapeados:** `# AC-9`, `# AC-11`, `# AC-12`, `# AC-13`, `# AC-21`.
  - **Verificacion:** Pruebas unitarias de servicio ejecutandose al 100% en verde con `ng test`.

- [x] **Tarea 2.3: Incorporacion de la novena tarjeta corporativa en `AdminDashboardComponent`**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.html`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.ts`
    - `Ec-frontend/src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  - **Descripcion:**
    * Anadir tarjeta boutique bajo la categoria "Gestion Comercial":
      - Titulo oficial: `"Gestionar promociones"`.
      - Descripcion: `"Parametrizacion de campanas comerciales, descuentos porcentuales, cupones y limites de canje."`.
      - Badge: `"Marketing y Descuentos"`.
      - Boton: `id="btn-gestionar-promociones"` con `routerLink="/admin/promociones"` y `(click)="navegar('/admin/promociones', $event)"`.
      - Icono vectorial SVG corporativo (sin emojis).
      - Condicional RBAC: `@if (esAdmin() || esEncargado())`.
    * Actualizar total de modulos activos en el controlador (`9 Activos` para admin, `7 Activos` para encargado).
    * Actualizar `admin-dashboard.component.spec.ts` verificando renderizado, rol y navegacion.
  - **Criterios Mapeados:** `# AC-14`.
  - **Verificacion:** Suite de pruebas del dashboard pasando en verde.

- [x] **Tarea 2.4: Componente Standalone `PromocionesAdminComponent` y registro de ruta en `app.routes.ts`**
  - **Archivos:**
    - `Ec-frontend/src/app/app.routes.ts`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.ts`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.html`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.scss`
  - **Descripcion:**
    * Registrar ruta `/admin/promociones` en `app.routes.ts` con guards `[authGuard, roleGuard(['administrador', 'encargado_sucursal'])]`.
    * Construir `PromocionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y layout editorial `max-w-[1440px]`.
    * Disenar cabecera institucional: H1 "Gestionar promociones", breadcrumb y boton "Volver al Panel Principal".
  - **Criterios Mapeados:** `# AC-15`.
  - **Verificacion:** Navegacion directa y fluida desde el dashboard principal.

- [x] **Tarea 2.5: Rejilla de metricas de red, barra reactiva con debounce y tabla maestra corporativa**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.html`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.ts`
  - **Descripcion:**
    * Implementar las 4 tarjetas de KPIs superiores (Promociones Activas, Cupones Vigentes, Descuento Promedio, Usos Acumulados).
    * Crear barra de filtros reactiva con debounce de 300 ms (`q`, `tipo_descuento`, `estado_activo`, `alcance`, boton de reinicio).
    * Construir tabla maestra con badges cromaticos de vigencia (`Vigente`, `Proxima`, `Expirada`), chip monoespaciado de cupon, columna de canjes y acciones operativas.
  - **Criterios Mapeados:** `# AC-16`, `# AC-17`, `# AC-18`, `# AC-22`.
  - **Verificacion:** Filtrado reactivo en tiempo real y visualizacion correcta de datos.

- [x] **Tarea 2.6: Modales reactivos, Luxury Banners no destructivos y suite unitaria Vitest**
  - **Archivos:**
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.html`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.ts`
    - `Ec-frontend/src/app/modules/comercial/cu27_promociones/paginas/promociones-admin.component.spec.ts`
  - **Descripcion:**
    * Disenar modal reactivo con `NonNullableFormBuilder` para creacion y edicion de promociones:
      - Validador sincronico inline de fechas `fecha_fin > fecha_inicio`.
      - Validacion condicional de porcentaje (1 a 100) y topes monetarios.
    * Disenar modal de confirmacion para baja logica y reactivacion.
    * Disenar Luxury Banners para captura no destructiva de colisiones 409 y errores 422.
    * Crear suite unitaria `promociones-admin.component.spec.ts` con cobertura de los criterios `# AC-14` al `# AC-22`.
  - **Criterios Mapeados:** `# AC-19`, `# AC-20`, `# AC-21`, `# AC-22`.
  - **Verificacion:** 100% de pruebas de frontend en verde con `ng test`.

---

### Oleada 3: Cierre, Verificacion Cruzada Integral y Definicion de Terminado (DoD)

- [x] **Tarea 3.1: Revalidacion cruzada de suites automatizadas locales y auditoria de entorno**
  - **Comandos / Archivos:**
    - Backend: `.venv\Scripts\pytest.exe -v`
    - Frontend: `npx ng test --watch=false`
    - Compilacion: `npm run build`
    - Auditoria lexica: verificacion de 0 emojis en codigo fuente y documentacion.
  - **Descripcion:**
    * Ejecutar la totalidad de pruebas automatizadas de backend garantizando cero regresiones.
    * Ejecutar la suite completa de pruebas unitarias de frontend en Vitest.
    * Compilar bundle de produccion de Angular asegurando cero advertencias y cero errores de tipos o plantillas.
    * Realizar escaneo lexico estricto confirmando la ausencia total de emojis.
  - **Verificacion:** 100% de pruebas en verde y cero emojis detectados.

- [x] **Tarea 3.2: Promocion de artefactos hacia `.specs/finalized/CU27/` y modulo permanente**
  - **Archivos:**
    - `.specs/finalized/CU27/spec.md`
    - `.specs/finalized/CU27/design.md`
    - `.specs/finalized/CU27/tasks.md`
    - `.specs/modules/comercial/CU27-gestionar-promociones.md`
  - **Descripcion:**
    * Promocionar formalmente los artefactos aprobados a `.specs/finalized/CU27/`.
    * Consolidar la especificacion permanente en `.specs/modules/comercial/CU27-gestionar-promociones.md`.
    * Purgar el directorio temporal `.specs/changes/CU27/` preservando `.specs/changes/.gitkeep`.
  - **Verificacion:** Sincronizacion documental completa en la linea base de especificaciones.

- [x] **Tarea 3.3: Registro formal del incremento funcional en CHANGELOGs (v2.4.0)**
  - **Archivos:**
    - `CHANGELOG.md`
    - `.specs/CHANGELOG.md`
  - **Descripcion:**
    * Registrar exhaustivamente el incremento funcional bajo la version 2.4.0 documentando la gestion de promociones y campanas de descuento.
    * Asentar la ratificacion documental de la exclusion justificada de `Ec-mobile`.
  - **Verificacion:** Bitacoras institucionales actualizadas y auditadas.

---

## 2. Matriz de Trazabilidad Criterios EARS vs. Tareas de Implementacion

| Criterio EARS | Descripcion Sintetica | Capa | Tarea(s) Asignada(s) |
| :--- | :--- | :--- | :--- |
| **# AC-1** | Autenticacion Obligatoria JWT (401) | Backend | Tarea 1.5, Tarea 1.6 |
| **# AC-2** | Control de Acceso RBAC por Rol (403) | Backend | Tarea 1.5, Tarea 1.6 |
| **# AC-3** | Segregacion Funcional de Operacion | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-4** | Estructura de Entidad Promocion | Backend | Tarea 1.1, Tarea 1.2 |
| **# AC-5** | Validacion Cronologica de Fechas (422) | Backend | Tarea 1.1, Tarea 1.2, Tarea 1.3, Tarea 1.6 |
| **# AC-6** | Validacion de Rango de Descuento (422) | Backend | Tarea 1.1, Tarea 1.2, Tarea 1.3, Tarea 1.6 |
| **# AC-7** | Validacion de Unicidad de Codigo Cupon (409) | Backend | Tarea 1.1, Tarea 1.2, Tarea 1.3, Tarea 1.4, Tarea 1.6 |
| **# AC-8** | Integridad de Alcance Promocional (422) | Backend | Tarea 1.1, Tarea 1.2, Tarea 1.3, Tarea 1.4, Tarea 1.6 |
| **# AC-9** | Listado Paginado con Filtros Multicriterio (200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-10** | Detalle Individual de Promocion (200 / 404) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-11** | Alta de Promocion Comercial (201) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-12** | Modificacion de Promocion (200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-13** | Baja Logica y Conmutacion de Estado (PATCH 200) | Backend | Tarea 1.4, Tarea 1.5, Tarea 1.6 |
| **# AC-14** | Tarjeta Corporativa en AdminDashboardComponent | Frontend | Tarea 2.3 |
| **# AC-15** | Layout Editorial y Cabecera de la Vista | Frontend | Tarea 2.4 |
| **# AC-16** | Tarjetas de KPIs Comerciales de Red | Frontend | Tarea 2.1, Tarea 2.5 |
| **# AC-17** | Barra de Filtros con Debounce (300 ms) | Frontend | Tarea 2.2, Tarea 2.5 |
| **# AC-18** | Tabla Maestra con Badges Cromaticos | Frontend | Tarea 2.1, Tarea 2.5 |
| **# AC-19** | Modal Reactivo con Validacion Sincronica | Frontend | Tarea 2.6 |
| **# AC-20** | Modal de Confirmacion de Baja Logica | Frontend | Tarea 2.6 |
| **# AC-21** | Luxury Banners No Destructivos | Frontend | Tarea 2.2, Tarea 2.6 |
| **# AC-22** | Estados de Carga y Vacio | Frontend | Tarea 2.5, Tarea 2.6 |

---

## 3. Definicion de Terminado (Definition of Done - DoD) para Fase 3

La Fase 3 (Plan de Tareas) se considerara formalmente concluida cuando:
1. El documento `.specs/changes/CU27/tasks.md` se encuentre debidamente registrado en el repositorio local.
2. Todas las casillas de tareas se encuentren en estado pendiente `[ ]` listas para su ejecucion secuencial.
3. Se mantenga estrictamente la denominacion oficial: *"Gestionar promociones"*.
4. Se haya auditado que los tres documentos de especificacion carecen al 100% de caracteres emoji o informales.
5. No se haya generado ni modificado codigo productivo en `Ec-backend`, `Ec-frontend` o `Ec-mobile`.
6. El usuario apruebe formalmente esta planificacion para autorizar el inicio de la ejecucion de la **Oleada 1: Backend**.
