# Especificación Técnica: Parámetros de la empresa (P2-CU11)

**ID del cambio:** `P2-CU11-parametros-empresa`
**Fuente:** `SI2-Parcial2.md` CU11, RF08, RN25, RN30, RN33, RN41, PF-18 y caso de prueba de CU11.
**Depende de:** `P2-CU03-CU04-usuarios-sucursales` (publicado junto o antes).
**Nivel SDD:** **2 (riesgo medio)**: tabla ya existente, sin migración; afecta a operaciones futuras (reservas, cambios, sincronización).
**Bloques:** Backend → Web. Sin bloque móvil (C6).
**Responsable:** Gustavo (`reparticion.md`).
**Estado:** 🟢 Aprobada e implementada (2026-11-09). Spec permanente: `.specs/modules/plataforma/P2-CU11-parametros-empresa.md`.
**Fecha:** 2026-11-09

---

## 0. Hallazgos (código y esquema al 2026-11-09)

### 0.1 Base de datos
`configuracion_tenant` existe desde `0012`, con RLS (`0014`) y fila para FASHION STORE:

| Columna | Por defecto | CHECK en la base |
| :--- | :--- | :--- |
| `moneda` | `EUR` | — |
| `zona_horaria` | `Europe/Madrid` | — |
| `horas_vencimiento_reserva` | 24 (RN25) | `> 0` |
| `dias_cambio_prenda` | 15 (RN30) | `>= 0` |
| `operacion_offline_habilitada` | `true` (RN33) | — |
| `dias_antiguedad_offline` | 7 (RN41) | `> 0` |
| `actualizado_en` | `now()` | — |

El modelo `ConfiguracionTenantORM` ya está en `plataforma/modelos.py`. No hay servicio, endpoint ni pantalla.

### 0.2 Quién usa cada parámetro
**Hoy ningún código lee esta tabla.** Cada parámetro tiene su consumidor en un caso de uso del bloque 3 o 4:

| Parámetro | Lo aplica | Estado actual |
| :--- | :--- | :--- |
| `horas_vencimiento_reserva` | CU15 (RN25: «vence a las horas que define la empresa, contadas desde su creación») | La reserva vence 2 h después de su **hora de cita** (`TOLERANCIA_VENCIMIENTO`, `cu13_consultar_cancelar_reservas`). No guarda su vencimiento. |
| `dias_cambio_prenda` | CU18 (cambio de prenda) | No existe. |
| `operacion_offline_habilitada`, `dias_antiguedad_offline` | CU14 y CU19 (sin conexión) | No existe. |

### 0.3 La reserva web y móvil no permite aplicar ya RN25
- El formulario web de reserva (`modal-reserva-boutique`) fija la cita siempre en «mañana a las 11:30». La franja elegida solo va al texto de la observación.
- Si la sucursal no está elegida, usa el id `1` (`?? 1`), un dato inventado.
- Con un vencimiento de 24 h contado desde la creación, toda reserva hecha antes de las 11:30 vencería antes de su cita.
- Aplicar RN25 exige rehacer la elección del horario en web y móvil, que es justo lo que pide CU15 («horario aproximado» y «fija su vencimiento según los parámetros de la empresa»).

Estos dos defectos del formulario se corrigen en CU15.

---

## 1. Alcance

### 1.1 Qué entrega
1. Pantalla **«Configuración»** (`/admin/configuracion`) para el administrador: muestra los seis parámetros y edita los cuatro operativos.
2. Validación, guardado y **bitácora** del cambio.
3. **Aviso** al desactivar la operación sin conexión (CU11 A2).
4. **`ParametrosEmpresaServicio.vigentes(db)`**: lectura de los parámetros de la empresa de la sesión, para que CU15, CU18, CU14 y CU19 los apliquen.
5. La regla «rigen para las operaciones posteriores» (A3), documentada para esos consumidores.

### 1.2 Fuera de alcance
- Aplicar los parámetros a reservas (CU15), cambios (CU18) y operación sin conexión (CU14, CU19): ver C1.
- Cambiar moneda y zona horaria (C2).
- Lectura pública de los parámetros para el cliente: llega con CU14, que la necesita para descargar el catálogo.
- Crear la fila de una empresa nueva: es parte del alta de empresa (CU05, de Tony). Aquí solo se cubre la que falte (C4).

---

## 2. Decisiones

| ID | Decisión |
| :--- | :--- |
| **C1** | **CU11 configura; cada caso de uso aplica su parámetro** (CU15, CU18, CU14 y CU19, todos de Gustavo). Aplicar ya el vencimiento de reservas exige una migración (`reservas.vence_en`) y rehacer el horario en web y móvil (§0.3), es decir, adelantar CU15 a medias. *Alternativa descartada:* hacerlo ahora, con migración `0016` y bloque móvil. |
| **C2** | **Moneda y zona horaria se muestran sin poder cambiarse.** Los precios están en euros con el IVA del 21 % incluido; cambiar la moneda solo cambiaría el símbolo. Ningún cálculo usa todavía la zona horaria de la empresa. Las fija el alta de empresa (CU05). |
| **C3** | Rangos válidos: horas de reserva **1–168** (hasta una semana: la reserva retiene stock); días de cambio **0–90** (0 = sin cambios); días de antigüedad sin conexión **1–30**. Fuera de rango → 422, sin guardar (A1). La base mantiene sus CHECK como segunda barrera. |
| **C4** | Si la empresa no tiene fila, `vigentes` y la pantalla la crean con los valores por defecto de la base (`INSERT … ON CONFLICT DO NOTHING`). No son datos inventados: son los valores por defecto de RN25, RN30 y RN41. |
| **C5** | Bitácora `CONFIGURACION_MODIFICADA`, con los valores anterior y nuevo **solo de lo que cambió**. Si no cambia nada, no se escribe. |
| **C6** | Sin bloque móvil: CU11 es solo web y el móvil no lee estos parámetros hasta CU14. |
| **C7** | **Regla para los consumidores (A3):** cada operación guarda el valor que la rige en el momento de crearse. Por ejemplo, una reserva guarda su `vence_en` y un cambio comprueba contra la fecha de la venta. Cambiar la configuración no recalcula nada ya registrado. |
| **C8** | Solo el administrador lee y cambia la configuración. Guardar exige suscripción vigente (`SuscripcionServicio.validar`), como cualquier operación de la empresa. |
| **C9** | **Sin migración.** El código vive en `plataforma/cu11_parametros_empresa/` (carpeta de Gustavo según `reparticion.md`); el modelo se usa tal como está en `plataforma/modelos.py`, sin tocarlo. |

---

## 3. Contratos

**`GET /api/v1/admin/configuracion`** (administrador):
```json
{
  "moneda": "EUR",
  "zona_horaria": "Europe/Madrid",
  "horas_vencimiento_reserva": 24,
  "dias_cambio_prenda": 15,
  "operacion_offline_habilitada": true,
  "dias_antiguedad_offline": 7,
  "actualizado_en": "2026-11-09T15:00:00Z"
}
```

**`PUT /api/v1/admin/configuracion`** (administrador). Recibe los cuatro editables y responde lo mismo que el `GET`:
```json
{ "horas_vencimiento_reserva": 48, "dias_cambio_prenda": 30,
  "operacion_offline_habilitada": false, "dias_antiguedad_offline": 7 }
```
- 422 con el campo fuera de rango (C3).
- `moneda` o `zona_horaria` en el cuerpo se ignoran (C2).
- 403 `SUSCRIPCION_NO_VIGENTE`.

**Servicio para otros paquetes:** `ParametrosEmpresaServicio.vigentes(db) → ParametrosEmpresa` (dataclass inmutable con los seis valores).

## 4. Web

- Ruta `/admin/configuracion` con `roleGuard(['administrador', 'admin'])`, tarjeta «Configuración» en el panel y retroceso a `/admin`, como el resto del panel.
- **Formulario:**
  - moneda y zona horaria, de solo lectura;
  - horas de vencimiento de reserva y días para cambiar una prenda, con su rango y el valor por defecto como ayuda;
  - interruptor «Permitir que los clientes reserven sin conexión» y días de antigüedad máxima (deshabilitado si el interruptor está apagado).
- **Al apagar el interruptor**, se pide confirmación con el texto de A2: «Los dispositivos de los clientes ya no podrán registrar reservas nuevas sin internet. Las operaciones pendientes se conservan y se sincronizarán».
- **Guardar:** el estado se reemplaza con la respuesta del servidor y se muestra «Configuración guardada. Rige para las operaciones nuevas».

## 5. Pruebas

- **Unitarias (backend):**
  - lectura con creación de la fila que falte;
  - guardado y bitácora solo con lo que cambió;
  - rangos (0 horas, días negativos, 169 horas → 422);
  - moneda y zona ignoradas;
  - roles (encargado, cajero y cliente → 403).
- **Integración (rama de pruebas):**
  - la empresa B lee y guarda la suya sin tocar la de FASHION STORE (RLS);
  - el CHECK de la base rechaza `horas_vencimiento_reserva = 0` aunque se salte la API.
- **Web:** spec de la página (carga, rangos, aviso al desactivar, guardado con el payload literal del backend) y de la ruta en `app.routes.spec.ts`.

## 6. Coordinación con Tony
- **CU05 (alta de empresa):** debe insertar la fila de `configuracion_tenant` de la empresa nueva. Si no lo hace, C4 la crea al primer uso, pero conviene que el alta la deje lista.
- No se toca `plataforma/modelos.py`.
