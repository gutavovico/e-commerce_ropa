# Especificación Técnica Formal: Consultar y Cancelar Reservas

**ID del Cambio:** `CU13-CU14-consultar-cancelar-reservas`
**Módulo Afectado:** `reservas` (backend) · `autenticacion_seguridad/cu04` (tarjeta del Perfil, Web y Mobile)
**Caso de Uso:** **CU13** — Consultar y cancelar reservas · **CU14** — Consultar estado de reserva
(`SI2-Parcial1.md`, §CU13/§CU14). Un único endpoint de listado cubre ambos: la vía de CU14 «selecciona
una reserva activa desde su panel» se resuelve con el mismo `ReservaOut` que ya expone el estado
completo de la cita (decisión D5, aprobada el 2026-09-29). La búsqueda por código para personal de
tienda queda fuera de alcance (pertenece a CU28/admin).
**Depende de:** CU12, que crea la reserva en `pendiente` y mueve las unidades de `cantidad_disponible` a
`cantidad_reservada`.
**Metodología:** Spec-Driven Development (SDD)
**Nivel SDD:** **3 (alto riesgo)** — libera inventario retenido; un error duplica o pierde existencias.
**Fuente de Verdad Visual:** captura de la pantalla *Mi Cuenta* (Web) del 2026-09-29: la tarjeta
«ORDEN EN CURSO · Bolsa de Compra · IR AL CHECKOUT» se sustituye por la de reservas.
**Fuente de Verdad de Datos:** PostgreSQL en Neon, verificado por introspección directa el 2026-09-29.
**Estado:** 🟢 Especificación aprobada el 2026-09-29 (D1-D5, todas las opciones recomendadas). Bloques 1
(Backend), 2 (Web) y 3 (Mobile) completos y verificados. Pendiente de promoción a `.specs/finalized/`.
**Fecha:** 2026-09-29

---

## 0. Hallazgos previos (verificados contra Neon y el código)

### 0.1 Esquema real

| Tabla | Columnas relevantes | Observación |
| :--- | :--- | :--- |
| `reservas` | `id_reserva`, `id_cliente`, `id_sucursal`, `fecha_hora_atencion` (TIMESTAMPTZ), `estado`, `canal_origen`, `creado_en`, `atendido_por`, `atendido_en`, `observacion` | **No existe** columna de motivo de cancelación (ver D2). |
| `reserva_detalle` | `id_reserva_detalle`, `id_reserva`, `id_variante`, `cantidad` | **No guarda** `id_sucursal` ni `id_temporada` de la fila de inventario apartada. |
| `inventario_sucursal` | clave única `(id_variante, id_sucursal, id_temporada)` | Una variante puede tener varias filas por temporada en la misma boutique. |
| `movimientos_inventario` | `id_inventario`, `tipo_movimiento`, `cantidad`, `referencia_documento`, saldos | CU12 escribe un movimiento `reserva` con `referencia_documento = 'RESERVA-{id}'`. |

- Enum `estado_reserva`: `pendiente`, `confirmada`, `en_atencion`, `atendida`, `cancelada`, `vencida`.
- Enum `tipo_movimiento` **ya contiene** `liberacion_reserva`: no hace falta DDL.
- `clientes.id_cliente` comparte clave con `usuarios.id_usuario` (1:1), igual que asume `CU12`.
- Único trigger sobre estas tablas: `trg_inventario_estado` (`BEFORE INSERT/UPDATE` en
  `inventario_sucursal`), que recalcula el campo `estado` de la fila, **no las cantidades**. No hay
  ningún trigger que libere stock al cambiar `reservas.estado`: la liberación la debe hacer el servicio.

### 0.2 Cómo localizar la fila de inventario a liberar

`reserva_detalle` no dice de qué temporada salieron las unidades. CU12 elige la temporada en el momento
de reservar (`obtener_inventario_para_reserva`: la más reciente con stock suficiente), así que
recalcularla al cancelar podría devolver las unidades a **otra** fila. En cambio, el movimiento
`reserva` escrito por CU12 conserva el `id_inventario` exacto. Las **9 reservas existentes tienen su
movimiento** (comprobado). La cancelación localizará la fila por ese movimiento, nunca adivinando.

### 0.3 Estado actual de los datos

- Hay **9 reservas, todas en `pendiente`**, de 3 clientes, que retienen **9 unidades** en total.
- **Las 9 tienen `fecha_hora_atencion` ya pasada** (entre el 2026-09-22 y el 2026-09-24): ningún proceso
  las marca como `vencidas`, así que su stock sigue retenido indefinidamente (ver D1).

### 0.4 Lo que existe hoy en el código

- Backend `reservas/cu12_reservar_prendas`: solo `POST /api/v1/reservas` (crear) y
  `GET /api/v1/sucursales/activas`. **No hay listado para el cliente ni cancelación.**
- `CU28` (admin) solo **lee** reservas (`/admin/ventas-reservas`); tampoco cancela.
- Web `perfil.component.html` (líneas ~260-285): la tarjeta «Bolsa de Compra» muestra el literal
  **«3 Artículos seleccionados · 1.250 €»** y un botón sin acción. Mobile `pantalla_perfil.dart`
  (líneas ~679-717): tarjeta gemela con «3 · Artículos · 1.250 €». Ambas violan «cero datos
  inventados»; este cambio las elimina al sustituirlas.
- Web: Tailwind se carga por CDN (`src/index.html`) con los tokens de espaciado `space-1…space-7`
  configurados, pero **sin** los tokens de color semánticos del design system (`secondary-container`,
  etc.). Las pantallas existentes usan los HEX de `fashionstore-tokens.md` como valores literales.

---

## 1. Decisiones — aprobadas el 2026-09-29 (todas las opciones recomendadas, A)

### D1. Reservas cuya cita ya pasó sin ser atendidas

| | **Opción A (recomendada)** | Opción B | Opción C |
| :--- | :--- | :--- | :--- |
| **Qué** | Vencimiento **perezoso**: al listar o cancelar, una reserva `pendiente`/`confirmada` cuya cita pasó hace más de la **tolerancia** (propuesta: **2 h**) pasa a `vencida`, libera su stock y registra `liberacion_reserva`. | Solo se **muestra** como vencida (estado calculado), sin tocar la base ni liberar stock. | Fuera de alcance: se listan tal cual están (`pendiente`). |
| **Pro** | Mismo patrón ya aprobado en CU15/CU16. Devuelve al stock las 9 unidades retenidas hoy. | Sin efectos secundarios en una lectura. | Mínimo trabajo. |
| **Contra** | Un `GET` con efecto secundario; el panel admin (CU28) solo lo verá tras la primera consulta del cliente. | El stock sigue retenido para siempre. | El cliente vería «pendiente» una cita de hace una semana. |

### D2. Motivo de cancelación

CU13 (paso 4) exige solicitarlo. No hay columna para guardarlo.
- **Recomendada:** motivo **obligatorio** (3-250 caracteres), guardado en `movimientos_inventario.observacion`
  y en el payload del evento de bitácora `CANCELAR_RESERVA`. `reservas.observacion` **no se toca**: es
  la nota del cliente para la estilista.
- Alternativa: anexarlo a `reservas.observacion` (mezcla dos datos distintos en un campo).
- Alternativa: añadir columna `motivo_cancelacion` (requiere DDL, y la cadena de Alembic está rota).

### D3. Hasta cuándo puede cancelar el cliente

- **Recomendada:** mientras la reserva esté en `pendiente` o `confirmada` **y la hora de la cita no haya
  llegado**. Entre la hora de la cita y el fin de la tolerancia de D1, no es cancelable ni vencida
  (el cliente puede estar llegando).
- Alternativa: exigir una antelación mínima (p. ej. 2 h antes).

### D4. Alcance Mobile

La tarjeta gemela existe en `pantalla_perfil.dart` y la constitución móvil incluye CU12-CU14.
- **Recomendada:** tres bloques (Backend → Web → Mobile), como en CU16.
- Alternativa: solo Backend + Web en este ciclo.

### D5. Alcance de CU14

- **Recomendada:** cubrir la vía «seleccionar una reserva activa desde su panel»: cada tarjeta de la
  lista muestra cabecera, sucursal, fecha/hora, estado y prendas. La búsqueda **por código** de reserva
  (pensada para el personal de tienda) queda para CU28/admin.
- Alternativa: añadir además `GET /api/v1/reservas/{id}` y una vista de detalle separada.

---

## A. Especificación Técnica Formal

### A.1 Máquina de estados (lo que implementa este cambio)

```
                     cliente cancela (antes de la cita)
   pendiente ──────────────────────────────────────────────▶ cancelada
       │                                                     (stock: reservada → disponible,
       │ (CU28/staff, fuera de alcance)                        movimiento liberacion_reserva)
       ▼
   confirmada ─────────── cliente cancela (antes de la cita) ─▶ cancelada
       │
       │ cita + tolerancia vencida sin atención (D1, perezoso)
       ▼
    vencida  (stock liberado igual que al cancelar, motivo «Vencida sin atención»)

   en_atencion / atendida: transiciones de tienda (fuera de alcance). No cancelables.
```

**Invariante de inventario:** liberar `n` unidades hace `cantidad_reservada -= n` y
`cantidad_disponible += n` **en la misma fila** que apartó CU12 (localizada por su movimiento), con
`SELECT … FOR UPDATE`. Nunca se libera una reserva dos veces: la cabecera se bloquea y su estado se
revalida dentro de la transacción.

### A.2 Contratos de API

Bajo `/api/v1`, `Authorization: Bearer <jwt>`, rol `cliente`. Errores con `{detail, code}`.
Importes `Decimal` (llegan como cadena JSON).

#### `GET /api/v1/reservas/mias`

Reservas del cliente autenticado. **Debe declararse antes** de cualquier ruta `/reservas/{id}` futura.

```jsonc
{
  "resumen": {
    "activas": 1,                         // pendiente + confirmada con cita futura
    "proxima": {                          // null si no hay ninguna activa
      "id_reserva": 12,
      "fecha_hora_atencion": "2026-10-02T15:30:00Z",
      "nombre_sucursal": "Atelier Serrano - Madrid"
    }
  },
  "proximas": [ /* ReservaOut, orden: fecha_hora_atencion ascendente */ ],
  "historial": [ /* ReservaOut: canceladas, atendidas, vencidas; orden descendente */ ]
}
```

```jsonc
// ReservaOut
{
  "id_reserva": 12,
  "codigo_reserva": "RES-2026-0012",      // mismo formato que ya emite CU12
  "estado": "pendiente",
  "fecha_hora_atencion": "2026-10-02T15:30:00Z",
  "creado_en": "2026-09-29T10:02:11Z",
  "sucursal": { "id_sucursal": 1, "nombre": "Atelier Serrano - Madrid", "direccion": "Calle Serrano 48" },
  "items": [
    {
      "id_variante": 7,
      "nombre_producto": "Blusa de satén fluido",
      "talla_codigo": "38",
      "color_nombre": "Champagne",
      "color_hex": "#E8DFCF",
      "imagen_url": "https://…",
      "cantidad": 1,
      "precio_unitario": "310.00"
    }
  ],
  "total_prendas": 1,
  "observacion": "Prefiero probador amplio",
  "puede_cancelar": true                  // decidido en el servidor (D3); el cliente no lo deriva
}
```

| Código | Situación |
| :--- | :--- |
| `200` | Lista (posiblemente vacía: `activas: 0`, `proxima: null`, listas `[]`) |
| `401` | Sin sesión |

#### `POST /api/v1/reservas/{id_reserva}/cancelar`

```jsonc
// ReservaCancelarIn
{ "motivo": "No podré asistir ese día" }   // obligatorio, 3-250 caracteres (D2)
```

Respuesta `200`: el `ReservaOut` actualizado (`estado: "cancelada"`, `puede_cancelar: false`).

**Secuencia transaccional:**
1. Cargar la cabecera con `FOR UPDATE` → `404 RESERVA_NO_ENCONTRADA`.
2. `reserva.id_cliente != usuario.id_usuario` → `403 RESERVA_AJENA`.
3. Aplicar vencimiento perezoso (D1). Si queda `vencida` → `409 RESERVA_VENCIDA`.
4. Estado no en (`pendiente`, `confirmada`) o cita ya iniciada (D3) → `409 RESERVA_NO_CANCELABLE`.
5. Por cada línea: localizar su movimiento `reserva` (`referencia_documento = 'RESERVA-{id}'`, misma
   variante) → fila de inventario con `FOR UPDATE`. Sin movimiento → `409 RESERVA_SIN_TRAZA`
   (no se adivina la temporada).
6. `cantidad_reservada -= n`, `cantidad_disponible += n`; movimiento `liberacion_reserva` con
   `id_usuario_responsable`, `referencia_documento = 'RESERVA-{id}'`, `observacion` con el motivo y
   saldos reales.
7. `reservas.estado = 'cancelada'`; `COMMIT`; bitácora `CANCELAR_RESERVA` (CU30).

| Código | Situación |
| :--- | :--- |
| `200` | Cancelada |
| `401` | Sin sesión |
| `403` | `RESERVA_AJENA` |
| `404` | `RESERVA_NO_ENCONTRADA` |
| `409` | `RESERVA_NO_CANCELABLE` · `RESERVA_VENCIDA` · `RESERVA_SIN_TRAZA` |
| `422` | Motivo ausente o fuera de longitud |

### A.3 Criterios de Aceptación (Gherkin)

```gherkin
Característica: CU13 — Consultar y cancelar reservas

  Escenario: Consultar mis reservas
    Dado que tengo una reserva pendiente con cita futura y otra cancelada
    Cuando consulto GET /api/v1/reservas/mias
    Entonces la pendiente aparece en "proximas" con puede_cancelar = true
    Y la cancelada aparece en "historial" con puede_cancelar = false
    Y no aparece ninguna reserva de otro cliente

  Escenario: Sin reservas
    Dado que nunca he reservado
    Cuando consulto mis reservas
    Entonces recibo 200 con resumen.activas = 0, proxima = null y listas vacías

  Escenario: Cancelar una reserva pendiente
    Dado una reserva pendiente con cita futura que retiene 2 unidades de una variante
    Cuando la cancelo indicando un motivo
    Entonces recibo 200 y la reserva queda "cancelada"
    Y en la misma fila de inventario que apartó CU12: reservada -2 y disponible +2
    Y se registra un movimiento "liberacion_reserva" con responsable, motivo y saldos reales

  Escenario: Cancelar una reserva ajena
    Cuando intento cancelar la reserva de otro cliente
    Entonces recibo 403 "RESERVA_AJENA" y el inventario no cambia

  Escenario: Cancelar una reserva no cancelable
    Dado una reserva en estado cancelada, atendida o en_atencion
    Cuando intento cancelarla
    Entonces recibo 409 "RESERVA_NO_CANCELABLE" y el inventario no cambia

  Escenario: Doble envío de la cancelación
    Cuando envío dos veces la cancelación de la misma reserva
    Entonces la primera responde 200 y la segunda 409
    Y el stock se libera una sola vez

  Escenario: Motivo ausente
    Cuando cancelo sin motivo
    Entonces recibo 422 y la reserva no cambia

  Escenario: Reserva vencida (si se aprueba D1-A)
    Dado una reserva pendiente cuya cita pasó hace más de la tolerancia
    Cuando consulto mis reservas
    Entonces aparece en "historial" como "vencida"
    Y su stock se ha liberado con un movimiento "liberacion_reserva"
```

### A.4 Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| Liberar stock dos veces (doble clic, dos pestañas) | `FOR UPDATE` sobre la cabecera y revalidación del estado dentro de la transacción; prueba de concurrencia. |
| Devolver las unidades a otra temporada | Fila localizada por el `id_inventario` del movimiento de CU12, nunca recalculada. |
| `cantidad_reservada` negativa por datos inconsistentes | Se verifica `cantidad_reservada >= n` antes de restar; si no, `409` y rollback (no se «arregla» en silencio). |
| `GET` con efecto secundario (D1-A) | Documentado; mismo patrón aceptado en CU15/CU16; idempotente (una reserva vencida no se vuelve a liberar). |
| Zona horaria | Fechas en UTC en la API; el cliente las formatea en la zona local del dispositivo. |
| Los tests en verde con sesión mockeada ocultan errores de SQL | Verificación end-to-end contra Neon en transacción revertida, como en CU15/CU16. |
