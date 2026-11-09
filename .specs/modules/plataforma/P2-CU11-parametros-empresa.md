# Especificación Técnica Permanente: Parámetros de la Empresa — P2-CU11 (Configurar parámetros de la empresa)

**Fuente:** `SI2-Parcial2.md` (CU11, RF08, RN25, RN30, RN33, RN41, PF-18)
**Paquete de Dominio:** `plataforma` (`cu11_parametros_empresa`)
**Backend:** sin migración (`configuracion_tenant` de `0012`) · `app/modules/plataforma/cu11_parametros_empresa/`
**Frontend:** `src/app/modules/plataforma/cu11_parametros_empresa/` · ruta `/admin/configuracion` · tarjeta en el panel
**Mobile:** sin cambios
**Depende de:** `P2-CU13-CU12-fundacion-multitenant.md`
**Estado:** Aprobado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU11-parametros-empresa/`

---

## 1. Decisiones

| ID | Decisión |
| :--- | :--- |
| C1 | CU11 configura; cada caso de uso aplica su parámetro: `horas_vencimiento_reserva` en CU15, `dias_cambio_prenda` en CU18, `operacion_offline_habilitada` y `dias_antiguedad_offline` en CU14 y CU19. |
| C2 | Moneda y zona horaria se muestran y no se cambian aquí (las fija el alta de empresa, CU05). |
| C3 | Rangos: reserva 1–168 h; cambio de prenda 0–90 días (0 = sin cambios); antigüedad sin conexión 1–30 días. La base conserva sus CHECK de mínimos. |
| C4 | Si la empresa no tiene fila, se crea con los valores por defecto de la base al primer uso. |
| C5 | Bitácora `CONFIGURACION_MODIFICADA` con el valor anterior y el nuevo de lo que cambió; sin cambios, no se escribe. |
| C7 | La operación que use un parámetro guarda el valor que la rige al crearse; cambiar la configuración no recalcula nada ya registrado (CU11 A3). |
| C8 | Solo el administrador; guardar exige suscripción vigente. |

## 2. Contratos

| Método y ruta | Auth | Comportamiento |
| :--- | :--- | :--- |
| `GET /api/v1/admin/configuracion` | Administrador | `{moneda, zona_horaria, horas_vencimiento_reserva, dias_cambio_prenda, operacion_offline_habilitada, dias_antiguedad_offline, actualizado_en}`. |
| `PUT /api/v1/admin/configuracion` | Administrador | Recibe los cuatro editables; responde como el `GET`. 422 fuera de rango; 403 `SUSCRIPCION_NO_VIGENTE`. `moneda` y `zona_horaria` se ignoran. |

**Lectura para otros paquetes:** `ParametrosEmpresaServicio.vigentes(db) → ParametrosEmpresa` (dataclass inmutable, empresa de la sesión).

## 3. Web

- `/admin/configuracion` (`roleGuard(['administrador', 'admin'])`), con tarjeta «Configuración» en el panel.
- Moneda y zona horaria de solo lectura. Los tres valores numéricos llevan su rango y su valor por defecto.
- Al desactivar la operación sin conexión se muestra el aviso de A2 y hay que confirmar. Con la opción apagada, la antigüedad máxima queda deshabilitada, pero se envía.
- El formulario se reemplaza con la respuesta del servidor; mensaje «Rige para las operaciones nuevas».

## 4. Pruebas

- Backend: `tests/modules/plataforma/test_p2_cu11_parametros_empresa.py` y `tests/integracion/test_multitenant.py` §P2-CU11 (fila por empresa con RLS, CHECK de la base).
- Web: `parametros-empresa.component.spec.ts` (payload literal del backend) y `app.routes.spec.ts`.

## 5. Limitaciones conocidas

- Hasta CU15, la reserva sigue venciendo 2 h después de su cita; el parámetro de horas aún no rige.
- El formulario de reserva web fija la cita en «mañana a las 11:30» y usa el id `1` si no hay sucursal elegida: se corrige en CU15.
- La lectura pública de los parámetros para el cliente llega con CU14.
