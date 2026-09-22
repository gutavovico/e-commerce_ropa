# Plan de Ejecución Secuencial: CU05 - Consultar Catálogo de Productos

**ID del Cambio:** `CU05-consultar-catalogo`  
**Caso de Uso:** CU05 - Consultar Catálogo de Productos  
**Estrategia:** Desarrollo guiado por especificación (SDD) en 3 fases estrictamente secuenciales (Backend ➔ Frontend Web ➔ Mobile).  
**Gate de Aprobación:** ⛔ Ninguna tarea de desarrollo comenzará hasta recibir la autorización explícita del usuario.

---

## 1. Fase 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 1.1 Objetivos Técnicos
- Crear el módulo `app/modules/catalogo/cu05_consultar_catalogo/` estructurado en capas limpias (`esquemas.py`, `repositorio.py`, `servicio.py`, `router.py`).
- Implementar consultas agregadas sobre `fashionstore.categorias`, `fashionstore.productos`, `fashionstore.variantes_producto`, `fashionstore.inventario_sucursal` y `fashionstore.promociones`.
- Resolver el conteo de prendas activas por categoría para los chips de filtrado.
- Garantizar consultas eficientes sin el problema de N+1 queries mediante `joinedload` y funciones agregadas de PostgreSQL.
- Exponer el endpoint `GET /api/v1/catalogo`.
- Conectar el sub-router en `app/modules/catalogo/router.py`.

### 1.2 Verificación Automatizada (Pytest)
- Crear suite de pruebas en `tests/modules/catalogo/test_cu05_catalogo.py`.
- Pruebas unitarias y de integración para:
  - Carga completa de catálogo con paginación por defecto.
  - Conteo verificado en `resumen_categorias`.
  - Filtrado específico por `categoria_id`.
  - Comprobación de que no se retornan prendas masculinas.
  - Manejo de categoría vacía (código 200 con lista vacía).
  - Cálculo de promociones y descuentos activos.
- Meta de calidad: 100% de tests pasando en `pytest`.

---

## 2. Fase 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

### 2.1 Objetivos Técnicos
- Crear el servicio `CatalogoService` en `src/app/modules/catalogo/servicios/catalogo.service.ts` con llamada tipada a `GET /api/v1/catalogo`.
- Crear el componente standalone `CatalogoComponent` en `src/app/modules/catalogo/cu05_consultar_catalogo/paginas/catalogo.component.ts`.
- Declarar la ruta `/catalogo` dentro de `MainLayoutComponent` en `app.routes.ts`:
  - Garantiza que la barra superior institucional permanezca siempre visible.
  - Sin botón de regreso (`← Volver`), cumpliendo la directriz Hub-and-Spoke.
- Maquetar con Tailwind CSS la vista editorial conforme a la captura de referencia Desktop:
  - Breadcrumbs con badge de sincronización en tiempo real.
  - H1 *"CATÁLOGO DE PRENDAS"* y subtítulo de sastrería.
  - Chips de categorías con contador numérico y activación reactiva mediante Signals.
  - Cuadrícula de 4 columnas (con opción a 2 columnas) con tarjetas de producto de lujo.
  - Badges editoriales, selector de tallas y círculos de colores textiles.
  - Enlace al hacer clic en tarjeta hacia detalle de producto (`/catalogo/:id` o `/productos/:id`).
  - Botón *"Filtrar y Ordenar"* con navegación hacia `/buscar` (CU06).
  - Paginación editorial con barra de progreso y botones numéricos.
  - Bloque editorial de Conserjería Privada de Fitting.

### 2.2 Verificación Automatizada (Vitest / Angular CLI)
- Crear suite en `catalogo.component.spec.ts` y actualizar `catalogo.service.spec.ts`.
- Pruebas para:
  - Renderizado correcto de cabecera y ausencia de botón de regreso.
  - Presencia del Navbar institucional del layout principal.
  - Cambio reactivo de categoría al hacer clic en chips.
  - Conexión del botón *"Filtrar y Ordenar"* hacia `/buscar`.
  - Manejo de estados de carga y empty state.
- Meta de calidad: 100% de tests pasando en `ng test --watch=false` y compilación sin errores (`npm run build`).

---

## 3. Fase 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

### 3.1 Objetivos Técnicos
- Crear DTOs y modelos de datos en `lib/src/modulos/catalogo/cu05_consultar_catalogo/datos/modelos/catalogo_dto.dart`.
- Crear datasource y repositorio HTTP en `lib/src/modulos/catalogo/cu05_consultar_catalogo/datos/`.
- Implementar `CatalogoBloc` con manejo de estados inmutables y eventos reactivos en `presentacion/bloc/`.
- Crear `PantallaCatalogo` en `lib/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart` con fidelidad exacta a la captura móvil:
  - AppBar institucional "Catálogo de Prendas" sin botón de retroceso (`automaticallyImplyLeading: false`).
  - Chips deslizables horizontales con unidades entre paréntesis.
  - Selector de vista en cuadrícula (2 columnas vs lista).
  - Tarjetas de producto en 2 columnas con badges superiores, wishlist, subtítulo de atelier y tallas.
  - Botón expansor *"CARGAR MÁS PRENDAS"* y paginación numerada.
  - Sello artesanal de Atelier al pie.
- Integrar `PantallaCatalogo` en el **Índice 2 (`Catálogo`)** de [`PantallaPrincipalHub`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/navegacion/pantalla_principal_hub.dart), reemplazando el placeholder en blanco.
- Asegurar que la barra de navegación inferior permanezca visible y la navegación entre Inicio, Buscar, Catálogo y Perfil sea 100% fluida.

### 3.2 Verificación Automatizada (Flutter Test & Flutter Analyze)
- Crear suite en `test/pantalla_catalogo_test.dart` y `test/catalogo_bloc_test.dart`.
- Pruebas para:
  - Renderizado de los elementos clave de la captura móvil.
  - Ausencia de botón de regreso en la AppBar.
  - Interacción con chips de categorías y carga de productos.
  - Cero incidencias en `flutter analyze`.
- Meta de calidad: 100% de tests pasando en `flutter test`.
