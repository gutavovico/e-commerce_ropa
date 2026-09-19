# Tareas de Implementación: CU02 - Iniciar Sesión

**Caso de Uso:** CU02. Iniciar Sesión  
**Alcance:** Bloque 1 (Backend: 🟢 Completado) | Bloque 2 (Frontend Web: 🟢 Completado) | Bloque 3 (Mobile: 🟢 Completado)  
**Estado:** 🟢 Implementación Completa al 100% en los 3 Bloques  

---

## Tareas a Ejecutar

- [x] **T1: Esquemas Pydantic (`cu02_iniciar_sesion/esquemas.py`)**
  - [x] Definir `LoginIn` con validación de `EmailStr`, `password` (mín. 1 carácter) y `recordar_dispositivo`.
  - [x] Definir `LoginOut` con `access_token`, `token_type: "bearer"`, `id_usuario`, `email`, `nombres`, `apellidos`, `rol`.

- [x] **T2: Servicio de Autenticación (`cu02_iniciar_sesion/servicio.py`)**
  - [x] Implementar `ServicioAutenticarLogin.autenticar_usuario(db, datos)`.
  - [x] Normalización de correo a minúsculas y búsqueda en `fashionstore.usuarios`.
  - [x] Verificación de hash con `verify_password` (Argon2id).
  - [x] Lanzamiento de `AuthenticationError` (401) ante correo no existente o clave errónea (`CREDENCIALES_INVALIDAS`).
  - [x] Lanzamiento de `AuthorizationError` (403) si la cuenta no está activa (`CUENTA_INACTIVA`).
  - [x] Actualización de `ultimo_acceso = datetime.now(timezone.utc)` en BD.
  - [x] Emisión de JWT con `create_access_token`.

- [x] **T3: Router HTTP y Montaje (`cu02_iniciar_sesion/router.py`)**
  - [x] Crear endpoint `POST /login` con `response_model=LoginOut` y status `200 OK`.
  - [x] Montar `cu02_router` dentro de `app/modules/autenticacion_seguridad/router.py`.

- [x] **T4: Suite de Pruebas Automatizadas (`test_cu02_iniciar_sesion.py`)**
  - [x] Tests unitarios de esquemas `LoginIn` y `LoginOut`.
  - [x] Tests unitarios del servicio `ServicioAutenticarLogin`.
  - [x] Tests de integración con `TestClient` para códigos 200, 401, 403 y 422.

- [x] **T5: Verificación de Calidad y Cierre de Fase 1**
  - [x] Ejecución de suite de `pytest` (0 fallos, 28/28 pasando al 100%).
  - [x] Prueba en vivo de autenticación contra PostgreSQL en Neon (códigos 200 y 401 confirmados, `ultimo_acceso` auditado).
  - [x] Actualización de checkpoint y tareas completadas.

---

### Bloque 2: Frontend Web (`Ec-frontend`)

- [x] **T6: Modelos y DTOs TypeScript (`cu02_iniciar_sesion/modelos/login.dto.ts`)**
  - [x] Definir interfaces `LoginPeticion`, `LoginRespuesta` y `UsuarioSesion`.
  - [x] Validar compatibilidad estricta con el contrato de FastAPI (`/api/v1/autenticacion/login`).

- [x] **T7: Servicio HTTP y Gestión de Sesión (`cu02_iniciar_sesion/servicios/login.service.ts`)**
  - [x] Implementar `LoginService` con `inject(HttpClient)`.
  - [x] Crear método `iniciarSesion(peticion)` con captura y mapeo de errores HTTP (401, 403, 422, 0).
  - [x] Métodos de almacenamiento de token y sesión (`guardarSesion`, `obtenerSesion`, `cerrarSesion`).

- [x] **T8: Componente Standalone de Inicio de Sesión (`cu02_iniciar_sesion/paginas/`)**
  - [x] Implementar `LoginComponent` con `ChangeDetectionStrategy.OnPush` y Signals (`cargando`, `mensajeError`, `mostrarPassword`).
  - [x] Construir formulario reactivo tipado (`email`, `password`, `recordarDispositivo`).
  - [x] Maquetar vista idéntica a mockup: fondo boutique de alta costura, badge flotante `FS`, tarjeta central blanca con bordes suaves, inputs perla con iconos integrados (@ y candado), alternancia de ojo para visibilidad, enlace a recuperación de clave, checkbox estilizado, botón obsidian `INICIAR SESIÓN  →` con microinteracción de carga y badge de seguridad inferior.

- [x] **T9: Configuración y Enrutamiento (`app.routes.ts`)**
  - [x] Registrar rutas `/login` e `/iniciar-sesion` con carga diferida (`loadComponent`).
  - [x] Conectar enlaces de navegación entre `/registro` y `/login`.

- [x] **T10: Compilación y Verificación de Frontend Web**
  - [x] Compilación limpia con Angular CLI (`npm run build` en 5.4s sin advertencias).
  - [x] Verificación de proxy y comunicación fluida en dev server (`http://localhost:4200/api/v1/autenticacion/login` -> 200 OK).
  - [x] Actualización de tareas y checkpoint final del Bloque 2.

---

### Bloque 3: Aplicación Móvil (`Ec-mobile`)

- [x] **T11: Modelos y DTOs Dart (`cu02_iniciar_sesion/datos/modelos/login_dto.dart`)**
  - [x] Implementar `LoginPeticionDto` con serialización `toJson()`.
  - [x] Implementar `LoginRespuestaDto` con deserialización `fromJson()`.

- [x] **T12: Datasource Remoto y Repositorio (`cu02_iniciar_sesion/datos/` y `dominio/`)**
  - [x] Crear `LoginRemotoDatasource` con consumo de `POST /api/v1/autenticacion/login`.
  - [x] Crear excepción `LoginExcepcion` con captura de códigos de error (401, 403, 422, red).
  - [x] Crear contrato `LoginRepositorio` e implementación `LoginRepositorioImpl`.

- [x] **T13: Controlador de Estado BLoC (`cu02_iniciar_sesion/presentacion/bloc/`)**
  - [x] Crear estados sellados `LoginInicial`, `LoginCargando`, `LoginExitoso`, `LoginFallido`.
  - [x] Implementar `LoginBloc` extendiendo `ChangeNotifier` con método `iniciarSesion`.

- [x] **T14: Vista Móvil Haute Couture (`cu02_iniciar_sesion/presentacion/pantallas/`)**
  - [x] Maquetar `PantallaLogin` idéntica al mockup: fondo atelier con desenfoque (`ImageFilter.blur`), badge squircle `FS`, tarjeta blanca inmaculada con bordes redondeados (28px).
  - [x] Inputs estilizados con iconos integrados (@ y candado) y toggle de visibilidad de contraseña.
  - [x] Casilla de recordar sesión y botón obsidiana `INICIAR SESIÓN  →` con indicador de carga.
  - [x] Enlace a `PantallaRegistro` y píldora de seguridad `CONEXIÓN CIFRADA & PRIVACIDAD MAISON`.

- [x] **T15: Suite de Pruebas Móviles y Verificación de Calidad**
  - [x] Pruebas unitarias de DTOs (`login_dto_test.dart`).
  - [x] Pruebas unitarias de BLoC (`login_bloc_test.dart`).
  - [x] Pruebas de widgets de la pantalla (`pantalla_login_test.dart`).
  - [x] Verificación con `flutter analyze` (0 issues) y `flutter test` (18/18 pruebas pasando al 100%).
  - [x] Actualización final de `tasks.md` y `checkpoint.md`.

- [x] **T16: Punto de Entrada Móvil y Enrutamiento Bidireccional (Actualización UX)**
  - [x] Establecer `PantallaLogin` como pantalla principal (`home`) en `Ec-mobile/lib/main.dart`.
  - [x] Configurar redirección a `PantallaLogin` en el enlace inferior de `PantallaRegistro` (`cu01_registrarse/presentacion/pantallas/pantalla_registro.dart`).
  - [x] Crear prueba de integración de widgets para la navegación fluida Login ↔ Registro en `widget_test.dart`.
  - [x] Validar que las 19 pruebas de `flutter test` pasen en verde al 100% y `flutter analyze` continúe sin observaciones.

- [x] **T17: Soporte de CORS Preflight Dinámico (`CORS_ORIGIN_REGEX`)**
  - [x] Diagnóstico de fallo `OPTIONS 400 Bad Request` por puertos efímeros de Flutter Web (`http://localhost:*`).
  - [x] Adición de `CORS_ORIGIN_REGEX` en `core/config.py` y pase de `allow_origin_regex` en `CORSMiddleware` (`main.py`).
  - [x] Configuración de patrón en `Ec-backend/.env`.
  - [x] Verificación de respuesta HTTP 200 OK en preflight `OPTIONS` y `POST` con cabeceras CORS.




