# Puntos de Control y Verificación: CU06 - Buscar y Filtrar Productos

**ID del Cambio:** `CU06-buscar-filtrar-productos`  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estado General:** 🟢 Todos los Puntos de Control Superados al 100%  

---

## Matriz de Puntos de Control (Checkpoints)

| ID | Capa / Módulo | Criterio de Aprobación | Método de Comprobación | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend API | Búsqueda morfológica/semántica por palabras sueltas (`q` con singular/plural, sinónimos y sin tildes sobre nombre, categoría, colección, color y descripción), reconocimiento de categorías completas ("vestidos", "chaquetas", etc.), filtros 100% opcionales y corrección de color a Rojo Carmín en "Vestido plisado seda". | `pytest tests/modules/catalogo/test_cu06_buscar_filtrar.py` (100% pasando: 20/20 tests de catálogo, 83/83 suite completa). | 🟢 Superado |
| **CP-02** | Backend Validación | Parámetros inválidos (`precio_min > precio_max`, `pagina < 1`) devuelven `422 Unprocessable Entity` sin excepción interna 500. | Tests específicos de Pydantic y cliente de prueba FastAPI. | 🟢 Superado |
| **CP-03** | Frontend Web UX | Búsqueda con confirmación explícita (`BUSCAR` y tecla Enter) con vaciado automático de input, filtros diferidos en borrador hasta confirmar, tipografía Outfit del Design System en 'Visto recientemente', paleta textil de 16 colores y alineación pixel-perfect de la barra superior/avatar entre `/buscar` y `/perfil` sin saltos ni diferencias tipográficas. | Angular Vitest specs `buscar-productos.component.spec.ts` y `perfil.component.spec.ts` (41/41 tests pasando). | 🟢 Superado |
| **CP-04** | Frontend URL State | Persistencia del estado en Query Params: recargar la página o navegar restaura exactamente los filtros y la grilla. | Pruebas de integración con `ActivatedRoute.queryParams` y llamadas HTTP comprobadas. | 🟢 Superado |
| **CP-05** | Frontend Build | Generación limpia de bundle de producción sin advertencias de dependencias ni fallos de compilación. | `npm run build` en `Ec-frontend` exitoso (0 errores, chunk perezoso generado). | 🟢 Superado |
| **CP-06** | Mobile BLoC & UI | Flujo de eventos reactivos en `CatalogoBloc`, visualización de 2 columnas en `GridView`, filtros diferidos con confirmación `BUSCAR`/Enter, limpieza de input, y soporte para BottomSheet de filtros avanzados. | `flutter test` en `Ec-mobile` (100% pasando: 56/56 tests, 14 nuevos de CU06). | 🟢 Superado |
| **CP-07** | Mobile Linter | Análisis estático sin incidencias ni problemas de tipado o accesibilidad. | `flutter analyze` reporta 0 issues (No issues found). | 🟢 Superado |
| **CP-08** | Fidelidad Visual | Coincidencia estética de alta costura, tipografías Outfit, badges (`EDICIÓN LIMITADA`, `EN SERRANO`), 16 colores textiles, botones `+ CESTA` y favoritos contra las capturas de referencia. | Revisión visual comparativa pixel a pixel en Web y Mobile y fidelidad al Design System. | 🟢 Superado |
