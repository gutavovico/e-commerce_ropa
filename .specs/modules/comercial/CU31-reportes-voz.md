# Especificacion Tecnica Permanente: CU31 - Generar reportes ejecutivos y consultas por voz

**Codigo:** CU31  
**Nombre:** Generar reportes ejecutivos y consultas por voz  
**Paquete de Dominio:** `comercial` / `analitica_reportes`  
**Directorio Funcional Backend:** `app/modules/comercial/cu31_reportes_voz`  
**Directorio Funcional Frontend:** `src/app/modules/comercial/cu31_reportes_voz`  
**Directorio Funcional Mobile:** Excluido formalmente (emision de reportes ejecutivos y exportaciones binarias reservada exclusivamente al back-office web corporativo)  
**Actores Primarios:**  
- Administrador (Acceso irrestricto transversal a reportes de Ventas, Reservas, Inventario y Bitacora en formatos Excel, PDF y CSV; consultas de consolidado corporativo o por sucursal).  
- Encargado de Sucursal (Acceso acotado a reportes de Ventas, Reservas e Inventario de su propia sucursal asignada; bloqueo estricto a Bitacora y consolidado global).  
**Actores Bloqueados:**  
- Cajero (Bloqueo estricto por politica RBAC - HTTP 403 Forbidden)  
- Cliente (Bloqueo estricto por confidencialidad comercial - HTTP 403 Forbidden)  
**Metodologia:** Spec-Driven Development (SDD) & Sintaxis EARS (Easy Approach to Requirements Syntax)  
**Version:** 2.8.0 (Linea Base Permanente)  
**Estado:** Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**  
- Documento Maestro de Requisitos: `SI2-Parcial1.md` (Modulo de Analitica y Reportes).  
- Arquitectura de Dominio Backend: `.agents/skills/fashionstore-backend-sdd/references/dominio.md`.  
- Design System Multiplataforma: `.agents/skills/fashionstore-frontend-sdd/references/fashionstore-tokens.md` (Diseno editorial Atelier, paleta Slate/Camel/Obsidian, tipografia Outfit, ChangeDetectionStrategy.OnPush, Angular Signals y streaming binario de archivos).  

---

## 1. Definicion Funcional y Reglas de Negocio

### 1.1 Proposito y Alcance
El caso de uso CU31 dota a la direccion ejecutiva y a los administradores de sucursal de una consola unificada para la generacion, previsualizacion cuantitativa y exportacion binaria en streaming de informes tabulares y documentos ejecutivos en formatos Excel (.xlsx), PDF vectorial (.pdf) y CSV plano (.csv). Cubre cuatro dominios cardinales: Ventas, Reservas, Inventario y Bitacora de Auditoria. Incorpora un Asistente de Consulta por Voz que captura ordenes verbales mediante la Web Speech API nativa del navegador y las procesa mediante un parser semantico determinista en backend.

### 1.2 Declaracion Formal de Exclusion de la Aplicacion Movil (Ec-mobile)
La aplicacion movil de FashionStore (`Ec-mobile`), desarrollada en Flutter 3.x, esta orientada exclusivamente al consumidor final B2C (catalogo inmersivo, vestidor con Realidad Aumentada, bolsa de compras y pagos).  
La generacion y descarga de archivos binarios contables, compilacion de PDFs de alta densidad y auditoria de trastienda son competencias exclusivas de la estacion web corporativa de escritorio (`Ec-frontend`).  
Por tanto, se ratifica formalmente la exclusion justificada de `Ec-mobile`: cero cambios o dependencias en Flutter para este caso de uso.

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
