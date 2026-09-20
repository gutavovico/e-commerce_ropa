# Especificación Técnica Permanente: CU33 - Recuperar Acceso de Cuenta / Restablecer Contraseña

**Código:** CU33  
**Nombre:** Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `cu33_recuperar_acceso`  
**Actores:** Cliente, Administrador, Empleado (Cualquier Actor del Sistema)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Línea Base Permanente)  
**Estado:** 🟢 Aprobado y Promovido a Permanente  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Líneas 590-593, CU33: "Permite recuperar el acceso a la cuenta de cualquier actor").
- Referencia Visual y UX: Capturas adjuntas de alta fidelidad para Desktop Web y Mobile (`FS` monogram, 3 barras de fuerza, botón negro `ACTUALIZAR Y ACCEDER →`, escudo de seguridad).
- Servicio de Correo: Servidor SMTP de Gmail (`smtp.gmail.com:587` TLS) con contraseña de aplicación y cabeceras RFC 5322 / RFC 3834 para entrega garantizada en bandeja principal.

---

## 1. Definición Funcional y Reglas de Negocio

### 1.1 Propósito y Alcance
Proporcionar a cualquier usuario registrado en la plataforma omnicanal FashionStore un mecanismo criptográficamente seguro, autónomo y accesible para restablecer sus credenciales de acceso cuando las haya olvidado o su cuenta haya sido bloqueada temporalmente.

### 1.2 Reglas de Negocio Estrictas

1. **Protección Contra Enumeración de Usuarios (Anti-User Enumeration):**
   - El endpoint de solicitud de código (`POST /api/v1/autenticacion/recuperar-password/solicitar`) retorna **siempre** una respuesta uniforme con código HTTP `200 OK` tanto si el correo existe como si no existe en la base de datos.
   - Mensaje estándar: *"Si el correo electrónico se encuentra registrado en nuestra plataforma, recibirás un código de verificación de 6 dígitos en los próximos instantes."*

2. **Generación Criptosegura de Código OTP:**
   - Código numérico de exactamente **6 dígitos decimales** (rango `100000` a `999999`), generado mediante el generador criptográfico del sistema (`secrets.randbelow(900000) + 100000`).

3. **Almacenamiento Seguro del OTP en Base de Datos (Neon PostgreSQL):**
   - El código en texto plano **nunca** se persiste en disco ni en base de datos.
   - Se almacena su digest criptográfico **SHA-256** (`codigo_hash`, longitud 64 caracteres) en la tabla `fashionstore.codigos_recuperacion`.
   - Campos: `id_codigo`, `id_usuario` (FK CASCADE), `codigo_hash`, `expira_en`, `usado`, `intentos_fallidos`, `ip_solicitante`, `creado_en`.

4. **Políticas Temporales y de Intentos:**
   - **TTL del Código:** 15 minutos exactos desde su emisión.
   - **Límite de Intentos Fallidos:** Máximo 5 intentos incorrectos. Al quinto fallo consecutivo, el registro se marca como `usado = True` para anular ataques de fuerza bruta.
   - **Cooldown de Reenvío (Rate Limiting):** Intervalo mínimo de 60 segundos entre solicitudes para un mismo usuario.
   - **Consumo Atómico y Único:** Un código solo puede utilizarse una vez. Al solicitar un nuevo código, todos los códigos previos activos del usuario quedan invalidados.

5. **Complejidad y Hashing de Contraseña:**
   - Longitud mínima de 8 caracteres, conteniendo al menos una letra (A-Z) y un número (0-9).
   - Coincidencia exacta entre `nueva_password` y `confirmar_password`.
   - Hashing mediante algoritmo **Argon2id** (`argon2-cffi`).
   - Revocación preventiva de sesiones activas en la lista negra en memoria (`TokenBlacklistService`).

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + PostgreSQL + SMTP)

### 2.1 Modelo ORM (`app/modules/autenticacion_seguridad/modelos.py`)
```python
class CodigoRecuperacionORM(Base):
    __tablename__ = "codigos_recuperacion"
    __table_args__ = {"schema": "fashionstore"}

    id_codigo: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    id_usuario: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("fashionstore.usuarios.id_usuario", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    codigo_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    expira_en: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    usado: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    intentos_fallidos: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    ip_solicitante: Mapped[Optional[str]] = mapped_column(String(45), nullable=True)
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    usuario: Mapped["UsuarioORM"] = relationship("UsuarioORM")
```

### 2.2 Migración Alembic
- Archivo: `alembic/versions/0002_codigos_recuperacion.py`.
- Aplica creación de tabla con esquema `fashionstore` e índices sobre `id_usuario` y `codigo_hash`.

### 2.3 Servicio Asíncrono de Correo y Entregabilidad Anti-Spam (`app/core/email_service.py`)
- Empleo de `smtplib` sobre `asyncio.to_thread` con STARTTLS sobre el puerto 587.
- **Cabeceras RFC 5322 & RFC 3834:**
  - `Message-ID`: `<id@dominio>` generado con `email.utils.make_msgid(domain=dominio)`.
  - `Date`: Fecha RFC 2822 generada con `email.utils.formatdate(localtime=True)`.
  - `From` y `Reply-To`: Codificación RFC 2047 con `email.utils.formataddr`.
  - `Subject`: Codificado en UTF-8 con `Header` (`Tu código de recuperación Fashion Store: XXX XXX`).
  - `Auto-Submitted: auto-generated`, `X-Auto-Response-Suppress: All`, `Precedence: bulk`.
- **Plantilla HTML Limpia y Versión en Texto Plano:**
  - Estética Haute Couture con monograma **FS**, código formateado `[ 849 201 ]` y tiempo de expiración.
  - Neutralización de términos de riesgo de phishing y sincronización exacta con texto plano.

### 2.4 Contrato de API REST
1. `POST /api/v1/autenticacion/recuperar-password/solicitar`
   - **Body:** `{"email": "cliente@fashionstore.com"}`
   - **Respuesta 200 OK:** `{"mensaje": "...", "tiempo_espera_segundos": 60}`
2. `POST /api/v1/autenticacion/recuperar-password/restablecer`
   - **Body:** `{"email": "...", "codigo": "849201", "nueva_password": "...", "confirmar_password": "..."}`
   - **Respuesta 200 OK:** `{"mensaje": "Contraseña restablecida exitosamente.", "exito": true, "codigo_evento": "PASSWORD_RESTABLECIDA"}`
   - **Errores:** `400 Bad Request` (código inválido/expirado/intentos superados), `422 Unprocessable Entity` (complejidad débil o contraseñas no coincidentes).

---

## 3. Arquitectura de Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Diseño Visual Fiel a la Captura Desktop
- **Fondo:** Fondo difuminado de boutique con viñeta oscura elegante (`/atelier_bg.jpg`).
- **Badge Superior FS:** Monograma blanco flotante `FS` en relieve.
- **Tarjeta Central:** Bordes `rounded-[28px]`, sombra suave:
  - Rótulos: `— RESTABLECER ACCESO —` y `FASHION STORE`.
  - Paso 1 (Solicitud): Input de correo con validación y botón de envío.
  - Paso 2 (Restablecimiento):
    - Campo `CÓDIGO DE VERIFICACIÓN (6 DÍGITOS)` con enlace `Reenviar` (con temporizador reactivo de 60s) e icono `[123]`.
    - Campo `NUEVA CONTRASEÑA` con candado, toggle de visibilidad y medidor visual de 3 barras horizontales (rojo, ámbar, verde).
    - Campo `CONFIRMAR CONTRASEÑA` con toggle de visibilidad.
    - Botón de acción principal: `ACTUALIZAR Y ACCEDER →` (negro, ancho completo, con spinner).
    - Divisor con punto central `•`, enlace `Regresar a Iniciar sesión` y escudo inferior.
- **Rutas:** `/recuperar-password` y `/recuperar-acceso` conectadas en `app.routes.ts`.
- **Enlace en Login:** Conectado en `¿Olvidaste tu contraseña?` de `login.component.html`.

---

## 4. Arquitectura de Aplicación Móvil (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Diseño Visual Fiel a la Captura Mobile
- `PantallaRecuperarPassword` adaptada a teléfonos móviles:
  - Badge superior redondeado flotante con monograma **FS**.
  - Tarjeta central blanca `BorderRadius.circular(28)` con sombra profunda.
  - Subtítulo `— RESTABLECER ACCESO —` y título `FASHION STORE`.
  - Campo de código con acción `REENVIAR` a la derecha (reactivo a cooldown).
  - Campo de nueva contraseña con candado, toggle de ojo y medidor de 3 barras animadas.
  - Campo de confirmación de contraseña.
  - Botón principal negro: `ACTUALIZAR Y ACCEDER →`.
  - Divisor con punto `•`, enlace `regresar a Iniciar sesión` y escudo de seguridad inferior.

### 4.2 BLoC y Estado Reactivo
- `RecuperarPasswordBloc` (`ChangeNotifier` con estados sellados):
  - `RecuperarPasswordInicial`, `RecuperarPasswordCargando`, `CodigoSolicitadoExitoso`, `RestablecimientoExitoso`, `RecuperarPasswordError`.
  - Manejo de cuenta regresiva de 60 segundos segundo a segundo con cancelación limpia en `dispose()`.
  - Cálculo instantáneo de complejidad de contraseña (niveles 0 a 3).
- **Conexión en Login:** Navegación desde `¿Olvidaste tu contraseña?` en `pantalla_login.dart`.

---

## 5. Matriz de Verificación y Calidad

| Capa / Aplicación | Método de Prueba | Cobertura / Criterio | Resultado |
| :--- | :--- | :--- | :--- |
| **Backend (`Ec-backend`)** | `pytest` | 63 tests acumulados (11 de CU33) | 🟢 **63/63 tests pasando (100%)** |
| **Backend (`Ec-backend`)** | Despacho SMTP Real | Handshake STARTTLS y envío a Gmail | 🟢 **Despacho real verificado a Inbox** |
| **Frontend Web (`Ec-frontend`)** | `ng test` (Vitest) | 17 tests unitarios y de componentes | 🟢 **17/17 tests pasando (100%)** |
| **Frontend Web (`Ec-frontend`)** | `npm run build` | Compilación de bundle de producción | 🟢 **0 errores, bundle en 3.7s** |
| **Mobile (`Ec-mobile`)** | `flutter test` | 42 tests unitarios, BLoC y widgets | 🟢 **42/42 tests pasando (100%)** |
| **Mobile (`Ec-mobile`)** | `flutter analyze` | Análisis estático y linter oficial | 🟢 **0 issues found** |
| **Seguridad de Credenciales** | Test funcional de login | Rechazo con contraseña antigua y login con nueva clave | 🟢 **Verificado con Argon2id** |
