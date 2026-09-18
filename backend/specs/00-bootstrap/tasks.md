# Tareas · 00-Bootstrap · Infraestructura base del backend

Specs aprobadas: requirements.md, design.md (2026-09-18).
Commits: uno por tarea. Push: al final de cada oleada, tras aprobacion.

## Oleada 1 -- Cimientos (sin dependencias entre si)

### T1 · Scaffolding del proyecto
- Contexto: specs/00-bootstrap/design.md seccion "Estructura de carpetas"
- Objetivo: crear la estructura de directorios, `pyproject.toml`, `.env.example`, y actualizar `.gitignore` para incluir `backend/.env`.
- Archivos permitidos: `.gitignore` (raiz), `backend/pyproject.toml`, `backend/.env.example`, `backend/core/__init__.py`, `backend/modules/__init__.py`, `backend/integrations/__init__.py`, `backend/tests/__init__.py`
- Criterios: AC-1, AC-3, AC-4
- Boundaries: no crear archivos de codigo funcional; solo estructura y configuracion
- Verificacion: `ls -R backend/` muestra la estructura esperada; `git diff .gitignore` confirma que `backend/.env` esta ignorado
- Hecho cuando: la estructura existe, `.env.example` tiene las 7 variables sin valores, y `.gitignore` incluye `backend/.env`

### T2 · Excepciones de dominio (`core/errors.py`)
- Contexto: specs/00-bootstrap/design.md seccion "core/errors.py"
- Objetivo: definir la jerarquia `DomainError > NotFoundError, ConflictError, AuthenticationError, AuthorizationError`
- Archivos permitidos: `backend/core/errors.py`
- Criterios: AC-9
- Boundaries: sin imports de FastAPI; sin logica HTTP
- Verificacion: `python -c "from core.errors import DomainError, NotFoundError, ConflictError, AuthenticationError, AuthorizationError; print('OK')"` ejecutado desde `backend/`
- Hecho cuando: las 5 clases se importan sin error y cada una tiene `message` y `code`

### T3 · Configuracion (`core/config.py`)
- Contexto: specs/00-bootstrap/design.md seccion "core/config.py"
- Objetivo: implementar `Settings(BaseSettings)` con campos obligatorios (`DATABASE_URL`, `JWT_SECRET`) y opcionales, e instancia singleton
- Archivos permitidos: `backend/core/config.py`
- Criterios: AC-2, AC-17
- Boundaries: sin imports de SQLAlchemy ni FastAPI
- Verificacion: `python -c "import os; os.environ['DATABASE_URL']='x'; os.environ['JWT_SECRET']='y'; from core.config import settings; print(settings.DATABASE_URL)"` ejecutado desde `backend/`
- Hecho cuando: `Settings` se instancia con variables de entorno y falla con `ValidationError` si faltan las obligatorias

## Oleada 2 -- Servicios core (dependen de Oleada 1)

### T4 · Base de datos (`core/database.py`)
- Contexto: specs/00-bootstrap/design.md seccion "core/database.py"; references/arquitectura.md seccion 5
- Objetivo: crear engine con `pool_pre_ping=True` y `search_path=fashionstore,public`, `SessionLocal`, y generador `get_db()`
- Archivos permitidos: `backend/core/database.py`
- Criterios: AC-5, AC-6, AC-7
- Boundaries: no crear modelos ORM; no importar FastAPI
- Verificacion: `python -c "from core.database import engine, SessionLocal, get_db; print(engine.pool.echo, engine.dialect.name)"` (con `.env` configurado) ejecutado desde `backend/`
- Hecho cuando: engine creado con pool_pre_ping, search_path configurado, `get_db` es un generador que yield/close

### T5 · Seguridad (`core/security.py`)
- Contexto: specs/00-bootstrap/design.md seccion "core/security.py"
- Objetivo: implementar `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- Archivos permitidos: `backend/core/security.py`
- Criterios: AC-8
- Boundaries: sin logica de login; sin dependencias de FastAPI; `decode_access_token` lanza `AuthenticationError` (de `core.errors`)
- Verificacion: `python -c "from core.security import hash_password, verify_password, create_access_token, decode_access_token; h=hash_password('test'); print(verify_password('test', h))"` ejecutado desde `backend/`
- Hecho cuando: las 4 funciones operan correctamente; hash produce un string argon2; JWT se crea y decodifica

### T6 · Dependencias placeholder (`core/deps.py`)
- Contexto: specs/00-bootstrap/design.md seccion "core/deps.py"
- Objetivo: crear archivo con docstring indicando que `get_current_user` y `require_roles` se implementan con CU01-CU04
- Archivos permitidos: `backend/core/deps.py`
- Criterios: AC-1 (completar estructura de core/)
- Boundaries: sin codigo funcional
- Verificacion: el archivo existe y contiene solo el docstring/comentario
- Hecho cuando: `core/deps.py` existe con el comentario

## Oleada 3 -- Aplicacion y Alembic (dependen de Oleada 2)

### T7 · Aplicacion FastAPI (`main.py`)
- Contexto: specs/00-bootstrap/design.md seccion "main.py"
- Objetivo: crear app FastAPI con CORS, exception handlers para la jerarquia de `DomainError`, schema `HealthResponse`, y endpoints `GET /api/v1/health` y `GET /`
- Archivos permitidos: `backend/main.py`
- Criterios: AC-9, AC-10, AC-11
- Boundaries: no importar modulos de dominio; no crear routers separados (health es inline por simplicidad)
- Verificacion: `cd backend && uvicorn main:app --host 127.0.0.1 --port 8000` y luego `curl http://127.0.0.1:8000/api/v1/health` retorna 200 con los 3 campos
- Hecho cuando: health responde 200; error handlers traducen excepciones a JSON con formato `{"detail": ..., "code": ...}`

### T8 · Configuracion de Alembic
- Contexto: specs/00-bootstrap/design.md secciones "alembic.ini" y "alembic/env.py"
- Objetivo: crear `alembic.ini` apuntando a `alembic/`, y `alembic/env.py` que lee `DATABASE_URL` de `Settings` y configura `version_table_schema`
- Archivos permitidos: `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/script.py.mako`
- Criterios: AC-12 (prerequisito)
- Boundaries: no crear migraciones aun
- Verificacion: `cd backend && alembic --help` no falla; `alembic/env.py` importa settings correctamente
- Hecho cuando: Alembic inicializado y configurado, listo para crear migraciones

### T9 · Migracion base (`0001_base_ddl.py`)
- Contexto: specs/00-bootstrap/design.md seccion "Migracion base"; DDL completo de `fashionstore.sql`
- Objetivo: crear migracion manual que ejecute el DDL completo en `upgrade()` y lo revierta en `downgrade()`
- Archivos permitidos: `backend/alembic/versions/0001_base_ddl.py`
- Criterios: AC-12, AC-13
- Boundaries: no modificar el DDL; reproducirlo tal cual; downgrade no elimina extensiones
- Verificacion: `cd backend && alembic upgrade head` aplica sin errores contra la BD de Docker (que ya tiene el esquema -- verificar idempotencia con `IF NOT EXISTS`); `alembic downgrade base` revierte
- Hecho cuando: `upgrade` y `downgrade` ejecutan sin errores; la BD queda en el estado esperado

## Oleada 4 -- Tests y documentacion (dependen de Oleada 3)

### T10 · Tests (`conftest.py` + `test_health.py`)
- Contexto: specs/00-bootstrap/design.md seccion "Estrategia de pruebas"
- Objetivo: crear `conftest.py` con fixture `client` (TestClient de httpx sin BD) y `test_health.py` con tests del health check y de los error handlers
- Archivos permitidos: `backend/tests/conftest.py`, `backend/tests/test_health.py`
- Criterios: AC-14, AC-15, AC-9 (error handlers), AC-10
- Boundaries: sin conexion a BD en tests
- Verificacion: `cd backend && pytest tests/ -v` -- todos los tests pasan
- Hecho cuando: al menos 3 tests pasan (health 200, error handler 404, error handler 409)

### T11 · Documentacion (`README.md`)
- Contexto: specs/00-bootstrap/design.md seccion "Estructura de carpetas"; AC-16
- Objetivo: crear `backend/README.md` con instrucciones para clonar, entorno virtual, instalar dependencias, configurar `.env`, Docker, migraciones y Uvicorn
- Archivos permitidos: `backend/README.md`
- Criterios: AC-16
- Boundaries: sin documentacion de endpoints de dominio (no existen aun)
- Verificacion: el archivo existe y cubre los 6 pasos
- Hecho cuando: un desarrollador nuevo puede seguir el README para levantar el proyecto desde cero
