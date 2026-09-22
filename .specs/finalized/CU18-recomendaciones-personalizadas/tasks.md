# Tareas de Implementación: CU18 - Recomendaciones Personalizadas

**Caso de Uso:** CU18 (Recibir Recomendaciones Personalizadas con Explicabilidad IA y Stock en Tiempo Real)  
**Integración:** Vista de Inicio (`/inicio`), CU36 (Consultar Colecciones) y CU18  
**Estado:** 🟢 Completado al 100% (Bloque 1: Backend, Bloque 2: Frontend & Bloque 3: Mobile)  

---

## Desglose Granular de Tareas

### Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0)
- [x] **Tarea 1.1**: Mapear `RecomendacionIAORM`, `SucursalORM`, `VentaORM` y `VentaDetalleORM` en `Ec-backend/app/modules/catalogo/modelos.py` con fidelidad al esquema `fashionstore` e índices de rendimiento.
- [x] **Tarea 1.2**: Implementar `get_optional_current_user` en `Ec-backend/app/core/deps.py` para permitir navegación fluida a visitantes y clientes sin token obligatorio.
- [x] **Tarea 1.3**: Implementar `GeminiService` en `Ec-backend/app/integrations/gemini_service.py` con integración a Google Gemini Flash y motor fallback determinista de alta costura a costo cero.
- [x] **Tarea 1.4**: Definir esquemas Pydantic `RecomendacionesPersonalizadasOut`, `ProductoRecomendadoItemOut` y `VarianteRecomendadaOut` en `Ec-backend/app/modules/catalogo/cu18_recomendaciones/esquemas.py`.
- [x] **Tarea 1.5**: Desarrollar la lógica de negocio en `Ec-backend/app/modules/catalogo/cu18_recomendaciones/servicio.py` (consulta de ventas pagadas, exclusión de prendas compradas, filtro de stock > 0, derivación de badges/subtítulos y caché de scores).
- [x] **Tarea 1.6**: Implementar `router.py` en `Ec-backend/app/modules/catalogo/cu18_recomendaciones/router.py` y montarlo en `app/modules/catalogo/router.py`.
- [x] **Tarea 1.7**: Escribir pruebas unitarias e integración en `Ec-backend/tests/modules/catalogo/test_cu18_recomendaciones.py`.
- [x] **Tarea 1.8**: Ejecutar `pytest` y verificar que todos los casos de prueba pasen al 100% (10/10 tests de CU18 pasando, 93/93 suite completa).

---

### Bloque 2: Frontend (`Ec-frontend` - Angular 19+ Standalone con Signals)
- [x] **Tarea 2.1**: Crear interfaces TypeScript y DTOs en `src/app/modules/inicio/modelos/inicio.modelos.ts`.
- [x] **Tarea 2.2**: Implementar `InicioService` en `src/app/modules/inicio/servicios/inicio.service.ts` con manejo reactivo de estados (`cargando`, `tieneHistorial`, `recomendaciones`, `motivoGeneral`, `boutiqueReferencia`, `cestaCount`, `favoritos`).
- [x] **Tarea 2.3**: Desarrollar componente Standalone `InicioComponent` en `src/app/modules/inicio/paginas/` (`inicio.component.ts`, `inicio.component.html`, `inicio.component.scss`) con:
  - Header superior de navegación con enlace activo en `INICIO`.
  - Barra de bienvenida al cliente (`Bienvenida, Ana Valenzuela`) y chip `ATELIER HABITUAL: Boutique Serrano (Madrid)`.
  - Banner Hero editorial con CTA interactivo hacia colecciones (CU36: `EXPLORAR COLECCIÓN CÁPSULA →`).
  - Módulo de recomendaciones CU18 con los 4 estados (Skeleton loader, Grid de cards con tags, Empty State con copy normativo y Fallback de error).
  - Módulo "Experiencia Atelier" con las 3 tarjetas de garantías exclusivas.
  - Footer editorial corporativo FASHION STORE.
- [x] **Tarea 2.4**: Configurar enrutamiento en `src/app/app.routes.ts` conectando `/inicio` a `InicioComponent` y alias `/home` -> `/inicio`. *(Reconciliado 2026-09-21: `/colecciones` no es un redirect a `/catalogo`; CU36 la declara como ruta secundaria propia con su `ColeccionesComponent` y su detalle `/colecciones/:id`, fuera de `MainLayoutComponent`.)*
- [x] **Tarea 2.5**: Escribir pruebas unitarias en `src/app/modules/inicio/paginas/inicio.component.spec.ts` y validar `npm test` (57/57 tests pasando) y `npm run build` (0 errores).

---

### Bloque 3: Mobile (`Ec-mobile` - Flutter 3.x & Dart)
- [x] **Tarea 3.1**: Definir DTOs inmutables con deserialización JSON robusta en `lib/src/modulos/catalogo/cu18_recomendaciones/datos/modelos/recomendacion_item_dto.dart` (`ProductoRecomendadoDto`, `VarianteRecomendadaDto`, `RecomendacionesResponseDto`).
- [x] **Tarea 3.2**: Implementar datasource HTTP en `lib/src/modulos/catalogo/cu18_recomendaciones/datos/datasources/recomendaciones_api.dart` consumiendo `GET /api/v1/catalogo/recomendaciones` con timeouts e inyección opcional de `access_token`.
- [x] **Tarea 3.3**: Crear gestor de estado `InicioBloc` en `lib/src/modulos/catalogo/cu18_recomendaciones/presentacion/bloc/inicio_bloc.dart` con soporte para ciclo de vida de carga, filtrado, favoritos, adición a cesta y notificación toast flotante.
- [x] **Tarea 3.4**: Maquetar `PantallaInicio` en `lib/src/modulos/catalogo/cu18_recomendaciones/presentacion/pantallas/pantalla_inicio.dart` con fidelidad exacta a la captura `media_1789982335778.png`:
  - AppBar con tipografía `FASHION STORE` (tracking 2.2), icono de notificaciones y avatar circular.
  - Chip redondeado `BOUTIQUE SERRANO (MADRID)` con icono `storefront` e indicador de ubicación.
  - Saludo `BIENVENIDA DE NUEVO`, `Ana Valenzuela` y copy editorial de silueta y estilo.
  - Hero Banner editorial con tag `• NUEVA TEMPORADA`, titular multilínea, descripción y CTA interactivo `EXPLORAR COLECCIÓN →`.
  - Sección `Recomendado para ti` con subtítulo `SELECCIÓN A MEDIDA • ATELIER RECOMMENDS` y enlace `Ver catálogo →`.
  - Carrusel horizontal de tarjetas de prendas de lujo con fotografía recortada, badge editorial, subtítulo atelier, categoría, precio en euros y botón de acción directa `+ BOLSA`.
  - Empty State normativo con contenedor marfil/dorado, icono `auto_awesome` y copy oficial para usuarios sin compras previas.
  - Sección "Experiencia Atelier" con tarjetas de patronaje a medida y entrega con guante blanco.
  - Barra de navegación inferior `BottomNavigationBar` con iconos para `Inicio`, `Buscar`, `Catálogo` y `Perfil`.
- [x] **Tarea 3.5**: Integrar `PantallaInicio` en el flujo de arranque de `lib/main.dart` conectando la navegación tras login hacia Inicio, Búsqueda y Perfil.
- [x] **Tarea 3.6**: Escribir pruebas de widgets en `test/pantalla_inicio_test.dart` validando todos los componentes y flujos de usuario (6/6 tests pasando).
- [x] **Tarea 3.7**: Ejecutar `flutter analyze` (0 errores, 0 warnings) y la suite completa `flutter test` (62/62 tests pasando al 100%).
- [x] **Tarea 3.8**: Habilitar soporte de plataforma web en `Ec-mobile` (`flutter create . --platforms=web`), generar `web/index.html` y `web/manifest.json`, y verificar targets con `flutter devices` para permitir ejecución en Edge (`flutter run -d edge`).
