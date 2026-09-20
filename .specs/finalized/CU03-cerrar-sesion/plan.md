# Plan de Ejecución Secuencial: CU03 - Cerrar Sesión (Logout)

**Caso de Uso:** CU03. Cerrar Sesión  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Estrategia:** Desarrollo Estrictamente Secuencial por Fases (Backend -> Frontend Web -> Mobile)  
**Fecha:** 2026-09-19  
**Estado:** 🟡 Pendiente de Aprobación del Usuario  

---

## 1. Fase 1: Backend (`Ec-backend` - FastAPI + PyJWT)

### Oleada 1: Servicio de Lista Negra de Tokens (`app/core/token_blacklist.py`)
- Crear servicio singleton `TokenBlacklistService` en memoria con soporte para expiración automática.
- Integrar la verificación `esta_revocado(token)` dentro de la dependencia `get_current_user` en `app/core/deps.py`.
- Lanzar `AuthenticationError("La sesión ha sido finalizada", code="TOKEN_REVOCADO")` si el token fue añadido a la lista negra.

### Oleada 2: Esquemas Pydantic y Router (`cu03_cerrar_sesion/`)
- Crear `LogoutOut` en `app/modules/autenticacion_seguridad/cu03_cerrar_sesion/esquemas.py`.
- Crear endpoint `POST /logout` en `app/modules/autenticacion_seguridad/cu03_cerrar_sesion/router.py`.
- Montar el router bajo el prefijo `/autenticacion` en `app/modules/autenticacion_seguridad/router.py`.

### Oleada 3: Suite de Pruebas Automatizadas Backend (`tests/`)
- Crear `tests/modules/autenticacion_seguridad/test_cu03_cerrar_sesion.py`:
  - Test de logout exitoso (200 OK con token Bearer).
  - Test de rechazo de llamada subsecuente a `/perfil` o `/logout` usando el token revocado (401 Unauthorized, code="TOKEN_REVOCADO").
  - Test de rechazo sin cabecera Authorization (401 Unauthorized, code="TOKEN_INVALIDO").
- Ejecutar suite de pruebas con `pytest` y asegurar 100% verde sin romper tests existentes.

---

## 2. Fase 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### Oleada 4: Actualización de `LoginService` (`cu02_iniciar_sesion/servicios/login.service.ts`)
- Implementar método `cerrarSesion()` con llamada HTTP `POST /api/v1/autenticacion/logout`.
- Garantizar purga atómica de `localStorage` y `sessionStorage` en el operador `finalize()`.
- Reseteo del signal `usuarioActual.set(null)` y navegación automática a `/login`.

### Oleada 5: Vinculación en Componentes y Verificación
- Conectar el botón `CERRAR SESIÓN SEGURA` en `PerfilComponent` (`perfil.component.ts` y `perfil.component.html`).
- Añadir indicador de carga deshabilitando clicks múltiples mientras se procesa la salida.
- Ejecutar compilación de producción con Angular CLI (`npm run build`) y verificar tests unitarios con `ng test`.

---

## 3. Fase 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x + Dart)

### Oleada 6: Capa de Datos y Repositorio de Salida
- Añadir método `cerrarSesion(String token)` en la capa de datos/repositorio (`login_repositorio.dart` o módulo específico).
- Enviar petición HTTP `POST /api/v1/autenticacion/logout` con cabecera `Authorization: Bearer $token`.
- Asegurar resiliencia ante errores de red (purga local garantizada).

### Oleada 7: Despacho BLoC, Reseteo de Memoria y Navegación
- Añadir método o evento `cerrarSesion` en `PerfilBloc` / `LoginBloc`.
- En `pantalla_perfil.dart`, implementar el botón `CERRAR SESIÓN SEGURA` para:
  1. Invocar el cierre de sesión remoto.
  2. Reiniciar los estados de los BLoCs en memoria (`reiniciar()`).
  3. Ejecutar `Navigator.pushAndRemoveUntil(..., (route) => false)` hacia `PantallaLogin`.
- En `main.dart`, suministrar el callback `alCerrarSesion` en la instanciación de `PantallaPerfil`.
- Ejecutar pruebas automatizadas con `flutter test` y validación de código con `flutter analyze`.
