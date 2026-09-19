# 00-Bootstrap · Infraestructura base del backend            Nivel: 2     Estado: borrador
Aprobado por: ---   Fecha: ---

## Proposito
Establecer la estructura de carpetas, la configuracion central (`core/`), el punto de entrada de la aplicacion (`main.py`), la migracion base de Alembic que reproduce el DDL de `fashionstore.sql` y la infraestructura de tests, de modo que cualquier modulo de dominio futuro pueda construirse sobre una base funcional y verificada.

## Actores y precondiciones
- Actor: desarrollador (sistema).
- Precondiciones: repositorio clonado en rama `Tony`, Python 3.12 disponible, instancia PostgreSQL local ejecutandose via Docker (`docker-compose up -d`) con el esquema `fashionstore` y las extensiones `pgcrypto`, `citext`, `pg_trgm` ya creadas por el DDL de inicializacion.

## Requisitos (EARS)

### Estructura y configuracion
- **AC-1** El sistema debera organizar el codigo del backend dentro de `backend/`, con la siguiente estructura: `core/` (config, database, security, deps, errors), `modules/` (vacio), `integrations/` (vacio), `alembic/`, `tests/`, `specs/`.
- **AC-2** Cuando la aplicacion se inicie, el sistema debera cargar toda la configuracion exclusivamente desde variables de entorno, utilizando `pydantic-settings` (`Settings`), sin valores secretos por defecto.
- **AC-3** El sistema debera exponer un archivo `backend/.env.example` con todos los nombres de variables esperados (`DATABASE_URL`, `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `IA_API_KEY`, `CORS_ORIGINS`) sin valores reales.
- **AC-4** El sistema debera incluir `backend/.env` en `.gitignore` **antes** del primer commit que contenga codigo.

### Base de datos
- **AC-5** Cuando se cree el engine de SQLAlchemy, el sistema debera configurar `pool_pre_ping=True` para tolerar desconexiones por inactividad.
- **AC-6** El sistema debera exponer una dependencia `get_db` que provea una sesion de SQLAlchemy por request y la cierre al finalizar.
- **AC-7** El sistema debera configurar el `search_path` de la conexion al esquema `fashionstore` via `connect_args`.

### Seguridad (esqueleto)
- **AC-8** El sistema debera proveer funciones de hash y verificacion de contrasenas con argon2, y funciones de creacion y decodificacion de JWT con PyJWT, en `core/security.py`. Sin logica de login ni de roles (corresponde a CU01-CU04).

### Excepciones de dominio
- **AC-9** El sistema debera definir una jerarquia de excepciones de dominio en `core/errors.py` (`DomainError`, `NotFoundError`, `ConflictError`, `AuthenticationError`, `AuthorizationError`) con traduccion automatica a codigos HTTP (404, 409, 401, 403) en `main.py`. Formato de error: `{"detail": "<mensaje>", "code": "<CODIGO_DOMINIO>"}`.

### Aplicacion y health check
- **AC-10** Cuando se haga `GET /api/v1/health`, el sistema debera responder 200 con `{"status": "online", "service": "fashionstore-backend", "timestamp": "<ISO-8601 UTC>"}`.
- **AC-11** El sistema debera configurar CORS usando los origenes definidos en la variable de entorno `CORS_ORIGINS`.

### Migracion base
- **AC-12** El sistema debera incluir una migracion de Alembic (revision inicial) que reproduzca fielmente el DDL de `fashionstore.sql`: esquema, extensiones, 10 enums, 22 tablas, indices, 2 funciones trigger, 2 triggers, 3 vistas y los datos semilla (ciudades, tallas, colores, categorias, temporadas). Sin modificarlo.
- **AC-13** La migracion debera ser reversible: `downgrade` elimina vistas, triggers, funciones, tablas, enums, extensiones y esquema en orden inverso de dependencias.

### Tests
- **AC-14** El sistema debera incluir un `conftest.py` con un fixture de `TestClient` (httpx) que use la aplicacion FastAPI sin necesidad de conexion a base de datos.
- **AC-15** El sistema debera incluir al menos un test que verifique que `GET /api/v1/health` responde 200 con los campos `status`, `service` y `timestamp`.

### Documentacion
- **AC-16** El sistema debera incluir un `backend/README.md` con instrucciones para: clonar, crear el entorno virtual, instalar dependencias con pip, configurar `.env`, levantar PostgreSQL con Docker, ejecutar migraciones con Alembic y arrancar el servidor de desarrollo con Uvicorn.

## Casos de error y borde
- **AC-17** Si `DATABASE_URL` o `JWT_SECRET` no estan definidas en las variables de entorno, entonces el sistema debera fallar al iniciar con un error claro de validacion de Pydantic.
- **AC-18** Si la conexion a la base de datos falla tras el inicio, entonces `pool_pre_ping` debera permitir la reconexion automatica en la siguiente peticion.

## Fuera de alcance
- Modulos de dominio (autenticacion, catalogo, inventario, reservas, compras/pagos, funciones avanzadas).
- Dependencias de auth (`get_current_user`, `require_roles`): se implementan con CU01-CU04.
- Logica de negocio, schemas de dominio, modelos ORM de dominio.
- Despliegue a Render/Neon.
- Migraciones que alteren el DDL original.
- Codigo de Angular o Flutter.

## Preguntas abiertas
Ninguna. Todas resueltas:
- DDL: proporcionado en linea, base de datos corriendo via Docker.
- Estructura: se trabaja en `backend/` sin tocar `Ec-backend/`.
- Stack: confirmado por el usuario (Python 3.12, SQLAlchemy 2.x sincrono + psycopg 3, Alembic, Pydantic v2, PyJWT, argon2, pytest + httpx, ruff).
