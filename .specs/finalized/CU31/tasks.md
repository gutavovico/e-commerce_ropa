# Plan de Tareas: [CU31] Generar reportes ejecutivos y consultas por voz

## Oleada 1: Backend (Ec-backend)
- [x] **Tarea 1.1: Generadores Binarios de Archivos en Memoria**
  - Implementar generador Excel (.xlsx) con `openpyxl` aplicando paleta Obsidian & Camel, auto-ancho de celdas y formulas de totalizacion.
  - Implementar generador PDF (.pdf) con `reportlab` usando maquetacion vectorial Letter, encabezado institucional, tablas estructuradas y canvas numerado.
  - Implementar generador CSV (.csv) con soporte de BOM UTF-8 y codificacion segura.
  - Ubicacion: `app/modules/comercial/cu31_reportes_voz/generadores/`.
- [x] **Tarea 1.2: Esquemas Pydantic v2 y Jerarquia de Errores**
  - Crear `app/modules/comercial/cu31_reportes_voz/esquemas.py` con enums (`ModuloReporteEnum`, `FormatoReporteEnum`, `RangoTemporalEnum`, `IntencionVozEnum`) y DTOs (`ComandoVozIn`, `ComandoVozOut`, `ReporteFiltrosIn`, `ReportePrevisualizacionOut`).
  - Crear `app/modules/comercial/cu31_reportes_voz/errores.py` con excepciones semanticas de dominio.
- [x] **Tarea 1.3: Parser Determinista de Comandos de Voz**
  - Implementar `app/modules/comercial/cu31_reportes_voz/parser_voz.py` con reglas lexico-sintacticas deterministas para extraer intencion, modulo, periodo temporal, sucursal y formato a partir de transcripciones verbales.
- [x] **Tarea 1.4: Servicio de Dominio Transaccional y Auditoria**
  - Crear `app/modules/comercial/cu31_reportes_voz/servicio.py` con la clase `ServicioReportesVoz`.
  - Implementar extraccion y agregacion de datos para Ventas, Reservas, Inventario y Bitacora respetando restricciones RBAC.
  - Registrar evento de auditoria en `fashionstore.bitacora` (`EXPORTAR_REPORTE`) mediante llamada defensiva no bloqueante.
- [x] **Tarea 1.5: Router REST y Streaming de Descargas**
  - Crear `app/modules/comercial/cu31_reportes_voz/router.py` con endpoints:
    * `POST /api/v1/admin/reportes/interpretar-comando-voz`
    * `POST /api/v1/admin/reportes/interpretar-voz`
    * `POST /api/v1/admin/reportes/previsualizar`
    * `POST /api/v1/admin/reportes/exportar` (StreamingResponse)
    * `GET /api/v1/admin/reportes/exportar` (StreamingResponse)
  - Registrar el router en `app/main.py`.
- [x] **Tarea 1.6: Suite de Pruebas Automatizadas Backend**
  - Crear `tests/modules/comercial/test_cu31_reportes_voz.py` cubriendo:
    * Parser determinista de voz con distintas expresiones coloquiales.
    * Generacion integra de buffers en Excel, PDF y CSV.
    * Validacion de permisos RBAC (administrador total vs. encargado acotado vs. 403 para cajero/cliente).
    * Validacion de no regresion de la suite completa con `pytest`.

---

## Oleada 2: Frontend Web (Ec-frontend)
- [x] **Tarea 2.1: Modelos e Interfaces TypeScript**
  - Crear `src/app/modules/comercial/cu31_reportes_voz/modelos/reportes-voz.dto.ts` replicando los contratos tipados del backend.
- [x] **Tarea 2.2: Servicio de Reconocimiento de Voz**
  - Implementar `src/app/modules/comercial/cu31_reportes_voz/servicios/voz-reconocimiento.service.ts` integrando Web Speech API (`webkitSpeechRecognition` / `SpeechRecognition`), Signals reactivas y deteccion defensiva de compatibilidad.
  - Crear pruebas unitarias del servicio en `voz-reconocimiento.service.spec.ts`.
- [x] **Tarea 2.3: Servicio HTTP de Reportes y Descarga de Blobs**
  - Implementar `src/app/modules/comercial/cu31_reportes_voz/servicios/reportes-admin.service.ts` con metodos de interpretacion, previsualizacion y descarga reactiva de archivos (`HttpResponse<Blob>`).
  - Crear pruebas unitarias del servicio en `reportes-admin.service.spec.ts`.
- [x] **Tarea 2.4: Componente de Pagina Editorial ReportesAdmin**
  - Crear `reportes-admin.component.ts`, `.html` y `.scss` en `src/app/modules/comercial/cu31_reportes_voz/paginas/`.
  - Integrar Barra de Asistente por Voz accesible con indicador visual reactivo y feedback de dictado.
  - Integrar Panel clasico de exportacion manual con selectores de modulo, periodo, sucursal y formato.
  - Integrar tarjeta de previsualizacion con conteo antes de la descarga.
- [x] **Tarea 2.5: Enrutamiento y Proteccion RBAC**
  - Registrar la ruta en `app.routes.ts`: `admin/reportes` con `authGuard` y `roleGuard(['administrador', 'admin', 'encargado_sucursal'])`.
- [x] **Tarea 2.6: Integracion en AdminDashboard y Pruebas Unitarias**
  - Incorporar la tarjeta numero 13 en `admin-dashboard.component.html` con `#btn-reportes-voz` y directiva dual estricta (`routerLink="/admin/reportes"` y `(click)="navegar('/admin/reportes', $event)"`).
  - Actualizar `admin-dashboard.component.ts` actualizando el conteo de modulos (13 para administrador, 10 para encargado).
  - Actualizar `admin-dashboard.component.spec.ts` agregando la prueba obligatoria de despacho de clic hacia `/admin/reportes`.
  - Crear `reportes-admin.component.spec.ts` con cobertura de asistentes de voz, filtros y descargas.

---

## Oleada 3: Cierre, Verificacion Cruzada Integral y DoD
- [x] **Tarea 3.1: Verificacion Integral de Suites Locales**
  - Ejecutar `pytest tests/` (todas las pruebas backend en verde sin regresiones).
  - Ejecutar `npm test -- --watch=false` (todas las pruebas frontend en verde).
  - Ejecutar `npm run build` (compilacion de produccion limpia con cero errores).
- [x] **Tarea 3.2: Promocion Documental y Changelogs**
  - Promover artefactos a `.specs/finalized/CU31/` (`spec.md`, `design.md`, `tasks.md`).
  - Crear documentacion modular en `.specs/modules/comercial/CU31-reportes-voz.md`.
  - Actualizar `CHANGELOG.md` y `.specs/CHANGELOG.md` documentando la version v2.8.0.
  - Limpiar `.specs/changes/CU31/` dejando `.gitkeep`.
- [x] **Tarea 3.3: Auditoria de Cero Emojis, Ratificacion de Exclusion y Balance Final**
  - Ejecutar auditoria automatizada confirmando 0 emojis en todo el repositorio.
  - Ratificar que `Ec-mobile` permanece 100% libre de codigo o dependencias de reportes.
  - Emitir reporte de cierre formal.
