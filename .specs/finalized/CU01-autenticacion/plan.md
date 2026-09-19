# Plan de Implementación SDD: Refactorización Visual y de UX (Fiel a Mockups)

**Caso de Uso:** CU01. Registrarse  
**Versión:** 1.1.0  
**Fecha de Cierre:** 2026-09-19  
**Estado:** 🟢 Completado y Verificado  
**Promovido a:** `.specs/modules/autenticacion_seguridad/CU01-registrarse.md`

---

## 1. Estrategia de Implementación por Capas

### Fase 1: Especificación y Criterios de Aceptación (Completada en `spec.md`)
- Definición de jerarquía visual (Split 50/50 en Desktop, Vertical Hero Card en Mobile).
- Tokens de diseño: Paleta Light Luxury (`#FFFFFF`, `#F5F5F5`, `#000000`, `#C5A059`), tipografía `Outfit`, inputs a 48px con iconos.
- Criterios BDD en formato Gherkin para medidor de contraseña, desglose de nombre completo y validación de términos.

### Fase 2: Frontend Web (`Ec-frontend` - Angular 19+ & Tailwind CSS)
Ubicación: `Ec-frontend/src/app/modules/autenticacion_seguridad/cu01_registrarse/`
- Layout split screen 50/50 responsive (`grid grid-cols-1 lg:grid-cols-2`).
- Panel izquierdo editorial con fotografía de atelier, cita de alta costura *"La pureza del corte. El lujo del tiempo."* y bloques de valor exclusivos.
- Formulario derecho luminoso con badge superior `[🔒 REGISTRO CIFRADO]`.
- Campo unificado `NOMBRE COMPLETO`, correo con icono de sobre, contraseña con medidor de 4 segmentos reactivo y desglose automático para el backend.
- Checkboxes de Términos y Privacidad (con validación de obligatoriedad) y Notificaciones.
- Botón de acción `CREAR CUENTA →` en negro sólido obsidian con microinteracción de carga.
- Compilación exitosa con `npm run build`.

### Fase 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x)
Ubicación: `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu01_registrarse/`
- Tarjeta hero superior con imagen boutique, esquinas redondeadas (`ClipRRect` 16px), badge circular de candado translúcido y lema *"REGISTRO PRIVADO"*.
- Encabezado centrado de marca *"BIENVENIDO A FASHION STORE"*.
- Campos de texto estilizados en gris claro con iconos vectoriales de línea.
- Widget interactivo del medidor de contraseña en 4 barras horizontales (`3/4 ROBUSTA`).
- Checkboxes de alta costura y botón negro `CREAR CUENTA EXCLUSIVA →`.
- Píldora inferior de seguridad `256-BIT SSL SECURED • PRIVACIDAD GARANTIZADA`.
- `flutter analyze`: 0 errores / 0 advertencias (`No issues found!`).
- `flutter test`: 7/7 pruebas unitarias pasando al 100%.

### Fase 4: Backend API (`Ec-backend` - FastAPI & Neon PostgreSQL)
- Consolidación de imports en `app/main.py` y `pyproject.toml`.
- Conexión configurada con Neon Serverless vía listener SQLAlchemy compatible con PgBouncer.
- Mapeo estricto del enum `fashionstore.rol_usuario` en `UsuarioORM`.
- 15/15 pruebas unitarias y de integración pasando al 100% con pytest.
