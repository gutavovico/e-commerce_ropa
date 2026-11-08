# Tareas — CU10: Utilizar Vestidor Virtual (Dos Motores: Local e IA Decart)

## Bloque 1 — Backend (`Ec-backend`)

- [x] **T-BE-01:** Crear modelo `SesionVestidorORM` en `app/modules/catalogo/cu10_vestidor_virtual/modelos.py` con columnas `motor` y `duracion_segundos`.
- [x] **T-BE-02:** Crear esquemas Pydantic en `esquemas.py` (`SesionVestidorCrearIn`, `TokenVestidorDecartOut`, `SesionVestidorOut`).
- [x] **T-BE-03:** Implementar cliente de integración `DecartService` en `app/integrations/decart_service.py` con método `generar_token_cliente()`.
- [x] **T-BE-04:** Implementar `repositorio.py` y `servicio.py` con validación de `modelo_ar_url` y persistencia de sesiones AR.
- [x] **T-BE-05:** Implementar `router.py` con `POST /api/v1/vestidor/token` (sin cuerpo en la petición, solo autenticación Bearer JWT; la app obtiene la imagen de la prenda del catálogo) y `POST /api/v1/vestidor/sesion`, y montarlo en `app/modules/catalogo/router.py`.
- [x] **T-BE-06:** Crear suite de pruebas en `tests/modules/catalogo/test_cu10_vestidor.py` validando registro de sesión (motor local e ia) y emisión de tokens con manejo de errores (401, 503).

---

## Bloque 2 — Frontend Web (`Ec-frontend`)

- [x] **T-FE-01:** Crear DTOs de TypeScript en `src/app/modules/catalogo/cu10_vestidor_virtual/modelos/vestidor.dto.ts`.
- [x] **T-FE-02:** Implementar `vestidor.service.ts` con soporte para `obtenerTokenDecart()` (sin payload) y `registrarSesion()`.
- [x] **T-FE-03:** Actualizar `ModalVestidorArComponent` para admitir simulación textil y soporte de probador interactivo.
- [x] **T-FE-04:** Integrar el modal en `ProductoDetalleComponent`.
- [x] **T-FE-05:** Pruebas unitarias de componentes y servicios.

---

## Bloque 3 — Móvil (`Ec-mobile`)

- [x] **T-MO-01:** Modelos DTO Dart en `lib/src/modulos/catalogo/cu10_vestidor_virtual/datos/modelos/vestidor_dto.dart` (`TokenVestidorDto`, `SesionVestidorCrearDto`, `SesionVestidorDto`, enum `MotorVestidor`).
- [x] **T-MO-02:** Datasource HTTP `datos/datasources/vestidor_api.dart`: `POST /token?canal=movil` (sin payload), `POST /sesion` y descarga del recurso de la prenda.
- [x] **T-MO-03:** **Motor 1 Local** en `presentacion/widgets/motor_local_camara.dart`: cámara frontal + `google_mlkit_pose_detection`; geometría pura en `dominio/ajuste_prenda.dart` (traducción de coordenadas, escala por anchura de hombros, giro y suavizado).
- [x] **T-MO-04:** **Motor 2 Realista** en `presentacion/widgets/motor_realista_webview.dart` + `assets/vestidor/decart_vton.html` (`@decartai/sdk@0.2.14` desde jsDelivr), token por marcación vía canal `Vestidor`, prenda aplanada sobre blanco (`dominio/recurso_prenda.dart`).
- [x] **T-MO-05:** Fallback automático (`presentacion/bloc/vestidor_bloc.dart`): 503 del token, red crítica, cámara, error/fin de sesión, 45 s sin vídeo; límite comercial de 60 s.
- [x] **T-MO-06:** Pruebas en `test/cu10_vestidor_test.dart` (24) y actualización de `test/pantalla_producto_detalle_test.dart`.
