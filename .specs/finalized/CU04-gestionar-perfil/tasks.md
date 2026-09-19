# Tareas de Implementación: CU04 - Gestionar Perfil del Cliente

**Caso de Uso:** CU04. Gestionar Perfil del Cliente  
**Alcance:** Bloque 1 (Backend), Bloque 2 (Frontend Web) y Bloque 3 (Mobile)  
**Estado:** 🟢 100% Ejecutado y Promovido a Baseline  

---

## Bloque 1: Backend (`Ec-backend`)

- [x] **T1: Dependencias de Autenticación y Autorización (`app/core/deps.py`)**
  - [x] Implementar función `get_current_user` extrayendo el token Bearer del header `Authorization`.
  - [x] Validar firma y expiración del JWT con `decode_access_token`.
  - [x] Consultar el usuario en `fashionstore.usuarios` con `joinedload(UsuarioORM.cliente)`.
  - [x] Lanzar `AuthenticationError` (401) ante token expirado o firma inválida.
  - [x] Lanzar `AuthorizationError` (403) ante cuenta con `activo == False`.
  - [x] Implementar decorador/función de dependencia `require_roles(roles)`.

- [x] **T2: Esquemas Pydantic (`cu04_gestionar_perfil/esquemas.py`)**
  - [x] Definir `PerfilClienteOut` con datos de cuenta, datos personales, preferencias de cliente y resumen de membresía.
  - [x] Definir `PerfilClienteUpdateIn` con validaciones de longitud, regex para tallas y género permitido.

- [x] **T3: Servicio de Perfil (`cu04_gestionar_perfil/servicio.py`)**
  - [x] Implementar `ServicioPerfilCliente.obtener_perfil(db, usuario)`.
  - [x] Implementar `ServicioPerfilCliente.actualizar_perfil(db, usuario, datos)` garantizando atomicidad y consistencia en `usuarios` y `clientes`.

- [x] **T4: Router HTTP y Montaje (`cu04_gestionar_perfil/router.py`)**
  - [x] Crear endpoint `GET /perfil` con status 200 OK y modelo `PerfilClienteOut`.
  - [x] Crear endpoint `PATCH /perfil` con status 200 OK y payload `PerfilClienteUpdateIn`.
  - [x] Montar el router en `app/modules/autenticacion_seguridad/router.py` y `app/main.py`.

- [x] **T5: Suite de Pruebas Automatizadas Backend (`test_cu04_gestionar_perfil.py`)**
  - [x] Tests unitarios de esquemas `PerfilClienteOut` y `PerfilClienteUpdateIn`.
  - [x] Tests de integración con `TestClient` para casos 200 OK (consulta y actualización).
  - [x] Tests de error para token ausente/inválido (401), rol no autorizado (403) y validación de tallas (422).
  - [x] Verificación de ejecución completa con `pytest` en verde (45/45 tests passing).

---

## Bloque 2: Frontend Web (`Ec-frontend`)

- [x] **T6: Modelos e Interfaces TypeScript (`cu04_gestionar_perfil/modelos/perfil.dto.ts`)**
  - [x] Definir interfaces `PerfilCliente`, `PerfilClienteActualizar` y `ResumenAtelier`.
  - [x] Garantizar paridad 1:1 con las respuestas y tipos del backend FastAPI.

- [x] **T7: Servicio HTTP de Perfil (`cu04_gestionar_perfil/servicios/perfil.service.ts`)**
  - [x] Implementar `PerfilService` inyectando `HttpClient`.
  - [x] Crear métodos `obtenerPerfil()` y `actualizarPerfil(datos)` inyectando cabecera Bearer con el token de sesión.
  - [x] Implementar Signals reactivas para perfil cargado, estados de carga y mensajes de notificación.

- [x] **T8: Componente Standalone de Perfil (`cu04_gestionar_perfil/paginas/`)**
  - [x] Maquetar `PerfilComponent` conforme a `media_1789842823031.png`:
    - [x] Cabecera con `FASHION STORE`, navegación y enlace `PERFIL` activo.
    - [x] Breadcrumb `MAISON & MEMBRESÍA • ATELIER VIP` y titular `Mi Cuenta`.
    - [x] Tarjeta de perfil con avatar, botón de cámara, badge `SOCIO PRIVÉ #8402`, nombre y botón `EDITAR INFORMACIÓN`.
    - [x] Matriz de 4 tarjetas de estadísticas de atelier.
    - [x] Tarjetas de acceso rápido a Wishlist y Bolsa.
    - [x] Split layout: Pedidos históricos (izquierda) y Preferencias/Servicios (derecha).
    - [x] Botón de cierre de sesión seguro `CERRAR SESIÓN SEGURA`.
    - [x] Modal reactivo para actualizar datos: selector de género eliminado (plataforma exclusiva de moda femenina).
    - [x] Sincronización atómica de sesión en `sessionStorage` y `localStorage` con `ChangeDetectorRef.markForCheck()`.

- [x] **T9: Configuración de Rutas y Guardias (`app.routes.ts`)**
  - [x] Registrar rutas `/perfil` y `/mi-cuenta` con carga diferida (`loadComponent`).
  - [x] Añadir guardia de autenticación funcional (`authGuard`) que redirija a `/login` si no existe token.
  - [x] Configuración de proxy HTTP hacia `http://127.0.0.1:8000` en `proxy.conf.json`.

- [x] **T10: Compilación y Verificación de Calidad Web**
  - [x] Compilación limpia con Angular CLI (`npm run build` en 0 errores, chunk `perfil-component` 34.54 kB).
  - [x] Suite de pruebas automatizadas en verde (`npx ng test --watch=false`, 6/6 tests pasando).

---

## Bloque 3: Aplicación Móvil (`Ec-mobile`)

- [x] **T11: Modelos y DTOs Dart (`cu04_gestionar_perfil/datos/modelos/perfil_dto.dart`)**
  - [x] Implementar `PerfilClienteDto` con `fromJson` y `PerfilClienteUpdateDto` con `toJson`.
  - [x] Implementar `ResumenAtelierDto` y `PedidoMovilDto` con mapeo de campos y valores predeterminados.

- [x] **T12: Datasource Remoto y Repositorio (`cu04_gestionar_perfil/datos/` y `dominio/`)**
  - [x] Crear `PerfilRemotoDatasource` consumiendo `GET /api/v1/perfil` y `PATCH /api/v1/perfil`.
  - [x] Crear `PerfilRepositorio` con manejo seguro de tokens y excepciones tipadas.

- [x] **T13: Controlador de Estado BLoC (`cu04_gestionar_perfil/presentacion/bloc/`)**
  - [x] Definir estados sellados: `PerfilInicial`, `PerfilCargando`, `PerfilCargado`, `PerfilActualizando`, `PerfilActualizado`, `PerfilError`.
  - [x] Implementar `PerfilBloc` para orquestar la carga de perfil y la actualización de datos personales.

- [x] **T14: Vista Móvil Haute Couture (`cu04_gestionar_perfil/presentacion/pantallas/`)**
  - [x] Maquetar `PantallaPerfil` conforme a `media_1789842906245.png`:
    - [x] Propagación del token real de sesión desde `PantallaLogin` (`alCompletarLoginConToken`) en `main.dart`.
    - [x] Consulta y renderizado en vivo de los datos del cliente desde Neon PostgreSQL.
    - [x] AppBar con logotipo `FASHION STORE | PERFIL`, campana y bolsa con contador badge.
    - [x] Titular `Mi Cuenta` y badge `• ATELIER VIP`.
    - [x] Tarjeta de cliente con foto, número de socio `SOCIO PRIVÉ #8402`, nombre y botón `Editar Información`.
    - [x] Fila de métricas en tarjeta gris (32 visitas, 4 boutiques, 100% seda & lana).
    - [x] Tarjetas gemelas Wishlist y Bolsa.
    - [x] Lista vertical de pedidos anteriores con botón de factura/ticket.
    - [x] Lista de opciones de preferencias (direcciones, pagos, personal shopper).
    - [x] Botón de cierre de sesión seguro `CERRAR SESIÓN SEGURA`.
    - [x] BottomNavigationBar con pestaña `PERFIL` activa.
    - [x] Modal bottom sheet para editar información personal sin selector de género y con actualización reactiva en vivo.

- [x] **T15: Suite de Pruebas Móviles y Análisis Estático**
  - [x] Pruebas unitarias de DTOs y BLoC (`perfil_dto_test.dart`, `perfil_bloc_test.dart`).
  - [x] Pruebas de widget de la pantalla de perfil (`pantalla_perfil_test.dart`).
  - [x] Verificación de calidad con `flutter test` (100% verde: 28/28 tests pasando) y `flutter analyze` (0 issues).
