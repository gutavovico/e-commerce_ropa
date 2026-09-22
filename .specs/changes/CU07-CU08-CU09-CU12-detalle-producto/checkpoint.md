# Puntos de Control y Verificación: Detalle de Producto, Variantes, Disponibilidad y Reservas

**ID del Cambio:** `CU07-CU08-CU09-CU12-detalle-producto`  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estado:** 🟢 CP-01 a CP-18 aprobados (Backend, Web y Mobile) · ⏳ CP-19 y CP-20 pendientes  
**Última verificación (2026-09-22):** `pytest` 123/123 · `ng test` 108/108 + `ng build` 0 errores · `dart analyze` 0 issues + `flutter test` 104/104. Verificación end-to-end contra Neon: catálogo, colecciones activas, filtros, recomendaciones, sucursales y productos responden HTTP 200 con datos reales.

---

## Matriz de Puntos de Control (Checkpoints)

| ID | Capa / Módulo | Criterio de Aprobación | Método de Comprobación | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend API | Endpoint `GET /api/v1/productos/{id_producto}` retorna 200 con ficha completa de alta costura, precios, variantes y galería multi-toma. | Test de integración en Pytest (`test_cu07_detalle_producto.py`). | ✅ Aprobado |
| **CP-02** | Backend Variantes | Variantes devuelven talla, color, SKU y recargo calculados correctamente a partir de `variantes_producto`. | Test unitario con aserciones sobre DTO `ProductoDetalleOut`. | ✅ Aprobado |
| **CP-03** | Backend Disponibilidad | Endpoint `GET /api/v1/productos/{id}/disponibilidad` reporta en tiempo real existencias por boutique física según la variante activa. | Test de integración en Pytest (`test_cu09_disponibilidad.py`). | ✅ Aprobado |
| **CP-04** | Backend Reserva Atómica | `POST /api/v1/reservas` descuenta `cantidad_disponible`, incrementa `cantidad_reservada` y registra auditoría en `movimientos_inventario` en una sola transacción. | Test transaccional en Pytest (`test_cu12_reservas.py`). | ✅ Aprobado |
| **CP-05** | Backend Conflicto Stock | Intento de reserva con unidades agotadas en la sucursal revierte y responde `409 Conflict`. | Test de excepción en Pytest. | ✅ Aprobado |
| **CP-06** | Backend 404 Guard | Consulta de producto inexistente o inactivo retorna código `404 Not Found`. | Test unitario de endpoint. | ✅ Aprobado |
| **CP-07** | Frontend Nav Spoke | `/productos/:id` se renderiza fuera de `MainLayoutComponent` sin la barra de navegación superior institucional. | Inspección de `app.routes.ts` y prueba de layout. | ✅ Aprobado |
| **CP-08** | Frontend Retorno Nativo | Botón `← VOLVER` consume `Location.back()`, retornando al origen real (Catálogo, Colecciones o Búsqueda). | Test unitario en Vitest con espía sobre `Location`. | ✅ Aprobado |
| **CP-09** | Frontend Variantes Signals | Clic en color o talla actualiza reactivamente el SKU, precio final y texto de stock por sucursal. | Test unitario de Signals en `producto-detalle.component.spec.ts`. | ✅ Aprobado |
| **CP-10** | Frontend Galería | Clic en miniaturas (*FRONTAL*, *TEXTURA SEDA*, *ESPALDA*, *COSTURA*) actualiza la fotografía principal. | Test unitario de interacción visual. | ✅ Aprobado |
| **CP-11** | Frontend Modal Reserva | Clic en *"CITA DE PRUEBA BOUTIQUE"* abre el modal interactivo fiel a `image_2e295b.png` con selección de boutique y horario. | Test unitario en `modal-reserva-boutique.component.spec.ts`. | ✅ Aprobado |
| **CP-12** | Frontend CU10 Aislado | Bloque *"SIMULADOR VESTIDOR VIRTUAL & ESCÁNER 3D"* maquetado en su posición sin dependencias 3D ni cámara. | Inspección visual y test unitario. | ✅ Aprobado |
| **CP-13** | Frontend Build | Compilación de producción limpia sin errores TypeScript (`npm run build`). | Ejecución exitosa de `ng build` (0 errores). | ✅ Aprobado |
| **CP-14** | Mobile Nav Spoke | `PantallaProductoDetalle` se ejecuta a pantalla completa mediante `Navigator.push` sin `BottomNavigationBar`. | Test de widget en Flutter con aserción de ausencia de barra inferior. | ✅ Aprobado |
| **CP-15** | Mobile Botón Pop | `AppBar` de detalle cuenta con `leading: IconButton(icon: Icon(Icons.arrow_back))` que invoca `Navigator.pop`. | Test de interacción en `pantalla_producto_detalle_test.dart`. | ✅ Aprobado |
| **CP-16** | Mobile Galería y AR | Galería con indicador `1/4`, 4 miniaturas táctiles y botón flotante en píldora oscura *"PROBAR EN AR"* maquetado. | Test de widget con hallazgo de elementos de galería. | ✅ Aprobado |
| **CP-17** | Mobile Reserva Continua | Acordeón de disponibilidad muestra cada boutique con su propio botón directo *"RESERVAR EN ESTA BOUTIQUE"* (`image_2e3062.png`). | Test de widget sobre botón de reserva por sucursal. | ✅ Aprobado |
| **CP-18** | Mobile Static Analysis | Código Flutter estricto, sin advertencias (`flutter analyze` 0 issues). | Ejecución de `flutter analyze`. | ✅ Aprobado |
| **CP-19** | Catálogo Femenino | 100% indumentaria, modelos, descripciones y tallas de alta costura femenina exclusiva; cero contenido masculino. | Auditoría de assets y consultas en base de datos. | ⏳ Pendiente |
| **CP-20** | Integridad BD Real | Todos los datos de prendas, sucursales y stock provienen estrictamente de PostgreSQL Neon. | Verificación de respuestas API con datos reales. | ⏳ Pendiente (ver Auditoría de Defectos, D-09) |

---

## Auditoría de Defectos (2026-09-21)

Diagnóstico transversal del repositorio. Ninguno de estos defectos era detectable por las suites
existentes: el backend mockea la sesión de base de datos y el móvil construía sus DTO con
constructores sin ejercitar nunca `fromJson`, de modo que los desajustes de contrato quedaban
invisibles mientras las 3 suites reportaban verde.

| ID | Severidad | Defecto | Resolución |
| :--- | :--- | :--- | :--- |
| **D-01** | Crítico | **Deriva entre el ORM y el esquema real de PostgreSQL.** `TemporadaORM`, `PromocionORM` y `ProveedorORM` mapeaban `activa`, `activo` y `nit`, pero en Neon esas columnas se llaman `estado_activo` y `nit_rut`. Tumbaba `GET /api/v1/catalogo`, `/catalogo/filtros-disponibles` y `/colecciones/activas` con `UndefinedColumn`. La migración `0001_base_ddl.py` **no describe la base desplegada**, así que ORM y migración se confirmaban entre sí mientras producción fallaba. | Corregido: nombre real como primer argumento de `mapped_column(...)` conservando los atributos de dominio, sin tocar el esquema. Guardia permanente en `tests/test_esquema_bd.py`. **Corrección de diagnóstico:** una versión previa de esta tabla culpaba a «un renombrado sin migración» y lo revirtió; el diagnóstico estaba invertido y el revert reintrodujo el fallo. La fuente de verdad es la base de datos desplegada, no la migración. |
| **D-02** | Alto | `POST /api/v1/reservas` respondía 500 (`IntegrityError` fuera del árbol `DomainError`) si el payload repetía un `id_variante`, por el `UNIQUE (id_reserva, id_variante)` de `reserva_detalle`; además descontaba el inventario dos veces. | Corregido: el servicio consolida las líneas por variante antes de tocar inventario y valida el tope de 5 unidades sobre el total agrupado (`CANTIDAD_MAXIMA_EXCEDIDA`, 400). |
| **D-03** | Alto | El repositorio de reservas usaba `scalar_one_or_none()` sobre `(id_variante, id_sucursal)`, que no es la clave única real de `inventario_sucursal` (incluye `id_temporada`): con stock en dos temporadas lanzaba `MultipleResultsFound` → 500. | Corregido: selección determinista de la fila que cubre la cantidad pedida (temporada más reciente primero), con fallback informativo. |
| **D-04** | Alto | El DTO móvil de reserva serializaba `fecha_reserva`, `notas_cliente` y `lineas` en lugar de `fecha_hora_atencion`, `observacion` e `items`, por lo que CU12 devolvía **422 en todos los intentos** desde la app. | Corregido en `producto_detalle_dto.dart`; el BLoC envía además `canal_origen: 'movil'`. |
| **D-05** | Alto | La suscripción a `SesionManager` vivía en el widget montado como ruta `home`; navegar al hub reemplazaba esa ruta y la cancelaba. El auto-redirect por 401 quedaba muerto tras el login y **cerrar sesión y volver a entrar dejaba la app en el formulario en silencio**. | Corregido: `main.dart` gestiona la sesión por encima del `Navigator` mediante `navigatorKey`/`scaffoldMessengerKey` globales. |
| **D-06** | Medio | El DTO móvil de CU07 leía `imagen_url` y `galeria_angulos`; el backend emite `imagen_principal` y `galeria`. La ficha mostraba siempre el placeholder y ningún carrusel multiángulo. | Corregido en `ProductoDetalleDto.fromJson`. |
| **D-07** | Medio | Las pestañas Catálogo y Buscar no propagaban el JWT a `PantallaProductoDetalle`, por lo que reservar desde ellas enviaba la petición sin `Authorization` (401 estando logueado). | Corregido: campo `token` añadido a `PantallaCatalogo`, `PantallaBuscarProductos`, `ColeccionesScreen` y `DetalleColeccionScreen`, propagado desde `PantallaPrincipalHub`. |
| **D-08** | Medio | La interfaz web `ReservaConfirmacion` declaraba `codigo_confirmacion`, `total_prendas` y `mensaje_cortesia`, campos que `ReservaCreadaOut` no envía: el modal imprimía «CÓDIGO: » vacío y el toast `Cita confirmada (undefined)`. El spec mockeaba la interfaz propia del frontend, blindando el contrato incorrecto. | Corregido: modelo alineado campo a campo y spec reescrito con un payload real del backend. |
| **D-09** | Medio | El registro web persistía la sesión como `fs_token_acceso`/`fs_usuario`, claves que ningún servicio lee: tras registrarse el usuario quedaba anónimo para el interceptor y `/perfil` rebotaba a `/login`. | Corregido: el registro delega en `LoginService.establecerSesion()`, único propietario de las claves. |

**Deuda registrada, fuera del alcance de esta corrección:** datos fabricados servidos como reales
(`/sucursales/activas` devuelve `cantidad_disponible=5` fijo e inventa boutiques si la tabla está
vacía; `/productos/{id}/disponibilidad` inventa 3 boutiques; `/productos/{id}` inventa tallas y
colores cuando el producto no tiene variantes). Esto bloquea **CP-20** y contradice la regla de
«cero productos inventados» del skill de dominio, porque la UI ofrece existencias que la reserva
luego rechaza.
