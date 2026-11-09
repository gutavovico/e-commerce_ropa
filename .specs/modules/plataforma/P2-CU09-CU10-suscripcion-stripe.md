# Especificación Técnica Permanente: Mi Suscripción y Pasarela Stripe (P2-CU09 · P2-CU10)

**Fuente:** `SI2-Parcial2.md` (CU09, CU10, RF04, RF05, RF06, RN09, RN13, RN14, RN15, RN16, RN18; PF-15 a PF-17) y `Repartición.md`.
**Paquete de Dominio:** `plataforma` (`cu09_cu10_suscripcion_empresa`)
**Backend:** Migración `0017_superadmin_catalogos.py` (con índice único parcial `uq_historial_suscripcion_referencia_pago`) · `app/modules/plataforma/cu09_cu10_suscripcion_empresa/`
**Frontend:** `src/app/modules/plataforma/mi_suscripcion/` · ruta `/admin/suscripcion` (rol `administrador`)
**Mobile:** sin cambios
**Depende de:** `P2-CU13-CU12-fundacion-multitenant` y pasarela `StripeService`
**Estado:** 🟢 Aprobado y verificado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU09-CU10-suscripcion-stripe/`

---

## 1. Decisiones Clave y Reglas de Negocio

| ID | Regla |
| :--- | :--- |
| S1 | Moneda directa BOB: Todos los planes se cotizan y cobran directamente en Bolivianos (`BOB`), sin conversiones manuales a USD ni tasas fijas de cambio. La moneda se transmite a Stripe en minúsculas (`bob`). |
| S2 | Vinculación estricta de pago: Al confirmar un cambio o renovación (`confirmar_cambio_o_renovacion`), el backend coteja rigurosamente que el `PaymentIntent` de Stripe corresponda a la solicitud: `amount == monto_total`, `currency == moneda`, `metadata.id_tenant == tenant.id_tenant`, `metadata.id_plan == datos.id_plan` y `metadata.meses == datos.meses`. |
| S3 | Anti-reutilización de pagos: Cada `referencia_pago` de Stripe solo puede utilizarse una única vez. Se valida a nivel de base de datos (`uq_historial_suscripcion_referencia_pago`) y en servicio (409 `REFERENCIA_PAGO_YA_UTILIZADA`). |
| S4 | Fechas en hora boliviana: Cálculo de vigencia y días restantes utilizando `core.tiempo.hoy()`. |

## 2. Contratos de API (`/api/v1/admin/mi-suscripcion/...`)

- `GET /api/v1/admin/mi-suscripcion` — Información completa del plan actual, estado, días restantes, uso de recursos vs límites y lista de planes disponibles.
- `GET /api/v1/admin/mi-suscripcion/historial` — Historial de eventos y renovaciones de la empresa.
- `POST /api/v1/admin/mi-suscripcion/crear-intento` — Genera un `PaymentIntent` en Stripe con metadatos de tenant, plan y meses.
- `POST /api/v1/admin/mi-suscripcion/confirmar` — Verifica el pago en Stripe, actualiza la suscripción atómicamente y registra el evento en `historial_suscripcion`.

## 3. Pruebas y Cobertura

- Suite unitaria: `Ec-backend/tests/modules/plataforma/test_p2_cu09_cu10_unitarias.py` (10 pruebas en verde).
