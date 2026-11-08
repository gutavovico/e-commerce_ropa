# Especificación Técnica Permanente: Fundación Multitenant — P2-CU13 (Aislar datos por empresa) · P2-CU12 (Validar suscripción y límites del plan)

**Fuente:** `SI2-Parcial2.md` (CU12, CU13, RF13, RF14, RNF02, RNF09, RNF16, RN01–RN18, RN51)
**Paquete de Dominio:** `plataforma` (modelo SaaS) · `core/tenant.py` (contexto transversal)
**Backend:** `app/core/tenant.py` · `app/core/database.py` · `app/core/deps.py` · `app/modules/plataforma/` · migraciones `0012`–`0014`
**Frontend / Mobile:** sin cambios en este ciclo (modo de transición; P2-CU02 los adaptará)
**Estado:** Aprobado y en producción (2026-11-08)
**Historial del cambio:** `.specs/finalized/P2-CU13-CU12-fundacion-multitenant/` · `CHANGELOG.md` defectos 53–56

---

## 1. Modelo de datos

| Tablas | Empresa | Notas |
| :--- | :--- | :--- |
| `tenants` | — | `codigo` único (RN03, `^[a-z0-9-]{3,60}$`), `estado` `activa`/`suspendida`/`baja` (RN08). Sin RLS. |
| `planes`, `funcionalidades`, `plan_funcionalidades` | Globales | Límites `max_sucursales_activas` y `max_empleados` (nulo = sin límite). Funcionalidades: `productos`, `ventas`, `reservas`, `operacion_offline`, `reportes_convencionales`, `reportes_ia`. |
| `suscripciones` (+ `historial_suscripcion`) | De la empresa | Como máximo una vigente (`prueba`/`activa`) por empresa (RN13); historial por evento (RN17). |
| `configuracion_tenant` | De la empresa | Vencimiento de reservas (24 h), plazo de cambio (15 días), operación sin conexión y antigüedad máxima (7 días). |
| `cliente_tenant` | De la empresa | Registro de un cliente (cuenta global) en una empresa. Carritos, reservas, ventas y demás tablas que referencian a un cliente apuntan aquí con FK compuesta. |
| `empleado_sucursal` | De la empresa | Sucursales autorizadas (RN07); una principal por empleado, reflejo de `usuarios.id_sucursal`. |
| 24 tablas de negocio | `id_tenant NOT NULL` | Valor por defecto del contexto; `UNIQUE (id_tenant, pk)`; FK compuestas entre ellas. |
| `usuarios` | `id_tenant` solo para empleados | Clientes y super administrador sin empresa (CHECK `chk_usuarios_tenant_segun_rol`). Correo único por empresa para empleados y global para cuentas sin empresa (RN05). |
| `bitacora` | `id_tenant` nulo para plataforma | Lo ve la empresa; los eventos de plataforma, solo el super administrador (RN51). |
| `ciudades`, `tallas`, `colores`, `clientes`, `codigos_recuperacion` | Globales | RN19 y cuenta de cliente global. |

## 2. Aislamiento en tres niveles (RNF02)

1. **Backend:** `get_db` resuelve la empresa (cabecera `X-Tenant`, o `TENANT_POR_DEFECTO` mientras dure la transición) y `get_current_user` aplica la del token, que manda. Token y cabecera de empresas distintas → 403 `TENANT_NO_COINCIDE`. Empresa inexistente → 404 `TENANT_NO_ENCONTRADO`; inactiva → 403 `TENANT_INACTIVO`. Token sin `id_tenant` → 401.
2. **Claves foráneas compuestas:** impiden relacionar filas de empresas distintas aunque el backend falle.
3. **Row Level Security:** política `aislamiento_tenant` en 31 tablas, contra `app.id_tenant`, `app.modo_plataforma` y `app.id_usuario`, que se fijan con `set_config(..., true)` al empezar cada transacción. Sin contexto, nada es visible ni escribible. Las vistas usan `security_invoker`.

La aplicación se conecta con `fashionstore_app` (NOBYPASSRLS, sin DDL). Las migraciones usan el dueño (`DATABASE_URL_MIGRACIONES`).

## 3. Autenticación (transición hasta P2-CU02)

- JWT `{sub, email, rol, id_tenant}`: la empresa del empleado; la de la sesión para un cliente registrado en ella; nula para el super administrador o un cliente sin registro.
- `POST /api/v1/autenticacion/login` admite `codigo_empresa` (opcional por ahora) y responde `tenant: {codigo, nombre}`.
- El registro (CU01) da de alta al cliente en la empresa de la petición.
- CU20: un empleado nuevo pertenece a la empresa de la sesión; cliente y empleado no se convierten entre sí (409 `CAMBIO_ROL_NO_PERMITIDO`).
- Carrito y reserva exigen que el cliente esté registrado en la empresa (403 `CLIENTE_NO_REGISTRADO`); un empleado en su propia empresa queda registrado automáticamente.

## 4. P2-CU12 — Validar suscripción y límites

`SuscripcionServicio.validar(db, funcionalidad=?, recurso=?)` y la dependencia `requiere_funcionalidad(...)`:
- 403 `SUSCRIPCION_NO_VIGENTE` si no hay suscripción en prueba o activa dentro de sus fechas (RN14); se detecta al consultar.
- 403 `FUNCIONALIDAD_NO_INCLUIDA`, con el plan que la incluye (RN16).
- 409 `LIMITE_PLAN_ALCANZADO`, con el límite y el uso en el mensaje (RN15; `sucursales` y `empleados`).
- El modo plataforma no se valida (CU12 A4); una petición sin usuario la deja al endpoint (401).

Conectado en: alta y reactivación de sucursales, alta de empleados, reservas, checkout, venta en caja y reportes por voz (`reportes_convencionales`). `reportes_ia` se conectará con P2-CU21.

## 5. Webhook de Stripe

Llega sin token: localiza el pago en modo plataforma, fija la empresa del pago y sale del modo plataforma. Los `PaymentIntent` nuevos llevan `metadata.id_tenant`.

## 6. Pruebas

- Unitarias: `tests/modules/plataforma/test_p2_cu12_cu13_unitarias.py`.
- Integración contra PostgreSQL real con el rol de la app: `tests/integracion/test_multitenant.py` (requiere `DATABASE_URL_PRUEBAS_APP`; se salta sin ella).
- `tests/test_esquema_bd.py` compara el ORM con `DATABASE_URL_PRUEBAS` si existe.

## 7. Pendiente en otros casos de uso

P2-CU02 (login con código obligatorio, selección de empresa en el móvil, portal web `/{codigo}` y fin de `TENANT_POR_DEFECTO`), P2-CU05 a P2-CU11 (gestión de empresas, planes, suscripciones, catálogos globales y parámetros), inventario sin temporada (RN21), totales calculados por la base de datos (RN26) y vencimiento de reservas a 24 h (RN25).
