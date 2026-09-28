# Especificacion Tecnica Permanente: CU31 - Generar reportes ejecutivos y consultas por voz

**Codigo:** CU31  
**Nombre:** Generar reportes ejecutivos y consultas por voz  
**Paquete de Dominio:** `comercial` / `analitica_reportes`  
**Directorio Funcional Backend:** `app/modules/comercial/cu31_reportes_voz`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/cu31_reportes_voz`  
**Directorio Funcional Mobile:** `lib/src/modulos/comercial/cu31_reportes_voz`  
**Actores Primarios:**  
- Administrador (Acceso irrestricto transversal a reportes de Ventas, Reservas, Inventario y Bitacora en formatos Excel, PDF y CSV; consultas de consolidado corporativo o por sucursal).  
- Encargado de Sucursal (Acceso acotado a reportes de Ventas, Reservas e Inventario de su propia sucursal asignada; bloqueo estricto a Bitacora y consolidado global).  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por confidencialidad comercial - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.9.0 (Ampliacion Multiplataforma Mobile)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Analitica y Reportes).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` y `.agents/skills/fashionstore-mobile-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush, Angular Signals, Flutter BLoC/ChangeNotifier y streaming binario de archivos).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU31 dota a la direccion ejecutiva y a los administradores de sucursal de una consola unificada para la generacion, previsualizacion cuantitativa y exportacion binaria en streaming de informes tabulares y documentos ejecutivos en formatos Excel (.xlsx), PDF vectorial (.pdf) y CSV plano (.csv). Cubre cuatro dominios cardinales: Ventas, Reservas, Inventario y Bitacora de Auditoria. Incorpora un Asistente de Consulta por Voz que captura ordenes verbales y las procesa mediante un parser semantico determinista en backend.

### 1.2 Soporte Multiplataforma Integral (Web y Mobile)
El caso de uso esta disponible en dos clientes oficiales de FashionStore:
1. **Estacion de Trabajo Web (`Ec-frontend`):** Pantalla `/admin/reportes` con integracion nativa a la Web Speech API del navegador.
2. **Aplicacion Movil (`Ec-mobile` - Flutter 3.x):** Pantalla ejecutiva `PantallaReportesVoz` accesible desde el perfil de usuario, con dictado por voz, chips de ordenes rapidas sugeridas, previsualizacion dinamica y exportacion binaria en streaming.

### 1.3 Reglas de Negocio Estrictas (RB)

1. **RB-1: Control de Acceso y Autorizacion RBAC:**
   - Requiere autenticacion con JWT valido. Roles `cajero` o `cliente` son rechazados con HTTP 403 Forbidden. `administrador` posee acceso total a todos los modulos incluida Bitacora. `encargado_sucursal` tiene acceso a Ventas, Reservas e Inventario de su propia sede.
2. **RB-2: Restriccion Territorial y Blindaje de Bitacora:**
   - Si el rol es `encargado_sucursal`, cualquier intento de exportar o consultar Bitacora se rechaza con HTTP 403 Forbidden. Asimismo, su parametro `id_sucursal` queda confinado a su sede asignada.
3. **RB-3: Generacion Binaria en Memoria sin Persistencia Temporal:**
   - Todos los documentos se compilan en buffers binarios volátiles (`io.BytesIO` / `io.StringIO`) y se transmiten mediante `StreamingResponse` con cabeceras `Content-Disposition`, evitando retencion de archivos temporales en disco del servidor.
4. **RB-4: Auditoria Automatica Defensiva:**
   - Cada descarga de reporte genera un evento inmutable en `fashionstore.bitacora` (`accion="EXPORTAR_REPORTE"`) con marca temporal, direccion IP, usuario emisor y parametros de consulta.
5. **RB-5: Degradacion Defensiva de Voz:**
   - Si el navegador carece de soporte para Web Speech API o no tiene microfono disponible, el sistema informa el estado de modo teclado sin bloquear el panel manual.

---

## 2. Arquitectura Tecnica del Backend (`Ec-backend`)

### 2.1 Capa de Dominio y Servicios
- **Modulo:** `app/modules/comercial/cu31_reportes_voz`
- **Servicio:** `ServicioReportesVoz`:
  * `interpretar_comando`: Procesa la transcripcion verbal mediante `ParserComandosVoz` y devuelve intencion, modulo, periodo, formato y sucursal.
  * `previsualizar_reporte`: Calcula el conteo de registros y resumen cuantitativo antes de generar el archivo.
  * `generar_archivo_reporte`: Extrae registros de la base de datos segun RBAC y compila el buffer binario utilizando el generador correspondiente (`GeneradorExcel`, `GeneradorPDF`, `GeneradorCSV`).
- **Motores Binarios:**
  * `GeneradorExcel`: Maquetacion con `openpyxl`, paleta Obsidian & Camel, auto-ancho de celdas y formulas de sumatoria `SUM()`.
  * `GeneradorPDF`: Compilacion vectorial con `reportlab`, tamano Letter, encabezado institucional, tablas paginadas y pie con numeracion de pagina.
  * `GeneradorCSV`: Generacion con prefijo BOM UTF-8 (`\ufeff`) para compatibilidad nativa con Excel en Windows.
- **Endpoints REST:**
  * `POST /api/v1/admin/reportes/interpretar-voz`
  * `POST /api/v1/admin/reportes/previsualizar`
  * `POST /api/v1/admin/reportes/exportar`
  * `GET /api/v1/admin/reportes/exportar`

---

## 3. Arquitectura Tecnica del Frontend Web (`Ec-frontend`)

### 3.1 Servicios y Estado Reactivo
- **Modulo:** `src/app/modules/comercial/cu31_reportes_voz`
- **Servicios:**
  * `VozReconocimientoService`: Integracion nativa con Web Speech API (`SpeechRecognition` / `webkitSpeechRecognition`), senales reactivas (`escuchando`, `transcripcion`, `errorVoz`, `soportaVoz`) y soporte regional `es-BO`.
  * `ReportesAdminService`: Consumo HTTP de endpoints de reportes, descarga de `Blob` binario mediante enlaces temporales y senales de filtros y previsualizacion.

### 3.2 Vista y Dashboard Administrativo
- **Componente:** `ReportesAdminComponent` (`/admin/reportes`):
  * Standalone Component con `ChangeDetectionStrategy.OnPush`.
  * Barra de voz interactiva con boton pulsante reactivo y visor de transcripcion.
  * Selector manual de modulo, periodo, sucursal y formato.
  * Previsualizacion en tiempo real antes de la descarga y boton de emision con estado spinner.
- **AdminDashboardComponent:**
  * Decimotercera tarjeta bajo "Analitica y Reportes" con badge "Voz & Exportacion", identificador `#btn-reportes-voz` y directiva dual estricta.
  * Conteo de modulos computado: 13 activos para Superusuario Administrador y 10 para Encargado de Sede.

---

## 4. Arquitectura Tecnica de la Aplicacion Movil (`Ec-mobile` - Flutter 3.x)

### 4.1 Capas de Datos y Dominio (Data & Domain Layers)
- **Directorio:** `lib/src/modulos/comercial/cu31_reportes_voz/`
- **Modelos DTO:**
  * `ComandoVozIn` y `ComandoVozOut`: Peticion y respuesta del parser semantico.
  * `ReporteFiltrosDto`: Parametros inmutables con soporte `copyWith`.
  * `ReportePrevisualizacionDto`: Contadores de registros y resumen financiero.
  * `SucursalOpcionDto`: Sucursales activas para selector de alcance.
- **Datasource Remoto:** `ReportesRemotoDatasource`
  * Consumo HTTP con `http.Client`.
  * Manejo centralizado de sesion 401 via `SesionManager.instancia.notificarSesionExpirada()`.
  * Extraccion de nombre de archivo desde cabecera `Content-Disposition`.
- **Repositorio:** `ReportesRepositorio` y su implementacion `ReportesRepositorioImpl`.

### 4.2 Capa de Presentacion (Presentation Layer)
- **BLoC / State Management:** `ReportesBloc` (`ChangeNotifier` con estados sellados inmutables `ReportesEstado`).
  * `ReportesInicial`, `ReportesCargando`, `ReportesListo`, `ReportesExportando`, `ReportesError`.
- **Pantalla Ejecutiva:** `PantallaReportesVoz`
  * Diseno Haute Couture Atelier con paleta Obsidian (`#111111`) y Camel (`#AD8C63`).
  * Tarjeta de dictado por voz con campo de texto compatible con microfono del teclado nativo y chips de ordenes sugeridas.
  * Tarjeta de previsualizacion cuantitativa en tiempo real.
  * Selectores de chips de modulo (Ventas, Reservas, Stock, Bitacora), formato (Excel, PDF, CSV), periodo y sucursal.
  * Boton de exportacion y streaming binario.
- **Acceso en Navegacion:** Opcion ejecutiva dentro de `PantallaPerfil` ("Reportes y Consultas por Voz").

