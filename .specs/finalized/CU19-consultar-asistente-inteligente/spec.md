# Especificación — CU19: Consultar Asistente Inteligente

> **Ajuste al código (2026-11-08):** timeout de Gemini de 6 s (no 3 s) y contexto de 3 productos y 2 sucursales
> (no 5 productos), tal como implementa `cu19_asistente_chatbot/servicio.py`. Promovida a `.specs/finalized/`.

## 1. Contexto y Objetivo

En `SI2-Parcial1.md` (sección 2.1.4.4 y 2.2), el caso de uso **CU19. Consultar asistente inteligente** permite al cliente o visitante de FashionStore interactuar con un chatbot o asistente virtual de estilismo y atención omnicanal en lenguaje natural (ej. *«¿Tienen vestidos plisados en Madrid?»*, *«¿Qué prendas de fiesta recomiendan para una gala?»*, *«¿Cuál es el horario de la boutique de Serrano?»*).

### Situación Actual
- **Backend (`Ec-backend`):** Existe un servicio preliminar `GeminiService` (`app/integrations/gemini_service.py`) usado exclusivamente para frases editoriales de CU18, pero **no existe** un router ni servicio de chatbot para procesar preguntas en lenguaje natural, responder con contexto de catálogo e inventario, ni persistir en la tabla `fashionstore.interacciones_chatbot`.
- **Frontend Web (`Ec-frontend`):** No existe componente de chatbot ni botón flotante de atención.
- **Móvil (`Ec-mobile`):** No existe pantalla ni widget de asistente de estilo en la app.

### Objetivo
Construir una solución omnicanal completa guiada por la regla **Cero datos inventados**:
1. El asistente comprende lenguaje natural y responde con tono editorial de alta costura ("Fashion Store").
2. Contextualiza sus respuestas con datos reales de PostgreSQL (`fashionstore.productos`, `fashionstore.sucursales`, `fashionstore.inventario_sucursal`).
3. Retorna referencias clickeables a prendas y sucursales reales del catálogo para una navegación fluida.
4. Persiste cada intercambio en `fashionstore.interacciones_chatbot` identificando el canal (`web` o `movil`) y asociando al cliente si está autenticado.
5. Cuenta con un **fallback determinista inteligente** a costo cero y sin latencia cuando la clave de Gemini no esté configurada o la API externa no responda en 6 segundos (timeout de `generar_respuesta_chat`).

---

## 2. Esquema de Base de Datos (Sin Migración)

La tabla ya existe en Neon PostgreSQL y no requiere ninguna migración de Alembic:

```sql
CREATE TABLE fashionstore.interacciones_chatbot (
    id_interaccion  BIGSERIAL PRIMARY KEY,
    id_cliente      BIGINT REFERENCES clientes(id_cliente), -- NULL si es visitante no autenticado
    mensaje_usuario TEXT NOT NULL,
    respuesta_ia    TEXT,
    canal           canal_origen NOT NULL, -- 'web', 'movil', 'sucursal'
    creado_en       TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

---

## 3. Contratos de la API REST

### 3.1 `POST /api/v1/asistente/chat`

Procesa un mensaje del usuario, consulta el motor de IA con contexto de catálogo y persiste la interacción.

- **Autenticación:** Opcional (`obtener_usuario_opcional`). Si el cliente envía token Bearer válido, se extrae y vincula su `id_cliente`. Si no envía token, se procesa como consulta de visitante con `id_cliente = None`.
- **Tags:** `["Asistente Inteligente"]`

#### Payload de Entrada (`MensajeChatbotIn`)
```json
{
  "mensaje": "¿Tienen blazers o abrigos disponibles en Madrid?",
  "canal": "web",
  "id_sucursal_preferida": 1
}
```
*Validaciones:*
- `mensaje`: String entre 2 y 1000 caracteres.
- `canal`: Enum `"web"` o `"movil"`.
- `id_sucursal_preferida`: Entero opcional para acotar recomendaciones de disponibilidad.

#### Respuesta `200 OK` (`RespuestaChatbotOut`)
```json
{
  "id_interaccion": 128,
  "respuesta": "En nuestra boutique Atelier Serrano (Madrid) disponemos de piezas distinguidas en paño noble y corte sastre que encajan a la perfección con lo que buscas.",
  "productos_sugeridos": [
    {
      "id_producto": 4,
      "nombre": "Blazer Sastrería Lana Virgen",
      "precio": "650.00",
      "categoria": "Sastrería",
      "imagen_url": "https://...",
      "disponible": true,
      "sucursal_nombre": "Atelier Serrano - Madrid"
    }
  ],
  "sucursales_sugeridas": [
    {
      "id_sucursal": 1,
      "nombre": "Atelier Serrano - Madrid",
      "direccion": "Calle Serrano 48",
      "horario": "09:00 - 20:00"
    }
  ],
  "sugerencias_rapidas": [
    "¿Qué tallas quedan disponibles?",
    "¿Puedo agendar una reserva para probármelo?",
    "Ver opciones en otros colores"
  ]
}
```

---

### 3.2 `GET /api/v1/asistente/historial`

Permite recuperar las interacciones recientes del cliente autenticado para dar continuidad a la conversación en Web y Móvil.

- **Autenticación:** Requiere JWT válido (`obtener_usuario_actual`).
- **Query params:** `limite: int = 15` (máximo 50).
- **Respuesta `200 OK`:** Lista de interacciones previas ordenadas cronológicamente (`creado_en ASC`).

```json
[
  {
    "id_interaccion": 120,
    "mensaje_usuario": "¿Cuáles son los horarios de atención?",
    "respuesta_ia": "Nuestras boutiques atienden de lunes a sábado de 09:00 a 20:00.",
    "canal": "web",
    "creado_en": "2026-11-07T06:15:00Z"
  }
]
```

---

## 4. Arquitectura del Motor de Asistencia y RAG

### 4.1 Inyección de Contexto Real (RAG Liviano en PostgreSQL)
Antes de invocar al modelo generativo:
1. El backend detecta términos clave de búsqueda (categorías como "vestido", "blazer", "abrigo", "pantalón", "seda", ciudades como "Madrid", "Santa Cruz", o acciones como "horario", "reserva", "talla").
2. Consulta en la base de datos hasta 3 productos coincidentes con stock positivo en `fashionstore.inventario_sucursal` (acotados a `id_sucursal_preferida` si llega).
3. Consulta hasta 2 sucursales coincidentes o activas en `fashionstore.sucursales`.
4. Construye el prompt inyectando estos datos reales.

### 4.2 System Prompt y Tono de Marca
- Rol: Asesor de alta costura y estilismo de **Fashion Store**.
- Reglas:
  - Nunca inventar precios, prendas ni tiendas inexistentes.
  - Tono refinado, educado, conciso (máximo 3 párrafos de lectura rápida).
  - Incluir recomendaciones sobre combinación de prendas, ocasión de uso o reserva en probador.

### 4.3 Fallback Determinista Inteligente
Si `IA_API_KEY` no está configurada o la llamada a Gemini excede el timeout de 6 segundos:
- El motor clasifica la intención mediante patrones léxicos (consulta de producto, consulta de sucursal/horario, reserva/probador, saludo/general).
- Genera una respuesta redactada con el mismo estilo editorial de lujo.
- Adjunta las tarjetas reales de productos y sucursales encontradas en la consulta de BD.
- **Resultado:** Disponibilidad del 100% de la funcionalidad sin depender de servicios externos.

---

## 5. Diseño de Interfaces (Frontend Web & Mobile)

### 5.1 Frontend Web (`Ec-frontend`)
- **Componente flotante global:** Botón discreto en la esquina inferior derecha con badge sutil, expandible a un panel de chat de lujo.
- **Panel de Chat:**
  - Encabezado con título "Asistente de Estilo Fashion Store", estado en línea y botón de cerrar/minimizar.
  - Historial de mensajes con burbujas diferenciadas (cliente a la derecha en tono acento/negro, asistente a la izquierda en fondo claro/neutro).
  - Tarjetas compactas horizontales de productos sugeridos con miniatura, nombre, precio y botón «Ver prenda» que navega con `RouterLink` a `/catalogo/:id`.
  - Píldoras de sugerencias rápidas ("¿Tienen vestidos de noche?", "¿Horarios en boutique?", "¿Cómo reservar?").
  - Formulario de entrada con `textarea` auto-ajustable y botón de enviar.

### 5.2 Aplicación Móvil (`Ec-mobile`)
- **Pantalla dedicada:** `PantallaAsistenteEstilo` accesible desde el BottomNavigationBar o la vista de catálogo.
- Burbujas con espaciado estricto `EspaciadoApp` y colores `ColoresApp`.
- Despliegue de tarjetas de productos sugeridos con imagen, precio y tap para abrir `PantallaDetalleProducto`.
- Chips de consulta rápida debajo del campo de texto.

