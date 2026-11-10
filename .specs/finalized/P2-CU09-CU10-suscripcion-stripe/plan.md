# Plan Técnico de Implementación: `P2-CU09-CU10-suscripcion-stripe`

## 1. Arquitectura y Diseño por Capas

### 1.1 Base de Datos y Migraciones
- Las tablas `planes`, `funcionalidades`, `plan_funcionalidades`, `suscripciones`, `historial_suscripcion` y `configuracion_tenant` ya existen en las migraciones `0012` y `0013`.
- No se requiere una nueva migración de esquema para `CU09` ni `CU10`.

### 1.2 Backend (`Ec-backend/app/modules/plataforma/cu09_cu10_suscripcion_empresa/`)
Siguiendo el patrón de capas estrictas (`Router -> Servicio -> Repositorio -> ORM`):
- `esquemas.py`:
  - `EmpresaSuscripcionInfoOut`, `SuscripcionEmpresaDetalleOut`, `UsoRecursoPlanOut`, `SucursalActivaResumenOut`, `UsoPlanEmpresaOut`, `FuncionalidadPlanEmpresaOut`, `HistorialMiSuscripcionOut`, `MiSuscripcionResumenOut`.
  - `PlanDisponibleEmpresaOut`, `IniciarPagoSuscripcionIn`, `IntentoPagoSuscripcionOut`, `ConfirmarCambioSuscripcionIn`.
- `repositorio.py`:
  - Consultas para obtener la empresa (`TenantORM`), moneda en `ConfiguracionTenantORM`, suscripción actual (`SuscripcionORM`), plan (`PlanORM`), todas las funcionalidades (`FuncionalidadORM`) y las asociadas a cada plan (`PlanFuncionalidadORM`), conteo y listado de sucursales activas (`fashionstore.sucursales`), conteo de empleados activos (`fashionstore.usuarios`), e historial (`HistorialSuscripcionORM`).
  - Escritura atómica en `suscripciones` e `historial_suscripcion`.
- `servicio.py`:
  - `MiSuscripcionServicio`:
    - `consultar_mi_suscripcion(db, usuario)`: resuelve `id_tenant`, calcula días restantes, vigencia y banderas `proxima_a_vencer` (`0 <= dias_restantes <= 7`) y `al_limite`, arma funcionalidades incluidas/no incluidas e historial.
    - `listar_planes_disponibles(db, usuario)`: devuelve planes activos con `es_plan_actual`, `compatible_con_uso_actual` y `motivo_incompatibilidad`.
    - `iniciar_pago(db, datos, usuario)`: valida `CU10 A1` (uso actual vs límites del plan destino) e invoca `StripeService.crear_intento(...)`.
    - `confirmar_cambio_o_renovacion(db, datos, usuario, ip)`: revalida `CU10 A1`, verifica el pago con `StripeService.verificar_intento(...)` (`CU10 A2` -> `402 PAGO_RECHAZADO`), actualiza `SuscripcionORM`, inserta `HistorialSuscripcionORM` (`RN17`), escribe en `bitacora` y limpia caché de tenants.
- `router.py`:
  - `GET /mi-suscripcion`
  - `GET /mi-suscripcion/planes`
  - `POST /mi-suscripcion/iniciar-pago`
  - `POST /mi-suscripcion/confirmar`
- Registro por adición en `Ec-backend/app/modules/plataforma/router.py`.

### 1.3 Frontend Web (`Ec-frontend/src/app/modules/plataforma/mi_suscripcion/`)
- `modelos/mi-suscripcion.model.ts`: Interfaces TypeScript alineadas 1:1 con los esquemas Pydantic.
- `servicios/mi-suscripcion.service.ts`: Servicio Angular con `HttpClient` hacia `/api/v1/plataforma/mi-suscripcion`.
- `paginas/mi-suscripcion-admin.component.{ts,html,scss,spec.ts}`:
  - Basado en Angular 19 Standalone + Signals + Tailwind CSS con estética editorial luxury (`#0F172A`, `#AD8C63`).
  - Sección 1 (`CU09`): Banner de alerta si la suscripción está vencida o próxima a vencer (`CU09 A1`), tarjeta del plan actual y vigencia, medidores de uso de sucursales activas y empleados activos con aviso cuando se llega al tope (`CU09 A2`), lista de sucursales activas y matriz de funcionalidades incluidas / no incluidas.
  - Sección 2 (`CU10`): Comparador de planes disponibles con indicador de compatibilidad (`CU10 A1`), selector de período (`1`, `3`, `6`, `12` meses), flujo de pago con Stripe en dos pasos (`Iniciar pago` -> `Confirmar cobro Stripe`) con selector de escenario de prueba (`exito`, `rechazado`, `fondos_insuficientes`) para demostrar el curso normal y el curso alterno `CU10 A2`.
  - Sección 3 (`CU09` / `RN17`): Tabla cronológica del historial de suscripción de la empresa.
- `app.routes.ts`: Adición de la ruta `/admin/suscripcion` con `canActivate: [authGuard, adminOnlyGuard]` antes del comodín `:codigo`.
- `admin-dashboard.component.html`: Adición de la tarjeta corporativa **"Mi suscripción y facturación"** exclusiva para `esAdmin()`.

