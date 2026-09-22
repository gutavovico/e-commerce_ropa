# Especificacion de Requisitos de Software: [CU30] Consultar bitacora

## 1. Denominacion Oficial y Dominio
- **Caso de Uso:** [CU30] Consultar bitacora
- **Modulo:** Seguridad y Gobernanza de Datos (Auditoria Corporativa)
- **Canal:** Web Corporativa Exclusiva (/admin/bitacora)
- **Exclusion Formal de Ec-mobile:** La auditoria y visualizacion de trazas de eventos del sistema, mutaciones de datos y analisis forense son operaciones reservadas exclusivamente a la direccion tecnologica y administracion general en la consola web de escritorio. Ec-mobile se enfoca en experiencia de boutique y catalogo omnicanal con vestidor de realidad aumentada para clientes finales.

---

## 2. Declaracion de Necesidad y Alcance
El sistema FashionStore requiere un registro inmutable y centralizado de eventos criticos de auditoria (bitacora de operaciones), garantizando trazabilidad total sobre autenticacion, creacion, modificacion y eliminacion de entidades (sucursales, prendas, inventario, promociones, ventas, reservas y roles). El modulo [CU30] permite a los superadministradores inspeccionar eventos cronologicos, filtrar por severidad, fecha, operador y modulo, e inspeccionar los payloads JSON estructurados (estado previo vs. estado nuevo).

---

## 3. Requisitos Funcionales en Notacion EARS

### Ubicuos (Reglas Universales)
- **[CU30-EARS-01]** El sistema siempre registrara la marca temporal ISO-8601 con zona horaria UTC, identificador del operador (o nulo para eventos anonimos), direccion IP de origen, accion formal, modulo afectado, nivel de severidad y payloads JSON para cada entrada de auditoria.
- **[CU30-EARS-02]** El sistema garantizara inmutabilidad estricta sobre la bitacora: los registros no podran ser modificados ni eliminados a traves de la API bajo ninguna circunstancia.

### Respuestas a Eventos (Trigger-Driven)
- **[CU30-EARS-03]** Cuando un administrador acceda al modulo en `/admin/bitacora`, el sistema consultara los registros paginados aplicando orden descendente por defecto (`creado_en_desc`) y calculara metricas consolidadas: total de eventos, eventos criticos, advertencias/errores y operadores unicos activos.
- **[CU30-EARS-04]** Cuando el administrador filtre por termino de busqueda (`q`), severidad (`INFO`, `WARN`, `ERROR`, `CRITICAL`), modulo (`tabla_modulo`), accion o rango de fechas (`fecha_inicio` y `fecha_fin`), el sistema actualizara los resultados con una latencia inferior a 500 ms tras un debounce de 300 ms.
- **[CU30-EARS-05]** Cuando el administrador seleccione un evento unitario para inspeccionar su payload, el sistema presentara una vista modal accesible con la comparativa estructurada entre el `payload_anterior` y el `payload_nuevo`.

### Condicionales de Estado (State-Driven)
- **[CU30-EARS-06]** Mientras la sesion del usuario no posea el rol `administrador` o su alias `admin`, el sistema bloqueara la consulta con codigo HTTP 403 Forbidden y redirigira al panel `/admin`.
- **[CU30-EARS-07]** Mientras no exista un token JWT valido en la peticion HTTP, el backend respondera con error HTTP 401 Unauthorized y el frontend redirigira a `/login`.

---

## 4. Criterios de Aceptacion (Gherkin)

### AC-1: Acceso y visualizacion inicial de metricas y listado
```gherkin
Dado que el usuario activo tiene rol 'administrador'
Cuando navega a '/admin/bitacora'
Entonces visualiza el encabezado H1 'Consultar bitacora'
Y visualiza 4 tarjetas de KPIs: Total de Eventos, Mutaciones Criticas, Advertencias/Errores y Operadores Activos
Y visualiza la tabla de auditoria paginada con columnas: Fecha y Hora, Severidad, Modulo, Accion, Operador, Direccion IP y Acciones.
```

### AC-2: Filtrado multicriterio reactivo
```gherkin
Dado que el administrador interactua con los filtros en '/admin/bitacora'
Cuando selecciona la severidad 'CRITICAL' o escribe un termino en el buscador
Entonces el servicio emite la consulta con debounce de 300 ms
Y la tabla presenta unicamente los eventos coincidentes con la severidad o texto especificado
Y las metricas cuantitativas se recalculan sobre el universo filtrado.
```

### AC-3: Inspeccion de payload de evento
```gherkin
Dado que el administrador localiza un evento con cambios de estado
Cuando presiona el boton 'Ver Payload'
Entonces se despliega un modal centrado con fondo atenuado
Y se muestran formateados los bloques JSON de 'Payload Anterior' y 'Payload Nuevo'
Y el modal puede cerrarse mediante boton de escape o clic en cerrar.
```

### AC-4: Seguridad y bloqueo por roles
```gherkin
Dado que un usuario autenticado posee rol 'encargado_sucursal' o 'cajero'
Cuando intenta realizar un GET a '/api/v1/admin/bitacora'
Entonces el backend rechaza la solicitud con codigo 403 Forbidden
Y el frontend no expone la tarjeta en el panel de control corporativo.
```
