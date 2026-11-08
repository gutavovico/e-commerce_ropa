# Checkpoints: CU13 — Consultar y Cancelar Reservas

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-09-29 (D1-D5, todas recomendadas) | — |
| 1 — Backend | 🟢 Completo | CP-01…CP-06 |
| 2 — Web | 🟢 Completo | CP-07…CP-11 |
| 3 — Mobile | 🟢 Completo | CP-12…CP-15 |

## Backend
- [x] **CP-01** `GET /reservas/mias` devuelve solo las reservas del cliente autenticado.
- [x] **CP-02** Cancelar libera stock en la fila exacta que apartó CU12 (por su movimiento), con movimiento `liberacion_reserva` y saldos reales.
- [x] **CP-03** `403`/`404`/`409`/`422` según `spec.md` §A.2, sin efectos secundarios en ningún caso de error.
- [x] **CP-04** Doble cancelación: el stock se libera una sola vez.
- [x] **CP-05** Vencimiento perezoso idempotente (D1-A).
- [x] **CP-06** Suite completa en verde (487/487) y verificación end-to-end contra Neon (vencimiento real de 7 reservas del cliente #2; ciclo reservar→cancelar simétrico 13→11→13 unidades).

## Web
- [x] **CP-07** La tarjeta del Perfil muestra datos reales (o su estado vacío) y navega a `/reservas`; desaparece el literal «3 Artículos · 1.250 €».
- [x] **CP-08** `/reservas` es una hoja con `← Volver`, fuera del layout principal; orden de rutas protegido por su spec.
- [x] **CP-09** Estados de carga, vacío y error; botón de cancelar solo con `puede_cancelar`.
- [x] **CP-10** Modal con motivo obligatorio; tras cancelar, el estado se reemplaza con la respuesta del servidor (recarga completa, no derivación local).
- [x] **CP-11** `tsc`, `ng test` (538/538) y `ng build` de producción en verde.

## Mobile
- [x] **CP-12** Tarjeta del Perfil con datos reales (`_activasReservas()`/`_subtituloReservas()` sobre `MisReservasBloc.estado`), `Navigator.push` con token vía `_abrirMisReservas`.
- [x] **CP-13** Pantalla hoja: `AppBar` con `BackButton`, sin `bottomNavigationBar`.
- [x] **CP-14** Sin `RenderFlex overflowed`: textos variables (nombre de producto, boutique, dirección) con `Expanded`/`Flexible` + `TextOverflow.ellipsis`.
- [x] **CP-15** `dart analyze` limpio ("No issues found!") y `flutter test` en verde (209/209, incluidas las 19 pruebas nuevas del módulo reservas).
