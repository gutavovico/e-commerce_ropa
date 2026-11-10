# Especificación Funcional y Técnica: Catálogo de Reportes Permitidos y Generación de Reportes con IA (`P2-CU22` y `P2-CU21`)

## 1. Contexto y Alcance
Este cambio implementa la **Fase 3** del Parcial 2 asignada a **Tony** según `Repartición.md` y `SI2-Parcial2.md`:
- **`P2-CU22` — Gestionar catálogo de reportes permitidos** (Actor: `super_administrador`): Permite definir qué reportes y qué elementos (`métricas`, `dimensiones`, `filtros_permitidos` y `tipos_grafico`) puede usar la IA, asociados exclusivamente a vistas de datos autorizadas (`vw_ventas_por_sucursal`, `vw_inventario_consolidado`, `vw_reservas_pendientes`, `ranking_productos`), evitando consultas libres sobre la base de datos (`RN45`).
- **`P2-CU21` — Generar reporte con IA** (Actor: `administrador` de una empresa con Plan Profesional): Permite solicitar un reporte escribiendo o dictando por voz en lenguaje natural. La IA interpreta la petición contra el catálogo activo de `CU22` (sin recibir datos del negocio), el backend valida el plan (`CU12`: funcionalidad `reportes_ia`, `RN44`), ejecuta una consulta controlada exclusivamente sobre el `id_tenant` del administrador (`RN46`), expresa todos los importes financieros en **Bolivianos (`Bs. / BOB`)** manejando el tipo de cambio oficial (`1 USD = 6.96 Bs.`, `1 EUR = 7.50 Bs.`), muestra el resultado en tabla y gráfico (`barras`, `linea` o `torta`) y permite exportarlo a **PDF** y **Excel (`XLSX`)** (`RN48`) además de consultar el historial de solicitudes (`RN47`).

**Frontera estricta de alcance:**
- **Base de Datos (`Ec-backend/alembic/versions/0018_catalogo_reportes_ia.py`)**: Tabla global `fashionstore.catalogo_reportes_ia` con semilla de 4 reportes permitidos (`RF32`) y columnas de trazabilidad en `fashionstore.solicitudes_reporte_ia`.
- **Backend (`Ec-backend/`)**:
  - `app/modules/plataforma/cu22_catalogo_reportes/` bajo `/api/v1/plataforma/catalogo-reportes` (para `super_administrador`).
  - `app/modules/comercial/cu21_reportes_ia/` bajo `/api/v1/reportes-ia` (para `administrador` de empresa).
- **Frontend Web (`Ec-frontend/`)**:
  - Pestaña o sección **"Catálogo Reportes IA (CU22)"** en `/admin/plataforma` (`SuperadminPanelComponent`).
  - Vista `/admin/reportes-ia` (`ReportesIaAdminComponent`) con entrada por texto y micrófono (Web Speech API), visualización tabular + gráficos (`barras`, `linea`, `torta`), montos en **Bolivianos (`Bs. / BOB`)** con selector/indicador de tipo de cambio, exportación a **PDF / Excel** e historial de solicitudes.
- **Móvil (`Ec-mobile/`)**: **CERO cambios**.

---

## 2. Reglas de Negocio y Cursos Alternos (`SI2-Parcial2.md`)

| Código | Regla / Curso Alterno | Implementación |
|---|---|---|
| **RN44 / CU21 A3** | Solo las empresas con Plan Profesional (funcionalidad `reportes_ia`) y suscripción vigente pueden generar reportes con IA. | Todos los endpoints de `CU21` invocan `SuscripcionServicio.validar(db, funcionalidad="reportes_ia")`. Si la empresa tiene Plan Básico o suscripción vencida, devuelve `403 FUNCIONALIDAD_NO_INCLUIDA` o `403 SUSCRIPCION_NO_VIGENTE`. |
| **RN45 / CU22 A1 / CU22 A2** | Catálogo cerrado de reportes: la IA solo usa reportes del catálogo permitido. En `CU22`, se rechazan vistas de datos no permitidas (**A1**), métricas/dimensiones sin expresión o tipos de gráfico fuera de `{"tabla", "barras", "linea", "torta"}` (**A2**). | Validación estricta en `CatalogoReportesServicio`: vistas permitidas `{"vw_ventas_por_sucursal", "ranking_productos", "vw_inventario_consolidado", "vw_reservas_pendientes"}`; cada métrica y dimensión exige `codigo`, `etiqueta` y `expresion` no vacía; gráficos en `{"tabla", "barras", "linea", "torta"}`. |
| **CU22 A3** | Al desactivar un reporte del catálogo, la IA deja de ofrecerlo y las solicitudes anteriores se conservan. | `PATCH /api/v1/plataforma/catalogo-reportes/{id}/estado` cambia `activo = false` sin borrar `solicitudes_reporte_ia`. |
| **RN46 / CU21 A7** | Todo reporte se limita a los datos de la empresa (`id_tenant`) del administrador que lo pide. Si los filtros piden otra empresa o elementos fuera del catálogo, se rechaza. | Las consultas SQL parametrizadas de `CU21` filtran obligatoriamente por `id_tenant = :id_tenant` además de ejecutarse bajo RLS. Si se solicita un `id_tenant` ajeno o un reporte inactivo/inexistente, se registra como `rechazada` (`422 FILTRO_REPORTE_NO_AUTORIZADO`). |
| **RN47 / CU21 A1 / CU21 A2** | Solicitud ambigua (**A1**) pide precisión; solicitud no soportada (**A2**) se rechaza con mensaje claro y ejemplos; cada solicitud queda registrada con su estado (`completada`, `ambigua`, `no_soportada`, `rechazada`, `error`). | El intérprete IA (`GeminiService` + motor semántico determinista) clasifica la intención y registra siempre la fila en `solicitudes_reporte_ia` con su `estado` y `mensaje_estado`. |
| **RN48** | Salida en tabla, gráfico (`barras`, `linea`, `torta`) o ambos, y exportación a PDF o Excel (`XLSX`) quedando registrada cada exportación. | `POST /api/v1/reportes-ia/generar` devuelve `columnas`, `filas`, `serie_grafico`, `resumen_kpis_bob` (en **Bolivianos `Bs.`** con tipo de cambio) y `GET /api/v1/reportes-ia/solicitudes/{id}/exportar?formato=pdf|excel` genera el archivo binario y anota la exportación en `solicitudes_reporte_ia.exportaciones`. |

---

## 3. Contratos de API

### 3.1 `P2-CU22` (`/api/v1/plataforma/catalogo-reportes` — `super_administrador`)
- `GET /api/v1/plataforma/catalogo-reportes`: Lista todos los reportes del catálogo y las vistas permitidas.
- `POST /api/v1/plataforma/catalogo-reportes`: Crea un nuevo reporte permitido validando vista (`CU22 A1`), expresiones de métricas/dimensiones y tipos de gráfico (`CU22 A2`), registrando en `bitacora`.
- `PUT /api/v1/plataforma/catalogo-reportes/{id_reporte}`: Actualiza un reporte permitido y registra en `bitacora`.
- `PATCH /api/v1/plataforma/catalogo-reportes/{id_reporte}/estado`: Activa o desactiva un reporte (`CU22 A3`).

### 3.2 `P2-CU21` (`/api/v1/reportes-ia` — `administrador` de empresa con `reportes_ia`)
- `GET /api/v1/reportes-ia/catalogo-activo`: Devuelve los reportes activos del catálogo (`CU22`), ejemplos de consultas en lenguaje natural y la configuración monetaria de la empresa (`moneda`, `tipo_cambio_bob = 6.96` Bs./USD o `7.50` Bs./EUR).
- `POST /api/v1/reportes-ia/generar`:
  - Body: `{ prompt_texto, formato_preferido?, fecha_inicio?, fecha_fin?, id_sucursal?, id_categoria?, moneda_visualizacion?: "BOB" | "USD" | "EUR", tipo_cambio_bob?: Decimal }`.
  - Respuesta: `SolicitudReporteIaResultadoOut` con `id_solicitud`, `estado` (`completada`, `ambigua`, `no_soportada`, `rechazada`, `error`), `mensaje_estado`, `codigo_reporte`, `titulo_reporte`, `interpretacion`, `moneda` (`BOB` / `Bs.`), `tipo_cambio_bob`, `formato_visualizacion`, `columnas`, `filas`, `serie_grafico` (`etiqueta`, `valor`, `valor_bob`), `resumen_kpis_bob` y `ejemplos_sugeridos`.
- `GET /api/v1/reportes-ia/historial`: Lista las solicitudes anteriores de la empresa (`solicitudes_reporte_ia`).
- `GET /api/v1/reportes-ia/solicitudes/{id_solicitud}`: Reconsulta/re-ejecuta una solicitud previa.
- `GET /api/v1/reportes-ia/solicitudes/{id_solicitud}/exportar?formato=pdf|excel`: Exporta el reporte en **PDF** o **Excel (`XLSX`)** con importes en **Bolivianos (`Bs. / BOB`)** y registra la exportación en `solicitudes_reporte_ia.exportaciones` (`RN48`).

---

## 4. Criterios de Aceptación (AC)
- **AC-01 (`CU22` Flujo normal + `RN45`)**: El `super_administrador` puede listar, crear, editar y activar/desactivar reportes del catálogo permitido, registrando cada cambio en `bitacora`.
- **AC-02 (`CU22 A1` y `A2` Validaciones)**: El backend rechaza vistas de datos fuera de la lista blanca (`422 VISTA_DATOS_NO_PERMITIDA`), métricas o dimensiones sin expresión y tipos de gráfico no permitidos (`422 ELEMENTO_REPORTE_INVALIDO`).
- **AC-03 (`CU22 A3` Desactivación)**: Un reporte desactivado deja de ser elegible por la IA en `CU21`, conservando intacto el historial de solicitudes previas.
- **AC-04 (`CU21 A3` / `RN44` Validación de Plan Profesional)**: Si una empresa con Plan Básico (sin `reportes_ia`) o suscripción vencida intenta usar `/api/v1/reportes-ia/*`, `SuscripcionServicio.validar` rechaza con `403 FUNCIONALIDAD_NO_INCLUIDA` o `403 SUSCRIPCION_NO_VIGENTE`.
- **AC-05 (`CU21` Flujo normal + Bolivianos `Bs./BOB`)**: Una petición válida (ej. `"ventas de este mes agrupadas por sucursal"` o `"top productos más vendidos"`) se traduce a uno de los reportes activos del catálogo, ejecuta la consulta controlada sobre el `id_tenant` del usuario, expresa los montos en **Bolivianos (`Bs. / BOB`)** aplicando el tipo de cambio y devuelve tabla + serie de gráfico.
- **AC-06 (`CU21 A1`, `A2` y `A7`)**: Solicitudes ambiguas quedan registradas con `estado = 'ambigua'` pidiendo precisión; solicitudes no soportadas quedan con `estado = 'no_soportada'` y devuelven ejemplos válidos; intentos de consultar otra empresa o un reporte inactivo se rechazan (`estado = 'rechazada'`).
- **AC-07 (`CU21` / `RN48` Exportación PDF y Excel)**: El endpoint de exportación genera archivos binarios PDF (`%PDF`) y Excel (`PK` XLSX) con los montos en **Bolivianos (`Bs.`)** y registra el evento de exportación en la solicitud.
- **AC-08 (Frontend Web)**: Panel de catálogo en `/admin/plataforma` (`CU22`) y centro de reportes con IA en `/admin/reportes-ia` (`CU21`) con entrada por texto y voz, gráficos interactivos (`barras`, `linea`, `torta`), montos en `Bs. (BOB)` y descarga PDF/Excel.

