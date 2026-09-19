# Diseno · 00-Bootstrap · Infraestructura base del backend
Requisitos: specs/00-bootstrap/requirements.md (borrador, pendiente de aprobacion)

## Enfoque
Crear un esqueleto funcional minimo del backend dentro de `backend/`, con `main.py` en la raiz del paquete (sin wrapper `app/`) y `alembic/` para migraciones. Esta estructura difiere de `references/arquitectura.md` seccion 3 en dos puntos: (1) no hay subdirectorio `app/` intermedio, y (2) el directorio de migraciones se llama `alembic/` en lugar de `migrations/`. Ambas decisiones siguen la instruccion explicita del usuario. La skill indica que la convencion del usuario prevalece.

Alternativas descartadas:
- Reutilizar `Ec-backend/`: su estructura plana (`crud/`, `db/`, `models/`, `schemas/`, `services/`) no sigue la organizacion modular por dominio, y los archivos estan vacios.
- Usar SQLAlchemy async: decision ya tomada por el usuario (sincrono con psycopg 3).
- Wrapper `app/`: el usuario especifica `backend/main.py` y `backend/core/` directamente.

## Contrato de API

| Metodo y ruta | Rol permitido | Entrada | Salida | Codigos |
|---|---|---|---|---|
| `GET /api/v1/health` | publico | ninguna | `HealthResponse` | 200 |
| `GET /` | publico | ninguna | JSON informativo | 200 |

### HealthResponse
```json
{
  "status": "online",
  "service": "fashionstore-backend",
  "timestamp": "2026-09-18T18:00:00+00:00"
}
```

### Formato de error (todos los endpoints futuros)
```json
{
  "detail": "Recurso no encontrado",
  "code": "NOT_FOUND"
}
```

## Capas afectadas

### core/config.py -- Settings
- Clase `Settings(BaseSettings)` con `model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")`.
- Campos obligatorios (sin default): `DATABASE_URL: str`, `JWT_SECRET: str`.
- Campos con default: `JWT_EXPIRE_MINUTES: int = 60`, `CORS_ORIGINS: list[str] = ["http://localhost:4200"]`, `STRIPE_SECRET_KEY: str = ""`, `STRIPE_WEBHOOK_SECRET: str = ""`, `IA_API_KEY: str = ""`.
- Si `DATABASE_URL` o `JWT_SECRET` faltan, Pydantic lanza `ValidationError` al instanciar (AC-17).
- Instancia singleton: `settings = Settings()` a nivel de modulo.
- URL de desarrollo: `postgresql+psycopg://fashion_user:fashion_password@localhost:5432/fashionstore_db`.

### core/database.py -- Engine y sesion
```python
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"options": "-c search_path=fashionstore,public"},
)
SessionLocal = sessionmaker(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```
- Driver: `psycopg` (psycopg 3); la URL usa el esquema `postgresql+psycopg://`.
- `pool_pre_ping=True` (AC-5): tolera desconexiones.
- `search_path=fashionstore,public` via `connect_args` (AC-7): todas las consultas resuelven al esquema `fashionstore` sin cualificar tablas; `public` incluido para que las extensiones (pgcrypto, citext, pg_trgm) sean visibles.

### core/security.py -- Hash y JWT (esqueleto)
- `hash_password(plain: str) -> str` usando `argon2-cffi` (`PasswordHasher`).
- `verify_password(plain: str, hashed: str) -> bool` que retorna `False` si la verificacion falla (no lanza excepcion).
- `create_access_token(data: dict, expires_delta: timedelta | None = None) -> str` usando `PyJWT` con `HS256` y `settings.JWT_SECRET`.
- `decode_access_token(token: str) -> dict` que lanza `AuthenticationError` si el token es invalido o expirado.
- Sin logica de login, sin dependencias de auth, sin roles.

### core/deps.py -- Dependencias (placeholder)
- Archivo con un comentario indicando que `get_current_user` y `require_roles` se implementan con CU01-CU04.
- No exporta nada por ahora.

### core/errors.py -- Excepciones de dominio
```python
class DomainError(Exception):
    """Base para todas las excepciones de dominio."""
    def __init__(self, message: str, code: str = "DOMAIN_ERROR"):
        self.message = message
        self.code = code
        super().__init__(message)

class NotFoundError(DomainError):
    def __init__(self, message: str = "Recurso no encontrado"):
        super().__init__(message, code="NOT_FOUND")

class ConflictError(DomainError):
    def __init__(self, message: str = "Conflicto"):
        super().__init__(message, code="CONFLICT")

class AuthenticationError(DomainError):
    def __init__(self, message: str = "No autenticado"):
        super().__init__(message, code="NOT_AUTHENTICATED")

class AuthorizationError(DomainError):
    def __init__(self, message: str = "Sin permiso"):
        super().__init__(message, code="FORBIDDEN")
```

### main.py -- Aplicacion FastAPI
- Instancia `FastAPI(title="FashionStore API", version="0.1.0")`.
- CORS con origenes de `settings.CORS_ORIGINS` (AC-11).
- Exception handlers registrados:
  - `NotFoundError` -> 404
  - `ConflictError` -> 409
  - `AuthenticationError` -> 401
  - `AuthorizationError` -> 403
  - `DomainError` (generico) -> 400
- Respuesta de error: `JSONResponse(status_code=..., content={"detail": e.message, "code": e.code})`.
- Schema `HealthResponse` con Pydantic: `status`, `service`, `timestamp`.
- `GET /api/v1/health` retorna `HealthResponse(status="online")`.
- `GET /` retorna JSON informativo con enlaces a docs y health.

## Estructura de carpetas resultante

```
backend/
├── pyproject.toml
├── alembic.ini
├── .env.example
├── README.md
├── main.py
├── core/
│   ├── __init__.py
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── deps.py
│   └── errors.py
├── modules/
│   └── __init__.py
├── integrations/
│   └── __init__.py
├── alembic/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
│       └── 0001_base_ddl.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_health.py
└── specs/
    └── 00-bootstrap/
        ├── requirements.md
        ├── design.md
        └── tasks.md
```

**Nota sobre importaciones.** Sin `app/`, los imports internos son directos: `from core.config import settings`, `from core.errors import NotFoundError`. Esto funciona cuando el directorio de trabajo es `backend/` (que es el caso al ejecutar `uvicorn main:app`). Para tests, `conftest.py` o `pyproject.toml` garantizan que `backend/` este en `sys.path`.

## Datos y migraciones

### Migracion base (`0001_base_ddl.py`)
- **upgrade()**: ejecuta el DDL completo de `fashionstore.sql` como SQL crudo via `op.execute()`. Contenido: creacion de esquema, 3 extensiones, 10 enums, 22 tablas con indices y constraints, 2 funciones de trigger, 2 triggers, 3 vistas, y datos semilla (3 ciudades, 6 tallas, 4 colores, 5 categorias, 2 temporadas).
- **downgrade()**: elimina todo en orden inverso de dependencias:
  1. Vistas (`vw_reservas_pendientes`, `vw_ventas_por_sucursal`, `vw_inventario_consolidado`)
  2. Trigger `trg_descontar_inventario` + funcion `fn_descontar_inventario_venta`
  3. Trigger `trg_inventario_estado` + funcion `fn_actualizar_estado_inventario`
  4. Tablas en orden inverso de dependencias (desde `solicitudes_reporte_ia` hasta `ciudades`)
  5. Enums (10 tipos)
  6. Esquema `fashionstore`
  - Las extensiones NO se eliminan en downgrade (son compartidas a nivel de BD y podrían afectar a otros esquemas).
- No se modifica el DDL; se reproduce tal cual (AC-12).

### alembic.ini
- `script_location = alembic`
- `sqlalchemy.url` se sobreescribe en `env.py` desde `settings.DATABASE_URL`.

### alembic/env.py
- Importa `Settings` de `core.config` y usa `settings.DATABASE_URL` para la URL.
- Configura `target_metadata = None` (no se usa autogenerate para la migracion base; cuando se creen modelos ORM de dominio, se apuntara al `Base.metadata`).
- Establece `version_table_schema = "fashionstore"` para que la tabla `alembic_version` viva dentro del esquema.
- Configura `include_schemas = True` para operaciones sobre el esquema `fashionstore`.

## Reglas, transacciones y concurrencia
No aplica en este incremento. No hay logica de negocio ni escrituras de dominio.

## Errores
| Excepcion | Codigo HTTP | code | Cuando |
|---|---|---|---|
| `NotFoundError` | 404 | `NOT_FOUND` | recurso no encontrado (futuro) |
| `ConflictError` | 409 | `CONFLICT` | conflicto de estado/unicidad (futuro) |
| `AuthenticationError` | 401 | `NOT_AUTHENTICATED` | token invalido/ausente (futuro) |
| `AuthorizationError` | 403 | `FORBIDDEN` | rol insuficiente (futuro) |
| `DomainError` (base) | 400 | `DOMAIN_ERROR` | error de dominio generico |
| `ValidationError` (Pydantic) | arranque | --- | `DATABASE_URL` o `JWT_SECRET` faltante |

## No funcionales
- **Rendimiento**: `pool_pre_ping` para reconexion; pool por defecto de SQLAlchemy (5 conexiones, 10 overflow).
- **Seguridad**: secretos solo por variables de entorno; `.env` en `.gitignore` antes del primer commit; argon2 para hash (resistente a GPU); JWT con HS256.
- **Compatibilidad**: el endpoint `/api/v1/health` es compatible con el que ya existe en `Ec-backend/main.py`.

## Dependencias (pyproject.toml)

```toml
[project]
name = "fashionstore-backend"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115,<1",
    "uvicorn[standard]>=0.30,<1",
    "sqlalchemy>=2.0,<3",
    "psycopg[binary]>=3.1,<4",
    "alembic>=1.13,<2",
    "pydantic>=2.0,<3",
    "pydantic-settings>=2.0,<3",
    "pyjwt>=2.8,<3",
    "argon2-cffi>=23.1,<24",
    "python-dotenv>=1.0,<2",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "httpx>=0.27,<1",
    "ruff>=0.5,<1",
]
```

## Estrategia de pruebas

| AC | Tipo de prueba | Descripcion |
|---|---|---|
| AC-10 | Integracion (endpoint) | `GET /api/v1/health` retorna 200 con campos `status`, `service`, `timestamp`. |
| AC-9 | Unitaria | Lanzar `NotFoundError` en un endpoint de prueba y verificar que el handler devuelve 404 con formato `{"detail": ..., "code": ...}`. |
| AC-9 | Unitaria | Lanzar `ConflictError` en un endpoint de prueba y verificar 409. |
| AC-14, AC-15 | Integracion | El `TestClient` se inicializa correctamente y puede hacer requests sin BD. |

Comando de verificacion: `cd backend && pytest tests/ -v`

**Nota**: los tests del health check no requieren conexion a BD (el endpoint no la usa). El `conftest.py` crea un `TestClient` directamente sobre la app FastAPI. Los tests de migracion (AC-12, AC-13) se verifican manualmente ejecutando `alembic upgrade head` y `alembic downgrade base` contra la BD de Docker.
