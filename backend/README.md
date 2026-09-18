# FashionStore - Backend API

API REST del e-commerce omnicanal FashionStore construida con Python, FastAPI y PostgreSQL.

## Requisitos previos

- Python 3.12 o superior
- Docker y Docker Compose (para base de datos PostgreSQL local)
- Git

## Guia de inicio rapido

### 1. Clonar el repositorio y ubicarse en backend

```bash
git clone https://github.com/gutavovico/e-commerce_ropa.git
cd e-commerce_ropa/backend
```

### 2. Crear y activar el entorno virtual

En Windows (PowerShell):
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

En Linux / macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar dependencias

Instalar el paquete en modo editable junto con las dependencias de desarrollo:
```bash
pip install -e ".[dev]"
```

O instalando individualmente:
```bash
pip install fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" alembic pydantic pydantic-settings pyjwt argon2-cffi python-dotenv pytest httpx ruff
```

### 4. Configurar variables de entorno

Copiar el archivo de plantilla `.env.example` a `.env`:
```bash
cp .env.example .env
```

Editar `backend/.env` con los valores correspondientes a su entorno local:
```env
DATABASE_URL=postgresql://fashionstore_user:fashionstore_pass@localhost:5432/fashionstore_db
JWT_SECRET=tu-clave-secreta-de-al-menos-32-caracteres-aleatorios
JWT_EXPIRE_MINUTES=60
STRIPE_SECRET_KEY=sk_test_placeholder
STRIPE_WEBHOOK_SECRET=whsec_placeholder
IA_API_KEY=ia_test_placeholder
CORS_ORIGINS=http://localhost:4200,http://localhost:3000,http://localhost:8000
```

> **Importante**: El archivo `.env` nunca debe commitearse al repositorio. Esta protegido en `.gitignore`.

### 5. Levantar base de datos PostgreSQL con Docker

Si dispone del contenedor Docker de PostgreSQL para desarrollo local:
```bash
docker-compose up -d
```

Asegurese de que PostgreSQL este corriendo en el puerto 5432 con la base de datos `fashionstore_db`.

### 6. Ejecutar migraciones con Alembic

Aplicar la migracion base que contiene el esquema `fashionstore`, enums, tablas, indices, triggers y vistas:
```bash
alembic upgrade head
```

Para revertir la migracion si es necesario:
```bash
alembic downgrade base
```

### 7. Arrancar el servidor de desarrollo

Iniciar FastAPI con Uvicorn en modo hot-reload:
```bash
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

El servidor quedara disponible en:
- API Base: `http://127.0.0.1:8000`
- Documentacion interactiva Swagger UI: `http://127.0.0.1:8000/docs`
- Documentacion ReDoc: `http://127.0.0.1:8000/redoc`
- Health Check: `http://127.0.0.1:8000/api/v1/health`

### 8. Ejecutar pruebas unitarias e integracion

Ejecutar la suite de tests con pytest:
```bash
pytest tests/ -v
```

## Estructura del proyecto

```text
backend/
├── alembic/              # Configuracion y scripts de migracion
│   ├── versions/         # Revisiones de migracion (0001_base_ddl.py)
│   └── env.py            # Contexto de migracion conectado a core.config
├── core/                 # Componentes transversales
│   ├── config.py         # Configuracion centralizada con Pydantic Settings
│   ├── database.py       # Engine SQLAlchemy, SessionLocal y dependencia get_db
│   ├── deps.py           # Inyeccion de dependencias de seguridad y contexto
│   ├── errors.py         # Jerarquia de excepciones de dominio
│   └── security.py       # Hash argon2 y manejo de tokens JWT
├── integrations/         # Clientes para servicios externos (Stripe, IA)
├── modules/              # Modulos de dominio por caso de uso
├── specs/                # Especificaciones SDD (requirements, design, tasks)
├── tests/                # Tests automatizados con pytest y TestClient
├── .env.example          # Plantilla de variables de entorno
├── alembic.ini           # Configuracion principal de Alembic
├── main.py               # Punto de entrada de la aplicacion FastAPI
├── pyproject.toml        # Metadatos del proyecto y dependencias
└── README.md             # Esta documentacion
```
