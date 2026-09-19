# Changelog Técnico de Arquitectura y SDD — FashionStore

Ver documento principal en [../../CHANGELOG.md](../../CHANGELOG.md).

## [1.2.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU04 - Gestionar Perfil del Cliente (Consulta, Actualización y Panel Mi Cuenta):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU04-gestionar-perfil.md`](modules/autenticacion_seguridad/CU04-gestionar-perfil.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU04-gestionar-perfil/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 45/45 tests en verde en `pytest` para toda la suite acumulada; verificación en vivo de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` sobre Neon PostgreSQL Serverless.
  - Frontend Web: Compilación limpia en Angular CLI (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 tests pasando en `ng test`, refresco instantáneo de estado bajo `OnPush` con `ChangeDetectorRef` y sincronización con `sessionStorage`/`localStorage`.
  - Mobile: 28/28 tests en verde en `flutter test`, 0 incidencias en `flutter analyze`, inyección de token real desde login y actualización interactiva en tiempo real.
  - Verificación en Vivo: Probado y validado en vivo por el usuario en web y móvil.

### Registro de Errores Corregidos y Soluciones Aplicadas
11. **Expiración Temprana de Token JWT (`401 Unauthorized: Signature has expired`)**:
    - *Causa:* El tiempo de expiración por defecto de tokens de acceso (`ACCESS_TOKEN_EXPIRE_MINUTES`) era corto (15-60 min), causando desconexiones silenciosas durante pruebas extendidas y edición de perfil.
    - *Solución:* Se amplió `ACCESS_TOKEN_EXPIRE_MINUTES = 1440` (24 horas) en `app/core/config.py` y `.env` para asegurar persistencia durante desarrollo y depuración.
12. **Exclusión de Selector de Género por Modelo de Marca de Alta Costura Femenina**:
    - *Causa:* Se incluía selector de género en los formularios de edición de perfil, lo cual no aplica para una firma exclusivamente orientada a indumentaria femenina (ni para cuentas de empleados).
    - *Solución:* Retiro completo del selector de género en el HTML/TypeScript de Angular (`PerfilComponent`) y en el bottom sheet modal de Flutter (`PantallaPerfil`), manteniendo en el backend compatibilidad opcional sin forzar su uso.
13. **Falta de Persistencia y Refresco Inmediato de Perfil en Frontend Web**:
    - *Causa:* Los cambios confirmados en el modal de edición no actualizaban el storage local de sesión (`fashionstore_user`) y la estrategia `OnPush` no redibujaba los datos sin una recarga manual de página.
    - *Solución:* Implementación de `sincronizarSesionStorage(perfilActualizado)` e inyección de `ChangeDetectorRef` con llamada a `this.cdr.markForCheck()` tras la respuesta del backend.
14. **Discrepancia de Datos de Cuenta y Persistencia en App Móvil**:
    - *Causa:* `PantallaPerfil` consumía datos con un token mock por defecto en vez del token dinámico emitido por el login en Neon PostgreSQL, mostrando datos de prueba no coincidentes con el usuario real.
    - *Solución:* Conexión del callback `alCompletarLoginConToken` en `PantallaLogin` de Flutter hacia `PantallaPerfil(token: token)` y emisión reactiva inmediata de `PerfilCargadoState` en `PerfilBloc` tras el guardado atómico en PostgreSQL.

## [1.1.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU02 - Iniciar Sesión (Login / Autenticación Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU02-iniciar-sesion.md`](modules/autenticacion_seguridad/CU02-iniciar-sesion.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU02-iniciar-sesion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 
  - Backend: 28/28 tests en verde en `pytest` y verificación en vivo de autenticación (200 OK, 401 Unauthorized) con actualización atómica de `ultimo_acceso` en Neon PostgreSQL.
  - Frontend Web: Compilación limpia en 5.4s con Angular CLI (`npm run build`) y comunicación proxy verificada.
  - Mobile: 19/19 tests en verde en `flutter test` y 0 incidencias en `flutter analyze`.

### Registro de Errores Corregidos y Soluciones Aplicadas
8. **`OPTIONS 400 Bad Request` y `ClientException: Failed to fetch` en Flutter Web**:
   - *Causa:* Flutter Web corre en puertos efímeros dinámicos (`http://localhost:*`). Starlette `CORSMiddleware` rechazaba los preflights al no estar el puerto dinámico en `CORS_ORIGINS`.
   - *Solución:* Adición de `CORS_ORIGIN_REGEX: str | None = r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"` en `core/config.py` y `main.py`, permitiendo cualquier puerto local de depuración.
9. **Desbordamientos RenderFlex en `PantallaLogin` de Flutter**:
   - *Causa:* Rótulos de contraseña y checkbox desbordaban en viewports móviles reducidos.
   - *Solución:* Adaptación con `Flexible`, `Expanded` y `TextOverflow.ellipsis`.
10. **Ajuste de Ruta de Entrada y Enrutamiento Bidireccional en Mobile**:
   - *Causa:* La app iniciaba en registro y el enlace inferior no resolvía hacia login cuando era raíz.
   - *Solución:* `home: const PantallaLogin()` en `main.dart` y navegación bidireccional inteligente en `pantalla_registro.dart` con `canPop`/`pushReplacement`.

## [1.0.0] - 2026-09-19

### Promoción a Baseline Permanente
- **CU01 - Registrarse (Alta Costura & Omnicanal):** Promovido oficialmente a especificación permanente del sistema en [`modules/autenticacion_seguridad/CU01-registrarse.md`](modules/autenticacion_seguridad/CU01-registrarse.md).
- **Cierre de Ciclo de Cambio:** Archivados los artefactos de propuesta en `finalized/CU01-autenticacion/` y limpiado el directorio de cambios activos `changes/`.
- **Validación Completa:** 15/15 tests en verde en `Ec-backend`, 7/7 tests unitarios en `Ec-mobile`, build exitoso en `Ec-frontend`, y esquema PostgreSQL migrado a la base de datos en la nube (Neon Serverless).

### Registro de Errores Corregidos y Soluciones Aplicadas
1. **`ModuleNotFoundError: No module named 'core'`**:
   - *Causa:* Desalineación de imports tras mover módulos a `app/`.
   - *Solución:* Inserción de `app/` en `sys.path` y configuración de `pythonpath = ["app", "."]` en `pyproject.toml`.
2. **`ModuleNotFoundError: No module named 'psycopg2'`**:
   - *Causa:* Prefijo `postgresql://` invoca `psycopg2` por defecto en SQLAlchemy en lugar de `psycopg` (v3).
   - *Solución:* Normalización automática de URL a `postgresql+psycopg://` en `database.py` y `alembic/env.py`.
3. **`ImportError: email-validator is not installed`**:
   - *Causa:* Pydantic requiere `email-validator` para validar el tipo `EmailStr`.
   - *Solución:* Instalación y adición formal de `email-validator>=2.0.0` a `pyproject.toml`.
4. **Fallos 404 en `tests/test_health.py`**:
   - *Causa:* Doble instancia de FastAPI en memoria (`main` vs `app.main`).
   - *Solución:* Homologación estricta de imports a `from app.main import app` y limpieza de `.pyc`.
5. **Metadatos vacíos en Alembic (`Base.metadata` sin tablas)**:
   - *Causa:* SQLAlchemy requiere importar los modelos para registrar las tablas.
   - *Solución:* Auto-descubrimiento dinámico e introspección de paquetes con `pkgutil.walk_packages` e `importlib` en `alembic/env.py`.
6. **Incompatibilidad con PgBouncer en Neon (`unsupported startup parameter in options: search_path`)**:
   - *Causa:* El endpoint con connection pooling (`-pooler`) de Neon rechaza el parámetro `search_path` en el paquete de inicio.
   - *Solución:* Eliminación de `options` en `connect_args` y adopción del hook `@event.listens_for(engine, "connect")` para ejecutar `SET search_path TO fashionstore, public`.
7. **Discordancia de tipos en columna `rol` (`DatatypeMismatch`)**:
   - *Causa:* La columna `rol` es tipo `ENUM` nativo (`fashionstore.rol_usuario`), pero en el modelo `UsuarioORM` estaba tipada como `String(30)`, enviando `VARCHAR`.
   - *Solución:* Mapeo con `rol_usuario_enum = PG_ENUM(..., name="rol_usuario", schema="fashionstore", create_type=False)`.
