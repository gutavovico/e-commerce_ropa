# FashionStore · Backend

API REST del e-commerce omnicanal de alta costura femenina **FashionStore**. Es la única fuente de
verdad de datos e importes: la web ([`Ec-frontend`](../Ec-frontend)) y el móvil
([`Ec-mobile`](../Ec-mobile)) solo consumen su contrato.

**Stack:** Python ≥ 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic · PostgreSQL (Neon) · JWT + Argon2.

## Requisitos previos

- Python 3.11 o superior
- Git
- La cadena `DATABASE_URL` de la base PostgreSQL de **Neon** (esquema `fashionstore`)

> No hay Docker ni base local. Todos los entornos —desarrollo, pruebas manuales y producción—
> hablan con la misma base de Neon. Pídele la cadena de conexión al equipo.

## Inicio rápido

Todos los comandos se ejecutan desde `Ec-backend/`.

### 1. Crear y activar el entorno virtual

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

Si PowerShell bloquea la activación: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.
También puede invocarse el intérprete por ruta directa, sin activar nada:
`./.venv/Scripts/python.exe -m pytest -q`.

### 2. Instalar dependencias

```bash
pip install -e ".[dev]"        # app + pytest, httpx y ruff
# o solo lo necesario para ejecutar:
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env           # PowerShell: Copy-Item .env.example .env
```

| Variable | Obligatoria | Descripción |
| :--- | :---: | :--- |
| `DATABASE_URL` | Sí | `postgresql+psycopg://usuario:clave@host-pooler/bd?sslmode=require` (Neon exige SSL) |
| `JWT_SECRET` | Sí | Mínimo 32 caracteres. `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_EXPIRE_MINUTES` | No | Vigencia del token (por defecto 1440) |
| `CORS_ORIGINS` | No | Orígenes permitidos, separados por coma o en JSON (por defecto `http://localhost:4200`) |
| `CORS_ORIGIN_REGEX` | No | Patrón adicional de orígenes (en producción, los despliegues `*.vercel.app`) |
| `STRIPE_SECRET_KEY` | No | `sk_test_...`. Sin una clave real el backend usa el **simulador** de pagos |
| `STRIPE_WEBHOOK_SECRET` | No | Se lee, pero el backend **aún no expone** el endpoint del webhook |
| `IA_API_KEY` | No | Clave de Google Gemini (CU18). Sin ella se usa el **fallback determinista** |
| `SMTP_*` | No | Envío de códigos OTP para recuperar acceso (CU33) |
| `OTP_EXPIRE_MINUTES`, `OTP_MAX_ATTEMPTS`, `OTP_RESEND_COOLDOWN_SECONDS` | No | Políticas del OTP (15 · 5 · 60) |

`.env` está en `.gitignore`: **nunca lo subas**. `.env.production.example` lista las variables que
debe tener Render.

### 4. Arrancar el servidor

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

El punto de entrada es `app/main.py`. Una vez arriba:

| Recurso | URL |
| :--- | :--- |
| API base | `http://127.0.0.1:8000/api/v1` |
| Swagger UI | http://127.0.0.1:8000/docs |
| ReDoc | http://127.0.0.1:8000/redoc |
| Health check | http://127.0.0.1:8000/api/v1/health |
| Archivos subidos | `http://127.0.0.1:8000/static/...` |

El frontend de desarrollo (`npm start` en `Ec-frontend/`) reenvía `/api` y `/static` a este puerto.

### 5. Ejecutar las pruebas

```bash
python -m pytest -q                                   # suite completa (487 tests)
python -m pytest tests/modules/compras_pagos -q       # un paquete
python -m pytest tests/modules/reservas/test_cu13_consultar_cancelar.py -v   # un archivo
```

`pyproject.toml` fija `pythonpath = ["app", "."]`, por eso los imports son `from core...` y
`from modules...` **sin** el prefijo `app.`.

> **Los tests verdes no prueban que el contrato funcione.** La suite mockea la sesión de base de
> datos. Para cambios que tocan la base, verifica además contra Neon (Swagger o `curl`).
> La excepción es `tests/test_esquema_bd.py`, que compara `Base.metadata` contra
> `information_schema` y se salta sola si no hay `DATABASE_URL`.

`ruff` está declarado en el extra `dev` (`ruff check .`).

## Arquitectura

Monolito modular por capas: **Router → Servicio → Repositorio → ORM**.

```text
Ec-backend/
├── app/
│   ├── main.py                 # Aplicación FastAPI, middlewares, routers y /static
│   ├── core/                   # config, database, deps, errors, security, token_blacklist, email_service
│   ├── integrations/           # stripe_service.py y gemini_service.py (simulador / fallback sin clave)
│   └── modules/
│       └── <paquete_dominio>/
│           ├── modelos.py              # ORM a nivel de paquete
│           ├── router.py               # agrega los routers del paquete
│           └── <cuNN_slug>/{router,servicio,repositorio,esquemas}.py
├── alembic/                    # env.py y versions/ (0001 … 0011)
├── tests/                      # tests/modules/<paquete>/test_cuNN_*.py + test_esquema_bd.py
├── specs/                      # bootstrap SDD y diseño físico de la base (diseno_fisico_neon.*)
├── static/uploads/             # imágenes subidas
├── render.yaml                 # Blueprint de despliegue en Render
├── requirements.txt            # dependencias de ejecución
└── pyproject.toml              # metadatos, extra `dev`, pytest y ruff
```

- **Router:** solo HTTP. Sin lógica de negocio ni consultas ORM.
- **Servicio:** negocio y transacción (una unidad de trabajo por caso de uso). No importa `fastapi`;
  lanza excepciones de dominio de `core/errors.py`, que `main.py` traduce a HTTP:
  `NotFoundError`→404 · `ConflictError`→409 · `AuthorizationError`→403 · `DomainError`→400.
- **Entre paquetes** se accede por el **servicio** del otro paquete, nunca por sus modelos.
- **Errores no controlados:** `capturar_errores_no_controlados` se registra *antes* del
  `CORSMiddleware` a propósito, para que un 500 atraviese CORS y el navegador vea el error real en
  lugar de «Failed to fetch».

### Paquetes de dominio

| Paquete | Casos de uso |
| :--- | :--- |
| `autenticacion_seguridad` | CU01 registro · CU02 login · CU03 logout · CU04 perfil · CU20 usuarios y roles · CU33 recuperar acceso |
| `catalogo` | CU05 catálogo · CU06 búsqueda y filtros · CU07 detalle (incluye CU08) · CU09 disponibilidad · CU18 recomendaciones · CU24 temporadas y colecciones · CU36 colecciones |
| `reservas` | CU12 reservar prendas · CU13 consultar y cancelar (incluye CU14) |
| `compras_pagos` | CU11 carrito · CU15 checkout · CU16 pago electrónico · CU17 historial de compras |
| `comercial` | CU27 promociones · CU28 ventas y reservas · CU29 indicadores · `cu31_reportes_voz` (reportes y exportación por voz: equivale a CU34 + CU35) |
| `gestion_operativa` | CU21 sucursales y ciudades · CU22 prendas y variantes · CU23 categorías, tallas y colores · CU24 inventario y stock · CU25 proveedores · CU26 inventario global |
| `seguridad` | CU30 bitácora de auditoría |

Todos los routers cuelgan de `/api/v1`. Sin implementar aún: CU10 (vestidor), CU19 (asistente) y
CU31/CU32 del documento maestro (venta presencial / POS).

## Reglas de dominio que el backend garantiza

- **Dinero:** todo importe es `Decimal`/`NUMERIC`, nunca `float`. El servidor **recalcula siempre**
  subtotal, descuento y total e ignora los importes del cliente. `total = subtotal − descuento`; el
  IVA (21 %) va incluido y solo se desglosa para mostrarlo.
- **Inventario:** toda variación de stock se escribe en `movimientos_inventario` dentro de la misma
  transacción, con `id_usuario_responsable`. La lectura previa a una escritura usa
  `SELECT … FOR UPDATE`, filtrando por la clave única real `(id_variante, id_sucursal, id_temporada)`.
- **Cero datos inventados:** todo lo que se sirve procede de PostgreSQL. Catálogo exclusivamente
  femenino.
- **`venta_detalle.subtotal_linea` es `GENERATED ALWAYS`:** se mapea en solo lectura; incluirla en
  un `INSERT` hace que PostgreSQL rechace la sentencia.
- **El trigger `trg_descontar_inventario` está neutralizado** (migración `0009`): el movimiento de
  stock lo ejecuta el servicio (`ReservaServicio`, `CheckoutServicio`).

## Base de datos y migraciones

**La base de datos manda, no la migración inicial.** `alembic/versions/0001_base_ddl.py` **por sí
sola no describe el esquema desplegado** (recoge el DDL inicial antes de los renombrados
`estado_activo`/`activa`, `nit_rut`/`nit`, cambios de tipo y tablas añadidas en `0002`–`0011`).
Antes de mapear una tabla, consulta el esquema real en `information_schema`; si el nombre real
difiere del término de dominio, pásalo como primer argumento: `mapped_column("estado_activo", Boolean)`.
El diseño físico completo está en [`specs/diseno_fisico_neon.sql`](specs/diseno_fisico_neon.sql) y
[`specs/diseno_fisico_neon.txt`](specs/diseno_fisico_neon.txt).

### Cadena de Alembic

La cadena es lineal y su única cabeza es `0011`:

```text
0001 → 0002 → … → 0008 → 0009 → 0009a → 0010 → 0010a → 0011
```

`0009a` (CU28) y `0010a` (CU29) son marcadores vacíos; llevan sufijo porque `0009` y `0010` ya
pertenecían a migraciones con DDL real (defecto 45 del [`CHANGELOG.md`](../CHANGELOG.md)).

```bash
python -m alembic heads        # debe imprimir una sola cabeza: 0011
python -m alembic history      # cadena completa
python -m alembic current      # revisión de la base (Neon): 0011 (head)
```

- Neon ya está en `0011`, así que `alembic upgrade head` (que Render ejecuta en cada despliegue) es
  un **no-op**.
- **Nueva migración:** usa un ID único (`0012`) con `down_revision = "0011"` y ejecuta
  `alembic heads` antes de enviarla; dos archivos con el mismo ID rompen toda la cadena.
- **La cadena completa `0001 → 0011` reproduce el esquema de Neon** (las 31 tablas, 236 columnas,
  10 enums, 46 índices, 3 vistas y el trigger). Aun así, si usas `alembic revision --autogenerate`,
  revisa siempre el archivo generado: cuatro tablas de Neon aún no tienen modelo ORM
  (`sesiones_vestidor_virtual`, `interacciones_chatbot`, `historial_navegacion` y
  `solicitudes_reporte_ia`).

## Despliegue (Render)

[`render.yaml`](render.yaml) define el servicio web (`rootDir: Ec-backend`, plan gratuito):

```text
build:      pip install --upgrade pip && pip install -r requirements.txt
preDeploy:  alembic upgrade head
start:      uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Las variables marcadas `sync: false` (`DATABASE_URL`, `SMTP_USER`, `SMTP_PASSWORD`,
`STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `IA_API_KEY`) se configuran a mano en el panel de
Render. Espera **arranques en frío** en el plan gratuito; la conexión usa `pool_pre_ping`.

> Cualquier dependencia nueva debe añadirse a `requirements.txt`, no solo a `pyproject.toml`:
> Render instala desde `requirements.txt` (un olvido ya tumbó un despliegue por `openpyxl` y
> `reportlab`).

## Problemas frecuentes

| Síntoma | Causa y solución |
| :--- | :--- |
| `ModuleNotFoundError: core` / `modules` | Ejecuta desde `Ec-backend/`, no desde `app/` ni desde la raíz |
| `ValidationError` al arrancar | Falta `DATABASE_URL` o `JWT_SECRET` en `.env` |
| Primera petición muy lenta en producción | Arranque en frío de Render |
| `Failed to fetch` en el navegador | Normalmente CORS: añade el origen a `CORS_ORIGINS` |
| `Revision … is present more than once` | Hay dos migraciones con el mismo ID; corrígelo antes de continuar |
| `test_esquema_bd.py` se salta | No hay `DATABASE_URL` en `.env` (es esperado sin acceso a Neon) |
