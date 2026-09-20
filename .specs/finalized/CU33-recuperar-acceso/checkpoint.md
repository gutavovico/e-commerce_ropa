# Puntos de Control y Verificación: CU33 - Recuperar Acceso de Cuenta / Recuperar Contraseña

**Caso de Uso:** CU33. Recuperar Acceso de Cuenta  
**Alcance:** Bloque 1 (Backend), Bloque 2 (Frontend Web), Bloque 3 (Mobile)  
**Estado:** 🟢 100% Verificado (Bloques 1, 2 y 3 Completados)  

---

## 1. Criterios de Aceptación Cuantitativos

| Checkpoint | Criterio de Verificación | Herramienta / Método | Condición de Aprobación | Estado Actual |
| :--- | :--- | :--- | :--- | :--- |
| **CP-1: Backend Tests** | Pruebas de solicitud, expiración, límite de intentos y cambio | `pytest` en `Ec-backend` | 100% pasando sin regresiones (>= 60 tests totales). | 🟢 Verificado (63/63 tests pasando) |
| **CP-2: Despacho SMTP Real** | Envío de correo y persistencia de códigos OTP | Pruebas de integración FastAPI | Códigos generados con hash SHA-256 y despachados vía SMTP con cabeceras RFC anti-spam. | 🟢 Verificado (Despacho SMTP exitoso con cabeceras RFC y plantilla limpia) |
| **CP-3: Fidelidad Visual Web** | Comparación pixel-match contra captura Desktop | Inspección de navegador | Coincidencia en insignia FS, tipografías, inputs, barras de fuerza y botón. | 🟢 Verificado (Fiel a Captura Desktop) |
| **CP-4: Compilación Web** | Compilación de bundle de producción Angular | `npm run build` en `Ec-frontend` | 0 errores de compilación TypeScript/SCSS. | 🟢 Verificado (0 errores, 17/17 tests en verde) |
| **CP-5: Fidelidad Visual Mobile** | Comparación visual contra captura Mobile | Ejecución en emulador/navegador | Coincidencia exacta con la segunda imagen provista (badge FS, inputs, 3 barras, botón, escudo). | 🟢 Verificado (Fiel a Captura Mobile) |
| **CP-6: Mobile Tests & Lint** | Tests automatizados y análisis estático Dart | `flutter test` y `flutter analyze` | 100% de tests en verde y 0 incidencias de linter. | 🟢 Verificado (42/42 tests pasando, 0 issues en analyze) |
| **CP-7: Seguridad de Credenciales** | Imposibilidad de acceso con clave antigua tras cambio | Test funcional de login | Rechazo con clave previa y acceso exitoso con la nueva clave. | 🟢 Verificado (Integración de Argon2id y revocación de sesión) |
