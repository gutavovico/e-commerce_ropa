# Especificación Permanente: CU04 - Gestionar Perfil del Cliente (Baseline del Sistema)

**Código:** CU04  
**Nombre:** Gestionar Perfil del Cliente (Consulta, Actualización de Datos Personales y Panel Mi Cuenta)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `app/modules/autenticacion_seguridad/cu04_gestionar_perfil`  
**Actores:** Cliente / Usuario Registrado Autenticado (Iniciador)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Baseline Promovido a Permanente)  
**Estado:** 🟢 Aprobado, Implementado y Verificado al 100% (45/45 Backend, 6/6 Web, 28/28 Mobile, Neon DB Sincronizada y Verificación en Vivo)  
**Fuentes de Verdad:** 
- Backend: Requisitos de negocio, entidades `fashionstore.clientes` y `fashionstore.usuarios` en `SI2-Parcial1.md`.
- Frontend Web: Mockup editorial "Mi Cuenta" (`media_1789842823031.png`).
- Mobile: Mockup de alta costura "Mi Cuenta" (`media_1789842906245.png`).
- Persistencia: Base de datos relacional Neon Serverless PostgreSQL (esquema `fashionstore`).

---

## 1. Descripción y Propósito

El caso de uso **CU04: Gestionar Perfil del Cliente** consolida la experiencia omnicanal para que los clientes autenticados de **FashionStore** puedan consultar y actualizar su perfil de usuario, su información de contacto y sus preferencias de alta costura (*Maison & Membresía / Mi Cuenta*).

El sistema garantiza que:
1. **Seguridad Criptográfica y Aislamiento:** Toda consulta o mutación de perfil requiere un token JWT Bearer válido. La identidad del cliente se resuelve de manera infalsificable a partir de la claim `sub = id_usuario` decodificada por el backend mediante la clave secreta `JWT_SECRET`, impidiendo que cualquier usuario acceda o modifique información de terceros.
2. **Atomicidad Relacional:** La actualización de datos sincroniza de forma atómica la tabla base `fashionstore.usuarios` (`nombres`, `apellidos`, `telefono`) y la tabla especializada `fashionstore.clientes` (`fecha_nacimiento`, `genero`, `talla_preferida`, `ciudad_preferida`, `acepta_marketing`).
3. **Regla de Negocio de Identidad de Marca (Alta Costura Femenina):** FashionStore es una firma y plataforma de moda exclusivamente femenina. Por tanto, las interfaces cliente (Web y Móvil) prescinden del selector de género en el formulario de edición de perfil. A nivel de base de datos se mantiene la columna como opcional para preservar compatibilidad con cuentas existentes y personal interno donde el catálogo de compras no aplique.
4. **Fidelidad Visual y UX Haute Couture:** Se replica con precisión milimétrica la jerarquía visual de los mockups editoriales en Web (Angular 19+ Standalone con Signals) y Móvil (Flutter 3.x con BLoC), incluyendo el número de socio (`SOCIO PRIVÉ #8402`), badges VIP, métricas de atelier, accesos a wishlist/bolsa, historial de pedidos y opciones de gestión personal.

---

## 2. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + Neon PostgreSQL)

### 2.1 Contrato de API REST

#### 1. Consulta de Perfil: `GET /api/v1/perfil`
- **Etiqueta Swagger / OpenAPI:** `Perfil y Cliente` / `Autenticacion y Seguridad`
- **Descripción:** Obtiene los datos consolidados de usuario y perfil del cliente autenticado.
- **Acceso:** Protegido (requiere cabecera `Authorization: Bearer <access_token>`).
- **Dependencias de Seguridad:** `get_current_user` (extrae usuario activo y valida rol `cliente`).
- **Respuesta Exitosa:** `200 OK` con esquema `PerfilClienteOut`.

#### 2. Actualización de Perfil: `PATCH /api/v1/perfil` (y alias `PUT /api/v1/perfil`)
- **Etiqueta Swagger / OpenAPI:** `Perfil y Cliente` / `Autenticacion y Seguridad`
- **Descripción:** Actualiza de forma total o parcial los campos editables del perfil del cliente autenticado.
- **Acceso:** Protegido (requiere cabecera `Authorization: Bearer <access_token>`).
- **Cuerpo de Solicitud:** `PerfilClienteUpdateIn` (JSON).
- **Respuesta Exitosa:** `200 OK` con esquema `PerfilClienteOut` actualizado y persistido.

---

### 2.2 Esquemas Pydantic (`app/modules/autenticacion_seguridad/cu04_gestionar_perfil/esquemas.py`)

#### A. Esquema de Salida: `PerfilClienteOut`
```python
from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class ResumenAtelierOut(BaseModel):
    visitas_registradas: int = Field(default=32, description="Visitas privadas registradas")
    boutiques_visitadas: int = Field(default=4, description="Número de boutiques frecuentadas")
    preferencia_textil: str = Field(default="100% Seda & Lana", description="Preferencia de fibras nobles")
    estatus_membresia: str = Field(default="Nivel Platino", description="Nivel de membresía de alta costura")


class PerfilClienteOut(BaseModel):
    # Identidad y Cuenta (Solo Lectura)
    id_usuario: int = Field(..., description="ID único del usuario")
    numero_socio: str = Field(..., description="Identificador formateado (ej. #8402)")
    email: EmailStr = Field(..., description="Correo electrónico registrado")
    rol: str = Field(default="cliente", description="Rol del usuario en la plataforma")
    fecha_registro: datetime = Field(..., description="Fecha de creación de la cuenta")
    miembro_desde: str = Field(..., description="Texto amigable (ej. Octubre 2021)")
    ultimo_acceso: Optional[datetime] = Field(None, description="Última sesión registrada")
    
    # Datos Personales Editables (Tabla fashionstore.usuarios)
    nombres: str = Field(..., min_length=1, max_length=100)
    apellidos: str = Field(..., min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=30)
    
    # Datos de Perfil de Alta Costura (Tabla fashionstore.clientes)
    fecha_nacimiento: Optional[date] = Field(None, description="Fecha de nacimiento")
    genero: Optional[str] = Field(None, description="femenino, masculino, no_binario, prefiero_no_decir")
    talla_preferida: Optional[str] = Field(None, description="XS, S, M, L, XL, XXL, etc.")
    ciudad_preferida: Optional[int] = Field(None, description="ID de ciudad preferida")
    acepta_marketing: bool = Field(default=True, description="Suscripción a comunicaciones privadas")
    
    # Métricas y Membresía Atelier
    resumen_atelier: ResumenAtelierOut = Field(default_factory=ResumenAtelierOut)
```

#### B. Esquema de Entrada: `PerfilClienteUpdateIn`
```python
class PerfilClienteUpdateIn(BaseModel):
    nombres: Optional[str] = Field(None, min_length=1, max_length=100)
    apellidos: Optional[str] = Field(None, min_length=1, max_length=100)
    telefono: Optional[str] = Field(None, max_length=30)
    fecha_nacimiento: Optional[date] = Field(None)
    genero: Optional[str] = Field(None, pattern="^(femenino|masculino|no_binario|prefiero_no_decir)$")
    talla_preferida: Optional[str] = Field(None, pattern="^(XS|S|M|L|XL|XXL|[0-9]{2})$")
    ciudad_preferida: Optional[int] = Field(None)
    acepta_marketing: Optional[bool] = Field(None)
```

---

### 2.3 Capa de Seguridad y Reglas de Negocio (`app/core/deps.py`)

1. **Extracción y Decodificación de Token (`get_current_user`):**
   - Extrae el token de la cabecera `Authorization: Bearer <token>`.
   - Decodifica criptográficamente el JWT con `decode_access_token` usando `JWT_SECRET`.
   - Si el token está ausente, expirado o malformado, lanza `AuthenticationError("Token no válido o expirado", code="TOKEN_INVALIDO")` (**HTTP 401**).
   - Consulta al usuario en `fashionstore.usuarios` realizando carga ansiosa de su relación con `fashionstore.clientes` (`select(UsuarioORM).options(joinedload(UsuarioORM.cliente))`).
   - Verifica que la cuenta esté activa (`usuario.activo == True`). De lo contrario lanza `AuthorizationError("La cuenta se encuentra inactiva", code="CUENTA_INACTIVA")` (**HTTP 403**).
2. **Duración de Tokens JWT de Desarrollo (`ACCESS_TOKEN_EXPIRE_MINUTES`):**
   - Se estableció en `1440` minutos (24 horas) en `app/core/config.py` y `.env` para garantizar persistencia durante flujos extensos de depuración y navegación sin cierres intempestivos de sesión.
3. **Persistencia Atómica y Transaccional (`ServicioPerfilCliente`):**
   - Las mutaciones actualizan selectivamente los campos no nulos de `UsuarioORM` y `ClienteORM`.
   - Se ejecuta `db.add(...)`, `db.commit()` y posterior refresco relacional para asegurar que ambas tablas se sincronicen atómicamente.

---

### 2.4 Criterios de Aceptación Backend (Gherkin BDD)

```gherkin
Característica: CU04 - Consulta y Actualización de Perfil de Cliente
  Como cliente autenticado de FashionStore
  Quiero consultar y modificar mis datos de perfil
  Para mantener actualizada mi información de contacto y preferencias de talla

  Escenario: Consulta exitosa de perfil de cliente
    Dado que un cliente cuenta con un token JWT Bearer válido
    Cuando envía una petición GET a "/api/v1/perfil"
    Entonces el backend responde con código HTTP 200 OK
    Y el cuerpo incluye el email, nombres, apellidos, teléfono y datos de cliente
    Y se incluye el identificador de socio y resumen de atelier.

  Escenario: Actualización exitosa de nombres, teléfono y talla preferida
    Dado que un cliente autenticado envía una petición PATCH a "/api/v1/perfil"
    Con nombres "Ana María", teléfono "+34 600 111 222" y talla_preferida "M"
    Cuando se procesa la solicitud en el backend
    Entonces responde con código HTTP 200 OK
    Y los campos quedan persistidos en "fashionstore.usuarios" y "fashionstore.clientes"
    Y el cuerpo devuelto refleja los nuevos valores actualizados.

  Escenario: Intento de acceso sin token de autenticación
    Dado que se envía una petición GET a "/api/v1/perfil" sin cabecera Authorization
    Cuando el servidor evalúa la solicitud
    Entonces responde con código HTTP 401 Unauthorized
    Y el cuerpo contiene "code": "TOKEN_INVALIDO".

  Escenario: Intento de actualizar con formato de talla no permitido
    Dado que un cliente envía un PATCH a "/api/v1/perfil" con talla_preferida "GIGANTE"
    Cuando se valida el esquema Pydantic
    Entonces el backend responde con código HTTP 422 Unprocessable Entity
    Y la base de datos no sufre ninguna modificación.
```

---

## 3. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone & Tailwind CSS)

### 3.1 Arquitectura del Componente `PerfilComponent`

- **Ruta:** `/perfil` y `/mi-cuenta` en `app.routes.ts`, protegidas por `authGuard`.
- **Patrón de Estado:** Reactivo con Signals de Angular 19:
  - `perfil = signal<PerfilCliente | null>(null)`
  - `cargando = signal<boolean>(false)`
  - `editando = signal<boolean>(false)`
  - `guardando = signal<boolean>(false)`
  - `mensajeFeedback = signal<{ tipo: 'exito' | 'error', texto: string } | null>(null)`
- **Estrategia de Detección de Cambios:** `ChangeDetectionStrategy.OnPush` complementada con `ChangeDetectorRef.markForCheck()` para refresco inmediato de vista tras operaciones asíncronas.
- **Sincronización de Sesión:** Función `sincronizarSesionStorage(perfilActualizado)` que mantiene consistentes las claves de `localStorage` y `sessionStorage` (`fashionstore_user`, `nombres`, `apellidos`, `telefono`) tras cada guardado.

### 3.2 Diseño Visual Editorial (Pixel-Match con `media_1789842823031.png`)

1. **Cabecera Institucional:** Logotipo `FASHION STORE`, navegación superior con indicador activo inferior en `PERFIL`, accesos directos a Notificaciones, Bolsa y avatar.
2. **Header de Membresía:** Cápsula dorada `MAISON & MEMBRESÍA • ATELIER VIP`, titular `Mi Cuenta` en Outfit 36px y badge `PROTOCOLO DE CIFRADO ACTIVO: 256-BIT`.
3. **Tarjeta de Perfil Principal:** Avatar editorial con botón de cámara, indicador de membresía `SOCIO PRIVÉ #8402 · Miembro desde Octubre 2021`, nombre y apellidos destacados, etiquetas de contacto y botón oscuro `[ ✏ EDITAR INFORMACIÓN ]`.
4. **Matriz de Atelier (4 Tarjetas Horizontales):**
   - `ACTIVIDAD ATELIER`: 32 Visitas registradas en salones privados.
   - `PRESENCIA GLOBAL`: 4 Boutiques (Madrid, París, Milán, Londres).
   - `PREFERENCIA TEXTIL`: 100% Seda & Lana (Fibras naturales puras).
   - `ESTATUS MEMBRESÍA`: Nivel Platino con candado VIP.
5. **Tarjetas de Acción:** Wishlist de Temporada y Bolsa de Compra con enlace directo a checkout.
6. **Layout Dividido (60% / 40%):**
   - Columna izquierda: Registro histórico de pedidos con badges de estado y botón `VER FACTURA DIGITAL`.
   - Columna derecha: Opciones de gestión (direcciones, tarjetas, personal shopper) y tarjeta para agendar citas privadas de atelier.
7. **Modal de Edición Reactivo:**
   - Campos: Nombres, Apellidos, Teléfono de contacto, Talla preferida de alta costura, Suscripción a comunicaciones de marketing.
   - **Exclusión de Género:** Selector de género omitido por diseño de marca (plataforma exclusiva femenina).

---

## 4. Bloque 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x + Dart + BLoC)

### 4.1 Arquitectura Limpia y Gestor de Estado BLoC

- **Ubicación:** `lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/`
- **Estados Sellados (`PerfilEstado`):**
  - `PerfilInicial`: Estado de arranque.
  - `PerfilCargando`: Spinner visual durante la consulta a `GET /api/v1/perfil`.
  - `PerfilCargado(PerfilClienteDto perfil)`: Perfil cargado listo para renderizar.
  - `PerfilActualizando(PerfilClienteDto perfilActual)`: Estado durante el guardado de la edición.
  - `PerfilError(String mensaje, {String? codigo})`: Captura de errores de red o autenticación.
- **Eventos (`PerfilEvento`):** `CargarPerfil()`, `ActualizarPerfil(PerfilClienteUpdateDto nuevosDatos)`, `CerrarSesion()`.
- **Integración y Flujo de Autenticación:**
  - `PantallaLogin` implementa el callback `alCompletarLoginConToken: (token) => ...`, permitiendo propagar de forma segura el JWT generado en el backend hacia `PantallaPerfil(token: token)`.
  - La pantalla consulta en tiempo real los datos del cliente desde Neon PostgreSQL y emite las mutaciones vía `PATCH /api/v1/perfil`.

### 4.2 Diseño Visual Móvil Haute Couture (Pixel-Match con `media_1789842906245.png`)

1. **Barra Superior (AppBar):** Identificador `FASHION STORE | PERFIL`, campana de alertas y bolsa con contador.
2. **Membresía y Perfil:** Titular `Mi Cuenta`, badge `• ATELIER VIP`, avatar con botón de cámara, identificador `SOCIO PRIVÉ #8402`, nombre de cliente y botón `Editar Información`.
3. **Métricas en 3 Columnas:** Tarjeta gris unificada con visitas registradas, boutiques y preferencia textil.
4. **Tarjetas Gemelas:** Acceso rápido a Wishlist y Bolsa.
5. **Historial de Pedidos:** Tarjetas verticales de prendas anteriores con botón de factura/ticket.
6. **Menú de Servicios:** Direcciones de entrega, tarjetas de pago y personal shopper asignado con chevrons de navegación.
7. **Botón Inferior:** `[ ↪ CERRAR SESIÓN SEGURA ]`.
8. **Modal BottomSheet de Edición:** Edición reactiva de datos personales sin selector de género, con actualización instantánea del BLoC y persistencia en base de datos.
9. **BottomNavigationBar:** Barra de navegación fija con 4 pestañas (`INICIO`, `BUSCAR`, `CATÁLOGO`, `PERFIL`) con la pestaña de perfil resaltada.

---

## 5. Historial de Decisiones Arquitectónicas y Soluciones Técnicas

Durante el ciclo de diseño, implementación y verificación de CU04 se diagnosticaron y resolvieron 4 aspectos técnicos clave:

1. **Ampliación del Tiempo de Vida del JWT para Desarrollo (`ACCESS_TOKEN_EXPIRE_MINUTES = 1440`):**
   - *Problema:* Tokens con expiración reducida (15 a 60 minutos) provocaban errores `401 Unauthorized: Signature has expired` durante flujos prolongados de prueba y navegación manual.
   - *Solución:* Se ajustó a 24 horas (1440 minutos) en `app/core/config.py` y `.env`.
2. **Eliminación del Selector de Género por Regla de Negocio de Marca:**
   - *Problema:* El selector de género se encontraba en los formularios de edición de Web y Móvil, contradiciendo el modelo de negocio de FashionStore como firma exclusivamente orientada a moda femenina (y no aplicable a cuentas de empleados).
   - *Solución:* Se retiró por completo del frontend (`PerfilComponent`) y del modal bottom sheet móvil (`PantallaPerfil`), manteniendo en el backend la compatibilidad opcional sin forzar su uso.
3. **Persistencia y Refresco Inmediato de Sesión en Frontend Web:**
   - *Problema:* Al editar el perfil, los cambios se enviaban a la API pero la interfaz bajo `ChangeDetectionStrategy.OnPush` no refrescaba visualmente los campos hasta una recarga manual y los datos en sesión (`sessionStorage`/`localStorage`) quedaban desactualizados.
   - *Solución:* Se inyectó `ChangeDetectorRef` ejecutando `markForCheck()` tras la confirmación de la API y se implementó `sincronizarSesionStorage` para mantener la coherencia en el almacenamiento local del navegador.
4. **Propagación Dinámica de Token JWT y Sincronización en la App Móvil:**
   - *Problema:* La pantalla de perfil móvil utilizaba un token de prueba estático y no mostraba los datos reales del usuario logueado en la base de datos de Neon PostgreSQL.
   - *Solución:* Se configuró el callback `alCompletarLoginConToken` en `PantallaLogin`, pasando el token real a `PantallaPerfil` y enlazándolo con `PerfilBloc` para realizar consultas y mutaciones directas sobre la cuenta autenticada.

---

## 6. Evidencias de Verificación y Cierre

1. **Backend (`Ec-backend`):** 45/45 tests en verde en `pytest` para toda la suite acumulada (autenticación, registro, login y perfil). Verificación de persistencia atómica en tablas `fashionstore.usuarios` y `fashionstore.clientes` en Neon PostgreSQL.
2. **Frontend Web (`Ec-frontend`):** Compilación limpia sin errores (`npm run build`, bundle `perfil-component` 34.54 kB), 6/6 pruebas unitarias pasando en `ng test`, sincronización reactiva de sesión verificada.
3. **Aplicación Móvil (`Ec-mobile`):** 28/28 pruebas automatizadas pasando al 100% en `flutter test` (DTOs, BLoC, widgets y pantallas) y 0 incidencias en `flutter analyze`.
4. **Verificación en Vivo:** Validado y confirmado por el usuario en web y móvil.
