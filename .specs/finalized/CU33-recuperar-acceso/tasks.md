# Tareas de Implementación: CU33 - Recuperar Acceso de Cuenta / Recuperar Contraseña

**Caso de Uso:** CU33. Recuperar Acceso de Cuenta  
**Alcance:** Bloque 1 (Backend), Bloque 2 (Frontend Web), Bloque 3 (Mobile)  
**Estado:** 🟢 100% Implementado y Verificado (Listo para Promoción a Especificación Permanente)

---

## Bloque 1: Backend (`Ec-backend`)

- [x] **T1.1: Configuración de Entorno y Variables SMTP**
  - [x] Añadir `SMTP_SERVER`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_USE_TLS` en `app/core/config.py`.
  - [x] Registrar credenciales en `Ec-backend/.env`.

- [x] **T1.2: Modelo ORM y Migración Alembic**
  - [x] Definir `CodigoRecuperacionORM` en `app/modules/autenticacion_seguridad/modelos.py`.
  - [x] Crear migración Alembic `0002_codigos_recuperacion.py` y aplicarla en Neon PostgreSQL.

- [x] **T1.3: Servicio de Correo SMTP y Plantilla Haute Couture (Optimización Anti-Spam)**
  - [x] Implementar `app/core/email_service.py` con envío asíncrono y STARTTLS.
  - [x] Diseñar plantilla HTML responsive con código OTP destacado y versión en texto plano.
  - [x] Incorporar cabeceras RFC 5322 y RFC 3834 (`Message-ID`, `Date`, `Reply-To`, `Auto-Submitted`, `Precedence`) y limpiar términos de riesgo de phishing para garantizar entrada en bandeja principal (Inbox).

- [x] **T1.4: Lógica de Negocio y Router de Recuperación**
  - [x] Crear `esquemas.py` con validaciones de 6 dígitos y complejidad de contraseña.
  - [x] Crear `servicio.py` con generación de código mediante `secrets`, hashing SHA-256, validación de TTL y límite de intentos.
  - [x] Crear `router.py` con endpoints `POST /recuperar-password/solicitar` y `POST /recuperar-password/restablecer`.
  - [x] Montar el router en `app/modules/autenticacion_seguridad/router.py`.

- [x] **T1.5: Pruebas Automatizadas Pytest**
  - [x] Crear `test_cu33_recuperar_acceso.py` cubriendo escenarios de éxito, error de código, expiración y límite de intentos.
  - [x] Validar suite completa con `pytest` sin regresiones (63/63 tests pasando).

---

## Bloque 2: Frontend Web (`Ec-frontend`)

- [x] **T2.1: Servicio HTTP de Recuperación de Acceso**
  - [x] Crear `recuperar-password.service.ts` con llamadas a los endpoints de solicitud y restablecimiento.

- [x] **T2.2: Componente Standalone y Maquetación Visual**
  - [x] Crear `recuperar-password.component.ts` y `.html` reproduciendo fielmente la imagen Web (badge FS, campos, 3 barras de fuerza, botón `ACTUALIZAR Y ACCEDER →`, escudo inferior).
  - [x] Implementar validador de fortaleza de contraseña en vivo (3 barras de progreso).
  - [x] Implementar temporizador de cuenta regresiva para el enlace `Reenviar`.

- [x] **T2.3: Enrutamiento y Enlace en Login**
  - [x] Configurar ruta `/recuperar-password` en `app.routes.ts`.
  - [x] Conectar enlace `¿Olvidaste tu contraseña?` en `login.component.html`.

- [x] **T2.4: Pruebas y Compilación**
  - [x] Crear pruebas unitarias del componente y servicio con Vitest (17/17 tests pasando).
  - [x] Validar compilación de producción limpia con `npm run build` (0 errores).

---

## Bloque 3: Aplicación Móvil (`Ec-mobile`)

- [x] **T3.1: Capa de Datos y Repositorio en Flutter**
  - [x] Crear DTOs de petición y respuesta para recuperación de contraseña (`recuperar_password_dto.dart`).
  - [x] Crear datasource remoto y repositorio para consumir los endpoints de backend (`recuperar_password_remoto_datasource.dart`, `recuperar_password_repositorio.dart`).

- [x] **T3.2: BLoC de Recuperación de Acceso**
  - [x] Crear `RecuperarPasswordBloc` con estados inmutables, timer reactivo de cooldown y cálculo de fortaleza de contraseña (`recuperar_password_bloc.dart`).

- [x] **T3.3: Pantalla Móvil de Recuperación de Contraseña**
  - [x] Crear `PantallaRecuperarPassword` con diseño idéntico a la captura móvil (monograma FS, inputs, 3 barras de fortaleza, botón negro `ACTUALIZAR Y ACCEDER →`, divisor con punto y escudo).
  - [x] Integrar navegación en `¿Olvidaste tu contraseña?` de `PantallaLogin`.

- [x] **T3.4: Pruebas y Análisis Estático**
  - [x] Crear tests de DTOs, tests unitarios de BLoC y tests de widgets en `test/` (42/42 tests pasando).
  - [x] Ejecutar `flutter analyze` asegurando 0 advertencias / 0 errores.
