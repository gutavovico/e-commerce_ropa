# Propuesta de Cambio Técnico Consolidada: CU18 - Recomendaciones Personalizadas

**ID del Cambio:** `CU18-recomendaciones-personalizadas`  
**Caso de Uso:** CU18 - Recibir Recomendaciones Personalizadas con Explicabilidad IA y Stock en Tiempo Real  
**Integración:** Vista Principal de Inicio (`/inicio`), CU36 (Consultar Colecciones) y Módulo Recomendado para Ti  
**Paquete de Dominio:** `catalogo` (Catálogo y Exploración)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estado:** 🟢 APROBADO & SUPERADO AL 100% (Promovido a Especificación Permanente)  
**Fecha de Finalización:** 2026-09-21  

---

## Índice de Contenidos
1. [A. Especificación Formal (`spec`)](#a-especificación-formal-spec)
   - [1. Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)](#1-bloque-1-backend-ec-backend---fastapi--sqlalchemy-20--postgresql-neon)
   - [2. Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)](#2-bloque-2-frontend-web-ec-frontend---angular-19-standalone-con-signals)
   - [3. Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)](#3-bloque-3-mobile-multiplataforma-ec-mobile---flutter-3x--dart)
2. [B. Plan de Ejecución Secuencial (`plan`)](#b-plan-de-ejecución-secuencial-plan)
3. [C. Lista de Tareas Atómicas (`tasks`)](#c-lista-de-tareas-atómicas-tasks)
4. [D. Puntos de Control y Verificación (`checkpoints`)](#d-puntos-de-control-y-verificación-checkpoints)

---

## A. Especificación Formal (`spec`)

### 1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

#### 1.1 Propósito y Reglas de Negocio
1. **Afinidad por Compras Históricas Pagadas:**
   - Consulta pedidos pagados (`ventas.estado = 'pagada'`) del cliente autenticado.
   - Analiza categorías y colecciones adquiridas para inferir estilo y patrones de silueta.
   - Excluye del resultado los productos previamente adquiridos (evita recompras innecesarias).
2. **Filtro Estricto de Stock en Tiempo Real:**
   - Solo sugiere prendas activas (`productos.activo = true`) con existencias reales (`inventario_sucursal.cantidad_disponible > 0`).
3. **Manejo de Casos en Frío (Visitantes y Clientes sin Compras):**
   - No genera recomendaciones ficticias. Responde `tiene_historial: false`, `items: []` y el texto normativo exacto:
     *"Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo"*.
4. **Explicabilidad con IA y Resiliencia sin Costo:**
   - Integración con Google Gemini Flash mediante `app/integrations/gemini_service.py`.
   - Motor de fallback determinista estilístico que garantiza costo cero y disponibilidad ante contingencias de cuota o falta de API key.
   - Almacenamiento y caché en `fashionstore.recomendaciones_ia` (`id_cliente`, `id_producto`, `score_relevancia`, `motivo`).

#### 1.2 Modelos de Persistencia (ORM)
- `RecomendacionIAORM`: Mapea `fashionstore.recomendaciones_ia` con claves foráneas e índices.
- `VentaORM` y `VentaDetalleORM`: Mapean transacciones omnicanal con enums `tipo_venta_enum` y `estado_venta_enum`.
- `SucursalORM`: Mapea las boutiques y flagships de la cadena.

#### 1.3 Contratos de API REST
- `GET /api/v1/catalogo/recomendaciones/personalizadas` (y alias `/api/v1/recomendaciones/personalizadas`).
- Autenticación opcional mediante `get_optional_current_user` (soporta navegación pública e identificada).
- Parámetros: `limite` (1 a 12, defecto 6), `id_sucursal` (opcional).

---

### 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)

#### 2.1 Arquitectura y Componentes
- **Patrón:** Standalone Components, Reactividad pura con Angular Signals, TypeScript estricto, estrategia `OnPush`.
- **Ubicación:** `src/app/modules/inicio/`
  - `modelos/inicio.modelos.ts`: Interfaces de contrato tipado.
  - `servicios/inicio.service.ts`: Estado centralizado (`cargando`, `tieneHistorial`, `recomendaciones`, `motivoGeneral`, `cestaCount`, `favoritos`).
  - `paginas/inicio.component.ts|html|scss`: Maquetación editorial de lujo.

#### 2.2 Estructura Visual de la Pantalla de Inicio
1. **Header Sticky:** Logotipo con espaciado editorial, navegación principal con enlace activo en `INICIO` y botones de perfil/cesta.
2. **Barra de Bienvenida Atelier:** Saludo al cliente autenticado (`Bienvenida, Ana Valenzuela`) y chip de boutique habitual `ATELIER HABITUAL: Boutique Serrano (Madrid)`.
3. **Hero Banner Promocional (CU36):** Imagen de fondo en penumbra, tipografía de alta costura, copy sobre patronaje atemporal y botón CTA interactivo `EXPLORAR COLECCIÓN CÁPSULA →` enlazado a `/colecciones` (redirige a `/catalogo`).
4. **Módulo de Recomendaciones (CU18):** Subtítulo dorado `SELECCIÓN A MEDIDA • ATELIER RECOMMENDS`, titular `Recomendado para ti` y botón `Ver catálogo completo →`. Soporta 4 estados:
   - Skeleton Loader durante carga.
   - Grid de tarjetas de producto con badges de lujo, subtítulo textil, precio en EUR y botón `+ Añadir a bolsa`.
   - Empty State sobrio para nuevos visitantes con el copy normativo y CTA `EXPLORAR CATÁLOGO COMPLETO →`.
   - Fallback de error con reintento.
5. **Experiencia Atelier:** 3 tarjetas de garantías exclusivas (Patronaje a medida en Serrano, Entrega con guante blanco y Trazabilidad de tejidos).
6. **Footer Corporativo:** Manifiesto editorial de sostenibilidad y enlaces institucionales.

---

### 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x & Dart)

#### 3.1 Arquitectura y Estado
- **Patrón:** Clean Architecture Feature-First, BLoC reactivo (`InicioBloc`), DTOs inmutables con constructores `const`.
- **Ubicación:** `lib/src/modulos/catalogo/cu18_recomendaciones/`
  - `datos/modelos/recomendacion_item_dto.dart`: DTOs serializables.
  - `datos/datasources/recomendaciones_api.dart`: Cliente HTTP con timeouts y token opcional.
  - `presentacion/bloc/inicio_bloc.dart`: Máquina de estados de la pantalla.
  - `presentacion/pantallas/pantalla_inicio.dart`: Pantalla de inicio con fidelidad visual a `media_1789982335778.png`.

#### 3.2 Componentes de la Pantalla Móvil
- **AppBar:** Identidad de marca `FASHION STORE` (tracking 2.2), icono de notificaciones y avatar circular seguro.
- **Chip Boutique:** `BOUTIQUE SERRANO (MADRID)` con icono `storefront`.
- **Hero Banner:** Tag `• NUEVA TEMPORADA`, titular multilínea, descripción textil y CTA `EXPLORAR COLECCIÓN`.
- **Carrusel de Recomendaciones:** Tarjetas con badges (`EDICIÓN N.º 12/50`, `LANA 100%`), subtítulos (`ALTA COSTURA`, `BIELLA 1850`), precio en euros y botón interactivo `+ BOLSA` con toast flotante.
- **Empty State Normativo:** Contenedor estilizado con icono `auto_awesome` y copy oficial sin recomendaciones falsas.
- **Experiencia Atelier & BottomNav:** Garantías exclusivas y barra de 4 accesos (`Inicio`, `Buscar`, `Catálogo`, `Perfil`).
- **Soporte Multiplataforma Web:** Andamiaje en `Ec-mobile/web/` (`index.html`, `manifest.json`) que permite ejecutar y depurar la app móvil en Microsoft Edge (`flutter run -d edge`).

---

## B. Plan de Ejecución Secuencial (`plan`)

1. **Fase I (Backend):** Modelos ORM -> Dependencias Auth -> Servicio con Explicabilidad IA -> Router FastAPI -> Tests Pytest (10/10).
2. **Fase II (Frontend):** Modelos TypeScript -> Servicio con Signals -> Maquetación InicioComponent -> Rutas -> Tests Vitest (8/8) -> Build producción.
3. **Fase III (Mobile):** DTOs inmutables -> Datasource HTTP -> InicioBloc -> PantallaInicio nativa -> Plataforma web -> Tests Flutter (6/6) -> Flutter Analyze (0 issues).

---

## C. Lista de Tareas Atómicas (`tasks`)

### Bloque 1: Backend
- [x] Tarea 1.1: Mapeo de `RecomendacionIAORM`, `SucursalORM`, `VentaORM`, `VentaDetalleORM` en `modelos.py`.
- [x] Tarea 1.2: Implementación de `get_optional_current_user` en `deps.py`.
- [x] Tarea 1.3: Servicio `GeminiService` con cliente Flash y motor fallback determinista sin costo.
- [x] Tarea 1.4: Esquemas Pydantic `RecomendacionesPersonalizadasOut`, `ProductoRecomendadoItemOut` y `VarianteRecomendadaOut`.
- [x] Tarea 1.5: Lógica en `RecomendacionesService` con exclusión de compras previas y filtro de stock > 0.
- [x] Tarea 1.6: Router FastAPI montado en `/api/v1/catalogo/recomendaciones/personalizadas`.
- [x] Tarea 1.7: Pruebas unitarias e integración en `test_cu18_recomendaciones.py`.
- [x] Tarea 1.8: Verificación exitosa en `pytest` (10/10 CU18, 93/93 suite total).

### Bloque 2: Frontend
- [x] Tarea 2.1: Interfaces TypeScript en `inicio.modelos.ts`.
- [x] Tarea 2.2: Servicio `InicioService` con Signals reactivos.
- [x] Tarea 2.3: Componente Standalone `InicioComponent` (Hero CU36, grid CU18, Empty State, Experiencia Atelier, Footer).
- [x] Tarea 2.4: Rutas `/inicio`, `/home`, `/colecciones` en `app.routes.ts`.
- [x] Tarea 2.5: Pruebas unitarias en `inicio.component.spec.ts` (8/8 pasando) y build de producción limpio.

### Bloque 3: Mobile
- [x] Tarea 3.1: DTOs inmutables en `recomendacion_item_dto.dart`.
- [x] Tarea 3.2: Datasource HTTP en `recomendaciones_api.dart`.
- [x] Tarea 3.3: Gestor de estado `InicioBloc`.
- [x] Tarea 3.4: Pantalla `PantallaInicio` con fidelidad exacta a `media_1789982335778.png`.
- [x] Tarea 3.5: Integración del flujo de navegación tras login en `main.dart`.
- [x] Tarea 3.6: Pruebas de widgets en `pantalla_inicio_test.dart` (6/6 pasando).
- [x] Tarea 3.7: Análisis estático `flutter analyze` (0 issues found) y suite completa `flutter test` (62/62 pasando).
- [x] Tarea 3.8: Soporte multiplataforma web en `Ec-mobile/web/` validado para ejecución en Edge.

---

## D. Puntos de Control y Verificación (`checkpoints`)

| ID | Capa / Módulo | Criterio de Aprobación | Método de Comprobación | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend DB | Modelos ORM `RecomendacionIAORM`, `SucursalORM`, `VentaORM`, `VentaDetalleORM` mapean fielmente las tablas de `fashionstore` con tipos estrictos. | Inspección de modelos y suite de tests ORM. | 🟢 Superado |
| **CP-02** | Backend Auth | `get_optional_current_user` permite solicitudes anónimas sin lanzar 401 y resuelve con token válido sin bloquear vistas públicas. | Tests `test_endpoint_recomendaciones_sin_token_retorna_200_con_empty_state` y con auth. | 🟢 Superado |
| **CP-03** | Backend Negocio | Clientes con compras pagadas reciben prendas afines en stock (`cantidad_disponible > 0`), se excluyen las ya compradas y se calcula el motivo. | Test `test_recomendaciones_cliente_con_compras_recomienda_afines_con_stock`. | 🟢 Superado |
| **CP-04** | Backend Empty State | Visitantes y clientes sin compras reciben `tiene_historial: false` y el texto normativo exacto sin inventar prendas ficticias. | Tests `test_recomendaciones_visitante_anonimo_retorna_empty_state` y cliente nuevo. | 🟢 Superado |
| **CP-05** | Backend Resiliencia | Generador de explicabilidad funciona con Gemini Flash y cuenta con fallback determinista de alta costura a costo cero. | Tests `test_gemini_service_fallback_determinista_seda` y conmutación por error. | 🟢 Superado |
| **CP-06** | Backend Test Suite | Cobertura integral de tests de CU18 pasando al 100% en pytest (10/10 tests de CU18, 93/93 tests totales en backend). | `pytest tests/modules/catalogo/test_cu18_recomendaciones.py -v`. | 🟢 Superado |
| **CP-07** | Frontend Web UX | Renderizado de los 4 estados en `/inicio` (Skeleton, Grid de 3 cards, Empty State sobrio con copy oficial, Error), Hero CU36, Experiencia Atelier y Footer. | Angular Vitest specs en `inicio.component.spec.ts` (8/8 tests pasando, 57/57 suite general). | 🟢 Superado |
| **CP-08** | Frontend Build | Compilación de producción limpia sin advertencias ni valores arbitrarios, generando chunk diferido `inicio-component`. | `npm run build` en `Ec-frontend` exitoso (257 kB bundle inicial, 28 kB lazy chunk). | 🟢 Superado |
| **CP-09** | Mobile Screen UX | `PantallaInicio` en Flutter reproduce fielmente `media_1789982335778.png`: Chip Boutique, Hero CU36, carrusel con badges y botón `+ BOLSA`, Experiencia Atelier y BottomNav. | Inspección visual y tests de widget interactivos en `pantalla_inicio_test.dart`. | 🟢 Superado |
| **CP-10** | Mobile Static Analysis | Código Flutter y Dart estricto, inmutable, sin `unnecessary_underscores` ni colores mágicos fuera de tokens normativos. | `flutter analyze` en `Ec-mobile` (0 issues found). | 🟢 Superado |
| **CP-11** | Mobile Test Suite | Cobertura integral de tests en Flutter pasando al 100% (6/6 tests de inicio, 62/62 tests en la suite completa de la app). | `flutter test` en `Ec-mobile` exitoso. | 🟢 Superado |
| **CP-12** | Mobile Multiplatform | Plataforma web configurada en `Ec-mobile/web/`, permitiendo compilación y depuración en navegador (`flutter run -d edge`) con suite de tests y linter al 100% verde. | `flutter devices`, `flutter analyze` y `flutter test` en `Ec-mobile`. | 🟢 Superado |
