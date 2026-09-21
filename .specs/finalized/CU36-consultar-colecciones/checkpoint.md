# Puntos de Control y Verificación: CU36 - Consultar Colecciones

**ID del Cambio:** `CU36-consultar-colecciones`  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estado General:** 🟢 100% Superado en los 3 Bloques (Backend, Frontend Web y Mobile) - Listo para Autorización y Consolidación  

---

## Matriz de Puntos de Control (Checkpoints)

| ID | Capa / Módulo | Criterio de Aprobación | Método de Comprobación | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend DB | Consultas SQL de temporada activa resuelven correctamente por rango de fechas (`CURRENT_DATE`) y fallback a `activa = true`. | Test unitario con sesión de prueba en Neon DB / SQLite. | 🟢 Superado |
| **CP-02** | Backend Cálculo | Cada colección calcula correctamente `precio_desde` (`MIN(precio_base)`) y `total_prendas` considerando solo prendas activas. | Test de aserción en `test_cu36_colecciones.py`. | 🟢 Superado |
| **CP-03** | Backend Endpoints | `GET /api/v1/colecciones/activas` y `GET /api/v1/colecciones/{id}/productos` retornan códigos 200/404 según contratos Pydantic. | Ejecución de suite `pytest` en `Ec-backend` (100/100 tests pasando). | 🟢 Superado |
| **CP-04** | Frontend Web Hero | La vista `/colecciones` muestra la Colección Destacada con sus 4 piezas clave, badges y tipografía editorial de alta costura. | Tests unitarios `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-05** | Frontend Web Grilla | La sección "Otras colecciones" renderiza las cards con badge de edición, temporada, precio de entrada y botón `VER COLECCIÓN →`. | Tests unitarios `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-06** | Frontend Web Navegación | Al pulsar `VER COLECCIÓN →`, navega a `/colecciones/:id` listando las prendas de dicha colección con enlace a `/catalogo/:id`. | Tests unitarios `coleccion-detalle.component.spec.ts` y enrutador. | 🟢 Superado |
| **CP-07** | Frontend Build | Compilación de producción limpia sin errores TypeScript ni estilos rotos. | `npm run build` en `Ec-frontend` (0 errores). | 🟢 Superado |
| **CP-08** | Mobile Screen | `ColeccionesScreen` reproduce `image_45cf27.png`: Chips de filtro, piezas clave 2x2 y lista vertical de otras colecciones con `VER COLECCIÓN →`. | Test de widgets en Flutter con physicalSize móvil en `colecciones_screen_test.dart`. | 🟢 Superado |
| **CP-09** | Mobile Detalle | `DetalleColeccionScreen` reproduce `image_45cbbe.png`: Grilla 2x2 de prendas con bookmark, precio en EUR y botón `VER →`. | Test de interacción en Flutter en `colecciones_screen_test.dart`. | 🟢 Superado |
| **CP-10** | Mobile Static Analysis | Código Flutter estricto, inmutable, sin `unnecessary_underscores` y conforme a tokens normativos. | `flutter analyze` en `Ec-mobile` (0 issues). | 🟢 Superado |
| **CP-11** | Mobile Test Suite | Suite completa de tests en Flutter pasando al 100% sin regresiones (74/74 tests totales, 12 de CU36). | `flutter test` en `Ec-mobile`. | 🟢 Superado |
| **CP-12** | Global E-commerce Femenino | Cero imágenes de hombres; 100% prendas y modelos de moda femenina exclusiva en todas las vistas y fallbacks. | Inspección visual y validación de assets en BD y código. | 🟢 Superado |
| **CP-13** | Integridad de BD Real | Todas las prendas provienen estrictamente de `fashionstore.productos` (20 prendas reales con inventario). Cero productos ficticios en cliente. | Consulta directa a API `/api/v1/colecciones/activas` y base Neon. | 🟢 Superado |
| **CP-14** | Card Cliqueable como Botón | Toda la card de "Otras colecciones" funciona como botón interactivo completo, navegando a `/colecciones/:id` al hacer click. | Test unitario en `colecciones.component.spec.ts`. | 🟢 Superado |
| **CP-15** | Carga de Imágenes HTTP 200 | Todas las imágenes de colecciones y prendas en Neon responden HTTP 200 sin links rotos, más fallback reactivo `onImgError`. | Verificación por script HTTP y suite frontend. | 🟢 Superado |
| **CP-16** | Responsive & Overflow Safety | Grillas y tarjetas en Flutter calibradas con `childAspectRatio: 0.65` y foto elástica en `Expanded` con `Positioned.fill`, eliminando el vacío blanco interior y previniendo `RenderFlex overflowed`. | Validación visual y suite de tests de widgets. | 🟢 Superado |
| **CP-17** | Serialización Decimal API | Deserialización tolerante de precios monetarios (`double.tryParse`) soportando tipos primitivos `num` y cadenas `Decimal` (`"310.00"`) de FastAPI Pydantic sin `TypeError`. | Test unitario en `colecciones_bloc_test.dart` y verificación en runtime. | 🟢 Superado |
| **CP-18** | Tipografía Design System (Outfit) | Unificación tipográfica global y atómica en Flutter bajo la familia `Outfit`, tracking normativo de badges (`letterSpacing: 0.8-1.1`), pesos `FontWeight.w600/w700` y paleta Obsidian/Camel de `fashionstore-tokens.md`. | Verificación visual y pruebas de widgets en `colecciones_screen_test.dart`. | 🟢 Superado |
| **CP-19** | Jerarquía Navegación Hub-and-Spoke | `CU36` (`Colecciones` y `DetalleColeccion`) clasificada como Pantalla Secundaria (Hoja/Spoke): barra de navegación oculta/no disponible en Web y Mobile, y botón funcional obligatorio de retroceso (`← Volver` / `leading: BackButton()`) hacia `Inicio` / pantalla previa. | Inspección arquitectónica de especificación, layouts y Scaffolds. | 🟢 Superado |


