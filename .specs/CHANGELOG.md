# Changelog Técnico de Arquitectura y SDD — FashionStore

Ver documento principal en [../../CHANGELOG.md](../../CHANGELOG.md).

## [1.9.0] - 2026-09-21

### Auditoría Transversal, Corrección de Defectos de Contrato y Reconciliación Documental
- **Defectos corregidos (34–42 en el changelog principal):** HTTP 500 en `GET /api/v1/colecciones/activas` por columnas renombradas sin migración; dos HTTP 500 sin manejar en el flujo de reservas de CU12 (variante duplicada e inventario multitemporada); HTTP 422 sistemático al reservar desde móvil; listener de sesión móvil autodesactivado tras el login; ficha de producto móvil sin fotografía ni galería; HTTP 401 al reservar desde las pestañas Catálogo y Buscar; confirmación de reserva web con campos en blanco; y sesión anónima tras completar el registro en web.
- **Causa raíz común:** las suites de pruebas no observaban los contratos reales —el backend mockea la sesión de base de datos y el móvil construía sus DTO con constructores sin ejercitar `fromJson`—, de modo que los tres bloques reportaban verde mientras CU12 era imposible de completar desde la aplicación móvil. Los mocks se reescribieron a partir de payloads literales del backend y se añadió un grupo de pruebas de contrato.
- **Reconciliación documental:** actualizada la directriz Hub-and-Spoke (declaraba CU05 pendiente y CU36 «en migración de layout en Web»); cerrados los gates de `change-detalle-producto-reservas.md` y `change-landing-page-publica.md`, que afirmaban no haber generado código con 18 y 13 tareas marcadas; resuelto el conflicto de rutas de `/inicio` y `/colecciones` a favor del enrutamiento vigente; marcado el Bloque 3 (Mobile) de CU07/CU08/CU09/CU12 según el repositorio real; y corregida la declaración de promoción de CU18, que nunca llegó a materializarse en `.specs/modules/`.
- **Segunda pasada (2026-09-22) — deriva de esquema:** errores HTTP 500 reproducidos en la aplicación en ejecución revelaron que `TemporadaORM`, `PromocionORM` y `ProveedorORM` mapeaban columnas (`activa`, `activo`, `nit`) que en PostgreSQL se llaman `estado_activo` y `nit_rut`, tumbando catálogo, filtros de búsqueda y colecciones. La trampa de fondo es que `alembic/versions/0001_base_ddl.py` **no refleja el esquema desplegado en Neon**: el ORM y la migración coincidían entre sí y discrepaban de la realidad, y ningún test lo veía porque todos mockean la sesión. Se alinearon los modelos con la base real sin tocar el esquema y se añadió `Ec-backend/tests/test_esquema_bd.py` como guardia permanente. Se corrigió además el diagnóstico previo de este mismo changelog, que atribuía el fallo a un renombrado indebido y lo había revertido.
- **También en la segunda pasada:** los HTTP 500 dejaron de disfrazarse de «Failed to fetch» (middleware registrado por dentro del `CORSMiddleware`, ya que `@app.exception_handler(Exception)` se monta en el `ServerErrorMiddleware`, por fuera de CORS), y se restauró la landing page pública, inalcanzable desde que CU05 introdujo un `path: ''` por delante del suyo. Se añadió la ruta comodín 404 que faltaba y el guard `app.routes.spec.ts`.
- **Deuda registrada, no corregida:** `alembic/versions/0001_base_ddl.py` no describe la base de datos real (reconciliarla es una decisión de esquema, pendiente de autorización); datos fabricados servidos como reales en `/sucursales/activas`, `/productos/{id}/disponibilidad` y `/productos/{id}` (bloquea CP-20 de CU07/CU12); credenciales SMTP como valores por defecto en `app/core/config.py`; `CORS_ORIGIN_REGEX` que admite cualquier dominio `*.vercel.app` con credenciales; `esTokenExpirado` que falla en abierto; y blacklist de tokens en memoria de proceso único.

## [1.8.0] - 2026-09-21

### Promoción a Baseline Permanente
- **CU05 - Consultar Catálogo de Productos (Colección General, Atelier & Sastrería Femenina):** Promovido oficialmente a especificación técnica permanente del sistema en [`modules/catalogo_productos/CU05-consultar-catalogo.md`](modules/catalogo_productos/CU05-consultar-catalogo.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU05-consultar-catalogo/` y limpiado el directorio de cambios activos `changes/`.
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
- **CU36 - Consultar Colecciones (Colecciones Activas y Exploración de Prendas por Colección):** Promovido oficialmente a especificación técnica permanente del sistema en [`modules/catalogo_productos/CU36-consultar-colecciones.md`](modules/catalogo_productos/CU36-consultar-colecciones.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU36-consultar-colecciones/` y limpiado el directorio de cambios activos `changes/`.
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
- **Definición Canónica:** Establecimiento formal de la directriz en [`architecture/directriz-navegacion-hub-and-spoke.md`](architecture/directriz-navegacion-hub-and-spoke.md).
- **Las 4 Pantallas Principales (Raíz / Hub):** Únicamente `/inicio`, `/buscar`, `/catalogo` y `/perfil` disponen de barra de navegación principal (navbar Web / BottomNavigationBar Mobile) permanentemente visible. Prohibido incluir botón de retroceso (`← Volver`).
- **Pantallas Secundarias (Hojas / Spoke):** Cualquier caso de uso derivado (incluyendo `CU36 Colecciones` y su vista de detalle) debe ocultar la barra de navegación principal y disponer de un botón de regreso obligatorio (`← Volver` / `leading: BackButton()`) hacia la pantalla previa desde la que se accedió.
- **Alineación de CU36:** Actualizadas las especificaciones activas de `CU36` (`spec.md`, `plan.md`, `tasks.md`, `checkpoint.md`, `change-consultar-colecciones.md`) para cumplir estrictamente con el patrón Hub-and-Spoke.

## [1.5.0] - 2026-09-20

### Promoción a Baseline Permanente
- **CU06 - Buscar y Filtrar Productos (Catálogo Omnicanal de Alta Costura Femenina):** Promovido oficialmente a especificación permanente del sistema en [`modules/catalogo_productos/CU06-buscar-filtrar-productos.md`](modules/catalogo_productos/CU06-buscar-filtrar-productos.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU06-buscar-filtrar-productos/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 83/83 tests en verde en `pytest` para toda la suite acumulada (20/20 específicos de catálogo); modelos ORM del catálogo (`ProductoORM`, `CategoriaORM`, `ColeccionORM`, `TemporadaORM`, `TallaORM`, `ColorORM`, `VarianteProductoORM`, `InventarioSucursalORM`), motor de búsqueda con normalización sin tildes/mayúsculas, expansión de singular/plural, búsqueda por palabras sueltas multicriterio, filtros 100% opcionales y endpoints `GET /api/v1/productos`, `GET /api/v1/catalogo/filtros-disponibles` y `POST /api/v1/catalogo/buscar`.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, 0 errores), 41/41 tests pasando en Vitest / Angular CLI (17/17 de catálogo), componente `BuscarProductosComponent` con confirmación diferida mediante botón `BUSCAR` y `Enter`, vaciado automático de input, badge editorial dismissible, paleta de 16 colores textiles, tipografía Outfit estandarizada y alineación pixel-perfect unificada con `/perfil` mediante `scrollbar-gutter: stable` y `max-w-[1440px] px-6`.
  - Mobile: 56/56 tests en verde en `flutter test` (14 de catálogo), 0 incidencias en `flutter analyze`, `CatalogoBloc` con estados sellados inmutables, `PantallaBuscarProductos` con carrusel horizontal de temporadas, filtros refinados con tallas cuadradas y 16 tonalidades, `GridView` de 2 columnas con tarjetas de lujo (`+ CESTA`, badges editoriales, favoritos), modal BottomSheet de rango y orden, y conexión fluida en BottomNavigationBar.

### Registro de Errores Corregidos y Soluciones Aplicadas
21. **Normalización Morfológica y Coincidencia Flexible en Búsqueda Multicriterio (`Términos sinónimos y palabras sueltas`)**:
    - *Causa:* Las consultas de búsqueda requerían coincidencia exacta o fallaban al buscar categorías directas ("vestido" vs "vestidos", "pantalón" con o sin tilde).
    - *Solución:* Implementación de `_normalizar_texto` (remoción de acentos/diacríticos y minúsculas), expansión semántica `_expandir_termino` (singular/plural de prendas y sinónimos de moda) y consultas combinadas con `or_` sobre nombre, descripción, categoría, colección, temporada y color sin error 500.
22. **Inconsistencia de Color y Modelo en Catálogo Femenino de Alta Costura**:
    - *Causa:* El producto "Vestido plisado seda" estaba incorrectamente listado como mármol, y existía una fotografía con modelo masculino en el catálogo de una firma exclusivamente orientada a moda femenina.
    - *Solución:* Corrección de semilla y registros a "Rojo Carmín" (`#991B1B`), SKU `VES-PLI-xx-ROJ`, sustitución de imágenes masculinas por modelos femeninas de alta costura, y expansión de la paleta textil a 16 tonalidades de confección real.
23. **Confirmación Explícita de Búsqueda y Modo Borrador Diferido (Web y Mobile)**:
    - *Causa:* Los filtros o la escritura en el campo de texto ejecutaban peticiones tempranas innecesarias o generaban discrepancias si el usuario modificaba varios filtros a la vez.
    - *Solución:* Implementación de modo borrador diferido en Angular y Flutter, botón explícito `BUSCAR` + tecla `Enter`, vaciado automático del input tras la confirmación y almacenamiento del término activo en badge editorial dismissible.
24. **Desalineación Visual de Cabecera y Salto Horizontal entre Páginas Web**:
    - *Causa:* `/perfil` utilizaba `max-w-7xl` (1280px) mientras que `/buscar` utilizaba `max-w-[1440px] px-6`, y la aparición/desaparición de la barra de scroll vertical producía un brinco horizontal de 15px en la barra institucional y avatar.
    - *Solución:* Homologación estricta a `max-w-[1440px] px-6` en `perfil.component.html` y adición de la directiva `scrollbar-gutter: stable;` en `styles.scss`, garantizando estabilidad geométrica absoluta.
25. **Tipografía No Conforme en Titular "Visto recientemente"**:
    - *Causa:* Se empleaba tipografía cursiva serif en "Visto recientemente", desalineada con el Design System general.
    - *Solución:* Sustitución por la tipografía institucional `Outfit` (`font-sans font-semibold tracking-tight`), unificando la identidad visual corporativa en Desktop y Mobile.

## [1.4.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU33 - Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU33-recuperar-acceso.md`](modules/autenticacion_seguridad/CU33-recuperar-acceso.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU33-recuperar-acceso/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 63/63 tests en verde en `pytest` para toda la suite acumulada; modelo relacional `CodigoRecuperacionORM` en esquema `fashionstore` (migración Alembic `0002_codigos_recuperacion.py`), persistencia segura mediante digest SHA-256 (nunca texto plano), política anti-enumeración de usuarios uniforme con `200 OK`, rate limiting de 60s y hashing de clave con **Argon2id**.
  - Servicio SMTP y Entregabilidad: Integración asíncrona mediante `asyncio.to_thread` con Gmail SMTP (`smtp.gmail.com:587` STARTTLS); cabeceras RFC 5322 (`Message-ID`, `Date`) y RFC 3834 (`Auto-Submitted: auto-generated`), eliminando clasificación en spam y garantizando entrada directa a Inbox.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle en 3.7s), 17/17 tests pasando en Vitest / Angular CLI, fidelidad visual exacta con la captura Desktop (badge FS, medidor dinámico de 3 barras horizontales, timer reactivo de reenvío de 60s y botón `ACTUALIZAR Y ACCEDER →`).
  - Mobile: 42/42 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, `RecuperarPasswordBloc` con estados sellados, diseño fiel a la captura Mobile (tarjeta, monograma FS, 3 barras de fuerza dinámicas, escudo inferior) y conexión en login.

### Registro de Errores Corregidos y Soluciones Aplicadas
18. **Rechazo de Autenticación SMTP por Contraseña Estándar de Gmail (`535 5.7.8 BadCredentials`)**:
    - *Causa:* Google descontinuó el acceso por contraseña básica en junio de 2022 y requiere Contraseña de Aplicación de 16 caracteres generada tras activar 2FA.
    - *Solución:* Parametrización en `.env` y `Settings` con contraseña de aplicación de 16 caracteres y diagnóstico activo con `logging.basicConfig(level=logging.INFO)` en `main.py`.
19. **Entregabilidad de Correo en Bandeja de Spam por Cabeceras Faltantes y Términos de Phishing**:
    - *Causa:* Falta de cabeceras RFC 5322 (`Message-ID`, `Date`), falta de RFC 3834 (`Auto-Submitted: auto-generated`), codificación sin `Header(..., 'utf-8')` y términos de riesgo heurístico en la plantilla ("Seguridad Criptográfica 256-Bit SSL", emojis en celdas).
    - *Solución:* Generación de `Message-ID` y `Date` RFC, adición de metadatos transaccionales y depuración de la plantilla HTML/Text, logrando entrada garantizada en la Bandeja Principal (Inbox).
20. **Desbordamiento de Rótulo en Pantallas Móviles Pequeñas (`RenderFlex overflowed`)**:
    - *Causa:* En anchos reducidos, el rótulo de 6 dígitos y el botón de reenvío en la misma fila desbordaban el ancho disponible.
    - *Solución:* Aplicación de `Flexible(child: Text(..., overflow: TextOverflow.ellipsis))` para adaptación fluida en cualquier resolución.

## [1.3.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU03 - Cerrar Sesión (Logout / Revocación Omnicanal de Token y Purga Segura):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU03-cerrar-sesion.md`](modules/autenticacion_seguridad/CU03-cerrar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU03-cerrar-sesion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 52/52 tests en verde en `pytest` para toda la suite acumulada; implementación de `TokenBlacklistService` en memoria con indexación SHA-256 y expiración automática; rechazo garantizado con `401 Unauthorized` (`code="TOKEN_REVOCADO"`) ante reuso de token en endpoints protegidos.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle completado en 4.22s), 10/10 tests pasando en Vitest / Angular CLI, purga integral y resiliente de `localStorage` y `sessionStorage` en `finalize()` de `LoginService`, reseteo de Signal reactivo `usuarioActual.set(null)` y etiqueta unificada estricta `CERRAR SESIÓN`.
  - Mobile: 30/30 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, reinicio de `LoginBloc`, blindaje de pila de navegación con `pushAndRemoveUntil(..., (route) => false)` y etiqueta de botón invariable `CERRAR SESIÓN`.

### Registro de Errores Corregidos y Soluciones Aplicadas
15. **Consistencia Visual y Estabilidad de Texto en Botón de Salida (`CERRAR SESIÓN`)**:
    - *Causa:* Se proponían rótulos extendidos ("CERRAR SESIÓN SEGURA") o textos dinámicos durante el proceso de carga.
    - *Solución:* Fijación del texto unificado como `CERRAR SESIÓN` en Frontend y Mobile por especificación estricta de experiencia de usuario.
16. **Resolución de Rutas Relativas Profundas en Widgets de Flutter (`Package Imports`)**:
    - *Causa:* Importaciones relativas (`../../cu02_iniciar_sesion/...`) en `pantalla_perfil.dart` fallaban al compilar desde tests debido a la profundidad de tres niveles de subdirectorios en `presentacion/pantallas`.
    - *Solución:* Migración a importaciones canónicas de paquete (`import 'package:ec_mobile/src/...'`), garantizando resolución universal en desarrollo y pruebas.
17. **Contrato de Interfaz de Repositorio en Mocks de Test (`cerrarSesion`)**:
    - *Causa:* La adición de `cerrarSesion(String token)` a la interfaz abstracta `LoginRepositorio` rompía mocks no actualizados en suites de test de widgets (`MockLoginRepositorio`).
    - *Solución:* Implementación del método en todos los mocks de prueba (`test/pantalla_login_test.dart`, etc.), restableciendo 100% de tests en verde.

## [1.2.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU04 - Gestionar Perfil del Cliente (Consulta, Actualización y Panel Mi Cuenta):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU04-gestionar-perfil.md`](modules/autenticacion_seguridad/CU04-gestionar-perfil.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU04-gestionar-perfil/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 45/45 tests en verde en `pytest` para toda la suite acumulada; verificación en vivo de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` sobre Neon PostgreSQL Serverless.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 tests pasando en `ng test`, refresco instantáneo de estado bajo `OnPush` con `ChangeDetectorRef` y sincronización con `sessionStorage`/`localStorage`.
  - Mobile: 28/28 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, inyección de token real desde login y actualización interactiva en tiempo real.
  - Verificación en Vivo: Probado y validado en vivo por el usuario en web y móvil.

### Registro de Errores Corregidos y Soluciones Aplicadas
11. **Expiración Temprana de Token JWT (`401 Unauthorized: Signature has expired`)**:
    - *Causa:* El tiempo de expiración por defecto de tokens de acceso (`ACCESS_TOKEN_EXPIRE_MINUTES`) era corto (15-60 min), causando desconexiones silenciosas durante pruebas extendidas y edición de perfil.
    - *Solución:* Se amplió `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24 horas) en `app/core/config.py` y `.env` para asegurar persistencia durante desarrollo y depuración.
12. **Exclusión de Selector de Género por Modelo de Marca de Alta Costura Femenina**:
    - *Causa:* Se incluía selector de género en los formularios de edición de perfil, lo cual no aplica para una firma exclusivamente orientada a indumentaria femenina (ni para cuentas de empleados).
    - *Solución:* Retiro completo del selector de género en el HTML/TypeScript de Angular (`PerfilComponent`) y en el bottom sheet modal de Flutter (`PantallaPerfil`), manteniendo en el backend compatibilidad opcional sin forzar su uso.
13. **Falta de Persistencia y Refresco Inmediato de Perfil en Frontend Web**:
    - *Causa:* Los cambios confirmados en el modal de edición no actualizaban el storage local de sesión (`fashionstore_user`) y la estrategia `OnPush` no redibujaba los datos sin una recarga manual de página.
    - *Solución:* Implementación de `sincronizarSesionStorage(perfilActualizado)` e inyección de `ChangeDetectorRef` con llamada a `this.cdr.markForCheck()` tras la respuesta del backend.
14. **Discrepancia de Datos de Cuenta y Persistencia en App Móvil**:
    - *Causa:* `PantallaPerfil` consumía datos con un token mock por defecto en vez del token dinámico emitido por el login en Neon PostgreSQL, mostrando datos de prueba no coincidentes con el usuario real.
    - *Solución:* Conexión del callback `alCompletarLoginConToken` en `PantallaLogin` de Flutter hacia `PantallaPerfil(token: token)` y emisión reactiva inmediata de `PerfilCargadoState` en `PerfilBloc` tras el guardado atómico en PostgreSQL.

## [1.1.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU02 - Iniciar Sesión (Login / Autenticación Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU02-iniciar-sesion.md`](modules/autenticacion_seguridad/CU02-iniciar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU02-iniciar-sesion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 28/28 tests en verde en `pytest` y verificación en vivo de autenticación (200 OK, 401 Unauthorized) con actualización atómica de `ultimo_acceso` en Neon PostgreSQL.
  - Frontend Web: Compilación limpia en 5.4s con Angular CLI (`npm run build`) y comunicación proxy verificada.
  - Mobile: 19/19 tests en verde en `flutter test` y 0 incidencias en `flutter analyze`.

### Registro de Errores Corregidos y Soluciones Aplicadas
8. **`OPTIONS 400 Bad Request` y `ClientException: Failed to fetch` en Flutter Web**:
   - *Causa:* Flutter Web corre en puertos efímeros dinámicos (`http://localhost:*`). Starlette `CORSMiddleware` rechazaba los preflights al no estar el puerto dinámico en `CORS_ORIGINS`.
   - *Solución:* Adición de `CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"` en `core/config.py` y `main.py`, permitiendo cualquier puerto local de depuración.
9. **Desbordamientos RenderFlex en `PantallaLogin` de Flutter**:
   - *Causa:* Rótulos de contraseña y checkbox desbordaban en viewports móviles reducidos.
   - *Solución:* Adaptación con `Flexible`, `Expanded` y `TextOverflow.ellipsis`.
10. **Ajuste de Ruta de Entrada y Enrutamiento Bidireccional en Mobile**:
   - *Causa:* La app iniciaba en registro y el enlace inferior no resolvía hacia login cuando era raíz.
   - *Solución:* `home: const PantallaLogin()` en `main.dart` y navegación bidireccional inteligente en `pantalla_registro.dart` con `canPop`/`pushReplacement`.

## [1.0.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU01 - Registrarse (Alta Costura & Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU01-registrarse.md`](modules/autenticacion_seguridad/CU01-registrarse.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU01-autenticacion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 15/15 tests en verde en `Ec-backend`, 7/7 tests unitarios en `Ec-mobile`, build exitoso en `Ec-frontend`, y esquema PostgreSQL migrado a la base de datos en la nube (Neon Serverless).

### Registro de Errores Corregidos y Soluciones Aplicadas
1. **`ModuleNotFoundError: No module named 'core'`**:
   - *Causa:* Desalineación de imports tras mover módulos a `app/`.
   - *Solución:* Inserción de `app/` en `sys.path` y configuración de `pythonpath = ["app", "."]` en `pyproject.toml`.
2. **`ModuleNotFoundError: No module named 'psycopg2'`**:
   - *Causa:* Prefijo `postgresql://` invoca `psycopg2` por defecto en SQLAlchemy en lugar de `psycopg` (v3).
   - *Solución:* Normalización automática de URL a `postgresql+psycopg://` en `database.py` y `alembic/env.py`.
3. **`ImportError: email-validator is not installed`**:
   - *Causa:* Pydantic requiere `email-validator` para validar el tipo `EmailStr`.
   - *Solución:* Instalación y adición formal de `email-validator>=2.0.0` a `pyproject.toml`.
4. **Fallos 404 en `tests/test_health.py`**:
   - *Causa:* Doble instancia de FastAPI en memoria (`main` vs `app.main`).
   - *Solución:* Homologación estricta de imports a `from app.main import app` y limpieza de `.pyc`.
5. **Metadatos vacíos en Alembic (`Base.metadata` sin tablas)**:
   - *Causa:* SQLAlchemy requiere importar los modelos para registrar las tablas.
   - *Solución:* Auto-descubrimiento dinámico e introspección de paquetes con `pkgutil.walk_packages` e `importlib` en `alembic/env.py`.
6. **Incompatibilidad con PgBouncer en Neon (`unsupported startup parameter in options: search_path`)**:
   - *Causa:* El endpoint con connection pooling (`-pooler`) de Neon rechaza el parámetro `search_path` en el paquete de inicio.
   - *Solución:* Eliminación de `options` en `connect_args` y adopción del hook `@event.listens_for(engine, "connect")` para ejecutar `SET search_path TO fashionstore, public`.
7. **Discordancia de tipos en columna `rol` (`DatatypeMismatch`)**:
   - *Causa:* La columna `rol` es tipo `ENUM` nativo (`fashionstore.rol_usuario`), pero en el modelo `UsuarioORM` estaba tipada como `String(30)`, enviando `VARCHAR`.
   - *Solución:* Mapeo con `rol_usuario_enum = PG_ENUM(..., name="rol_usuario", schema="fashionstore", create_type=False)`.
