# Especificación Técnica Permanente: Acceso por Empresa — P2-CU02 (Iniciar sesión) · P2-CU01 (Registrarse)

**Fuente:** `SI2-Parcial2.md` (CU01, CU02, CU12, RN03–RN06, RN08; corregido el 2026-11-08)
**Paquete de Dominio:** `plataforma` (`cu02_acceso_empresa`, `servicio_tenants`) · `autenticacion_seguridad` (CU01, CU02, CU20, CU33) · `core/tenant.py`
**Backend:** migración `0015_correo_global` · `app/core/{tenant,database,deps}.py` · `app/modules/plataforma/cu02_acceso_empresa/` · `app/modules/autenticacion_seguridad/cuentas.py`
**Frontend:** `src/app/core/tenant/` · `core/guards/tenant.guard.ts` · `core/layouts/portal/` · `modules/plataforma/directorio/` · `app.routes.ts`
**Mobile:** `lib/src/core/{empresa_actual,cliente_http_api}.dart` · `cu02_iniciar_sesion/presentacion/pantallas/pantalla_seleccion_empresa.dart`
**Depende de:** `P2-CU13-CU12-fundacion-multitenant.md`
**Estado:** Aprobado y en producción (2026-11-08)
**Historial del cambio:** `.specs/finalized/P2-CU02-CU01-acceso-por-empresa/` · `CHANGELOG.md` defectos 57–62

---

## 1. Decisiones

| ID | Decisión |
| :--- | :--- |
| A1 | Login con correo y contraseña, sin código de empresa, para todos los roles. |
| A2 | Correo único en toda la plataforma: quien sea empleado de una empresa y cliente de otra necesita dos correos. |
| A3 / A4 | Portal web por ruta `/{codigo}`; la raíz `/` es el directorio de tiendas disponibles. |
| A5 | El empleado inicia sesión en `/login` y va a su panel; si abre el portal de otra empresa, vuelve al suyo. |
| A6 / A7 / A8 | En el móvil, el cliente elige tienda tras el login; sin tiendas ve un estado vacío. El registro de cuentas sigue en el móvil (sin empresa); el registro **en una tienda** es exclusivo de la web. |
| A9 | El empleado pertenece a la empresa del administrador que crea su cuenta (CU20). |
| A10 | El token del cliente no lleva empresa: la tienda viaja en `X-Tenant` y cambiarla no exige la contraseña. |
| A11 / A12 | `cuenta_por_email` y `empresas_disponibles`, funciones `SECURITY DEFINER` mínimas, en lugar de abrir el modo plataforma. |
| A13 | Códigos de empresa reservados (rutas fijas de la web). |
| A14 | Las rutas antiguas del cliente (`/inicio`, `/bolsa`…) redirigen al directorio. |
| A15 / A16 | El login devuelve las tiendas del cliente; la selección del móvil se muestra siempre. |

## 2. Base de datos (migración `0015`)

- `uq_usuarios_email UNIQUE (lower(email))` sustituye a los índices parciales por empresa de `0013`.
- `fashionstore.cuenta_por_email(text) → (id_usuario, id_tenant)`: única forma de encontrar una cuenta antes de conocer su empresa (la RLS de `usuarios` oculta a los empleados de otras empresas).
- `fashionstore.empresas_disponibles() → (id_tenant, codigo, nombre)`: empresas `activa` con suscripción `prueba`/`activa` vigente hoy.
- Ambas: `SECURITY DEFINER`, `search_path` fijo, `REVOKE … FROM PUBLIC`, `EXECUTE` solo para `fashionstore_app`.
- `chk_tenants_codigo_reservado`: `admin`, `login`, `registro`, `recuperar-acceso`, `recuperar-password`, `iniciar-sesion`, `api`, `ar`, `static`, `assets`, `mis-tiendas`, `pago`, `plataforma`.

## 3. Contexto de empresa

| Quién | Empresa de la petición |
| :--- | :--- |
| Visitante sin token | La de `X-Tenant`; sin cabecera, ninguna (la RLS no devuelve datos de negocio). |
| Cliente | La de `X-Tenant`. Un token anterior a P2-CU02 con `id_tenant` se usa solo si no hay cabecera. |
| Empleado | La de su token; otra cabecera → 403 `TENANT_NO_COINCIDE`. |
| Super administrador | La de la petición (su panel llega con P2-CU05). |

## 4. Contratos

| Método y ruta | Auth | Comportamiento |
| :--- | :--- | :--- |
| `POST /api/v1/autenticacion/login` | Pública | Correo y contraseña (`codigo_empresa` se ignora). Empleado: empresa activa (`TENANT_INACTIVO`) y suscripción vigente (`SUSCRIPCION_NO_VIGENTE`). Respuesta: `tenant` (empresa del empleado o `null`) y `empresas` (tiendas disponibles del cliente). |
| `POST /api/v1/autenticacion/registrarse` | Pública | Con `X-Tenant`: crea la cuenta y la registra en la tienda (debe estar disponible). Sin cabecera: cuenta sin empresa. Token sin empresa. 409 `USUARIO_YA_EXISTE` si el correo existe en cualquier rol. |
| `GET /api/v1/tenants` | Pública | Directorio `[{codigo, nombre}]`. |
| `GET /api/v1/tenants/{codigo}` | Pública | Datos del portal; 404 `TENANT_NO_ENCONTRADO`, 403 `TENANT_INACTIVO`. |
| `GET /api/v1/mis-empresas` | Cliente | Tiendas disponibles en las que está registrado. 403 `SOLO_CLIENTES`. |
| `POST /api/v1/mis-empresas` | Cliente + `X-Tenant` | «Registrarme en esta tienda». 201 al registrar, 200 si ya lo estaba; 400 `TENANT_REQUERIDO`; 403 `SOLO_CLIENTES`, `TENANT_INACTIVO` o `CLIENTE_DESACTIVADO`. Queda en la bitácora (`REGISTRO_EN_TIENDA`). |

Recuperación de acceso (CU33) y alta de empleados (CU20) localizan la cuenta o comprueban el correo con `cuenta_por_email`.

## 5. Web

- Rutas, en este orden: directorio `''` → rutas fijas (`login`, `recuperar-*`, `admin/...`) → redirecciones antiguas → `:codigo` (`PortalComponent` + `tenantGuard`, con landing, `MainLayoutComponent` y sus 4 raíces, hojas, `login`, `registro`, `recuperar-password`) → `**`.
- `TenantService.tenantActual`: lo fija `tenantGuard` y se limpia al salir del portal (evento `ResolveEnd`). `authInterceptor` envía `X-Tenant` solo dentro del portal y abre «Registrarme en esta tienda» ante un 403 `CLIENTE_NO_REGISTRADO`.
- Enlaces del cliente con el pipe `rutaPortal` o `TenantService.ruta()`. Marca con `<app-marca-tienda />` y `TituloTiendaStrategy` (obtiene `TenantService` de forma diferida para evitar NG0200).
- Destinos del login: empleado → su panel (`destinoEmpleado`); cliente desde un portal → `/{codigo}/inicio`; cliente desde `/login` → directorio con «Mis tiendas».
- Tienda inexistente o no disponible → directorio con aviso (`?aviso=tienda-inexistente|tienda-no-disponible`).
- Vercel: `vercel.json` sin `cleanUrls`, o las rutas distintas de `/` dan 404 al recargarlas.

## 6. Móvil

- `PantallaLogin` → (cliente) `PantallaSeleccionEmpresa` → `PantallaPrincipalHub`; (empleado) → hub con la empresa de su cuenta.
- `EmpresaActual` guarda la tienda; `ClienteHttpApi` (cliente por defecto de todos los datasources) añade `X-Tenant` a las rutas `/api/...`. Se limpia al cerrar sesión.
- «Cambiar de tienda» en Perfil (solo clientes) vuelve a la selección sin cerrar sesión.
- Marca visible: `EmpresaActual.instancia.marca` (sin tienda, «FashionStore»).

## 7. Pruebas

- Backend: `tests/modules/plataforma/test_p2_cu02_acceso_empresa.py` (unitarias) y `tests/integracion/test_multitenant.py` §P2-CU02 (funciones de `0015`, índice global, códigos reservados, directorio, flujo del cliente entre dos tiendas, alta de empleado).
- Web: `core/tenant/tenant.spec.ts`, `app.routes.spec.ts`, `app.config.spec.ts` (arranque con la configuración real).
- Móvil: `test/p2_cu02_acceso_empresa_test.dart` (payloads literales del login y de `/mis-empresas`, `ClienteHttpApi`, pantalla de selección).

## 8. Limitaciones conocidas

- Tras «Registrarme en esta tienda» no se repite automáticamente la acción interrumpida; el cliente la vuelve a pulsar.
- La portada de cada tienda es todavía la de FASHION STORE; el contenido por empresa llega con Menshopping (RF15).
- El super administrador puede iniciar sesión, pero no tiene pantalla hasta P2-CU05.
- Las apps móviles anteriores a este cambio no envían la tienda y no ven datos: hay que instalar el APK nuevo.
