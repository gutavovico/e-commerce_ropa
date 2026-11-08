# Especificación Técnica Permanente: CU13 + CU14 — Consultar y Cancelar Reservas

**Código:** CU13 (Consultar y cancelar reservas) · CU14 (Consultar estado de reserva)
**Paquete de Dominio:** `reservas`
**Backend:** `app/modules/reservas/cu13_consultar_cancelar_reservas/`
**Frontend:** `src/app/modules/reservas/cu13_consultar_cancelar_reservas/` (ruta hoja `/reservas`, tarjeta «Mis Reservas» en `/perfil`)
**Mobile:** `lib/src/modulos/reservas/cu13_consultar_cancelar_reservas/` (`PantallaMisReservas`, tarjeta en `PantallaPerfil`)
**Actor:** Cliente autenticado
**Estado:** Aprobado y promovido a permanente (2026-11-08; decisiones D1–D5 aprobadas el 2026-09-29)
**Historial del cambio:** `.specs/finalized/CU13-CU14-consultar-cancelar-reservas/`

---

## 1. Reglas

- **CU14** se resuelve con el mismo listado: cada reserva expone cabecera, boutique, fecha/hora, estado y prendas. La búsqueda por código para personal de tienda pertenece a CU28 y a la caja (CU31-CU32).
- **Vencimiento perezoso (D1):** al listar o cancelar, una reserva `pendiente`/`confirmada` cuya cita pasó hace más de **2 h** pasa a `vencida` y libera su stock (`liberacion_reserva`, motivo «Vencida sin atención»).
- **Cancelable (D3)** mientras esté en `pendiente` o `confirmada` y la cita no haya llegado. `puede_cancelar` lo decide el servidor.
- **Motivo (D2)** obligatorio, 3–250 caracteres: va a `movimientos_inventario.observacion` y a la bitácora `CANCELAR_RESERVA`. `reservas.observacion` (nota del cliente) no se toca.
- **Invariante de inventario:** se libera en la misma fila que apartó CU12, localizada por su movimiento `reserva` (`referencia_documento = RESERVA-{id}`), con `FOR UPDATE`; sin movimiento → `409 RESERVA_SIN_TRAZA`. Nunca se recalcula la temporada.
- `en_atencion` y `atendida` son transiciones de tienda (las aplica la caja, CU31-CU32) y no son cancelables.

## 2. Contratos

### `GET /api/v1/reservas/mias`
`{resumen: {activas, proxima|null}, proximas: ReservaOut[] (cita ascendente), historial: ReservaOut[] (descendente)}`.
`ReservaOut`: `id_reserva`, `codigo_reserva` (`RES-AAAA-NNNN`), `estado`, `fecha_hora_atencion`, `creado_en`, `sucursal {id_sucursal, nombre, direccion}`, `items[] {id_variante, nombre_producto, talla_codigo, color_nombre, color_hex, imagen_url, cantidad, precio_unitario}`, `total_prendas`, `observacion`, `puede_cancelar`.

### `POST /api/v1/reservas/{id_reserva}/cancelar`
Cuerpo `{motivo}`. Respuesta: el `ReservaOut` actualizado.
Errores: `403 RESERVA_AJENA` · `404 RESERVA_NO_ENCONTRADA` · `409 RESERVA_NO_CANCELABLE | RESERVA_VENCIDA | RESERVA_SIN_TRAZA` · `422` motivo inválido.

## 3. Interfaz

Web y móvil: pestañas Próximas / Historial, badge de estado, prendas con talla, color y miniatura, y botón «Cancelar reserva» solo con `puede_cancelar`. El modal u hoja de cancelación exige el motivo y, tras confirmar, recarga la lista del servidor.
