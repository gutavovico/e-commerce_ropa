# Especificación Técnica: CU33 - Recuperar Acceso de Cuenta / Recuperar Contraseña

**Código:** CU33  
**Nombre:** Recuperar Acceso de Cuenta (Verificación OTP por Correo SMTP y Restablecimiento de Credenciales)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `cu33_recuperar_acceso`  
**Actores:** Cliente, Administrador, Empleado (Cualquier Actor del Sistema)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Propuesta Activa de Cambio)  
**Estado:** 🟡 En Espera de Aprobación Explícita del Usuario (Fase de Especificación y Planificación)  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Líneas 590-593, CU33: "Permite recuperar el acceso a la cuenta de cualquier actor").
- Referencia Visual y UX: Capturas adjuntas de alta fidelidad para Desktop Web y Mobile.
- Servicio de Correo: Servidor SMTP de Gmail (`smtp.gmail.com:587` TLS) con emisor `fashionstore321@gmail.com` y credencial en `.env` (`SMTP_PASSWORD=PasswordSegura321`).

---

## ⛔ GATE DE APROBACIÓN OBLIGATORIO (STRICT STOP)
> [!CAUTION]
> **PROHIBICIÓN ESTRICTA DE CÓDIGO FUNCIONAL:**
> Queda terminantemente prohibido generar, editar o ejecutar código fuente de producción o de pruebas (`.py`, `.ts`, `.dart`, etc.) en cualquiera de las tres aplicaciones (`Ec-backend`, `Ec-frontend`, `Ec-mobile`) hasta que la presente especificación técnica formal y el plan de trabajo sean revisados y aprobados explícitamente por el usuario.

---

## 1. Reglas de Negocio y Seguridad de la Información

1. **Protección Contra Enumeración de Usuarios (Anti-User Enumeration):**
   - El endpoint `POST /api/v1/autenticacion/recuperar-password/solicitar` responderá invariablemente con `200 OK` y el mismo mensaje neutro tanto si el email existe como si no.
   - Mensaje estándar: *"Si el correo electrónico se encuentra registrado en nuestra plataforma, recibirás un código de verificación de 6 dígitos en los próximos instantes."*

2. **Generación Criptosegura de Código OTP:**
   - Código numérico de exactamente 6 dígitos (`100000` - `999999`), generado con `secrets.SystemRandom` de Python.

3. **Almacenamiento Seguro del Código en Base de Datos:**
   - Tabla: `fashionstore.codigos_recuperacion`.
   - Se almacena el hash SHA-256 del OTP (`codigo_hash`), no el valor en texto plano.
   - Campos: `id_codigo`, `id_usuario`, `codigo_hash`, `expira_en`, `usado`, `intentos_fallidos`, `ip_solicitante`, `creado_en`.

4. **Políticas de Expiración, Límite de Intentos y Caducidad:**
   - TTL: 15 minutos desde su emisión.
   - Intentos máximos: 5 intentos fallidos antes de invalidar el código (`usado = True`).
   - Cooldown de reenvío: Mínimo 60 segundos entre solicitudes para un mismo correo.
   - Consumo atómico de un solo uso.

5. **Complejidad y Hashing de Contraseña:**
   - Mínimo 8 caracteres, al menos una letra y un dígito.
   - Coincidencia exacta de contraseñas.
   - Algoritmo de hashing: **Argon2id** (`argon2-cffi`).
   - Revocación de sesiones activas previas en lista negra de tokens.

---

## 2. Bloque 1: Backend (`Ec-backend` - FastAPI + PostgreSQL + SMTP)

### 2.1 Configuración Centralizada (`app/core/config.py` y `.env`)
```python
SMTP_SERVER: str = "smtp.gmail.com"
SMTP_PORT: int = 587
SMTP_USER: str = "fashionstore321@gmail.com"
SMTP_PASSWORD: str = "PasswordSegura321"
SMTP_USE_TLS: bool = True
SMTP_FROM_NAME: str = "Fashion Store Atelier"
OTP_EXPIRE_MINUTES: int = 15
OTP_MAX_ATTEMPTS: int = 5
OTP_RESEND_COOLDOWN_SECONDS: int = 60
```

### 2.2 Modelo ORM (`app/modules/autenticacion_seguridad/modelos.py`)
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

### 2.3 Servicio Asíncrono de Correo y Entregabilidad Anti-Spam (`app/core/email_service.py`)
- Empleo de `smtplib` en `asyncio.to_thread` con TLS sobre puerto 587.
- **Cabeceras RFC 5322 & RFC 3834 para evitar carpeta de Spam:**
  - `Message-ID`: Identificador único criptográfico generado mediante `email.utils.make_msgid(domain=dominio)`.
  - `Date`: Formato RFC 2822 mediante `email.utils.formatdate(localtime=True)`.
  - `From` y `Reply-To`: Con codificación de nombres según RFC 2047 mediante `email.utils.formataddr`.
  - `Subject`: Codificado explícitamente en UTF-8 con `Header` y asunto contextualizado (`Tu código de recuperación Fashion Store: XXX XXX`).
  - `Auto-Submitted: auto-generated`: Identifica al mensaje como notificación transaccional legítima del sistema.
  - `X-Auto-Response-Suppress: All` y `Precedence: bulk`.
- **Plantilla HTML Limpia y Versión en Texto Plano:**
  - Eliminación de términos gatillo de filtros de phishing ("Seguridad Criptográfica 256-Bit SSL", emojis en celdas de tablas).
  - Texto plano sincronizado al 100% con la versión HTML para neutralizar advertencias de discrepancia MIME multipart.
  - Diseño responsive Haute Couture con monograma **FS**, código formateado `[ 849 201 ]` y tiempo de expiración.

### 2.4 Esquemas Pydantic (`app/modules/autenticacion_seguridad/cu33_recuperar_acceso/esquemas.py`)
- `SolicitarCodigoIn`: `email: EmailStr`.
- `SolicitarCodigoOut`: `mensaje: str`, `tiempo_espera_segundos: int = 60`.
- `RestablecerPasswordIn`: `email: EmailStr`, `codigo: str (6 dígitos)`, `nueva_password: str (>=8 caracteres, letras y números)`, `confirmar_password: str`.
- `RestablecerPasswordOut`: `mensaje: str`, `exito: bool = True`, `codigo_evento: str = "PASSWORD_RESTABLECIDA"`.

### 2.5 Endpoints REST
1. `POST /api/v1/autenticacion/recuperar-password/solicitar`
2. `POST /api/v1/autenticacion/recuperar-password/restablecer`

---

## 3. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### 3.1 Diseño Visual Fiel a la Captura Desktop
- Fondo difuminado de tienda de alta costura (`backdrop-blur-sm`).
- Tarjeta central blanca curvada con sombra delicada.
- Badge superior con monograma `FS`.
- Rótulos: `— RESTABLECER ACCESO —` y `FASHION STORE`.
- Texto de ayuda: *"Introduce el código enviado a tu correo para restablecer tu contraseña y proteger tu cuenta."*
- Campos:
  1. `CÓDIGO DE VERIFICACIÓN (6 DÍGITOS)` con enlace `Reenviar` a la derecha (con temporizador reactivo), icono `[123]`, placeholder `ej. 849 201`.
  2. `NUEVA CONTRASEÑA` con icono de candado, placeholder `Mínimo 8 caracteres (A-Z, 0-9)`, toggle de visibilidad y medidor visual de 3 barras horizontales.
  3. `CONFIRMAR CONTRASEÑA` con icono de repetición, placeholder `Repite tu nueva contraseña` y toggle de visibilidad.
- Botón: `ACTUALIZAR Y ACCEDER →` (negro, ancho completo, bordes redondeados).
- Divisor con punto central, enlace *"Regresar a Iniciar sesión"* e icono de escudo de seguridad.
- Ruta: `/recuperar-password`. Enlace activado desde `¿Olvidaste tu contraseña?` en login.

---

## 4. Bloque 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x + BLoC)

### 4.1 Diseño Visual Fiel a la Captura Mobile
- Pantalla `PantallaRecuperarPassword` con adaptación responsiva:
  - Insignia `FS` en contenedor superior.
  - Subtítulo `— RESTABLECER ACCESO —` y título `FASHION STORE`.
  - Input `CÓDIGO DE VERIFICACIÓN (6 DÍGITOS)` con botón `REENVIAR`.
  - Input `NUEVA CONTRASEÑA` con 3 barras dinámicas de fortaleza.
  - Input `CONFIRMAR CONTRASEÑA`.
  - Botón `ACTUALIZAR Y ACCEDER →`.
  - Divisor con punto, enlace `"regresar a Iniciar sesión"` y escudo inferior.

### 4.2 BLoC Reactivo
- `RecuperarPasswordBloc`:
  - Eventos: `SolicitarCodigoSubmitted`, `ReenviarCodigoSubmitted`, `RestablecerPasswordSubmitted`, `PasswordChanged`.
  - Estados: `RecuperarPasswordInicial`, `SolicitandoCodigoCargando`, `CodigoEnviadoExitoso`, `RestableciendoPasswordCargando`, `RestablecimientoExitoso`, `RecuperarPasswordError`.
- Conexión desde `PantallaLogin`: navegación limpia al pulsar `¿Olvidaste tu contraseña?`.
