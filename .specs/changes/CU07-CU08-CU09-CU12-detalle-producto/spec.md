# Especificación Técnica Formal: Detalle de Producto, Variantes, Disponibilidad y Reservas

**Casos de Uso Integrados:**
1. **CU07** - Consultar Detalle de Producto
2. **CU08** - Consultar Tallas, Colores y Características
3. **CU09** - Consultar Disponibilidad por Sucursal
4. **CU12** - Reservar Prendas (Cita de Prueba Presencial en Boutique)
5. **CU10 (Diferido / Aislado)** - Utilizar Vestidor Virtual (AR): Maquetación del CTA interactivo sin lógica 3D ni cámara.

**Paquetes de Dominio:** `catalogo_productos` / `reservas`  
**Directorio Funcional:** `cu07_cu08_cu09_cu12_detalle_producto`  
**Actores:** Cliente (Registrado y Visitante Anónimo para consulta; Cliente Registrado para Reserva CU12)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Propuesta de Cambio Inicial)  
**Estado:** 🟡 EN FASE DE ESPECIFICACIÓN Y PLANIFICACIÓN (Gate de Aprobación Activo)  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1_terminado.pdf` (Líneas 975-1025: CU07, CU08, CU09, CU12, tablas `productos`, `variantes_producto`, `tallas`, `colores`, `inventario_sucursal`, `sucursales`, `reservas`, `reserva_detalle`, `movimientos_inventario`).
- Referencia Visual y UX Mobile: `image_2e3062.png` (AppBar con botón `← VOLVER` y wishlist, galería con indicador `1/4`, botón flotante *"PROBAR EN AR"*, 4 miniaturas, ficha técnica, 4 selectores circulares de color, botones de talla con estado deshabilitado, acordeón de composición textil noble, acordeón de disponibilidad con botón directo *"RESERVAR EN ESTA BOUTIQUE"* y barra inferior con botón *"AÑADIR A LA BOLSA"*).
- Referencia Visual y UX Web: `image_2e2d7e.png` (Cabecera ligera con `← VOLVER` y breadcrumbs, layout 2 columnas, galería con 4 tomas rotuladas, bloque morfológico *"INICIAR PROBADOR INTERACTIVO"*, selector de color con acabado artesanal, botones de talla, stock multisede en tiempo real, CTA *"AÑADIR A LA BOLSA"* y *"CITA DE PRUEBA BOUTIQUE"*, recomendaciones "Completa el look atelier") e `image_2e295b.png` (Modal interactivo *"RESERVAR CITA DE PRUEBA EN BOUTIQUE"* con tarjeta de prenda, selector de boutique con badges de stock, franja horaria y botón de confirmación).
- Directriz Arquitectónica Global: Jerarquía de Vistas (Hub-and-Spoke) ([`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/architecture/directriz-navegacion-hub-and-spoke.md)).
- Design System: Tipografía corporativa `Outfit`, paleta textil Obsidian/Camel/Marfil de `fashionstore-tokens.md`, y catálogo estrictamente femenino.

---

## 1. Especificación Formal por Caso de Uso

### 1.1 CU07: Consultar Detalle de Producto

#### 1.1.1 Propósito y Reglas de Negocio
- Permitir a cualquier usuario visualizar la ficha técnica completa de una prenda de alta costura, incluyendo su nombre, subtítulo de atelier, línea editorial, precio base, precio con descuento (si cuenta con promoción activa), desglose de ahorro, cuotas de financiación (*Atelier Pay*), calificación de atelier, descripción poética y galería de tomas fotográficas de alta resolución.
- **Regla Femenina Inquebrantable:** Todas las prendas, descripciones, tallas y fotografías corresponden estrictamente al guardarropa femenino. Cero indumentaria ni modelos masculinos.
- **Galería Editorial Multi-Ángulo:** La prenda cuenta con una lista de imágenes de alta fidelidad que cubren al menos cuatro perspectivas: *Frontal*, *Textura Tejido*, *Espalda* y *Detalle Costura*.
- **Trazabilidad Textil Noble:** Se expone la composición detallada:
  - Cuerpo Principal (ej. *100% Seda Natural 22 Momme*).
  - Forro Interior (ej. *Crepé de seda puro transpirable*).
  - Técnica Textil (ej. *Plisado artesanal al vapor de Lyon*).
  - Instrucciones de cuidado y sostenibilidad (*Limpieza profesional*, *Vapor vertical*, *Almacenamiento en funda transpirable*).
- **Recomendaciones "Completa el Look Atelier":** Retorna hasta 3 prendas complementarias activas de la misma colección o temporada para sugerir un estilismo integral.

#### 1.1.2 Contrato de API REST
- **Ruta:** `GET /api/v1/productos/{id_producto}`
- **Método:** `GET`
- **Autenticación:** Pública (opcional `Authorization: Bearer <token>` para asociar estado de favorito).
- **Parámetros Path:** `id_producto: int` (ID de la prenda).
- **Respuestas:**
  - `200 OK`: `ProductoDetalleOut` con todos los metadatos descriptivos, precios, variantes, galería y recomendaciones.
  - `404 Not Found`: Prenda no encontrada o inactiva (`activo = false`).

---

### 1.2 CU08: Consultar Tallas, Colores y Características

#### 1.2.1 Propósito y Reglas de Negocio
- Exponer de forma estructurada todas las variantes comerciales existentes para la prenda consultada, cruzando `variantes_producto`, `tallas` y `colores`.
- **Selector Cromático:** Lista de colores únicos disponibles para el producto (`id_color`, `nombre`, `codigo_hex`), indicando si tienen stock disponible en al menos una talla.
- **Selector de Tallas Normalizadas (FR / ES):** Lista de tallas (`34`, `36`, `38`, `40`, `42`) ordenadas por `tallas.orden`. Para el color seleccionado, cada talla indica:
  - `disponible: bool` (true si `cantidad_disponible > 0` en alguna sucursal).
  - `stock_total: int` (suma de unidades disponibles en la red de boutiques).
  - Si una talla no tiene existencias, se visualiza en cliente como deshabilitada con tachado diagonal.
- **SKU Dinámico y Precio:** Al cambiar la combinación de talla y color, el cliente actualiza reactivamente el `sku` (ej. `ATEL-2025-VD9-38-MAR`) y el precio final (considerando posibles `precio_extra` de variante y promociones aplicables).

#### 1.2.2 Estructura de Datos en `ProductoDetalleOut`
Cada variante expone:
- `id_variante: int`
- `sku: str`
- `id_talla: int`, `talla_codigo: str`, `talla_orden: int`
- `id_color: int`, `color_nombre: str`, `color_hex: str`
- `precio_extra: Decimal`
- `precio_final_variante: Decimal`
- `stock_total_disponible: int`
- `tiene_stock: bool`

---

### 1.3 CU09: Consultar Disponibilidad por Sucursal

#### 1.3.1 Propósito y Reglas de Negocio
- Permitir al cliente consultar en tiempo real las existencias físicas de una variante específica (o de la variante seleccionada) en cada boutique insignia de la cadena.
- **Agrupación y Metadatos de Boutique:**
  - `id_sucursal: int`
  - `nombre: str` (ej. *Flagship Serrano (Madrid)*, *Boutique Saint-Honoré (París)*, *Madrid Central Atelier Hub*).
  - `ciudad: str` (*Madrid*, *París*).
  - `direccion: str` (ej. *Calle de Serrano 44, Salamanca*).
  - `horario_apertura: str`, `horario_cierre: str`.
  - `cantidad_disponible: int`, `cantidad_reservada: int`.
  - `estado_stock: str` (*disponible*, *ultimas_unidades*, *agotada*).
  - `badge_texto: str` (ej. *"2 UDS EN STOCK"*, *"1 UD EN STOCK"*, *"CITA CON SASTRE JEFE"*).
  - `citas_disponibles_texto: str` (ej. *"Citas de prueba disponibles hoy y mañana"*).
- **Regla de Negocio:** Una sucursal con `cantidad_disponible > 0` permite la reserva presencial inmediata (CU12). Si `cantidad_disponible == 0`, no admite reservas presenciales directas para esa variante.

#### 1.3.2 Contrato de API REST
- **Ruta:** `GET /api/v1/productos/{id_producto}/disponibilidad`
- **Método:** `GET`
- **Parámetros Query:** `id_variante: Optional[int] = None` (si es nulo, toma la variante por defecto o consolida por sucursal).
- **Respuestas:**
  - `200 OK`: `DisponibilidadSucursalesOut` con la lista de sucursales, existencias y estados.
  - `404 Not Found`: Producto o variante inexistente.

---

### 1.4 CU12: Reservar Prendas (Cita de Prueba Presencial en Boutique)

#### 1.4.1 Propósito y Reglas de Negocio
- Proporcionar a los clientes el servicio exclusivo de reservar una o más prendas para una cita privada de prueba presencial (*Fitting VIP*) en una boutique insignia seleccionada.
- **Autenticación Requerida:** Requiere sesión iniciada de cliente (`id_usuario` registrado). Si un visitante anónimo pulsa reservar, el sistema preserva la intención y solicita iniciar sesión.
- **Validación de Horario Comercial:**
  - La fecha y hora de atención (`fecha_hora_atencion`) debe ser futura (`> now()`).
  - Debe encontrarse dentro del rango comercial de la sucursal (`horario_apertura <= hora <= horario_cierre`).
- **Transacción Atómica de Inventario (Reglas de Oro SDD):**
  En una **única transacción de base de datos**:
  1. Se verifica con bloqueo optimista/pesimista que la sucursal cuente con existencias: `cantidad_disponible >= cantidad_solicitada`.
  2. Se descuenta el stock disponible: `cantidad_disponible = cantidad_disponible - cantidad`.
  3. Se incrementa el stock reservado: `cantidad_reservada = cantidad_reservada + cantidad`.
  4. El trigger de BD `trg_inventario_estado` recalcula automáticamente el `estado` (`reservada` o `agotada` si disponible llega a 0).
  5. Se inserta el registro en `fashionstore.reservas`:
     - `estado = 'pendiente'`
     - `canal_origen = 'web'` o `'movil'`
     - `fecha_hora_atencion = fecha_hora_seleccionada`
  6. Se insertan los renglones en `fashionstore.reserva_detalle` vinculando `id_variante` y `cantidad`.
  7. Se registra el movimiento de auditoría en `fashionstore.movimientos_inventario`:
     - `tipo_movimiento = 'reserva'`
     - `cantidad = cantidad`
     - `referencia_documento = 'RESERVA-' + str(id_reserva)`
     - `observacion = 'Reserva de cita privada de fitting en boutique'`
- **Regla de Conflicto (409 Conflict):** Si en el momento de confirmar la cita otra cliente reservó la última unidad disponible, la transacción revierte y responde `409 Conflict` con mensaje claro de agotado.

#### 1.4.2 Contrato de API REST
- **Ruta:** `POST /api/v1/reservas`
- **Método:** `POST`
- **Autenticación:** Obligatoria (`Bearer <token>`).
- **Cuerpo de Petición (`ReservaCrearIn`):**
  ```json
  {
    "id_sucursal": 1,
    "fecha_hora_atencion": "2026-09-22T11:30:00Z",
    "canal_origen": "web",
    "observacion": "Cita de prueba privada para fitting de seda marfil",
    "items": [
      {
        "id_variante": 5,
        "cantidad": 1
      }
    ]
  }
  ```
- **Códigos de Respuesta:**
  - `201 Created`: `ReservaCreadaOut` con `id_reserva`, `codigo_confirmacion`, `nombre_sucursal`, `fecha_hora_atencion`, `estado: "pendiente"` y mensaje de cortesía atelier.
  - `400 Bad Request`: Horario fuera de rango comercial o fecha pasada.
  - `401 Unauthorized`: Token no proporcionado o inválido.
  - `404 Not Found`: Sucursal o variante no encontrada.
  - `409 Conflict`: Stock insuficiente en la sucursal seleccionada.

---

### 1.5 CU10: Vestidor Virtual AR (Aislamiento Visual)
- **Alcance Estricto:** Exclusivamente maquetación del componente visual de acceso.
- **Mobile (`image_2e3062.png`):** Botón flotante estilizado `[ 👁 PROBAR EN AR ]` sobre la esquina inferior derecha de la fotografía principal e icono de escáner en la barra inferior. Emite aviso de cortesía *"Módulo de Probador Virtual AR en preparación para el próximo ciclo"*.
- **Web (`image_2e2d7e.png`):** Bloque interactivo *"SIMULADOR VESTIDOR VIRTUAL & ESCÁNER 3D"* bajo la galería, con simulación morfológica inteligente de talla, métricas técnicas de caída textil y botón `[ 👁 INICIAR PROBADOR INTERACTIVO ]` con diálogo informativo.
- **Sin dependencias pesadas ni procesamiento de cámara en este ciclo.**

---

## 2. Criterios de Aceptación (Gherkin)

```gherkin
Característica: Consulta de Detalle de Prenda de Alta Costura (CU07, CU08)

  Escenario: Consulta exitosa de prenda activa con variantes completas
    Dado que existe en base de datos el producto con id 1 y activo verdadero
    Cuando el cliente envía una petición GET a "/api/v1/productos/1"
    Entonces el código de respuesta debe ser 200 OK
    Y el cuerpo de respuesta debe incluir "nombre", "precio_base", "subtitulo_atelier"
    Y la lista de "variantes" debe contener al menos una talla y un color válidos
    Y debe incluir "composicion" con cuerpo principal y técnica textil

  Escenario: Consulta de producto inexistente o inactivo
    Dado que no existe ningún producto activo con id 99999
    Cuando el cliente envía una petición GET a "/api/v1/productos/99999"
    Entonces el código de respuesta debe ser 404 Not Found

Característica: Disponibilidad de Stock por Sucursal (CU09)

  Escenario: Consulta de disponibilidad multisede para una variante
    Dado que la variante con id 1 cuenta con 2 unidades en Flagship Serrano y 1 en Saint-Honoré
    Cuando el cliente envía una petición GET a "/api/v1/productos/1/disponibilidad?id_variante=1"
    Entonces el código de respuesta debe ser 200 OK
    Y debe listar las sucursales con su respectiva cantidad disponible y estado "disponible"

Característica: Reserva de Cita de Prueba Presencial en Boutique (CU12)

  Escenario: Reserva exitosa con decremento de inventario disponible y registro de movimiento
    Dado que la clienta está autenticada con token válido
    Y la sucursal 1 tiene 2 unidades disponibles de la variante 1
    Cuando la clienta envía una petición POST a "/api/v1/reservas" con:
      | id_sucursal          | 1                     |
      | fecha_hora_atencion  | 2026-09-22T11:30:00Z  |
      | canal_origen         | web                   |
      | items                | [{"id_variante": 1, "cantidad": 1}] |
    Entonces el código de respuesta debe ser 201 Created
    Y la sucursal 1 debe tener ahora 1 unidad disponible y 1 unidad reservada
    Y debe existir un movimiento de inventario con tipo "reserva" y referencia a la reserva creada

  Escenario: Conflicto por falta de existencias en boutique seleccionada
    Dado que la sucursal 1 tiene 0 unidades disponibles de la variante 2
    Cuando la clienta intenta reservar 1 unidad de la variante 2 en la sucursal 1
    Entonces el código de respuesta debe ser 409 Conflict
    Y no debe modificarse el inventario ni crearse la reserva
```
