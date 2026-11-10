# Changelog Técnico de Arquitectura y SDD — FashionStore

Todas las modificaciones notables, correcciones de errores de infraestructura y promociones de especificaciones del proyecto se documentan en este archivo.

## [Unreleased] - 2026-11-09 (Parcial 2)

### Caja en el móvil — P2-CU16 y P2-CU17
- **Qué:** cajero, encargado y administrador entran en la app directamente a la caja, sin el hub del cliente (decisión E1). Venden con buscador de prendas, cliente y sus reservas, y cupón; cobran en efectivo, con tarjeta, QR o transferencia, incluido el rechazo del datáfono; ven el comprobante en pantalla (E2); gestionan las pendientes del día y los pedidos web en efectivo (E3). Sin conexión no se registra ni se cobra.
- **Cómo:** solo móvil (`cu16_cu17_caja`), con el mismo contrato que la caja web; sin cambios en backend ni web y sin dependencias nuevas. Todos los importes los calcula el servidor.
- **Corregido durante el desarrollo:** el diálogo de anulación liberaba su controlador mientras animaba el cierre; el bloc notificaba tras cerrarse la caja.
- **Pruebas:** 26 nuevas (`test/caja/`); suite móvil 325/325.
- **Spec:** `.specs/modules/compras_pagos/P2-CU16-CU17-caja-movil.md` · historial en `.specs/finalized/P2-CU16-CU17-caja-movil/`.

### Operación sin conexión — P2-CU14, CU15, CU19 y CU20 (bloque 3)
- **Qué:** el cliente descarga el catálogo de su tienda y reserva sin internet en la PWA y en la app Flutter. Al volver la conexión las operaciones se sincronizan sin duplicarse (RN35). Lo que el servidor no acepta se cancela con un aviso (reservas) o se reembolsa (compras ya cobradas, solo móvil). El encargado o el administrador revisa los conflictos y el administrador procesa los reembolsos con Stripe al cierre del mes. La caja web no opera sin conexión. Las reservas vencen a las horas que define la empresa (RN25).
- **Backend:** paquete nuevo `sincronizacion` (12 endpoints) y migración `0020_sin_conexion` (5 tablas con RLS; `reservas.vence_en` y `codigo_provisional`). Reutiliza los servicios de reserva y pago con piezas sin `commit`, sin copiar sus reglas.
- **Web:** service worker (solo la aplicación, nunca la API), IndexedDB, banda «Sin conexión», hojas `/{codigo}/sin-conexion` y `/{codigo}/sincronizacion`, y `/admin/conflictos`.
- **Móvil:** SQLite, `connectivity_plus` con comprobación de `/health`, catálogo y reserva sin conexión, compra interrumpida y bandeja de avisos.
- **Pruebas:** backend 852 (5 de integración, 2 de concurrencia real), web 706, móvil 299.
- **Despliegue:** requiere aplicar `0017`–`0020` en producción antes del push. `vence_en` tiene valor por defecto para que el código anterior siga creando reservas mientras tanto.
- **Spec:** `.specs/modules/sincronizacion/P2-CU14-CU15-CU19-CU20-sin-conexion.md` · historial en `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/`.

### Fix · La reserva web y móvil ignoraba la franja elegida (defecto sin numerar: se numera al fusionar)
- **Móvil:** la hoja de reserva de `PantallaProductoDetalle` tenía el mismo defecto: franjas fijas («SÁBADO 11:00H») y la cita siempre a «ahora + 1 día», justo en el límite del vencimiento de 24 h. Usa ahora `franjasDeCita` (`core/sin_conexion/franjas_cita.dart`), con el mismo criterio que la web, y el 409 muestra las sucursales alternativas.
- **Causa (web):** el modal de reserva del detalle de producto ofrecía franjas fijas («MAÑANA 11:30H», «MAÑANA 16:30H», «VIERNES 12:00H»), pero siempre enviaba la cita para el día siguiente a las 11:30, eligiera lo que eligiera el cliente. Con el vencimiento de P2-CU15 (RN25: 24 h desde la creación por defecto), esa hora fija superaba el plazo en cuanto se reservaba antes de las 11:30 y el servidor la rechazaba con `CITA_FUERA_DE_PLAZO`.
- **Solución:** las horas se generan con `franjasDeCita` (`core/sin-conexion/franjas-cita.ts`) dentro del vencimiento de la empresa y del horario de la tienda, y se envía exactamente la elegida. El 409 por falta de stock muestra las sucursales alternativas que devuelve el servidor.

### Fix · Pruebas de integración que fallaban según la hora o con el esquema real (defecto sin numerar: se numera al fusionar)
- **Causa 1 (intermitente):** `test_login_de_empleado_con_suscripcion_vencida_403` y `test_cu12_suscripcion_vencida` vencían la suscripción con `current_date - 1` desde una conexión sin zona horaria, es decir, con la fecha UTC. Entre las 20:00 y las 24:00 de Bolivia esa fecha ya es «mañana», y «ayer» en UTC seguía siendo «hoy» para la aplicación (`core/tiempo.py`): la suscripción seguía vigente y las pruebas fallaban.
- **Causa 2:** `test_aislamiento_multitenant_tablas_nuevas_ia_ml_suscripcion` insertaba en `datasets_ml`, `modelos_ml`, `predicciones_ml` y `segmentos_clientes_ml` columnas que la migración `0019` no crea (`tipo`, `registros`, `horizonte_dias`…). Se saltaba sin avisar mientras la rama de pruebas estaba en `0016`, y empezó a fallar al aplicarle `0017`–`0019` para ensayar la `0020`.
- **Solución:** el `_contexto` de las pruebas fija también `TimeZone = America/La_Paz` en la transacción, como hace la aplicación. La prueba de ML usa las columnas reales de `0019` y sigue comprobando lo mismo (aislamiento entre empresas).

### Empresa de prueba Menshopping — P2-RF15
- **Qué:** segunda empresa del SaaS, de moda masculina, cargada en producción: plan Básico, sucursales en Santa Cruz y Beni (Trinidad, ciudad global nueva), 4 prendas en BOB (Bs 120 / 280 / 350 / 480) con tallas M y L, stock 5 + 5 y 2 + 2, y 5 empleados (administrador, encargado y cajero por sucursal). Sin ventas inventadas: las ventas son las reales hechas en la caja de cada sucursal.
- **Cómo:** `Ec-backend/scripts/cargar_menshopping.py` con los datos en `scripts/datos/menshopping.json` (sin contraseñas); una transacción, ensayo sin `--aplicar` y contraseña inicial por `getpass`. PNG del vestidor en `Ec-frontend/public/ar/menshopping_*.png`, desplegados antes de la carga.
- **Pruebas:** 14 unitarias del script y una de integración con rollback en `pruebas-multitenant` (aislamiento con FASHION STORE en ambos sentidos, directorio, login y catálogo). Ensayo aplicado en la rama de pruebas antes de producción.
- **Incidencia del CI:** la guarda de contraseñas en claro tomó por contraseña el identificador `"clave": "santacruz"` del archivo de datos. Se renombró a `codigo` en lugar de aflojar la guarda. En local no saltó porque la guarda solo revisa archivos ya versionados.
- **Spec:** `.specs/modules/plataforma/P2-RF15-menshopping.md` · historial en `.specs/finalized/P2-RF15-menshopping/`.

### Correcciones de Auditoría Parcial 2 — Trabajo de Plataforma, Reportes IA y ML (Tony)
- **CU10 (Bloqueante 1 y Punto 3 — Pagos con Stripe y moneda BOB):**
  - Vinculación estricta de pagos: `confirmar_cambio_o_renovacion` valida que el `PaymentIntent` de Stripe coincida exactamente en importe (`amount`), moneda (`currency`), `id_tenant`, `id_plan` y `meses`.
  - Anti-reutilización de pagos: bloqueo con índice único parcial `uq_historial_suscripcion_referencia_pago` en migración `0017` y validación de servicio (409 `REFERENCIA_PAGO_YA_UTILIZADA`).
  - Precios en `BOB` sin tipos de cambio manuales: se eliminaron tasas fijas de conversión (`TASAS_CAMBIO_BOB`), cobrando directamente en la moneda de la empresa y transmitiendo la moneda a Stripe.
- **CU23–CU25 (Bloqueante 2 — Aprendizaje automático real con scikit-learn y cero datos inventados):**
  - Motor ML reescrito con `scikit-learn`, `pandas` y `numpy` reales (`RandomForestRegressor`, `KMeans`, `StandardScaler`, `train_test_split` 70/15/15). Eliminado `_hash_fraccion`.
  - Cero datos inventados: prendas, variantes, sucursales y clientes provienen exclusivamente de las tablas de la empresa en PostgreSQL. Si no hay datos, se devuelve estado vacío sin nombres ficticios.
- **CU07 A1 (Punto 4 — Suscripciones):**
  - Al dar de alta una suscripción (`alta`), si la empresa ya tiene una suscripción vigente (`activa` o `prueba`), se rechaza con `409 SUSCRIPCION_VIGENTE_EXISTENTE` remitiendo a cambiar plan o renovar, eliminando la cancelación silenciosa previa.
- **CU06 A2 (Punto 5 — Planes):**
  - Se impide desactivar un plan si existen empresas con suscripciones vigentes (`409 PLAN_CON_EMPRESAS_SUSCRITAS`).
- **CU21 (Punto 6 — Reportes con IA):**
  - Rechazo explícito de reportes no implementados con `422 REPORTE_NO_EJECUTABLE`, impidiendo caídas silenciosas en consultas de reservas.
- **Hallazgos menores:**
  - Hora oficial de Bolivia: sustituido `datetime.now(timezone.utc).date()` por `core.tiempo.hoy()` y `core.tiempo.ahora()` en todos los módulos de plataforma y comercial.
  - Validación de correo en CU05 con función `SECURITY DEFINER` `correo_ocupado()`.
  - Configuración inicial de empresa en `cu05` fijada a moneda `BOB` y zona `America/La_Paz` (evitando violación de CHECK constraints de migración 0016).
  - Pruebas de integración multitenant para tablas nuevas (`solicitudes_reporte_ia`, `datasets_ml`, `modelos_ml`, `predicciones_ml`, `segmentos_clientes_ml`, `historial_suscripcion`) en `tests/integracion/test_multitenant.py`.
  - Normalización de URL en `test_esquema_bd.py` para compatibilidad nativa con `psycopg` v3.
  - Especificaciones SDD sincronizadas con migraciones `0017–0019`, promovidas a `.specs/finalized/` y especificaciones permanentes creadas en `.specs/modules/`.

### Fix · «Mi perfil» del empleado (defecto sin numerar: se numera al fusionar)
- **Causa:**
  - «MI CUENTA» en el dashboard, productos, categorías y sucursales enlazaba a `/perfil`, una ruta antigua del cliente que desde P2-CU02 redirige al directorio de tiendas.
  - `/admin/perfil` (desde el 2026-09-22) reutilizaba la pantalla de perfil del cliente: `GET /api/v1/perfil` solo admite clientes y respondía 403 a cualquier empleado. La pantalla mostraba entonces sus textos fijos de FASHION STORE («Consola Administrativa Corporativa», «12 módulos», foto y tallas de mujer).
  - Un empleado no tenía forma de cambiar su propia contraseña.
- **Solución:**
  - `GET/PATCH /api/v1/mi-perfil-empleado` para administrador, encargado y cajero: datos, rol, empresa con su moneda y sucursales autorizadas (RN07).
  - `POST /api/v1/mi-perfil-empleado/contrasena`: cambio de la propia contraseña pidiendo la actual; la bitácora nunca guarda contraseñas.
  - Página «Mi perfil» en `/admin/perfil`, con la marca de la empresa del empleado; los enlaces del panel apuntan a ella y el cajero entra desde la caja. El perfil del cliente queda solo para clientes.
- **Pruebas:** 10 unitarias y 2 de integración contra la rama de pruebas (empresa y sucursales reales; cambio de contraseña con login posterior); 6 de web.

### Integración continua y revisión obligatoria de PR
- **Motivo:** el PR #2 se fusionó en `main` con solo los checks de Vercel. Traía una migración (`0017`) con el hash y la contraseña en claro del super administrador en un repositorio público, y tres migraciones sin aplicar en producción. Ninguna de las pruebas locales se ejecutaba en GitHub.
- **CI** (`.github/workflows/ci.yml`): backend, migraciones en un PostgreSQL temporal (cadena completa, `downgrade`/`upgrade` y `test_esquema_bd`), integración contra `pruebas-multitenant`, web, móvil y guardas (`.github/scripts/guardas.sh` y gitleaks). No toca producción.
- **Revisión:** `.github/CODEOWNERS` según `reparticion.md` y plantilla de PR con las casillas de spec, suites, secretos y migraciones.
- **Primer resultado sobre `main`:** las guardas detectan el hash y la contraseña de la `0017` y una conversión fija `'EUR' → 7.5` en `mi-suscripcion-admin.component.ts`; ambos quedan para su responsable.

### Aprendizaje Automático y Analítica Predictiva en Bolivianos — P2-CU23 (Gestionar datos y modelos de aprendizaje), P2-CU24 (Consultar predicciones) y P2-CU25 (Consultar segmentos de clientes)
- **Base de datos (migración `0019_aprendizaje_automatico_ml`):** tablas multitenant `fashionstore.datasets_ml`, `fashionstore.modelos_ml`, `fashionstore.predicciones_ml` y `fashionstore.segmentos_clientes_ml` con `id_tenant`, políticas `ROW LEVEL SECURITY` y restricción `CHECK (probabilidad >= 0.0000 AND probabilidad <= 1.0000)` (`RN50`).
- **Backend (`Ec-backend`):** paquete `app/modules/comercial/cu23_cu25_aprendizaje_ml/` expuesto en `/api/v1/aprendizaje-ml` para el `administrador` de empresa:
  - **CU23:** creación de datasets (`sintetico`, `real`, `mixto`) con validación de datos reales mínimos (`CU23 A1` → `422 DATOS_INSUFICIENTES_ML`), pipeline de preprocesamiento (limpieza de nulos, codificación one-hot y escalado en **Bolivianos `Bs. / BOB`**), entrenamiento de modelos `supervisado` (exigiendo `variable_objetivo` según `CU23 A2` / `RN49`) y `no_supervisado` (clustering RFM), evaluación guardando métricas de `entrenamiento`, `validacion` y `prueba` (`RN49`), activación y archivado conservando métricas (`CU23 A5`).
  - **CU24:** consulta de predicciones del modelo supervisado activo con filtros por producto, sucursal y período, probabilidades en `[0, 1]` (`RN50`), ingresos esperados en **Bolivianos (`Bs. / BOB`)** y equivalente en `USD` (`T.C. 6.96 Bs./USD`), aviso cuando el modelo no está activo (`CU24 A1`) o cuando se entrenó con datos sintéticos (`CU24 A3`).
  - **CU25:** consulta de segmentos de clientes del modelo no supervisado activo con tamaño, características definitorias (ticket promedio en **Bolivianos `Bs.`**, frecuencia y recencia), listado de clientas del segmento e indicación de grupos sin clientes (`CU25 A2`) o entrenamiento con datos sintéticos (`CU25 A3`).
- **Frontend Web (`Ec-frontend`):** módulo `cu23_cu25_aprendizaje_ml/` (`AprendizajeMlAdminComponent`, `AprendizajeMlService`) en `/admin/aprendizaje-ml` con 3 pestañas integradas (`CU23`, `CU24`, `CU25`), importes en **Bolivianos (`Bs. / BOB`)** y tarjeta de acceso en `admin-dashboard.component.html`.
- **Pruebas:** `pytest` 77/77 en `tests/modules/comercial/` y `tests/modules/plataforma/` · `ng test` 39/39 en specs afectadas · `tsc --noEmit` y `ng build` limpios.

### Catálogo de Reportes Permitidos y Generación de Reportes con IA en Bolivianos — P2-CU22 (Catálogo de reportes permitidos) y P2-CU21 (Generar reporte con IA)
- **Base de datos (migración `0018_catalogo_reportes_ia`):** tabla global `fashionstore.catalogo_reportes_ia` con 4 reportes semilla (`ventas_por_sucursal`, `top_productos_vendidos`, `inventario_por_sucursal`, `reservas_por_estado_sucursal`) y ampliación de `fashionstore.solicitudes_reporte_ia` con `estado`, `interpretacion`, `formato_visualizacion`, `mensaje_estado` y `exportaciones` (RN48).
- **Backend (`Ec-backend`):**
  - **CU22 (`app/modules/plataforma/cu22_catalogo_reportes/`):** endpoints bajo `/api/v1/plataforma/catalogo-reportes` para el `super_administrador`, validando vistas autorizadas (`CU22 A1`), métricas con expresión y tipos de gráfico permitidos (`CU22 A2`) y desactivación sin perder solicitudes históricas (`CU22 A3`).
  - **CU21 (`app/modules/comercial/cu21_reportes_ia/`):** endpoints bajo `/api/v1/reportes-ia` para el `administrador` de empresa con validación `SuscripcionServicio.validar(db, funcionalidad="reportes_ia")` (`RN44` / `CU21 A3`), intérprete semántico de lenguaje natural + Gemini opcional sin enviar datos del negocio (`RN45`), detección de solicitudes ambiguas (`CU21 A1`), no soportadas (`CU21 A2`) y filtros de otra empresa (`CU21 A7` / `RN46`), consultas controladas expresadas en **Bolivianos (`Bs. / BOB`)** con tipo de cambio oficial (`6.96 Bs./USD`) y exportación a **PDF** y **Excel (`.xlsx`)** con registro de descargas (`RN48`).
- **Frontend Web (`Ec-frontend`):** pestaña `Catálogo Reportes IA (CU22)` en `/admin/plataforma` y módulo `cu21_reportes_ia/` (`ReportesIaAdminComponent`, `ReportesIaService`) en `/admin/reportes-ia` con entrada por texto y micrófono (`SpeechRecognition` + `CU21 A4`), gráficos interactivos (`barras`, `linea`, `torta`), tabla en **Bolivianos (`Bs.`)**, exportación PDF/Excel e historial.
- **Pruebas:** `pytest` 72/72 en `tests/modules/comercial/test_p2_cu22_cu21_reportes_ia_unitarias.py` y `tests/modules/plataforma/` · `ng test` 35/35 en specs afectadas · `tsc --noEmit` y `ng build` limpios.

### Suscripción de la Empresa y Renovación con Stripe — P2-CU09 (Consultar suscripción y uso del plan) y P2-CU10 (Cambiar de plan y renovar suscripción)
- **Backend (`Ec-backend`):** paquete `app/modules/plataforma/cu09_cu10_suscripcion_empresa/` expuesto en `/api/v1/plataforma/mi-suscripcion` para el `administrador` de la empresa (permitiendo el acceso aun con suscripción vencida según CU09 A1 y CU10 A4):
  - **CU09:** estado de suscripción y vigencia efectiva (`dias_restantes`, `vigente`, `proxima_a_vencer`), consumo frente a límites de sucursales activas y empleados activos (RN15, CU09 A2), listado de sucursales activas, funcionalidades incluidas y no incluidas (RN16), historial de suscripción (RN17) y conversión automática a **Bolivianos (`BOB` / `Bs.`)** con tipo de cambio oficial BCB (`6.96 Bs./USD`, `7.50 Bs./EUR`).
  - **CU10:** catálogo de planes activos con evaluación de compatibilidad frente al uso actual (`CU10 A1` → `409 USO_SUPERA_LIMITE_PLAN` indicando qué sucursales activas deben desactivarse antes de bajar de plan), apertura y confirmación de `PaymentIntent` con `StripeService` (`CU10 A2` → `402 PAGO_RECHAZADO` sin alterar el plan ni el vencimiento actuales si la tarjeta es rechazada), actualización de vigencia y registro en `historial_suscripcion` (RN17) y `bitacora`.
- **Frontend Web (`Ec-frontend`):** módulo `mi_suscripcion/` (`MiSuscripcionAdminComponent`, `MiSuscripcionService`) en `/admin/suscripcion` con visualización de importes en **Bolivianos (`Bs. / BOB`)** y tipo de cambio, medidores de uso, comparador de planes, pasarela de prueba Stripe de dos pasos y tarjeta de acceso en `admin-dashboard.component.html`.
- **Pruebas:** `pytest` 63/63 en `tests/modules/plataforma/` · `ng test` 44/44 en specs afectadas · `tsc --noEmit` y `ng build` limpios.

### Panel del Super Administrador SaaS — P2-CU05 (Empresas y supervisión), P2-CU06 (Planes y funcionalidades), P2-CU07 (Suscripciones de empresas) y P2-CU08 (Catálogos globales)
- **Base de datos (migración `0017_superadmin_catalogos`) y aprovisionamiento fuera de banda (`scripts/crear_superadmin.py`):** columna `activo BOOLEAN NOT NULL DEFAULT true` en las tablas globales `fashionstore.ciudades`, `fashionstore.tallas` y `fashionstore.colores` (para desactivar elementos en uso sin eliminarlos según P2-CU08 A2). Sin credenciales ni hashes fijos en migraciones; el alta o rotación de `super_administrador` se ejecuta fuera de banda con `scripts/crear_superadmin.py` (variables de entorno o `getpass`) y `dependencias.py` bloquea permanentemente por digest SHA-256 cualquier contraseña o hash expuesto previamente.
- **Backend (`Ec-backend`):** dependencia `exigir_super_administrador` en `app/modules/plataforma/dependencias.py` que verifica el rol y activa `app.modo_plataforma = 'on'`. Paquetes `cu05_empresas_supervision`, `cu06_planes_funcionalidades`, `cu07_suscripciones` y `cu08_catalogos_globales` expuestos bajo `/api/v1/plataforma`:
  - **CU05:** listado y detalle de empresas con indicadores agregados (sin exponer clientes ni comprobantes privados), alta atómica de `Tenant` + `ConfiguracionTenant` + `Suscripcion` + `HistorialSuscripcion` + cuenta de `administrador` + ficha en `empleados`, cambio de estado con validación de suspensión previa para baja (RN10), métricas globales y bitácora de plataforma.
  - **CU06:** catálogo de funcionalidades (RN11), alta/edición de planes con advertencias cuando empresas activas superan un límite reducido (Curso Alterno A1) y activación/desactivación de planes (Curso Alterno A2).
  - **CU07:** listado de suscripciones con consumo frente a límites, historial inmutable (RN17) y operaciones (`alta`, `cambio_plan`, `renovacion`, `suspension`, `reactivacion`, `cancelacion`) bloqueando cambios a un plan cuyo límite es menor que el uso actual (Curso Alterno A1).
  - **CU08:** CRUD de ciudades, tallas y colores globales (RN21), bloqueando eliminación física con `409 ELEMENTO_CATALOGO_EN_USO` si tienen sucursales o variantes asociadas y permitiendo su desactivación (Curso Alterno A2).
- **Frontend Web (`Ec-frontend`):** vista `/admin/plataforma` (`SuperadminPanelComponent`, `SuperadminService`) protegida por `authGuard` + `roleGuard(['super_administrador'])`, con 5 pestañas operativas y redirección automática tras login para `super_administrador`.
- **Pruebas:** `pytest` 55/55 en `tests/modules/plataforma/` · `ng test` 25/25 en specs afectadas · `tsc --noEmit` y `ng build` limpios.

## [Unreleased] - 2026-11-08 (Parcial 2)

### Fundación Multitenant — P2-CU13 (Aislar datos por empresa) y P2-CU12 (Validar suscripción y límites del plan)
- **Base de datos (migraciones `0012`–`0014`):** tablas `tenants`, `planes`, `funcionalidades`, `plan_funcionalidades`, `suscripciones`, `historial_suscripcion`, `configuracion_tenant`, `cliente_tenant` y `empleado_sucursal`. FASHION STORE es la empresa 1 (plan Profesional hasta 2027-11-08). `id_tenant` en 24 tablas de negocio, `usuarios` y `bitacora`, con valor por defecto tomado del contexto de la transacción; claves únicas por empresa; 42 claves foráneas compuestas; Row Level Security en 31 tablas; vistas con `security_invoker`; rol `super_administrador`. La aplicación se conecta con `fashionstore_app` (sin `BYPASSRLS`) y las migraciones con el dueño (`DATABASE_URL_MIGRACIONES`). El `downgrade` restaura el esquema original exacto (verificado).
- **Backend:** empresa de cada petición por la cabecera `X-Tenant` o `TENANT_POR_DEFECTO` (transición), aplicada en cada transacción; JWT con `id_tenant` (el token manda sobre la cabecera); login con `codigo_empresa` opcional; registro de clientes por empresa; validación de suscripción, funcionalidades y límites del plan en sucursales, empleados, reservas, checkout, venta en caja y reportes; webhook de Stripe con modo plataforma.
- **Pruebas:** `pytest` 613/613, de ellas 18 de integración contra PostgreSQL real con el rol de la aplicación. En producción: humo 42 GET × 5 perfiles sin 5xx y escrituras de extremo a extremo 21/21.
- **Efecto para los usuarios:** todos deben iniciar sesión de nuevo una vez (los tokens anteriores no llevan empresa). Web y móvil no cambian en este ciclo.
- Defectos 53–56 de la bitácora.

### Acceso por Empresa — P2-CU02 (Iniciar sesión) y P2-CU01 (Registrarse)
- **Base de datos (migración `0015`):** correo único en toda la plataforma (`uq_usuarios_email`); funciones `SECURITY DEFINER` `cuenta_por_email` (solo `id_usuario` e `id_tenant`) y `empresas_disponibles` (empresas activas con suscripción vigente); códigos de empresa reservados (`chk_tenants_codigo_reservado`). Aplicada a mano en producción antes del push (0 correos repetidos).
- **Backend:** login solo con correo y contraseña para todos los roles; la cuenta determina la empresa del empleado, que además necesita suscripción vigente. El token del cliente no lleva empresa: navega con `X-Tenant`. Endpoints `GET /tenants`, `GET /tenants/{codigo}`, `GET /mis-empresas` y `POST /mis-empresas` («Registrarme en esta tienda»). Se retira `TENANT_POR_DEFECTO`: sin tienda indicada no se ve ninguna empresa.
- **Web:** directorio de tiendas en `/`; portal de cada tienda en `/{codigo}/...` con su login, registro y recuperación; aviso «Registrarme en esta tienda»; marca y títulos con el nombre de la tienda; las rutas antiguas del cliente redirigen al directorio.
- **Móvil:** pantalla de selección de tienda entre el login y el hub, «Cambiar de tienda» en Perfil, `X-Tenant` en todas las peticiones (`ClienteHttpApi`) y marca por tienda.
- **Pruebas:** `pytest` 624, `ng test` 638 y `flutter test` 276, todas en verde. En producción: API pública, directorio, portal y login comprobados; recorridos con sesión probados por el usuario en web y móvil.
- **Efecto para los usuarios:** las apps móviles anteriores dejan de ver datos (no envían la tienda); hay que instalar el APK nuevo.
- Defectos 57–62 de la bitácora.

### Usuarios y Sucursales por Empresa — P2-CU03 (Gestionar usuarios y roles) y P2-CU04 (Gestionar sucursales)
- **Seguridad:** el administrador de una empresa ya no ve ni modifica clientes ni al super administrador (defecto 63).
- **Backend:** sucursales autorizadas por empleado con una principal (`empleado_sucursal`), aplicadas en caja, cobro en efectivo, inventario, ventas y reservas, indicadores y reportes por voz (RN07); solo se asignan roles de empleado; `GET /mis-sucursales` y `GET /admin/sucursales/uso-plan`; las ciudades son de solo lectura para el administrador (su gestión pasa a P2-CU08); límites del plan serializados por empresa con `pg_advisory_xact_lock` y límite de empleados al reactivar; bitácora de usuarios y sucursales. Sin migración.
- **Web:** casillas de sucursales autorizadas y principal en «Usuarios», sin el rol cliente; uso del plan y aviso de límite en «Sucursales»; pestaña «Ciudades» de solo lectura; selector de sucursal en la caja para el cajero o encargado con más de una.
- **Pruebas:** `pytest` 676 (integración contra la rama de pruebas: fuga cerrada, empleado con dos sucursales, uso del plan, bloqueo por empresa) y `ng test` 644, en verde; `ng build` correcto.
- Defectos 63–65 de la bitácora.

### Parámetros de la Empresa — P2-CU11 (Configurar parámetros de la empresa)
- **Backend:** `GET` y `PUT /api/v1/admin/configuracion` (solo administrador; guardar exige suscripción vigente) sobre `configuracion_tenant`, que ya existía desde `0012`. Rangos: reserva 1–168 h, cambio de prenda 0–90 días, antigüedad sin conexión 1–30 días. Moneda y zona horaria solo se consultan. La fila que falte se crea con los valores por defecto. Bitácora `CONFIGURACION_MODIFICADA` con lo que cambió. `ParametrosEmpresaServicio.vigentes(db)` para los casos de uso que aplican cada parámetro. Sin migración.
- **Web:** página `/admin/configuracion` con su tarjeta en el panel y el aviso de CU11 A2 al desactivar la operación sin conexión.
- **Alcance:** CU11 configura; los parámetros se aplican en CU15 (vencimiento de reservas), CU18 (plazo de cambio), CU14 y CU19 (operación sin conexión). Cada operación guardará el valor que la rige al crearse.
- **Pruebas:** `pytest` 695 (2 de integración contra la rama de pruebas) y `ng test` 651, en verde; `ng build` correcto.
- **Pendiente para CU15:** el formulario de reserva web fija la cita en «mañana a las 11:30» sin usar la franja elegida y, sin sucursal elegida, usa el id `1`.

### Moneda y Zona Horaria de Bolivia — fix de P2-CU11
- **Base de datos (migración `0016`):** moneda `BOB` o `USD` y zona `America/La_Paz` (CHECK); todas las empresas pasan a BOB sin convertir importes (decisión del usuario: 120 € pasan a Bs 120); `empresas_disponibles()` devuelve la moneda. Aplicada a mano en producción antes del push.
- **Backend:** «hoy» con la hora de Bolivia en todo el backend (`core/tiempo.py` y `TimeZone` de cada transacción de PostgreSQL); moneda y zona editables en Configuración, con la moneda bloqueada si la empresa tiene ventas (409 `MONEDA_CON_OPERACIONES`); moneda en directorio, portal, login, carrito, checkout y pago; Stripe cobra en la moneda de la empresa; `formatear_importe` (`Bs 1.234,50`, `US$ 1.234,50`) en el comprobante y los textos; IVA del 13 %; `tzdata` en las dependencias.
- **Web:** pipe `importe` y moneda de la tienda (portal o empresa del empleado); 74 importes sin «€»; selectores de moneda y zona en Configuración.
- **Móvil:** `EmpresaTienda.moneda` y `formatoImporte`; 31 importes sin «€»; IVA 13 %.
- **Pruebas:** `pytest` 715, `ng test` 656 y `flutter test` 280, en verde.
- **Efecto para los usuarios:** precios, ventas y pagos de FASHION STORE se leen en Bs con el mismo número. Las apps móviles anteriores siguen mostrando «€» hasta instalar el APK nuevo.
- Defectos 66–68 de la bitácora.

## [Unreleased] - 2026-11-08

### Implementación y Cierre — CU31 (Registrar venta presencial) y CU32 (Procesar venta y emitir comprobante)
- **Backend (`Ec-backend`):** paquete `compras_pagos/cu31_cu32_punto_venta/` bajo `/api/v1/pos` para administrador, encargado y cajero (el administrador elige boutique). Venta en caja espontánea o desde reserva con retención de stock (`reserva` → `venta_confirmada` al cobrar; `liberacion_reserva` de lo que el cliente deja), cobro en efectivo (cambio calculado en servidor), tarjeta (con registro del rechazo del datáfono), QR o transferencia, anulación con motivo y vencimiento perezoso a las 2 h. Comprobante en PDF de 80 mm (`GET /pos/ventas/{id}/comprobante.pdf`). Búsquedas de prenda (nombre, categoría o SKU), cliente (nombre o correo), reservas activas del cliente y cupones vigentes. Las reservas se operan por `reservas/atencion_caja.py`. 37 pruebas propias y verificación de extremo a extremo contra Neon con rollback.
- **Frontend Web (`Ec-frontend`):** `/admin/pos` con pestañas «Nueva venta», «Pendientes y del día» y «Pedidos web por cobrar» (cobro en efectivo de CU16), ticket imprimible de 80 mm y descarga del PDF. Totales siempre desde `POST /pos/ventas/previsualizar`. 19 pruebas de la página.
- **Mobile:** excluido por especificación (el cajero opera en la web).
- **Métricas:** `pytest` 567/567 · `ng test` 624/624 · `ng build` limpio. Defectos 49–52 de la bitácora.

## [Unreleased] - 2026-11-07

### Implementación y Cierre Integral — CU17 (Historial de Compras) y CU16 (Pagos, Webhook y Caja Mostrador)
- **CU17 - Consultar historial de compras personales (Fullstack):**
  - **Backend (`Ec-backend`):** Implementado endpoint `GET /api/v1/ventas/mias` con paginación, filtros opcionales de estado y fecha, retorno de líneas con SKU, producto, variante, precio y subtotales reales de base de datos PostgreSQL. Suite de pruebas con 4 tests específicos (`test_cu17_historial_compras.py`).
  - **Frontend Web (`Ec-frontend`):** Vista de historial de compras en `/perfil` (`PerfilComponent`, `PerfilService`), eliminando datos estáticos y renderizando compras pagadas/pendientes, comprobantes, montos y prendas reales. 9 pruebas unitarias actualizadas.
  - **Mobile (`Ec-mobile`):** Modelos `PerfilDto`, repositorio `PerfilRepositorio`, `PerfilBloc` y `PantallaPerfil` consumiendo el historial real paginado sin datos inventados. Pruebas de BLoC y widgets actualizadas.
- **CU16 - Realizar Pago Electrónico (Ronda 3 - Webhook Stripe, Efectivo en Boutique y Caja Mostrador):**
  - **Backend (`Ec-backend`):** Endpoint `POST /api/v1/pagos/webhook` para reconciliación asíncrona de Stripe (`payment_intent.succeeded` y `payment_intent.payment_failed`) con validación criptográfica de firma `Stripe-Signature` y fallback de simulación. Consolidación de inventario y auditoría idempotente. 6 pruebas nuevas de webhook en `test_cu16_pagos.py` (55/55 pruebas en verde).
  - **Frontend Web (`Ec-frontend`):** Opción de «Pago en Efectivo en Sucursal» (CP-33) en `CheckoutPagoComponent` restringida a `tipo_entrega === 'recogida_boutique'`, con recibo de 24 horas de reserva de cortesía. Acciones de caja en mostrador (CP-38) integradas en el modal de detalle de `VentasReservasAdminComponent` (CU28) para confirmar o cancelar cobros en efectivo con actualización reactiva. Pruebas Vitest ampliadas (548/548 en verde).
  - **Mobile (`Ec-mobile`):** Datasource `pago_api.dart` (`registrarPagoEfectivo`), orquestación en `PagoBloc.confirmarYPagar()`, opción condicional de efectivo en `CheckoutPaymentScreen` con aviso de reserva de 24 horas y recibo adaptado. Corrección de restricción de layout horizontal en encabezados de aviso con `Expanded`. Pruebas en verde (216/216).
- **Métricas globales de validación:**
  - Backend: 497/497 pasados (`pytest`).
  - Frontend Web: 548/548 pasados (`vitest`) y build de producción exitoso.
  - Mobile: 216/216 pasados (`flutter test`) y `flutter analyze` con 0 incidencias.

## [2.8.0] - 2026-09-27

### Promocion a Baseline Permanente
- **CU07 - Consultar detalle de producto, CU08 - Consultar tallas/colores/caracteristicas, CU09 - Consultar disponibilidad por sucursal y CU12 - Reservar varias prendas (cita de prueba presencial):** Promovidos oficialmente a especificacion permanente del sistema. El cambio cubria ademas la maqueta aislada de CU10 (Probador Virtual AR), sin logica ni dependencias 3D en este ciclo.
- **CU31 - Generar reportes ejecutivos y consultas por voz (Analitica, Emision Binaria y Reconocimiento de Voz):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU31-reportes-voz.md`](.specs/modules/comercial/CU31-reportes-voz.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU07-CU08-CU09-CU12-detalle-producto/` (`spec.md`, `plan.md`, `tasks.md`, `checkpoint.md`, `change-detalle-producto-reservas.md`) y en `.specs/finalized/CU31/` (`spec.md`, `design.md`, `tasks.md`); limpiados los directorios de cambios temporales `.specs/changes/` y `.specs/changes/CU31/`.
- **Cierre de deuda pendiente (CP-19/CP-20):** el gate inicial del 2026-09-21 dejaba dos checkpoints abiertos por datos fabricados (defecto `D-09`, ver entradas 61 y 62 abajo). Se corrigieron y ahora los 20 checkpoints (`CP-01…CP-20`) quedan aprobados.
- **Exclusion Formal Justificada de Ec-mobile (CU31):** Ratificada documentalmente la exclusion justificada de la aplicacion movil (`Ec-mobile`). La emision de reportes ejecutivos contables, compilacion de hojas de calculo complejas, generacion de documentos PDF vectoriales y procesamiento de comandos de trastienda son competencias exclusivas del back-office en la consola web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni dependencias de reporte.
- **Validacion por bloque de trabajo** (cifras del punto de promocion de cada cambio; ver `[Unreleased]`/entradas mas recientes para la cifra vigente tras la fusion de ambos):
  - CU07-CU12: Backend 413/413, Web 467/467 (48 archivos), Mobile 150/150.
  - CU31: Backend 407/407 (20/20 especificos en `test_cu31_reportes_voz.py`; motores de generacion binaria en memoria — `GeneradorExcel` con `openpyxl` aplicando paleta Obsidian & Camel y formulas SUM, `GeneradorPDF` con `reportlab` horizontal Letter con encabezado corporativo y pie paginado, `GeneradorCSV` con prefijo BOM UTF-8 `﻿`; parser lexico-semantico determinista de voz `ParserComandosVoz` sin dependencias externas para resolucion de modulos, fechas, sedes y formatos; endpoints REST en `/api/v1/admin/reportes` con streaming binario (`StreamingResponse`) y cabeceras `Content-Disposition`; RBAC estricto con aislamiento por sede y bloqueo de bitacora para `encargado_sucursal`; emision defensiva del evento de auditoria `EXPORTAR_REPORTE` en `fashionstore.bitacora`), Web 448/448 (`ng build` limpio; 8/8 en `reportes-admin.component.spec.ts`, 7/7 en `voz-reconocimiento.service.spec.ts`, 6/6 en `reportes-admin.service.spec.ts`, 27/27 en `admin-dashboard.component.spec.ts` — decimotercera tarjeta corporativa en `AdminDashboardComponent` bajo "Analitica y Reportes", servicio `VozReconocimientoService` sobre Web Speech API nativa en `es-BO`, servicio `ReportesAdminService` con descarga reactiva de Blobs, vista `ReportesAdminComponent` en `/admin/reportes`).

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 74. Despliegue en Render Fallaba al Arrancar: `openpyxl`/`reportlab` Ausentes de `requirements.txt`
- **Causa:** CU31 (reportes-voz) importa `openpyxl` y `reportlab` en `modules/comercial/cu31_reportes_voz/generadores/`. Ambas librerias estaban declaradas en `pyproject.toml` (fuente de verdad para el entorno de desarrollo local, ya instaladas en el `.venv`) pero nunca se propagaron a `requirements.txt`, que es el archivo que `render.yaml` usa literalmente en su `buildCommand` (`pip install -r requirements.txt`). El build de Render completaba sin errores porque `pip install` no valida imports; el proceso arrancaba con `uvicorn app.main:app`, que al importar la cadena de routers llegaba hasta `generador_excel.py` y fallaba con `ModuleNotFoundError: No module named 'openpyxl'`, terminando con `Exited with status 1` sin mas contexto visible en el resumen del log de Render.
- **Diagnostico:** reproducido localmente instalando en un venv nuevo las mismas versiones exactas que Render resolvio en el build fallido (Python 3.14, `fastapi==0.141.1`, `sqlalchemy==2.1.1`, `starlette==1.7.0`, sin pins en `requirements.txt`) e importando `app.main` directamente: mismo `ModuleNotFoundError`. Instalar `openpyxl`/`reportlab` en ese mismo venv resolvio el import sin tocar codigo.
- **Solucion:** anadidas `openpyxl>=3.1.0` y `reportlab>=4.0.0` a `requirements.txt`, alineandolo con `pyproject.toml`.
- **Verificacion:** import de `app.main` exitoso con las versiones que Render realmente instala; suite backend 487/487 sin cambios de codigo.
- **Leccion:** `requirements.txt` y `pyproject.toml` son dos manifiestos de dependencias mantenidos a mano por separado en este repositorio — toda nueva dependencia debe anadirse a ambos, o Render (que solo lee `requirements.txt`) queda desincronizado del entorno de desarrollo sin que ningun test local lo detecte.

#### 61. Datos Fabricados en Disponibilidad Multisede (CP-20, `CU07-CU08-CU09-CU12-detalle-producto`)
- **Causa:** `DisponibilidadServicio.consultar_disponibilidad` (`app/modules/catalogo/cu09_disponibilidad/servicio.py`) sustituia la lista real de `obtener_sucursales_activas` por tres boutiques ficticias (`sucursales_mock`: Flagship Serrano, Boutique Saint-Honore y un "Madrid Central Atelier Hub") cuando `fashionstore.sucursales` no devolvia filas, ofreciendo existencias inventadas que la reserva rechazaba despues.
- **Solucion:** Eliminada la rama de relleno; sin sucursales activas la respuesta trae `sucursales: []` y `total_disponible_global: 0`, conforme a la regla de dominio "cero datos inventados". Prueba de regresion: `tests/modules/catalogo/test_cu09_disponibilidad.py::test_consultar_disponibilidad_sin_sucursales_devuelve_lista_vacia`.

#### 62. Tallas y Colores Fabricados en Ficha de Producto (CP-20, `CU07-CU08-CU09-CU12-detalle-producto`)
- **Causa:** `ProductoDetalleServicio.consultar_detalle_producto` (`app/modules/catalogo/cu07_detalle_producto/servicio.py`) rellenaba `tallas_disponibles` con 5 tallas fijas (34-42) y `colores_disponibles` con 4 colores fijos (Seda Marfil Natural, Obsidian Negro, Camel Suave, Vino Borgona) cuando el producto no tenia `variantes_producto` en base de datos, sin vinculo alguno con la prenda real.
- **Solucion:** Eliminado el bloque de relleno; un producto sin variantes ahora devuelve `variantes`, `tallas_disponibles` y `colores_disponibles` como listas vacias, y la interfaz muestra su estado vacio. Prueba de regresion: `tests/modules/catalogo/test_cu07_detalle_producto.py::test_consultar_detalle_producto_sin_variantes_no_inventa_tallas_ni_colores`.

#### 73. Mobile: Pantalla "Mis Reservas" y Tarjeta del Perfil sin Datos Inventados (CU13/CU14, Mobile)
- **Causa:** igual que en Web (entrada 72), la tarjeta de "Bolsa" en `pantalla_perfil.dart` mostraba literales fijos (`"3"`, `"Artículos · 1.250 €"`) sin relacion con la bolsa real del cliente, y la app movil no tenia ningun modulo de reservas: CU12 (reservar) nunca se habia construido en Mobile, ni CU13/CU14 (consultar/cancelar).
- **Solucion:** modulo `modulos/reservas/cu13_consultar_cancelar_reservas/` completo, espejo de Web y del contrato del backend: `ReservaDto`/`MisReservasDto` con `fromJson` tolerante (`precio_unitario` via `parsearImporte`, Decimal serializado como cadena JSON), `ReservasApiImpl` (mismo patron que `PagoApiImpl`: cabeceras, manejo de `SocketException`/`TimeoutException`, 401 -> `SesionManager.notificarSesionExpirada`), `MisReservasBloc` con estados sellados (`Inicial`/`Cargando`/`Listo`/`Error`) y un campo `cancelando`/`errorCancelacion` separado del estado de la lista para que una cancelacion en vuelo no la oculte. La tarjeta del Perfil pasa a "Mis Reservas" (numero real de reservas activas y proxima cita, o su estado vacio) y abre `PantallaMisReservas` por `Navigator.push` con el token propagado — pantalla hoja (`AppBar` con `BackButton`, sin `bottomNavigationBar`), con pestañas Proximas/Historial, `RefreshIndicator`, y una hoja inferior (`HojaCancelarReserva`) con motivo obligatorio (3-250 caracteres) que permanece abierta mostrando el error del servidor si la cancelacion es rechazada.
- **Verificacion:** 19 pruebas nuevas (`reserva_dto_test.dart`, `mis_reservas_bloc_test.dart`, `pantalla_mis_reservas_test.dart`) con payloads literales del backend, mas el ajuste de `pantalla_perfil_test.dart` para inyectar el nuevo bloc. Mobile 209/209 (190 previas + 19 nuevas), `dart analyze` limpio. Se confirmo que `pantalla_principal_hub_test.dart` sigue en verde sin inyectar un mock del nuevo bloc: sigue el mismo patron ya existente con `PerfilBloc` (un fallo de red real en el entorno de test se captura y transiciona a un estado de error controlado, sin excepcion no controlada).
- **Cierre de ciclo:** con este bloque, CU13/CU14 queda completo en los tres stacks (Backend, Web, Mobile) — ver `tasks.md`/`checkpoint.md` de `CU13-CU14-consultar-cancelar-reservas`, pendiente de promocion a `.specs/finalized/`.

#### 72. Web: Pantalla "Mis Reservas" y Tarjeta del Perfil sin Datos Inventados (CU13/CU14, Web)
- **Causa:** la tarjeta "Bolsa de Compra" del Perfil mostraba el literal fijo "3 Artículos seleccionados · 1.250 €" y un botón "IR AL CHECKOUT" sin accion, mientras la bolsa real del cliente podia estar vacia — el mismo defecto de "cero datos inventados" ya corregido en CU07-CU12. Ademas no existia ninguna pantalla donde el cliente pudiera consultar o cancelar sus reservas de CU12/CU13/CU14.
- **Solucion:** la tarjeta pasa a "Mis Reservas", alimentada por `MisReservasService` (Signals) contra `GET /reservas/mias`: numero real de reservas activas, proxima cita y boutique, con su propio estado de carga y vacio. Nueva pantalla `/reservas` (hoja Hub-and-Spoke, fuera del layout principal, con `← Volver`): pestañas Proximas/Historial, tarjetas con badge de estado (colores del design system), prendas con talla/color/miniatura, y boton "Cancelar reserva" visible solo cuando el backend indica `puede_cancelar`. Modal de cancelacion con motivo obligatorio (3-250 caracteres); tras confirmar, el servicio recarga la lista completa desde el servidor en vez de derivar el nuevo estado en el cliente.
- **Verificacion:** 31 pruebas nuevas con payloads literales del backend. Web 538/538, `tsc --noEmit` limpio, `ng build` de produccion exitoso, `ng serve` sirviendo `/perfil` y `/reservas` verificado.

#### 71. Reservas Pendientes Retenian Stock Indefinidamente al no Vencer Nunca (CU13/CU14, Backend)
- **Causa:** CU12 crea reservas de citas de prueba presencial apartando existencias (`cantidad_disponible -> cantidad_reservada`), pero el proyecto no tenia ningun endpoint para consultarlas ni cancelarlas, y ningun proceso las marcaba como vencidas cuando la cita pasaba sin atencion. Verificado contra Neon real: **las 9 reservas existentes en la base estaban en `pendiente` con la cita ya pasada** (entre el 2026-09-22 y el 2026-09-24), reteniendo 9 unidades de inventario para siempre.
- **Solucion:** `GET /api/v1/reservas/mias` (CU13 + CU14: la misma respuesta cubre el listado, la cancelacion y la consulta de estado de una reserva especifica) y `POST /api/v1/reservas/{id_reserva}/cancelar` (motivo obligatorio). Vencimiento perezoso: una reserva `pendiente`/`confirmada` cuya cita paso hace mas de 2 horas se marca `vencida` y libera su stock al primer listado o intento de cancelacion, sin esperar a un cron. La fila de inventario a liberar se localiza por el movimiento `reserva` que CU12 dejo escrito (nunca se recalcula la temporada: una variante puede tener stock repartido en varias). Se extrajo `modules/reservas/utilidades.py::formatear_codigo_reserva`, que CU12 duplicaba inline.
- **Verificacion:** 25 pruebas nuevas (`test_cu13_consultar_cancelar.py`), suite completa 487/487. End-to-end contra Neon real en transacciones revertidas: (a) `listar_mis_reservas` sobre el cliente real con reservas vencidas liberó las 7 que le pertenecian, devolviendo su inventario a `cantidad_reservada = 0`; (b) ciclo `crear_reserva_presencial` -> `cancelar_reserva` sobre una reserva nueva devolvio el inventario exactamente a su valor original (13 -> 11 -> 13).
- **Pendiente:** Web y Mobile (tarjeta del Perfil y pantalla de reservas) — ver `tasks.md` de `CU13-CU14-consultar-cancelar-reservas`.

#### 70. Verificacion end-to-end contra Stripe real (modo test) y correccion del `urlScheme` en Mobile (CU16)
- **Contexto:** con `STRIPE_SECRET_KEY`/`STRIPE_PUBLISHABLE_KEY` de prueba ya configuradas (backend y Web), se ejecuto el flujo completo contra la API real de Stripe: login (JWT emitido directamente con `core.security.create_access_token`, sin exponer contrasenas), `POST /carrito/items`, `POST /ventas/checkout`, `POST /pagos/intentos` (abrio un `PaymentIntent` real), confirmacion directa contra Stripe con `stripe.PaymentIntent.confirm(...)` (simulando lo que hace Stripe.js/el SDK de Flutter) y `POST /pagos/{id_pago}/confirmar`.
- **Resultado:** dos ordenes reales pagadas (`FS-2026-000012` con tarjeta aprobada `pm_card_visa`, `FS-2026-000013` con un primer intento rechazado por `pm_card_chargeDeclined` y un segundo intento aprobado) mas un pago `rechazado` conservado como historial. Inventario consolidado correctamente (`cantidad_disponible` 15 -> 13, dos unidades vendidas, nunca regreso a disponible). `referencia_pasarela` guardo el `PaymentIntent` real de Stripe (`pi_3...`), `marca_tarjeta`/`ultimos_digitos` se leyeron del `payment_method` que Stripe devolvio, nunca de un dato enviado por el cliente.
- **Defecto encontrado durante la prueba:** `stripe.PaymentIntent.confirm()` devolvio `This PaymentIntent is configured to accept payment methods enabled in your Dashboard... you must provide a return_url` porque `crear_intento` no restringe `automatic_payment_methods` ni fija `allow_redirects: 'never'` (a proposito, para permitir 3DS/SCA). Web ya lo resolvia (`confirmParams: { return_url: window.location.href }` en `checkout-pago.component.ts`), pero Mobile no: `flutter_stripe` no recibe un `return_url` por llamada como Stripe.js, sino que lo resuelve desde un ajuste global (`Stripe.urlScheme`) que nunca se configuro. Se anadio `Stripe.urlScheme = 'fashionstore'` en `main.dart`, junto a una nota de que aun falta registrar el mismo esquema en `AndroidManifest.xml`/`Info.plist` para que un redirect real (p. ej. una tarjeta que exige 3D Secure) vuelva a la app — pendiente de verificar en un dispositivo/emulador real, que no está disponible en este entorno.
- **Tarjetas de prueba de Stripe usadas:** ver la tabla que se entrega junto a esta entrada en la conversacion; son las oficiales de Stripe (`pm_card_visa`, `pm_card_chargeDeclined`, etc.), no literales inventados.

#### 69. Mobile Migrado al SDK de Stripe: la App ya no Envia la Tarjeta a Nuestro Servidor (CU16, Mobile)
- **Causa:** igual que en Web (entrada 68), `checkout_payment_screen.dart` recolectaba numero/titular/expiracion/CVV en `TextEditingController`s propios y los enviaba en `PagoProcesarInDto.tarjeta`, un contrato que el backend ya no acepta tras el rediseno (entrada 67). Mobile nunca habia tenido un archivo de configuracion para una clave de Stripe.
- **Solucion:** `flutter_stripe` instalado. `STRIPE_PUBLISHABLE_KEY` anadida a `api_config.dart` con el mismo patron `String.fromEnvironment` que `API_URL`; `main()` inicializa el SDK solo si la clave no esta vacia. Se creo `StripeGateway` (interfaz + `StripeGatewayReal`/`StripeGatewaySimulado`) para desacoplar `PagoBloc` del SDK concreto: con clave real, `confirmarYPagar()` encadena `iniciarPago()` -> `StripeGateway.confirmarPago()` (que envuelve `Stripe.instance.confirmPayment`, usando lo que el `CardField` ya capturo en el SDK nativo) -> `confirmarPago()`; sin clave, usa el mismo mecanismo `escenario_prueba` del simulador del backend. Bizum/QR y PayPal, decorativos desde siempre, se abren igual que antes, siempre aprobados. La "Atelier Privé Black Card" pasa a ser decorativa (ya no refleja en vivo lo tecleado, porque el widget ya no tiene acceso a esos datos).
- **Nativo:** iOS ya declaraba `IPHONEOS_DEPLOYMENT_TARGET = 13.0` y Android hereda `flutter.minSdkVersion` de Flutter; ambos ya satisfacian el minimo que exige `flutter_stripe` sin tocar `build.gradle`/`Podfile`.
- **Verificacion:** `dart analyze` sin incidencias, `flutter test` 181/181. **No verificado en un emulador/dispositivo real** (no hay uno disponible en este entorno): ni el `CardField` nativo ni una confirmacion real con `4242 4242 4242 4242` se ejercitaron end-to-end. Ese camino se cubre en cambio con un `StripeGateway` falso inyectado directamente en `PagoBloc`, que ejercita la misma secuencia de llamadas que correria con el SDK real.

#### 68. Web Migrada a Stripe Elements: el Navegador ya no Envia la Tarjeta a Nuestro Servidor (CU16, Web)
- **Causa:** tras el rediseño del backend (entrada 67), `checkout-pago.component.ts` seguia recolectando numero/titular/expiracion/CVV en un `FormGroup` propio y enviandolos al backend, que ya no los aceptaba. Ademas el proyecto no tenia ningun archivo `environment.ts`: no habia donde guardar una clave publicable de Stripe, que por diseno no es secreta y por eso no puede vivir en el backend.
- **Solucion:** instalado `@stripe/stripe-js`; creados `src/environments/environment.ts`/`environment.prod.ts` (con `fileReplacements` en `angular.json`) para `STRIPE_PUBLISHABLE_KEY`. `PagoService.procesarPago` se dividio en `iniciarPago`/`confirmarPago`/`registrarPagoEfectivo`, espejo de los tres endpoints nuevos del backend. `CheckoutPagoComponent` monta el **Payment Element** de Stripe en modo *deferred* (visible antes de que el cliente pulse pagar) y encadena `elements.submit()` -> `iniciarPago()` -> `stripe.confirmPayment({redirect:'if_required'})` -> `confirmarPago()`; se anadio manejo del retorno por redireccion (algunos metodos con SCA la exigen incluso con `if_required`) guardando el `id_pago` en `sessionStorage` antes de salir. Sin `STRIPE_PUBLISHABLE_KEY` real configurada (el estado actual del proyecto), el componente no carga Stripe.js: muestra un panel de "modo simulador" con 3 botones (`aprobado`/`rechazado`/`fondos_insuficientes`) que reflejan el mismo `escenario_prueba` del simulador del backend.
- **Defecto de arquitectura de pruebas descubierto:** el sistema de pruebas de este proyecto (`@angular/build:unit-test`) **rechaza `vi.mock` sobre imports relativos** ("Please use Angular TestBed for mocking dependencies"), a diferencia de Vitest puro. Se creo `StripeConfigService`/`StripeLoaderService` para envolver `environment`/`loadStripe` en servicios inyectables y poder sustituirlos via `TestBed`, el unico mecanismo de mock que este runner admite.
- **Verificacion:** Web 484/484, `tsc --noEmit` limpio, `ng build` de produccion exitoso, `ng serve` sirviendo `/pago/:idVenta` sin errores. **No verificado con Stripe.js real ni con la tarjeta `4242 4242 4242 4242`**: no hay ninguna clave real de Stripe configurada en este proyecto (backend ni frontend). El flujo con Stripe real se cubre en cambio con `StripeLoaderService` mockeado via `TestBed`, ejercitando la misma secuencia de llamadas que correria con Stripe.js real.

#### 67. El Backend Recibia el PAN y el CVV en Crudo, Algo que Stripe Bloquea por Defecto (CU16, Backend)
- **Causa:** `TarjetaIn`/`PagoProcesarIn` recogian numero, titular, expiracion y CVV en el cuerpo de `POST /pagos/procesar` y los reenviaba a Stripe como `payment_method_data.card.*` en `StripeService._construir_metodo_pago`. Stripe bloquea esta via ("raw card data APIs") por defecto en cualquier cuenta nueva desde 2019: con una clave de prueba real la llamada habria fallado del lado de Stripe, no del nuestro, y de haber funcionado habria supuesto una superficie PCI innecesaria en este servidor.
- **Solucion:** El cobro digital se dividio en dos pasos, ninguno de los cuales recibe datos de tarjeta. `POST /pagos/intentos` (`PagoServicio.iniciar_pago`) abre un `PaymentIntent` en Stripe (`automatic_payment_methods` habilitado, sin `confirm` y sin `allow_redirects: 'never'`, para permitir 3D Secure/SCA) y devuelve su `client_secret`; el cliente confirma el cobro directamente contra Stripe con Stripe.js/el SDK de Flutter, sin pasar por este backend. `POST /pagos/{id_pago}/confirmar` (`PagoServicio.confirmar_pago`) recupera el `PaymentIntent` por su id y decide `aprobado`/`rechazado` segun lo que **Stripe** responda, nunca segun lo que el cliente reporte — la misma regla que ya rige los importes de una orden, aplicada ahora al desenlace de un cobro. El pago en efectivo, que nunca toco una tarjeta, se separo en su propio endpoint (`POST /pagos/efectivo`) sin cambio de comportamiento.
- **Contrapartida documentada, no resuelta en esta ronda:** no existe todavia un webhook de Stripe (`payment_intent.succeeded`). Si el cliente cierra la pestaña o la app entre la confirmacion en Stripe y la llamada a `confirmar_pago`, el pago queda aprobado en Stripe pero sin reflejarse en `pagos`/`ventas` hasta que alguien vuelva a invocar ese endpoint.
- **Verificacion:** `tests/modules/compras_pagos/test_cu16_pagos.py` reescrito (49 pruebas: apertura del intento, verificacion aprobada/rechazada/con fallo tecnico, idempotencia en ambos pasos, reenvio idempotente natural de una confirmacion ya cerrada, guardas de pertenencia y de metodo). Suite completa del backend: 442/442. Verificado ademas end-to-end contra Neon real, en una transaccion revertida: `iniciar_pago` seguido de `confirmar_pago` sobre una venta y un inventario reales, comprobando que la fila de `pagos` nunca persiste el `client_secret` y que el inventario se consolida igual que antes. Web y Mobile quedan pendientes de adaptarse al nuevo contrato (`tasks.md` de CU16, Ronda 2, Bloques 2 y 3).

#### 66. La Promocion Automatica se Llamaba "Membresia Prive" sin Existir Ninguna Membresia (CU11 + CU16)
- **Causa:** La migracion `0010` sembro `fashionstore.promociones.id_promocion = 2` con el nombre "Membresia Prive", copiado literalmente del mockup. La promocion es de catalogo (`alcance='producto'`, sin `codigo_cupon`) y se aplica automaticamente, via `CarritoRepositorio.obtener_promociones_por_producto`, a cualquiera que compre una de las 3 prendas activas de mayor precio vinculadas en `promocion_producto` — el sistema no tiene ningun concepto de membresia ni de segmentacion de clientes, asi que el nombre prometia un beneficio de cliente VIP que el mecanismo real nunca ofrecio.
- **Solucion:** Renombrada a "Seleccion Atelier" en la fila real de Neon, en el seed de la migracion `0010` y en cada literal de codigo/pruebas que la citaba: `motivo_descuento` en los tests de `CU11`, la etiqueta `Beneficio {{ nombre }}` de `checkout-pago.component.html` (Web) y el texto equivalente de `pantalla_producto_detalle.dart` (Mobile). La mecanica de aplicacion automatica no cambio, solo el nombre; queda documentada en `spec.md` de `CU16` para diferenciarla de "Bono Atelier de Bienvenida" (`MAISON-2025`), que si exige un cupon explicito.
- **Verificacion:** Backend 432/432, Web 478/478, Mobile 173/173 (`dart analyze` sin incidencias).

#### 65. La Bolsa se Vaciaba al Tramitar, Aunque el Pago Nunca se Confirmara (CU15 + CU16)
- **Causa:** `CheckoutServicio.tramitar_pedido` vaciaba `carrito_detalle` en el mismo acto de emitir la orden. Cuando se especifico CU15 el checkout era el final del recorrido, pero con CU16 en produccion dejo de serlo: la orden nace en estado `pendiente` y el cobro ocurre despues. El resultado era que un pago rechazado (402), abandonado, o a la espera del cajero (pago en efectivo, hasta 24 h) dejaba al cliente **sin su seleccion y sin haber comprado nada**. Los dos clientes agravaban el efecto fingiendo ademas una bolsa vacia en local (`CarritoService.tramitarPedido` en Web y `CarritoBloc.tramitarPedido` en Mobile).
- **Solucion:** La bolsa sobrevive al checkout. Las prendas se retiran unicamente cuando el cobro queda confirmado, en los tres caminos: pasarela para tarjeta, pasarela para Bizum/QR, y `confirmar-efectivo` para el pago en caja —nunca al registrarlo—. El retiro es selectivo por `(id_variante, id_sucursal)` y no un vaciado total, porque el cliente puede haber anadido prendas mientras el pago estaba pendiente; y al confirmar un pago en efectivo se resuelve por `venta.id_cliente` y no por el usuario autenticado, que ahi es el cajero. Se retiro tambien el vaciado local de Web y Mobile.
- **Contrapartida necesaria:** al conservar la bolsa, pulsar «TRAMITAR PEDIDO» dos veces habria emitido dos ventas reteniendo el inventario dos veces por las mismas prendas. Se anadio la guarda `409 ORDEN_PENDIENTE_EXISTENTE`, que ademas libera la orden anterior si su ventana ya vencio, para que una orden abandonada no bloquee al cliente indefinidamente.
- **Verificacion:** end-to-end contra Neon, en transacciones revertidas, de los tres caminos: (a) tarjeta —bolsa intacta tras tramitar, segundo checkout rechazado con `ORDEN_PENDIENTE_EXISTENTE`, bolsa vacia tras confirmar el cobro—; y (b) efectivo —bolsa intacta con el pago `pendiente`, vaciada solo cuando el administrador confirma en caja—. Backend 432/432, Web 478/478, Mobile 173/173.

#### 64. Checkout Caido con `GeneratedAlways` al Perderse el Mapeo de Solo Lectura de `subtotal_linea` (CU15)
- **Causa:** `venta_detalle.subtotal_linea` es `GENERATED ALWAYS AS ((cantidad)::numeric * precio_unitario)` en PostgreSQL y rechaza cualquier valor explicito en el INSERT, **incluido NULL**. El commit `6325f6f` ("alineacion de modelos tras merge de main", 2026-09-22) consolido `VentaDetalleORM` desde `catalogo/modelos.py` hacia `comercial/cu28_ventas_reservas/modelos.py` y, al hacerlo, perdio el mapeo de solo lectura original (`server_default=FetchedValue()`, `server_onupdate=FetchedValue()`), quedando como columna normal `mapped_column(Numeric(12, 2), nullable=True)`. Desde entonces la unidad de trabajo de SQLAlchemy incluia la columna con `None` en cada INSERT y **`POST /api/v1/ventas/checkout` respondia 500** (`psycopg.errors.GeneratedAlways`), dejando el carrito inutilizable en produccion. El servicio nunca asigno el atributo: el defecto estaba solo en el mapeo.
- **Solucion:** La columna se declara con `Computed("cantidad * precio_unitario", persisted=True)`, que es la forma en que SQLAlchemy representa una columna generada: queda fuera del INSERT/UPDATE y se recupera por `RETURNING`. Verificado end-to-end contra Neon ejecutando el checkout real sobre un carrito de 4 lineas dentro de una transaccion revertida: comprobante emitido, `subtotal_linea` calculada por PostgreSQL (756.50 / 620.00 / 340.00 / 420.00) e invariante `total = subtotal - descuento` respetada.
- **Por que 424 pruebas en verde no lo detectaron:** toda la suite mockea la sesion de base de datos, de modo que ningun INSERT real llega a compilarse; y las dos guardias de `tests/test_esquema_bd.py` solo comparaban nombres y familias de tipo, no la *escribibilidad* de la columna. Se anadieron dos regresiones: `test_esquema_bd.py::test_las_columnas_generadas_se_mapean_en_solo_lectura`, que contrasta `information_schema.is_generated` contra el ORM para toda columna generada del esquema, y `test_cu15_checkout.py::test_subtotal_linea_se_mapea_como_columna_generada`, que corre sin base de datos. Ambas se verificaron revirtiendo el mapeo: fallan con el codigo defectuoso.

#### 63. RenderFlex Overflowed en la Pantalla de Pago Seguro Movil (CU16, `Ec-mobile`)
- **Causa:** En `CheckoutPaymentScreen` (`lib/src/modulos/compras_pagos/cu16_realizar_pago/presentacion/pantallas/checkout_payment_screen.dart`), la fila con el titulo "Selecciona Forma de Pago" y el badge "CIFRADO SEGURO" usaba `mainAxisAlignment: spaceBetween` sin `Expanded`, igual que la fila de la pantalla de confirmacion (`_filaResumen`) cuando el valor era largo (por ejemplo, "VISA terminada en 1111"). Es la sexta aparicion de este defecto en el proyecto (CHANGELOG, entradas 9, 20, 26 y 31).
- **Solucion:** Envueltos los textos variables en `Expanded` con `overflow: TextOverflow.ellipsis`, sin reducir tamanos de fuente, siguiendo la practica ya fijada en `CLAUDE.md` para este defecto recurrente.
---

## [2.7.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU30 - Consultar bitacora (Seguridad, Gobernanza y Auditoria Corporativa):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/seguridad/CU30-consultar-bitacora.md`](.specs/modules/seguridad/CU30-consultar-bitacora.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU30/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU30/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion justificada de la aplicacion movil (`Ec-mobile`). La consulta de bitacora, auditoria forense y analisis de mutaciones de datos del sistema corresponden con exclusividad a la direccion de tecnologia y superadministracion en la consola web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni endpoints.
- **Validacion Completa:**
  - Backend: 312/312 tests en verde en `pytest` (14/14 especificos de CU30 en `test_cu30_bitacora.py`); migracion DDL Alembic `0011_cu30_bitacora.py` en PostgreSQL Neon sobre `fashionstore.bitacora` con indices en `creado_en DESC`, `severidad`, `tabla_modulo`, `id_usuario`; modelo relacional `Bitacora` (`app/modules/seguridad/cu30_bitacora/modelos.py`); esquemas Pydantic v2 defensivos con filtros multicriterio, metricas agregadas y serializacion de payloads JSON; servicio de dominio `ServicioBitacoraAuditoria` con control estricto RBAC (solo `administrador` y alias `admin`, bloqueo 403 para resto de roles); endpoints REST bajo `/api/v1/admin/bitacora`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores, 0 advertencias), 358/358 tests en verde en Vitest / Angular CLI (9/9 en `bitacora-admin.component.spec.ts`, 4/4 en `bitacora-admin.service.spec.ts`, 25/25 en `admin-dashboard.component.spec.ts`); duodecima tarjeta corporativa en `AdminDashboardComponent` ("Consultar bitacora") bajo "Gobernanza y Accesos" con badge "Seguridad y Auditoria", boton `id="btn-consultar-bitacora"`, directiva dual de navegacion (`routerLink="/admin/bitacora"` y `(click)="navegar('/admin/bitacora', $event)"`), conteo de 12 modulos activos para administrador, y prueba unitaria de despacho de evento click real sobre el DOM; componente Standalone `BitacoraAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/bitacora`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs (Total Eventos, Mutaciones Criticas, Alertas / Errores, Operadores Activos); barra reactiva de filtros multicriterio con retardo debounce de 300 ms en busqueda textual; tabla cronologica con timestamps monoespaciados UTC, badges cromaticos de severidad (`INFO`, `WARN`, `ERROR`, `CRITICAL`); modal accesible para inspeccion de JSON diff (`payload_anterior` vs `payload_nuevo`); y Luxury Banners contextuales.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 59. Prevencion de Navegacion Estatica mediante Directiva Dual y roleGuard Permisivo en Rutas Administrativas
- **Causa:** En Angular, las navegaciones pueden resolver silenciosamente en `false` sin disparar captura de error si un guard bloquea o hay desfase de roles (`roleGuard(['administrador'])` rechazando alias como `admin`).
- **Solucion:** Declaracion explicita en `app.routes.ts` de roles compatibles `roleGuard(['administrador', 'admin'])`, adopcion de directiva dual en botones de navegacion del panel administrativo (`routerLink` mas click handler defensivo con reintento) y verificacion unitaria mediante despacho de evento `MouseEvent` nativo sobre el DOM.

#### 60. Alineacion de Instancia FastAPI en Entorno de Pruebas Unitarias y Aislamiento de Red
- **Causa:** La existencia de importaciones disjuntas entre `main` y `app.main` en `conftest.py` provocaba bifurcacion de instancias de la aplicacion FastAPI, saltandose overrides de dependencias como `get_db` y generando llamadas de red concurrentes a PostgreSQL Neon remoto durante la ejecucion de la suite completa.
- **Solucion:** Normalizacion de importaciones en `conftest.py` y `test_health.py` hacia `from main import app`, e implementacion de overrides defensivos en todas las pruebas de seguridad para evitar conexiones no mockeadas a bases de datos remotas.

---

## [2.6.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU29 - Visualizar indicadores empresariales (Inteligencia de Negocios y Analitica Directiva):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU29-visualizar-indicadores-empresariales.md`](.specs/modules/comercial/CU29-visualizar-indicadores-empresariales.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU29/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU29/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion justificada de la aplicacion movil (`Ec-mobile`). La inteligencia de negocios, supervision cuantitativa de rentabilidad agregada, ranking macro de prendas y comparativa de productividad multi-sucursal corresponden exclusivamente a competencias directivas y de back-office corporativo radicadas en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni peticiones HTTP.
- **Validacion Completa:**
  - Backend: 298/298 tests en verde en `pytest` (17/17 especificos de CU29 en `test_cu29_indicadores.py`); modelos declarativos consolidados en esquema `fashionstore` (`VentaORM`, `VentaDetalleORM`, `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `SucursalORM`, `CiudadORM`); esquemas Pydantic v2 defensivos con saneamiento y validador de rangos cronologicos (`fecha_desde <= fecha_hasta`); motor analitico `ServicioIndicadoresEmpresariales` con segregacion forzosa de alcance por sucursal para encargados, calculo relacional de variaciones porcentuales relativas contra periodos precedentes sin division por cero, agrupaciones cronologicas con `date_trunc`, ranking Top N de productos y distribucion multicanal; endpoints REST bajo `/api/v1/admin/indicadores` custodiados por RBAC con roles autorizados (`administrador` y `encargado_sucursal`).
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 338/338 tests en verde en Vitest / Angular CLI (11/11 en `indicadores-admin.component.spec.ts`, 10/10 en `indicadores-admin.service.spec.ts`, 21/21 en `admin-dashboard.component.spec.ts`); undecima tarjeta corporativa en `AdminDashboardComponent` ("Visualizar indicadores empresariales") bajo "Analitica y Reportes" con badge "Business Intelligence", boton `id="btn-visualizar-indicadores-empresariales"`, doble directiva de navegacion (`routerLink="/admin/indicadores"` y `(click)="navegar('/admin/indicadores', $event)"`) y prueba unitaria de despacho de evento click sobre el DOM; componente Standalone `IndicadoresAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/indicadores`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs ejecutivos con flechas de tendencia y color semaforico discreto; conmutador reactivo de periodos ('7d', '30d', 'mes_actual', 'anio_actual', 'personalizado'); selector de sucursales habilitado para administrador y bloqueado con badge para encargado; graficas vectoriales nativas en SVG puro (curva interpolada de ingresos con area sombreada y puntos interactivos con tooltips, barras horizontales relativas de Top 5 productos, barras de progreso segmentadas por canales y categorias) y comparativa de sucursales restringida a administradores; skeletons de carga y Luxury Banners para contingencias no destructivas.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 56. Segregacion Territorial Defensiva en Consultas Analiticas para Encargados
- **Causa:** Un usuario con rol encargado de sucursal podia enviar parametros `id_sucursal` arbitrarios en los query params de los endpoints analiticos o intentar consultar la comparativa corporativa entre sucursales.
- **Solucion:** El servicio `ServicioIndicadoresEmpresariales` sobreescribe forzosamente `id_sucursal` con el identificador asignado al usuario encargado en base de datos, ignorando cualquier parametro externo, y arroja `AccesoComparativaDenegadoError` (HTTP 403) ante cualquier intento de acceso al endpoint de comparativa entre tiendas.

#### 57. Prevencion Determinista de Division por Cero en Variaciones Relativas y Ticket Promedio
- **Causa:** En periodos nuevos o sucursales sin operaciones transaccionales registradas en el periodo actual o precedente, las operaciones de cociente para calcular el ticket promedio o la variacion porcentual generaban errores aritmeticos de division por cero.
- **Solucion:** Implementacion de clausulas condicionales y funciones `NULLIF`/`COALESCE` en agregaciones SQL y evaluacion defensiva en Python devolviendo `0.00` de forma determinista ante denominadores nulos o iguales a cero.

#### 58. Visualizaciones Graficas Vectoriales en SVG Nativo con Cambio de Deteccion OnPush
- **Causa:** El uso de bibliotecas de graficos externas de gran volumen (como Chart.js o D3) incrementa el tamano del bundle y genera dependencias complejas con el arbol de componentes reactivo de Angular.
- **Solucion:** Desarrollo de directivas y trazados SVG nativos puros integrados con Angular Signals (`puntosGraficoCalculados`, `lineaCurvaSvg`, `areaSombreadaSvg`, `lineasGuiaY`), logrando un renderizado fluido, responsive y con zero dependencias externas pesadas.

---

## [2.5.0] - 2026-09-22

### Promocion a Baseline Permanente
- **CU28 - Consultar ventas y reservas (Auditoria Comercial y Consolidacion de Ventas y Reservas):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU28-consultar-ventas-reservas.md`](.specs/modules/comercial/CU28-consultar-ventas-reservas.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU28/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU28/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La consulta analitica de comprobantes de ventas, auditoria de reservas multi-sucursal y computo financiero de ticket promedio corresponden exclusivamente a atribuciones de trastienda y back-office corporativo que residen en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin modelos, pantallas ni servicios mutables.
- **Validacion Completa:**
  - Backend: 280/280 tests en verde en `pytest` (16/16 especificos de CU28 en `test_cu28_ventas_reservas.py`); modelos declarativos ORM en `fashionstore` (`VentaORM`, `VentaDetalleORM`, `PagoORM`, `ReservaORM`, `ReservaDetalleORM`); esquemas Pydantic v2 defensivos con saneamiento y validador de consistencia de fechas (`fecha_desde <= fecha_hasta`); servicio transaccional `ServicioConsultarVentasReservas` con segregacion obligatoria por sucursal segun rol (`administrador` vs `encargado_sucursal`), calculo de metricas cuantitativas de red (`monto_total_facturado`, `total_ventas_concluidas`, `reservas_activas`, `ticket_promedio`) y consulta expandida de detalle; endpoints REST unificados bajo `/api/v1/admin/ventas-reservas` protegidos por RBAC con roles autorizados.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 310/310 tests en verde en Vitest / Angular CLI (32/32 en `ventas-reservas-admin.component.spec.ts`, 10/10 en `ventas-reservas-admin.service.spec.ts`, 19/19 en `admin-dashboard.component.spec.ts`); decima tarjeta corporativa en `AdminDashboardComponent` ("Consultar ventas y reservas") dentro de "Gestion Comercial" con badge "Auditoria y Ventas", boton `id="btn-consultar-ventas-reservas"`, doble directiva de navegacion (`routerLink="/admin/ventas-reservas"` y `(click)="navegar('/admin/ventas-reservas', $event)"`) y visibilidad RBAC; componente Standalone `VentasReservasAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/ventas-reservas`; layout editorial `max-w-[1440px]`; grid superior de 4 tarjetas KPIs reactivas; barra reactiva de filtros multicriterio con retardo *debounce* de 300 ms en busqueda textual; tabla maestra unificada de comprobantes con badges cromaticos por tipo y estado; modal accesible de detalle transaccional (`role="dialog"`) con desglose de lineas de prenda y traza de pagos; y Luxury Banners contextuales para retroalimentacion amigable.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 53. Segregacion Territorial Transaccional Estricta para Encargados de Sucursal
- **Causa:** Un encargado de sucursal podia enviar identificadores de otras sucursales en los filtros de consulta o intentar acceder directamente a los comprobantes de venta o reserva de sedes ajenas.
- **Solucion:** El servicio de dominio valida el rol del usuario autenticado e ignora cualquier parametro foraneo de sucursal para `encargado_sucursal`, forzando la consulta unicamente a su sede asignada y arrojando `SucursalNoAutorizadaError` (HTTP 403) ante cualquier intento de acceso foraneo a detalles unitarios.

#### 54. Unificacion Polimorfica y Determinista de Transacciones de Ventas y Reservas
- **Causa:** Las ventas y reservas residen en tablas relacionales disjuntas con esquemas y ciclos de vida diferentes, lo que dificultaba una paginacion y ordenamiento unificados por monto o fecha.
- **Solucion:** Implementacion de consulta unificada en `ServicioConsultarVentasReservas` con mapeo normalizado a `TransaccionResumenItemOut`, admitiendo filtrado conjunto o segmentado por tipo de operacion y ordenamiento determinista sobre el consolidado.

#### 55. Calculo Cuantitativo de Ticket Promedio Libre de Division por Cero
- **Causa:** En rangos de fechas o sucursales con cero transacciones de venta concluidas, el calculo del ticket promedio (`monto_total / cantidad_ventas`) provocaba excepciones de division por cero.
- **Solucion:** Implementacion defensiva en `obtener_metricas` que evalua la cantidad de ventas concluidas y asigna `0.0` de forma segura cuando no existen ventas concluidas en el periodo consultado.

---

## [2.4.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU27 - Gestionar promociones (Marketing, Descuentos y Cupones Comerciales):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/comercial/CU27-gestionar-promociones.md`](.specs/modules/comercial/CU27-gestionar-promociones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU27/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU27/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La definicion de campanas comerciales, parametros financieros de descuento, aprovisionamiento de cupones con topes monetarios y supervision analitica del volumen de canjes corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 264/264 tests en verde en `pytest` para toda la suite acumulada (16/16 especificos de CU27); migracion DDL Alembic `0008_cu27_promociones.py` ejecutada en PostgreSQL Neon; tabla `fashionstore.promociones` con restricciones `CheckConstraint("fecha_fin > fecha_inicio", name="chk_promociones_fechas_orden")`, `CheckConstraint("tipo_descuento IN ('porcentaje', 'monto_fijo')", name="chk_promociones_tipo_descuento")`, `CheckConstraint("valor_descuento > 0", name="chk_promociones_valor_positivo")`, `CheckConstraint("(tipo_descuento != 'porcentaje') OR (valor_descuento >= 1.00 AND valor_descuento <= 100.00)", name="chk_promociones_porcentaje_tope")`, e indice unico funcional lower-case (`Index("uq_promociones_codigo_cupon_lower", func.lower(func.trim(codigo_cupon)), unique=True, postgresql_where=codigo_cupon.isnot(None))`); modelo relacional `PromocionORM` en esquema `fashionstore` con sinonimo `activa = synonym("estado_activo")` y claves foraneas hacia categorias y productos; esquemas Pydantic v2 defensivos con saneamiento y conversion a mayusculas de codigos de cupon; servicio transaccional `ServicioGestionPromociones` con paginacion multicriterio (`q`, `tipo_descuento`, `estado_activo`, `alcance`, `ordenar_por`), calculo de metricas cuantitativas de red (`promociones_activas`, `cupones_vigentes`, `descuento_promedio`, `usos_totales`) y conmutacion atomica de estado logico; y endpoints REST bajo `/api/v1/admin/promociones` custodiados por RBAC con roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 268/268 tests en verde en Vitest / Angular CLI (13/13 en `promociones-admin.component.spec.ts`, 9/9 en `promociones-admin.service.spec.ts`, 15/15 en `admin-dashboard.component.spec.ts`); novena tarjeta corporativa en `AdminDashboardComponent` ("Gestionar promociones") dentro de la categoria "Gestion Comercial" con badge "Marketing y Descuentos", boton `id="btn-gestionar-promociones"`, doble directiva de navegacion (`routerLink="/admin/promociones"` y `(click)="navegar('/admin/promociones', $event)"`) y visibilidad RBAC para administrador y encargado; componente Standalone `PromocionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/promociones`; layout editorial `max-w-[1440px]`; cabecera con H1 "Gestionar promociones" y boton superior `"Volver al Panel Principal"`; grid superior de 4 tarjetas de KPIs cuantitativos; barra reactiva de filtros con retardo *debounce* de 300 ms en busqueda textual; tabla maestra con chips monoespaciados e indicadores de vigencia cromados (`Vigente`, `Proxima`, `Expirada`); modales reactivos con validacion sincronica inline de fechas y rango porcentual; y Luxury Banners para captura no destructiva de colisiones HTTP 409 y validaciones 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 50. Normalizacion Idempotente de Estado y Compatibilidad Retroactiva en Tabla `fashionstore.promociones`
- **Causa:** La base DDL preexistente incluia la columna `activa` de tipo boolean, mientras que los estandares de arquitectura SDD requerian `estado_activo`, junto con constraints CHECK de orden de fechas, rangos porcentuales e indice unico funcional lower-case sobre `codigo_cupon`.
- **Solucion:** Implementacion de la migracion Alembic `0008_cu27_promociones.py` que renombra de forma segura e idempotente `activa` a `estado_activo`, define constraints CHECK y crea el indice `uq_promociones_codigo_cupon_lower` con clausula condicional `WHERE codigo_cupon IS NOT NULL`. Se establecio ademas `activa = synonym("estado_activo")` en `PromocionORM` para garantizar compatibilidad retroactiva total.

#### 51. Control Dinamico de Topes Financieros y Validacion Condicional de Alcance
- **Causa:** Promociones con descuento porcentual requieren opcionalmente un tope maximo monetario para evitar perdidas en compras de alto valor, mientras que promociones por monto fijo no deben parametrizar tope. Asimismo, alcances por categoria o producto exigian validar la presencia y consistencia de las entidades referenciadas.
- **Solucion:** Implementacion de validadores defensivos `@model_validator(mode="after")` en backend y `validadorPromocion` sincronico a nivel de `FormGroup` en frontend, bloqueando anomalías en tiempo real y habilitando o inhabilitando campos condicionalmente segun el tipo de descuento y alcance seleccionado.

#### 52. Preservacion de Notificaciones de Exito y Aislamiento de Errores en Operaciones de Mutacion
- **Causa:** En el servicio reactivo de frontend, refrescar la lista de promociones inmediatamente tras una creacion, edicion o conmutacion de estado podia provocar que el reseteo de variables de estado eliminara de forma prematura el mensaje de exito para el usuario.
- **Solucion:** Desacoplamiento de la limpieza de errores y mensajes de exito en `PromocionesAdminService`, preservando el banner contextual de confirmacion tras el ciclo de recarga de datos en segundo plano.

---

## [2.3.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU24 - Gestionar temporadas y colecciones (Calendario Editorial y Curaduria de Moda):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/catalogo_productos/CU24-gestionar-temporadas-colecciones.md`](.specs/modules/catalogo_productos/CU24-gestionar-temporadas-colecciones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU24/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La planificacion del calendario estacional de moda, la vigencia de campanas y la estructuracion taxonomica de colecciones capsula corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 248/248 tests en verde en `pytest` para toda la suite acumulada (14/14 especificos de CU24); migracion DDL Alembic `0007_cu24_temporadas_colecciones.py` ejecutada en PostgreSQL Neon; modelos relacionales `TemporadaORM` y `ColeccionORM` en esquema `fashionstore` con restricciones `CheckConstraint("fecha_fin > fecha_inicio", name="chk_temporadas_fechas_orden")` y `CheckConstraint("anio >= 2020", name="chk_temporadas_anio_valido")`; indice unico funcional insensible a mayusculas (`Index("uq_temporadas_nombre_anio_lower", func.lower(func.trim(nombre)), anio, unique=True)`); compatibilidad retroactiva mediante `synonym("estado_activo")` preservando atributos heredados; esquemas Pydantic v2 con validacion de rango cronologico y saneamiento de cadenas; servicios de dominio `ServicioGestionTemporadas` y `ServicioGestionColecciones` con soporte para listados paginados multicriterio, baja logica no destructiva (`estado_activo = False`) e integridad referencial forzada; y 10 endpoints REST bajo `/api/v1/admin/temporadas` y `/api/v1/admin/colecciones` custodiados por RBAC con roles `administrador` y `encargado_sucursal` protegiendo contra accesos no autenticados (401) o no autorizados (403).
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 244/244 tests en verde en Vitest / Angular CLI (11/11 en `temporadas-colecciones-admin.component.spec.ts`, 10/10 en `temporadas-colecciones-admin.service.spec.ts`, 13/13 en `admin-dashboard.component.spec.ts`); octava tarjeta corporativa en `AdminDashboardComponent` ("Gestionar temporadas y colecciones") dentro de la categoria "Taxonomia Comercial" con badge "Calendario Editorial", boton `id="btn-gestionar-temporadas-colecciones"` y visibilidad condicionada por RBAC para administrador y encargado; componente Standalone `TemporadasColeccionesAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/temporadas-colecciones`; sistema de pestanas reactivas (Temporadas / Colecciones); barra reactiva de filtros con retardo *debounce* de 300 ms en busqueda textual; modales reactivos con validacion sincronica de fechas (`fecha_fin > fecha_inicio`), badges cromaticos y Luxury Banners para captura no destructiva de errores HTTP 409 y 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 47. Validacion de Consistencia Cronologica y Coexistencia con Modelos Previos (`chk_temporadas_fechas_orden` y `TemporadaORM.activa`)
- **Causa:** La definicion formal requeria validar que `fecha_fin > fecha_inicio` e indices unicos lower-case sobre nombre y anio. Asimismo, pruebas preexistentes del catalogo invocaban `TemporadaORM` con el atributo booleano `activa` o inicializacion directa `TemporadaORM(nombre=..., activa=True)`, mientras que el nuevo esquema estandarizaba el estado bajo `estado_activo`.
- **Solucion:** Implementacion de `CheckConstraint("fecha_fin > fecha_inicio", name="chk_temporadas_fechas_orden")` e indice compuesto `uq_temporadas_nombre_anio_lower` en PostgreSQL Neon mediante revision Alembic `0007_cu24_temporadas_colecciones.py`. Adicion de `synonym("estado_activo")` y constructor compatible en `TemporadaORM` para asegurar compatibilidad total con tests heredados sin fisuras en base de datos.

#### 48. Validacion Sincronica y Defensiva de Fechas en Formularios Reactivos Web
- **Causa:** La seleccion manual de fechas en la creacion o edicion de temporadas en el cliente web permitia inadvertidamente seleccionar fechas de culminacion anteriores a la fecha de inicio, requiriendo el rechazo en backend con HTTP 422.
- **Solucion:** Implementacion de un validador personalizado a nivel de `FormGroup` en Angular (`validarRangoFechas`) que intercepta la discrepancia cronologica en tiempo real, inhabilita el boton de envio y proyecta alertas contextuales inmediatas en el modal corporativo.

#### 49. Aislamiento de Estado y Debounce Desacoplado en Interfaz Dual de Pestanas
- **Causa:** En una interfaz de administracion compartida con pestanas para temporadas y colecciones, busquedas rapidas con peticiones asincronas en vuelo podian cruzar estados o resetear indebidamente la paginacion de la entidad contigua.
- **Solucion:** Desacoplamiento estricto del estado reactivo mediante Signals independientes por entidad, operadores RxJS `debounceTime(300)` y reinicio focalizado de paginacion al alternar de pestana.

---

## [2.2.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU26 - Consultar inventario global (Vision Panoramica Multi-Sede y Balances de Red):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md`](.specs/modules/gestion_operativa/CU26-consultar-inventario-global.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU26/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU26/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La auditoria corporativa analitica, la consolidacion de existencias multi-sucursal y los balances de red comercial corresponden a atribuciones de trastienda y back-office corporativo que residen exclusivamente en la plataforma web de escritorio (`Ec-frontend`). La aplicacion movil B2C queda formalmente excluida sin pantallas, modelos ni servicios mutables.
- **Validacion Completa:**
  - Backend: 234/234 tests en verde en `pytest` para toda la suite acumulada (10/10 especificos de CU26); servicio analitico `ServicioInventarioGlobal` con agregacion relacional uniendo `VarianteProductoORM`, `ProductoORM`, `CategoriaORM`, `TallaORM`, `ColorORM`, con `LEFT OUTER JOIN` hacia `InventarioSucursalORM` y `SucursalORM` activa; computo de disponibilidad consolidada mediante `func.sum` y `func.coalesce` defensivo; exclusion estricta de sucursales inactivas; metricas cuantitativas de red (`total_unidades_red`, `variantes_monitoreadas`, `alertas_stock_bajo`, `sedes_activas`); semaforizacion automatizada de estado de existencias (`optimo`, `alerta_baja`, `agotado`); filtros multicriterio combinables (`q`, `id_categoria`, `id_sucursal`, `estado_stock`, `ordenar_por`) con paginacion determinista; y endpoint REST analitico `GET /api/v1/admin/inventario/global` custodiado por roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 222/222 tests en verde en Vitest / Angular CLI (23/23 en `inventario-global-admin.component.spec.ts`, 6/6 en `inventario-global-admin.service.spec.ts`, 12/12 en `admin-dashboard.component.spec.ts`); septima tarjeta boutique en `AdminDashboardComponent` ("Consultar inventario global") dentro de "Gestion Operativa" con badge "Consolidado Multi-Sede", boton `id="btn-consultar-inventario-global"` y visibilidad segmentada por RBAC para administrador y encargado; componente Standalone `InventarioGlobalAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals en `/admin/inventario-global`; layout editorial centrado `max-w-[1440px]`; boton superior `"Volver al Panel Principal"`; grid superior de 4 tarjetas de metricas de red; barra de filtros reactiva con retardo *debounce* de 300 ms en busqueda textual; tabla maestra consolidada con chips interactivos de stock por sede, valores en red y badges cromaticos; modal accesible de detalle logistico y coordinacion inter-tiendas con direccion fisica y enlace directo `tel:`; y Luxury Banners para gestion no destructiva de errores de red.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 44. Agregacion Defensiva contra Nulos y Exclusion de Sucursales Inactivas
- **Causa:** Variantes registradas sin existencias previas en `inventario_sucursal` o asociadas a sucursales clausuradas o inactivas podian generar valores `NULL` o distorsionar el stock real disponible de la red.
- **Solucion:** Implementacion de `func.coalesce(func.sum(case(...)), 0)` junto con filtro relacional estricto `SucursalORM.activa.is_(True)`, garantizando que el stock de red refleje unicamente sedes operativas y devuelva 0 de forma segura para prendas sin stock previo.

#### 45. Enlace Logistico Inter-Tiendas con Informacion de Contacto Directo
- **Causa:** Ante alertas de rotura de stock en una tienda, el personal operativo carecia de un mecanismo rapido para ubicar y contactar a boutiques con inventario excedente.
- **Solucion:** Incorporacion matricial de los datos de contacto (`direccion`, `ciudad` y `telefono`) en el desglose de existencias por sucursal y creacion de enlaces directos `tel:` en el modal de detalle logistico para derivaciones telefonicas inmediatas.

#### 46. Optimizacion de Subconsultas Paginadas y Conteo Determinista
- **Causa:** En consultas analiticas con agrupamiento y clausulas `HAVING`, el calculo ingenuo de `total_registros` producia conteos incorrectos o duplicacion de lineas.
- **Solucion:** Encapsulamiento del conteo en una subconsulta estructurada con alias explicito (`conteo_subquery`), asegurando una paginacion y calculo de `total_paginas` matematicamente exacto.

---

## [2.1.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU25 - Gestionar Proveedores (Cadena de Abastecimiento y Talleres Textiles):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md`](.specs/modules/gestion_operativa/CU25-gestionar-proveedores.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU25/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU25/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La gestion societaria, contratos de confeccion mayorista, captura de datos tributarios (NIT/RUT) y evaluacion de talleres textiles corresponden a labores exclusivas de trastienda y back-office corporativo web (`Ec-frontend`). La app movil B2C queda formalmente excluida sin pantallas ni modelos mutables.
- **Validacion Completa:**
  - Backend: 224/224 tests en verde en `pytest` para toda la suite acumulada (16/16 especificos de CU25); modelo ORM en esquema `fashionstore` (`ProveedorORM`), revision DDL Alembic `0006_cu25_proveedores_extension.py` en PostgreSQL Neon; restricciones de unicidad estricta sobre `nit_rut` y `razon_social` (insensible a mayusculas); esquemas Pydantic v2 con validadores de sanitizacion obligatoria y correo valido; excepciones semanticas de dominio (`ProveedorNoEncontradoError`, `ProveedorDuplicadoError`, `ProveedorInvalidoError`); servicio de dominio con soporte multicriterio paginado, prevencion de colisiones 409 y baja logica (`estado_activo = False`) preservando integridad historica referencial; y endpoints REST bajo `/api/v1/admin/proveedores` protegidos por roles `administrador` y `encargado_sucursal`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 192/192 tests en verde en Vitest / Angular CLI (13/13 en `proveedores-admin.component.spec.ts`, 9/9 en `proveedores-admin.service.spec.ts`, 11/11 en `admin-dashboard.component.spec.ts`); sexta tarjeta boutique en `AdminDashboardComponent` ("Proveedores y Fabricantes") dentro de "Gestion de Abastecimiento" con badge "Cadena de Suministro" y control RBAC dinamico (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `ProveedoresAdminComponent` con `ChangeDetectionStrategy.OnPush` y Angular Signals; boton superior editorial `"<- Volver al Panel Principal"` con `routerLink="/admin"`; barra reactiva de filtros con busqueda textual con debounce de 300 ms, selector de estado y selector de rubro textil; tabla maestra editorial con NIT/RUT, contacto comercial, ciudad e insignias cromadas de estado (verde esmeralda / slate); modales reactivos con `NonNullableFormBuilder` (Alta, Edicion y Confirmacion de Baja Logica con advertencia de cese de recepcion sin perdida de historico); y Luxury Banners para captura contextual no destructiva de errores HTTP 409 y 422 preservando los datos del formulario.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 41. Prevencion de Duplicidad Tributaria y Societaria Multicapa (`uq_proveedores_nit_rut` y `uq_proveedores_razon_social`)
- **Causa:** La duplicidad inadvertida de registros de un mismo taller textil bajo leves variaciones de razon social o reutilizacion de NIT generaba inconsistencias fiscales y distorsionaba la auditoria de abastecimiento.
- **Solucion:** Validacion previa en capa de servicio con consultas normalizadas y creacion de indices unicos `uq_proveedores_nit_rut` y `uq_proveedores_razon_social` (con funcion `LOWER()` en PostgreSQL Neon), emitiendo de forma determinista la excepcion HTTP 409 Conflict.

#### 42. Trazabilidad e Inmutabilidad Historica mediante Baja Logica (`estado_activo = False`)
- **Causa:** La eliminacion fisica de un proveedor con prendas asociadas en catalogo o recepciones historicas de kardex rompia la integridad referencial de base de datos o dejaba registros huerfanos.
- **Solucion:** Politica estricta de baja logica mediante el flag `estado_activo = False` que cesa inmediatamente la habilitacion para nuevos pedidos pero conserva la totalidad del historico comercial y documental.

#### 43. Captura No Destructiva de Conflictos y Debounce Asincrono en Formularios Reactivos
- **Causa:** La emision de errores de validacion o colision tributaria solia reiniciar los formularios o generar parpadeos en busquedas continuas.
- **Solucion:** Implementacion de retardo *debounce* de 300 ms en el input de busqueda conectado a Signals y contencion no destructiva en Luxury Banners mediante captura en `errorBanner`, preservando integro el estado de los controles en `formCrear` y `formEditar`.

---

## [2.0.0] - 2026-09-21

### Promocion a Baseline Permanente
- **CU24 - Gestionar Inventario, Stock y Existencias por Sucursal (Logistica y Existencias Fisicas):** Promovido oficialmente a especificacion permanente del sistema en [`.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md`](.specs/modules/gestion_operativa/CU24-gestionar-inventario-stock.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU24/` (`spec.md`, `design.md`, `tasks.md`) y limpiado el directorio de cambios temporales `.specs/changes/CU24/`.
- **Exclusion Formal Justificada de Ec-mobile:** Ratificada documentalmente la exclusion de la aplicacion movil (`Ec-mobile`). La recepcion de lotes de confeccion, registro de mermas fisicas, transferencias masivas entre boutiques y auditoria contable de kardex son funciones operativas de trastienda y back-office corporativo que residen exclusivamente en el panel web de administracion. La aplicacion movil participa en calidad de consultor pasivo de existencias (`Read-Only`) mediante el endpoint publico `/api/v1/inventario/disponibilidad/{id_variante}`.
- **Validacion Completa:**
  - Backend: 208/208 tests en verde en `pytest` para toda la suite acumulada (17/17 especificos de CU24); modelos ORM en esquema `fashionstore` (`InventarioSucursalORM` y `MovimientoInventarioORM`), migracion Alembic `0005_cu24_inventario_kardex.py` ejecutada en PostgreSQL Neon; restriccion de unicidad compuesta `uq_inventario_sucursal_variante` y `CheckConstraint` de no negatividad (`cantidad_disponible >= 0`); libro de movimientos Kardex inmutable; transaccionalidad ACID con bloqueo exclusivo `with_for_update()` en transferencias inter-sucursales; computo determinista de semaforos de stock (`optimo`, `alerta_baja`, `agotado`); segregacion territorial forzada para rol `encargado_sucursal` bloqueando con HTTP 403 accesos a sedes ajenas; endpoints administrativos bajo `/api/v1/admin/inventario` y vitrina publica `/api/v1/inventario/disponibilidad/{id_variante}`.
  - Frontend Web: Compilacion limpia en Angular CLI (`ng build`, 0 errores), 168/168 tests en verde en Vitest / Angular CLI (12/12 en `inventario-admin.component.spec.ts`, 9/9 en `inventario-admin.service.spec.ts`, 10/10 en `admin-dashboard.component.spec.ts`); quinta tarjeta boutique en `AdminDashboardComponent` ("Inventario y Existencias") con segmentacion dinamica RBAC (visible para `administrador` y `encargado_sucursal`, oculta para cajeros y clientes); componente Standalone `InventarioAdminComponent` con `ChangeDetectionStrategy.OnPush` y Signals; barra reactiva de filtros con selector de sucursal fijado y deshabilitado para encargados de boutique; tabla maestra editorial con swatches `#HEX`, miniatura con fallback SVG, desglose de cantidades y badges cromados de umbral; modales reactivos con `NonNullableFormBuilder` (Alta inicial, Ajuste fisico con motivo obligatorio min. 5 caracteres y control de stock, Transferencia inter-sedes excluyendo sede origen y con tope en disponible); panel de Kardex cronologico descendente con variaciones (+/-); y Luxury Banners para captura contextual de errores HTTP 409 y 422.

---

### Errores Corregidos y Soluciones Tecnicas Aplicadas

#### 38. Bloqueo Pesimista ACID y Doble Asiento en Transferencias Inter-Sucursales (`with_for_update`)
- **Causa:** En transferencias concurrentes entre boutiques, la lectura no sincronizada del saldo en origen podia ocasionar condiciones de carrera y saldos negativos de inventario.
- **Solucion:** Bloqueo pesimista mediante `with_for_update()` sobre la fila del inventario de origen dentro de una unica transaccion atomica, deduciendo el saldo disponible, acreditando en la sede destino (o creando el registro si no existia) e insertando los dos asientos simetricos de Kardex (`transferencia_salida` y `transferencia_entrada`).

#### 39. Segregacion Territorial Obligatoria y Proteccion RBAC Multinivel
- **Causa:** Personal con rol `encargado_sucursal` podria intentar consultar o mutar existencias de otras tiendas comerciales si el frontend no aplicara restricciones o el backend confiara en los parametros query del cliente.
- **Solucion:** Sobreescritura forzada del parametro de sucursal en el backend validando contra `usuario_sesion.id_sucursal` (HTTP 403 si discrepa), complementada en el frontend mediante bloqueo y deshabilitacion reactiva del selector de sucursal para encargados.

#### 40. Control Reactivo de Umbrales y Validacion de Motivo Obligatorio en Ajustes
- **Causa:** Ajustes manuales por merma o rotura sin justificacion auditable o con cantidades superiores al stock disponible comprometian la fidelidad contable y violaban constraints de base de datos.
- **Solucion:** Validacion Pydantic v2 en `InventarioAjusteIn` exigiendo minimo 5 caracteres no vacios en el motivo, verificacion en servicio de que decrementos no superen `cantidad_disponible` (HTTP 409 `STOCK_INSUFICIENTE`), y reflejo reactivo en interfaz mediante validadores reactivos y Luxury Banners sin perdida de datos.

---
## [1.9.0] - 2026-09-21

### Auditoría Transversal y Corrección de Defectos de Contrato

Diagnóstico completo de `Ec-backend`, `Ec-frontend` y `Ec-mobile` contra la documentación de
`.agents/` y `.specs/`. El hallazgo estructural es que **las tres suites reportaban verde mientras
CU12 (Reservar Prendas) era imposible de completar desde la aplicación móvil**: el backend mockea
la sesión de base de datos en sus tests y el móvil construía sus DTO con constructores sin
ejercitar nunca `fromJson`, de modo que ningún desajuste de nombres de campo era observable.

- **Blindaje de las pruebas contra el contrato real:** los mocks de reserva del web y del móvil se
  reescribieron a partir de payloads literales de `POST /api/v1/reservas`, y se añadió un grupo de
  pruebas de contrato en `test/pantalla_producto_detalle_test.dart` que valida `toJson`/`fromJson`
  frente a los esquemas Pydantic. Se añadieron `registro.component.spec.ts` y una prueba de
  supervivencia del listener de sesión en `widget_test.dart`, los dos archivos con más cambio de
  comportamiento y sin cobertura previa.
- **Reconciliación documental:** actualizada la directriz Hub-and-Spoke (declaraba CU05 pendiente y
  CU36 «en migración de layout en Web»), cerrados los gates de aprobación de
  `change-detalle-producto-reservas.md` y `change-landing-page-publica.md` (afirmaban que no se
  había generado código con 18 y 13 tareas ya marcadas), resuelto el conflicto de rutas de
  `/inicio` y `/colecciones` a favor del enrutamiento vigente, y marcado el Bloque 3 (Mobile) de
  CU07/CU08/CU09/CU12 según el estado real del repositorio.
- **Deriva de esquema entre el ORM y PostgreSQL (2026-09-22):** una segunda pasada, motivada por
  errores HTTP 500 reproducidos en la aplicación en ejecución, reveló que tres modelos mapeaban
  columnas inexistentes en la base de datos real. La trampa de fondo es que
  `alembic/versions/0001_base_ddl.py` **no refleja el esquema desplegado en Neon**: ORM y migración
  coincidían entre sí y discrepaban de la realidad. Se alinearon los modelos con la base de datos
  —sin tocar el esquema— y se añadió `Ec-backend/tests/test_esquema_bd.py` como guardia permanente.
- **Verificación:** `pytest` 123/123 (incluye la guardia de esquema contra Neon) · `ng test`
  108/108 y `ng build` 0 errores · `dart analyze` 0 issues y `flutter test` 104/104. Además,
  verificación end-to-end contra la base real: `/api/v1/catalogo`, `/api/v1/colecciones/activas`,
  `/api/v1/catalogo/filtros-disponibles`, `/api/v1/catalogo/recomendaciones/personalizadas`,
  `/api/v1/sucursales/activas` y `/api/v1/productos` devuelven HTTP 200 con datos de Neon.

### Deuda Técnica Registrada (Resuelta documentalmente — Opción A)
- **`alembic/versions/0001_base_ddl.py` por sí sola refleja el DDL inicial, no el estado final.**
  Declara `activa`, `activo` y `nit` donde PostgreSQL tiene `estado_activo` y `nit_rut`, y no
  incluye las columnas y tablas introducidas después (`bitacora`, `codigos_recuperacion`,
  `actualizado_en`, `anio`, `codigo_cupon`, `alcance`, `limite_usos`, `direccion`, `ciudad`,
  `rubro`, entre otras). Sin embargo, **la cadena completa `0001 → 0011` sí reproduce el esquema
  real de Neon** (las 31 tablas, 236 columnas, 10 enums, 46 índices, 3 vistas y el trigger): las
  migraciones `0002`–`0011` aplican todos los `ALTER` y creaciones que compensan el desfase de
  `0001`. Se actualizó el DDL de `SI2-Parcial1.md` para reflejar el esquema vigente en producción
  (Opción A). Para consultar el esquema de una tabla debe usarse `information_schema` o
  `Ec-backend/specs/diseno_fisico_neon.sql`, nunca `0001` de forma aislada.

### Registro de Errores Corregidos y Soluciones Aplicadas
34. **HTTP 500 en Catálogo, Búsqueda y Colecciones por Deriva entre el ORM y el Esquema Real de PostgreSQL**:
    - *Causa:* `TemporadaORM`, `PromocionORM` y `ProveedorORM` mapeaban columnas llamadas `activa`, `activo` y `nit`, mientras que en la base de datos de Neon esas columnas se llaman `estado_activo` y `nit_rut`. SQLAlchemy emitía `SELECT temporadas.activa …` y PostgreSQL respondía `UndefinedColumn`, tumbando `GET /api/v1/catalogo` (vía `PromocionORM`), `GET /api/v1/catalogo/filtros-disponibles` y `GET /api/v1/colecciones/activas` (ambos vía `TemporadaORM`).
    - *Agravante que impidió diagnosticarlo:* la migración `alembic/versions/0001_base_ddl.py` **no describe la base de datos realmente desplegada** —declara los nombres antiguos—, de modo que ORM y migración se confirmaban mutuamente mientras producción fallaba. Sumado a que todos los tests mockean la sesión, no existía ningún punto del proyecto donde el desajuste fuese observable.
    - *Solución:* Se pasó el nombre real como primer argumento de `mapped_column("estado_activo", …)` / `mapped_column("nit_rut", …)` en `Ec-backend/app/modules/catalogo/modelos.py`, conservando los atributos de dominio (`activa`, `activo`, `nit`) para no alterar ninguna consulta. No se modificó el esquema de la base de datos. Se añadió `tests/test_esquema_bd.py`, que contrasta `Base.metadata` contra `information_schema` y falla ante cualquier columna mapeada inexistente.
    - *Nota de corrección:* una revisión anterior de este mismo changelog atribuyó el fallo a «un renombrado a `nit_rut`/`estado_activo` sin migración de respaldo» y lo revirtió. El diagnóstico estaba invertido: esos eran los nombres correctos y el revert reintrodujo el error. La fuente de verdad es la base de datos desplegada, no la migración.
35. **HTTP 500 al Reservar la Misma Variante Dos Veces en una Cita**:
    - *Causa:* El servicio de CU12 recorría `payload.items` sin consolidar, descontando el inventario tantas veces como líneas repetidas e insertando detalles duplicados que violaban el `UNIQUE (id_reserva, id_variante)` de `reserva_detalle`. El `IntegrityError` resultante no pertenece al árbol `DomainError`, por lo que escapaba del manejador de errores como un 500. La restricción tampoco estaba declarada en el ORM.
    - *Solución:* Consolidación de líneas por `id_variante` antes de tocar inventario, validación del tope de 5 unidades sobre el total agrupado (`CANTIDAD_MAXIMA_EXCEDIDA`, HTTP 400) y declaración del `UniqueConstraint` en `ReservaDetalleORM`.
36. **HTTP 500 Latente por Consulta de Inventario sobre una Clave No Única**:
    - *Causa:* El repositorio de reservas resolvía el inventario con `scalar_one_or_none()` filtrando por `(id_variante, id_sucursal)`, pero la clave única real de `inventario_sucursal` incluye `id_temporada`. Bastaba con que una variante tuviera existencias de una segunda temporada en la misma boutique para que toda reserva de esa prenda lanzara `MultipleResultsFound`. Permanecía latente solo porque el seed siembra una única temporada.
    - *Solución:* Selección determinista de la fila que cubre la cantidad solicitada (temporada más reciente primero), con fallback a la de mayor stock para que el mensaje de existencias insuficientes informe la disponibilidad real.
37. **HTTP 422 Sistemático al Reservar Cita desde la Aplicación Móvil**:
    - *Causa:* `ReservaCrearInDto.toJson` serializaba `fecha_reserva`, `notas_cliente` y `lineas`, mientras que `ReservaCrearIn` exige `fecha_hora_atencion`, `observacion` e `items` (este último obligatorio). Tres de las cuatro claves eran incorrectas, por lo que CU12 nunca llegó a funcionar en móvil. El DTO de respuesta presentaba el mismo problema, de modo que todos los campos caían en sus valores por defecto y el diálogo de confirmación mostraba datos inventados.
    - *Solución:* Alineación campo a campo de la petición y la respuesta con los esquemas Pydantic, envío explícito de `canal_origen: 'movil'` y derivación de `totalPrendas` a partir de las líneas devueltas.
38. **Listener de Sesión Móvil Autodesactivado tras el Login**:
    - *Causa:* La suscripción a `SesionManager` vivía en el widget montado como ruta `home`. Al navegar al hub mediante `pushReplacement` desde el contexto de ese mismo estado, la ruta se reemplazaba a sí misma, el estado se desmontaba y `dispose()` cancelaba la suscripción. El auto-redirect por HTTP 401 solo escuchaba mientras el usuario permanecía en el login —justo cuando un 401 no puede producirse— y, al cerrar sesión, los callbacks del nuevo login apuntaban a un estado destruido, de modo que volver a autenticarse dejaba la aplicación en el formulario sin mensaje alguno.
    - *Solución:* Reestructuración de `main.dart` para que la gestión de sesión resida por encima del `Navigator`, actuando mediante `navigatorKey` y `scaffoldMessengerKey` globales, y liberación del flag anti-duplicados de `SesionManager` en cada retorno al login.
39. **Ficha de Producto Móvil sin Fotografía Principal ni Galería Multiángulo**:
    - *Causa:* `ProductoDetalleDto.fromJson` leía `imagen_url` y `galeria_angulos`, mientras que `ProductoDetalleOut` emite `imagen_principal` y `galeria`. Ambos resolvían a `null` y lista vacía.
    - *Solución:* Corrección puntual de ambas claves, preservando `imagen_url` en los DTO de listado, donde sí es el nombre correcto.
40. **HTTP 401 al Reservar desde las Pestañas Catálogo y Buscar**:
    - *Causa:* `PantallaCatalogo` y `PantallaBuscarProductos` no declaraban campo `token` ni lo propagaban a `PantallaProductoDetalle`, por lo que la petición de reserva salía sin cabecera `Authorization` aun con el usuario autenticado.
    - *Solución:* Añadido el campo `token` a ambas pantallas y a las de colecciones, propagado desde `PantallaPrincipalHub`.
41. **Confirmación de Reserva Web con Campos en Blanco**:
    - *Causa:* La interfaz `ReservaConfirmacion` declaraba `codigo_confirmacion`, `total_prendas` y `mensaje_cortesia`, campos que `ReservaCreadaOut` no envía. El modal imprimía «CÓDIGO: » sin contenido y la notificación mostraba `Cita confirmada (undefined)`. El spec mockeaba la interfaz del propio frontend, dando por válido un contrato que el servidor nunca produce.
    - *Solución:* Modelo alineado con `ReservaCreadaOut`, total derivado de las líneas mediante `computed()`, y spec reescrito sobre un payload real del backend.
42. **Sesión Anónima tras Completar el Registro en Web**:
    - *Causa:* `RegistroComponent` persistía la sesión con claves propias (`fs_token_acceso`, `fs_usuario`) que ningún servicio consulta, ya que `LoginService`, `PerfilService` e `InicioService` leen `fashionstore_token` y `fashionstore_user`. El usuario recién registrado quedaba sin autenticar, el interceptor no adjuntaba el token y `/perfil` rebotaba a `/login`.
    - *Solución:* El registro delega la persistencia en el nuevo método `LoginService.establecerSesion()`, dejando las claves de almacenamiento bajo un único propietario.
43. **Todo Fallo Interno del Backend Llegaba al Navegador como «Failed to fetch»**:
    - *Causa:* Ante una excepción no controlada, la respuesta 500 la generaba el `ServerErrorMiddleware` de Starlette, que envuelve a todos los middlewares de usuario, incluido el `CORSMiddleware`. La respuesta salía sin `Access-Control-Allow-Origin` y el navegador la descartaba, de modo que la web y la app Flutter mostraban un error de red genérico en lugar del error real. Añadir un `@app.exception_handler(Exception)` no lo resuelve: Starlette monta ese manejador precisamente en el `ServerErrorMiddleware`.
    - *Solución:* Middleware `capturar_errores_no_controlados` registrado **antes** del `CORSMiddleware` (`add_middleware` antepone, así que el primero declarado queda por dentro), que devuelve un 500 JSON estructurado y atraviesa CORS. El traceback se registra en el log del servidor y nunca se envía al cliente. Se conserva el manejador de excepción externo como último recurso para fallos del propio CORSMiddleware.
44. **Landing Page Pública Inalcanzable en la URL Raíz**:
    - *Causa:* La ruta `{ path: '', component: MainLayoutComponent, children: [...] }` introducida con CU05 quedó declarada por delante de `{ path: '', loadComponent: landing, pathMatch: 'full' }`. Angular resuelve las rutas en orden: la URL raíz entraba en el layout y, al no existir ningún hijo con `path: ''`, la landing dejaba de mostrarse. El proyecto seguía compilando sin errores.
    - *Solución:* La landing se declara primero en `app.routes.ts`; su `pathMatch: 'full'` garantiza que solo capture la URL vacía exacta. Se añadió además la ruta comodín `{ path: '**' }` que faltaba —sin ella, cualquier URL desconocida producía un `NG04002` y una pantalla en blanco, agravado porque `vercel.json` reescribe todo a `index.html`— y el guard `src/app/app.routes.spec.ts`, que navega a `/` y verifica el orden de declaración.
45. **Cadena de Alembic Irresoluble por Revisiones `0009` y `0010` Duplicadas**:
    - *Causa:* Había dos archivos con `revision = "0009"` (`0009_checkout_ddl.py` y `0009_cu28_ventas_reservas.py`) y dos con `revision = "0010"` (`0010_seed_promociones.py` y `0010_cu29_indicadores.py`), con el mismo `down_revision` cada par. Alembic avisaba «Revision 0010 is present more than once» y `alembic history` / `alembic upgrade head` fallaban con «overlaps with other requested revisions», aunque `render.yaml` invoca `alembic upgrade head` en `preDeployCommand`. Los marcadores de CU28 y CU29 son revisiones vacías (`pass`) que se numeraron sin comprobar que el ID ya estaba tomado. Un diagnóstico anterior achacaba el fallo a que faltaban las revisiones `0004`–`0008`, pero esos archivos ya existían.
    - *Solución:* Se encadenaron con IDs únicos, sin borrar ni reordenar el DDL real: `0008 → 0009 (checkout) → 0009a (CU28) → 0010 (seed promociones) → 0010a (CU29) → 0011 (bitácora)`. `0011.down_revision` pasó a `0010a`. La base de Neon está sellada en `0011`, que sigue siendo la única cabeza, así que **no requirió tocar la base de datos** y `alembic upgrade head` es un no-op sobre ella.
    - *Verificación:* `alembic heads` → una sola cabeza (`0011`); `alembic history` lineal de `<base>` a `0011`; `alembic current` contra Neon → `0011 (head)`; `alembic upgrade 0001:head --sql` genera los 12 pasos en orden sin avisos; `pytest` 487/487.
46. **CU10 · Modo Realista Decart: Timeout sin Causa Visible, Sesiones Huérfanas y Uso Siempre en 0**:
    - *Síntoma:* Al activar el Motor 2, el spinner esperaba 40 s y caía al Motor 1 con «Tiempo de espera excedido»; la prenda nunca se veía sobre la cámara y el panel de Decart marcaba uso 0.
    - *Diagnóstico:* Una sonda de señalización (WebSocket a `/v1/stream`, sin medios) demostró que token, origen `http://localhost:4200`, capacidad (sin cola) e imagen (`set_image_ack success`) funcionan. El fallo ocurre después, en la conexión WebRTC (LiveKit); como Decart solo factura segundos de generación, el uso queda en 0. Ese fallo de red quedaba oculto por cuatro defectos del cliente y del backend.
    - *Causa 1 — ceguera:* los `rt.on('error' | 'sessionEnded' | 'diagnostic')` se registraban tras `await connect()`, y el SDK retiene esos eventos hasta que `connect()` resuelve; tampoco se pasaban `onQueuePosition`, `onCapacityWait` ni `logger`.
    - *Causa 2 — temporizador más corto que el SDK y sin cancelación:* el SDK reintenta 5 veces manteniendo el estado `connecting`; los 40 s de la UI vencían antes, y `desconectarDecart()` no podía cerrar nada porque `rtClient` seguía en `null` hasta que `connect()` resolvía. La conexión seguía en segundo plano y, si llegaba a abrirse, emitía sin vista.
    - *Causa 3 — token fijo:* `createDecartClient({ apiKey: token })` reutilizaba un token de 60 s en cada re-marcación, que fallaba con `TOKEN_EXPIRED`.
    - *Causa 5 — timeout del backend:* `DecartService` esperaba 4 s y la primera emisión de token midió 4,55 s (frío; 0,9–1,4 s en caliente): falso `DECART_TIMEOUT` (503).
    - *Solución:* `apiKeyProvider` que entrega el token ya emitido y pide uno nuevo en cada re-marcación; callbacks `onQueuePosition`/`onCapacityWait`/`onConnectionChange` y `createConsoleLogger('info')` dentro de `connect()`; `retries: 1` y `capacityRetryBudgetMs: 20000` para que el SDK se rinda dentro del margen de la UI (45 s); contador `intentoConexionIA` que invalida la conexión en vuelo al cerrar, conmutar o vencer el tiempo, y desconecta al instante la sesión que llegue tarde. El límite de 60 s se separó de la vida del token (`LIMITE_SESION_IA_SEGUNDOS`), como exige la spec. Backend: `TIMEOUT_TOKEN_SEGUNDOS = 10`.
    - *Pendiente fuera de este arreglo:* la causa de red de WebRTC en el equipo afectado; en producción, `render.yaml` no declara `DECART_API_KEY` y su `CORS_ORIGINS` (`fashionstore-web.vercel.app`) no coincide con el dominio real, y Decart rechaza el origen con «Origin not allowed» (cierre 1008); la imagen de referencia es una foto de modelo vistiendo la prenda, no una prenda aislada.
    - *Ampliación tras contrastar con la skill y la documentación de Decart:* (a) la referencia era `imagen_principal`, una foto de modelo vistiendo la prenda, lo que Decart señala como error común; ahora se envía solo `modelo_ar_url` (la prenda sola), aplanada sobre fondo blanco, con aviso si mide menos de 512 px y sin recurrir nunca a la foto de catálogo; (b) el prompt genérico «Virtually try on…» se sustituye por el patrón «Substitute the current … with …» según el tipo de prenda (`servicios/prompt-vton.ts`); (c) la pista de cámara se ajusta a `model.width`/`model.height`/`model.fps`; (d) `checkConnectivity()` antes de conectar: con red `critical` cae al Motor 1 al instante en vez de esperar 45 s. Se añadió la prenda de ejemplo `public/ar/camiseta_original.png` (800×1000, fondo liso). `ng test` 595/595 y `ng build` correcto.
    - *Causa raíz (identificada con el registro del navegador):* checkConnectivity `good`, LiveKit `connected` en `mx-central-1` y la pista de la cámara publicada, pero ni `generating` ni stream remoto. En Chromium el SDK activa la marca de tiempo por fotograma: crea `new Worker(new URL("./frame-metadata-worker.js", import.meta.url))` y LiveKit hace pasar cada fotograma codificado por ese worker (insertable streams). Con `ng serve`, Vite pre-empaqueta `@decartai/sdk` en `.angular/cache/.../vite/deps/` y el worker no existe junto al chunk (**404**, verificado contra el servidor de desarrollo); con `ng build` el chunk lo referencia pero no se emite. Con el worker caído no sale ningún fotograma: Decart no genera, no factura y la UI agota su espera.
    - *Solución de la causa raíz (`angular.json`):* asset `frame-metadata-worker.js` copiado desde `node_modules/@decartai/sdk/dist/realtime/browser` a la raíz de la salida, y `serve.options.prebundle.exclude: ["@decartai/sdk"]` para que en desarrollo el SDK se empaquete como chunk de la aplicación (raíz), igual que en producción. Verificado: `ng build` emite el worker junto a `chunk-*.js`; un `ng serve` temporal responde `200 text/javascript` en `/frame-metadata-worker.js`.
    - *Prenda de prueba:* producto 22 «Camiseta básica amarilla de algodón» (Camisas · Edición Milano: Punto & Lino, 45,00), color nuevo «Amarillo» (#FACE03, id 58), variantes S/M/L/XL (137–140) y 10 unidades por talla en la sucursal 1, temporada 1, con su movimiento `ingreso_proveedor` en el kárdex (responsable: administrador 8). Alta hecha con los servicios de CU23, CU22 y CU24, no con SQL directo. Imagen `public/ar/camiseta_basica_amarilla.png` (659×824, prenda sola sobre fondo liso) generada con Decart `lucy-image-2` a partir de una foto de producto; se usa como `imagen_url` y `modelo_ar_url`. Limitación: el móvil pinta `imagen_url` con `Image.network` y no resuelve rutas relativas.
    - *Ajuste del Motor 1:* el Motor 1 superpone `modelo_ar_url` sobre la cámara, así que necesita un PNG con transparencia; con la foto de fondo gris opaco se veía un rectángulo que tapaba el vídeo y el aviso de cámara. Se separó `modelo_ar_url = /ar/camiseta_basica_amarilla_ar.png` (recorte con canal alfa, 563×630; el Motor 2 lo aplana sobre blanco) de `imagen_url` (foto con fondo, para el catálogo). Además, `iniciarCamaraLocal` descartaba el error de `getUserMedia`: ahora lo registra (`[VESTIDOR] No se pudo abrir la cámara: <DOMException.name>`), muestra la causa en el panel lateral (permiso bloqueado, cámara en uso, sin cámara) y ofrece «Reintentar cámara». `ng test` 600/600.
    - *Verificación:* `ng test` 579/579 (3 pruebas nuevas en `modal-vestidor-ar.component.spec.ts`) · `tsc --noEmit` limpio · `pytest` de CU10 12/12 (1 nueva). La suite completa del backend arrastra 5–7 fallos intermitentes en los tests de webhook de `test_cu16_pagos.py`, previos a este cambio.
47. **Secuencias de PostgreSQL Atrasadas: Altas de Variantes, Colecciones y Proveedores Fallaban con `UniqueViolation`**:
    - *Causa:* las semillas insertaron filas con ids explícitos sin avanzar sus secuencias. En Neon, `variantes_producto_id_variante_seq` proponía 131 con un máximo de 136; `colecciones_id_coleccion_seq`, 5 con máximo 5; `proveedores_id_proveedor_seq`, 1 con máximo 1. Cualquier alta desde el panel (CU22 matriz de variantes, CU24 colecciones, CU25 proveedores) fallaba con `duplicate key value violates unique constraint` y se veía como un 500. Apareció al crear las variantes de la prenda de prueba de CU10: el producto se creó, la matriz de variantes se revirtió entera.
    - *Solución:* `setval(pg_get_serial_sequence(...), max(id), true)` sobre las tres secuencias, en una transacción: solo avanza el contador, no toca filas. Se revisaron todas las secuencias del esquema `fashionstore`; el resto estaba al día.
    - *Prevención:* toda semilla o carga con ids explícitos debe terminar con el mismo `setval` sobre las tablas que toque.
48. **Móvil: Imágenes con Ruta Relativa No se Mostraban (Camiseta de Prueba en «ATELIER»)**:
    - *Causa:* la base de datos guarda algunos recursos como rutas relativas (`/ar/...` del frontend web y, para las fotos subidas desde el panel, `/static/...` del backend). El navegador las completa con el origen de la página; `Image.network` de Flutter no, así que el móvil pintaba el marcador de respaldo. Las 20 prendas originales no lo sufrían porque usan URLs absolutas de Unsplash.
    - *Solución:* `lib/src/core/url_recurso.dart` (`resolverUrlRecurso`) resuelve en la capa de datos, con prefijos conocidos: `/ar/` → `WEB_URL` y `/static/` → `API_URL`. Se aplica en las 19 lecturas de URLs de imagen de 10 DTO (catálogo, búsqueda, detalle y galería, recomendaciones, asistente, colecciones, bolsa, pago, reservas y perfil); las pantallas no cambian. El vestidor (CU10) usa la misma función.
    - *Decisión de diseño (modo offline futuro):* se resuelven solo prefijos de servidor y todo lo demás se devuelve intacto, porque en Android las rutas de archivos locales también empiezan por `/` (`/data/user/0/...`). Las imágenes descargadas para el modo offline no se confundirán con rutas web.
    - *Verificación:* `dart analyze` limpio · `flutter test` 266/266 (`test/url_recurso_test.dart`, con el payload real de `GET /api/v1/productos/22`).
49. **CU31-CU32 · El Personal de Caja no Tenía Ficha en `empleados`**:
    - *Causa:* CU20 creaba el usuario con rol `cajero` o `encargado_sucursal` pero no su fila en `empleados`, que la venta presencial exige como `id_empleado` (FK de `ventas`). Los usuarios 13 y 14 de Neon no la tenían: toda venta de caja habría fallado.
    - *Solución:* `asegurar_ficha_empleado()` en el servicio de CU20 (alta y cambio de rol; `INSERT … ON CONFLICT DO NOTHING`, código `EMP-<id>`) y el script idempotente `Ec-backend/scripts/regularizar_fichas_empleado.py`, aplicado en Neon (EMP-13, EMP-14).
50. **Web: el Cajero Aterrizaba en `/inicio` y Veía Módulos del Panel que no Podía Usar**:
    - *Causa:* el login solo enviaba a `/admin` a administrador y encargado; y `/admin`, `/admin/atributos` y `/admin/productos` solo tenían `authGuard`, así que un cajero que llegara al panel veía y abría las tarjetas de categorías y productos (el backend las rechaza).
    - *Solución:* el cajero entra directo a `/admin/pos` y `cajeroACajaGuard` lo devuelve allí desde esas tres rutas; la caja le muestra su nombre y «Cerrar sesión» en lugar de «Volver al Panel Principal». Administrador y encargado conservan su panel con la tarjeta «Punto de venta».
51. **`GeminiService(api_key="")` Usaba la Clave Real del `.env`**:
    - *Causa:* `self.api_key = api_key or settings.IA_API_KEY`: la cadena vacía es falsa y caía en la clave configurada. Las pruebas del fallback determinista de CU18 llamaban a Gemini de verdad y fallaban según lo que redactara la IA (en una máquina sin clave pasaban).
    - *Solución:* `api_key if api_key is not None else settings.IA_API_KEY`, el mismo criterio que `StripeService`. Prueba nueva que fija una clave en el entorno y comprueba que `api_key=""` la ignora.
52. **Pruebas del Webhook de Stripe (CU16) Dependían del `.env` Local**:
    - *Causa:* las cinco pruebas del modo sin secreto enviaban el evento sin firma, pero heredaban `STRIPE_WEBHOOK_SECRET` del `.env`; con el secreto presente el servicio exige `Stripe-Signature` y respondían 400. Pasaban o fallaban según la máquina.
    - *Solución:* fixture `sin_secreto_webhook` que fija el modo sin secreto en esas pruebas, y una prueba nueva que firma el evento con HMAC-SHA256 como Stripe (`t=…,v1=…`) para cubrir el modo producción. El código del webhook no cambió.
    - *Verificación (49–52):* `pytest` 567/567 en verde, sin fallos previos arrastrados.
53. **`Settings` Rechazaba Variables Nuevas del `.env` y el Backend Local no Arrancaba**:
    - *Causa:* `pydantic-settings` lee `Ec-backend/.env` y, con su configuración por defecto, lanza `ValidationError` ante variables no declaradas. Al añadir `DATABASE_URL_MIGRACIONES`, `DATABASE_URL_PRUEBAS` y `DATABASE_URL_PRUEBAS_APP` para la fundación multitenant, el backend local dejó de arrancar (producción no se vio afectada: Render no las tenía).
    - *Solución:* se declararon en `Settings`, junto con `TENANT_POR_DEFECTO`. Toda variable nueva del `.env` debe declararse en `core/config.py` en el mismo cambio.
54. **P2-CU13 · El Personal Perdía el Carrito (Regresión Detectada por la Prueba de Humo)**:
    - *Causa:* `asegurar_cliente` crea una ficha de cliente para cualquier usuario que use el carrito o reserve. Tras la migración `0013`, `carritos` y `reservas` apuntan a `cliente_tenant` con una FK compuesta, y la ficha recién creada del encargado 13 no estaba registrada en la empresa: `GET /carrito` respondía 500.
    - *Solución:* `TenantServicio.exigir_cliente_en_tenant` antes de crear carritos o reservas. Un cliente no registrado en la empresa recibe 403 `CLIENTE_NO_REGISTRADO` (decisión D-B) y un empleado que compra en su propia empresa queda registrado, como funcionaba antes.
    - *Verificación:* prueba de humo de 42 GET × 5 perfiles sin 5xx, en la rama de pruebas y en producción; dos pruebas de integración nuevas.
55. **Despliegue de la Fundación Multitenant sin Migración: Producción Caída (Error 500 en Todo Acceso a Datos)**:
    - *Causa:* Render desplegó el commit `4c4931b` pero no ejecutó el `preDeployCommand` (`alembic upgrade head`): la base siguió en `0011`. Al pasar `DATABASE_URL` al rol `fashionstore_app` —que sin la migración `0014` no tiene permisos—, toda consulta respondió `permission denied for schema fashionstore`. La causa más probable es que el plan gratuito de Render no ejecuta comandos previos al despliegue.
    - *Solución:* `alembic upgrade head` aplicado a mano con `DATABASE_URL_MIGRACIONES` (dueño de las tablas). Verificado después: base en `0014`, datos intactos, humo sin 5xx y escrituras de extremo a extremo 21/21.
    - *Prevención:* las migraciones se aplican a mano **antes** del push y se comprueba `alembic current` contra producción; no se cambia `DATABASE_URL` en Render hasta confirmar la migración (documentado en `CLAUDE.md`).
56. **`GET /productos` Devolvía el SQL y el Tipo de Excepción en sus Errores 500**:
    - *Causa:* el router de CU06 capturaba cualquier excepción y respondía `detail=f"{type(exc).__name__}: {exc}"`. Durante el incidente 55, la respuesta pública incluía `ProgrammingError … [SQL: SELECT …]`, que revela la estructura de la base.
    - *Solución:* se eliminó ese `except`; el error sube al middleware `capturar_errores_no_controlados`, que lo registra y responde el 500 genérico (que además atraviesa CORS). Era el único router con ese patrón. Prueba nueva: `test_un_error_interno_no_expone_sql_ni_detalles`.

57. **P2-CU02 · Login de Cliente con Error 500 por un Evento de Bitácora sin Empresa**:
    - *Causa:* sin empresa por defecto, el login de un cliente fuera de un portal deja la sesión sin empresa y su evento de bitácora se guarda con `id_tenant` nulo. El ORM inserta con `RETURNING` y PostgreSQL rechaza un `RETURNING` sobre una fila que la política de lectura no deja ver. El fallo se capturaba como «no bloqueante», pero dejaba la sesión inservible y la petición terminaba en 500.
    - *Solución:* `registrar_evento_seguro` inserta sin `RETURNING` y, en la sesión del caso de uso, dentro de un punto de guardado: un fallo de auditoría ya no puede tumbar la operación.
    - *Detección:* prueba de integración del flujo del cliente contra la rama de pruebas, antes de llegar a producción.
58. **P2-CU02 · Web en Blanco al Arrancar por Dependencia Circular (NG0200)**:
    - *Causa:* `TituloTiendaStrategy` inyectaba `TenantService`, que inyecta el `Router`, que necesita la estrategia de títulos para construirse. Angular no arrancaba. Las pruebas no lo veían porque ninguna usaba `appConfig`.
    - *Solución:* la estrategia obtiene `TenantService` con el `Injector` al actualizar el título. `app.config.spec.ts` arranca con la configuración real y falla ante cualquier ciclo.
    - *Detección:* el usuario, en `ng serve`, antes del despliegue.
59. **Vercel Respondía 404 al Abrir o Recargar Cualquier Ruta que no Fuera la Raíz**:
    - *Causa:* `vercel.json` tenía `"cleanUrls": true` desde el primer despliegue (2026-09-20). Con esa opción, la reescritura `/(.*) → /index.html` no encuentra el destino y Vercel responde `NOT_FOUND`. Navegando dentro de la aplicación no se notaba; abrir `/login` o `/admin` directamente siempre falló.
    - *Solución:* se quitó `cleanUrls`. Era urgente con P2-CU02: el portal `/{codigo}` es el enlace que se comparte y la vuelta de Stripe tras 3D Secure recarga `/{codigo}/pago/...`.
60. **Móvil · El Hub se Abría Dos Veces tras el Login**:
    - *Causa:* `main.dart` pasaba a `PantallaLogin` dos callbacks (`alCompletarLoginConUsuario` y `alCompletarLoginConToken`) y la pantalla invocaba los dos: dos `pushAndRemoveUntil` seguidos.
    - *Solución:* solo se usa `alCompletarLoginConUsuario`, que ahora decide entre la selección de tienda (cliente) y el hub (empleado).
61. **Web · Con Sesión Abierta, el Login Enviaba al Encargado de Sucursal a `/inicio`**:
    - *Causa:* `ngOnInit` del login solo distinguía cajero y administrador.
    - *Solución:* el login usa el mismo destino por rol que el guard del portal (`destinoEmpleado`).
62. **Móvil · RenderFlex Overflowed en el Botón «Iniciar Sesión» (Sexta Aparición)**:
    - *Causa:* la fila texto + flecha del botón no cabía cuando el botón tenía muy poco ancho (14,4 px durante la animación del diseño en Chrome).
    - *Solución:* `Row` con `mainAxisSize.min` y el texto en `Flexible` con `TextOverflow.ellipsis`, sin reducir la fuente.

63. **P2-CU03 · El Administrador de Cualquier Empresa Veía y Podía Modificar a Todos los Clientes y al Super Administrador**:
    - *Causa:* la política RLS de `usuarios` deja leer las cuentas sin empresa (clientes y super administrador) a cualquier sesión, porque el login y el carrito las necesitan. `cu20_usuarios_roles` no añadía ningún filtro propio, así que «Usuarios» listaba a los clientes de todas las tiendas y permitía cambiarles el correo, desactivarlos, eliminarlos o restablecerles la contraseña; también al super administrador, una escalada de privilegios. Presente en producción desde la fundación multitenant (`0014`).
    - *Solución:* todas las consultas de `cu20` se limitan en SQL a roles de empleado con `id_tenant` de la empresa de la sesión, con una segunda comprobación sobre el objeto cargado; cualquier otra cuenta responde 404. El administrador ya no puede crear ni asignar el rol cliente (422 `ROL_NO_PERMITIDO`).
    - *Detección y verificación:* revisión al escribir la spec de P2-CU03. Prueba de integración contra la rama de pruebas con clientes reales (listado, consulta, restablecimiento y desactivación → 404) y prueba unitaria que comprueba el filtro en el SQL generado.
    - *Regla:* la RLS de `usuarios` no basta para listar o modificar cuentas; todo caso de uso que lo haga debe filtrar por rol y empresa (documentado en `CLAUDE.md`).
64. **Eliminar un Empleado sin Movimientos de Inventario Daba Error 500**:
    - *Causa:* `eliminar_usuario` comprobaba dependencias en `fashionstore.pedidos`, una tabla que no existe en el esquema; PostgreSQL respondía `UndefinedTable`. Las pruebas unitarias simulaban la sesión y no lo veían.
    - *Solución:* se quitó esa comprobación (las ventas y reservas ya se protegen con sus claves foráneas y con la ficha de `empleados`).
65. **Web · La Pestaña «Ciudades» de `/admin/sucursales` no se Podía Abrir**:
    - *Causa:* el binding `[class.border-[#ECE4D8]="..."` de la tabla de ciudades estaba sin cerrar; al pintar la pestaña, el navegador lanzaba `InvalidCharacterError`. Ninguna prueba abría esa pestaña.
    - *Solución:* binding corregido al dejar la pestaña de solo lectura, y prueba nueva que la abre y comprueba su contenido.
66. **El Servidor Calculaba «Hoy» en UTC, Cuatro Horas por Delante de Bolivia**:
    - *Causa:* catálogo, detalle, colecciones y carrito usaban `date.today()`; la caja, la medianoche UTC para «ventas del día»; la suscripción, `datetime.now(timezone.utc).date()`; PostgreSQL, su zona por defecto (UTC) en `current_date` y `date_trunc`; los reportes, `datetime.now()` sin zona. Render corre en UTC. Entre las 20:00 y las 24:00 de Bolivia se aplicaban las promociones del día siguiente, la lista del día de la caja se vaciaba, las suscripciones vencían 4 h antes y los indicadores llevaban esas ventas al día siguiente. `configuracion_tenant.zona_horaria` existía, pero ningún código la leía.
    - *Solución:* `core/tiempo.py` (`ahora`, `ahora_local`, `hoy`, `inicio_del_dia` en `America/La_Paz`) en todos esos sitios y `set_config('TimeZone', 'America/La_Paz', true)` en el listener `after_begin`. Pruebas con un reloj fijo a las 22:30 de Bolivia y de integración (`current_setting('TimeZone')` y `current_date` contra la rama de pruebas).
67. **Móvil · RenderFlex Overflowed en las Filas de Precio (Séptima Aparición)**:
    - *Causa:* «Bs 890,00» es más largo que «890 €»: la fila de precios de la ficha de producto (precio, precio tachado y ahorro) y la de las piezas de colecciones (precio y «+ CESTA») desbordaban en pantallas estrechas.
    - *Solución:* `Wrap` en la ficha (un precio no se trunca) y `Flexible` con elipsis en las piezas, sin reducir fuentes.
68. **Web · Precios Inventados en la Landing**:
    - *Causa:* las tarjetas ilustrativas del asistente en la landing mostraban «875 €» y «550 €» escritos a mano, sin relación con el catálogo.
    - *Solución:* se quitaron las dos líneas de precio y se conservó la ilustración (regla «cero datos inventados»).

## [1.8.0] - 2026-09-21

### Promoción a Baseline Permanente
- **CU05 - Consultar Catálogo de Productos (Colección General, Atelier & Sastrería Femenina):** Promovido oficialmente a especificación técnica permanente del sistema en [`.specs/modules/catalogo_productos/CU05-consultar-catalogo.md`](.specs/modules/catalogo_productos/CU05-consultar-catalogo.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU05-consultar-catalogo/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa en los 3 Bloques:**
  - **Backend (`Ec-backend`):** 107/107 tests en verde en `pytest` (7/7 específicos de catálogo general); modelos ORM `ProductoORM`, `CategoriaORM`, `VarianteProductoORM`, `PromocionORM` y `PromocionProductoORM`; endpoint `GET /api/v1/catalogo` con paginación, filtros de categoría y ordenamiento; cálculo agregado de conteo por categoría sin queries N+1; cálculo dinámico de promociones vigentes y asignación de subtítulos y badges de alta costura.
  - **Frontend Web (`Ec-frontend`):** 86/86 tests pasando en Vitest / Angular CLI (8/8 de catálogo), compilación de producción limpia (`npm run build`, 0 errores); vista `CatalogoComponent` implementada como Pantalla Raíz (Hub) bajo `MainLayoutComponent` (navbar superior visible, sin botón `← Volver`, pestaña activa destacada); carrusel horizontal de chips con unidades; grilla editorial de 4 columnas con selector de densidad (4 vs 2 columnas); tarjetas con badges de atelier, tallas, dots de color y wishlist; paginación editorial y bloque de Conserjería Privada de Fitting.
  - **Mobile Multiplataforma (`Ec-mobile`):** 86/86 tests pasando en `flutter test` (9/9 específicos de CU05), 0 incidencias en `flutter analyze`; `PantallaCatalogo` integrada en el Índice 2 (`Catálogo`) de `PantallaPrincipalHub` con `BottomNavigationBar` visible y `AppBar` con `automaticallyImplyLeading: false`; carrusel horizontal de chips con conteo; selector de 1 o 2 columnas; cuadrícula con `childAspectRatio: 0.58` libre de desbordamientos `RenderFlex`; paginación con botón expansor y sello institucional "ATELIER FLAGSHIP MADRID · PARÍS".

### Registro de Errores Corregidos y Soluciones Aplicadas
31. **Desbordamiento de RenderFlex y Huecos Excesivos en Tarjetas Móviles de Catálogo**:
    - *Causa:* En pantallas móviles de resolución estándar, la proporción de aspecto 0.50 dejaba un espacio inferior desmedido, mientras que proporciones mayores a 0.65 comprimían el bloque de tallas provocando overflow vertical en tarjetas con títulos de 2 líneas.
    - *Solución:* Calibración precisa a `childAspectRatio: 0.58` en `PantallaCatalogo`, asegurando un ajuste armónico de imagen 3:4, badges, títulos, precio, tallas y selector cromático con cero desbordamientos.
32. **Regresión en Expectativa de Placeholder en Suite de Pruebas de Navegación Móvil (`pantalla_principal_hub_test.dart`)**:
    - *Causa:* El test de navegación original comprobaba la presencia de `PantallaCatalogoPlaceholder` en el índice 2, fallando tras la sustitución por la implementación real de CU05.
    - *Solución:* Actualización del test para validar la presencia de `PantallaCatalogo`, garantizando que la navegación bidireccional entre las 4 pestañas raíz mantenga el 100% de aprobación.
33. **Alineación con Linter Dart 3 (`unnecessary_underscores` y `dangling_library_doc_comments`)**:
    - *Causa:* El uso de identificadores múltiples no utilizados (`__`, `___`) en callbacks de constructores y comentarios de librería no vinculados activaron advertencias en `flutter analyze`.
    - *Solución:* Sustitución por comodines simples `_` compatibles con Dart 3 y enlace de la directiva `library;` en modelos DTO, logrando 0 issues en el análisis estático.

## [1.7.0] - 2026-09-21

### Promoción a Baseline Permanente
- **CU36 - Consultar Colecciones (Colecciones Activas y Exploración de Prendas por Colección):** Promovido oficialmente a especificación técnica permanente del sistema en [`.specs/modules/catalogo_productos/CU36-consultar-colecciones.md`](.specs/modules/catalogo_productos/CU36-consultar-colecciones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU36-consultar-colecciones/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa en los 3 Bloques:**
  - **Backend (`Ec-backend`):** 100/100 tests en verde en `pytest` (17/17 específicos de colecciones y prendas); modelos ORM `ColeccionORM`, `TemporadaORM`, `ProductoORM`; endpoints `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id}/productos` (con alias `/api/v1/catalogo/colecciones/...`); resolución de temporada comercial activa por rango de fechas (`CURRENT_DATE`) y fallback a `activa = true`; cálculo dinámico de `precio_desde` (`MIN(precio_base)`) y `total_prendas` sin queries N+1.
  - **Frontend Web (`Ec-frontend`):** 78/78 tests pasando en Vitest / Angular CLI, compilación de producción limpia (`npm run build`, 0 errores); vistas `ColeccionesComponent` y `ColeccionDetalleComponent` estructuradas como pantallas secundarias fuera de `MainLayoutComponent` (sin barra de navegación superior institucional, maximizando inmersión editorial, con botón de retorno obligatorio `← Volver` hacia `/inicio` o `/colecciones`); card completa de "Otras colecciones" interactiva como botón de enlace.
  - **Mobile Multiplataforma (`Ec-mobile`):** 77/77 tests pasando en `flutter test`, 0 incidencias en `flutter analyze`; vistas `ColeccionesScreen` y `DetalleColeccionScreen` ejecutadas a pantalla completa sin `BottomNavigationBar` y con `leading: BackButton()`; calibración visual de tarjetas con `childAspectRatio: 0.65`, contenedores elásticos en `Expanded` y fotos en `Positioned.fill` (eliminando espacios blancos excesivos y previniendo `RenderFlex overflowed`); deserialización tolerante de tipos `num` y `Decimal` (`"310.00"`); tipografía corporativa unificada en `Outfit`; y orquestación del Hub raíz con `PantallaPrincipalHub` (`IndexedStack` de 4 posiciones: Inicio, Buscar, Catálogo en blanco para CU05, Perfil) con saludo dinámico para el usuario autenticado (ej. "Joaquinita Chumacero").

### Registro de Errores Corregidos y Soluciones Aplicadas
26. **Espacio en Blanco Excesivo y Desproporción Fotográfica en Tarjetas Móviles (`ColeccionesScreen`)**:
    - *Causa:* El contenedor de la tarjeta forzaba una altura fija con márgenes rígidos que dejaban un área blanca desproporcionada debajo de la fotografía de la colección.
    - *Solución:* Ajuste de `childAspectRatio: 0.65`, integración de imagen fotográfica en `Expanded` con `Positioned.fill` y `fit: BoxFit.cover`, logrando un encuadre editorial compacto y equilibrado.
27. **Discrepancia Tipográfica en Tarjetas de Colección Móviles**:
    - *Causa:* Ciertas etiquetas y badges utilizaban estilos o fuentes por defecto de Flutter sin aplicar los tokens normativos del Design System.
    - *Solución:* Unificación tipográfica atómica bajo la familia `Outfit`, tracking normativo (`letterSpacing: 0.8-1.1`), pesos `FontWeight.w600/w700` y paleta Obsidian/Camel de `fashionstore-tokens.md`.
28. **Incompatibilidad de Tipos en Deserialización de Precios Monetarios (`TypeError: String is not a subtype of num`)**:
    - *Causa:* FastAPI serializa campos `Decimal` de SQLAlchemy como cadenas JSON (ej. `"310.00"`), produciendo un fallo de conversión directa a `num` en Dart.
    - *Solución:* Implementación de parsing tolerante y robusto mediante `double.tryParse(json['precio_base'].toString()) ?? 0.0`.
29. **Navegación Circular y Corrupción de Pila entre Pestañas Raíz en Flutter**:
    - *Causa:* Cada pantalla (`Inicio`, `Buscar`, `Perfil`) creaba su propio `Scaffold` con `BottomNavigationBar` local y utilizaba `Navigator.push` entre sí, provocando apilamiento de rutas y callbacks desalineados (ej. pulsar Inicio desde Perfil solo ejecutaba un `setState` local).
    - *Solución:* Creación de `PantallaPrincipalHub` con un único `Scaffold` raíz e `IndexedStack` de 4 pestañas (`Inicio`, `Buscar`, `Catálogo`, `Perfil`), permitiendo alternar instantáneamente entre vistas por índice sin duplicar rutas y reservando `Navigator.push` exclusivamente para pantallas secundarias como `ColeccionesScreen`.
30. **Nombre de Usuario Estático en Saludo de Bienvenida en Móvil**:
    - *Causa:* `InicioBloc` inicializaba con `'Ana Valenzuela'` quemado y `main.dart` no transfería los datos del usuario autenticado tras el inicio de sesión.
    - *Solución:* Propagación de `LoginRespuestaDto` desde `PantallaLogin` hacia `PantallaPrincipalHub` y `PantallaInicio`, y consulta asíncrona de perfil con el token activo, mostrando dinámicamente el nombre real (ej. "Joaquinita Chumacero").

## [1.6.0] - 2026-09-21

### Directriz Arquitectónica Global de Navegación y Jerarquía de Vistas (Hub-and-Spoke)
- **Definición Canónica:** Establecimiento formal de la directriz en [`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](.specs/architecture/directriz-navegacion-hub-and-spoke.md).
- **Las 4 Pantallas Principales (Raíz / Hub):** Únicamente `/inicio`, `/buscar`, `/catalogo` y `/perfil` disponen de barra de navegación principal (navbar Web / BottomNavigationBar Mobile) permanentemente visible. Prohibido incluir botón de retroceso (`← Volver`).
- **Pantallas Secundarias (Hojas / Spoke):** Cualquier caso de uso derivado (incluyendo `CU36 Colecciones` y su vista de detalle) debe ocultar la barra de navegación principal y disponer de un botón de regreso obligatorio (`← Volver` / `leading: BackButton()`) hacia la pantalla previa desde la que se accedió.
- **Alineación de CU36:** Actualizadas las especificaciones activas de `CU36` (`spec.md`, `plan.md`, `tasks.md`, `checkpoint.md`, `change-consultar-colecciones.md`) para cumplir estrictamente con el patrón Hub-and-Spoke.

## [1.5.0] - 2026-09-20

### Promoción a Baseline Permanente
- **CU06 - Buscar y Filtrar Productos (Catálogo Omnicanal de Alta Costura Femenina):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/catalogo_productos/CU06-buscar-filtrar-productos.md`](.specs/modules/catalogo_productos/CU06-buscar-filtrar-productos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU06-buscar-filtrar-productos/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 83/83 tests en verde en `pytest` para toda la suite acumulada (20/20 específicos de catálogo); modelos ORM del catálogo (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`), motor de búsqueda con normalización sin tildes/mayúsculas, expansión de singular/plural, búsqueda por palabras sueltas multicriterio, filtros 100% opcionales y endpoints `GET /api/v1/productos`, `GET /api/v1/catalogo/filtros-disponibles` y `POST /api/v1/catalogo/buscar`.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, 0 errores), 41/41 tests pasando en Vitest / Angular CLI (17/17 de catálogo), componente `BuscarProductosComponent` con confirmación diferida mediante botón `BUSCAR` y `Enter`, vaciado automático de input, badge editorial dismissible, paleta de 16 colores textiles, tipografía Outfit estandarizada y alineación pixel-perfect unificada con `/perfil` mediante `scrollbar-gutter: stable` y `max-w-[1440px] px-6`.
  - Mobile: 56/56 tests en verde en `flutter test` (14 de catálogo), 0 incidencias en `flutter analyze`, `CatalogoBloc` con estados sellados inmutables, `PantallaBuscarProductos` con carrusel horizontal de temporadas, filtros refinados con tallas cuadradas y 16 tonalidades, `GridView` de 2 columnas con tarjetas de lujo (`+ CESTA`, badges editoriales, favoritos), modal BottomSheet de rango y orden, y conexión fluida en BottomNavigationBar.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 21. Normalización Morfológica y Coincidencia Flexible en Búsqueda Multicriterio (`Términos sinónimos y palabras sueltas`)
- **Causa:** Las consultas de búsqueda requerían coincidencia exacta o fallaban al buscar categorías directas ("vestido" vs "vestidos", "pantalón" con o sin tilde).
- **Solución:** Implementación de `_normalizar_texto` (remoción de acentos/diacríticos y minúsculas), expansión semántica `_expandir_termino` (singular/plural de prendas y sinónimos de moda) y consultas combinadas con `or_` sobre nombre, descripción, categoría, colección, temporada y color sin error 500.

#### 22. Inconsistencia de Color y Modelo en Catálogo Femenino de Alta Costura
- **Causa:** El producto "Vestido plisado seda" estaba incorrectamente listado como mármol, y existía una fotografía con modelo masculino en el catálogo de una firma exclusivamente orientada a moda femenina.
- **Solución:** Corrección de semilla y registros a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ`, sustitución de imágenes masculinas por modelos femeninas de alta costura, y expansión de la paleta textil a 16 tonalidades de confección real.

#### 23. Confirmación Explícita de Búsqueda y Modo Borrador Diferido (Web y Mobile)
- **Causa:** Los filtros o la escritura en el campo de texto ejecutaban peticiones tempranas innecesarias o generaban discrepancias si el usuario modificaba varios filtros a la vez.
- **Solución:** Implementación de modo borrador diferido en Angular y Flutter, botón explícito `BUSCAR` + tecla `Enter`, vaciado automático del input tras la confirmación y almacenamiento del término activo en badge editorial dismissible.

#### 24. Desalineación Visual de Cabecera y Salto Horizontal entre Páginas Web
- **Causa:** `/perfil` utilizaba `max-w-7xl` (1280px) mientras que `/buscar` utilizaba `max-w-[1440px] px-6`, y la aparición/desaparición de la barra de scroll vertical producía un brinco horizontal de 15px en la barra institucional y avatar.
- **Solución:** Homologación estricta a `max-w-[1440px] px-6` en `perfil.component.html` y adición de la directiva `scrollbar-gutter: stable;` en `styles.scss`, garantizando estabilidad geométrica absoluta.

#### 25. Tipografía No Conforme en Titular "Visto recientemente"
- **Causa:** Se empleaba tipografía cursiva serif en "Visto recientemente", desalineada con el Design System general.
- **Solución:** Sustitución por la tipografía institucional `Outfit` (`font-sans font-semibold tracking-tight`), unificando la identidad visual corporativa en Desktop y Mobile.

---

## [1.4.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU33 - Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU33-recuperar-acceso.md`](.specs/modules/autenticacion_seguridad/CU33-recuperar-acceso.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU33-recuperar-acceso/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 63/63 tests en verde en `pytest` para toda la suite acumulada; modelo relacional `CodigoRecuperacionORM` en esquema `fashionstore` (migración Alembic `0002_codigos_recuperacion.py`), persistencia segura mediante digest SHA-256 (nunca texto plano), política anti-enumeración de usuarios uniforme con `200 OK`, rate limiting de 60s y hashing de clave con **Argon2id**.
  - Servicio SMTP y Entregabilidad: Integración asíncrona mediante `asyncio.to_thread` con Gmail SMTP (`smtp.gmail.com:587` STARTTLS); cabeceras RFC 5322 (`Message-ID`, `Date`) y RFC 3834 (`Auto-Submitted: auto-generated`), eliminando clasificación en spam y garantizando entrada directa a Inbox.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle en 3.7s), 17/17 tests pasando en Vitest / Angular CLI, fidelidad visual exacta con la captura Desktop (badge FS, medidor dinámico de 3 barras horizontales, timer reactivo de reenvío de 60s y botón `ACTUALIZAR Y ACCEDER →`).
  - Mobile: 42/42 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, `RecuperarPasswordBloc` con estados sellados, diseño fiel a la captura Mobile (tarjeta, monograma FS, 3 barras de fuerza dinámicas, escudo inferior) y conexión en login.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 18. Rechazo de Autenticación SMTP por Contraseña Estándar de Gmail (`535 5.7.8 BadCredentials`)
- **Causa:** Google descontinuó el acceso por contraseña básica en junio de 2022 y requiere Contraseña de Aplicación de 16 caracteres generada tras activar 2FA.
- **Solución:** Parametrización en `.env` y `Settings` con contraseña de aplicación de 16 caracteres y diagnóstico activo con `logging.basicConfig(level=logging.INFO)` en `main.py`.

#### 19. Entregabilidad de Correo en Bandeja de Spam por Cabeceras Faltantes y Términos de Phishing
- **Causa:** Falta de cabeceras RFC 5322 (`Message-ID`, `Date`), falta de RFC 3834 (`Auto-Submitted: auto-generated`), codificación sin `Header(..., 'utf-8')` y términos de riesgo heurístico en la plantilla ("Seguridad Criptográfica 256-Bit SSL", emojis en celdas).
- **Solución:** Generación de `Message-ID` y `Date` RFC, adición de metadatos transaccionales y depuración de la plantilla HTML/Text, logrando entrada garantizada en la Bandeja Principal (Inbox).

#### 20. Desbordamiento de Rótulo en Pantallas Móviles Pequeñas (`RenderFlex overflowed`)
- **Causa:** En anchos reducidos, el rótulo de 6 dígitos y el botón de reenvío en la misma fila desbordaban el ancho disponible.
- **Solución:** Aplicación de `Flexible(child: Text(..., overflow: TextOverflow.ellipsis))` para adaptación fluida en cualquier resolución.

---

## [1.3.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU03 - Cerrar Sesión (Logout / Revocación Omnicanal de Token y Purga Segura):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU03-cerrar-sesion.md`](.specs/modules/autenticacion_seguridad/CU03-cerrar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU03-cerrar-sesion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 52/52 tests en verde en `pytest` para toda la suite acumulada; implementación de `TokenBlacklistService` en memoria con indexación SHA-256 y expiración automática; rechazo garantizado con `401 Unauthorized` (`code="TOKEN_REVOCADO"`) ante reuso de token en endpoints protegidos.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle completado en 4.22s), 10/10 tests pasando en Vitest / Angular CLI, purga integral y resiliente de `localStorage` y `sessionStorage` en `finalize()` de `LoginService`, reseteo de Signal reactivo `usuarioActual.set(null)` y etiqueta unificada estricta `CERRAR SESIÓN`.
  - Mobile: 30/30 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, reinicio de `LoginBloc`, blindaje de pila de navegación con `pushAndRemoveUntil(..., (route) => false)` y etiqueta de botón invariable `CERRAR SESIÓN`.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 15. Consistencia Visual y Estabilidad de Texto en Botón de Salida (`CERRAR SESIÓN`)
- **Causa:** Se proponían rótulos extendidos ("CERRAR SESIÓN SEGURA") o textos dinámicos durante el proceso de carga.
- **Solución:** Fijación del texto unificado como `CERRAR SESIÓN` en Frontend y Mobile por especificación estricta de experiencia de usuario.

#### 16. Resolución de Rutas Relativas Profundas en Widgets de Flutter (`Package Imports`)
- **Causa:** Importaciones relativas (`../../cu02_iniciar_sesion/...`) en `pantalla_perfil.dart` fallaban al compilar desde tests debido a la profundidad de tres niveles de subdirectorios en `presentacion/pantallas`.
- **Solución:** Migración a importaciones canónicas de paquete (`import 'package:ec_mobile/src/...'`), garantizando resolución universal en desarrollo y pruebas.

#### 17. Contrato de Interfaz de Repositorio en Mocks de Test (`cerrarSesion`)
- **Causa:** La adición de `cerrarSesion(String token)` a la interfaz abstracta `LoginRepositorio` rompía mocks no actualizados en suites de test de widgets (`MockLoginRepositorio`).
- **Solución:** Implementación del método en todos los mocks de prueba (`test/pantalla_login_test.dart`, etc.), restableciendo 100% de tests en verde.

---

## [1.2.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU04 - Gestionar Perfil del Cliente (Consulta, Actualización y Panel Mi Cuenta):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU04-gestionar-perfil.md`](.specs/modules/autenticacion_seguridad/CU04-gestionar-perfil.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU04-gestionar-perfil/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 45/45 tests en verde en `pytest` para toda la suite acumulada; verificación en vivo de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` sobre Neon PostgreSQL Serverless.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 tests pasando en `ng test`, refresco instantáneo de estado bajo `OnPush` con `ChangeDetectorRef` y sincronización con `sessionStorage`/`localStorage`.
  - Mobile: 28/28 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, inyección de token real desde login y actualización interactiva en tiempo real.
  - Verificación en Vivo: Probado y validado en vivo por el usuario en web y móvil.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 11. Expiración Temprana de Token JWT (`401 Unauthorized: Signature has expired`)
- **Causa:** El tiempo de expiración por defecto de tokens de acceso (`ACCESS_TOKEN_EXPIRE_MINUTES`) era de 60 minutos (o 15 minutos en configuración base), causando desconexiones silenciosas durante pruebas extendidas y edición de perfil.
- **Solución:** Se amplió `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24 horas) en `app/core/config.py` y `.env` para asegurar persistencia durante desarrollo y depuración.

#### 12. Exclusión de Selector de Género por Modelo de Marca de Alta Costura Femenina
- **Causa:** Se incluía selector de género en los formularios de edición de perfil, lo cual no aplica para una firma exclusivamente orientada a indumentaria femenina (ni para cuentas de empleados).
- **Solución:** Retiro completo del selector de género en el HTML/TypeScript de Angular (`PerfilComponent`) y en el bottom sheet modal de Flutter (`PantallaPerfil`), manteniendo en el backend compatibilidad opcional sin forzar su uso.

#### 13. Falta de Persistencia y Refresco Inmediato de Perfil en Frontend Web
- **Causa:** Los cambios confirmados en el modal de edición no actualizaban el storage local de sesión (`fashionstore_user`) y la estrategia `OnPush` no redibujaba los datos sin una recarga manual de página.
- **Solución:** Implementación de `sincronizarSesionStorage(perfilActualizado)` e inyección de `ChangeDetectorRef` con llamada a `this.cdr.markForCheck()` tras la respuesta del backend.

#### 14. Discrepancia de Datos de Cuenta y Persistencia en App Móvil
- **Causa:** `PantallaPerfil` consumía datos con un token mock por defecto en vez del token dinámico emitido por el login en Neon PostgreSQL, mostrando datos de prueba no coincidentes con el usuario real.
- **Solución:** Conexión del callback `alCompletarLoginConToken` en `PantallaLogin` de Flutter hacia `PantallaPerfil(token: token)` y emisión reactiva inmediata de `PerfilCargadoState` en `PerfilBloc` tras el guardado atómico en PostgreSQL.

---

## [1.1.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU02 - Iniciar Sesión (Login / Autenticación Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU02-iniciar-sesion.md`](.specs/modules/autenticacion_seguridad/CU02-iniciar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU02-iniciar-sesion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 
  - Backend: 28/28 tests en verde en `pytest` y verificación en vivo de autenticación (códigos 200, 401) y actualización atómica de `ultimo_acceso` en Neon PostgreSQL.
  - Frontend Web: Compilación limpia en 5.4s con Angular CLI (`npm run build`) y comunicación proxy verificada (`/api/v1/autenticacion/login`).
  - Mobile: 19/19 tests en verde en `flutter test` y 0 incidencias en `flutter analyze`.

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 8. Error: `OPTIONS 400 Bad Request` y `ClientException: Failed to fetch` en Flutter Web
- **Causa:** Al ejecutar Flutter en navegador (`flutter run -d edge` o `chrome`), Flutter Web asigna un puerto efímero dinámico en desarrollo (ej. `http://localhost:50870`). Starlette `CORSMiddleware` evaluaba el origen únicamente contra una lista estática `settings.CORS_ORIGINS`. Al no coincidir el puerto, Starlette rechazaba el preflight `OPTIONS` con `400 Bad Request` (`Disallowed CORS origin`), provocando que el navegador bloqueara la petición `POST`.
- **Solución:** Se implementó `CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"` en `app/core/config.py` y se configuró `allow_origin_regex` en `CORSMiddleware` en `app/main.py` y `Ec-backend/.env`, admitiendo cualquier puerto de depuración local conservando el aislamiento estricto en producción.

#### 9. RenderFlex Overflows en `PantallaLogin` (Flutter)
- **Causa:** En resoluciones móviles estrechas, la fila de contraseña (`CONTRASEÑA` y `¿Olvidaste tu contraseña?`) y la fila de checkbox (`Recordar en este dispositivo`) provocaban desbordamientos horizontales por rigidez de constraints sin `Flexible`/`Expanded`.
- **Solución:** Se envolvieron los textos y componentes en `Flexible` y `Expanded` con manejo de elipsis en textos de seguridad, eliminando desbordamientos en cualquier ancho de pantalla.

#### 10. Flujo y Enrutamiento Bidireccional en Aplicación Móvil
- **Causa:** La aplicación móvil iniciaba en `PantallaRegistro` y el enlace inferior no permitía acceder a la pantalla de login cuando ésta no estaba en la pila de navegación.
- **Solución:** Se estableció `home: const PantallaLogin()` en `Ec-mobile/lib/main.dart` como punto de entrada primario y se configuró un enrutamiento bidireccional inteligente en `PantallaRegistro` que evalúa `Navigator.canPop(context)` para hacer `pop()` o `pushReplacement(...)` hacia `PantallaLogin`.

---

## [1.0.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU01 - Registrarse (Alta Costura & Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`.specs/modules/autenticacion_seguridad/CU01-registrarse.md`](.specs/modules/autenticacion_seguridad/CU01-registrarse.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `.specs/finalized/CU01-autenticacion/` y limpiado el directorio de cambios activos `.specs/changes/`.
- **Validación Completa:** 15/15 tests en verde en `Ec-backend`, 7/7 tests unitarios en `Ec-mobile`, build exitoso en `Ec-frontend`, y esquema PostgreSQL migrado a la base de datos en la nube (Neon Serverless).

---

### Errores Corregidos y Soluciones Técnicas Aplicadas

#### 1. Error: `ModuleNotFoundError: No module named 'core'`
- **Causa:** Tras reorganizar los archivos dentro del paquete `app/` (`app/core`, `app/modules`), las rutas de importación directas quedaron desalineadas con respecto a la raíz del proyecto. Al ejecutarse herramientas externas o subprocesos sin tener `app/` en la variable de entorno `PYTHONPATH`, Python intentaba localizar `core` en el directorio de trabajo inmediato y fallaba.
- **Solución:** Se unificaron las importaciones canónicas, se insertó `app/` en `sys.path` al inicio de `app/main.py` y `alembic/env.py`, y se configuró formalmente `pythonpath = ["app", "."]` en el archivo `pyproject.toml`. De este modo, tanto pytest, uvicorn como los scripts CLI resuelven de forma idéntica e inequívoca las rutas de módulos.

#### 2. Error: `ModuleNotFoundError: No module named 'psycopg2'`
- **Causa:** Las cadenas de conexión estándar de PostgreSQL proporcionadas por servicios en la nube (como Neon o Render) comienzan con el prefijo genérico `postgresql://`. Por especificación interna de SQLAlchemy, dicho prefijo invoca automáticamente el driver histórico `psycopg2`. Dado que el proyecto utiliza la versión moderna y asíncrona/síncrona de alto rendimiento `psycopg` (v3, paquete `psycopg[binary]`), la ejecución fallaba por ausencia de `psycopg2`.
- **Solución:** Se implementó una normalización automática y transparente de la URL de conexión en `app/core/database.py` y `alembic/env.py`. Si la variable `DATABASE_URL` comienza por `postgresql://` o `postgres://`, el sistema la transforma en tiempo de ejecución a `postgresql+psycopg://`, forzando el uso exclusivo del driver Psycopg 3 instalado.

#### 3. Error: `ImportError: email-validator is not installed`
- **Causa:** Los esquemas de validación Pydantic (`RegistroClienteIn`) implementan el tipo `EmailStr` para garantizar la conformidad estricta con el estándar RFC 5322. Pydantic delega esta validación en la librería de terceros `email-validator`, la cual no se encontraba declarada en las dependencias base del entorno virtual.
- **Solución:** Se instaló la librería en el entorno virtual (`.venv`) y se añadió formalmente `email-validator>=2.0.0` a la lista de dependencias obligatorias en `pyproject.toml`.

#### 4. Error: Fallos 404 en `tests/test_health.py` (AssertionError en handlers de error)
- **Causa:** Divergencia de instancias de la aplicación en memoria (`sys.modules`). El archivo `tests/test_health.py` importaba la aplicación mediante `from main import app`, mientras que el archivo de fixtures `tests/conftest.py` lo hacía a través de `from app.main import app`. Como consecuencia, Python instanció dos objetos `FastAPI` independientes; las rutas auxiliares de prueba registradas por el test residían en una instancia distinta a la evaluada por el cliente de pruebas `TestClient`, provocando respuestas `404 Not Found`.
- **Solución:** Se homologaron de forma estricta todas las referencias de importación en la suite de pruebas hacia `from app.main import app`, alineando el espacio de nombres, y se eliminaron los directorios residuales de caché compilada (`__pycache__` y `.pyc`).

#### 5. Problema: Metadatos vacíos en Alembic (`Base.metadata` sin tablas)
- **Causa:** SQLAlchemy 2.0 opera mediante un registro declarativo bajo demanda: las tablas solo se agregan a `Base.metadata` cuando el intérprete de Python carga e importa explícitamente las clases ORM que heredan de `Base`. Si `alembic/env.py` solo importa `Base`, `target_metadata` permanece vacío y el comando `alembic revision --autogenerate` no detecta ningún cambio ni tabla a migrar.
- **Solución:** Se implementó un mecanismo de auto-descubrimiento dinámico e introspección de paquetes en `alembic/env.py` utilizando las librerías estándar `pkgutil.walk_packages` e `importlib`. Al inicializarse Alembic, se escanea recursivamente el directorio de paquetes `app/modules` e importa automáticamente cualquier módulo que contenga definiciones ORM (`.modelos`), registrando todas las tablas en `Base.metadata` sin requerir importaciones manuales para cada nuevo caso de uso.

#### 6. Error Adicional Resuelto: Incompatibilidad con PgBouncer en Neon (`unsupported startup parameter: search_path`)
- **Causa:** La cadena de conexión de Neon configurada con *Connection Pooling* (`-pooler`) interactúa a través del proxy PgBouncer en modo transacción. Al pasar `connect_args={"options": "-c search_path=fashionstore,public"}`, PgBouncer rechaza la conexión en el paquete de inicio (*startup packet*) con el error `ERROR: unsupported startup parameter in options: search_path`.
- **Solución:** Se eliminó el parámetro `options` de los argumentos de conexión de arranque en `app/core/database.py` y se reemplazó por un listener de ciclo de vida `@event.listens_for(engine, "connect")` que ejecuta `SET search_path TO fashionstore, public` inmediatamente tras establecerse la conexión física, garantizando compatibilidad total con Neon Serverless.

#### 7. Error Adicional Resuelto: Discordancia de Tipos en Columna `rol` (`DatatypeMismatch`)
- **Causa:** En la base de datos PostgreSQL de Neon, la columna `usuarios.rol` fue creada como tipo `ENUM` nativo (`fashionstore.rol_usuario`). En el modelo `UsuarioORM`, la columna estaba tipada como `String(30)`. Al ejecutar el `INSERT`, SQLAlchemy emitía `%(rol)s::VARCHAR`, lo que provocaba que PostgreSQL abortara la transacción por discordancia de tipo de dato (`column "rol" is of type rol_usuario but expression is of type character varying`).
- **Solución:** Se importó `from sqlalchemy.dialects.postgresql import ENUM as PG_ENUM` en `app/modules/autenticacion_seguridad/modelos.py` y se mapeó la columna con `rol_usuario_enum` configurado con `create_type=False`, asegurando que el driver emita el valor con el cast nativo a `fashionstore.rol_usuario`.
