# Checkpoints — CU10: Utilizar Vestidor Virtual

| Gate | Estado | Notas |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada | Delta del Bloque 3: parámetro `canal` en `POST /vestidor/token` (ver `spec.md` §3.1). |
| 1 — Backend | 🟢 Completo | `pytest` CU10 18/18 (canal móvil, timeout de 10 s, restricción de origen). |
| 2 — Web | 🟢 Completo | Motor 1 sin seguimiento corporal por decisión del usuario (no se amplía el alcance web). |
| 3 — Mobile | 🟡 Implementado, pendiente de prueba en dispositivo | Ver «Pendiente». |

## Mobile (Bloque 3)

- [x] **CP-M01** DTO con `fromJson` probados con payloads literales del backend.
- [x] **CP-M02** `POST /vestidor/token?canal=movil` sin cuerpo y con JWT; 503 → `VestidorException` con `DECART_NO_DISPONIBLE`.
- [x] **CP-M03** Motor 1: cámara frontal + ML Kit; la prenda (PNG transparente de `modelo_ar_url`) sigue la línea de hombros (posición, escala y giro suavizados); sin cuerpo detectado, espera centrada con indicación.
- [x] **CP-M04** Motor 2: WebView con `@decartai/sdk@0.2.14`; token por marcación, chequeo de conectividad, cámara con `model.width/height/fps`, prompt de sustitución, prenda aplanada sobre blanco.
- [x] **CP-M05** Fallback al Motor 1 (503, red crítica, cámara, error o fin de sesión, 45 s sin vídeo); límite comercial de 60 s.
- [x] **CP-M06** Una sola sesión registrada (`dispositivo: app_flutter`, `motor: ia` si Decart llegó a emitir, `genero_interes: true` al añadir a la bolsa).
- [x] **CP-M07** Hub-and-Spoke: pantalla hoja con `BackButton`, sin `BottomNavigationBar` de navegación; barra de acción inferior admitida.
- [x] **CP-M08** Sin `modelo_ar_url` o sin sesión, la ficha no abre el vestidor y lo explica.
- [x] **CP-M09** `dart analyze` → «No issues found!» · `flutter test` 258/258.
- [x] **CP-M10** Permisos nativos: `CAMERA` (Android), `NSCameraUsageDescription` e iOS 15.5 (mínimo de ML Kit).

## Pendiente

- Prueba en dispositivo físico Android/iOS (la skill de Decart lo exige: el emulador no tiene WebRTC real).
- Producción: los recursos `/ar/...` se resuelven contra `WEB_URL` (por defecto `https://fashionstorefront.vercel.app`); `camiseta_basica_amarilla*.png` debe estar desplegado en Vercel.
