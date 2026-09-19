# Plan de Implementación SDD: CU02 - Iniciar Sesión

**Caso de Uso:** CU02. Iniciar Sesión  
**Alcance Actual:** Bloque 1 (Backend: 🟢 Completado), Bloque 2 (Frontend Web: 🟢 Completado) y Bloque 3 (Mobile: 🟢 Completado)  
**Metodología:** SDD por Oleadas de Implementación y Verificación  
**Fecha:** 2026-09-19  
**Estado:** 🟢 Completado al 100% (Bloques 1, 2 y 3)  

---

## Estrategia de Ejecución por Oleadas (Backend)

### Oleada 1: Esquemas de Validación Pydantic
- **Directorio:** `app/modules/autenticacion_seguridad/cu02_iniciar_sesion/`
- **Archivo:** `esquemas.py`
- **Componentes:**
  - `LoginIn`: `email: EmailStr`, `password: str`, `recordar_dispositivo: bool = False`.
  - `LoginOut`: `access_token: str`, `token_type: str = "bearer"`, `id_usuario: int`, `email: str`, `nombres: str`, `apellidos: str`, `rol: str`.

### Oleada 2: Servicio de Dominio Transaccional
- **Archivo:** `servicio.py`
- **Componente:** `ServicioAutenticarLogin`
- **Comportamiento:**
  - Búsqueda por `email` normalizado en `fashionstore.usuarios`.
  - Validación con `verify_password` (Argon2id).
  - Lanzamiento de `AuthenticationError` (401) ante correo no encontrado o contraseña inválida (`code="CREDENCIALES_INVALIDAS"`).
  - Lanzamiento de `AuthorizationError` (403) si `activo == False` (`code="CUENTA_INACTIVA"`).
  - Actualización atómica de `ultimo_acceso = now()` en BD.
  - Emisión de JWT con claims requeridos mediante `create_access_token`.

### Oleada 3: Router HTTP de FastAPI
- **Archivo:** `router.py` en `cu02_iniciar_sesion/`
- **Componente:** Endpoint `POST /login` con dependencia de sesión de base de datos (`get_db`).
- **Montaje:** Integración de `cu02_router` dentro de `app/modules/autenticacion_seguridad/router.py`.

### Oleada 4: Suite de Pruebas Automatizadas
- **Archivo:** `tests/modules/autenticacion_seguridad/test_cu02_iniciar_sesion.py`
- **Casos de prueba:**
  1. `test_esquema_login_in_valido` / `test_esquema_login_in_email_invalido`
  2. `test_servicio_login_exitoso`
  3. `test_servicio_login_credenciales_invalidas_password`
  4. `test_servicio_login_credenciales_invalidas_email`
  5. `test_servicio_login_cuenta_inactiva`
  6. `test_endpoint_post_login_200_ok`
  7. `test_endpoint_post_login_401_credenciales_invalidas`
  8. `test_endpoint_post_login_403_cuenta_inactiva`
  9. `test_endpoint_post_login_422_validacion`

### Oleada 5: Ejecución y Verificación en Vivo
- Ejecución de `pytest` (verificar que 100% de los tests nuevos y preexistentes pasen).
- Prueba HTTP en vivo contra la base de datos de Neon.
- Actualización de `tasks.md` y `checkpoint.md`.

---

## Estrategia de Ejecución por Oleadas (Bloque 2: Frontend Web)

### Oleada 6: Interfaces y DTOs Tipados
- **Ubicación:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/modelos/`
- **Archivo:** `login.dto.ts`
- **Componentes:**
  - `LoginPeticion`: `email: string`, `password: string`, `recordar_dispositivo: boolean`.
  - `LoginRespuesta`: `access_token: string`, `token_type: string`, `id_usuario: number`, `email: string`, `nombres: string`, `apellidos: string`, `rol: string`.
  - `UsuarioSesion`: Interfaz de sesión activa en cliente.

### Oleada 7: Servicio HTTP y Gestión de Sesión
- **Ubicación:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/`
- **Archivo:** `login.service.ts`
- **Componentes:**
  - `LoginService` con inyección vía `inject(HttpClient)`.
  - Método `iniciarSesion(peticion: LoginPeticion): Observable<LoginRespuesta>`.
  - Persistencia de sesión (`localStorage` si `recordar_dispositivo` es true, `sessionStorage` en caso contrario).
  - Manejo de excepciones y mapeo de errores HTTP (401, 403, 422, 0).

### Oleada 8: Componente Standalone con Signals y OnPush
- **Ubicación:** `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/paginas/`
- **Archivos:** `login.component.ts`, `login.component.html`, `login.component.scss`
- **Componentes:**
  - `LoginComponent` con `ChangeDetectionStrategy.OnPush`.
  - Formulario Reactivo tipado (`FormGroup<FormularioLogin>`).
  - Maquetación con background de boutique atelier (`atelier_bg.jpg`), badge flotante superior `FS`, tarjeta blanca inmaculada, inputs estilizados con iconos integrados, toggle de visibilidad de contraseña, checkbox personalizado, botón negro `INICIAR SESIÓN  →` con microinteracción de spinner y badge de seguridad inferior.

### Oleada 9: Declaración de Rutas en Angular
- **Ubicación:** `Ec-frontend/src/app/app.routes.ts`
- **Rutas:** Mapeo de `login` e `iniciar-sesion` con carga diferida (`loadComponent`).

### Oleada 10: Compilación y Verificación Frontend
- Verificación de tipos TypeScript estrictos.
- Ejecución de compilación con Angular CLI (`npm run build`).
- Actualización de `tasks.md` y `checkpoint.md`.

---

## Estrategia de Ejecución por Oleadas (Bloque 3: Aplicación Móvil Flutter)

### Oleada 11: DTOs y Modelos de Entrada/Salida
- **Ubicación:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/`
- **Archivo:** `login_dto.dart`
- **Componentes:**
  - `LoginPeticionDto`: serialización `toJson()` con saneamiento de espacios.
  - `LoginRespuestaDto`: deserialización `fromJson()` con tokens, usuario y rol.

### Oleada 12: Datasource Remoto y Repositorio
- **Ubicación:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/fuentes_datos/` y `dominio/repositorios/`
- **Archivos:** `login_remoto_datasource.dart`, `login_repositorio.dart`
- **Componentes:**
  - `LoginRemotoDatasource`: llamada HTTP POST a `${ApiConfig.baseUrl}/api/v1/autenticacion/login`.
  - Excepción tipada `LoginExcepcion` con captura de status (401, 403, 422, socket).
  - Repositorio `LoginRepositorio` y su implementación `LoginRepositorioImpl`.

### Oleada 13: Gestión de Estado con BLoC
- **Ubicación:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/bloc/`
- **Archivo:** `login_bloc.dart`
- **Componentes:**
  - Estados inmutables sellados: `LoginInicial`, `LoginCargando`, `LoginExitoso`, `LoginFallido`.
  - `LoginBloc` extendiendo `ChangeNotifier` con método `iniciarSesion(LoginPeticionDto)`.

### Oleada 14: Vista de Interfaz Móvil Haute Couture
- **Ubicación:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/`
- **Archivo:** `pantalla_login.dart`
- **Componentes:**
  - Maquetación fiel a `media_1789836194645.png`:
    1. Fondo `assets/atelier_bg.jpg` con `ImageFilter.blur` y overlay oscuro.
    2. Badge squircle blanco `FS` flotante superior (`BorderRadius.circular(16)`).
    3. Tarjeta blanca central (`BorderRadius.circular(28)`).
    4. Encabezado `— BIENVENIDO DE VUELTA —` y `FASHION STORE`.
    5. Campos con prefijo `@` y candado, botón de ojo para alternar contraseña.
    6. Casilla `Recordar en este dispositivo`.
    7. Botón obsidiana `INICIAR SESIÓN  →` con `CircularProgressIndicator`.
    8. Enlace a `PantallaRegistro`.
    9. Píldora inferior de seguridad `CONEXIÓN CIFRADA & PRIVACIDAD MAISON`.

### Oleada 15: Suite de Pruebas y Análisis Estático
- **Ubicación:** `Ec-mobile/test/`
- **Archivos:** `login_dto_test.dart`, `login_bloc_test.dart`, `pantalla_login_test.dart`.
- **Verificación:**
  - Ejecución de `flutter analyze` (0 issues).
  - Ejecución de `flutter test` (100% pasando).
  - Actualización de `tasks.md` y `checkpoint.md`.

### Oleada 16: Configuración de Ruta Inicial y Enrutamiento Bidireccional
- **Ubicación:** `Ec-mobile/lib/main.dart` y `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu01_registrarse/presentacion/pantallas/pantalla_registro.dart`
- **Cambios Realizados:**
  - `main.dart`: Cambio de `home: const PantallaRegistro()` a `home: const PantallaLogin()` para que la pantalla de entrada principal sea el inicio de sesión.
  - `pantalla_registro.dart`: Ajuste en el callback `onTap` del enlace inferior para retornar a `PantallaLogin` mediante `Navigator.pop(context)` o `Navigator.pushReplacement` si no hay ruta previa en la pila.
  - `test/widget_test.dart`: Actualización de la prueba de widget de nivel de aplicación para verificar el arranque en `PantallaLogin` y el ciclo de navegación bidireccional Login ↔ Registro.


