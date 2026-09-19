# Plan de Ejecución Secuencial: CU04 - Gestionar Perfil del Cliente

**Caso de Uso:** CU04. Gestionar Perfil del Cliente  
**Metodología:** Spec-Driven Development (SDD) & PUDS  
**Estrategia:** Desarrollo Estrictamente Secuencial por Fases (Backend -> Frontend Web -> Mobile)  
**Fecha:** 2026-09-19  
**Estado:** 🟢 100% Ejecutado y Promovido a Baseline  

---

## 1. Fase 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

### Oleada 1: Dependencias de Seguridad y Extracción de JWT (`app/core/deps.py`)
- Formalizar `get_current_user(token, db)` en `app/core/deps.py`.
- Extraer `sub` (ID de usuario) desde el token Bearer decodificado con `decode_access_token`.
- Realizar consulta a `fashionstore.usuarios` con carga ansiosa (`joinedload`) de `UsuarioORM.cliente`.
- Validar `usuario.activo == True` y lanzar `AuthenticationError` (401) o `AuthorizationError` (403).
- Implementar `require_roles(roles_permitidos)` como guardia de autorización.

### Oleada 2: Esquemas Pydantic (`cu04_gestionar_perfil/esquemas.py`)
- Crear `PerfilClienteOut` (solo lectura, metadatos, datos de usuario y cliente, resumen de atelier).
- Crear `PerfilClienteUpdateIn` (campos editables con validación de expresiones regulares de tallas y género).

### Oleada 3: Servicio de Dominio (`cu04_gestionar_perfil/servicio.py`)
- Crear clase `ServicioPerfilCliente`:
  - `obtener_perfil(db, usuario)`: Transforma la entidad `UsuarioORM` y su relación `ClienteORM` al DTO `PerfilClienteOut`, calculando el número de socio y miembro desde.
  - `actualizar_perfil(db, usuario, datos)`: Aplica cambios atómicos en `UsuarioORM` (`nombres`, `apellidos`, `telefono`) y `ClienteORM` (`fecha_nacimiento`, `genero`, `talla_preferida`, `ciudad_preferida`, `acepta_marketing`), asegurando atomicidad con `db.commit()`.

### Oleada 4: Router HTTP y Montaje (`cu04_gestionar_perfil/router.py`)
- `GET /perfil`: Protegido con `Depends(get_current_user)`, retorna `PerfilClienteOut`.
- `PATCH /perfil`: Protegido con `Depends(get_current_user)`, recibe `PerfilClienteUpdateIn` y retorna `PerfilClienteOut`.
- Montar `cu04_router` en `app/modules/autenticacion_seguridad/router.py` bajo el prefijo `/perfil`.

### Oleada 5: Suite de Pruebas Automatizadas Backend (`tests/`)
- Tests unitarios de esquemas Pydantic y lógica de servicio.
- Tests de integración HTTP con `TestClient` simulando tokens válidos, expirados, roles denegados y payloads inválidos (cobertura 200, 401, 403, 422).

---

## 2. Fase 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### Oleada 6: DTOs e Interfaz de Dominio (`cu04_gestionar_perfil/modelos/`)
- Declarar interfaces `PerfilCliente`, `PerfilClienteActualizar` y `ResumenAtelier` en TypeScript.

### Oleada 7: Servicio HTTP y Estado Reactivo (`cu04_gestionar_perfil/servicios/`)
- Crear `PerfilService` inyectable (`providedIn: 'root'`) con `HttpClient`.
- Métodos `obtenerPerfil()` y `actualizarPerfil(datos)` enviando la cabecera `Authorization: Bearer <token>` (usando el token persistido por `LoginService`).
- Señales reactivas de estado (`perfil`, `cargando`, `guardando`, `error`).

### Oleada 8: Componente Standalone de Perfil (`cu04_gestionar_perfil/paginas/`)
- Maquetar `PerfilComponent` con `ChangeDetectionStrategy.OnPush`:
  - Navbar superior institucional y breadcrumb editorial VIP.
  - Tarjeta de perfil principal con avatar, metadatos de socio, contactos y botón `EDITAR INFORMACIÓN`.
  - Grid de 4 estadísticas de atelier.
  - Accesos directos a Wishlist y Bolsa.
  - Layout dividido: Registro histórico de pedidos a la izquierda y menú de servicios/preferencias a la derecha.
  - Botón de cierre de sesión seguro conectado a `LoginService.cerrarSesion()`.
  - Modal/formulario flotante para edición de datos personales con Typed Forms y validaciones.
  - Exclusión de opción de género por modelo de negocio.

### Oleada 9: Enrutamiento y Guardias de Seguridad (`app.routes.ts`)
- Configurar rutas `/perfil` y `/mi-cuenta` con carga diferida (`loadComponent`).
- Configurar `AuthGuard` funcional para redirigir a `/login` si no hay sesión activa.

### Oleada 10: Compilación y Verificación Web
- Compilación de producción con Angular CLI (`npm run build`).
- Prueba de comunicación y renderizado en vivo mediante el proxy de desarrollo.

---

## 3. Fase 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x)

### Oleada 11: Modelos y DTOs Dart (`cu04_gestionar_perfil/datos/modelos/`)
- Crear `PerfilClienteDto` con `fromJson` y `PerfilClienteUpdateDto` con `toJson`.

### Oleada 12: Datasource y Repositorio Remoto (`cu04_gestionar_perfil/datos/` y `dominio/`)
- Implementar `PerfilRemotoDatasource` consumiendo `GET /api/v1/perfil` y `PATCH /api/v1/perfil`.
- Implementar `PerfilRepositorio` con manejo de excepciones tipadas (`PerfilExcepcion`, `TokenInvalidoExcepcion`).

### Oleada 13: Gestor de Estado BLoC (`cu04_gestionar_perfil/presentacion/bloc/`)
- Crear estados sellados: `PerfilInicial`, `PerfilCargando`, `PerfilCargado`, `PerfilActualizando`, `PerfilError`.
- Implementar `PerfilBloc` con métodos para recargar datos y enviar actualizaciones.

### Oleada 14: Vista Móvil Haute Couture (`cu04_gestionar_perfil/presentacion/pantallas/`)
- Maquetar `PantallaPerfil` reproduciendo fielmente el mockup móvil:
  - Header superior `FASHION STORE | PERFIL` con acciones.
  - Tarjeta de perfil con avatar, badge de cámara, número de socio y botón `Editar Información`.
  - Banda de estadísticas en 3 columnas.
  - Tarjetas gemelas para Wishlist y Bolsa.
  - Lista de pedidos anteriores con botón de factura.
  - Preferencias y configuración con chevrons de navegación.
  - Botón inferior de cierre de sesión.
  - BottomNavigationBar persistente con la pestaña `PERFIL` activa.
  - Integración de login con callback `alCompletarLoginConToken` hacia `PantallaPerfil(token: token)`.
  - BottomSheet de edición reactiva en vivo sin selector de género.

### Oleada 15: Suite de Pruebas y Análisis Móvil
- Pruebas unitarias de DTOs y BLoC (`test/perfil_bloc_test.dart`, `test/perfil_dto_test.dart`).
- Pruebas de widget de la pantalla de perfil (`test/pantalla_perfil_test.dart`).
- Verificación de calidad con `flutter test` y `flutter analyze`.
