# Especificación Técnica: CU04 - Gestionar Perfil del Cliente

**Código:** CU04  
**Nombre:** Gestionar Perfil del Cliente (Consulta, Actualización de Datos Personales y Panel Mi Cuenta)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `cu04_gestionar_perfil`  
**Actores:** Cliente Autenticado (Iniciador)  
**Metodología:** Spec-Driven Development (SDD) & PUDS  
**Versión:** 1.0.0  
**Estado:** 🟢 Aprobado e Implementado al 100% (Bloques 1, 2 y 3) — Promovido a Permanente  
**Fuentes de Verdad:**
- Backend: Requisitos de negocio, entidad `fashionstore.clientes` y `fashionstore.usuarios` en `SI2-Parcial1.md`.
- Frontend Web: Mockup editorial "Mi Cuenta" (`media_1789842823031.png`).
- Mobile: Mockup de alta costura "Mi Cuenta" (`media_1789842906245.png`).

---

## 1. Descripción y Propósito del Caso de Uso

El caso de uso **CU04: Gestionar perfil del cliente** permite al cliente autenticado de **FashionStore** consultar de manera centralizada su panel de cuenta (*Maison & Membresía / Mi Cuenta*) y actualizar de forma segura sus datos personales de contacto, preferencias de talla y canales de comunicación.

### Objetivos Clave:
1. **Seguridad y Privacidad:** Extracción estricta de la identidad del cliente mediante el token Bearer JWT (`sub = id_usuario`). Los clientes solo pueden consultar y modificar su propia información.
2. **Integridad Relacional:** Modificación coordinada y atómica entre la tabla base `fashionstore.usuarios` (`nombres`, `apellidos`, `telefono`) y la tabla de perfil `fashionstore.clientes` (`fecha_nacimiento`, `genero`, `talla_preferida`, `ciudad_preferida`, `acepta_marketing`).
3. **Consistencia Visual Omnicanal Haute Couture:** Reproducción exacta de la jerarquía visual de los mockups en Desktop Web (Angular 19+) y Mobile (Flutter 3.x), incluyendo número de socio (`SOCIO PRIVÉ #8402`), badges VIP, métricas de atelier, accesos a wishlist/bolsa, registro histórico y opciones de configuración.
4. **Regla de Negocio de Marca:** Omisión del selector de género en los formularios de edición de perfil web y móvil al tratarse de una firma orientada exclusivamente a moda femenina.

---

## 2. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0 + PostgreSQL Neon)

### 2.1 Contrato de API REST

#### 1. Consulta de Perfil: `GET /api/v1/perfil`
- **Descripción:** Obtiene los datos consolidados de usuario y perfil del cliente autenticado.
- **Seguridad:** Requiere cabecera `Authorization: Bearer <access_token>`.
- **Dependencias:** `get_current_user` (extrae usuario activo y valida rol `cliente`).
- **Respuesta Exitosa:** `200 OK` con esquema `PerfilClienteOut`.

#### 2. Actualización de Perfil: `PATCH /api/v1/perfil` (y alias `PUT /api/v1/perfil`)
- **Descripción:** Actualiza de forma total o parcial los campos editables del perfil del cliente.
- **Seguridad:** Requiere cabecera `Authorization: Bearer <access_token>`.
- **Cuerpo de Solicitud:** `PerfilClienteUpdateIn` (JSON).
- **Respuesta Exitosa:** `200 OK` con esquema `PerfilClienteOut` actualizado.

---

### 2.2 Esquemas Pydantic (`cu04_gestionar_perfil/esquemas.py`)

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

### 2.3 Reglas de Negocio, Seguridad y Dependencias (`core/deps.py`)

1. **Formalización de `get_current_user` en `core/deps.py`:**
   - Extrae el token Bearer de la cabecera `Authorization: Bearer <token>`.
   - Decodifica criptográficamente el token con `decode_access_token(token)` usando `JWT_SECRET`.
   - Manejo de excepciones: Si el token está expirado, corrupto o ausente, lanza `AuthenticationError("Token no válido o expirado", code="TOKEN_INVALIDO")` (**HTTP 401**).
   - Busca el usuario en PostgreSQL (`fashionstore.usuarios`) junto con su relación `cliente` mediante `select(UsuarioORM).options(joinedload(UsuarioORM.cliente))`.
   - Verifica que el usuario exista y esté activo (`usuario.activo == True`). Si no está activo, lanza `AuthorizationError("La cuenta se encuentra inactiva", code="CUENTA_INACTIVA")` (**HTTP 403**).
2. **Verificación de Rol (`require_roles(["cliente"])`):**
   - Asegura que el usuario autenticado posea el rol `cliente`.
3. **Integridad de Datos en Actualización:**
   - La transacción actualiza los campos de `UsuarioORM` (`nombres`, `apellidos`, `telefono`) y `ClienteORM` (`fecha_nacimiento`, `genero`, `talla_preferida`, `ciudad_preferida`, `acepta_marketing`).
   - Los campos `id_usuario`, `email`, `rol` y `fecha_registro` son estrictamente inmutables desde este endpoint.
   - Se realiza `db.commit()` atómico y `db.refresh()`.

#### Matriz de Códigos HTTP
| Código | Condición | Detalle |
|---|---|---|
| **`200 OK`** | Consulta o actualización exitosa | Retorna `PerfilClienteOut` completo |
| **`401 Unauthorized`** | Token ausente, inválido o expirado | `{"detail": "Token no válido o expirado", "code": "TOKEN_INVALIDO"}` |
| **`403 Forbidden`** | Usuario con rol distinto o cuenta inactiva | `{"detail": "Acceso restringido", "code": "ACCESO_DENEGADO"}` |
| **`422 Unprocessable`** | Talla inválida, género no reconocido o fechas mal formadas | `{"detail": [{"loc": ["body", "talla_preferida"], ...}]}` |

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

### 3.1 Análisis de UI Fiel a Mockup Desktop (`media_1789842823031.png`)

1. **Barra de Navegación Superior Institucional:**
   - Marca: `FASHION STORE` (mayúsculas espaciadas).
   - Enlaces de cabecera: `INICIO`, `BUSCAR`, `CATÁLOGO`, `PERFIL` (con barra indicadora activa inferior en `PERFIL`).
   - Iconos de la derecha: Notificaciones / usuario, bolsa de compra, avatar circular miniatura del usuario.
2. **Encabezado y Metadatos de Seguridad:**
   - Rótulo superior: `MAISON & MEMBRESÍA • ATELIER VIP` en cápsula beige dorada.
   - Titular principal: `Mi Cuenta` en Outfit 36px.
   - Indicador a la derecha: `PROTOCOLO DE CIFRADO ACTIVO: 256-BIT` con punto indicador de seguridad.
3. **Tarjeta de Perfil Principal (White Luxury Canvas):**
   - Avatar editorial (100x100 px) con botón interactivo de cámara en esquina inferior derecha para actualización de foto.
   - Metadatos: `SOCIO PRIVÉ #8402 · Miembro desde Octubre 2021`.
   - Nombre: `Ana Valenzuela`.
   - Datos de contacto en pastillas: Email (`ana.valenzuela@studio.es`), Teléfono (`+34 612 884 901`).
   - Botón de acción: `[ ✏ EDITAR INFORMACIÓN ]` que despliega el formulario modal de edición.
4. **Matriz de Métricas de Atelier (4 Tarjetas Horizontales):**
   - `ACTIVIDAD ATELIER`: `32 Visitas registradas` / `En salones privados`
   - `PRESENCIA GLOBAL`: `4 Boutiques` / `Madrid, París, Milán, Londres`
   - `PREFERENCIA TEXTIL`: `100% Seda & Lana` / `Fibras naturales puras`
   - `ESTATUS MEMBRESÍA`: `Nivel Platino 🔒` / `Acceso exclusivo limitado`
5. **Tarjetas de Acción Rápida (2 Columnas):**
   - `Wishlist de Temporada` (corazón, prendas guardadas, enlace `EXPLORAR PIEZAS →`).
   - `Bolsa de Compra` (bolsa, artículos en curso, botón negro `IR AL CHECKOUT`).
6. **Contenido Principal (Layout 60% / 40%):**
   - **Columna Izquierda (60%):** `Registro Histórico` (`Compras Anteriores y Pedidos`), tag `5 PEDIDOS COMPLETADOS`. Tarjetas de pedidos con imagen, boutique de origen, descripción de prenda, talla, precio (`890 €`), fecha, estado y botón `VER FACTURA DIGITAL`.
   - **Columna Derecha (40%):**
     - Enlaces de gestión: `Direcciones de entrega`, `Métodos de pago`, `Personal Shopper`, `Preferencias y Tallas`.
     - Tarjeta dorada de Cita Privada: `Prueba de Alta Costura Personalizada`, botón `AGENDAR CITA DE ATELIER →`.
     - Botón de cierre: `[ ↪ CERRAR SESIÓN SEGURA ]` con confirmación.
7. **Modal / Formulario Reactivo de Edición:**
   - Campos tipados: Nombres, Apellidos, Teléfono, Talla preferida, Suscripción a marketing (Selector de género excluido por regla de negocio).
   - Validaciones reactivas en tiempo real y microanimaciones de guardado.

### 3.2 Arquitectura Frontend (Angular Signals & Typed Forms)
- **Ruta:** `/perfil` y `/mi-cuenta` en `app.routes.ts` (con `AuthGuard` que verifica token en sesión).
- **Servicio:** `PerfilService` con Signals reactivas (`perfil`, `cargando`, `editando`, `guardando`, `mensajeFeedback`).
- **Componente Standalone:** `PerfilComponent` con `ChangeDetectionStrategy.OnPush` y `ChangeDetectorRef.markForCheck()`.
- **Sincronización:** `sincronizarSesionStorage(perfilActualizado)` actualiza `localStorage` y `sessionStorage`.

---

## 4. Bloque 3: Aplicación Móvil (`Ec-mobile` - Flutter 3.x + Dart)

### 4.1 Análisis de UI Fiel a Mockup Móvil (`media_1789842906245.png`)

1. **AppBar:** Identificador `FASHION STORE | PERFIL` con icono de notificaciones y bolsa con badge de conteo.
2. **Encabezado:** Titular `Mi Cuenta` y badge `• ATELIER VIP`.
3. **Tarjeta de Perfil:** Avatar con botón de cámara, identificador `SOCIO PRIVÉ #8402`, nombre de usuario y botón `Editar Información`.
4. **Métricas en 3 Columnas:** Visitas registradas (32), Boutiques frecuentadas (4) y Preferencia textil (100% Seda & Lana).
5. **Tarjetas Gemelas:** Accesos rápidos a Wishlist y Bolsa de compra.
6. **Pedidos Anteriores:** Tarjetas verticales con miniatura, boutique, fecha, importe y botón de factura digital.
7. **Menú de Opciones:** Direcciones de entrega, métodos de pago y personal shopper asignado con navegación interactiva.
8. **Botón Inferior:** `[ ↪ CERRAR SESIÓN SEGURA ]`.
9. **Barra de Navegación Inferior (BottomNavigationBar):** 4 pestañas (`INICIO`, `BUSCAR`, `CATÁLOGO`, `PERFIL`) con `PERFIL` activo.

### 4.2 Clean Architecture y Manejo de Estado BLoC
- **Ubicación:** `Ec-mobile/lib/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/`
- **Estados Sellados (`PerfilEstado`):** `PerfilInicial`, `PerfilCargando`, `PerfilCargado(perfil)`, `PerfilActualizando(perfilActual)`, `PerfilError(mensaje)`.
- **Eventos:** `CargarPerfil()`, `ActualizarPerfil(nuevosDatos)`, `CerrarSesion()`.
- **Integración de Autenticación:** Token dinámico inyectado desde `PantallaLogin` vía `alCompletarLoginConToken` hacia `PantallaPerfil(token: token)`, realizando consultas y mutaciones persistidas en Neon PostgreSQL.
