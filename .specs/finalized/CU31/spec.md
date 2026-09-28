# Especificacion de Requisitos de Software: [CU31] Generar reportes ejecutivos y consultas por voz

## 1. Denominacion Oficial y Dominio
- **Caso de Uso:** [CU31] Generar reportes ejecutivos y consultas por voz
- **Modulo:** Analitica y Reportes Corporativos (Direccion Ejecutiva)
- **Canal:** Web Corporativa Exclusiva (/admin/reportes)
- **Exclusion Formal de Ec-mobile:** La generacion masiva de documentos contables, exportacion fiscal en planillas Excel (.xlsx), documentos PDF con maquetacion vectorial institucional y procesamiento de comandos de reporte corporativo es competencia exclusiva de estaciones de trabajo de escritorio (Ec-frontend). Los dispositivos moviles (Ec-mobile) estan optimizados para la experiencia de fitting, catalogo omnicanal y vestidor de Realidad Aumentada (AR) para clientes finales. La emision de reportes ejecutivos y streaming binario de archivos no aplica al entorno movil, garantizando cero impacto en el footprint de la app movil.

---

## 2. Declaracion de Necesidad y Alcance
El sistema FashionStore requiere dotar a la direccion corporativa (superadministradores) y a la gerencia de sede (encargados de sucursal) de un centro unificado de emision documental y consulta analitica avanzada. El modulo [CU31] habilita la generacion y descarga directa de reportes ejecutivos en formatos Excel (.xlsx), PDF institucional (.pdf) y CSV plano (.csv) cubriendo cuatro dominios cardinales:
1. Ventas y Facturacion comercial.
2. Reservas de Prendas en boutique.
3. Inventario y Kardex valorizado.
4. Bitacora y Auditoria de seguridad.

Adicionalmente, incorpora un Asistente de Consulta por Voz que captura ordenes habladas mediante la Web Speech API nativa del navegador, remitiendo la transcripcion al backend para su interpretacion semantica determinista mediante un parser de lenguaje natural que extrae intencion, dominio, periodo, sucursal y formato solicitado, disparando la descarga o filtrado de forma inmediata.

---

## 3. Requisitos Funcionales en Notacion EARS

### Ubicuos (Reglas Universales)
- **[CU31-EARS-01]** El sistema siempre garantizara la integridad y fidelidad de los datos exportados respecto a la base de datos PostgreSQL Neon, formateando fechas bajo estandar ISO-8601 / formato local boliviano, importes monetarios en Bolivianos (BOB) con dos decimales y totales consolidados.
- **[CU31-EARS-02]** El sistema siempre emitira las descargas documentales mediante streaming binario HTTP con cabeceras `Content-Disposition: attachment; filename="..."` y tipos MIME normalizados para cada extension (`application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/pdf`, `text/csv; charset=utf-8`).

### Respuestas a Eventos (Trigger-Driven)
- **[CU31-EARS-03]** Cuando un usuario autenticado y autorizado solicite la exportacion manual seleccionando modulo, rango temporal, sucursal y formato, el sistema generara el archivo en memoria y retornara el flujo binario en un tiempo inferior a 3.0 segundos para lotes de hasta 5,000 registros.
- **[CU31-EARS-04]** Cuando el usuario interactue con la Barra de Asistente por Voz y dicte una peticion verbal, el sistema activara la captura mediante Web Speech API, mostrara la transcripcion progresiva en pantalla y remitira el texto al endpoint de interpretacion semantica (`POST /api/v1/admin/reportes/interpretar-comando-voz`).
- **[CU31-EARS-05]** Cuando el backend reciba la transcripcion textual de una orden hablada, el parser determinista extraera la intencion operativa ('exportar', 'consultar', 'filtrar'), el modulo destino ('ventas', 'reservas', 'inventario', 'bitacora'), el periodo temporal ('hoy', 'ayer', 'esta_semana', 'este_mes', 'anio_actual' o rango explicito), la sucursal referida (por coincidencia de nombre o consolidado global) y el formato solicitado ('excel', 'pdf', 'csv'), retornando el comando estructurado para ejecucion automatica en la interfaz.
- **[CU31-EARS-06]** Cuando el usuario modifique los criterios de filtrado manual en el panel web, el sistema consultara de forma preliminar el conteo estimado de registros coincidentes antes de disparar la generacion pesada del archivo.

### Condicionales de Estado (State-Driven)
- **[CU31-EARS-07]** Mientras el usuario en sesion posea el rol `encargado_sucursal`, el sistema restringira estrictamente el alcance de los reportes a su propia sucursal asignada (`id_sucursal`), bloqueando cualquier consulta global o acceso al dominio de `bitacora` con codigo HTTP 403 Forbidden.
- **[CU31-EARS-08]** Mientras el usuario en sesion posea el rol `administrador` o `admin`, el sistema permitira la consolidacion transversal de todas las sucursales y la exportacion integral del modulo de auditoria y bitacora.
- **[CU31-EARS-09]** Mientras el rol del usuario sea `cajero`, `cliente` o no autenticado, el sistema denegara el acceso a cualquier operacion del modulo de reportes con codigo HTTP 403 o 401 respectivamente.
- **[CU31-EARS-10]** Mientras el navegador del usuario no soporte la Web Speech API o el usuario deniegue permisos de microfono, el sistema degradara suavemente la experiencia mostrando un indicador accesible de voz no disponible y permitiendo operar con normalidad mediante el panel manual.

---

## 4. Criterios de Aceptacion (Gherkin)

### AC-1: Acceso al Modulo desde el Dashboard Administrativo (Regla Anti-Botones Estaticos)
```gherkin
Dado que el usuario autenticado posee rol 'administrador' o 'encargado_sucursal'
Cuando se encuentra en el dashboard principal '/admin'
Entonces visualiza la tarjeta de modulo 'Generar reportes ejecutivos y consultas por voz' bajo la seccion de analitica
Y la tarjeta presenta el badge 'Voz & Exportacion'
Y al hacer clic sobre el boton '#btn-reportes-voz' se dispara la navegacion inmediata hacia '/admin/reportes' mediante enlace directo y handler programmatico con preventDefault
Y la prueba unitaria confirma el despacho de clic hacia la ruta '/admin/reportes'.
```

### AC-2: Exportacion Manual de Reporte de Ventas en Excel
```gherkin
Dado que un administrador accede a '/admin/reportes'
Cuando selecciona el modulo 'Ventas y Facturacion', periodo 'Este Mes', sucursal 'Todas las Sucursales' y formato 'Excel (.xlsx)'
Y presiona el boton 'Generar y Descargar Reporte'
Entonces el backend genera un archivo binario formateado con cabeceras estilizadas en la paleta Obsidian & Camel
Y la respuesta HTTP incluye Content-Type 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
Y el navegador descarga el archivo con nomenclatura 'reporte_ventas_[fecha].xlsx'
Y el archivo contiene columnas de codigo de venta, fecha, cliente, sucursal, metodo de pago, desglose impositivo y total.
```

### AC-3: Exportacion de Reporte en PDF Institucional con Tablas Estructuradas
```gherkin
Dado que un administrador o encargado solicita un reporte en formato PDF
Cuando confirma la descarga
Entonces el backend compila el documento vectorial mediante reportlab
Y el documento incluye encabezado corporativo 'FASHION STORE - ALTA COSTURA', metadatos de emision, tabla paginada con filas alternadas y fila de totales generales al pie
Y el navegador completa la descarga con Content-Type 'application/pdf'.
```

### AC-4: Interpretacion de Comando de Voz para Exportacion Inmediata
```gherkin
Dado que el administrador activa el microfono en '/admin/reportes'
Cuando dicta: "Descargar reporte de ventas de este mes en excel"
Entonces el servicio Web Speech API transcribe el texto
Y el endpoint '/api/v1/admin/reportes/interpretar-comando-voz' retorna:
  | intencion | exportar |
  | modulo    | ventas   |
  | periodo   | este_mes |
  | formato   | excel    |
Y la interfaz actualiza los selectores visuales y ejecuta la descarga automaticamente.
```

### AC-5: Interpretacion de Comando de Voz con Filtrado de Sucursal
```gherkin
Dado que el administrador dicta: "Consultar inventario de la boutique equipetrol en pdf"
Cuando el backend procesa la solicitud textual
Entonces detecta el modulo 'inventario', la sucursal correspondiente a 'Equipetrol', el formato 'pdf' y la intencion 'consultar'
Y la interfaz sincroniza los filtros y despliega la previsualizacion de datos de dicha boutique.
```

### AC-6: Restriccion RBAC para Encargado de Sucursal
```gherkin
Dado que el usuario autenticado tiene rol 'encargado_sucursal' asignado a la sucursal ID 1 ('Equipetrol')
Cuando intenta solicitar un reporte del modulo 'bitacora' o seleccionar 'Todas las Sucursales'
Entonces el backend rechaza la operacion con HTTP 403 Forbidden y codigo 'ACCESO_NO_AUTORIZADO'
Y el frontend deshabilita y bloquea visualmente las opciones no permitidas.
```

### AC-7: Degradacion Defensiva ante Falta de Microfono
```gherkin
Dado que el navegador del cliente carece de soporte para Web Speech API o el microfono esta bloqueado
Cuando se carga la vista '/admin/reportes'
Entonces el indicador del asistente por voz informa 'Reconocimiento de voz no disponible en este dispositivo'
Y el panel clasico de exportacion manual permanece 100% operativo y accesible.
```
