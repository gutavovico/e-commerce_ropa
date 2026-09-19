# Especificación Permanente: CU02 - Iniciar Sesión (Baseline del Sistema)

**Código:** CU02  
**Nombre:** Iniciar Sesión (Autenticación de Clientes y Emisión de Token de Acceso)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `app/modules/autenticacion_seguridad/cu02_iniciar_sesion`  
**Actores:** Cliente / Usuario Registrado (Iniciador)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Baseline Promovido a Permanente)  
**Estado:** 🟢 Aprobado, Implementado y Verificado (28/28 Backend, 19/19 Mobile, Web Compilado, Neon DB Sincronizada)  
**Fuentes de Verdad:** Mockups visuales oficiales (Desktop & Mobile), arquitectura modular `app/`, esquema `fashionstore` en Neon PostgreSQL.

---

## 1. Descripción y Propósito

El caso de uso **CU02: Iniciar Sesión** provee el mecanismo central de autenticación segura para los usuarios de la plataforma **FashionStore** en sus canales Web (Angular) y Móvil (Flutter).

El flujo permite a un usuario registrado enviar sus credenciales (correo electrónico y contraseña en texto plano) a través de un canal seguro HTTPS. El backend valida la existencia de la cuenta, verifica criptográficamente el hash con **Argon2id**, actualiza la fecha de último acceso en la base de datos y genera un **JSON Web Token (JWT)** firmado con algoritmo **HS256** que contiene los claims de identidad y rol del usuario.

---

## 2. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy + Neon)

### 2.1 Contrato de API REST

#### `POST /api/v1/autenticacion/login`
- **Etiqueta Swagger / OpenAPI:** `Autenticacion y Seguridad`
- **Descripción:** Valida credenciales de acceso, verifica contraseña con Argon2 y emite token Bearer JWT.
- **Acceso:** Público (sin cabecera Authorization requerida).

#### Cabeceras de Solicitud
```http
Content-Type: application/json
Accept: application/json
```

#### Esquema de Entrada: `LoginIn`
```python
class LoginIn(BaseModel):
    email: EmailStr = Field(
        ...,
        description="Correo electrónico registrado del usuario",
        example="c.laurent@atelier-mode.fr",
    )
    password: str = Field(
        ...,
        min_length=1,
        max_length=128,
        description="Contraseña en texto plano para verificación",
        example="PasswordSeguro123!",
    )
    recordar_dispositivo: bool = Field(
        default=False,
        description="Indica si el usuario solicitó mantener la sesión prolongada en el cliente",
    )
```

#### Esquema de Salida: `LoginOut`
```python
class LoginOut(BaseModel):
    access_token: str = Field(
        ...,
        description="Token JWT firmado (HS256) con expiración y claims de usuario",
    )
    token_type: str = Field(
        default="bearer",
        description="Tipo de token para uso en cabecera Authorization: Bearer <token>",
    )
    id_usuario: int = Field(
        ...,
        description="Identificador primario del usuario en fashionstore.usuarios",
    )
    email: str = Field(
        ...,
        description="Correo electrónico normalizado del usuario",
    )
    nombres: str = Field(
        ...,
        description="Nombres del usuario",
    )
    apellidos: str = Field(
        ...,
        description="Apellidos del usuario",
    )
    rol: str = Field(
        ...,
        description="Rol del usuario (cliente, administrador, encargado_sucursal, etc.)",
    )
```

---

### 2.2 Lógica de Negocio y Seguridad (`ServicioAutenticarLogin`)

1. **Normalización del Correo:**  
   Se aplica `email.strip().lower()` para búsqueda consistente en `fashionstore.usuarios`.
2. **Consulta a la Base de Datos:**  
   Se ejecuta `select(UsuarioORM).where(UsuarioORM.email == email_normalizado)`.
3. **Manejo de Cuenta Inexistente:**  
   Si la consulta retorna `None`, se lanza `AuthenticationError("Credenciales incorrectas", code="CREDENCIALES_INVALIDAS")` (traducido a **HTTP 401**).  
   *Regla de Seguridad:* Mensaje idéntico para correo inexistente o clave errónea para evitar ataques de enumeración de cuentas.
4. **Verificación Criptográfica de Contraseña:**  
   Se invoca `verify_password(datos.password, usuario.password_hash)` mediante la biblioteca `argon2-cffi`.  
   Si retorna `False`, se lanza `AuthenticationError("Credenciales incorrectas", code="CREDENCIALES_INVALIDAS")` (**HTTP 401**).
5. **Verificación de Estado de la Cuenta:**  
   Si `usuario.activo == False`, se lanza `AuthorizationError("La cuenta se encuentra inactiva o suspendida.", code="CUENTA_INACTIVA")` (traducido a **HTTP 403**).
6. **Actualización de Auditoría:**  
   Se actualiza en la sesión `usuario.ultimo_acceso = datetime.now(timezone.utc)` y se confirma (`db.commit()`).
7. **Emisión de JWT:**  
   Se genera el token con `create_access_token` conteniendo:
   - `sub`: `str(usuario.id_usuario)`
   - `email`: `usuario.email`
   - `rol`: `str(usuario.rol)`
   - `exp`: fecha UTC calculada con `JWT_EXPIRE_MINUTES`.

#### Matriz de Respuestas HTTP
| Código | Causa | Formato / Detalle |
|---|---|---|
| **`200 OK`** | Autenticación exitosa | `LoginOut` con token JWT, datos del usuario y rol |
| **`401 Unauthorized`** | Correo inexistente o contraseña no coincide | `{"detail": "Credenciales incorrectas", "code": "CREDENCIALES_INVALIDAS"}` |
| **`403 Forbidden`** | Usuario registrado pero con `activo = false` | `{"detail": "La cuenta se encuentra inactiva o suspendida.", "code": "CUENTA_INACTIVA"}` |
| **`422 Unprocessable Entity`** | Email inválido o payload mal formado | `{"detail": [{"loc": ["body", "email"], "msg": "value is not a valid email address", ...}]}` |

---

### 2.3 Criterios de Aceptación Backend (Gherkin BDD)

```gherkin
Característica: CU02 - Inicio de Sesión y Emisión de JWT
  Como usuario registrado de FashionStore
  Quiero autenticarme con mis credenciales
  Para acceder a las funcionalidades protegidas de la tienda

  Escenario: Inicio de sesión exitoso con credenciales válidas
    Dado que existe un usuario en "fashionstore.usuarios" con email "cliente.valido@fashionstore.com"
    Y su contraseña hash en Argon2 corresponde a "ClaveSegura123!"
    Y el usuario tiene el campo "activo" en verdadero
    Cuando se envía una petición POST a "/api/v1/autenticacion/login" con dicho email y contraseña
    Entonces el backend responde con código HTTP 200 OK
    Y el cuerpo de respuesta incluye "access_token", "token_type: bearer"
    Y los campos "id_usuario", "email", "nombres", "apellidos" y "rol: cliente"
    Y el campo "ultimo_acceso" del usuario en la base de datos se actualiza con la fecha UTC actual.

  Escenario: Intento de inicio de sesión con contraseña incorrecta
    Dado que existe un usuario registrado con email "cliente.valido@fashionstore.com"
    Cuando se envía una petición POST a "/api/v1/autenticacion/login" con una contraseña equivocada
    Entonces el backend responde con código HTTP 401 Unauthorized
    Y el cuerpo contiene "code": "CREDENCIALES_INVALIDAS".

  Escenario: Intento de inicio de sesión con correo inexistente
    Dado que el correo "no.existe@fashionstore.com" no está registrado en la base de datos
    Cuando se envía una petición POST a "/api/v1/autenticacion/login" con ese correo
    Entonces el backend responde con código HTTP 401 Unauthorized
    Y el cuerpo contiene exactamente "code": "CREDENCIALES_INVALIDAS" para evitar enumeración.

  Escenario: Intento de acceso de cuenta inactiva o deshabilitada
    Dado que existe un usuario registrado con email "inactivo@fashionstore.com"
    Y su contraseña es correcta pero su columna "activo" es falso
    Cuando se envía la solicitud de login
    Entonces el backend responde con código HTTP 403 Forbidden
    Y el cuerpo contiene "code": "CUENTA_INACTIVA".

  Escenario: Validación de esquema ante campos vacíos o formato de correo inválido
    Dado que el cliente envía un payload con email "no-es-correo" o password vacío
    Cuando se procesa la petición
    Entonces el backend responde con código HTTP 422 Unprocessable Entity
    Y no se ejecuta ninguna consulta a la base de datos.
```

---

## 3. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ & Tailwind CSS)

### 3.1 Arquitectura y Estructura Modular
El módulo se aloja en: `Ec-frontend/src/app/modules/autenticacion_seguridad/cu02_iniciar_sesion/`
- `modelos/login.dto.ts`: Interfaces TypeScript tipadas estrictamente (`LoginPeticion`, `LoginRespuesta`, `UsuarioSesion`).
- `servicios/login.service.ts`: Servicio HTTP inyectable (`providedIn: 'root'`) que gestiona peticiones a `/api/v1/autenticacion/login` y almacenamiento seguro de token con Angular Signals.
- `paginas/login.component.ts`: Componente Standalone con `ChangeDetectionStrategy.OnPush`, Signals y Formularios Reactivos tipados.
- `paginas/login.component.html`: Plantilla semántica HTML5 con control flow moderno (`@if`), diseño responsive fiel al mockup oficial.
- `paginas/login.component.scss`: Estilos locales encapsulados y microanimaciones de foco.

### 3.2 Jerarquía Visual y Tokens de Alta Costura
1. **Lienzo de Fondo:** Imagen fotográfica de boutique y sastrería de alta costura (`/atelier_bg.jpg`) con overlay oscuro suave (`rgba(10, 10, 10, 0.45)`).
2. **Badge Superior Flotante `FS`:**
   - Contenedor squircle blanco (`#FFFFFF`) con bordes redondeados (`rounded-2xl` / 16px).
   - Tipografía Outfit en mayúsculas: `FS`, peso Bold 700, color negro obsidiana (`#000000`).
   - Sombra sutil de elevación óptica.
3. **Tarjeta Central Flotante (Museum Canvas):**
   - Superficie blanca inmaculada `#FFFFFF`, esquinas suaves de 28px (`rounded-[28px]`), sombra de profundidad editorial (`shadow-2xl`).
   - Máximo ancho contenido: 440px (`max-w-[440px]`), padding simétrico de 36px (`p-9`).
4. **Encabezado Editorial:**
   - Subtítulo superior: `— BIENVENIDO DE VUELTA —` en tipografía Outfit con tracking amplio (`tracking-[0.2em]`), tamaño micro (11px), color neutral-500.
   - Título de marca: `FASHION STORE` en Outfit mayúsculas, tamaño 28px (`text-[28px]`), peso Medium 500, color neutral-950 (`#09090B`).
5. **Campos del Formulario:**
   - **Correo Electrónico:** Etiqueta `CORREO ELECTRÓNICO` (11px, SemiBold 600), fondo gris perla suave (`#F4F4F5`), radio 8px, icono `@` integrado en línea izquierda.
   - **Contraseña:** Fila con etiqueta `CONTRASEÑA` y enlace `¿Olvidaste tu contraseña?`. Caja con icono de candado e icono de ojo para alternar texto plano.
   - **Casilla de Recordar Dispositivo:** Checkbox cuadrado negro con tilde blanco, etiqueta `Recordar en este dispositivo` (13px).
6. **Botón Principal de Acción:**
   - Negro obsidiana sólido `#000000` con texto blanco `#FFFFFF`.
   - Altura estándar de 48px, texto `INICIAR SESIÓN  →` (tracking expandido, 13px, Medium 500).
   - Microinteracción de carga con spinner y texto `AUTENTICANDO...`.
7. **Divisor y Pie de Registro:**
   - Línea hairline `#E4E4E7`.
   - Pregunta `¿Aún no tienes una cuenta exclusiva?` y enlace `Regístrate aquí` navegando a `/registro`.
8. **Píldora de Seguridad Inferior:**
   - Icono de escudo de seguridad vectorial y texto `CONEXIÓN CIFRADA & PRIVACIDAD MAISON`.

### 3.3 Matriz de Traducción de Errores HTTP en Frontend
| Código HTTP | Error Backend | Mensaje al Usuario en Pantalla |
|---|---|---|
| **`401`** | `CREDENCIALES_INVALIDAS` | "Correo electrónico o contraseña incorrectos. Por favor, verifica tus datos." |
| **`403`** | `CUENTA_INACTIVA` | "Tu cuenta se encuentra inactiva o suspendida. Por favor, contacta a soporte." |
| **`422`** | Fallo de validación Pydantic | "El formato del correo o de la contraseña no es válido." |
| **`0`** | Network / Timeout | "No se pudo conectar con el servidor. Revisa tu conexión a internet." |

### 3.4 Criterios de Aceptación Frontend (Gherkin BDD)
```gherkin
Caraterística: CU02 - Inicio de Sesión en Frontend Web
  Como cliente de FashionStore
  Quiero acceder al formulario de login en /login
  Para autenticarme con mis credenciales y acceder a la tienda

  Escenario: Carga inicial de la vista de autenticación
    Dado que el usuario navega a "/login"
    Entonces se presenta la pantalla con el fondo de alta costura de la boutique
    Y el badge superior flotante con las iniciales "FS"
    Y la tarjeta central blanca con los campos de correo y contraseña vacíos
    Y el botón "INICIAR SESIÓN  →" en estado activo.

  Escenario: Envío exitoso de credenciales
    Dado que el usuario ingresa su correo "cliente@fashionstore.com" y su contraseña
    Y presiona el botón "INICIAR SESIÓN  →"
    Entonces el botón entra en estado de carga con "AUTENTICANDO..."
    Y al responder el servidor HTTP 200 OK
    Se almacena el token JWT recibido en el almacenamiento local
    Y el usuario es redirigido a la vista principal o catálogo.

  Escenario: Manejo visual de error 401 Credenciales Inválidas
    Dado que el usuario ingresa una contraseña errónea
    Cuando se procesa el formulario
    Entonces el servidor responde HTTP 401
    Y se visualiza un banner de alerta con fondo carmesí claro
    Y el mensaje "Correo electrónico o contraseña incorrectos. Por favor, verifica tus datos."

  Escenario: Alternancia de visibilidad de contraseña
    Dado que el campo de contraseña tiene texto ingresado
    Cuando el usuario hace clic en el icono del ojo
    Entonces el tipo de entrada cambia de "password" a "text"
    Y el icono cambia a ojo tachado.
```

---

## 4. Bloque 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x & Dart)

### 4.1 Arquitectura y Estructura Modular
El módulo móvil se ubica en: `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/`
- `datos/modelos/login_dto.dart`: DTOs inmutables de entrada y salida (`LoginPeticionDto`, `LoginRespuestaDto`).
- `datos/fuentes_datos/login_remoto_datasource.dart`: Cliente HTTP (`package:http`) contra `/api/v1/autenticacion/login` con manejo de excepciones `LoginExcepcion`.
- `dominio/repositorios/login_repositorio.dart`: Contrato abstracto e implementación concreta del repositorio de autenticación.
- `presentacion/bloc/login_bloc.dart`: Controlador de estado BLoC (`ChangeNotifier`) con estados inmutables sellados (`LoginInicial`, `LoginCargando`, `LoginExitoso`, `LoginFallido`).
- `presentacion/pantallas/pantalla_login.dart`: Vista de alta costura adaptada al diseño institucional.

### 4.2 Jerarquía Visual y Tokens de Experiencia Móvil
1. **Lienzo de Fondo y Desenfoque:**
   - Imagen `assets/atelier_bg.jpg` en pantalla completa (`BoxFit.cover`).
   - Filtro de desenfoque suave (`ImageFilter.blur(sigmaX: 5, sigmaY: 5)`) y tinte cálido con opacidad controlada (`Colors.black.withValues(alpha: 0.40)`).
2. **Badge Superior Flotante `FS`:**
   - Contenedor cuadrado redondeado de 56x56 px en blanco puro (`#FFFFFF`).
   - Radio de esquinas de 16 px (`BorderRadius.circular(16)`), elevación óptica con sombra difusa.
   - Tipografía Outfit en mayúsculas `FS`, peso Bold 700, negro obsidiana.
3. **Tarjeta Central Flotante (Museum Canvas):**
   - Tarjeta en color blanco inmaculado (`Colors.white`), radio de borde de 28 px (`BorderRadius.circular(28)`).
   - Padding interno de 24 a 32 px con restricciones máximas de ancho (420 px).
4. **Encabezado Tipográfico:**
   - Subtítulo `— BIENVENIDO DE VUELTA —` (11 px, mayúsculas, tracking 1.5).
   - Título de marca `FASHION STORE` (26 px, Outfit, peso SemiBold, negro).
5. **Campos de Entrada de Datos:**
   - **Correo Electrónico:** Etiqueta superior `CORREO ELECTRÓNICO` (11 px), caja gris suave (`#F4F4F5`), radio de 8 px, icono prefijo `@`.
   - **Contraseña:** Fila superior flexible con `CONTRASEÑA` a la izquierda y `¿Olvidaste tu contraseña?` a la derecha. Icono de candado a la izquierda y botón de ojo a la derecha para visibilidad.
   - **Recordar Dispositivo:** Casilla de verificación con tilde blanco y texto `Recordar en este dispositivo` envuelto en `Expanded`.
6. **Botón de Acción Principal:**
   - Negro obsidiana sólido (`#000000`), altura de 48 px, bordes de 8 px.
   - Texto `INICIAR SESIÓN  →` en blanco con espaciado amplio.
   - Estado de carga interactivo con `CircularProgressIndicator` blanco.
7. **Divisor y Pie:**
   - Línea hairline (`#E5E5E5`, 1 px).
   - Texto `¿Aún no tienes una cuenta exclusiva?` y enlace interactivo `Regístrate aquí` conectado a `PantallaRegistro`.
8. **Insignia Inferior de Seguridad:**
   - Icono de escudo y texto `CONEXIÓN CIFRADA & PRIVACIDAD MAISON` con `Flexible` y elipsis para protección de layout en pantallas estrechas.

### 4.3 Flujo de Navegación y Punto de Entrada Móvil (Actualización UX)
1. **Punto de Entrada Primario de la Aplicación (`main.dart`):**
   - La pantalla principal y ruta inicial (`home`) de `EcMobileApp` se establece formalmente en `PantallaLogin`.
   - Principio UX: Priorizar el acceso recurrente de clientes registrados, disponiendo el inicio de sesión como la vista inicial por defecto.
2. **Navegación Bidireccional Login ↔ Registro:**
   - **Desde Login hacia Registro:** En `PantallaLogin`, el enlace inferior `¿Aún no tienes una cuenta exclusiva? Regístrate aquí` (`key: 'login_register_link'`) empuja la ruta de `PantallaRegistro` mediante `Navigator.push(...)`.
   - **Desde Registro hacia Login:** En `PantallaRegistro`, el enlace inferior `¿Ya posees una cuenta? Iniciar sesión` evalúa `Navigator.canPop(context)`: si es verdadero, ejecuta `Navigator.pop(context)` para retornar limpiamente a la pantalla de login existente; si es falso, ejecuta `Navigator.pushReplacement(...)` hacia `PantallaLogin`.

### 4.4 Criterios de Aceptación Mobile (Gherkin BDD)
```gherkin
Caraterística: CU02 - Inicio de Sesión y Navegación en Aplicación Móvil Flutter
  Como usuario de la app móvil FashionStore
  Quiero iniciar sesión con mi correo y contraseña
  Para acceder a mi cuenta, mis compras y el vestidor AR

  Escenario: Renderizado visual fiel a la pantalla de Login
    Dado que la aplicación inicia en "PantallaLogin"
    Entonces se visualiza el fondo del atelier con filtro difuminado
    Y el badge superior flotante con las iniciales "FS"
    Y la tarjeta blanca con el título "FASHION STORE"
    Y los campos de correo y contraseña con sus iconos respectivos
    Y el botón "INICIAR SESIÓN  →".

  Escenario: Envío exitoso de credenciales
    Dado que el usuario ingresa su correo y contraseña válidos
    Cuando presiona el botón "INICIAR SESIÓN  →"
    Entonces el botón entra en estado de carga
    Y tras recibir respuesta HTTP 200 de FastAPI
    El BLoC emite el estado "LoginExitoso" con el token Bearer JWT
    Y se presenta un mensaje de confirmación en pantalla.

  Escenario: Notificación visual ante credenciales erróneas
    Dado que el usuario ingresa una contraseña incorrecta
    Cuando presiona "INICIAR SESIÓN  →"
    Entonces el backend responde HTTP 401
    Y el BLoC emite el estado "LoginFallido"
    Y se despliega un SnackBar de alta costura con el mensaje de error.

  Escenario: Alternar visibilidad de contraseña
    Dado que el campo de contraseña contiene caracteres ocultos
    Cuando el usuario pulsa el icono de ojo
    Entonces los caracteres se muestran en texto plano
    Y el icono cambia a ojo tachado.

  Escenario: Navegación bidireccional entre Login y Registro
    Dado que la app inicia mostrando "PantallaLogin" como pantalla raíz
    Cuando el usuario toca el enlace "Regístrate aquí"
    Entonces la aplicación realiza la transición a "PantallaRegistro"
    Y cuando en la pantalla de registro toca "¿Ya posees una cuenta? Iniciar sesión"
    Entonces el sistema regresa de forma inmediata y limpia a "PantallaLogin".
```

---

## 5. Análisis y Resolución Técnica de CORS Preflight (Flutter Web / Edge)

### 5.1 Diagnóstico del Incidente
- **Síntoma:** Al ejecutar la aplicación móvil en navegador web (`flutter run -d edge` o `flutter run -d chrome`), el intento de autenticación resultaba en:
  `ClientException: Failed to fetch, uri=http://localhost:8000/api/v1/autenticacion/login`
  Y en los registros del servidor FastAPI se reportaba:
  `OPTIONS /api/v1/autenticacion/login HTTP/1.1 400 Bad Request`
- **Causa Raíz:**
  1. Los navegadores web ejecutan una solicitud pre-vuelo (`OPTIONS preflight`) obligatoria antes de cualquier petición `POST` de origen cruzado que incluya cabeceras no simples (`Content-Type: application/json`).
  2. Flutter Web asigna en cada sesión de depuración un puerto HTTP efímero aleatorio (ej. `http://localhost:50870`).
  3. El middleware `CORSMiddleware` en `app/main.py` validaba exclusivamente orígenes estáticos mediante `settings.CORS_ORIGINS` (`http://localhost:4200`, etc.).
  4. Al no coincidir el origen dinámico de depuración, Starlette denegaba el preflight con `HTTP 400 Bad Request` (`Disallowed CORS origin`), provocando que el navegador bloqueara la llamada de red antes de emitir el `POST`.

### 5.2 Solución Arquitectónica Implementada
1. **Configuración de Patrón Regex para Orígenes de Desarrollo (`CORS_ORIGIN_REGEX`):**
   - En `app/core/config.py`, se adicionó el parámetro:
     ```python
     CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
     ```
   - En `app/main.py`, se enlazó dicho parámetro a `CORSMiddleware`:
     ```python
     app.add_middleware(
         CORSMiddleware,
         allow_origins=settings.CORS_ORIGINS,
         allow_origin_regex=settings.CORS_ORIGIN_REGEX,
         allow_credentials=True,
         allow_methods=["*"],
         allow_headers=["*"],
     )
     ```
   - En `Ec-backend/.env`, se declaró:
     ```env
     CORS_ORIGIN_REGEX=^https?://(localhost|127\.0\.0\.1)(:\d+)?$
     ```
2. **Impacto y Beneficio:**
   - Habilita la interoperabilidad transparente de Flutter Web (`localhost:*`), Angular (`localhost:4200`) y herramientas locales sin requerir reconfigurar puertos estáticos.
   - Preserva la seguridad estricta para entornos de producción mediante el filtro de dominios de `CORS_ORIGINS`.

### 5.3 Criterios de Aceptación CORS (Gherkin BDD)
```gherkin
Caraterística: Gestión de CORS Preflight para Canales Web y Flutter Web
  Como cliente web o Flutter Web en navegador
  Quiero que mis peticiones HTTP con payload JSON sean autorizadas por el preflight
  Para poder iniciar sesión y consumir los endpoints sin bloqueos del navegador

  Escenario: Solicitud pre-vuelo OPTIONS exitosa desde puerto local dinámico
    Dado que un cliente Flutter Web envía una petición "OPTIONS /api/v1/autenticacion/login"
    Con cabecera "Origin: http://localhost:50870"
    Y cabecera "Access-Control-Request-Method: POST"
    Cuando el backend procesa la solicitud con "CORSMiddleware"
    Entonces responde con código HTTP 200 OK
    Y la cabecera "Access-Control-Allow-Origin" devuelve "http://localhost:50870"
    Y la cabecera "Access-Control-Allow-Credentials" es "true".
```

---

## 6. Evidencias de Verificación y Cierre

1. **Backend (`Ec-backend`):** 28/28 pruebas unitarias y de integración pasando al 100% en `pytest` (`test_cu01_registrarse.py`, `test_cu02_iniciar_sesion.py`, `test_health.py`).
2. **Validación en Vivo contra Neon PostgreSQL:** Autenticación de usuario validada con actualización inmediata y atómica de `ultimo_acceso` en la base de datos en la nube.
3. **Frontend Web (`Ec-frontend`):** Compilación de producción con Angular CLI en 5.4s sin advertencias ni errores (`chunk-SNJJEDBX.js`). Proxy verificado hacia el backend en vivo.
4. **Aplicación Móvil (`Ec-mobile`):** 19/19 pruebas en verde en `flutter test` (DTOs, BLoC, Pantalla y Navegación) y 0 incidencias en `flutter analyze`.
5. **CORS Preflight:** Validado con código `200 OK` para orígenes dinámicos locales en Edge/Chrome.
