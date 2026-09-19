# Checkpoint SDD: CU02 - Iniciar Sesión (Bloques 1, 2 y 3)

**Caso de Uso:** CU02. Iniciar Sesión  
**Fecha:** 2026-09-19  
**Estado:** 🟢 Bloques 1 (Backend), 2 (Frontend Web) y 3 (Mobile) Completados y Verificados al 100%  
**Directorio de Especificación:** `.specs/changes/CU02-iniciar-sesion/`  
**Módulo Backend:** `Ec-backend/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/`  
**Módulo Frontend:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/`  
**Módulo Mobile:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/`  

---

## 1. Estado de Tareas Ejecutadas

### Bloque 1: Backend (`Ec-backend`)
- [x] **T1 (Esquemas Pydantic):** `LoginIn` y `LoginOut` implementados en `esquemas.py` con validación estricta y normalización de espacios.
- [x] **T2 (Servicio de Dominio):** `ServicioAutenticarLogin` implementado en `servicio.py` con verificación Argon2id, protección contra enumeración de usuarios, comprobación de estado de cuenta y emisión de token JWT.
- [x] **T3 (Router HTTP y Montaje):** Endpoint `POST /login` implementado en `router.py` y montado en el router central del paquete `autenticacion_seguridad` (`/api/v1/autenticacion/login`).
- [x] **T4 (Suite de Pruebas):** 13 pruebas unitarias y de integración desarrolladas en `test_cu02_iniciar_sesion.py`.
- [x] **T5 (Verificación Final):** 28/28 tests de pytest pasando al 100% y validación en vivo exitosa contra PostgreSQL en Neon.

### Bloque 2: Frontend Web (`Ec-frontend`)
- [x] **T6 (Modelos y DTOs TypeScript):** `LoginPeticion`, `LoginRespuesta` y `UsuarioSesion` definidos en `login.dto.ts` en concordancia 1:1 con la API de FastAPI.
- [x] **T7 (Servicio HTTP y Sesión):** `LoginService` implementado con `inject(HttpClient)`, Signals para `usuarioActual` y `estaAutenticado`, persistencia condicional (`localStorage` o `sessionStorage`) y mapeo de errores HTTP (401, 403, 422, 0).
- [x] **T8 (Componente Standalone):** `LoginComponent` con `ChangeDetectionStrategy.OnPush`, Signals reactivos, formulario tipado y maquetación fiel al mockup (`media_1789836328018.png` y `media_1789836194645.png`):
  - Fondo atelier boutique de alta costura con overlay (`/atelier_bg.jpg`).
  - Badge flotante superior `FS` en squircle blanco con elevación óptica.
  - Tarjeta central blanca inmaculada (`rounded-[28px]`, `shadow-2xl`).
  - Encabezado con `— BIENVENIDO DE VUELTA —` y `FASHION STORE`.
  - Campos de entrada gris perla con iconos vectoriales integrados (@ y candado).
  - Toggle de visibilidad de contraseña con icono de ojo.
  - Casilla de recordar sesión y botón obsidian `INICIAR SESIÓN  →` con microinteracción de carga.
  - Píldora inferior de seguridad `CONEXIÓN CIFRADA & PRIVACIDAD MAISON`.
- [x] **T9 (Rutas y Navegación):** Rutas `/login` e `/iniciar-sesion` registradas en `app.routes.ts` con carga diferida (`loadComponent`). Enlaces bidireccionales entre `/registro` y `/login` verificados.
- [x] **T10 (Compilación y Verificación):** Compilación de producción con Angular CLI (`npm run build`) completada en 5.4s sin advertencias ni errores. Comunicación de proxy verificada (`localhost:4200` -> `localhost:8000`).

### Bloque 3: Aplicación Móvil (`Ec-mobile`)
- [x] **T11 (Modelos y DTOs Dart):** `LoginPeticionDto` y `LoginRespuestaDto` implementados en `login_dto.dart` con serialización `toJson` y deserialización segura `fromJson`.
- [x] **T12 (Datasource y Repositorio):** `LoginRemotoDatasource` y `LoginRepositorioImpl` implementados en `datos/` y `dominio/` consumiendo el backend con manejo tipado de `LoginExcepcion`.
- [x] **T13 (Controlador de Estado BLoC):** `LoginBloc` implementado con estados sellados (`LoginInicial`, `LoginCargando`, `LoginExitoso`, `LoginFallido`) y gestión reactiva de carga.
- [x] **T14 (Vista Móvil Haute Couture):** `PantallaLogin` implementada con estética idéntica al mockup (`media_1789836194645.png`):
  - Fondo atelier con desenfoque (`BackdropFilter` con `ImageFilter.blur`).
  - Squircle badge flotante `FS` en tipografía Outfit con elevación 16.
  - Tarjeta central Museum Canvas blanca inmaculada (`BorderRadius.circular(28)`).
  - Inputs con iconos @ y candado, toggle para mostrar/ocultar contraseña.
  - Checkbox de recordar en dispositivo y botón obsidiana `INICIAR SESIÓN  →` con spinner integrado.
  - Enlace de redirección a `PantallaRegistro` y píldora `CONEXIÓN CIFRADA & PRIVACIDAD MAISON`.
- [x] **T15 (Suite de Pruebas y Análisis):**
  - `login_dto_test.dart`: 4 pruebas unitarias de serialización/deserialización.
  - `login_bloc_test.dart`: 4 pruebas unitarias de estados y transiciones BLoC.
  - `pantalla_login_test.dart`: 3 pruebas de renderizado de widgets, validación reactiva e interacción de toggle de contraseña.
  - `flutter test`: 19/19 pruebas pasando al 100%.
  - `flutter analyze`: 0 issues found.
- [x] **T16 (Punto de Entrada Móvil y Enrutamiento Bidireccional):**
  - Configuración de `home: const PantallaLogin()` en `main.dart`.
  - Navegación bidireccional Login ↔ Registro con `Navigator.push` y `Navigator.pop`/`Navigator.pushReplacement`.
  - Prueba de integración en `test/widget_test.dart` verificando arranque en Login y navegación a Registro y regreso.

---

## 2. Evidencias de Verificación

### 2.1 Backend (`pytest`)
- **Comando:** `.\.venv\Scripts\pytest -v`
- **Resultado:** `28 passed, 2 warnings in 0.80s` (100% verde).

### 2.2 Validación en Vivo contra Neon Serverless PostgreSQL
1. **Intento con usuario inexistente:** `POST /api/v1/autenticacion/login` -> `HTTP 401 Unauthorized` (`CREDENCIALES_INVALIDAS`).
2. **Registro y Login exitoso:** Registro en `CU01` (`HTTP 201`) y Login inmediato en `CU02` (`HTTP 200`) retornando token Bearer JWT con rol `cliente`.
3. **Contraseña errónea:** `POST /api/v1/autenticacion/login` -> `HTTP 401 Unauthorized` (`CREDENCIALES_INVALIDAS`).
4. **Auditoría de BD:** Columna `ultimo_acceso` en Neon actualizada atómicamente a timestamp UTC.

### 2.3 Compilación Angular CLI (`Ec-frontend`)
- **Comando:** `npm run build`
- **Resultado:**
  ```text
  Application bundle generation complete. [5.467 seconds]
  Lazy chunk files:
    chunk-SNJJEDBX.js (login-component) | 11.93 kB | Estimated transfer: 3.97 kB
    chunk-HRR53JKM.js (registro-component) | 15.78 kB | Estimated transfer: 4.83 kB
  ```
- **Salida:** `dist/Ec-frontend` generada con éxito (0 errores, 0 advertencias de tipo).

### 2.4 Integración Proxy Frontend -> Backend
- **Endpoint:** `POST http://localhost:4200/api/v1/autenticacion/login`
- **Resultado:** `HTTP 200 OK`
- **Payload recibido:**
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsIn...",
    "token_type": "bearer",
    "id_usuario": 4,
    "email": "test.login.1789837183@fashionstore.com",
    "nombres": "Test",
    "apellidos": "Login",
    "rol": "cliente"
  }
  ```

### 2.5 Pruebas y Análisis Estático Flutter (`Ec-mobile`)
- **Comando:** `flutter test`
  ```text
  00:01 +19: All tests passed!
  ```
- **Comando:** `flutter analyze`
  ```text
  Analyzing Ec-mobile...
  No issues found! (ran in 2.7s)
  ```

### 2.6 Verificación de Preflight CORS (Flutter Web en Puertos Dinámicos)
- **Solicitud de Prueba:** `OPTIONS /api/v1/autenticacion/login` con cabeceras `Origin: http://localhost:50870`, `Access-Control-Request-Method: POST`, `Access-Control-Request-Headers: content-type`.
- **Resultado:** `HTTP 200 OK`
- **Cabeceras Retornadas:**
  - `access-control-allow-origin`: `http://localhost:50870`
  - `access-control-allow-credentials`: `true`
  - `access-control-allow-methods`: `DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT`
  - `access-control-allow-headers`: `content-type`
- **Llamada POST Subsiguiente:** `POST /api/v1/autenticacion/login` responde con la cabecera `Access-Control-Allow-Origin: http://localhost:50870` eliminando el fallo `ClientException: Failed to fetch`.

---

## 3. Estado del Caso de Uso

El caso de uso **CU02 - Iniciar Sesión** se encuentra **100% implementado, probado y verificado** en las tres capas del sistema:
- 🟢 **Backend:** FastAPI + PostgreSQL en Neon + Argon2id + PyJWT.
- 🟢 **Frontend Web:** Angular 19 (Standalone, Signals, OnPush, Typed Reactive Forms, Tailwind CSS).
- 🟢 **Aplicación Móvil:** Flutter 3.x (BLoC, DTOs tipados, Widgets Haute Couture y 100% pruebas en verde).
