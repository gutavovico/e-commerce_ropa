# Checkpoints — Usuarios y sucursales por empresa (P2-CU03 · P2-CU04)

| Gate | Estado | Condición de paso |
| :--- | :--- | :--- |
| 0 — Especificación | 🟢 Aprobada el 2026-11-09 | B1–B10. Publicación conjunta, separada por commits (decisión del usuario). |
| 1 — Backend | 🟢 Aprobado (2026-11-09) | `pytest` **676/676** (unitarias e integración contra `pruebas-multitenant` con `fashionstore_app`): fuga de B1 cerrada, empleado con dos sucursales, uso del plan, bloqueo por empresa, ciudades de solo lectura. Deltas Δ1–Δ3. Condición: `pytest` completo en verde, incluida la integración contra la rama de pruebas (fuga de B1 cerrada y activación simultánea). |
| 2 — Web | 🟢 Aprobado (2026-11-09) | `tsc` sin errores; `ng test` **644/644** (usuarios: roles, casillas y principal, tabla; sucursales: uso del plan, aviso de límite, ciudades de solo lectura; caja: selector para un cajero con dos sucursales, con payload literal de `/mis-sucursales`); `ng build` correcto. Delta Δ4. Condición: `tsc`, `ng test` y `ng build` en verde. |
| 3 — Producción | ⚪ Pendiente del push del usuario | Push sin migración; comprobación con una cuenta de administrador. |
| 4 — Cierre | 🟢 Completo (2026-11-09) | `CHANGELOG.md` (sección P2-CU03/CU04 y defectos 63–65), `CLAUDE.md` (alcance de `usuarios`, RN07, bloqueo de límites, catálogos globales), spec permanente en `.specs/modules/plataforma/`, promoción a `finalized/`. |

## Deltas respecto a la spec

- **Δ1 (defecto 64):** `eliminar_usuario` consultaba `fashionstore.pedidos`, una tabla que no existe: eliminar un empleado sin movimientos de inventario daba 500. Se quitó la consulta.
- **Δ2:** RN07 sin pasar `db` a los 7 sitios: `SucursalesEmpleadoServicio.autorizadas(usuario)` lee `empleado_sucursal` con la sesión del propio usuario (`object_session`) y la guarda en el objeto durante la petición.
- **Δ3:** `TenantServicio.sincronizar_sucursal_principal` se retira (la sustituye `SucursalesEmpleadoServicio.reemplazar`). En inventario, ventas, reservas e indicadores el encargado puede consultar cualquiera de sus sucursales autorizadas; sin indicarla, la principal (como antes).
- **Δ4 (defecto 65):** la pestaña «Ciudades» de `/admin/sucursales` no se podía abrir: el binding `[class.border-[#ECE4D8]=` estaba sin cerrar y el navegador lanzaba `InvalidCharacterError` al pintar la tabla. Corregido al dejarla de solo lectura.
