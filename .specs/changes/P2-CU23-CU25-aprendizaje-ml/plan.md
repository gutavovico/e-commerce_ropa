# Plan Técnico de Implementación: `P2-CU23-CU25-aprendizaje-ml`

## 1. Migración Alembic (`0018_aprendizaje_automatico_ml.py`)
- `down_revision = "0017"`
- Tablas en el esquema `fashionstore` con aislamiento por empresa (`id_tenant` + RLS):
  1. `fashionstore.datasets_ml`:
     - `id_dataset` (PK), `id_tenant` (FK a `tenants`), `nombre`, `origen` (`sintetico` | `real` | `mixto`), `cantidad_registros`, `variables_seleccionadas` (JSONB), `parametros_generacion` (JSONB), `resumen_preprocesamiento` (JSONB), `muestra_datos` (JSONB), `creado_por` (FK a `usuarios`), `creado_en`.
  2. `fashionstore.modelos_ml`:
     - `id_modelo` (PK), `id_tenant` (FK a `tenants`), `id_dataset` (FK a `datasets_ml`), `nombre`, `tipo_modelo` (`supervisado` | `no_supervisado`), `algoritmo`, `variable_objetivo` (nullable), `variables_entrada` (JSONB), `origen_datos` (`sintetico` | `real` | `mixto`), `estado` (`entrenando` | `evaluado` | `activo` | `archivado` | `fallido`), `activo` (BOOLEAN), `motivo_error` (TEXT), `metricas_entrenamiento` (JSONB), `metricas_validacion` (JSONB), `metricas_prueba` (JSONB), `creado_por`, `creado_en`, `actualizado_en`.
  3. `fashionstore.predicciones_ml`:
     - `id_prediccion` (PK), `id_tenant` (FK), `id_modelo` (FK a `modelos_ml`), `id_producto` (INT nullable), `nombre_producto` (VARCHAR), `id_sucursal` (INT nullable), `nombre_sucursal` (VARCHAR), `periodo` (VARCHAR), `demanda_esperada` (INT), `ingresos_esperados_bob` (NUMERIC(12,2)), `probabilidad` (NUMERIC(5,4) entre `0` y `1` — `RN50`), `nivel_confianza` (VARCHAR), `creado_en`.
  4. `fashionstore.segmentos_clientes_ml`:
     - `id_segmento` (PK), `id_tenant` (FK), `id_modelo` (FK a `modelos_ml`), `codigo_grupo` (VARCHAR), `nombre_grupo` (VARCHAR), `descripcion` (TEXT), `cantidad_clientes` (INT), `caracteristicas` (JSONB — frecuencia media, recencia días, ticket promedio en `Bs.`, gasto promedio en `Bs.`), `clientes_muestra` (JSONB), `creado_en`.

## 2. Backend (`Ec-backend/app/modules/comercial/cu23_cu25_aprendizaje_ml/`)
- `modelos.py`: Modelos ORM SQLAlchemy 2.0 (`DatasetMlORM`, `ModeloMlORM`, `PrediccionMlORM`, `SegmentoClienteMlORM`).
- `esquemas.py`: DTOs Pydantic v2 para `CU23`, `CU24` y `CU25` con importes en **Bolivianos (`Bs. / BOB`)** y tipo de cambio (`6.96 Bs./USD`).
- `motor_ml.py`: Motor de preprocesamiento, generación sintética, entrenamiento supervisado (regresión/proyección de demanda con probabilidades en `[0, 1]`) y entrenamiento no supervisado (clustering RFM por cuantiles/centroides sobre clientes reales o sintéticos de la empresa).
- `repositorio.py`: Consultas aisladas por `id_tenant`.
- `servicio.py`: Orquestación de `CU23`, `CU24` y `CU25`, validación `SuscripcionServicio.validar`, conversión a Bolivianos (`Bs. / BOB`) y auditoría en bitácora (`RN51`).
- `router.py`: Endpoints REST bajo `/api/v1/aprendizaje-ml` montados en `Ec-backend/app/modules/comercial/router.py`:
  - `GET /api/v1/aprendizaje-ml/resumen` (contexto de datasets, modelos, productos y sucursales de la empresa)
  - `POST /api/v1/aprendizaje-ml/datasets` (`CU23` crear y preprocesar dataset)
  - `POST /api/v1/aprendizaje-ml/modelos/entrenar` (`CU23` entrenar y evaluar modelo supervisado o no supervisado)
  - `PATCH /api/v1/aprendizaje-ml/modelos/{id_modelo}/activar` (`CU23` paso 7 activar modelo)
  - `PATCH /api/v1/aprendizaje-ml/modelos/{id_modelo}/archivar` (`CU23 A5` archivar modelo conservando métricas)
  - `GET /api/v1/aprendizaje-ml/predicciones` (`CU24` consultar predicciones del modelo supervisado activo con filtros)
  - `GET /api/v1/aprendizaje-ml/segmentos` (`CU25` consultar segmentos de clientes del modelo no supervisado activo)

## 3. Frontend Web (`Ec-frontend/src/app/modules/comercial/cu23_cu25_aprendizaje_ml/`)
- Ruta `/admin/aprendizaje-ml` protegida para `administrador`, con 3 pestañas integradas:
  1. **Datos y Modelos (`CU23`)**: Generador de datasets (`sintetico`, `real`, `mixto`), selector de variables con preprocesamiento, entrenamiento de modelos supervisados y no supervisados, tabla comparativa de métricas (`entrenamiento`, `validacion`, `prueba`) y botones de activar/archivar.
  2. **Dashboard de Predicciones (`CU24`)**: Filtros por producto, sucursal y período, aviso cuando el modelo usa datos sintéticos (`CU24 A3`), barras de probabilidad (`0%–100%`, `RN50`), demanda proyectada e ingresos esperados en **Bolivianos (`Bs. / BOB`)** y `USD`.
  3. **Segmentos de Clientes (`CU25`)**: Tarjetas de grupos detectados, métricas del modelo no supervisado, comparador de características (frecuencia, recencia y ticket promedio en **Bolivianos `Bs.`**) y detalle de clientes por segmento.

