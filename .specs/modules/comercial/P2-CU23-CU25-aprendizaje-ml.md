# Especificación Técnica Permanente: Aprendizaje Automático — P2-CU23 · P2-CU24 · P2-CU25

**Fuente:** `SI2-Parcial2.md` (CU23, CU24, CU25, RF33, RF34, RF35, RN49, RN50, PF-21 a PF-23) y `Repartición.md`.
**Paquete de Dominio:** `comercial` (`cu23_cu25_aprendizaje_ml`)
**Backend:** Migración `0019_aprendizaje_automatico_ml.py` · `app/modules/comercial/cu23_cu25_aprendizaje_ml/`
**Frontend:** `/admin/aprendizaje-ml` (rol `administrador`)
**Mobile:** sin cambios
**Depende de:** `scikit-learn`, `pandas`, `numpy`, `P2-CU13-CU12-fundacion-multitenant`
**Estado:** 🟢 Aprobado y verificado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU23-CU25-aprendizaje-ml/`

---

## 1. Decisiones Clave y Reglas de Aprendizaje Automático

| ID | Regla |
| :--- | :--- |
| M1 | Cero datos inventados: Todo el preprocesamiento, partición y entrenamiento opera sobre prendas, variantes, sucursales y clientes reales de la empresa en la base de datos PostgreSQL. Se prohíben datos ficticios o hashes sintéticos. |
| M2 | Modelado supervisado con scikit-learn (`CU23` / `CU24`): Partición 70 % entrenamiento, 15 % validación y 15 % prueba (`RN49`) con `train_test_split`. Entrenamiento real mediante `RandomForestRegressor`. Métricas reales: $R^2$, MAE y RMSE. Probabilidades normalizadas en $[0, 1]$ (`RN50`). |
| M3 | Modelado no supervisado con KMeans (`CU25`): Segmentación RFM real de clientes con `StandardScaler` y `KMeans`. Cálculo de métricas reales de agrupamiento (`silhouette_score`, `davies_bouldin_score`, `inertia_`). |
| M4 | Aislamiento multitenant: Todas las tablas ML (`datasets_ml`, `modelos_ml`, `predicciones_ml`, `segmentos_clientes_ml`) cuentan con `id_tenant`, índice y `FORCE ROW LEVEL SECURITY`. |

## 2. Contratos de API (`/api/v1/aprendizaje-ml/...`)

- `POST /api/v1/aprendizaje-ml/datasets/preprocesar` — Construye el dataset y preprocesa variables con pandas y scikit-learn.
- `GET /api/v1/aprendizaje-ml/datasets` — Lista datasets generados de la empresa.
- `POST /api/v1/aprendizaje-ml/modelos/entrenar` — Entrena el modelo supervisado o no supervisado con scikit-learn.
- `GET /api/v1/aprendizaje-ml/modelos` — Modelos entrenados con métricas de evaluación.
- `POST /api/v1/aprendizaje-ml/modelos/{id}/activar` — Pone un modelo en estado activo.
- `GET /api/v1/aprendizaje-ml/predicciones/demanda` — Pronósticos de ventas e ingresos en Bolivianos (`Bs. BOB`).
- `GET /api/v1/aprendizaje-ml/segmentos` — Segmentos RFM de clientes con métricas de cluster.

## 3. Pruebas y Cobertura

- Suite unitaria: `Ec-backend/tests/modules/comercial/test_p2_cu23_cu25_aprendizaje_ml_unitarias.py` (6 pruebas en verde).
- Integración multitenant: `Ec-backend/tests/integracion/test_multitenant.py`.
