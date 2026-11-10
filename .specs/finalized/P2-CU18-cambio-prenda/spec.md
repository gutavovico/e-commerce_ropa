# Requisitos · P2-CU18 — Registrar cambio de prenda   Nivel: 3   Estado: aprobado

**ID del cambio:** `P2-CU18-cambio-prenda`
**Aprobado por:** Gustavo (usuario) **Fecha:** 2026-11-10
**Fase SDD:** 1 de 4 (Requisitos). Diseño en `plan.md`, tareas en `tasks.md`, puertas en `checkpoint.md`.
**Fuente:** `SI2-Parcial2.md` CU18 («Web/Móvil», con conexión), RN30 (plazo de cambio), RN31
(cantidad cambiada), RN32 (inventario en cambios), CU11 (`dias_cambio_prenda`).
**Decisiones del usuario (2026-11-10):** F1 la diferencia a favor del cliente **se devuelve en
efectivo** · F2 la prenda devuelta vale **lo pagado**: precio de la línea menos su parte proporcional
del cupón de la venta · F3 alcance **backend, web y móvil**, por bloques.
**Nivel 3 porque** mueve inventario y dinero, con una migración nueva (`0021`).

---

## Propósito

Que el cajero o el encargado cambie en caja una o más prendas de una venta pagada por otras, dentro del
plazo que define la empresa, cobrando o devolviendo la diferencia y con el inventario y su kardex al día.

## Actores y precondiciones

| Actor | Precondiciones |
| :--- | :--- |
| Cajero, encargado de sucursal, administrador | Sesión iniciada; opera en una sucursal autorizada (RN07); suscripción vigente con «ventas»; conexión |
| Cliente (presente en caja) | Trae el número de comprobante de una venta **pagada** de la empresa |

## Hallazgos

- No existe nada de CU18: ni tablas, ni endpoints, ni pantallas.
- Ya existen `configuracion_tenant.dias_cambio_prenda` (CU11, 15 por defecto, 0 = sin cambios) y el
  tipo de movimiento `devolucion`.
- Cada línea de venta guarda su precio con las promociones de la prenda; el cupón es un descuento sobre
  toda la venta (`ventas.descuento`).

---

## Requisitos (EARS)

- **AC-1** Cuando el empleado busca una venta por su número de comprobante, el sistema deberá mostrarla
  con sus líneas, cuántas unidades quedan por cambiar en cada una, su valor unitario a devolver (F2),
  la fecha de la venta y los días transcurridos.
- **AC-2** Si la venta no existe, es de otra empresa o no está pagada, entonces el sistema deberá
  responder que no existe (404 `VENTA_NO_ENCONTRADA`) (A4).
- **AC-3** Si pasaron más días que `dias_cambio_prenda` desde la fecha de la venta (en hora de Bolivia),
  o el parámetro es 0, entonces el sistema deberá rechazar el cambio e informar cuántos días pasaron
  (409 `PLAZO_DE_CAMBIO_VENCIDO`) (A1, RN30).
- **AC-4** Si se pide devolver una línea que no es de la venta, o más unidades de las que quedan por
  cambiar en esa línea, entonces el sistema deberá rechazarlo (409 `CANTIDAD_NO_CAMBIABLE`) (A2, RN31).
- **AC-5** Cuando el empleado elige las prendas nuevas, el sistema deberá validar sus existencias en la
  sucursal del cambio; sin existencias, 409 `STOCK_INSUFICIENTE` (A3).
- **AC-6** El sistema deberá calcular en el servidor el valor devuelto (F2), el valor de las prendas
  nuevas (precio vigente con sus promociones, sin cupón) y la **diferencia** = nuevo − devuelto.
- **AC-7** Si la diferencia es positiva, entonces el empleado deberá cobrarla (efectivo con monto
  recibido y cambio; tarjeta, QR o transferencia con referencia). Si es negativa, el sistema deberá
  registrar que se devuelve en efectivo (F1). Si es cero, no hay cobro.
- **AC-8** Cuando el empleado confirma, el sistema deberá, en una sola transacción: registrar el cambio
  con un número de comprobante único en la empresa; ingresar al inventario de la sucursal las prendas
  devueltas y descontar las nuevas, con sus movimientos (RN32); y dejarlo en la bitácora.
- **AC-9** Cuando el cambio se registra, la app deberá mostrar su comprobante: número, fecha, venta
  original, prendas devueltas y nuevas con sus valores, diferencia y cómo se cobró o devolvió.
- **AC-10** Mientras una venta tenga unidades por cambiar dentro del plazo, el sistema deberá permitir
  más de un cambio sobre ella; nunca se cambian más unidades de las vendidas (RN31).
- **AC-11** Si dos cambios compiten por la misma línea o por la última unidad de una prenda nueva,
  entonces solo uno deberá pasar y ni las unidades por cambiar ni el stock quedarán negativos.
- **AC-12** El sistema deberá aislar los cambios por empresa (RLS) y el encargado o cajero solo podrá
  hacerlos en sus sucursales autorizadas.
- **AC-13** Sin conexión, la caja web y la móvil no deberán permitir registrar un cambio (CU18: «con
  conexión»).

## Casos de error

| Caso | Respuesta |
| :--- | :--- |
| Venta inexistente, de otra empresa o no pagada | 404 `VENTA_NO_ENCONTRADA` |
| Plazo vencido o cambios desactivados | 409 `PLAZO_DE_CAMBIO_VENCIDO` (con los días) |
| Línea ajena o más unidades de las que quedan | 409 `CANTIDAD_NO_CAMBIABLE` |
| Prenda nueva sin stock en la sucursal | 409 `STOCK_INSUFICIENTE` |
| Cambio vacío (sin devolver o sin prenda nueva) | 422 |
| Cobro de la diferencia: monto o referencia | 400 `MONTO_INSUFICIENTE` / `REFERENCIA_REQUERIDA` (como la caja) |
| Sucursal no autorizada / suscripción | 403 `SUCURSAL_AJENA` / `SUSCRIPCION_NO_VIGENTE` |

## Fuera de alcance

- Devolución sin cambio (reembolso de la venta) y notas de crédito.
- Cambiar otra vez una prenda recibida en un cambio (no pertenece a la venta original).
- Reflejar los cambios en reportes, indicadores y predicciones.
- PDF del comprobante del cambio (web: ticket imprimible como el de la caja; móvil: en pantalla).

## Preguntas abiertas

Ninguna: F1–F3 decididas el 2026-11-10.
