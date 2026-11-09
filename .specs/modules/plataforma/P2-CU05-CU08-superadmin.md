# Especificación Técnica Permanente: Panel del Super Administrador SaaS (P2-CU05 · P2-CU06 · P2-CU07 · P2-CU08)

**Fuente:** `SI2-Parcial2.md` (CU05, CU06, CU07, CU08, RF01, RF02, RF07, RF09, RF10, RNF16, RNF17, RN01–RN05, RN08, RN11–RN14, RN17, RN19, RN51; PF-10 a PF-14) y `Repartición.md`.
**Paquete de Dominio:** `plataforma` (`cu05_empresas_supervision`, `cu06_planes_funcionalidades`, `cu07_suscripciones`, `cu08_catalogos_globales`)
**Backend:** Migración `0017_superadmin_catalogos.py` · `app/modules/plataforma/`
**Frontend:** `src/app/modules/plataforma/superadmin/` · ruta `/admin/plataforma` (requiere rol `super_administrador`)
**Mobile:** sin cambios
**Depende de:** `P2-CU13-CU12-fundacion-multitenant` y `P2-CU02-CU01-acceso-por-empresa`
**Estado:** 🟢 Aprobado y verificado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU05-CU08-superadmin/`

---

## 1. Decisiones Clave

| ID | Decisión |
| :--- | :--- |
| S1 | Desactivación en catálogos globales (`CU08 A2`): columna `activo` en `ciudades`, `tallas` y `colores` vía migración `0017`. Borrado físico restringido a elementos no vinculados. |
| S2 | Autenticación y creación de `super_administrador` fuera de banda mediante `scripts/crear_superadmin.py` con Argon2id, sin semillas en código ni migraciones. |
| S3 | Modo plataforma seguro (`core/tenant.py`): solo se activa con token verificado de `super_administrador` invocando `exigir_super_administrador`. |
| S4 | Protección de planes y suscripciones: `CU06 A2` impide desactivar un plan con suscripciones vigentes (`PLAN_CON_EMPRESAS_SUSCRITAS`); `CU07 A1` rechaza dar de alta una suscripción si la empresa ya tiene una activa (`SUSCRIPCION_VIGENTE_EXISTENTE`). |
| S5 | Cálculo de fechas con hora oficial de Bolivia (`core.tiempo.hoy()` y `core.tiempo.ahora()`). |
| S6 | Validación de unicidad de correos de administradores con `correo_ocupado()` llamando a la función `SECURITY DEFINER` de PostgreSQL. |

## 2. Contratos de API (`/api/v1/plataforma/...`)

- `GET /api/v1/plataforma/empresas` — Lista empresas con estado, plan y métricas consolidadas.
- `POST /api/v1/plataforma/empresas` — Registro atómico de empresa, tenant, configuración inicial en BOB, suscripción y usuario administrador.
- `GET /api/v1/plataforma/empresas/{id}` — Detalle completo de una empresa.
- `PUT /api/v1/plataforma/empresas/{id}` — Actualización de datos de contacto.
- `PATCH /api/v1/plataforma/empresas/{id}/estado` — Transición de estado (`activa`, `suspendida`, `baja` — requiere suspensión previa).
- `GET /api/v1/plataforma/metricas` — Indicadores globales de la plataforma SaaS.
- `GET /api/v1/plataforma/planes` y `POST /api/v1/plataforma/planes` — Gestión de planes y funcionalidades.
- `PUT /api/v1/plataforma/planes/{id}` — Edición de límites con cálculo de advertencias para empresas que superen nuevos límites.
- `PATCH /api/v1/plataforma/planes/{id}/estado` — Activar/desactivar plan (valida suscripciones activas).
- `GET /api/v1/plataforma/suscripciones` — Lista de suscripciones de todas las empresas.
- `POST /api/v1/plataforma/suscripciones/{id_tenant}/operar` — Operaciones de alta, renovación, cambio de plan y suspensión con auditoría en `historial_suscripcion`.
- `GET /api/v1/plataforma/catalogos/...` — CRUD de ciudades, tallas y colores globales.
- `GET /api/v1/plataforma/bitacora` — Consulta de la bitácora global de auditoría.

## 3. Pruebas y Cobertura

- Suite unitaria: `Ec-backend/tests/modules/plataforma/test_p2_cu05_cu08_unitarias.py` (22 pruebas en verde).
- Integración multitenant: `Ec-backend/tests/integracion/test_multitenant.py`.
