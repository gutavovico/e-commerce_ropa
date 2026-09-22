---
name: fashionstore-backend-sdd
description: Desarrollo del BACKEND de FashionStore (e-commerce omnicanal de una cadena de ropa) con Python + FastAPI + PostgreSQL, guiado por Spec-Driven Development (SDD) - primero la especificación, después el código. Úsala SIEMPRE que se pida crear, modificar, revisar, depurar, probar o especificar algo del backend/API - routers, services, modelos ORM, schemas Pydantic, migraciones, endpoints /api/v1/..., autenticación y roles, catálogo y variantes talla/color, inventario por sucursal, reservas, carrito, checkout, punto de venta, pagos con Stripe, vestidor AR, recomendaciones/chatbot IA, reportes o bitácora - o cuando se mencione un caso de uso (CU01-CU35), una spec, requisitos, diseño o tareas del backend, aunque no se diga "SDD" ni "FashionStore". No aplica a Angular ni a Flutter.
---

# FashionStore · Backend con SDD

Esta skill guía cómo construir el backend de FashionStore de forma que **el código sea la consecuencia de una especificación aprobada**, no de un prompt improvisado. Un agente de IA interpreta literalmente lo que lee; si los requisitos quedan implícitos, inventa (deriva de arquitectura, reglas de stock incorrectas, endpoints incompatibles con los clientes). Por eso el trabajo se organiza así: el humano decide qué, por qué y dentro de qué límites; el agente ejecuta; la revisión humana se concentra en las **puertas de aprobación**, donde corregir cuesta menos.

## Alcance

- **Solo backend** (Python + FastAPI + PostgreSQL en Neon, desplegado en Render). Angular y Flutter son *consumidores del contrato de API*: no generes código de frontend; si la tarea los toca, define el contrato (rutas, JSON, códigos de error) y detente ahí.
- Lecturas bajo demanda (no las cargues todas siempre):
  - `references/arquitectura.md` → capas, estructura de carpetas, catálogo de routers/services por paquete. **Léelo antes de crear o tocar cualquier módulo.**
  - `references/dominio.md` → esquema de BD, estados, invariantes, contratos de API ya probados y **riesgos conocidos del diseño**. **Léelo antes de tocar inventario, reservas, ventas, pagos o autenticación.**
  - `references/plantillas-sdd.md` → plantillas de requirements/design/tasks, notación EARS, DoR/DoD. **Léelo al abrir una spec nueva.**

## Flujo SDD de cuatro fases, con puertas

Cada incremento (un CU, una historia, un cambio) recorre las cuatro fases. No es waterfall: la secuencia se aplica a *un incremento pequeño* —horas o días—, no a todo el proyecto, y hay feedback en cada puerta.

| Fase | Artefacto (en `specs/<CU>-<slug>/`) | Contenido | Puerta |
|---|---|---|---|
| 1. Requisitos | `requirements.md` | Problema, actores, comportamiento en EARS, casos de error, fuera de alcance | Humano aprueba |
| 2. Diseño | `design.md` | Endpoints y schemas, capas afectadas, datos/migraciones, transacciones, errores, no funcionales | Humano aprueba |
| 3. Tareas | `tasks.md` | Tareas atómicas ordenadas en oleadas, cada una con su verificación | Humano aprueba |
| 4. Implementación | código + tests | Ejecutar tareas; verificar contra la spec | Revisión contra la spec + DoD |

**Detente en cada puerta y pide aprobación explícita** antes de pasar a la siguiente. Si el usuario aprueba varias fases de golpe, procede, pero deja registrado en la spec qué se aprobó.

### Proporcionalidad: calibra el ritual al riesgo

Especificar de más es tan malo como no especificar. Clasifica antes de empezar y dilo en una línea:

- **Nivel 1 – trivial** (lookup CRUD como tallas/colores/categorías, un bug acotado, un campo nuevo sin reglas): 3–5 líneas de requisitos EARS + tareas en línea. Sin `design.md`.
- **Nivel 2 – feature típica** (consultas de catálogo CU05–CU09, promociones, proveedores, perfil): las tres specs, breves (una página cada una).
- **Nivel 3 – alto riesgo** (inventario, reservas, checkout, pagos y webhooks, autenticación/roles, migraciones que alteran datos): ciclo completo, sección de riesgos, transacciones y concurrencia explícitas, pruebas de concurrencia. **No se salta ninguna puerta.**

### Procedimiento ante cualquier solicitud

1. **Identifica** el/los CU y el paquete (ver `references/arquitectura.md`).
2. **Inspecciona el repositorio** antes de asumir nada: estructura, `requirements`/`pyproject`, cómo se nombran routers/services, cómo se hace auth. **Si el repo ya tiene una convención, gana el repo** sobre los defaults de esta skill; menciona la diferencia en una línea.
3. **Busca la spec**. Si existe, trabaja contra ella. Si tu cambio la contradice, propón un *delta* (ADDED / MODIFIED / REMOVED, ver plantillas) en vez de editarla en silencio.
4. **Si no existe**, clasifica el nivel, redacta la siguiente fase pendiente y pide aprobación.
5. **Verifica la Definition of Ready for AI** (abajo) antes de implementar.
6. **Implementa por oleadas**, con tests, y reporta contra los criterios de aceptación (qué pasó, qué no, qué supuestos hiciste).

**CU sin requisitos detallados.** En el documento del proyecto solo están detallados los CU de los ciclos 1 y 2. Reservas (CU12–14), pago electrónico (CU16), historial (CU17), IA (CU18–19), dashboards y reportes (CU28, 29, 34, 35) y recuperación de acceso (CU33) no tienen flujo detallado. Para ellos, la fase 1 es obligatoria y la implementación es *Ask First*: no inventes el flujo a partir del nombre del CU.

## Constitución del backend (principios que no se negocian en una tarea)

0. **E-COMMERCE EXCLUSIVO PARA MUJERES Y JERARQUÍA CANÓNICA:**
   - FashionStore es una plataforma **EXCLUSIVAMENTE DE MODA FEMENINA**. Todos los productos (`fashionstore.productos`), categorías, variantes y fotografías de catálogo pertenecen al segmento de alta costura para mujer. Prohibido registrar o asociar prendas masculinas.
   - Jerarquía relacional obligatoria: una **temporada** contiene una o más **colecciones** (`colecciones.id_temporada -> temporadas.id_temporada`), y una **colección** contiene múltiples **prendas de ropa** (`productos.id_coleccion -> colecciones.id_coleccion`).
   - Toda información provista a clientes web y móviles proviene estrictamente de la base de datos PostgreSQL real.

1. **Monolito modular en capas**: `Router → Service → ORM/Model`, un paquete por dominio (6 paquetes). No microservicios, no capas nuevas sin decisión explícita.
2. **Router delgado**: solo HTTP (validación con Pydantic, dependencia de auth, traducción de excepciones de dominio a códigos HTTP). Sin lógica de negocio y sin consultas ORM directas.
3. **Service = negocio + transacción**: cada caso de uso es una unidad de trabajo. No importa `Request`/`HTTPException`; lanza excepciones de dominio (`StockInsuficiente`, `ReservaNoCancelable`…) que el router traduce. Así la lógica se prueba sin levantar HTTP.
4. **ORM/Model = persistencia**: mapea tablas; no decide reglas de negocio.
5. **Contrato estable**: `/api/v1/<paquete>/<recurso>`, JSON, códigos coherentes (200 lectura/actualización, 201 creación, 400/422 validación, 401 sin sesión, 403 sin permiso, 404, 409 conflicto como stock insuficiente o SKU duplicado, 502 fallo de pasarela o IA). Un cambio incompatible es *Ask First*.
6. **Autorización por rol y por alcance**: roles `cliente`, `administrador`, `encargado_sucursal`, `cajero`, `proveedor`. Encargado y cajero operan **solo sobre su sucursal** (`usuarios.id_sucursal`); valídalo en el service, no confíes en lo que envíe el cliente.
7. **El servidor es la fuente de verdad de precios, totales, descuentos y sucursal.** Recalcula siempre; ignora montos enviados por el cliente.
8. **Dinero con `Decimal`/`NUMERIC`, nunca `float`.** Fechas en UTC (`TIMESTAMPTZ`).
9. **Todo cambio de stock deja rastro**: se escribe en `movimientos_inventario` en la **misma transacción** que modifica `inventario_sucursal`.
10. **Integraciones externas aisladas** (Stripe, servicio de IA) detrás de un cliente en `integrations/`, con timeout y manejo de error propio; nunca dentro de una transacción de BD larga.
11. **Secretos solo por variables de entorno** (Settings). Nunca en el repo, nunca en logs.
12. **Trazabilidad**: cada criterio de aceptación tiene al menos un test; cada test cita el criterio (`# AC-3`).

## Boundaries (marco de delegación)

**Siempre (Always)**
- Leer la spec y la referencia relevante antes de escribir código.
- Validar entradas con Pydantic y devolver errores con formato consistente.
- Usar una sola transacción en operaciones que tocan varias tablas.
- Escribir o actualizar los tests del CU y ejecutarlos antes de declarar terminado.
- Declarar supuestos y desviaciones respecto a la spec.

**Preguntar primero (Ask First)**
- Cambiar el esquema de BD: tablas, enums, triggers, vistas, o cualquier migración que borre/transforme datos.
- Añadir dependencias o cambiar el stack.
- Romper el contrato de un endpoint que ya consumen Angular/Flutter.
- Modificar reglas de inventario o transiciones de estado de venta/pago/reserva (ver riesgos en `dominio.md`).
- Decisiones de seguridad: expiración y revocación de tokens, política de contraseñas, permisos por rol.
- Implementar un CU sin requisitos detallados.
- Cualquier cosa que apunte a Stripe en modo *live* o a la BD de producción.

**Nunca (Never)**
- Commitear secretos (`.env`, claves de Stripe/IA, cadena de conexión de Neon).
- `UPDATE` directo de `inventario_sucursal` sin pasar por el service de inventario y sin movimiento asociado.
- Devolver `password_hash` o el `payload_respuesta` crudo de la pasarela al cliente.
- Construir SQL concatenando strings con datos del usuario.
- Confiar en precio, total, descuento o sucursal enviados por el cliente.
- Desactivar validaciones o tests para que algo "pase".
- Ejecutar migraciones o scripts destructivos contra producción sin confirmación explícita.
- Escribir código de Angular o Flutter.

## Convenciones rápidas

- **Nombres**: dominio en español, coherente con el documento (`catalogo`, `reservas`, `inventario_sucursal`); código Python en `snake_case`, clases en `PascalCase`. Un service por caso de uso o por agregado cohesionado, con nombres de acción (`crear_reserva`, `consultar_stock`).
- **Stack** — el documento fija FastAPI, PostgreSQL (Neon), un ORM sin nombrar y Stripe (sandbox). Defaults propuestos si el repo no dice otra cosa: SQLAlchemy 2.x, Alembic, Pydantic v2 + `pydantic-settings`, JWT con PyJWT, hash con bcrypt/argon2, `pytest` + `httpx`, `ruff`. Confírmalos si vas a introducirlos (Ask First).
- **Búsqueda difusa** de catálogo con `pg_trgm` (índice GIN ya definido sobre `productos.nombre`).
- **Stock concurrente**: descuenta con una sentencia atómica (`UPDATE … SET cantidad_disponible = cantidad_disponible - :n WHERE … AND cantidad_disponible >= :n`, verificando filas afectadas) o con `SELECT … FOR UPDATE`. Nunca leer-comprobar-escribir sin bloqueo.
- **Pagos**: el monto lo fija el servidor; el cambio de estado a pagado lo confirma el **webhook** de la pasarela (firma verificada, idempotente), no el navegador del cliente.

## Definition of Ready for AI (antes de implementar)

La tarea está lista para un agente solo si: la spec está aprobada; los criterios son verificables (se puede decidir si se cumplen viendo el resultado); el fuera de alcance está escrito; hay ejemplos de entrada/salida; las boundaries aplican; los riesgos de nivel 3 tienen decisión tomada; y se sabe qué comando prueba que está hecho. Si falta algo, **pregunta o especifica**; no rellenes el hueco con suposiciones.

## Definition of Done reforzada

"Compila" o "el agente dice que funciona" no es terminado. Terminado es: cada criterio de aceptación tiene test que pasa; sin secretos ni código muerto; migración incluida y reversible cuando aplica; contrato de API documentado (OpenAPI de FastAPI) y sin cambios rompientes no aprobados; código revisado **contra la spec** por un humano.

## Formato de respuesta

Al cerrar una tarea entrega: (1) nivel SDD aplicado y fase alcanzada, (2) qué se hizo mapeado a criterios de aceptación (AC-n → test), (3) supuestos y desviaciones, (4) decisiones pendientes para el humano. Sé breve; el detalle vive en los artefactos de `specs/`.

## Ejemplo mínimo

*Solicitud:* "Implementa el carrito (CU11)."
1. CU11 → paquete Compras y Pagos, Nivel 2 (toca stock pero solo lo *valida*, no lo descuenta).
2. Repo inspeccionado; sin spec previa → redacta `requirements.md` con EARS, por ejemplo: *Cuando el cliente agrega una variante, el sistema deberá verificar que `cantidad_disponible` en la sucursal indicada sea ≥ a la cantidad solicitada.* / *Si la cantidad supera lo disponible, entonces el sistema deberá responder 409 con el máximo permitido.*
3. Pide aprobación → `design.md` (`POST /api/v1/carrito/items`, schemas, un carrito activo por cliente) → aprobación → `tasks.md` en oleadas (modelos y schemas → service → router → tests) → implementa y reporta AC→test.
