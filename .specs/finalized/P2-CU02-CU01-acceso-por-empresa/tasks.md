# Tareas — Acceso por empresa (P2-CU02 · P2-CU01)

## Bloque 0 — Preparación
- [x] **T-0-01:** Corregir `SI2-Parcial2.md` según §1.4 (copia previa en el scratchpad).
- [x] **T-0-02 (usuario):** En el editor SQL de Neon, en la rama principal y en `pruebas-multitenant`:
  ```sql
  SELECT lower(email), count(*) FROM fashionstore.usuarios GROUP BY 1 HAVING count(*) > 1;
  ```
  Debe devolver 0 filas. Si devuelve alguna, se decide qué cuenta se conserva antes de seguir.

## Bloque 1 — Backend (rama de pruebas)
- [x] **T-BE-01:** `0015_correo_global` (§A.1); `alembic heads` con una cabeza; `upgrade → downgrade → upgrade` en `pruebas-multitenant`.
- [x] **T-BE-02:** `core/tenant.py` y `database.py` sin empresa por defecto; `aplicar_tenant_del_token` según §A.4; `TENANT_POR_DEFECTO` eliminado.
- [x] **T-BE-03:** Login sin código (§A.3), con `empresas` en la respuesta.
- [x] **T-BE-04:** Registro con y sin `X-Tenant`; correo global en `cu01`, `cu20` y `cu33`.
- [x] **T-BE-05:** `GET /tenants`, `GET /tenants/{codigo}`, `GET /mis-empresas`, `POST /mis-empresas`.
- [x] **T-BE-06:** Pruebas unitarias y de integración de §A.6; suite completa en verde. (El humo de los GET con `X-Tenant` se hace en T-PR-03.)

## Bloque 2 — Web
- [x] **T-WEB-01:** `TenantService`, `tenantGuard`, `X-Tenant` en `authInterceptor`.
- [x] **T-WEB-02:** Rutas `/{codigo}`, redirecciones antiguas, `app.routes.spec.ts`.
- [x] **T-WEB-03:** Directorio en `/` con «Mis tiendas».
- [x] **T-WEB-04:** Login general y del portal, registro del portal, recuperación del portal y helper `rutaPortal` en las navegaciones del cliente.
- [x] **T-WEB-05:** `RegistroEnTiendaComponent` y manejo de `CLIENTE_NO_REGISTRADO`.
- [x] **T-WEB-06:** Nombre de la empresa en las cabeceras; `tsc`, `ng test` y `ng build` en verde.

## Bloque 3 — Producción (solo con confirmación explícita)
- [x] **T-PR-01 (usuario):** `alembic upgrade head` en la rama principal; `alembic current` = `0015`.
- [x] **T-PR-02 (usuario):** quitar `TENANT_POR_DEFECTO` del `.env` local y de Render, si existe.
- [x] **T-PR-03:** Push de backend y web; verificación de extremo a extremo (directorio, portal, login de cada rol, registro en una tienda, compra).

## Bloque 4 — Móvil
- [x] **T-MOV-01:** `EmpresaActual` y cabeceras en los 17 datasources.
- [x] **T-MOV-02:** DTO del login con `tenant` y `empresas` (payload literal) y `PantallaSeleccionEmpresa`.
- [x] **T-MOV-03:** Navegación login → selección → hub; «Cambiar de tienda»; registro sin empresa; nombre en la cabecera.
- [x] **T-MOV-04:** `dart analyze` y `flutter test` en verde (276/276); probado por el usuario.

## Cierre
- [x] **T-CI-01:** `CHANGELOG.md`, `CLAUDE.md`, constituciones web y móvil, promoción de la spec.
