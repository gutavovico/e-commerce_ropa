# FashionStore

**E-commerce omnicanal de alta costura femenina** · SI2 — Parcial 1

Plataforma con tres aplicaciones (API, web y móvil) que comparten una única base de datos
PostgreSQL desplegada en Neon. El backend es la única fuente de verdad de datos e importes.

## Integrantes

| Nombre |
| :--- |
| Gustavo Antonio Sandoval Sanchez |
| Tony Vargas Jimenez |

## Estructura del repositorio

| Directorio | Stack | Rol |
| :--- | :--- | :--- |
| [`Ec-backend/`](Ec-backend) | Python ≥ 3.11 · FastAPI · SQLAlchemy 2.0 · Alembic | API REST |
| [`Ec-frontend/`](Ec-frontend) | Angular 21 · Standalone · Signals · Tailwind | Cliente web |
| [`Ec-mobile/`](Ec-mobile) | Flutter 3.x · Dart 3 | Cliente móvil |
| [`.specs/`](.specs) | Markdown | Especificaciones SDD por caso de uso |
| [`.agents/skills/`](.agents/skills) | Markdown | «Constitución» de cada stack para el agente de IA |

---

## Requisitos previos

| Herramienta | Versión | Para qué |
| :--- | :--- | :--- |
| Python | 3.11 o superior | Backend |
| Node.js + npm | Node 22 · npm 11 | Frontend web |
| Flutter | 3.x (SDK Dart `^3.11`) | App móvil |
| Git | cualquiera | Clonar el repositorio |
| Cadena de conexión a Neon | — | Base de datos compartida del equipo |

> El proyecto **no usa Docker ni una base de datos local**: todos los stacks hablan con la base
> PostgreSQL de Neon (esquema `fashionstore`). Pídele la cadena `DATABASE_URL` al equipo.

---

## Cómo activar el entorno

### Backend (entorno virtual de Python)

Desde `Ec-backend/`:

```powershell
# Windows (PowerShell)
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt          # o: pip install -e ".[dev]" para incluir pytest y ruff
```

```bash
# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Si PowerShell bloquea el script de activación:
`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

Sin activar el entorno también se puede invocar por ruta directa, como hace el equipo:
`./.venv/Scripts/python.exe -m pytest -q`.

### Frontend web

Desde `Ec-frontend/`:

```bash
npm install
```

### Móvil

Desde `Ec-mobile/`:

```bash
flutter pub get
```

---

## Variables de entorno (backend)

Copia la plantilla y complétala:

```bash
cd Ec-backend
cp .env.example .env          # en PowerShell: Copy-Item .env.example .env
```

| Variable | Obligatoria | Descripción |
| :--- | :---: | :--- |
| `DATABASE_URL` | Sí | Cadena de Neon: `postgresql+psycopg://usuario:clave@host-pooler/bd?sslmode=require` |
| `JWT_SECRET` | Sí | Mínimo 32 caracteres. Genérala con `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `JWT_EXPIRE_MINUTES` | No | Vigencia del token (por defecto 1440) |
| `CORS_ORIGINS` | No | Orígenes web permitidos (por defecto `http://localhost:4200`) |
| `STRIPE_SECRET_KEY` | No | Clave `sk_test_...`. Sin una clave real, el backend usa el **simulador** de pagos |
| `STRIPE_WEBHOOK_SECRET` | No | Declarada, pero el backend aún no expone el webhook |
| `IA_API_KEY` | No | Clave de Google Gemini. Sin ella, las recomendaciones usan el **fallback determinista** |
| `SMTP_USER`, `SMTP_PASSWORD` | No | Correo para los códigos OTP de recuperación de acceso (CU33) |

`.env` está en `.gitignore`: **nunca lo subas al repositorio**.

---

## Cómo desplegar y ejecutar en local

Abre dos terminales (tres si vas a probar el móvil). **El backend debe estar arriba antes que el
frontend**, porque el proxy de Angular reenvía `/api` a `127.0.0.1:8000`.

### 1. Backend — `http://127.0.0.1:8000`

```bash
cd Ec-backend
./.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

| Recurso | URL |
| :--- | :--- |
| Swagger UI | http://127.0.0.1:8000/docs |
| Health check | http://127.0.0.1:8000/api/v1/health |

### 2. Frontend web — `http://localhost:4200`

```bash
cd Ec-frontend
npm start
```

`npm start` ejecuta `ng serve --proxy-config proxy.conf.json`: las peticiones a `/api` y `/static`
se reenvían al backend local. La clave pública de Stripe (`pk_test_...`) está en
`src/environments/environment.ts`; si queda vacía, el checkout muestra el panel de modo simulador.

### 3. Móvil (opcional)

```bash
cd Ec-mobile
flutter run --dart-define=API_URL=http://localhost:8000
# opcional, para Stripe real:
#   --dart-define=STRIPE_PUBLISHABLE_KEY=pk_test_...
```

`api_config.dart` usa `10.0.2.2` en el emulador de Android y `localhost` en el resto. Un
`flutter build apk` **sin** `--dart-define=API_URL=...` genera un binario que apunta a localhost.

### Pruebas

```bash
# Backend (desde Ec-backend/)
./.venv/Scripts/python.exe -m pytest -q

# Frontend (desde Ec-frontend/) — usa siempre `ng test`, no `npx vitest`
npx ng test --watch=false
npx tsc -p tsconfig.app.json --noEmit

# Móvil (desde Ec-mobile/)
dart analyze
flutter test
```

> Toda la suite del backend mockea la sesión de base de datos: que esté en verde no prueba que el
> contrato funcione contra Neon. Para cambios que tocan la base de datos, verifica además de forma
> manual contra Swagger.

### Despliegue en producción

| Pieza | Plataforma | Configuración |
| :--- | :--- | :--- |
| Backend | Render | [`Ec-backend/render.yaml`](Ec-backend/render.yaml) (`rootDir: Ec-backend`) |
| Web | Vercel | [`Ec-frontend/vercel.json`](Ec-frontend/vercel.json): `/api/*` se reescribe al backend de Render |
| Base de datos | Neon PostgreSQL | Esquema `fashionstore` |

---

## Inteligencia artificial utilizada

Hay dos usos distintos: la IA **que ayudó a construir** el proyecto y la IA **que forma parte del
producto**.

### Durante el desarrollo

| Herramienta | Uso |
| :--- | :--- |
| **Claude Code** (Anthropic) | Asistente de programación que implementó los casos de uso siguiendo las specs. Lee [`CLAUDE.md`](CLAUDE.md) y las skills de [`.agents/skills/`](.agents/skills). Aparece como coautor en commits del historial. |

### Dentro del producto

| Funcionalidad | Tecnología | Comportamiento |
| :--- | :--- | :--- |
| **CU18 · Recomendaciones personalizadas** | Google **Gemini Flash**, por HTTP REST ([`gemini_service.py`](Ec-backend/app/integrations/gemini_service.py)) | Genera el motivo de cada recomendación. Si no hay `IA_API_KEY` o la llamada falla, conmuta a un **fallback determinista**, así que la función nunca depende de la IA. |
| **CU31 · Reportes por voz** | **Web Speech API** del navegador + parser determinista en el backend | La voz se transcribe en el cliente; el backend extrae intención, módulo, periodo, sucursal y formato con reglas, **sin LLM**. |
| **CU16 · Pagos** | Stripe (no es IA) | Simulador automático cuando no hay claves reales. |

---

## Cómo funcionan las specs personalizadas (Spec-Driven Development)

El desarrollo se organiza por **caso de uso** (CU01, CU05, CU11…), no por capa técnica. La idea: el
código es la consecuencia de una especificación aprobada, no de un prompt improvisado. Una persona
decide el qué y el porqué; el agente de IA ejecuta; la revisión humana se concentra en las **puertas
de aprobación**.

### Las «skills» de cada stack — `.agents/skills/`

Hay una por stack: `fashionstore-backend-sdd`, `fashionstore-frontend-sdd` y
`fashionstore-mobile-sdd`. Cada una contiene un `SKILL.md` y una carpeta `references/` con:

- **Arquitectura y convenciones** del stack (capas, estructura de carpetas, nomenclatura).
- **Listas de *Never* y *Ask First***: lo que el agente jamás debe hacer y lo que debe consultar
  antes de tocar.
- **Plantillas SDD** (requisitos en notación EARS, diseño, tareas) y **tokens de diseño**.

El agente las carga automáticamente cuando la tarea toca ese stack. Si el repositorio ya tiene una
convención, gana el repositorio sobre la skill.

### El flujo de cuatro fases con puertas

| Fase | Artefacto | Puerta |
| :--- | :--- | :--- |
| 1. Requisitos | `spec.md` (comportamiento en EARS, errores, fuera de alcance) | El usuario aprueba |
| 2. Diseño | `plan.md` (endpoints, capas, datos, transacciones) | El usuario aprueba |
| 3. Tareas | `tasks.md` (tareas atómicas con su verificación) | El usuario aprueba |
| 4. Implementación | código + pruebas + `checkpoint.md` | Revisión contra la spec |

El orden de implementación también tiene puertas: **Backend → Web → Mobile**, y no se pasa al
siguiente bloque sin aprobación del anterior. El esfuerzo se calibra al riesgo: un CRUD trivial
lleva 3–5 líneas de requisitos; inventario, pagos y autenticación llevan el ciclo completo.

### Dónde viven las specs — `.specs/`

| Carpeta | Contenido |
| :--- | :--- |
| `.specs/changes/<id>/` | Cambios **en curso** (hoy: CU13–CU14 y CU16) |
| `.specs/finalized/<CU>/` | Casos de uso **terminados** |
| `.specs/modules/<paquete>/` | Especificación permanente tras la promoción |
| `.specs/architecture/` | Directrices transversales, p. ej. la navegación Hub-and-Spoke |
| [`CHANGELOG.md`](CHANGELOG.md) | Bitácora numerada de defectos corregidos, con causa y solución |

El `checkpoint.md` de cada cambio es la lista de criterios de paso (CP-01, CP-02…) marcados por
bloque; un CU se considera cerrado cuando todos están aprobados.

---

## Reglas de dominio que no se negocian

- **Cero datos inventados:** toda prenda, precio, boutique y existencia procede de PostgreSQL. Si no
  hay datos, la pantalla muestra su estado vacío.
- **Catálogo exclusivamente femenino.** La marca se escribe siempre «FASHION STORE».
- **Dinero:** todo importe es `Decimal`; el servidor recalcula siempre subtotal, descuento y total.
- **Navegación Hub-and-Spoke:** exactamente cuatro pantallas raíz (Inicio, Buscar, Catálogo, Perfil).

La guía completa para trabajar con el agente está en [`CLAUDE.md`](CLAUDE.md).

---

## Estado de los casos de uso

Terminados en los tres stacks (o en los que aplican): CU01–CU09, CU11–CU18, CU20–CU30, CU33 y
CU36, además del módulo de reportes y exportación por voz (`cu31_reportes_voz`, equivale a CU34 + CU35).

Pendientes o incompletos:

| CU | Estado |
| :--- | :--- |
| CU10 Vestidor virtual | Solo un modal informativo; sin backend ni integración AR |
| CU19 Asistente inteligente | Sin implementar |
| CU31 / CU32 Venta presencial (POS) | Sin implementar; solo existen los endpoints de confirmación de pago en efectivo |

> **Aviso de numeración:** en el documento maestro `SI2-Parcial1.md`, CU31 es «Registrar venta
> presencial». El código usa el nombre `cu31_reportes_voz` para el módulo de reportes (CU34/CU35).
