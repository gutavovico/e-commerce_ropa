# Tareas de Implementación: CU03 - Cerrar Sesión (Logout)

**Caso de Uso:** CU03. Cerrar Sesión  
**Alcance:** Bloque 1 (Backend), Bloque 2 (Frontend Web) y Bloque 3 (Mobile)  
**Estado:** 🟢 Bloque 1 (Backend), Bloque 2 (Frontend Web) y Bloque 3 (Mobile) 100% Completados y Verificados

---

## Bloque 1: Backend (`Ec-backend`)

- [x] **T1: Servicio de Lista Negra de Tokens (`app/core/token_blacklist.py`)**
  - [x] Implementar `TokenBlacklistService` con almacenamiento en memoria y métodos `revocar_token` y `esta_revocado`.
  - [x] Integrar la verificación en `get_current_user` en `app/core/deps.py` para rechazar tokens revocados con HTTP 401 (`TOKEN_REVOCADO`).

- [x] **T2: Esquema Pydantic y Router de Logout (`cu03_cerrar_sesion/`)**
  - [x] Definir esquema `LogoutOut` con campos `mensaje`, `revocado` y `codigo`.
  - [x] Implementar endpoint `POST /autenticacion/logout` protegido con `Depends(get_current_user)`.
  - [x] Montar el router en `app/modules/autenticacion_seguridad/router.py`.

- [x] **T3: Pruebas Automatizadas Backend (`test_cu03_cerrar_sesion.py`)**
  - [x] Test unitario de revocación exitosa (HTTP 200 OK con token válido).
  - [x] Test de rechazo de reutilización de token revocado en endpoints protegidos (HTTP 401 Unauthorized, code="TOKEN_REVOCADO").
  - [x] Test de llamada sin cabecera Authorization (HTTP 401 Unauthorized).
  - [x] Verificación de ejecución completa de suite con `pytest` sin regresiones (52/52 tests pasando).

---

## Bloque 2: Frontend Web (`Ec-frontend`)

- [x] **T4: Servicio de Logout y Purga de Almacenamiento (`login.service.ts`)**
  - [x] Añadir método `cerrarSesion()` que ejecute `POST /api/v1/autenticacion/logout` con el token Bearer.
  - [x] Manejar resiliencia en `finalize()` para purgar `fashionstore_token` y `fashionstore_user` de `localStorage` y `sessionStorage`.
  - [x] Resetear el Signal reactivo `usuarioActual.set(null)` (provocando `estaAutenticado = false`).
  - [x] Redirigir mediante Angular Router a `/login`.

- [x] **T5: Vinculación en Componentes y Verificación de Compilación**
  - [x] Enlazar el botón con texto estricto `CERRAR SESIÓN` en `PerfilComponent` gestionando estado de carga `cerrandoSesion`.
  - [x] Ejecutar compilación de producción con Angular CLI (`npm run build`).
  - [x] Ejecutar y validar pruebas unitarias (`npx ng test --watch=false`, 10/10 tests pasando).

---

## Bloque 3: Aplicación Móvil (`Ec-mobile`)

- [x] **T6: Repositorio y Llamada Remota de Logout**
  - [x] Implementar método `cerrarSesion(String token)` en `login_repositorio.dart` ejecutando `POST /api/v1/autenticacion/logout`.
  - [x] Implementar captura de excepciones para asegurar que errores de conexión no impidan la salida local.

- [x] **T7: Reseteo de Estados BLoC y Navegación Restrictiva**
  - [x] Reiniciar `LoginBloc` y `PerfilBloc` mediante sus métodos `reiniciar()`.
  - [x] Configurar el callback `alCerrarSesion` en `main.dart` y en `PantallaPerfil` con botón `CERRAR SESIÓN` para ejecutar:
    `Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const PantallaLogin()), (route) => false);`.
  - [x] Ejecutar pruebas de widget y unitarias con `flutter test` (30/30 tests pasando).
  - [x] Ejecutar análisis estático con `flutter analyze` asegurando 0 advertencias.
