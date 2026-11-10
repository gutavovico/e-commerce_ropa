# Especificación Técnica Permanente: Operación sin conexión — P2-CU14, CU15, CU19 y CU20

**Fuente:** `SI2-Parcial2.md` (CU14, CU15, CU16 A4, CU17 A4, CU19, CU20; RN25, RN33–RN43, RNF03, RNF15)
y las decisiones del usuario del 2026-11-09 (D1 avisos en la app sin push, D2 cierre de mes con un
botón, D3 caja móvil en otro cambio).
**Paquete de Dominio:** `sincronizacion` (nuevo) · CU15 sigue en `reservas/cu12_reservar_prendas`.
**Backend:** migración `0020_sin_conexion` · `app/modules/sincronizacion/{cu14_dispositivo_catalogo,cu19_sincronizar,cu20_conflictos,avisos_cliente}/`
**Frontend:** PWA (`ngsw-config.json`, `public/manifest.webmanifest`) · `src/app/core/sin-conexion/` ·
`src/app/modules/sincronizacion/` · rutas `/{codigo}/sin-conexion`, `/{codigo}/sincronizacion`, `/admin/conflictos`
**Mobile:** `lib/src/core/sin_conexion/` · `lib/src/modulos/sincronizacion/` · compra interrumpida en `cu16_realizar_pago`
**Depende de:** `P2-CU13-CU12-fundacion-multitenant.md`, `P2-CU11-parametros-empresa.md`
**Estado:** En producción (2026-11-10, migración `0020`). Pendiente: prueba manual en
dispositivo físico.
**Historial del cambio:** `.specs/finalized/P2-CU14-CU15-CU19-CU20-sin-conexion/`

---

## 1. Qué hace

| CU | Comportamiento |
| :--- | :--- |
| CU14 | El cliente registra su dispositivo por tienda (UUID generado en el dispositivo, código corto de 4 caracteres) y descarga el catálogo de esa tienda: productos activos, variantes y precios, categorías, tallas, colores, promociones vigentes sin cupón, sucursales activas y existencias. Sin red ve lo guardado con «Datos del …». |
| CU15 | Reserva en línea: vence a `creado_en + horas_vencimiento_reserva` (RN25), guardado en `reservas.vence_en`. Sin red: se guarda en el dispositivo con código `PROV-<corto>-<correlativo de 6 dígitos>`. |
| CU19 | Lote de hasta 50 operaciones (`reserva` y, solo en el móvil, `compra_interrumpida`). Cada una queda `confirmada`, `rechazada` o `en_conflicto`, sin duplicados. |
| CU20 | Compras pagadas que no pudieron completarse: el administrador o el encargado (sus sucursales) acepta el reembolso; el administrador lo procesa con Stripe al cierre del mes. |
| CU16/CU17 | La caja web no deja registrar ni cobrar sin conexión. |

## 2. Reglas

| ID | Regla |
| :--- | :--- |
| R1 | **Idempotencia (RN35):** `UNIQUE (id_tenant, uuid_operacion)`. El registro de la operación se inserta en la misma transacción que su efecto; un segundo envío del mismo UUID se deshace entero y devuelve el resultado guardado. Una transacción por operación. |
| R2 | **Orden de validación (RN39, RN41):** suscripción y plan → antigüedad (`registrada_en` del dispositivo, margen de 5 min; en compras, desde `ventas.fecha_venta`) → sucursal activa → producto y variante activos → stock con `FOR UPDATE`. |
| R3 | **Reserva sin stock:** se rechaza y el cliente recibe un aviso; no es un conflicto. |
| R4 | **Compra cobrada (RN38, RN40):** se verifica con Stripe; si no puede completarse, el pago queda `confirmado`, la retención se devuelve y se abre un conflicto. **Nunca queda `rechazada`.** Un solo conflicto por venta (`UNIQUE (id_tenant, id_venta)`). Si Stripe no responde: `reintentar`, sin guardar nada. |
| R5 | **Aceptar reembolso:** la venta pasa a `anulada` sin tocar el inventario; aviso «Recibirá su reembolso al finalizar el mes o en 15 días hábiles». Un segundo intento: 409 `CONFLICTO_YA_RESUELTO`. |
| R6 | **Cierre de mes (D2):** solo el administrador, el último día del mes en hora de Bolivia; otro día exige confirmar un «cierre anticipado de prueba», que queda así en la bitácora. Un conflicto por transacción con `FOR UPDATE SKIP LOCKED` e `idempotency_key` `reembolso-<tenant>-<conflicto>-<intento>`. Un fallo deja el conflicto pendiente con el motivo y el intento. |
| R7 | **Plan:** registrar el dispositivo y descargar el catálogo exigen la funcionalidad `operacion_offline`. Sincronizar lo pendiente sigue permitido aunque la empresa desactive la operación sin conexión (CU11 A2). |
| R8 | **Cita dentro del plazo:** una cita posterior a `vence_en` responde 400 `CITA_FUERA_DE_PLAZO`. Web y móvil solo ofrecen horas en punto dentro del vencimiento y del horario 9–20 (`franjasDeCita`). |
| R9 | **Datos guardados (RN43):** `operaciones_sync.datos` pasa por una lista blanca: nunca tokens, contraseñas, `client_secret` ni tarjetas. De una compra solo `id_venta` e `id_pago`. |
| R10 | **Almacenamiento local:** separado por tienda y cliente (`<codigo>:<idCliente>`). Cerrar sesión borra el catálogo, nunca las operaciones (RNF03). El service worker no cachea la API. |
| R11 | **Avisos (D1):** tabla `avisos_cliente`; tipos `reserva_cancelada`, `reembolso_aceptado` y `reembolso_procesado`; bandeja en la app, sin push. |

## 3. Contratos (`/api/v1`)

| Método y ruta | Quién | Notas |
| :--- | :--- | :--- |
| `POST /sin-conexion/dispositivos` | cliente | 201 alta · 200 reutilizado · 409 `DISPOSITIVO_DE_OTRO_CLIENTE` |
| `GET /sin-conexion/catalogo?dispositivo=&modo=completo\|indispensable` | cliente | Importes como cadena |
| `POST /sin-conexion/sincronizar` | cliente | 1–50 operaciones; 200 con un resultado por operación |
| `GET /sin-conexion/operaciones?dispositivo=` | cliente | Incluye `estado_conflicto` |
| `GET /avisos` · `POST /avisos/{id}/leido` | cliente | |
| `GET /conflictos-sync[?estado=]` · `GET /conflictos-sync/{id}` · `GET /conflictos-sync/resumen` | administrador, encargado | El encargado: 404 fuera de sus sucursales |
| `POST /conflictos-sync/{id}/aceptar-reembolso` | administrador, encargado | |
| `GET /conflictos-sync/cierre` · `POST /conflictos-sync/procesar-cierre {forzar}` | administrador | 409 `CIERRE_NO_DISPONIBLE` |
| `POST /reservas` | cliente | Añade `vence_en` y `codigo_provisional`; 409 con `alternativas` |

## 4. Base de datos (`0020`)

Tablas de empresa con RLS `aislamiento_tenant`, `UNIQUE (id_tenant, pk)` y FK compuestas:
`dispositivos`, `operaciones_sync`, `conflictos_sync`, `sync_log`, `avisos_cliente`. Estados y tipos
con `VARCHAR` + `CHECK`. En `reservas`: `vence_en` (`NOT NULL`, relleno `creado_en + 24 h`, por
defecto `now() + 24 h` para el código anterior al despliegue) y `codigo_provisional`.

## 5. Pruebas

- Backend: 49 unitarias de `tests/modules/sincronizacion`, 7 de `test_p2_cu15_vencimiento.py`, 5 de
  integración en `test_multitenant.py` (2 de concurrencia real con datos confirmados que se borran).
- Web: `sin-conexion.service.spec.ts`, conflictos, catálogo local, guard sin red, caja sin red y rutas.
- Móvil: `test/sin_conexion/` con SQLite real (`sqflite_common_ffi`) y `pago_bloc_test.dart`.

## 6. Fuera de alcance

Caja en el móvil (CU16/CU17 Flutter, cambio siguiente) · push real · compras sin conexión en la web ·
RN21 (inventario sin temporada) · descarga incremental del catálogo · `precio_modificado` como causa de
conflicto (el precio se congela en el checkout).
