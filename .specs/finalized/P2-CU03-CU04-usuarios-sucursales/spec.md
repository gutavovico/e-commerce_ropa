# Especificación Técnica: Usuarios y sucursales por empresa (P2-CU03 · P2-CU04)

**ID del cambio:** `P2-CU03-CU04-usuarios-sucursales`
**Fuente:** `SI2-Parcial2.md` CU03, CU04, RN04–RN07, RN11, RN15, PF-09, PF-15 y casos de prueba de CU03/CU04.
**Depende de:** `P2-CU02-CU01-acceso-por-empresa` (en producción, Alembic `0015`).
**Nivel SDD:** **3 (alto riesgo)**: corrige una fuga de datos entre empresas (§0.1) y cambia la autorización por sucursal en caja, inventario, ventas, reservas y reportes.
**Bloques:** Backend → Web (CU03 y CU04 son solo web). Sin bloque móvil (§1.3).
**Responsable:** Gustavo (`reparticion.md`).
**Estado:** 🟢 Aprobada e implementada (2026-11-09). Spec permanente: `.specs/modules/plataforma/P2-CU03-CU04-usuarios-sucursales.md`.
**Fecha:** 2026-11-09

---

## 0. Hallazgos (código y esquema al 2026-11-09)

### 0.1 Fuga entre empresas en la gestión de usuarios (grave)
La política RLS de `usuarios` (`0014`) deja ver **las cuentas sin empresa** a cualquier sesión:
`id_tenant IS NULL OR id_tenant = <empresa> OR <plataforma>`. Es necesario para el login y el
carrito, pero `cu20_usuarios_roles` no filtra nada más, así que **el administrador de cualquier
empresa**:
- ve en «Usuarios» a **todos los clientes de la plataforma** (de todas las tiendas) y al **super administrador**;
- puede **modificar su correo, desactivarlos, restablecer su contraseña o eliminarlos** (`PUT`, `PATCH /estado`, `POST /reset-password`, `DELETE`).

Restablecer la contraseña del super administrador desde una empresa cualquiera es una escalada de
privilegios. Se corrige en este cambio (B1): defecto 63 de `CHANGELOG.md`.

### 0.2 Backend
- **CU03:**
  - La API solo recibe `id_sucursal`, que hace de sucursal principal. `empleado_sucursal` existe desde `0013` pero solo refleja esa principal (`TenantServicio.sincronizar_sucursal_principal`).
  - `RolUsuarioEnum` admite `cliente`: el administrador puede crear clientes (contradice A4 de CU03).
  - Reactivar un empleado (`PATCH /estado` con `activo=true`) **no comprueba el límite de empleados** del plan.
  - Ninguna operación de `cu20` escribe en la bitácora.
- **CU04:**
  - El administrador tiene CRUD completo de `/admin/ciudades`. En el Parcial 2 las ciudades son globales y solo las administra el super administrador (CU08, de Tony).
  - A3 (no desactivar con reservas pendientes) **ya está** en `cambiar_estado_sucursal`.
  - Ninguna operación de `cu21` escribe en la bitácora.
- **Concurrencia del límite (PF-15, prueba CU04 paso 4):** `SuscripcionServicio.validar` cuenta sin bloquear. Dos activaciones simultáneas con un cupo libre pasan las dos.
- **RN07** se aplica comparando con `usuario.id_sucursal` (una sola sucursal) en 7 sitios:

| Sitio | Rol afectado |
| :--- | :--- |
| `compras_pagos/cu31_cu32_punto_venta/servicio.py` (`resolver_sucursal`, `_verificar_alcance`) | cajero, encargado |
| `compras_pagos/cu16_realizar_pago/servicio.py` (`_verificar_alcance_caja`) | cajero, encargado |
| `gestion_operativa/cu24_inventario_stock/servicio.py` (`_validar_acceso_sucursal` y listado) | encargado |
| `comercial/cu28_ventas_reservas/servicio.py` (`resolver_alcance_sucursal` y dos comprobaciones) | encargado |
| `comercial/cu29_indicadores/servicio.py` | encargado |
| `comercial/cu31_reportes_voz/servicio.py` | encargado |

### 0.3 Web
- `usuarios-admin`: selector de rol con «Cliente» y un único selector de sucursal.
- `sucursales-admin`: pestaña «Ciudades» con alta, edición y baja; no muestra el uso del plan.
- La caja (`/admin/pos`) fija la sucursal del cajero; no hay selector para él.

### 0.4 Documento
`SI2-Parcial2.md` aún contradice RN05 en CU03 (paso 5: «correo único en la empresa») y en su caso
de prueba (paso 4: acepta el mismo correo en otra empresa).

---

## 1. Alcance

### 1.1 Qué entrega
1. Gestión de usuarios limitada a los **empleados de la propia empresa** (B1).
2. Roles asignables: administrador, encargado de sucursal y cajero (B2).
3. **Varias sucursales autorizadas** con una principal para encargados y cajeros (B3).
4. **RN07** aplicado con las sucursales autorizadas en los 7 sitios de §0.2 (B4), y la caja web con selector de sucursal cuando el empleado tiene más de una.
5. Ciudades de **solo lectura** para el administrador (B6).
6. **Uso del plan** en la pantalla de sucursales (B7).
7. Límites del plan **seguros ante solicitudes simultáneas** y límite de empleados al reactivar (B8).
8. **Bitácora** de usuarios y sucursales (B9).
9. Corrección de `SI2-Parcial2.md` (§0.4).

### 1.2 Fuera de alcance
- Gestión de ciudades del super administrador: CU08 (Tony).
- Consulta completa de suscripción y uso: CU09 (Tony). Aquí solo el uso de sucursales.
- CU04 A3 «operaciones sin sincronizar»: se añade en el bloque 3, cuando exista esa tabla.
- Gestión de clientes por el administrador (no la pide CU03).

### 1.3 Móvil
Sin cambios. El reporte por voz del móvil (`cu31_reportes_voz`) usa el backend y sigue funcionando:
un encargado con una sola sucursal se comporta igual que hoy, y con varias puede elegir cualquiera
de las autorizadas.

---

## 2. Decisiones

| ID | Decisión |
| :--- | :--- |
| **B1** | `cu20` solo lista, consulta y modifica usuarios con `id_tenant` = empresa de la sesión y rol de empleado. Cualquier otro id → **404** `USUARIO_NO_ENCONTRADO` (no se revela que existe). El filtro de rol del listado deja de ofrecer «cliente». |
| **B2** | Al crear o editar, el rol solo puede ser `administrador`, `encargado_sucursal` o `cajero`. `cliente` → **422** `ROL_NO_PERMITIDO` (A4: los clientes se registran solos). `super_administrador` ya no existe en el enum de entrada. |
| **B3** | Encargado y cajero: `sucursales_autorizadas: list[int]` (al menos una, activas y de la empresa → si no, `SUCURSAL_INVALIDA` o `SUCURSAL_REQUERIDA`) e `id_sucursal_principal`, que debe estar en la lista. `usuarios.id_sucursal` sigue siendo la principal. **El administrador opera en todas** las sucursales de su empresa: no lleva lista. **Compatibilidad:** si llega solo `id_sucursal` (cliente antiguo), equivale a `[id_sucursal]` con esa principal. |
| **B4** | Nuevo `SucursalesEmpleadoServicio` (archivo nuevo `modules/plataforma/servicio_sucursales_empleado.py`, de Gustavo): `autorizadas(db, usuario) → set[int] \| None` (`None` = todas, para el administrador) y `exigir(db, usuario, id_sucursal)`. Los 7 sitios de §0.2 pasan a usarlo y **conservan sus códigos de error** actuales (`SUCURSAL_AJENA`, etc.). Si el empleado no indica sucursal, se usa la principal, como hoy. |
| **B5** | `GET /api/v1/mis-sucursales` (empleado): sus sucursales autorizadas activas, con la principal marcada. Lo usa la caja web para el selector. |
| **B6** | `/admin/ciudades`: el administrador conserva el `GET`. `POST`, `PUT` y `DELETE` se **retiran** de `cu21` y la pestaña web queda de solo lectura con el aviso de CU04 A4 («pide el alta al super administrador»). Tony crea la gestión en CU08 sin reutilizar estos endpoints. |
| **B7** | `SuscripcionServicio.uso(db, recurso) → {uso, limite, plan}` (método nuevo en `cu12`, de lectura) y `GET /api/v1/admin/sucursales/uso-plan`. **CU09 de Tony reutiliza `uso`**: se le avisa. |
| **B8** | En `SuscripcionServicio.validar` con `recurso`, antes de contar: `pg_advisory_xact_lock(hashtext('limite_' \|\| recurso), id_tenant)`. El bloqueo dura hasta el `commit` de la operación, así que la segunda solicitud cuenta ya con la primera. No requiere permisos nuevos y funciona con PgBouncer en modo transacción. Reactivar un empleado valida `recurso="empleados"`. |
| **B9** | Bitácora con `registrar_evento_seguro` (sin `RETURNING`, regla del defecto 57) en cada alta, modificación, cambio de estado, restablecimiento de contraseña y eliminación de usuarios y sucursales. Sin la contraseña en el payload. |
| **B10** | **Sin migración.** `empleado_sucursal` ya tiene todo lo necesario (PK `(id_empleado, id_sucursal)`, índice único de principal, FK compuestas y RLS). Si la implementación demostrara lo contrario, se avisa a Tony antes de tomar la `0016`. |

---

## 3. Contratos

### 3.1 Usuarios (`/api/v1/admin/usuarios`, rol administrador)

**Entrada (crear y editar):**
```json
{
  "nombres": "Ana", "apellidos": "Ruiz", "email": "ana@tienda.com", "password": "…",
  "rol": "cajero",
  "sucursales_autorizadas": [3, 5],
  "id_sucursal_principal": 3
}
```
En la edición todos los campos son opcionales; si llega `sucursales_autorizadas`, sustituye la lista completa.

**Salida (detalle y resumen):** los campos actuales (`id_sucursal`, `sucursal_nombre`, `sucursal_ciudad` describen la principal) más:
```json
"sucursales_autorizadas": [
  {"id_sucursal": 3, "nombre": "Centro", "es_principal": true},
  {"id_sucursal": 5, "nombre": "Norte",  "es_principal": false}
]
```

**Errores nuevos:** 422 `ROL_NO_PERMITIDO`; 422 `SUCURSAL_PRINCIPAL_INVALIDA` (la principal no está en la lista); 404 para usuarios fuera del alcance de B1. El resto se mantiene (`EMAIL_DUPLICADO` 409, `LIMITE_PLAN_ALCANZADO` 409, `SUCURSAL_INVALIDA`, `SUCURSAL_REQUERIDA`, `ULTIMO_ADMINISTRADOR`…).

**Filtro `id_sucursal` del listado:** empleados autorizados en esa sucursal (no solo los de principal).

### 3.2 Sucursales y ciudades
| Método y ruta | Cambio |
| :--- | :--- |
| `GET /api/v1/admin/ciudades` | Sin cambios (administrador). |
| `POST/PUT/DELETE /api/v1/admin/ciudades…` | **Retirados** (B6). |
| `GET /api/v1/admin/sucursales/uso-plan` | Nuevo: `{"uso": 2, "limite": 2, "plan": "Básico"}` (`limite: null` = sin límite). |
| `PATCH /api/v1/admin/sucursales/{id}/estado` | Bloqueo de B8 al activar. |
| `GET /api/v1/mis-sucursales` | Nuevo (B5): `[{"id_sucursal": 3, "nombre": "Centro", "ciudad": "Madrid", "es_principal": true}]`. Roles: administrador (todas las activas), encargado y cajero (sus autorizadas activas). |
| `GET /api/v1/admin/sucursales` | `total_empleados` cuenta empleados **autorizados** en la sucursal. |

---

## 4. Web

- **Usuarios:**
  - Selector de rol sin «Cliente», tanto en el formulario como en el filtro.
  - Encargado o cajero: casillas de sucursales activas y un botón de opción para la principal entre las marcadas. Exige al menos una.
  - La tabla muestra la principal y «+N» con las demás.
- **Sucursales:**
  - Encabezado con «N de M sucursales activas (plan X)», o «sin límite».
  - En el límite, el botón «Activar» y el alta muestran el aviso de CU04 A1, sin depender solo del 409.
  - Pestaña «Ciudades» de solo lectura, con el aviso de A4.
- **Caja (`/admin/pos`):** si `mis-sucursales` devuelve más de una, el cajero o encargado elige sucursal, igual que el administrador hoy. Con una sola, no cambia nada.
- Importes y conteos vienen del servidor; los textos siguen el tono del panel.

## 5. Pruebas

- **Unitarias (backend):**
  - B1: el listado y cada operación sobre un cliente, el super administrador o un empleado de otra empresa devuelven 404.
  - B2, B3 y la compatibilidad con `id_sucursal`.
  - B4 en los 7 sitios: autorizada pasa, no autorizada se rechaza con el código actual, y el administrador pasa siempre.
  - B6: las rutas retiradas dan 404 o 405.
  - B9: se llama a la bitácora sin contraseña.
- **Integración (`tests/integracion/test_multitenant.py`, rama de pruebas):**
  - El administrador de la empresa A no ve ni modifica clientes, el super administrador ni empleados de B.
  - Un empleado con dos sucursales opera en ambas y no en una tercera.
  - **Activación simultánea** con un cupo libre: dos hilos, cada uno con su sesión `fashionstore_app` → exactamente una tiene éxito (PF-15).
  - Reactivar un empleado en el límite → 409.
- **Web:** specs de `usuarios-admin` (rol, casillas, principal), `sucursales-admin` (uso del plan, ciudades de solo lectura) y del selector de la caja.
- **Contrato:** los mocks de la web usan payloads literales copiados de la respuesta del backend.

## 6. Coordinación con Tony
- `cu12_validar_suscripcion/servicio.py` gana `uso()` y el bloqueo de B8. Tony lo reutiliza en CU09 y CU10.
- `plataforma/servicio_sucursales_empleado.py` es nuevo y de Gustavo.
- Las rutas de escritura de ciudades desaparecen de `cu21`. CU08 las crea en su panel.
