# Especificación Funcional y Técnica (SDD): `P2-CU23`, `P2-CU24` y `P2-CU25` — Aprendizaje Automático (ML)

## 1. Alcance y Casos de Uso (`SI2-Parcial2.md`)

Esta especificación cubre el **Bloque 4 (Aprendizaje Automático)** asignado a **Tony**, integrando:
1. **`P2-CU23` — Gestionar datos y modelos de aprendizaje** (`administrador` de la empresa).
2. **`P2-CU24` — Consultar predicciones** (`administrador` de la empresa — modelo supervisado activo).
3. **`P2-CU25` — Consultar segmentos de clientes** (`administrador` de la empresa — modelo no supervisado activo).

Adicionalmente, todos los importes monetarios (proyección de ingresos esperados en predicciones de demanda y monto total/ticket promedio por segmento de clientes) se expresan en **Bolivianos (`Bs. / BOB`)** con soporte del tipo de cambio oficial del Banco Central de Bolivia (`1 USD = 6.96 Bs.`, `1 EUR = 7.50 Bs.`).

---

## 2. Reglas de Negocio y Cursos Alternos

### 2.1. `P2-CU23` — Gestionar datos y modelos de aprendizaje
- **Flujo Normal**:
  1. El administrador crea un conjunto de datos (`datasets_ml`) eligiendo su origen: `sintetico`, `real` o `mixto` (`RN49`).
  2. Si es `sintetico` o `mixto`, define los parámetros (cantidad de registros simulados, horizonte de meses, semilla) y el sistema genera datos realistas sobre los productos, sucursales y clientes de su empresa (`id_tenant`).
  3. Selecciona las variables (`variables_seleccionadas`) y el sistema ejecuta el preprocesamiento (limpieza de nulos, codificación categórica one-hot/ordinal y escalado estándar `z-score` / `min-max`).
  4. Elige el tipo de modelo (`modelos_ml`):
     - `supervisado`: exige obligatoriamente `variable_objetivo` (`demanda_unidades` o `ingresos_bob`) (`RN49`).
     - `no_supervisado`: segmentación de clientes por comportamiento RFM (Recencia, Frecuencia y Monto en **Bolivianos `Bs.`**) con `numero_clusters` (por defecto 3 o 4).
  5. El sistema entrena el modelo pasando por el estado `entrenando` → `evaluado` y genera las predicciones (`predicciones_ml`) o segmentos (`segmentos_clientes_ml`).
  6. El sistema evalúa el modelo y guarda sus métricas por subconjunto (`metricas_entrenamiento`, `metricas_validacion`, `metricas_prueba` — `RN49`):
     - Supervisado: `r2`, `mae`, `rmse`, `exactitud_confianza`.
     - No supervisado: `silhouette_score`, `inercia`, `davies_bouldin`.
  7. El administrador revisa las métricas y **activa** el modelo (`activo = true`), desactivando cualquier modelo activo anterior del mismo tipo en su empresa.
  8. Cada operación queda registrada en la bitácora (`RN51`).
- **Cursos Alternos**:
  - **CU23 A1 (Datos insuficientes)**: Si la empresa pide origen `real` pero tiene menos de 5 registros históricos de ventas/clientes, el sistema rechaza con `422 DATOS_INSUFICIENTES_ML` y sugiere usar origen `sintetico` o `mixto`.
  - **CU23 A2 (Modelo supervisado sin variable objetivo)**: Si `tipo_modelo == 'supervisado'` y `variable_objetivo` está vacía, rechaza con `422 VARIABLE_OBJETIVO_REQUERIDA` (`RN49`).
  - **CU23 A3 (Fallo de entrenamiento)**: El modelo queda en estado `fallido` con el motivo registrado.
  - **CU23 A4 (Métricas insatisfactorias)**: El administrador conserva el modelo como `evaluado` sin activarlo y puede entrenar otro con distintas variables.
  - **CU23 A5 (Archivar un modelo)**: El modelo pasa a `estado = 'archivado'` y `activo = false`, pero conserva todas sus métricas históricas.

### 2.2. `P2-CU24` — Consultar predicciones (Supervisado)
- **Flujo Normal**:
  1. Muestra el modelo supervisado activo de la empresa, su fecha de entrenamiento, su origen de datos (`sintetico`, `real`, `mixto`) y sus métricas de entrenamiento, validación y prueba (`RN49`).
  2. Permite filtrar por `id_producto`, `id_sucursal` y `periodo` (ej. `proximo_mes`, `proximo_trimestre`, `proximos_6_meses`).
  3. Devuelve las predicciones de demanda esperada (unidades proyectadas e **ingresos proyectados en Bolivianos `Bs. / BOB`** con su equivalente en `USD` a `T.C. 6.96`) junto con su `probabilidad` en el rango `[0.0, 1.0]` (`RN50`).
- **Cursos Alternos**:
  - **CU24 A1 (No hay modelo supervisado activo)**: Informa que no existe un modelo supervisado activo y guía al usuario a la pestaña `CU23` para entrenar/activar uno.
  - **CU24 A2 (No hay predicciones para los filtros elegidos)**: Informa que no existen registros para esa combinación de filtros.
  - **CU24 A3 (Modelo entrenado con datos sintéticos)**: Incluye `aviso_datos_sinteticos = true` y un mensaje visible señalando que las predicciones provienen de un entrenamiento con datos sintéticos o mixtos.

### 2.3. `P2-CU25` — Consultar segmentos de clientes (No Supervisado)
- **Flujo Normal**:
  1. Muestra el modelo no supervisado activo de la empresa y sus métricas (`silhouette_score`, `inercia`, etc.).
  2. Lista los grupos/segmentos detectados (ej. *Clientes VIP Alta Costura*, *Compradoras Frecuentes Omnicanal*, *Clientes Ocasionales / En Riesgo*) con su tamaño (`cantidad_clientes`), descripción y características definitorias (frecuencia media de compra, recencia en días, ticket promedio en **Bolivianos `Bs. / BOB`** y gasto acumulado en **Bs.**).
  3. Al seleccionar un segmento, muestra sus características detalladas y el listado de clientes de la empresa asociados a ese grupo.
- **Cursos Alternos**:
  - **CU25 A1 (No hay modelo no supervisado activo)**: Informa y dirige a `CU23`.
  - **CU25 A2 (Un grupo no tiene clientes)**: Indica explícitamente que el segmento tiene `0` clientes reales asignados.
  - **CU25 A3 (Modelo entrenado con datos sintéticos)**: Señala junto a los resultados que el modelo fue entrenado con datos sintéticos/mixtos.

---

## 3. Criterios de Aceptación (`AC-01` a `AC-08`)

- **`AC-01` (`CU23` Datasets)**: Creación de datasets (`sintetico`, `real`, `mixto`) aislados por `id_tenant` con preprocesamiento de variables y validación `CU23 A1` (`422 DATOS_INSUFICIENTES_ML`).
- **`AC-02` (`CU23` Modelos Supervisados y `A2`)**: Entrenamiento de modelo supervisado exige `variable_objetivo` (`422 VARIABLE_OBJETIVO_REQUERIDA` en `CU23 A2`) y guarda métricas de `entrenamiento`, `validacion` y `prueba` (`RN49`).
- **`AC-03` (`CU23` Modelos No Supervisados)**: Entrenamiento de clustering genera segmentos de clientes con métricas y características en **Bolivianos (`Bs. / BOB`)**.
- **`AC-04` (`CU23` Activar y Archivar `A5`)**: Activar un modelo desactiva el anterior del mismo tipo en la empresa; archivar (`A5`) desactiva el modelo conservando sus métricas.
- **`AC-05` (`CU24` Predicciones y `RN50`)**: Consulta de predicciones del modelo supervisado activo con filtros (`id_producto`, `id_sucursal`, `periodo`), probabilidades en `[0, 1]` (`RN50`), ingresos esperados en **Bolivianos (`Bs.`)** (`T.C. 6.96 Bs./USD`) y aviso de datos sintéticos (`CU24 A3`).
- **`AC-06` (`CU24 A1` y `CU25 A1`)**: Cuando no hay modelo supervisado o no supervisado activo, devuelve estructura clara con `tiene_modelo_activo = false` e indicación de ir a `CU23`.
- **`AC-07` (`CU25` Segmentos de Clientes)**: Consulta de segmentos del modelo no supervisado activo con tamaño, características RFM en **Bolivianos (`Bs.`)**, clientes del grupo y aviso de datos sintéticos (`CU25 A3`).
- **`AC-08` (Aislamiento Multitenant `CU13` y Suscripción `CU12`)**: Toda operación verifica suscripción vigente y filtra estrictamente por `id_tenant`.

