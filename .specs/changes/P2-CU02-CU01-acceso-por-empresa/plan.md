# Plan — Acceso por empresa (P2-CU02 · P2-CU01)

## Orden
1. **Preparación:** comprobar que no hay correos repetidos (producción y pruebas) y corregir `SI2-Parcial2.md` (§1.4 de la spec).
2. **Backend** (gate 1):
   - `0015` ensayada en `pruebas-multitenant` con `upgrade → downgrade → upgrade`;
   - login, registro, `cu20`, `cu33`, endpoints de empresas y retirada de `TENANT_POR_DEFECTO`;
   - pruebas unitarias y de integración.
   Nada se despliega todavía: sin la web nueva, el portal dejaría de funcionar.
3. **Web** (gate 2): rutas `/{codigo}`, directorio, `TenantService`, guard, interceptor, login/registro del portal y «Registrarme en esta tienda».
4. **Producción** (con confirmación explícita):
   - el usuario aplica `alembic upgrade head` (`0015`) y se comprueba `alembic current`;
   - se elimina `TENANT_POR_DEFECTO` del `.env` si está declarada;
   - push conjunto de backend y web;
   - verificación de extremo a extremo.
5. **Móvil** (gate 3): selección de empresa, `EmpresaActual`, cabeceras en los 17 datasources, «Cambiar de tienda» y APK nuevo.
6. **Cierre:** `CHANGELOG.md`, `CLAUDE.md` (portal `/{codigo}`, correo global, `X-Tenant` obligatorio), constitución web y móvil, promoción de la spec.

## Archivos principales
- **Backend:**
  - `alembic/versions/0015_correo_global.py`;
  - `core/{tenant,database,config}.py`;
  - `modules/autenticacion_seguridad/{cu01,cu02,cu20,cu33}`;
  - `modules/plataforma/` (repositorio de empresas, `cu02_acceso_empresa/` con router y servicio de `/tenants` y `/mis-empresas`);
  - `main.py` (registro del router).
- **Web:**
  - `app.routes.ts`, `core/tenant/`, `core/guards/tenant.guard.ts`, `core/interceptors/auth.interceptor.ts`;
  - `modules/autenticacion_seguridad/cu02_iniciar_sesion/`, `modules/plataforma/directorio/`;
  - las cabeceras de los layouts.
- **Móvil:**
  - `lib/src/core/empresa_actual.dart`;
  - `cu02_iniciar_sesion/` (DTO y pantalla de selección);
  - `main.dart`, los 17 datasources y la cabecera del hub y el perfil.
