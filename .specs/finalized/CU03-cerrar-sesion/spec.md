# Especificación Técnica: CU03 - Cerrar Sesión (Logout)

**Código:** CU03  
**Nombre:** Cerrar Sesión (Invalidación Segura de Sesión, Revocación de Token y Purga Omnicanal)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `cu03_cerrar_sesion`  
**Actores:** Cliente, Administrador (Iniciador)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Propuesta Activa de Cambio)  
**Estado:** 🟡 En Espera de Aprobación del Usuario (Fase de Especificación y Planificación)  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Sección 2.1.1.2, CU03 líneas 500, 618, 741-755, 1278, 2526).
- Código Existente: `Ec-backend`, `Ec-frontend`, `Ec-mobile`.

---

## 1. Auditoría del Estado Actual y Brechas Técnicas

### 1.1 Fuente de Verdad del Negocio (`SI2-Parcial1.md`)
En el documento maestro `SI2-Parcial1.md`, el caso de uso se define formalmente en las líneas 741-755:
- **Propósito:** Permitir al usuario finalizar de forma segura su sesión activa en el sistema.
- **Actores:** Cliente, Administrador.
- **Precondiciones:** El usuario debe tener una sesión iniciada.
- **Flujo Principal:**
  1. El usuario selecciona la opción "Cerrar sesión".
  2. El sistema invalida el token/sesión activa.
  3. El sistema redirige al usuario a la pantalla de inicio o login.
- **Postcondiciones:** La sesión del usuario queda finalizada, requiriendo autenticación nuevamente.
- **Excepciones:** Error de conexión al momento de cerrar sesión.

### 1.2 Auditoría de Backend (`Ec-backend`)
- **Estado Actual:**
  - El sistema utiliza JSON Web Tokens (JWT) con firma criptográfica `HS256`, claim `sub = id_usuario` y tiempo de expiración `exp`.
  - La resolución de identidad y autenticación se realiza en `app/core/deps.py` mediante la dependencia `get_current_user`.
  - **Brecha Técnica:** No existe actualmente un módulo `cu03_cerrar_sesion` ni un endpoint `POST /api/v1/autenticacion/logout`.
  - Dado que los tokens JWT son técnicamente sin estado (*stateless*), para cumplir con la postcondición explícita de `SI2-Parcial1.md` (*"El sistema invalida el token/sesión activa"*), se debe implementar un mecanismo de **Lista de Revocación / Blacklist de Tokens** en el backend.
  - Al recibir una solicitud válida de cierre de sesión, el token del usuario se registra en la lista de revocación con su tiempo restante de vida. Cualquier intento posterior de consumir la API con dicho token es rechazado con `401 Unauthorized` (`code="TOKEN_REVOCADO"`).

### 1.3 Auditoría de Frontend Web (`Ec-frontend`)
- **Estado Actual:**
  - Existe un disparador visual explícito en `src/app/modules/autenticacion_seguridad/cu04_gestionar_perfil/paginas/perfil.component.html` (línea 476): botón `CERRAR SESIÓN SEGURA`.
  - En `perfil.component.ts` se invoca `this.loginService.cerrarSesion()` y se realiza `router.navigate(['/login'])`.
  - En `LoginService` (`src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service.ts`):
    - `usuarioActual` es un Signal reactivo inicializado con los datos de sesión.
    - El método `cerrarSesion()` elimina localmente `fashionstore_token` y `fashionstore_user` de `localStorage` y `sessionStorage`, y setea `usuarioActual.set(null)`.
  - **Brecha Técnica:**
    - La operación es 100% local en el navegador; nunca contacta al backend para invalidar el token en el servidor.
    - No existe manejo de resiliencia: si la red falla, el cliente debe garantizar de todos modos la purga total de credenciales y la redirección forzada a `/login`.
    - No hay un estado visual de carga (`cerrandoSesion`) que inhabilite el botón mientras se procesa la salida.

### 1.4 Auditoría de Aplicación Móvil (`Ec-mobile`)
- **Estado Actual:**
  - En `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart` (líneas 915-927) existe el botón estilizado `CERRAR SESIÓN SEGURA`.
  - Al presionarlo, evalúa `widget.alCerrarSesion != null ? widget.alCerrarSesion!() : Navigator.pop(context);`.
  - En `lib/main.dart`, la pantalla `PantallaPerfil` es instanciada sin suministrar el callback `alCerrarSesion`, por lo que simplemente hace un `pop()` hacia `PantallaLogin`.
  - Ni `LoginBloc` ni `PerfilBloc` manejan el evento formal de revocación/logout remoto.
  - **Brecha Técnica:**
    - No se realiza llamada HTTP al endpoint de logout.
    - No se reinicia el estado de los BLoCs en memoria (`LoginBloc.reiniciar()`, `PerfilBloc.reiniciar()`).
    - Al usar `Navigator.pop()`, la pila de navegación podría quedar comprometida si se navegó desde rutas profundas, permitiendo al usuario volver atrás a pantallas protegidas mediante el botón físico/gesto de regreso de Android/iOS. Se requiere `pushAndRemoveUntil`.

---

## 2. Bloque 1: Especificación Técnica Backend (`Ec-backend` - FastAPI)

### 2.1 Contrato de API REST

#### Endpoint: `POST /api/v1/autenticacion/logout`
- **Etiqueta Swagger / OpenAPI:** `Autenticacion y Seguridad`
- **Descripción:** Invalida el token Bearer JWT activo del usuario agregándolo a la lista de revocación y finalizando la sesión en el servidor.
- **Acceso:** Protegido (requiere cabecera `Authorization: Bearer <access_token>`).
- **Dependencias:** `get_current_user` (extrae usuario activo y token desde `deps.py`).
- **Respuesta Exitosa:** `200 OK` con esquema `LogoutOut`.

#### Cabeceras de Solicitud
```http
Authorization: Bearer <access_token>
Content-Type: application/json
Accept: application/json
```

#### Esquema de Salida: `LogoutOut`
```python
from pydantic import BaseModel, Field


class LogoutOut(BaseModel):
    mensaje: str = Field(
        default="Sesión finalizada exitosamente.",
        description="Mensaje confirmando el cierre de sesión seguro.",
        example="Sesión finalizada exitosamente.",
    )
    revocado: bool = Field(
        default=True,
        description="Indicador de que el token ha sido revocado en el servidor.",
        example=True,
    )
    codigo: str = Field(
        default="SESION_FINALIZADA",
        description="Código de evento para trazabilidad y auditoría.",
        example="SESION_FINALIZADA",
    )
```

---

### 2.2 Servicio de Revocación de Tokens (`app/core/token_blacklist.py`)

Para garantizar que los tokens no puedan volver a utilizarse hasta su expiración natural:
1. **Clase `TokenBlacklistService`:**
   - Mantiene en memoria de servidor (o persistido en caché/almacenamiento transaccional) el identificador del token (o su firma hash) junto con su marca de tiempo de expiración (`exp`).
   - Método `revocar_token(token: str, exp_timestamp: float) -> None`: Registra el token en la lista negra.
   - Método `esta_revocado(token: str) -> bool`: Verifica si el token se encuentra en la lista negra.
   - Método de limpieza automática: Elimina periódicamente de la memoria los tokens cuya fecha `exp` ya haya pasado naturalmente.
2. **Integración en `app/core/deps.py` (`get_current_user`):**
   ```python
   # Verificación de revocación antes de consultar la base de datos
   if token_blacklist.esta_revocado(token):
       raise AuthenticationError(
           "La sesión ha sido finalizada. Inicie sesión nuevamente.",
           code="TOKEN_REVOCADO"
       )
   ```

#### Matriz de Códigos HTTP
| Código | Condición | Detalle de Respuesta |
|---|---|---|
| **`200 OK`** | Cierre de sesión exitoso | `{"mensaje": "Sesión finalizada exitosamente.", "revocado": true, "codigo": "SESION_FINALIZADA"}` |
| **`401 Unauthorized`** | Token ausente, inválido o expirado | `{"detail": "Token de acceso no proporcionado", "code": "TOKEN_INVALIDO"}` |
| **`401 Unauthorized`** | Token previamente revocado | `{"detail": "La sesión ha sido finalizada. Inicie sesión nuevamente.", "code": "TOKEN_REVOCADO"}` |

---

### 2.3 Criterios de Aceptación Backend (Gherkin BDD)

```gherkin
Característica: CU03 - Cierre de Sesión y Revocación de Token
  Como usuario autenticado de FashionStore
  Quiero cerrar mi sesión activa en el sistema
  Para evitar accesos no autorizados a mi cuenta en dispositivos compartidos

  Escenario: Cierre de sesión exitoso con token válido
    Dado que un usuario cuenta con un token JWT Bearer válido
    Cuando envía una petición POST a "/api/v1/autenticacion/logout" con dicho token
    Entonces el backend responde con código HTTP 200 OK
    Y el cuerpo contiene "revocado": true y "codigo": "SESION_FINALIZADA"
    Y el token queda registrado en la lista negra de revocación.

  Escenario: Rechazo de petición subsiguiente con token revocado
    Dado que un usuario cerró sesión exitosamente y su token fue revocado
    Cuando intenta realizar una petición GET a "/api/v1/perfil" con el mismo token
    Entonces el servidor responde con código HTTP 401 Unauthorized
    Y el detalle de error indica "TOKEN_REVOCADO".

  Escenario: Intento de cerrar sesión sin token de autenticación
    Dado que se envía una petición POST a "/api/v1/autenticacion/logout" sin cabecera Authorization
    Cuando el servidor evalúa la solicitud
    Entonces responde con código HTTP 401 Unauthorized
    Y el cuerpo contiene "code": "TOKEN_INVALIDO".
```

---

## 3. Bloque 2: Especificación Técnica Frontend Web (`Ec-frontend` - Angular 19+)

### 3.1 Arquitectura del Flujo de Salida
1. **Actualización de `LoginService` (`src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service.ts`):**
   - Incorporación del método `cerrarSesionRemota(): Observable<void>`:
     - Extrae el token actual de `usuarioActual()?.token` o de `localStorage`/`sessionStorage`.
     - Si hay token, ejecuta petición HTTP `POST /api/v1/autenticacion/logout` enviando la cabecera `Authorization: Bearer <token>`.
     - Implementa un operador `finalize()` para asegurar que, **tanto si la petición responde 200 OK como si hay error de red o timeout**, se ejecute la limpieza atómica del cliente:
       1. `this.usuarioActual.set(null)` (el computed `estaAutenticado` se actualiza inmediatamente a `false`).
       2. Eliminación de `fashionstore_token` y `fashionstore_user` de `localStorage` y `sessionStorage`.
       3. Redirección forzada mediante `this.router.navigate(['/login'])`.
2. **Vinculación en `PerfilComponent`:**
   - El botón `CERRAR SESIÓN SEGURA` en `perfil.component.html` muestra estado de carga (`cerrandoSesion = signal(false)`), deshabilitando clicks repetidos.
   - Al completar la purga, navega limpiamente a la vista de login.

---

## 4. Bloque 3: Especificación Técnica Aplicación Móvil (`Ec-mobile` - Flutter 3.x)

### 4.1 Arquitectura Limpia y Despacho BLoC
1. **Capa de Datos (`cu03_cerrar_sesion` o delegación en `LoginRepositorio`):**
   - Creación de método `cerrarSesion(String token): Future<void>` en el repositorio remoto:
     - Realiza `POST` a `http://10.0.2.2:8000/api/v1/autenticacion/logout` (emulador) o `http://127.0.0.1:8000/api/v1/autenticacion/logout` (web/dispositivo físico) con cabecera `Authorization: Bearer $token`.
     - Manejo resiliente: si el backend responde con error o falta de red, la excepción se captura para no bloquear la salida local del usuario.
2. **Limpieza de Estado y Almacenamiento Local:**
   - Reinicio de los controladores de estado en memoria: `LoginBloc.reiniciar()`, `PerfilBloc.reiniciar()`.
3. **Navegación Restrictiva y Blindaje de Pila:**
   - Sustitución de `Navigator.pop(context)` por:
     ```dart
     Navigator.of(context).pushAndRemoveUntil(
       MaterialPageRoute(builder: (_) => const PantallaLogin()),
       (route) => false,
     );
     ```
   - Esto vacía de raíz el stack de navegación, imposibilitando que el usuario regrese a la pantalla de perfil mediante el botón atrás del dispositivo móvil sin volverse a autenticar.
