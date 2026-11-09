# Especificación Técnica Permanente: Usuarios y Sucursales por Empresa — P2-CU03 (Gestionar usuarios y roles) · P2-CU04 (Gestionar sucursales)

**Fuente:** `SI2-Parcial2.md` (CU03, CU04, RN04–RN07, RN11, RN15, PF-09, PF-15; corregido el 2026-11-09)
**Paquete de Dominio:** `autenticacion_seguridad` (`cu20_usuarios_roles`) · `gestion_operativa` (`cu21_sucursales_ciudades`) · `plataforma` (`servicio_sucursales_empleado`, `cu12_validar_suscripcion`)
**Backend:** sin migración (usa `empleado_sucursal` de `0013`) · `app/modules/plataforma/servicio_sucursales_empleado.py` · `cu20_usuarios_roles/` · `cu21_sucursales_ciudades/` · `cu12_validar_suscripcion/{servicio,repositorio}.py`
**Frontend:** `cu20_usuarios_roles/` · `cu21_sucursales_ciudades/` · `compras_pagos/cu31_cu32_punto_venta/`
**Mobile:** sin cambios (CU03 y CU04 son solo web)
**Depende de:** `P2-CU13-CU12-fundacion-multitenant.md`, `P2-CU02-CU01-acceso-por-empresa.md`
**Estado:** Aprobado (2026-11-09)
**Historial del cambio:** `.specs/finalized/P2-CU03-CU04-usuarios-sucursales/` · `CHANGELOG.md` defectos 63–65

---

## 1. Decisiones

| ID | Decisión |
| :--- | :--- |
| B1 | «Usuarios» solo lista, consulta y modifica empleados (`administrador`, `encargado_sucursal`, `cajero`) de la empresa de la sesión. Cualquier otra cuenta → 404 `USUARIO_NO_ENCONTRADO`. |
| B2 | Solo se asignan roles de empleado; `cliente` → 422 `ROL_NO_PERMITIDO`. |
| B3 | Encargado y cajero: `sucursales_autorizadas` (al menos una, activas, de la empresa) e `id_sucursal_principal` entre ellas; `usuarios.id_sucursal` = principal. El administrador opera en todas. `id_sucursal` solo equivale a `[id_sucursal]`. |
| B4 | RN07 con `SucursalesEmpleadoServicio.autoriza(usuario, id_sucursal)` en caja, cobro en efectivo, inventario, ventas y reservas, indicadores y reportes por voz; cada sitio conserva su código de error. Sin sucursal indicada, la principal. |
| B5 | `GET /mis-sucursales`: sucursales activas en las que opera el empleado, la principal primero. |
| B6 | Ciudades de solo lectura para el administrador; su gestión es de P2-CU08. |
| B7 | `GET /admin/sucursales/uso-plan` → `{uso, limite, plan}` (`limite: null` = sin límite), con `SuscripcionServicio.uso()`. |
| B8 | Límites del plan serializados por empresa y recurso (`pg_advisory_xact_lock`); reactivar un empleado valida el límite de empleados. |
| B9 | Bitácora: `USUARIO_CREADO`, `USUARIO_MODIFICADO`, `USUARIO_ESTADO`, `USUARIO_PASSWORD_RESET`, `USUARIO_ELIMINADO`, `SUCURSAL_CREADA`, `SUCURSAL_MODIFICADA`, `SUCURSAL_ACTIVADA`, `SUCURSAL_DESACTIVADA`, `SUCURSAL_ELIMINADA`. Nunca contraseñas. |

## 2. Contratos

| Método y ruta | Auth | Comportamiento |
| :--- | :--- | :--- |
| `GET/POST /api/v1/admin/usuarios`, `GET/PUT/DELETE /admin/usuarios/{id}`, `PATCH …/estado`, `POST …/reset-password` | Administrador | B1–B3, B8, B9. Entrada con `sucursales_autorizadas` e `id_sucursal_principal`; salida con `sucursales_autorizadas: [{id_sucursal, nombre, es_principal}]`. Errores: 404 fuera de alcance, 422 `ROL_NO_PERMITIDO`, 422 `SUCURSAL_PRINCIPAL_INVALIDA`, 422 `SUCURSAL_REQUERIDA`, 422 `SUCURSAL_INEXISTENTE_O_INACTIVA`, 409 `EMAIL_DUPLICADO`, 409 `LIMITE_PLAN_ALCANZADO`. Filtro `id_sucursal`: autorizados en esa sucursal. |
| `GET /api/v1/mis-sucursales` | Administrador, encargado, cajero | `[{id_sucursal, nombre, ciudad, es_principal}]`. |
| `GET /api/v1/admin/sucursales/uso-plan` | Administrador | `{uso, limite, plan}`. |
| `GET /api/v1/admin/ciudades` | Administrador | Solo lectura (`POST/PUT/DELETE` → 405). |
| `POST /admin/sucursales`, `PATCH …/estado` | Administrador | Límite de sucursales activas con bloqueo por empresa (409 `LIMITE_PLAN_ALCANZADO`). `total_empleados` cuenta empleados autorizados. |

## 3. Web

- **Usuarios:** roles de empleado; casillas de sucursales activas con su opción «Principal»; no envía un encargado o cajero sin sucursales; la tabla muestra la principal y «+N».
- **Sucursales:** tarjeta con el uso del plan; en el límite, «Activar» y «Nueva Boutique» avisan (CU04 A1) sin llamar al servidor; pestaña «Ciudades» de solo lectura.
- **Caja:** con más de una sucursal autorizada, el cajero o encargado elige sucursal (empieza en la principal) y se envía en todas las peticiones; con una, nada cambia.

## 4. Pruebas

- Backend: `tests/modules/autenticacion_seguridad/test_cu20_usuarios_roles.py` (B1 con cada operación, B2, B3, B8, B9), `tests/modules/gestion_operativa/test_cu21_sucursales_ciudades.py` (B5–B7, B9), `tests/modules/plataforma/test_p2_cu03_sucursales_autorizadas.py` (RN07 en los 7 sitios), `tests/integracion/test_multitenant.py` §P2-CU03 · P2-CU04.
- Web: specs de `usuarios-admin`, `sucursales-admin` (componente y servicio) y `punto-venta` (cajero con dos sucursales, payload literal de `/mis-sucursales`).

## 5. Limitaciones conocidas

- CU04 A3 «operaciones sin sincronizar»: llega con el bloque sin conexión (CU14–CU20).
- Eliminar una sucursal borra en cascada sus autorizaciones adicionales; si era la principal de alguien, lo impide la comprobación de empleados asignados.
- El móvil no cambia: el reporte por voz usa la sucursal dictada si está autorizada, o la principal.
