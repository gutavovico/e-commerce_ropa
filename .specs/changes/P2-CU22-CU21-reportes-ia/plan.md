# Plan Técnico de Implementación: `P2-CU22-CU21-reportes-ia`

## 1. Base de Datos y Migración (`0017_catalogo_reportes_ia.py`)
- `down_revision = "0016"`.
- Crea `fashionstore.catalogo_reportes_ia` y siembra de forma idempotente 4 reportes permitidos iniciales (`ventas_por_sucursal`, `top_productos_vendidos`, `inventario_por_sucursal`, `reservas_por_estado_sucursal`).
- Amplía `fashionstore.solicitudes_reporte_ia` con `estado`, `interpretacion`, `formato_visualizacion`, `mensaje_estado` y `exportaciones` (`ADD COLUMN IF NOT EXISTS`).

## 2. Backend (`Ec-backend/`)
1. **`app/modules/plataforma/cu22_catalogo_reportes/`**:
   - `modelos.py`: `CatalogoReporteIaORM`.
   - `esquemas.py`: `ElementoReporteInOut`, `CatalogoReporteCrearIn`, `CatalogoReporteActualizarIn`, `CambiarEstadoReporteIn`, `CatalogoReporteOut`.
   - `repositorio.py` y `servicio.py`: validación de lista blanca de vistas (`CU22 A1`), validación de expresiones y tipos de gráfico (`CU22 A2`), desactivación sin pérdida de historial (`CU22 A3`) y auditoría en `bitacora`.
   - `router.py`: montado en `app/modules/plataforma/router.py` bajo `/catalogo-reportes`.
2. **`app/modules/comercial/cu21_reportes_ia/`**:
   - `modelos.py`: `SolicitudReporteIaORM` (`fashionstore.solicitudes_reporte_ia`).
   - `esquemas.py`: `GenerarReporteIaIn`, `InterpretacionReporteIaOut`, `PuntoGraficoReporteOut`, `SolicitudReporteIaResultadoOut`, `SolicitudReporteIaHistorialOut`.
   - `interprete_ia.py`: Traductor semántico que construye un prompt seguro (solo texto + catálogo activo `CU22`, cero datos de negocio) para `GeminiService` y dispone de un parser determinista en español para fechas, sucursales, tipos de gráfico (`barras`, `linea`, `torta`, `tabla`), detección de solicitudes ambiguas (`CU21 A1`) y no soportadas (`CU21 A2`).
   - `repositorio.py` y `servicio.py`:
     - Valida suscripción y funcionalidad `reportes_ia` con `SuscripcionServicio.validar(db, funcionalidad="reportes_ia")` (`CU21 A3`, `RN44`).
     - Ejecuta las 4 consultas controladas por `id_tenant` (`RN46`) y convierte importes a **Bolivianos (`Bs. / BOB`)** según el tipo de cambio (`6.96 Bs./USD`, `7.50 Bs./EUR`, `1.00 Bs./BOB`).
     - Exporta a PDF (`GeneradorPDF`) y Excel (`GeneradorExcel`) registrando la exportación en `solicitudes_reporte_ia.exportaciones` (`RN48`).
   - `router.py`: montado en `app/modules/comercial/router.py` bajo `/reportes-ia`.

## 3. Frontend Web (`Ec-frontend/`)
1. **Superadmin (`CU22`)**: En `SuperadminService` y `SuperadminPanelComponent` (`/admin/plataforma`), añadir pestaña **"Catálogo Reportes IA (CU22)"** para listar, crear, editar y activar/desactivar reportes permitidos.
2. **Administrador de Empresa (`CU21`)**:
   - Crear `src/app/modules/comercial/cu21_reportes_ia/` (`modelos/`, `servicios/`, `paginas/reportes-ia-admin.component.{ts,html,scss,spec.ts}`).
   - Registrar ruta `/admin/reportes-ia` en `app.routes.ts` (antes de `:codigo`) y botón/tarjeta en `admin-dashboard.component.html`.

