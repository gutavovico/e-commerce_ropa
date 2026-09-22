# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

FashionStore es un e-commerce omnicanal de alta costura femenina. Monorepo con tres aplicaciones
que comparten una única base de datos PostgreSQL desplegada en Neon.

| Directorio | Stack | Rol |
| :--- | :--- | :--- |
| `Ec-backend/` | Python 3.12 · FastAPI · SQLAlchemy 2.0 · Alembic | API REST, única fuente de verdad de datos e importes |
| `Ec-frontend/` | Angular 21 · standalone · Signals · Tailwind | Cliente web |
| `Ec-mobile/` | Flutter 3.x · Dart 3 | Cliente móvil (rol Cliente) |

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
flutter run --dart-define=API_URL=http://localhost:8000
```

`api_config.dart` resuelve la URL por plataforma (`10.0.2.2` en Android, `localhost` en el resto).
Un `flutter build apk` sin `--dart-define=API_URL=...` genera un binario que apunta a localhost y
no puede hablar con producción.

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

**Flujo de gate:** el usuario aprueba la especificación antes de que se escriba código, y aprueba
cada bloque (Backend → Web → Mobile) antes de pasar al siguiente. No cruces ese límite sin permiso
explícito.

---

## Reglas que esta base de código ya ha pagado caro

### La base de datos manda, no las migraciones

`alembic/versions/0001_base_ddl.py` **no describe el esquema desplegado**. Difiere en nombres de
columna (`estado_activo` frente a `activa`, `nit_rut` frente a `nit`) y en tipos (`TIMESTAMPTZ`
frente a `DATE`). Confiar en la migración ya tumbó catálogo, búsqueda y colecciones en producción
(defecto 34 del `CHANGELOG.md`).

Antes de mapear una tabla, **consulta el esquema real**:

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

**La cadena de Alembic está rota:** la base declara `alembic_version = '0010'`, pero las revisiones
`0004`–`0008` no existen como archivos. `alembic upgrade head` no puede resolverla, y `render.yaml`
la invoca en `preDeployCommand`. Las migraciones `0009` y `0010` se aplicaron ejecutando su DDL de
forma idempotente. Reconciliar la cadena es una decisión de esquema pendiente.

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

Paquetes actuales: `autenticacion_seguridad`, `catalogo`, `reservas`, `compras_pagos`.

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
- `authInterceptor` adjunta el JWT y gestiona el 401. Las claves de sesión (`fashionstore_token`,
  `fashionstore_user`) pertenecen en exclusiva a `LoginService`: usa `establecerSesion()` en lugar
  de escribir en `localStorage` desde otro sitio.

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
