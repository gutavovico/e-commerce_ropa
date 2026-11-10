# Especificación Técnica Permanente: Catálogo de Reportes Permitidos — P2-CU22

**Fuente:** `SI2-Parcial2.md` (CU22, RF32, RNF18, RNF19, RN45, RN46, PF-20) y `Repartición.md`.
**Paquete de Dominio:** `plataforma` (`cu22_catalogo_reportes`)
**Backend:** Migración `0018_catalogo_reportes_ia.py` · `app/modules/plataforma/cu22_catalogo_reportes/`
**Frontend:** Pestaña "Catálogo Reportes IA" en `/admin/plataforma` (rol `super_administrador`)
**Mobile:** sin cambios
**Depende de:** `P2-CU13-CU12-fundacion-multitenant`
**Estado:** 🟢 Aprobado y verificado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU22-CU21-reportes-ia/`

---

## 1. Decisiones Clave

| ID | Decisión |
| :--- | :--- |
| C1 | Gobierno centralizado del catálogo: Solo el `super_administrador` define los reportes ejecutables mediante el catálogo global `fashionstore.catalogo_reportes_ia`. |
| C2 | Vistas origen autorizadas (`CU22 A1`): Lista blanca estricta (`v_ventas_resumen`, `v_top_productos`, `v_rotacion_inventario`, `v_reservas_sucursal`). Se rechazan intentos de registrar vistas ajenas o SQL libre. |
| C3 | Desactivación sin pérdida de trazabilidad (`CU22 A3`): Los reportes se desactivan con un interruptor lógico; las solicitudes históricas conservan sus referencias íntegras. |

## 2. Contratos de API (`/api/v1/plataforma/catalogo-reportes/...`)

- `GET /api/v1/plataforma/catalogo-reportes` — Lista completa de reportes del catálogo para el superadministrador.
- `POST /api/v1/plataforma/catalogo-reportes` — Registro de un nuevo reporte controlado.
- `PUT /api/v1/plataforma/catalogo-reportes/{id}` — Actualización de metadatos, métricas, dimensiones o ejemplos.
- `PATCH /api/v1/plataforma/catalogo-reportes/{id}/estado` — Activar o desactivar reporte.
