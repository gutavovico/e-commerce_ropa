# Puntos de Control y Verificación: CU03 - Cerrar Sesión (Logout)

**Caso de Uso:** CU03. Cerrar Sesión  
**Fase:** Bloques 1 (Backend), 2 (Frontend Web) y 3 (Mobile) Completados y Verificados  
**Fecha:** 2026-09-19  
**Estado:** 🟢 100% Superado y Verificado en los 3 Bloques (Listo para Promoción a Permanente)  

---

## 1. Criterios de Aceptación Cuantitativos

Para que la implementación del caso de uso `CU03` sea aprobada y considerada lista para promoción a permanente, se deberán superar obligatoriamente los siguientes gates de calidad:

### 1.1 Backend (`Ec-backend`)
- [x] **Suite de Pruebas Automatizadas:** 100% de tests en verde en `pytest` para la suite completa acumulada (52/52 pruebas pasando: 45 existentes + 7 nuevas de `CU03`).
- [x] **Cobertura de Casos de Error:** Verificación explícita de `200 OK` (salida exitosa), `401 Unauthorized` (token no suministrado), y `401 Unauthorized` con `code="TOKEN_REVOCADO"` ante reuso de token revocado.
- [x] **Persistencia de Revocación:** Comprobación de que tras invocar `POST /api/v1/autenticacion/logout`, cualquier endpoint protegido (`GET /api/v1/perfil`, etc.) rechaza de inmediato dicho token.

### 1.2 Frontend Web (`Ec-frontend`)
- [x] **Inspección de Almacenamiento:** Eliminación verificable de `fashionstore_token` y `fashionstore_user` tanto en `localStorage` como en `sessionStorage`.
- [x] **Reseteo de Estado Reactivo:** El signal `usuarioActual()` se convierte en `null` y el computed `estaAutenticado()` en `false`.
- [x] **Redirección y Protección de Rutas:** Redirección automática a `/login` e impedimento de reingreso a `/perfil` mediante navegación hacia atrás en el historial del navegador.
- [x] **Compilación Limpia:** Compilación de producción con Angular CLI (`npm run build`) en 0 errores (bundle en 4.22s).
- [x] **Tests Unitarios:** Suite de pruebas en verde con `ng test` (10/10 tests pasando).
- [x] **Consistencia Visual:** Texto del botón de acción preservado estrictamente como `CERRAR SESIÓN`.

### 1.3 Aplicación Móvil (`Ec-mobile`)
- [x] **Pila de Navegación Vacía:** Uso estricto de `pushAndRemoveUntil`, comprobando que presionar el botón físico de retroceso no regrese a la pantalla protegida de perfil.
- [x] **Reseteo en Memoria:** Los controladores BLoC (`LoginBloc`, `PerfilBloc`) vuelven a su estado inicial.
- [x] **Pruebas Automatizadas:** 100% de tests en verde en `flutter test` (30/30 tests pasando).
- [x] **Análisis Estático:** 0 incidencias en `flutter analyze` (clean).
- [x] **Consistencia Visual:** Texto del botón de acción preservado estrictamente como `CERRAR SESIÓN`.

---

## 2. Matriz de Trazabilidad de Verificación

| Componente | Criterio de Verificación | Herramienta / Comando | Estado Actual |
| :--- | :--- | :--- | :--- |
| **Backend** | Tests unitarios y de integración de revocación | `pytest tests/modules/autenticacion_seguridad/` | 🟢 Verificado (52/52 tests pasando) |
| **Backend** | Rechazo de token revocado | Test automatizado en Pytest | 🟢 Verificado (HTTP 401 TOKEN_REVOCADO) |
| **Frontend Web** | Purga de Storage y señal reactiva | Inspección de estado y tests Angular | 🟢 Verificado (10/10 tests pasando) |
| **Frontend Web** | Compilación de bundle de producción | `npm run build` | 🟢 Verificado (0 errores, bundle generado) |
| **Mobile** | Despacho de logout y vaciado de stack | `flutter test` | 🟢 Verificado (30/30 tests pasando) |
| **Mobile** | Análisis estático sin advertencias | `flutter analyze` | 🟢 Verificado (0 issues found) |
