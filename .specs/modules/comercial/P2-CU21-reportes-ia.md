# Especificación Técnica Permanente: Generación de Reportes con IA — P2-CU21

**Fuente:** `SI2-Parcial2.md` (CU21, RF31, RNF18, RNF19, RN44, RN45, RN46, RN47, RN48, PF-19) y `Repartición.md`.
**Paquete de Dominio:** `comercial` (`cu21_reportes_ia`)
**Backend:** Migración `0018_catalogo_reportes_ia.py` · `app/modules/comercial/cu21_reportes_ia/`
**Frontend:** `/admin/reportes-ia` (rol `administrador`)
**Mobile:** sin cambios
**Depende de:** `P2-CU12` (`validar('reportes_ia')`), `P2-CU22` (`catalogo_reportes_ia`)
**Estado:** 🟢 Aprobado y verificado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU22-CU21-reportes-ia/`

---

## 1. Decisiones Clave y Reglas de Seguridad

| ID | Regla |
| :--- | :--- |
| R1 | Seguridad semántica y RLS (RN45, RN46): A la IA solo se envían el prompt en lenguaje natural y la lista de nombres y ejemplos del catálogo permitido. Jamás se transmiten datos del negocio, contraseñas ni filas de base de datos. Las consultas SQL parametrizadas filtran estrictamente por `id_tenant`. |
| R2 | Rechazo de reportes desconocidos (Punto 6 Auditoría): Si el código solicitado no cuenta con un ejecutor SQL controlado en el servicio, se rechaza inmediatamente con `422 REPORTE_NO_EJECUTABLE` sin caer jamás por omisión en consultas de reservas ni de ninguna otra vista. |
| R3 | Detección de ambigüedad (`CU21 A1`) y no soportados (`CU21 A2`): Respuestas con sugerencias y ejemplos sin ejecutar consultas incompletas. |
| R4 | Moneda y exportación: Ingresos y valorizaciones en Bolivianos (`Bs. / BOB`), con desglose en PDF y Excel (`openpyxl` / `reportlab`). |

## 2. Contratos de API (`/api/v1/reportes-ia/...`)

- `GET /api/v1/reportes-ia/contexto` — Catálogo activo, moneda y ejemplos de consulta.
- `POST /api/v1/reportes-ia/generar` — Interpreta el prompt con Gemini / fallback determinista, ejecuta la consulta controlada y retorna datos, KPIs y serie para gráficos.
- `GET /api/v1/reportes-ia/historial` — Historial de solicitudes de la empresa.
- `GET /api/v1/reportes-ia/solicitudes/{id}/exportar` — Descarga en formato `pdf` o `excel`.

## 3. Pruebas y Cobertura

- Suite unitaria: `Ec-backend/tests/modules/comercial/test_p2_cu22_cu21_reportes_ia_unitarias.py` (10 pruebas en verde).
