# Plan de Implementación: CU33 - Recuperar Acceso de Cuenta / Recuperar Contraseña

**Caso de Uso:** CU33. Recuperar Acceso de Cuenta  
**Alcance:** Bloque 1 (Backend), Bloque 2 (Frontend Web), Bloque 3 (Mobile)  
**Estado:** 🟢 Bloques 1, 2 y 3 100% Implementados y Verificados (Listo para Promoción a Especificación Permanente)  

---

## 1. Secuencia de Fases y Bloques de Trabajo

### Fase 1: Bloque 1 - Backend (`Ec-backend`) [🟢 COMPLETADO]
1. **Configuración SMTP:** Añadida configuración en `app/core/config.py` y `Ec-backend/.env`.
2. **Entidad ORM y Migración Alembic:**
   - Creado `CodigoRecuperacionORM` en `modelos.py`.
   - Aplicada migración `0002_codigos_recuperacion.py` en Neon PostgreSQL.
3. **Servicio SMTP y Anti-Spam:** Implementado `email_service.py` con plantilla HTML Haute Couture, cabeceras RFC 5322 / RFC 3834 y soporte STARTTLS.
4. **Módulo de Recuperación:** Implementados `esquemas.py`, `servicio.py`, `router.py` y montado en API REST.
5. **Verificación Automatizada:** 63/63 tests pasando en `pytest` (11 nuevos de CU33 + 52 existentes).

### Fase 2: Bloque 2 - Frontend Web (`Ec-frontend`) [🟢 COMPLETADO]
1. **Servicio Angular:** Creado `recuperar-password.service.ts` con consumo de endpoints de solicitud y restablecimiento.
2. **Componente Visual:** Creado `recuperar-password.component.ts` y `.html` con estricta fidelidad a la captura de diseño Desktop.
3. **Validación Reactiva:** Medidor de 3 barras segmentadas de fortaleza y temporizador de reenvío de 60 segundos.
4. **Enrutamiento:** Conectada ruta `/recuperar-password` en `app.routes.ts` y enlace activo en `login.component.html`.
5. **Pruebas y Build:** 17/17 tests pasando en Vitest y bundle de producción compilado limpiamente en 3.7s con `npm run build`.

### Fase 3: Bloque 3 - Aplicación Móvil (`Ec-mobile`) [🟢 COMPLETADO]
1. **Capa de Datos:** Implementados DTOs (`recuperar_password_dto.dart`), datasource remoto y repositorio para recuperación de acceso.
2. **BLoC:** Creado `RecuperarPasswordBloc` con estados inmutables, temporizador de 60s reactivo y cálculo de fortaleza de contraseña en tiempo real.
3. **Pantalla Flutter:** Creada `PantallaRecuperarPassword` reproduciendo milimétricamente la segunda imagen provista para Mobile (tarjeta, monograma FS, inputs, 3 barras de fuerza, botón negro `ACTUALIZAR Y ACCEDER →` y escudo).
4. **Enlace en Login:** Conectado `¿Olvidaste tu contraseña?` en `pantalla_login.dart`.
5. **Pruebas y Análisis:** 42/42 tests pasando en `flutter test` y 0 incidencias en `flutter analyze`.
