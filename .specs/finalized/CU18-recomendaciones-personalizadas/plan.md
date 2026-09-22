# Plan de Implementación: CU18 - Recomendaciones Personalizadas

**Caso de Uso:** CU18 (Recibir recomendaciones personalizadas con Explicabilidad IA y Stock en Tiempo Real)  
**Paquete:** Catálogo y Exploración (`catalogo`)  
**Alcance Consolidado:** Bloque 1 (Backend FastAPI), Bloque 2 (Frontend Angular 19+), Bloque 3 (Mobile Flutter 3.x Multiplataforma)  
**Estado:** 🟢 Ejecutado y Superado al 100%  

---

## Fases de Ejecución

### Fase I: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + Neon PostgreSQL)
- **Oleada 1: Modelos de Persistencia y Esquemas Pydantic**
  - Mapeo ORM de `RecomendacionIAORM`, `SucursalORM`, `VentaORM`, `VentaDetalleORM` e índices de rendimiento.
  - Esquemas Pydantic estrictos `RecomendacionesPersonalizadasOut`, `ProductoRecomendadoItemOut` y `VarianteRecomendadaOut`.
- **Oleada 2: Motor de Explicabilidad IA y Resiliencia**
  - Servicio `GeminiService` con cliente Google Gemini Flash y algoritmo fallback determinista de alta costura a costo cero.
- **Oleada 3: Servicio de Dominio de Recomendaciones**
  - Lógica en `RecomendacionesService`: consulta de ventas pagadas, exclusión de prendas adquiridas, filtro de existencias en tiempo real (`cantidad_disponible > 0`), derivación de badges/subtítulos textiles y caché en `fashionstore.recomendaciones_ia`.
- **Oleada 4: Enrutamiento y Autenticación Opcional**
  - Implementación de `get_optional_current_user` en `deps.py` y endpoints en `cu18_recomendaciones/router.py`.
- **Oleada 5: Pruebas y Validación**
  - Suite de 10 tests unitarios y de integración (`pytest`) aprobada al 100% (93/93 en suite general).

---

### Fase II: Frontend Web (`Ec-frontend` - Angular 19+ Standalone con Signals)
- **Oleada 6: Modelos y Estado Reactivo**
  - Interfaces TypeScript y `InicioService` con Signals para carga, recomendaciones, motivo, favoritos y bolsa.
- **Oleada 7: Componente de Alta Costura y Enrutamiento**
  - Desarrollo de `InicioComponent` (Hero CU36, grid CU18, Empty State normativo, Experiencia Atelier y Footer corporativo).
  - Enrutamiento lazy en `app.routes.ts` (`/inicio`, `/home`, `/colecciones`).
- **Oleada 8: Pruebas y Compilación**
  - 8/8 tests unitarios pasando en Vitest (57/57 suite general) y build limpio de producción (`ng build`).

---

### Fase III: Mobile (`Ec-mobile` - Flutter 3.x & Dart Multiplataforma)
- **Oleada 9: DTOs y Datasource HTTP**
  - DTOs inmutables y cliente HTTP para `GET /api/v1/catalogo/recomendaciones` con timeouts e inyección de token.
- **Oleada 10: Gestor de Estado y Pantalla Nativa**
  - `InicioBloc` reactivo y `PantallaInicio` con fidelidad exacta a `media_1789982335778.png`: Chip Boutique, Saludo Ana Valenzuela, Hero CU36, carrusel con botón `+ BOLSA`, Empty State oficial y BottomNavigationBar.
- **Oleada 11: Soporte Multiplataforma Web y Enrutamiento**
  - Habilitación de plataforma web (`flutter create . --platforms=web`) para ejecución en Edge (`flutter run -d edge`) y conexión post-login en `main.dart`.
- **Oleada 12: Pruebas y Linter**
  - 6/6 tests de widgets en Flutter pasando al 100% (62/62 suite general) y `flutter analyze` con 0 issues.
