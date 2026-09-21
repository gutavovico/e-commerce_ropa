# Lista de Tareas Atómicas: CU05 - Consultar Catálogo de Productos

**ID del Cambio:** `CU05-consultar-catalogo`  
**Metodología:** Spec-Driven Development (SDD)  
**Estado:** 🟡 Pendiente de Aprobación para Inicio de Desarrollo

---

## 1. Tareas de Backend (`Ec-backend` - FastAPI + SQLAlchemy)

- [x] **T-BE-01**: Crear directorio de caso de uso `app/modules/catalogo/cu05_consultar_catalogo/` con `__init__.py`.
- [x] **T-BE-02**: Implementar esquemas Pydantic en `esquemas.py`:
  - [x] `ColorItemOut` (`id_color`, `nombre`, `codigo_hex`).
  - [x] `CategoriaResumenOut` (`id_categoria`, `nombre`, `total_prendas`).
  - [x] `ProductoCatalogoOut` (`id_producto`, `nombre`, `precio_base`, `precio_final`, `etiqueta_badge`, `subtitulo_atelier`, `tallas_disponibles`, `colores_disponibles`, `tiene_stock`).
  - [x] `CatalogoOut` con paginación, metadatos y resumen de categorías.
- [x] **T-BE-03**: Implementar repositorio de catálogo en `repositorio.py`:
  - [x] Consulta agregada para resumen de categorías con conteo de prendas activas.
  - [x] Consulta paginada de productos activos con filtro opcional por `categoria_id` y ordenación.
  - [x] Precarga optimizada con `joinedload`/`selectinload` de tallas, colores e inventarios para evitar N+1 queries.
- [x] **T-BE-04**: Implementar servicio de catálogo en `servicio.py`:
  - [x] Lógica de negocio para aplicar promociones y descuentos activos (`precio_final`).
  - [x] Enriquecimiento editorial de subtítulos y badges de atelier.
  - [x] Cálculo de metadatos de paginación (`total_paginas`, `tiene_siguiente`, `tiene_anterior`).
- [x] **T-BE-05**: Implementar router HTTP en `router.py`:
  - [x] Endpoint `GET /api/v1/catalogo` con parámetros `categoria_id`, `ordenar_por`, `pagina` y `limite`.
- [x] **T-BE-06**: Integrar sub-router de CU05 en `app/modules/catalogo/router.py`.
- [x] **T-BE-07**: Escribir suite de pruebas Pytest en `tests/modules/catalogo/test_cu05_catalogo.py`:
  - [x] Test de carga inicial con paginación por defecto.
  - [x] Test de filtrado por categoría.
  - [x] Test de cálculo de resumen de categorías.
  - [x] Test de empty state con categoría sin prendas.
- [x] **T-BE-08**: Ejecutar `pytest` y asegurar 100% de tests en verde (107/107 pruebas pasando).

---

## 2. Tareas de Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- [x] **T-FE-01**: Crear modelos de catálogo en `src/app/modules/catalogo/cu05_consultar_catalogo/modelos/catalogo.model.ts`.
- [x] **T-FE-02**: Actualizar/crear `CatalogoService` en `src/app/modules/catalogo/servicios/catalogo.service.ts` para consumir `GET /api/v1/catalogo`.
- [x] **T-FE-03**: Crear componente standalone `CatalogoComponent` en `src/app/modules/catalogo/cu05_consultar_catalogo/paginas/catalogo.component.ts`.
- [x] **T-FE-04**: Configurar Signals de estado reactivo en `CatalogoComponent`:
  - [x] `categoriaSeleccionada`, `productos`, `resumenCategorias`, `paginaActual`, `totalArticulos`, `cargando`.
- [x] **T-FE-05**: Diseñar plantilla HTML con Tailwind CSS según la captura de referencia Desktop:
  - [x] Breadcrumbs con badge de sincronización en tiempo real.
  - [x] Cabecera editorial "CATÁLOGO DE PRENDAS" con subtítulo y sello artesanal.
  - [x] Fila de chips de categorías con contador de prendas ("TODOS LOS PRODUCTOS (20)", etc.).
  - [x] Botón "Filtrar y Ordenar" con navegación a `/buscar`.
  - [x] Selector de vista de cuadrícula (4 columnas vs 2 columnas).
  - [x] Grilla de 4 columnas con tarjetas de prendas, badges de atelier, tallas, dots de color y botón de wishlist.
  - [x] Paginación editorial con barra de progreso y botones numéricos.
  - [x] Bloque editorial de Conserjería Privada de Tallas & Fitting con botón CTA.
- [x] **T-FE-06**: Declarar la ruta `/catalogo` dentro de `MainLayoutComponent` en `app.routes.ts`:
  - [x] Navbar superior persistente visible y destacando la pestaña Catálogo.
  - [x] Sin botón de regreso (`← Volver`), cumpliendo la directriz Hub-and-Spoke.
- [x] **T-FE-07**: Escribir pruebas unitarias en `catalogo.component.spec.ts`:
  - [x] Test de renderizado de cabecera y chips.
  - [x] Test de interacción al pulsar chips de categorías.
  - [x] Test de navegación a `/buscar` y wishlist.
- [x] **T-FE-08**: Ejecutar `npm test` y `npm run build` garantizando 0 errores (86/86 pruebas unitarias pasando y build de producción exitoso).

---

## 3. Tareas de Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x)

- [x] **T-MO-01**: Crear DTOs y modelos de datos en `lib/src/modulos/catalogo/cu05_consultar_catalogo/datos/modelos/catalogo_dto.dart`.
- [x] **T-MO-02**: Crear cliente HTTP / Datasource y repositorio en `lib/src/modulos/catalogo/cu05_consultar_catalogo/datos/`.
- [x] **T-MO-03**: Implementar `CatalogoBloc`, `CatalogoEstado` y `CatalogoEvento` en `presentacion/bloc/`:
  - [x] Manejo de eventos de carga, filtrado por chip, conmutación de vista y paginación.
  - [x] Deserialización robusta y tolerante de precios numéricos y `Decimal`.
- [x] **T-MO-04**: Crear `PantallaCatalogo` en `presentacion/pantallas/pantalla_catalogo.dart`:
  - [x] AppBar institucional "Catálogo de Prendas" con `automaticallyImplyLeading: false`.
  - [x] Carrusel horizontal de chips de categorías con unidades ("Todos (24)", etc.).
  - [x] Controles de vista y botón "Filtrar y Ordenar" hacia la pestaña de búsqueda.
  - [x] `GridView` de 2 columnas con tarjetas de lujo, badges superiores, wishlist y tallas.
  - [x] Botón expansor "CARGAR MÁS PRENDAS (18) ⌵" y paginación numerada.
  - [x] Sello editorial inferior "ATELIER FLAGSHIP MADRID · PARÍS".
- [x] **T-MO-05**: Integrar `PantallaCatalogo` en el **Índice 2 (`Catálogo`)** de `PantallaPrincipalHub`, sustituyendo el placeholder en blanco.
- [x] **T-MO-06**: Escribir tests de widgets y BLoC en `test/pantalla_catalogo_test.dart`.
- [x] **T-MO-07**: Ejecutar `flutter analyze` y `flutter test` garantizando 100% de aprobación.
