# Especificación Técnica Permanente: CU03 - Cerrar Sesión (Logout)

**Código:** CU03  
**Nombre:** Cerrar Sesión (Invalidación Segura de Sesión, Revocación de Token y Purga Omnicanal)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `cu03_cerrar_sesion`  
**Actores:** Cliente, Administrador (Iniciador)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Línea Base Permanente)  
**Estado:** 🟢 Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Sección 2.1.1.2, CU03 líneas 500, 618, 741-755, 1278, 2526).
- Implementación y Verificación: `Ec-backend`, `Ec-frontend`, `Ec-mobile`.

---

## 1. Definición Funcional y Reglas de Negocio

De acuerdo con la fuente de verdad técnica `SI2-Parcial1.md`:
- **Propósito:** Permitir al usuario autenticado finalizar de manera segura y confiable su sesión activa en el sistema omnicanal (Web y Móvil).
- **Actores:** Cliente, Administrador.
- **Precondiciones:** El usuario debe contar con una sesión activa representada por un token JWT válido.
- **Flujo Principal:**
  1. El usuario presiona la acción interactiva de cierre de sesión (`CERRAR SESIÓN`).
  2. El sistema envía la solicitud de invalidación al servidor, registrando el token activo en la lista de revocación (blacklist).
  3. El sistema purga de manera inmediata e irrevocable todas las credenciales y datos de sesión cacheados en el almacenamiento del cliente (`localStorage`, `sessionStorage`, memoria reactiva de BLoC / Signals).
  4. El sistema redirige al usuario a la pantalla de inicio o login, impidiendo la navegación hacia atrás a vistas protegidas.
- **Postcondiciones:** La sesión queda completamente terminada. Cualquier intento de reutilizar el token emitido es rechazado por el backend con `401 Unauthorized` (`code="TOKEN_REVOCADO"`).
- **Flujos de Excepción:**
  - Si ocurre una desconexión o fallo de red durante el llamado HTTP al backend, el cliente prioriza la seguridad local ejecutando de todos modos la purga total de tokens y la redirección a la pantalla de login (*resiliencia offline-first*).

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + Python)

### 2.1 Contrato de API REST

#### Endpoint: `POST /api/v1/autenticacion/logout`
- **Etiqueta OpenAPI:** `Autenticacion y Seguridad`
- **Ruta Completa:** `/api/v1/autenticacion/logout`
- **Seguridad:** Requiere cabecera `Authorization: Bearer <access_token>`.
- **Dependencias:** `get_current_user` (`app/core/deps.py`).
- **Respuesta:** `200 OK` con esquema `LogoutOut`.

#### Esquema Pydantic: `LogoutOut` (`app/modules/autenticacion_seguridad/cu03_cerrar_sesion/esquemas.py`)
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

### 2.2 Servicio de Lista Negra de Tokens (`app/core/token_blacklist.py`)
- **Implementación:** `TokenBlacklistService` administra en memoria (con soporte para hash SHA-256 como identificador de bajo consumo) el listado de tokens revocados junto con su marca temporal de expiración (`exp`).
- **Limpieza de Recursos:** Purga periódicamente los tokens cuya vigencia natural haya expirado, liberando memoria de manera eficiente.
- **Validación en Dependencia Central (`app/core/deps.py`):**
  Al procesar cualquier petición autenticada, `get_current_user` verifica:
  ```python
  if token_blacklist.esta_revocado(token):
      raise AuthenticationError(
          "La sesión ha sido finalizada. Inicie sesión nuevamente.",
          code="TOKEN_REVOCADO",
      )
  ```
- **Matriz de Respuestas HTTP:**
  - `200 OK`: Token invalidado exitosamente.
  - `401 Unauthorized` (`TOKEN_INVALIDO`): Token malformado o no proporcionado.
  - `401 Unauthorized` (`TOKEN_REVOCADO`): Intento de consumo de API con token registrado en blacklist.

---

## 3. Arquitectura Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Integración en `LoginService` (`cu02_iniciar_sesion/servicios/login.service.ts`)
- **Método `cerrarSesion(): Observable<void>`:**
  - Extrae el token activo mediante `obtenerToken()`.
  - Si el token está presente, despacha `POST /api/v1/autenticacion/logout` con cabecera `Authorization: Bearer <token>`.
  - Mediante el operador RxJS `finalize()`, garantiza la ejecución irrestricta de `purgarSesionLocal()`:
    1. Remoción de `fashionstore_token` y `fashionstore_user` de `localStorage` y `sessionStorage`.
    2. Actualización de la señal reactiva `this.usuarioActual.set(null)` (lo que actualiza automáticamente `estaAutenticado = false`).
    3. Redirección forzada mediante `this.router.navigate(['/login'])`.

### 3.2 Interfaz de Usuario (`PerfilComponent`)
- **Botón de Acción:** Ubicado en la barra lateral del panel de cuenta, identificado con la etiqueta estricta **`CERRAR SESIÓN`**.
- **Control de Concurrencia:** Señal `cerrandoSesion = signal(false)` que inhabilita el botón con `[disabled]="cerrandoSesion()"` para prevenir dobles invocaciones accidentales.

---

## 4. Arquitectura Aplicación Móvil (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Capa de Datos y Dominio
- **`LoginRepositorio` y `LoginRemotoDatasource`:**
  - Método `cerrarSesion(String token)` que ejecuta `POST /api/v1/autenticacion/logout`.
  - Resiliencia ante fallos: captura interna de `Exception` para garantizar que la desconexión del servidor nunca atrape al usuario en un estado local logueado.

### 4.2 Control de Estado y Navegación Segura
- **Reinicio de BLoCs:** Invocación a `LoginBloc.reiniciar()` restableciendo el estado a `LoginInicial`.
- **Blindaje de Pila de Navegación:**
  En `main.dart` y `PantallaPerfil`, la acción de logout utiliza:
  ```dart
  Navigator.of(context).pushAndRemoveUntil(
    MaterialPageRoute(builder: (_) => const PantallaLogin()),
    (route) => false,
  );
  ```
  Esto erradica completamente las rutas previas de la memoria, impidiendo que el usuario pueda volver a pantallas privadas mediante el botón físico o gesto de retroceso del dispositivo.
- **Consistencia Visual:** Botón interactivo con el texto estricto **`CERRAR SESIÓN`**.

---

## 5. Matriz de Verificación y Pruebas Automatizadas

| Módulo / Capa | Herramienta | Pruebas Ejecutadas | Resultado |
| :--- | :--- | :--- | :--- |
| **Backend** | `pytest` | 52 tests (7 específicos de CU03 + 45 existentes) | 🟢 **100% Passing (0 regresiones)** |
| **Frontend Web** | `Vitest / ng test` | 10 tests unitarios y de integración | 🟢 **100% Passing** |
| **Frontend Web** | Angular CLI (`ng build`) | Compilación de bundle de producción | 🟢 **Compilación limpia en 4.22s** |
| **Mobile** | `flutter test` | 30 tests unitarios, BLoC y de widgets | 🟢 **100% Passing** |
| **Mobile** | `flutter analyze` | Análisis estático de código Dart | 🟢 **0 issues found** |

---

## 6. Historial de Decisiones Técnicas y Ajustes de Implementación

1. **Lista de Revocación en Memoria con Algoritmo SHA-256:** Para maximizar la velocidad y desacoplar la carga de la base de datos PostgreSQL Serverless, la lista negra opera en memoria indexada por hash de firma SHA-256 con purga programada por fecha de expiración `exp`.
2. **Resiliencia Cliente (Offline-First Logout):** En Frontend y Mobile, el flujo de salida ejecuta la purga de almacenamiento local incluso si la petición HTTP falla o excede el timeout de red.
3. **Consistencia Visual en Etiqueta de Acción:** Por indicación directa del usuario, se descartaron sufijos ("CERRAR SESIÓN SEGURA") o textos dinámicos ("CERRANDO SESIÓN..."), manteniendo la etiqueta unificada e invariable como **`CERRAR SESIÓN`** en ambas aplicaciones.
4. **Normalización de Imports en Flutter:** Se adoptaron rutas absolutas de paquete (`package:ec_mobile/...`) en los widgets de presentación para evitar fallos de resolución de paths relativos entre submódulos distantes.
