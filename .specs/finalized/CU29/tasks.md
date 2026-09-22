# Plan de Tareas: [CU29] Visualizar indicadores empresariales

**Codigo del Caso de Uso:** CU29  
**Denominacion Oficial:** Visualizar indicadores empresariales  
**Modulo:** Analitica y Reportes / Inteligencia Empresarial (`analitica_reportes` / `comercial`)  
**Metodologia:** Spec-Driven Development (SDD) & Ejecucion por Oleadas  
**Entorno:** 100% Local (Prohibido git push)  
**Exclusion Formal:** `Ec-mobile` (Flutter 3.x) 100% excluida  

---

## Resumen de Oleadas y Dependencias

```
+--------------------------------------------------------------------------------+
| OLEADA 1: Backend (Ec-backend - FastAPI + PostgreSQL Neon)                     |
| [x] Tarea 1.1: Modelos y Dependencias de Entidades Relacionales                |
| [x] Tarea 1.2: Esquemas Pydantic v2 y Jerarquia de Errores Semanticos          |
| [x] Tarea 1.3: Servicio Analitico y Motor de Agregaciones SQL                  |
| [x] Tarea 1.4: Router REST FastAPI y Registro en API v1                        |
| [x] Tarea 1.5: Suite de Pruebas Automatizadas Pytest                           |
+---------------------------------------+----------------------------------------+
                                        | (Requiere aprobacion previa)
                                        v
+---------------------------------------+----------------------------------------+
| OLEADA 2: Frontend Web (Ec-frontend - Angular 19+ Standalone)                  |
| [x] Tarea 2.1: Modelos de Datos y DTOs TypeScript                              |
| [x] Tarea 2.2: Servicio HTTP Reactivo con Angular Signals                      |
| [x] Tarea 2.3: Tarjeta en AdminDashboardComponent con Directiva Dual y Clic   |
| [x] Tarea 2.4: Vista Principal /admin/indicadores (Barra Temporal y KPIs)      |
| [x] Tarea 2.5: Componentes Graficos SVG Nativos y Luxury Banners               |
| [x] Tarea 2.6: Suite de Pruebas Unitarias Vitest                               |
+---------------------------------------+----------------------------------------+
                                        | (Requiere aprobacion previa)
                                        v
+---------------------------------------+----------------------------------------+
| OLEADA 3: Cierre, Verificacion Cruzada Integral y DoD                          |
| [x] Tarea 3.1: Verificacion Cruzada Integral de Suites Locales                |
| [x] Tarea 3.2: Consolidacion y Promocion Documental a .specs/finalized/CU29/   |
| [x] Tarea 3.3: Actualizacion de Bitacoras CHANGELOG.md y Cierre de Ciclo       |
+--------------------------------------------------------------------------------+
```

---

## OLEADA 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

### [x] Tarea 1.1: Modelos y Dependencias de Entidades Relacionales
- **Archivo destino:** `app/modules/comercial/cu29_indicadores/modelos.py`
- **Descripcion:**
  * Importar y registrar de forma segura las referencias ORM declarativas bajo el esquema `fashionstore`: `VentaORM`, `VentaDetalleORM`, `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `SucursalORM`.
  * Asegurar compatibilidad relacional con SQLAlchemy 2.0 evitando duplicaciones o colisiones en el catalogo de metadatos.
- **Verificacion:** Modulo importable en Python limpiamente sin errores de mapeo ni dependencias circulares.

### [x] Tarea 1.2: Esquemas Pydantic v2 y Jerarquia de Errores Semanticos
- **Archivos destino:**
  * `app/modules/comercial/cu29_indicadores/esquemas.py`
  * `app/modules/comercial/cu29_indicadores/errores.py`
- **Descripcion:**
  * En `esquemas.py`: Definir los DTOs de entrada y salida: `IndicadoresFiltrosIn` (con validacion cronologica de `fecha_desde <= fecha_hasta` para periodos personalizados), `MetricaVariacionItem`, `ResumenEjecutivoOut`, `PuntoSerieTemporalOut`, `SerieTemporalOut`, `ProductoTopOut`, `TopProductosOut`, `CategoriaDistribucionOut`, `DistribucionCategoriasOut`, `CanalDistribucionOut`, `DistribucionCanalesOut`, `SucursalComparativaOut`, `ComparativaSucursalesOut`.
  * En `errores.py`: Definir excepciones semanticas `IndicadoresEmpresarialesError`, `RangoFechasInvalidoError` (422), `SucursalNoAutorizadaError` (403), `ComparativaRestringidaError` (403).
- **Verificacion:** Pruebas unitarias sobre validadores Pydantic ejecutadas correctamente.

### [x] Tarea 1.3: Servicio Analitico y Motor de Agregaciones SQL
- **Archivo destino:** `app/modules/comercial/cu29_indicadores/servicio.py`
- **Descripcion:** Implementar la clase `ServicioIndicadoresEmpresariales`:
  * Metodo auxiliar de resolucion temporal de rangos y periodos equivalentes precedentes para el computo de variaciones porcentuales.
  * Segregacion territorial forzada para el rol `encargado_sucursal` y alcance global para `administrador`.
  * Metodo `obtener_resumen_ejecutivo`: Calculo de ingresos totales, transacciones, ticket promedio, unidades vendidas, margen comercial y comparativas relativas.
  * Metodo `obtener_serie_temporal`: Agrupacion por intervalo (`date_trunc`) con ordenamiento cronologico ascendente.
  * Metodo `obtener_top_productos`: Ranking agregado de prendas mas comercializadas con parametro de limite.
  * Metodo `obtener_distribucion_categorias`: Agrupacion de ventas por categoria taxonomica.
  * Metodo `obtener_distribucion_canales`: Clasificacion por canal (`presencial`, `digital_web`, `digital_movil`).
  * Metodo `obtener_comparativa_sucursales`: Agrupacion por sede activa con validacion de rol administrador obligatoria.
- **Verificacion:** Invocacion de metodos analiticos en entorno aislado de pruebas con agregaciones deterministas.

### [x] Tarea 1.4: Router REST FastAPI y Registro en API v1
- **Archivos destino:**
  * `app/modules/comercial/cu29_indicadores/router.py`
  * `app/main.py`
- **Descripcion:**
  * En `router.py`: Implementar los endpoints `GET /resumen`, `GET /serie-temporal`, `GET /top-productos`, `GET /distribucion-categorias`, `GET /distribucion-canales`, `GET /sucursales-comparativa` custodiados por `require_roles(["administrador", "encargado_sucursal"])`.
  * En `main.py`: Registrar el router analitico bajo el prefijo `/api/v1/admin/indicadores` con etiqueta comercial.
- **Verificacion:** Montaje de rutas visible y documentado en OpenAPI `/docs`.

### [x] Tarea 1.5: Suite de Pruebas Automatizadas Pytest
- **Archivo destino:** `tests/modules/comercial/test_cu29_indicadores.py`
- **Descripcion:** Desarrollar suite de pruebas automatizadas cubriendo:
  * Autenticacion requerida (HTTP 401).
  * Control de acceso RBAC para roles cajero y cliente (HTTP 403).
  * Segregacion por sucursal para encargado de sede.
  * Bloqueo de comparativa de sucursales para encargados (HTTP 403).
  * Validacion de rangos cronologicos invertidos en periodo personalizado (HTTP 422).
  * Verificacion del calculo matematico de variaciones porcentuales y ticket promedio sin division por cero.
  * Respuestas HTTP 200 para todos los endpoints analiticos con rol administrador.
- **Verificacion:** Ejecucion de `pytest tests/modules/comercial/test_cu29_indicadores.py` al 100% en verde.

---

## OLEADA 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### [x] Tarea 2.1: Modelos de Datos y DTOs TypeScript
- **Archivo destino:** `src/app/modules/comercial/cu29_indicadores/modelos/indicadores.dto.ts`
- **Descripcion:** Definir interfaces TypeScript estrictas: `PeriodoPreset`, `IndicadoresFiltros`, `MetricaVariacion`, `ResumenEjecutivo`, `PuntoSerieTemporal`, `SerieTemporal`, `ProductoTop`, `TopProductos`, `CategoriaDistribucion`, `CanalDistribucion`, `SucursalComparativa`.
- **Verificacion:** Compilacion TypeScript sin errores (`tsc --noEmit`).

### [x] Tarea 2.2: Servicio HTTP Reactivo con Angular Signals
- **Archivos destino:**
  * `src/app/modules/comercial/cu29_indicadores/servicios/indicadores-admin.service.ts`
  * `src/app/modules/comercial/cu29_indicadores/servicios/indicadores-admin.service.spec.ts`
- **Descripcion:** Implementar `IndicadoresAdminService`:
  * Signals reactivos para el estado analitico: `resumen`, `serieTemporal`, `topProductos`, `distribucionCategorias`, `distribucionCanales`, `comparativaSucursales`, `filtros`, `cargando`, `error`.
  * Metodos HTTP: `consultarResumen`, `consultarSerieTemporal`, `consultarTopProductos`, `consultarDistribucionCategorias`, `consultarDistribucionCanales`, `consultarComparativaSucursales`, `cargarSucursalesAuxiliares`.
  * Pruebas unitarias completas con `provideHttpClientTesting`.
- **Verificacion:** `npx ng test --include "src/app/modules/comercial/cu29_indicadores/servicios/*.spec.ts"` al 100% en verde.

### [x] Tarea 2.3: Tarjeta en AdminDashboardComponent con Directiva Dual y Clic
- **Archivos destino:**
  * `src/app/modules/admin/dashboard/admin-dashboard.component.html`
  * `src/app/modules/admin/dashboard/admin-dashboard.component.ts`
  * `src/app/modules/admin/dashboard/admin-dashboard.component.spec.ts`
  * `src/app/app.routes.ts`
- **Descripcion:**
  * En `admin-dashboard.component.html`: Agregar la tarjeta oficial 10 "Visualizar indicadores empresariales" dentro de "Analitica y Reportes" con badge "Business Intelligence", boton `#btn-visualizar-indicadores-empresariales` y directiva dual: `routerLink="/admin/indicadores"` y `(click)="navegar('/admin/indicadores', $event)"`.
  * En `app.routes.ts`: Registrar la ruta `/admin/indicadores` con guards de autenticacion y roles.
  * En `admin-dashboard.component.spec.ts`: Incorporar prueba unitaria obligatoria de despacho de evento click sobre `#btn-visualizar-indicadores-empresariales` verificando la llamada a `navegar`.
- **Verificacion:** Pruebas unitarias del dashboard al 100% en verde.

### [x] Tarea 2.4: Vista Principal /admin/indicadores (Barra Temporal y KPIs)
- **Archivos destino:**
  * `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.ts`
  * `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.html`
  * `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.scss`
- **Descripcion:**
  * Layout editorial `max-w-[1440px]` con H1 "Visualizar indicadores empresariales", breadcrumbs corporativos y enlace superior de retorno.
  * Barra superior reactiva con selector rapido de periodo (`7D`, `30D`, `Mes`, `Ano`, `Personalizado`), selectores de fecha y selector de sucursal (bloqueado con indicador informativo para encargados).
  * Rejilla de 4 tarjetas de KPIs ejecutivos con flechas de tendencia cromaticas discretas (verde esmeralda, carmin, gris neutro).
- **Verificacion:** Renderizado reactivo OnPush limpio con Signals.

### [x] Tarea 2.5: Componentes Graficos SVG Nativos y Luxury Banners
- **Archivos destino:**
  * `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.html`
  * `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.ts`
- **Descripcion:**
  * Grafico de Serie Temporal nativo en SVG con lineas de cuadricula, curva escalada y puntos interactivos con tooltips.
  * Grafico de barras horizontales SVG para el Top de prendas mas comercializadas.
  * Grafico de participacion porcentual por canales de comercializacion (fisico boutique, web, movil).
  * Tabla/ranking comparativo de sucursales con participacion de red (condicionado a rol administrador).
  * Luxury Banners contextuales para retroalimentacion amigable ante contingencias.
- **Verificacion:** Renderizado grafico responsivo sin librerias externas pesadas.

### [x] Tarea 2.6: Suite de Pruebas Unitarias Vitest
- **Archivo destino:** `src/app/modules/comercial/cu29_indicadores/paginas/indicadores-admin.component.spec.ts`
- **Descripcion:** Desarrollar suite de pruebas para el componente cubriendo:
  * Renderizado del titulo y tarjetas de KPIs ejecutivos.
  * Interaccion con la botonera de periodos y actualizacion reactiva.
  * Validacion de permisos de seleccion de sucursal segun rol.
  * Renderizado de las graficas SVG nativas.
  * Gestion de estados de carga y Luxury Banners.
- **Verificacion:** `npx ng test --include "src/app/modules/comercial/cu29_indicadores/**/*.spec.ts"` al 100% en verde.

---

## OLEADA 3: Cierre, Verificacion Cruzada Integral y DoD

### [x] Tarea 3.1: Verificacion Cruzada Integral de Suites Locales
- **Descripcion:** Revalidacion exhaustiva en ambos proyectos:
  * Backend: `pytest tests/` (100% en verde).
  * Frontend: `npx ng test --watch=false` y `npm run build` (100% en verde, 0 errores).
  * Auditoria de emojis: 0 emojis en todo el codigo fuente, pruebas y documentacion.
- **Verificacion:** Compilacion de produccion impecable y ejecucion de pruebas sin regresiones.

### [x] Tarea 3.2: Consolidacion y Promocion Documental a .specs/finalized/CU29/
- **Archivos destino:**
  * `.specs/finalized/CU29/spec.md`
  * `.specs/finalized/CU29/design.md`
  * `.specs/finalized/CU29/tasks.md`
  * `.specs/modules/comercial/CU29-visualizar-indicadores-empresariales.md`
- **Descripcion:** Copiar y archivar formalmente las especificaciones aprobadas en el catalogo historico y modular permanente.
- **Verificacion:** Existencia e integridad de las especificaciones permanentes.

### [x] Tarea 3.3: Actualizacion de Bitacoras CHANGELOG.md y Cierre de Ciclo
- **Archivos destino:**
  * `CHANGELOG.md` (raiz)
  * `.specs/CHANGELOG.md`
- **Descripcion:** Registrar la version `v2.6.0` con la incorporacion de [CU29] Visualizar indicadores empresariales, ratificando la exclusion formal de `Ec-mobile` y eliminando la carpeta temporal `.specs/changes/CU29/`.
- **Verificacion:** Bitacoras sincronizadas y espacio de trabajo 100% limpio.
