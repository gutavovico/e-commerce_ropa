# Puntos de Control y Verificación: CU04 - Gestionar Perfil del Cliente

**Caso de Uso:** CU04. Gestionar Perfil del Cliente  
**Fase:** Implementación y Verificación Completa de Bloques 1, 2 y 3  
**Fecha:** 2026-09-19  
**Estado:** 🟢 Bloques 1, 2 y 3 Completados, Verificados y Promovidos a Baseline  

---

## 1. Criterios de Aceptación Cuantitativos para Promoción a Baseline

El caso de uso `CU04` superó con éxito todos los gates de calidad requeridos para su promoción definitiva a baseline permanente:

### 1.1 Calidad en Backend (`Ec-backend`)
- [x] **Suite de Pruebas Automatizadas:** 100% de tests en verde en `pytest` para toda la suite acumulada (45/45 pruebas pasando: 28 existentes + 17 nuevas de `CU04`).
- [x] **Cobertura de Casos de Error:** Verificación explícita de códigos de respuesta HTTP `200 OK`, `401 Unauthorized` (token expirado/inexistente), `403 Forbidden` (cuenta inactiva o rol no cliente), y `422 Unprocessable Entity` (talla inválida).
- [x] **Persistencia en Neon Serverless:** Verificación en vivo de actualización atómica en las tablas `fashionstore.usuarios` y `fashionstore.clientes` (`#0005`, `Claire Victoria`, `talla_preferida='S'`).
- [x] **Seguridad Criptográfica:** Garantía de que la identidad del cliente provenga exclusivamente de las claims del token JWT verificado con `JWT_SECRET`.
- [x] **Configuración de Vida del Token:** Ampliación a 1440 minutos en desarrollo para prevenir deslogueos silenciosos (`app/core/config.py`).

### 1.2 Fidelidad Visual y Calidad en Frontend Web (`Ec-frontend`)
- [x] **Pixel-Match Editorial:** Correspondencia visual estricta con el mockup desktop (`media_1789842823031.png`):
  - Cabecera institucional con navegación activa en `PERFIL`.
  - Tarjeta de cliente con avatar, badge de cámara, número de socio `#8402` y botón `EDITAR INFORMACIÓN`.
  - Matriz de 4 estadísticas de atelier y accesos rápidos a Wishlist y Bolsa.
  - Layout dividido: Pedidos históricos y Preferencias/Servicios.
  - Formulario modal de actualización con validaciones reactivas y mensajes de feedback.
  - Botón de cierre de sesión seguro funcional.
  - Selector de género eliminado por regla de negocio de marca.
- [x] **Compilación Limpia:** Compilación de producción con Angular CLI (`npm run build`) en 0 errores y 0 advertencias de tipos (chunk `perfil-component` 34.54 kB).
- [x] **Manejo de Sesión y Reactividad:** Refresco inmediato bajo OnPush con `ChangeDetectorRef.markForCheck()` y sincronización persistente de sesión en `sessionStorage` y `localStorage`.

### 1.3 Fidelidad Visual y Calidad en Aplicación Móvil (`Ec-mobile`)
- [x] **Pixel-Match Móvil:** Correspondencia visual estricta con el mockup móvil (`media_1789842906245.png`):
  - AppBar institucional `FASHION STORE | PERFIL` con acciones.
  - Tarjeta de perfil con botón de edición, banda de métricas en 3 columnas y tarjetas gemelas Wishlist/Bolsa.
  - Lista vertical de pedidos y opciones de configuración con chevrons.
  - BottomNavigationBar persistente con la pestaña `PERFIL` activa.
- [x] **Pruebas Automatizadas y Análisis Estático:** 100% de pruebas en verde con `flutter test` (28/28 pruebas pasando: suite completa incluyendo DTOs, BLoC y Widgets de `CU04`).
- [x] **Análisis Estático Limpio:** 0 issues en `flutter analyze`.
- [x] **Propagación Real de Token y Resiliencia:** Modal bottom sheet con actualización de datos sin selector de género, propagación de JWT real de autenticación desde el login y persistencia atómica en Neon PostgreSQL.

---

## 2. Matriz de Trazabilidad de Verificación

| Componente | Criterio de Verificación | Herramienta / Comando | Estado Actual |
| :--- | :--- | :--- | :--- |
| **Backend** | Tests unitarios y de integración | `pytest tests/modules/autenticacion_seguridad/` | 🟢 Verificado (45/45 tests pasando) |
| **Backend** | Consistencia en base de datos Neon | Script de validación en vivo | 🟢 Superado (Atómico en PostgreSQL Neon) |
| **Frontend Web** | Compilación de bundle de producción | `npm run build` | 🟢 Verificado (0 errores, chunk 34.54 kB) |
| **Frontend Web** | Pruebas unitarias de componentes | `npx ng test --watch=false` | 🟢 Verificado (6/6 tests pasando) |
| **Frontend Web** | Inspección visual contra mockup desktop | Comparación visual con `media_1789842823031.png` | 🟢 Superado (Pixel-Match editorial sin selector de género) |
| **Mobile** | Pruebas de widgets y BLoC | `flutter test` | 🟢 Verificado (28/28 tests pasando) |
| **Mobile** | Análisis estático sin advertencias | `flutter analyze` | 🟢 Verificado (0 issues encontrados) |
| **Mobile** | Inspección visual contra mockup móvil | Comparación visual con `media_1789842906245.png` | 🟢 Superado (Pixel-Match móvil Haute Couture) |
