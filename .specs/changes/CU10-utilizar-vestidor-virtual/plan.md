# Plan Técnico — CU10: Utilizar Vestidor Virtual (Dos Motores)

## Estrategia por Bloques

1. **Bloque 1 — Backend (`Ec-backend`):**
   - Módulo `app/modules/catalogo/cu10_vestidor_virtual/`.
   - `modelos.py`: `SesionVestidorORM` con campos `motor` y `duracion_segundos`.
   - `esquemas.py`: `SesionVestidorCrearIn`, `TokenVestidorDecartOut`, `SesionVestidorOut`.
   - `integraciones/decart_service.py`: Cliente seguro para solicitar tokens de corta duración a la API de Decart (`/v1/client-tokens`).
   - `router.py`: `POST /api/v1/vestidor/token` (sin cuerpo, solo header `Authorization: Bearer <jwt>`) y `POST /api/v1/vestidor/sesion`.
   - Tests: `tests/modules/catalogo/test_cu10_vestidor.py`.

2. **Bloque 2 — Frontend Web (`Ec-frontend`):**
   - Modal interactivo de vestidor virtual con selector de motor (Local Canvas / Simulación).
   - Servicio `vestidor.service.ts` con llamada a `/token` (sin payload) y registro de sesión.

3. **Bloque 3 — Móvil (`Ec-mobile`):**
   - **Motor 1 Local:** Integración de `google_mlkit_pose_detection` en `pantalla_vestidor_ar.dart`, detección de puntos anatómicos y deformación 2D sobre torso.
   - **Motor 2 Realista:** WebView con página HTML que incluye `@decartai/sdk` y streaming en tiempo real mediante el SDK de Decart (@decartai/sdk) usando el token efímero del backend.
   - **Fallback:** Manejo de excepciones para regresar fluidamente al Motor 1 ante cualquier fallo de red o créditos en Decart.
   - Tests: `test/cu10_vestidor_test.dart`.
