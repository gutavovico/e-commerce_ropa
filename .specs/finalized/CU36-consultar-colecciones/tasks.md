# Tareas de Implementación: CU36 - Consultar Colecciones

**Caso de Uso:** CU36 (Consultar colecciones)  
**Estado:** 🟢 100% Completado (Bloques 1, 2 y 3 Verificados y Probados - Pendiente de Autorización de Consolidación)  

---

## Lista de Tareas Atómicas

### Bloque 1: Backend (`Ec-backend`)
- [x] **Tarea 1.1**: Verificar mapeo de `ProveedorORM` y relaciones de `ColeccionORM` con `TemporadaORM` y `ProductoORM` en `app/modules/catalogo/modelos.py`.
- [x] **Tarea 1.2**: Crear esquemas Pydantic `ColeccionResumenOut`, `ColeccionDetalleOut`, `ProductoColeccionItemOut` y `ColeccionesActivasResponseOut` en `app/modules/catalogo/cu36_colecciones/esquemas.py`.
- [x] **Tarea 1.3**: Implementar `ColeccionesService` en `app/modules/catalogo/cu36_colecciones/servicio.py` con cálculo de `precio_desde`, filtro de temporada activa y piezas clave.
- [x] **Tarea 1.4**: Implementar endpoints `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id_coleccion}/productos` en `app/modules/catalogo/cu36_colecciones/router.py`.
- [x] **Tarea 1.5**: Montar el router en `app/modules/catalogo/router.py`.
- [x] **Tarea 1.6**: Escribir pruebas unitarias e integración en `tests/modules/catalogo/test_cu36_colecciones.py` cubriendo todos los escenarios Gherkin.
- [x] **Tarea 1.7**: Ejecutar `pytest` y asegurar 100% de tests pasando en backend (100/100 tests totales).

### Bloque 2: Frontend Web (`Ec-frontend`)
- [x] **Tarea 2.1**: Definir interfaces TypeScript en `src/app/modules/colecciones/modelos/colecciones.modelos.ts`.
- [x] **Tarea 2.2**: Implementar `ColeccionesService` en `src/app/modules/colecciones/servicios/colecciones.service.ts` con Signals reactivos.
- [x] **Tarea 2.3**: Desarrollar componente Standalone `ColeccionesComponent` (vista principal con colección destacada y grilla editorial de otras colecciones).
- [x] **Tarea 2.4**: Desarrollar componente Standalone `ColeccionDetalleComponent` (vista de prendas exclusivas de la colección seleccionada con botón volver y cards con enlace a `/catalogo/:id`).
- [x] **Tarea 2.5**: Configurar rutas en `src/app/app.routes.ts` (`/colecciones` y `/colecciones/:id`) y vincular botón Hero de `/inicio`.
- [x] **Tarea 2.6**: Escribir pruebas unitarias en `colecciones.component.spec.ts` y validar `npm test` (74/74 tests) y `npm run build` (0 errores).
- [x] **Tarea 2.7**: Garantizar que el frontend consuma estrictamente los productos desde PostgreSQL (`fashionstore.productos`) sin quemar productos ficticios.
- [x] **Tarea 2.8**: Sustituir todas las imágenes de hombres por fotografía editorial de moda femenina exclusiva en todas las colecciones y cards.
- [x] **Tarea 2.9**: Registrar la regla global inquebrantable de "E-commerce Exclusivo para Mujeres" en la constitución del backend, frontend, mobile y especificaciones.
- [x] **Tarea 2.10**: Hacer toda la tarjeta de "Otras colecciones" cliqueable como botón para navegación intuitiva (`(click)="irAColeccion(col)"`, accesibilidad `role="button"`, `tabindex="0"` y teclado).
- [x] **Tarea 2.11**: Reemplazar URL rota de portada en Colección 2 y productos 13/9 por URLs Unsplash verificadas HTTP 200 e implementar manejador `onImgError`.
- [x] **Tarea 2.12**: Registrar alineación arquitectónica de `ColeccionesComponent` y `ColeccionDetalleComponent` como Pantallas Secundarias (Hojas), fuera de `MainLayoutComponent`, sin barra de navegación principal y con botón funcional obligatorio `← Volver` hacia `/inicio`.

### Bloque 3: Mobile (`Ec-mobile`)
- [x] **Tarea 3.1**: Crear DTOs inmutables en `lib/src/modulos/catalogo/cu36_consultar_colecciones/datos/modelos/coleccion_dto.dart` (`ColeccionResumenDto`, `ColeccionDetalleDto`, `ProductoColeccionItemDto`, `ColeccionesActivasResponseDto`).
- [x] **Tarea 3.2**: Implementar datasource HTTP en `lib/src/modulos/catalogo/cu36_consultar_colecciones/datos/datasources/colecciones_api.dart` con manejo robusto de excepciones de red y decodificación UTF-8.
- [x] **Tarea 3.3**: Implementar `ColeccionesBloc` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/bloc/colecciones_bloc.dart` con arquitectura sellada y ChangeNotifier reactivo.
- [x] **Tarea 3.4**: Maquetar `ColeccionesScreen` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/colecciones_screen.dart` reproduciendo fielmente `image_45cf27.png` (chips interactivos, 4 piezas clave 2x2, tarjetas de otras colecciones navegables).
- [x] **Tarea 3.5**: Maquetar `DetalleColeccionScreen` en `lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/detalle_coleccion_screen.dart` reproduciendo fielmente `image_45cbbe.png` (grilla 2x2, bookmarks, swatches de color y empty state editorial).
- [x] **Tarea 3.6**: Conectar navegación entre `ColeccionesScreen` y `DetalleColeccionScreen` mediante el botón `VER COLECCIÓN →` y enlazar callback `alIrAColecciones` en `PantallaInicio` y `main.dart`.
- [x] **Tarea 3.7**: Escribir pruebas de BLoC en `test/colecciones_bloc_test.dart` (7 tests) y pruebas de widgets en `test/colecciones_screen_test.dart` (5 tests).
- [x] **Tarea 3.8**: Ejecutar `flutter analyze` (0 issues encontrados) y `flutter test` (74/74 tests pasando).
- [x] **Tarea 3.9**: Resolver advertencias de renderizado móvil (`RenderFlex overflowed` en badges y titulares mediante `Flexible` y `childAspectRatio` calibrado a 0.49/0.52).
- [x] **Tarea 3.10**: Corregir notificación de estado durante el ciclo de build de Flutter mediante `addPostFrameCallback`.
- [x] **Tarea 3.11**: Blindar deserialización de DTOs en Flutter (`coleccion_dto.dart`) ante campos `Decimal` de Pydantic serializados como `String` (`"310.00"` y `"890.00"`), previniendo `TypeError: type 'String' is not a subtype of type 'num?'`.
- [x] **Tarea 3.12**: Calibrar proporción geométrica de tarjetas en grillas (`childAspectRatio: 0.65`) y contenedor de foto elástico (`Expanded` con `Positioned.fill` y `ClipRRect`), eliminando por completo el espacio en blanco vacío bajo las etiquetas de precio y botones.
- [x] **Tarea 3.13**: Unificar tipografía con el Design System normativo (`Outfit`, escala `fashionstore-tokens.md`) en `main.dart`, `ColeccionesScreen` y `DetalleColeccionScreen`, aplicando tracking `label-caps` (`letterSpacing: 0.8` a `1.1`), pesos `FontWeight.w600` / `w700` y colores semánticos (`primary-900: #0F1116`, `secondary-500: #AD8C63`, `neutral-500: #71717A`).
- [x] **Tarea 3.14**: Blindar la jerarquía de navegación móvil Hub-and-Spoke: asegurar que `ColeccionesScreen` y `DetalleColeccionScreen` se ejecuten en Scaffolds independientes sin `bottomNavigationBar` y con `leading: BackButton()` activo hacia `Inicio`.


