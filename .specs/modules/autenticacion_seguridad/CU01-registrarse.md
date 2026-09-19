# Especificación Permanente: CU01 - Registrarse (Baseline del Sistema)

**Código:** CU01  
**Nombre:** Registrarse (Auto-registro de Clientes y Emisión de Token)  
**Paquete de Dominio:** `autenticacion_seguridad`  
**Directorio Funcional:** `app/modules/autenticacion_seguridad/cu01_registrarse`  
**Actores:** Cliente (Iniciador / No autenticado)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Baseline Promovido a Permanente)  
**Estado:** 🟢 Aprobado, Implementado y Verificado (15/15 Backend, 7/7 Mobile, Web Compilado, Neon DB Sincronizada)

---

## 1. Descripción y Propósito

Permite a un usuario no registrado crear de manera autónoma una cuenta de tipo `cliente` en la plataforma omnicanal **FashionStore**. 

El proceso es transaccional y atómico:
1. Valida la unicidad y formato del correo electrónico normalizado.
2. Cifra la contraseña mediante el algoritmo criptográfico **Argon2id**.
3. Inserta simultáneamente la entidad base en `fashionstore.usuarios` y el perfil extendido en `fashionstore.clientes`.
4. Emite inmediatamente un token de acceso **JWT (HS256)** para que el cliente inicie sesión de forma transparente sin requerir un login secundario.

---

## 2. Experiencia de Usuario y Especificación Visual (Haute Couture)

El diseño responde a una estética *Light Luxury / Alta Costura*, adaptada de forma omnicanal:

### A. Vista Desktop / Web (Split Screen 50/50 - Angular)
- **Panel Izquierdo Editorial (50%):** Fotografía inmersiva de atelier de sastrería, overlay oscuro degradado, titular *"La pureza del corte. El lujo del tiempo."*, y bloques informativos de *"ACCESO PRIVADO"* y *"ATELIER CONCIERGE"*.
- **Panel Derecho Formulario (50%):** Superficie blanca pura `#FFFFFF`, badge superior `[🔒 REGISTRO CIFRADO]`, marca expandida *"FASHION STORE - HAUTE COUTURE & READY-TO-WEAR"*.
- **Campo Unificado `NOMBRE COMPLETO`:** Campo único en UI que se desglosa automáticamente en `nombres` y `apellidos` al enviarse al backend.
- **Medidor de Fortaleza de Contraseña:** Componente reactivo de 4 segmentos (`1/4 Débil`, `2/4 Media`, `3/4 ROBUSTA`, `4/4 EXCELENTE`).
- **Checkboxes de Alta Costura:** Aceptación obligatoria de Términos y Privacidad, y suscripción opcional a comunicaciones exclusivas.
- **Botón Obsidian Black:** Botón primario negro `#000000` con texto expandido `CREAR CUENTA →` y microinteracción de carga.

### B. Vista Mobile (Hero Card Vertical - Flutter)
- **Tarjeta Hero Superior:** Esquinas redondeadas (radio 16px), imagen de boutique con mockup AR superpuesto, badge translúcido con icono de candado y leyendas *"REGISTRO PRIVADO"* y *"«La pureza del corte. El lujo del tiempo.»"*.
- **Controles Estilizados:** Inputs con fondo `#F5F5F5`, iconos de línea vectoriales (`person_outline`, `mail_outline`, `lock_outline`), alternancia de visibilidad de contraseña y medidor dinámico en 4 barras horizontales.
- **Píldora de Confianza Inferior:** Badge centrado `256-BIT SSL SECURED • PRIVACIDAD GARANTIZADA`.

---

## 3. Contrato de API REST

### `POST /api/v1/autenticacion/registrarse`

Endpoint público sin requerimiento de autenticación previa.

#### Cabeceras de Solicitud
```http
Content-Type: application/json
Accept: application/json
```

#### Esquema de Entrada: `RegistroClienteIn`
| Campo | Tipo | Requerido | Restricciones / Reglas |
|---|---|---|---|
| `email` | `EmailStr` | Sí | Formato RFC 5322 válido. Se normaliza a minúsculas y sin espacios. |
| `password` | `str` | Sí | Mínimo 8 caracteres, máximo 128 caracteres. |
| `nombres` | `str` | Sí | Longitud 1 a 100 caracteres. No puede estar vacío. |
| `apellidos` | `str` | Sí | Longitud 1 a 100 caracteres. No puede estar vacío. |
| `telefono` | `str` | No | Máximo 30 caracteres. |
| `fecha_nacimiento` | `date` | No | Fecha en formato ISO-8601 (`YYYY-MM-DD`). |
| `genero` | `str` | No | Opciones: `femenino`, `masculino`, `no_binario`, `prefiero_no_decir`. |
| `talla_preferida` | `str` | No | Opciones: `XS`, `S`, `M`, `L`, `XL`, `XXL`. |
| `ciudad_preferida` | `int` | No | Referencia a `fashionstore.ciudades(id_ciudad)`. |
| `acepta_marketing` | `bool` | No | Valor por defecto: `true`. |

#### Ejemplo de Carga Útil (Payload)
```json
{
  "email": "camille.laurent@atelier-mode.fr",
  "password": "PasswordSeguro123!",
  "nombres": "Camille",
  "apellidos": "Laurent",
  "telefono": "+591 70012345",
  "talla_preferida": "M",
  "acepta_marketing": true
}
```

#### Respuestas HTTP y Códigos de Estado

##### `201 Created` — Registro Exitoso
Retorna la entidad creada junto con el token de acceso JWT.
```json
{
  "id_usuario": 1,
  "email": "camille.laurent@atelier-mode.fr",
  "nombres": "Camille",
  "apellidos": "Laurent",
  "rol": "cliente",
  "token_acceso": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "tipo_token": "bearer"
}
```

##### `409 Conflict` — Correo Electrónico Duplicado
Se produce cuando el correo ya existe en `fashionstore.usuarios`.
```json
{
  "detail": "El correo electronico ya se encuentra registrado en la plataforma.",
  "code": "USUARIO_YA_EXISTE"
}
```

##### `422 Unprocessable Entity` — Error de Validación de Entrada
Se produce si los campos requeridos faltan, el formato de correo es incorrecto o la clave tiene menos de 8 caracteres.
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "String should have at least 8 characters",
      "type": "string_too_short"
    }
  ]
}
```

---

## 4. Modelo de Datos y Persistencia (PostgreSQL / Neon)

Las entidades se encuentran alojadas en el esquema `fashionstore`:

```
┌────────────────────────────────────────────────────────┐
│               fashionstore.usuarios                    │
├────────────────────────────────────────────────────────┤
│ id_usuario     : BIGSERIAL PRIMARY KEY                 │
│ email          : CITEXT UNIQUE NOT NULL                │
│ password_hash  : VARCHAR(255) NOT NULL (Argon2id)      │
│ nombres        : VARCHAR(100) NOT NULL                 │
│ apellidos      : VARCHAR(100) NOT NULL                 │
│ telefono       : VARCHAR(30) NULL                      │
│ rol            : fashionstore.rol_usuario = 'cliente'  │
│ id_sucursal    : INTEGER NULL                          │
│ activo         : BOOLEAN NOT NULL DEFAULT TRUE         │
│ fecha_registro : TIMESTAMPTZ NOT NULL DEFAULT now()    │
│ ultimo_acceso  : TIMESTAMPTZ NULL                      │
└───────────────────────────┬────────────────────────────┘
                            │ 1:1 (ON DELETE CASCADE)
┌───────────────────────────▼────────────────────────────┐
│               fashionstore.clientes                    │
├────────────────────────────────────────────────────────┤
│ id_cliente       : BIGINT PRIMARY KEY (FK usuarios)    │
│ fecha_nacimiento : DATE NULL                           │
│ genero           : VARCHAR(20) NULL                    │
│ talla_preferida  : VARCHAR(10) NULL                    │
│ ciudad_preferida : INTEGER NULL (FK ciudades)          │
│ acepta_marketing : BOOLEAN NOT NULL DEFAULT TRUE       │
└────────────────────────────────────────────────────────┘
```

### Reglas Técnicas de Persistencia
1. **Tipos Enumerados:** La columna `usuarios.rol` utiliza el tipo ENUM nativo de PostgreSQL `fashionstore.rol_usuario ('cliente', 'administrador', 'encargado_sucursal', 'cajero', 'proveedor')`. En SQLAlchemy está mapeada explícitamente con `create_type=False` para evitar discordancias de tipos `character varying`.
2. **Atomicidad:** `db.flush()` obtiene el `id_usuario` generado e inserta inmediatamente el registro subordinado en `fashionstore.clientes`. Se realiza `commit` en una única transacción de base de datos.
3. **Seguridad:** El `password_hash` nunca se expone en los esquemas de salida (`RegistroClienteOut`).

---

## 5. Criterios de Aceptación (Gherkin BDD)

```gherkin
Característica: CU01 - Registro de Clientes en FashionStore
  Como usuario visitante no registrado
  Quiero registrar una nueva cuenta de cliente
  Para acceder al catálogo exclusivo, reservas de prendas y realizar compras en línea

  Escenario: Registro exitoso con emisión inmediata de JWT
    Dado que el usuario envía un correo "cliente.nuevo@fashionstore.com" que no existe en el sistema
    Y una contraseña de 8 o más caracteres "Segura123!"
    Y su nombre completo "Ana García"
    Cuando se procesa la solicitud en "POST /api/v1/autenticacion/registrarse"
    Entonces el backend responde con código HTTP 201 Created
    Y crea un registro en "fashionstore.usuarios" con rol "cliente"
    Y crea un registro subordinado en "fashionstore.clientes" con el mismo ID
    Y la respuesta incluye "token_acceso" firmado con HS256 y "tipo_token" igual a "bearer".

  Escenario: Intento de registro con correo duplicado
    Dado que el correo "existente@fashionstore.com" ya está registrado en "fashionstore.usuarios"
    Cuando un usuario intenta registrarse con ese mismo correo
    Entonces el backend responde con código HTTP 409 Conflict
    Y el cuerpo JSON contiene "code": "USUARIO_YA_EXISTE".

  Escenario: Validación de entrada - Contraseña demasiado corta
    Dado que el usuario ingresa una contraseña con menos de 8 caracteres
    Cuando se envía la solicitud
    Entonces el backend responde con código HTTP 422 Unprocessable Entity
    Y ninguna fila es insertada en la base de datos.

  Escenario: Desglose automático de Nombre Completo en clientes Web/Móvil
    Dado que el formulario web o móvil unifica el input a "Camille Laurent"
    Cuando el cliente envía el formulario
    Entonces el cliente divide la cadena en nombres: "Camille" y apellidos: "Laurent"
    Cumpliendo el contrato del payload de la API.

  Escenario: Medidor visual reactivo de fortaleza
    Dado que el usuario teclea su contraseña en el formulario
    Cuando la clave supera 8 caracteres y combina números y letras
    Entonces la interfaz ilumina dinámicamente 3 de las 4 barras del medidor
    Y muestra la etiqueta "3/4 ROBUSTA".
```

---

## 6. Verificación y Evidencia de Cumplimiento

| Componente | Métrica / Comando | Resultado | Estado |
|---|---|---|---|
| **Backend API** | `pytest tests/ -v` | 15 pasados, 0 fallidos | 🟢 Verde |
| **Mobile App** | `flutter analyze` & `flutter test` | 0 issues, 7/7 tests OK | 🟢 Verde |
| **Frontend Web** | `npm run build` | Compilación exitosa, 0 errores | 🟢 Verde |
| **Neon Database** | `alembic current` | Conectado a Postgres/Neon (versión `0001 head`) | 🟢 Sincronizado |
| **Endpoint Real** | `POST /api/v1/autenticacion/registrarse` | Retorna `201 Created` con JWT | 🟢 Operativo |
