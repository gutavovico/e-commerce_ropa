# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

FashionStore es un e-commerce omnicanal de alta costura femenina. Monorepo con tres aplicaciones
que comparten una única base de datos PostgreSQL desplegada en Neon.

| Directorio | Stack | Rol |
| :--- | :--- | :--- |
| `Ec-backend/` | Python ≥ 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic | API REST, única fuente de verdad de datos e importes |
| `Ec-frontend/` | Angular 21 · standalone · Signals · Tailwind | Cliente web |
| `Ec-mobile/` | Flutter 3.x · Dart 3 | Cliente móvil (rol Cliente; incluye además la pantalla de reportes por voz de CU31) |

El idioma del dominio es el español: nombres de clase, variables, comentarios y documentación.

---

## Comandos

### Backend (`Ec-backend/`)

El entorno virtual vive en `.venv/`. En este repositorio se invoca por ruta directa:

```bash
./.venv/Scripts/python.exe -m pytest -q          # suite completa
./.venv/Scripts/python.exe -m pytest tests/modules/compras_pagos -q   # un paquete
./.venv/Scripts/python.exe -m pytest tests/modules/compras_pagos/test_cu15_checkout.py::test_tramitacion_exitosa_crea_venta_pendiente -v   # un test
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

`ruff` está declarado en el extra `dev` de `pyproject.toml` pero **no está instalado** en el
`.venv` actual; requiere `pip install -e ".[dev]"` antes de usarlo.

`pyproject.toml` fija `pythonpath = ["app", "."]`, de modo que los imports son `from core...` y
`from modules...` sin el prefijo `app.`.

### Frontend Web (`Ec-frontend/`)

```bash
npm start                      # ng serve con proxy a 127.0.0.1:8000
npx tsc -p tsconfig.app.json --noEmit
npx ng test --watch=false      # Vitest sobre el builder de Angular
npx ng test --watch=false --include="src/app/app.routes.spec.ts"   # un archivo
npx ng build
```

**No ejecutes `npx vitest` directamente**: no carga el `initTestEnvironment` de Angular y toda la
suite falla con «Need to call TestBed.initTestEnvironment() first». Usa siempre `ng test`.

### Mobile (`Ec-mobile/`)

```bash
dart analyze                                  # debe terminar en «No issues found!»
flutter test
flutter test test/shopping_bag_test.dart
flutter run --dart-define=API_URL=http://10.0.2.2:8000 --dart-define=WEB_URL=http://10.0.2.2:4200
```

Sin `--dart-define`, `api_config.dart` apunta en Android/iOS a **producción**: `API_URL` → Render y
`WEB_URL` → Vercel (origen de los recursos relativos `/ar/...` de `modelo_ar_url`). En escritorio y
web usa `localhost`.

CU10 (vestidor) en móvil: Motor 1 = `camera` + `google_mlkit_pose_detection` (iOS ≥ 15.5); Motor 2 =
WebView con `assets/vestidor/decart_vton.html`, que pide el token con `POST /vestidor/token?canal=movil`
(sin `allowedOrigins`: la página es `file://` y su `Origin` es `null`). Solo se prueba de verdad en
dispositivo físico.

---

## Metodología: Spec-Driven Development

El desarrollo se organiza por **caso de uso** (CU01, CU05, CU11…), no por capa técnica.

- `.agents/skills/fashionstore-{backend,frontend,mobile}-sdd/` — la «constitución» de cada stack:
  reglas de arquitectura, convenciones, listas de *Never* y *Ask First*, y los tokens de diseño.
  **Léelas antes de escribir código en un stack nuevo.**
- `.specs/changes/<id>/` — cambios en curso, con `spec.md`, `plan.md`, `tasks.md` y `checkpoint.md`
  (o un único `change-*.md` que agrupe las cuatro secciones).
- `.specs/finalized/<CU>/` — casos de uso terminados.
- `.specs/modules/<paquete>/<CU>-*.md` — especificación permanente tras la promoción.
- `.specs/architecture/directriz-navegacion-hub-and-spoke.md` — directriz de navegación, transversal
  y obligatoria en web y móvil.
- `CHANGELOG.md` — bitácora numerada de defectos corregidos. Al arreglar un bug real, añade su
  entrada con causa y solución.

**Colisión de numeración de CU.** En `SI2-Parcial1.md`, CU31 es «Registrar venta presencial» y
CU32 «Procesar venta presencial y emitir comprobante», mientras que CU34 es «Reportes» (con comandos de
voz) y CU35 «Exportar». En el código conviven los dos nombres:
- `cu31_cu32_punto_venta` (paquete `compras_pagos`, ruta web `/admin/pos`) es el POS de caja: CU31 + CU32
  del documento. Spec en `.specs/finalized/CU31-CU32-punto-de-venta-presencial/` y
  `.specs/modules/compras_pagos/CU31-CU32-punto-de-venta-presencial.md`. Solo web.
- `cu31_reportes_voz` (paquete `comercial`, `.specs/finalized/CU31/`) cubre CU34 + CU35 en web y móvil.
  Su spec permanente es `.specs/modules/comercial/CU31-reportes-voz.md`; los documentos de
  `finalized/CU31/` que excluyen el móvil están marcados como superados.

Cuando el usuario diga «CU31», aclara a cuál se refiere.

**Flujo de gate:** el usuario aprueba la especificación antes de que se escriba código, y aprueba
cada bloque (Backend → Web → Mobile) antes de pasar al siguiente. No cruces ese límite sin permiso
explícito.

---

## Reglas que esta base de código ya ha pagado caro

### La base de datos manda, no la migración inicial

`alembic/versions/0001_base_ddl.py` **por sí sola no describe el esquema desplegado**: recoge el DDL
inicial de la especificación y difiere del estado final en nombres de columna (`estado_activo`
frente a `activa`, `nit_rut` frente a `nit`), en tipos (`TIMESTAMPTZ` frente a `DATE`) y en las
tablas y columnas añadidas por `0002`–`0011`. Confiar en `0001` aisladamente ya tumbó catálogo,
búsqueda y colecciones en producción (defecto 34 del `CHANGELOG.md`).

Antes de mapear una tabla, **consulta el esquema real** (o `Ec-backend/specs/diseno_fisico_neon.sql`):

```bash
./.venv/Scripts/python.exe -c "
import os, sys; sys.path.insert(0,'app')
from dotenv import load_dotenv; load_dotenv()
from sqlalchemy import create_engine, text
with create_engine(os.environ['DATABASE_URL']).connect() as c:
    for r in c.execute(text('''SELECT column_name, data_type FROM information_schema.columns
        WHERE table_schema='fashionstore' AND table_name='ventas' ORDER BY ordinal_position''')):
        print(r)
"
```

Cuando el nombre real difiera del término de dominio, pásalo como primer argumento posicional y
conserva el atributo Python: `mapped_column("estado_activo", Boolean, ...)`.

`tests/test_esquema_bd.py` es la guardia permanente: compara `Base.metadata` contra
`information_schema` y falla ante columnas inexistentes o familias de tipo incompatibles. Se salta
sola cuando no hay `DATABASE_URL` en `Ec-backend/.env`.

**La cadena de Alembic es lineal desde el defecto 45 del `CHANGELOG.md`:**
`0001 → … → 0008 → 0009 → 0009a → 0010 → 0010a → 0011`. `0009a` (CU28) y `0010a` (CU29) son
marcadores vacíos; los IDs llevan sufijo porque `0009` y `0010` ya pertenecían a migraciones con DDL
real. La base de Neon está sellada en `0011` (la única cabeza), por lo que `alembic upgrade head`
—que `render.yaml` ejecuta en `preDeployCommand`— es un no-op sobre ella. **Nueva migración:**
`down_revision = "0011"` e ID nuevo y único (`0012`); comprueba `alembic heads` antes de enviarla.
La cadena completa `0001 → 0011` sí reproduce el esquema desplegado en Neon (las 31 tablas, 236
columnas, 10 enums, 46 índices, 3 vistas y el trigger); dos tablas de Neon aún no tienen modelo
ORM (`historial_navegacion` y `solicitudes_reporte_ia`; `sesiones_vestidor_virtual` e
`interacciones_chatbot` ya lo tienen, en CU10 y CU19), por lo que cualquier `--autogenerate` debe
revisarse antes de aplicarse.

### Los tests verdes no prueban que el contrato funcione

Toda la suite del backend mockea la sesión de base de datos, y durante un tiempo los DTO de Flutter
se construían con sus constructores sin ejercitar `fromJson`. Resultado: las tres suites en verde
mientras CU12 devolvía 422 en cada intento desde el móvil.

- Los mocks de respuesta deben ser **payloads literales copiados del backend**, no objetos armados
  a mano sobre la interfaz del cliente (ver `Ec-mobile/test/mocks/mock_carrito_api.dart`).
- FastAPI serializa `Decimal` como cadena JSON. En Dart se parsea con tolerancia; en TypeScript los
  importes se tipan como `string` y no se convierten a `number`.
- Para cambios que tocan base de datos, verifica end-to-end contra Neon además de los tests.

### Navegación Hub-and-Spoke

Existen **exactamente cuatro pantallas raíz**: Inicio, Buscar, Catálogo y Perfil. Solo ellas
muestran la navegación principal y tienen prohibido el botón de retroceso.

- **Web:** las raíces cuelgan de `MainLayoutComponent`; todo lo demás (`/bolsa`, `/colecciones`,
  `/productos/:id`) se declara al nivel raíz de `app.routes.ts`, con su propio `← Volver` vía
  `Location.back()`. `app.routes.spec.ts` guarda el orden de rutas: la landing (`path: ''` con
  `pathMatch: 'full'`) debe ir **antes** del bloque del layout, y el comodín `**` al final.
- **Mobile:** el `BottomNavigationBar` de 4 ítems pertenece en exclusiva a `PantallaPrincipalHub`.
  Las hojas se abren con `Navigator.push`, llevan `leading: BackButton()` y no declaran barra de
  navegación. Un `bottomNavigationBar` con una **barra de acción** (total + botón principal) sí es
  admisible, como en `ShoppingBagScreen`.

### Cero datos inventados

Toda prenda, precio, boutique y existencia debe proceder de PostgreSQL. Está prohibido rellenar
huecos con literales o *fallbacks* ficticios: la interfaz llegó a ofrecer boutiques y stock que el
backend rechazaba después. Si la base no tiene datos, la pantalla muestra su estado vacío.

El catálogo es **exclusivamente femenino**: ni prendas, ni modelos, ni imágenes de respaldo
masculinas. La marca se escribe siempre «FASHION STORE».

---

## Arquitectura

### Backend

Monolito modular por capas: `Router → Servicio → Repositorio → ORM`.

```
app/modules/<paquete_dominio>/<cuNN_slug>/{router,servicio,repositorio,esquemas}.py
app/modules/<paquete_dominio>/modelos.py      # ORM a nivel de paquete
app/core/{config,database,deps,errors,security,token_blacklist}.py
```

Paquetes actuales: `autenticacion_seguridad`, `catalogo`, `reservas`, `compras_pagos` (incluye el POS
`cu31_cu32_punto_venta`), `comercial` (CU27–CU29 y `cu31_reportes_voz`), `gestion_operativa` (CU21–CU26)
y `seguridad` (CU30 bitácora).
Las integraciones externas viven en `app/integrations/` (`stripe_service.py` y `gemini_service.py`,
ambos con simulador/fallback determinista cuando falta la clave).

- **Router:** solo HTTP. Sin lógica de negocio ni consultas ORM.
- **Servicio:** negocio y transacción; una unidad de trabajo por caso de uso. No importa `fastapi`;
  lanza excepciones de dominio de `core/errors.py`, que `main.py` traduce a códigos HTTP
  (`NotFoundError`→404, `ConflictError`→409, `AuthorizationError`→403, `DomainError`→400).
- El acceso entre paquetes va por el **servicio** del otro paquete, nunca por sus modelos.

Cuidado con dónde vive un modelo antes de declararlo: `VentaORM` y `VentaDetalleORM` están en
`modules/catalogo/modelos.py` (los introdujo CU18). Redeclararlos en otro paquete produce
`InvalidRequestError` por tabla duplicada; extiéndelos donde ya están y reexpórtalos.

**Inventario y dinero:**
- Todo importe es `Decimal`/`NUMERIC`. Nunca `float`.
- El servidor recalcula siempre subtotal, descuento y total; los importes que envíe el cliente se
  ignoran.
- Semántica fija: `subtotal` agrega precios de lista, `descuento` el ahorro, y siempre
  `total = subtotal − descuento`. El IVA (21 %) va incluido en el precio y solo se desglosa para
  mostrarlo; no se persiste.
- Toda variación de stock se escribe en `movimientos_inventario` dentro de la misma transacción,
  con `id_usuario_responsable`.
- La lectura de inventario previa a una escritura usa `SELECT … FOR UPDATE`. La clave única real de
  `inventario_sucursal` es `(id_variante, id_sucursal, id_temporada)`: filtrar solo por los dos
  primeros con `scalar_one_or_none()` provoca `MultipleResultsFound` en cuanto hay dos temporadas.
- `venta_detalle.subtotal_linea` es `GENERATED ALWAYS`: se mapea en solo lectura con
  `FetchedValue()`; incluirla en un `INSERT` hace que PostgreSQL rechace la sentencia.
- El trigger `trg_descontar_inventario` fue **neutralizado** en la migración `0009`. El movimiento
  de stock lo ejecuta el servicio, como en `ReservaServicio` y `CheckoutServicio`.

**Errores no controlados:** `capturar_errores_no_controlados` se registra *antes* que el
`CORSMiddleware` a propósito. `add_middleware` antepone, así que el primero declarado queda por
dentro y su 500 sí atraviesa CORS. Un `@app.exception_handler(Exception)` no sirve: Starlette lo
monta en el `ServerErrorMiddleware`, por fuera de CORS, y el navegador reporta «Failed to fetch»
en lugar del error real.

### Frontend Web

```
src/app/modules/<paquete_dominio>/<cuNN_slug>/{paginas,componentes,servicios,modelos}/
src/app/core/{guards,interceptors,layouts}/
```

- Componentes **standalone** con `ChangeDetectionStrategy.OnPush` explícito. `NgModule` prohibido.
- Estado con Signals (`signal`, `computed`); inyección con `inject()`, nunca por constructor.
- Control de flujo `@if`/`@for` con `track`. `*ngIf`/`*ngFor` prohibidos.
- Los servicios reemplazan su estado con la respuesta del servidor; no derivan importes en cliente.
- **Decart (CU10) depende de dos entradas de `angular.json` que no deben quitarse:** el asset que copia
  `frame-metadata-worker.js` de `@decartai/sdk` a la raíz de la salida y
  `serve.options.prebundle.exclude: ["@decartai/sdk"]`. Sin ellas el worker da 404, LiveKit no envía
  fotogramas y la sesión queda `connected` sin generar nunca (defecto 46). Tras actualizar el SDK,
  comprueba que el archivo sigue en esa ruta.
- `authInterceptor` adjunta el JWT y gestiona el 401. Las claves de sesión (`fashionstore_token`,
  `fashionstore_user`) pertenecen en exclusiva a `LoginService`: usa `establecerSesion()` en lugar
  de escribir en `localStorage` desde otro sitio.
- **El cajero no comparte el panel corporativo** (decisión del usuario, CU31-CU32): su único espacio es
  `/admin/pos`. El login lo envía allí y `cajeroACajaGuard` lo devuelve desde `/admin` y desde las rutas
  del panel sin guard de rol. Una ruta nueva del panel debe llevar `roleGuard` o `cajeroACajaGuard`.

### Mobile

```
lib/src/modulos/<paquete_dominio>/<cuNN_slug>/{datos,dominio,presentacion}/
lib/src/{core,navegacion}/
```

- `datos/` DTO con `fromJson`/`toJson`, datasources y repositorios; `presentacion/` BLoCs basados en
  `ChangeNotifier` con estados sellados (`sealed class`).
- El JWT se propaga por constructor desde `PantallaPrincipalHub` hasta cada pantalla hoja. Olvidarlo
  produce 401 con el usuario autenticado.
- `SesionManager` es un singleton con stream broadcast: los datasources notifican el 401 y
  `main.dart` redirige al login mediante `navigatorKey` global, por encima del `Navigator`.
- `RenderFlex overflowed` ha reaparecido cinco veces. Usa `Expanded`/`Flexible` con
  `overflow: TextOverflow.ellipsis` en lugar de reducir tamaños de fuente.

---

## Despliegue

- **Backend:** Render (`render.yaml`, `rootDir: Ec-backend`). Espera arranques en frío; la conexión
  usa `pool_pre_ping`.
- **Web:** Vercel. `vercel.json` reescribe `/api/:path*` al backend de Render y todo lo demás a
  `index.html` — de ahí que la ruta comodín de Angular sea imprescindible.
- **Base de datos:** Neon PostgreSQL, esquema `fashionstore`. `Ec-backend/.env` no está versionado.
