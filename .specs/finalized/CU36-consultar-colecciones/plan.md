# Plan de Implementación: CU36 - Consultar Colecciones

**Caso de Uso:** CU36 (Consultar colecciones)  
**Paquete:** Catálogo y Exploración (`catalogo`)  
**Alcance:** Bloque 1 (Backend FastAPI), Bloque 2 (Frontend Angular 19+), Bloque 3 (Mobile Flutter 3.x)  
**Estado:** 🟢 Fases 1, 2 y 3 Verificadas y Aprobadas (100% Tests Pasando - Listo para Consolidación Permanente)  

---

## Fases de Ejecución

### Fase 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0)
1. **Modelos:** Verificar y asegurar relaciones en `app/modules/catalogo/modelos.py` (`ColeccionORM`, `TemporadaORM`, `ProveedorORM`, `ProductoORM`).
2. **Esquemas:** Crear `app/modules/catalogo/cu36_colecciones/esquemas.py` con `ColeccionResumenOut`, `ColeccionDetalleOut`, `ProductoColeccionItemOut`, `ColeccionesActivasResponseOut`.
3. **Servicio de Dominio:** Crear `app/modules/catalogo/cu36_colecciones/servicio.py`:
   - Lógica de resolución de temporada activa por fecha y flag.
   - Cálculo de precio de entrada (`precio_desde = MIN(precio_base)`).
   - Conteo de prendas activas y extracción de piezas clave.
   - Consulta de productos por `id_coleccion` con stock y badges.
4. **Router:** Crear `app/modules/catalogo/cu36_colecciones/router.py` y registrar rutas en `app/modules/catalogo/router.py`.
5. **Pruebas:** Crear suite `tests/modules/catalogo/test_cu36_colecciones.py` y ejecutar con `pytest`.

### Fase 2: Frontend Web (`Ec-frontend` - Angular 19+)
1. **Modelos:** Crear `src/app/modules/colecciones/modelos/colecciones.modelos.ts`.
2. **Servicio:** Implementar `ColeccionesService` con Signals reactivos y manejo de errores.
3. **Componente Principal:** Maquetar `ColeccionesComponent` con Hero destacado, grilla de 4 piezas clave y grilla de "Otras colecciones".
4. **Componente de Detalle:** Maquetar `ColeccionDetalleComponent` con listado de prendas y botón volver.
5. **Enrutamiento:** Conectar `/colecciones` y `/colecciones/:id` en `src/app/app.routes.ts` como rutas secundarias fuera de `MainLayoutComponent`, garantizando que no muestren la barra de navegación principal y dispongan del botón funcional `← Volver` hacia `/inicio`.
6. **Pruebas:** Escribir unit tests en `colecciones.component.spec.ts` y validar con `npm test` y `npm run build`.

### Fase 3: Mobile (`Ec-mobile` - Flutter 3.x Multiplataforma)
1. **Capa de Datos:** Crear DTOs (`coleccion_dto.dart`) y datasource HTTP (`colecciones_api.dart`).
2. **BLoC:** Implementar `ColeccionesBloc`, eventos y estados.
3. **Pantalla Principal (`ColeccionesScreen`):** Maquetar chips superiores, piezas clave 2x2 y lista vertical de otras colecciones con botón `VER COLECCIÓN →`, Scaffold sin `bottomNavigationBar` y AppBar con `leading: BackButton()` hacia `Inicio`.
4. **Pantalla de Detalle (`DetalleColeccionScreen`):** Maquetar grilla 2x2 con bookmarks, subtítulos textiles, precios y botón `VER →`, Scaffold sin `bottomNavigationBar` y AppBar con `leading: BackButton()` hacia `ColeccionesScreen`.
5. **Navegación:** Conectar navegación mediante `Navigator.push` desde `PantallaInicio` (Hero CU36) hacia `ColeccionesScreen`.
6. **Pruebas y Linter:** Escribir tests de widgets en `test/colecciones_screen_test.dart`, ejecutar `flutter test` y `flutter analyze`.
