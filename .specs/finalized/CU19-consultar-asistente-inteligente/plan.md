# Plan Técnico — CU19: Consultar Asistente Inteligente

## Estrategia por Bloques

Siguiendo la regla de trabajo de `CLAUDE.md`, la implementación se divide en 3 bloques independientes con compuerta de aprobación entre ellos:
1. **Bloque 1 — Backend (`Ec-backend`)**
2. **Bloque 2 — Frontend Web (`Ec-frontend`)**
3. **Bloque 3 — Móvil (`Ec-mobile`)**

---

## Bloque 1 — Backend (`Ec-backend`)

### Estructura de Archivos
Se creará el subpaquete `app/modules/catalogo/cu19_asistente_chatbot/`:
- `__init__.py`
- `modelos.py`: Entidad `InteraccionChatbotORM` mapeando fielmente `fashionstore.interacciones_chatbot` (`id_interaccion`, `id_cliente`, `mensaje_usuario`, `respuesta_ia`, `canal`, `creado_en`).
- `esquemas.py`:
  - `MensajeChatbotIn`: `mensaje: str`, `canal: Literal["web", "movil"]`, `id_sucursal_preferida: Optional[int]`.
  - `ProductoChatbotOut`: `id_producto`, `nombre`, `precio`, `categoria`, `imagen_url`, `disponible`.
  - `SucursalChatbotOut`: `id_sucursal`, `nombre`, `direccion`, `horario`.
  - `RespuestaChatbotOut`: `id_interaccion`, `respuesta`, `productos_sugeridos`, `sucursales_sugeridas`, `sugerencias_rapidas`.
  - `InteraccionChatbotHistorialOut`: Registro para el endpoint de historial.
- `repositorio.py`: `ChatbotRepositorio`:
  - `buscar_contexto_productos(db, consulta: str, id_sucursal: Optional[int]) -> list[ProductoORM]`: Extrae productos activos y variantes con stock positivo para alimentar el RAG.
  - `buscar_contexto_sucursales(db, consulta: str) -> list[SucursalORM]`: Extrae sucursales relevantes (por ciudad, nombre o todas las activas).
  - `guardar_interaccion(db, id_cliente: Optional[int], mensaje: str, respuesta: str, canal: str) -> InteraccionChatbotORM`.
  - `obtener_historial_cliente(db, id_cliente: int, limite: int) -> list[InteraccionChatbotORM]`.
- `servicio.py`: `ServicioAsistenteChatbot`:
  - Orquesta la extracción de contexto real de BD.
  - Llama a `GeminiService` formateando el prompt con instrucciones editoriales de lujo y catálogo verídico.
  - Si Gemini no responde o no hay API key, conmuta al **fallback determinista** (`_responder_fallback_contextual`) para devolver un mensaje coherente con las prendas y sucursales encontradas.
  - Persiste la interacción en la base de datos.
- `router.py`:
  - `POST /api/v1/asistente/chat`
  - `GET /api/v1/asistente/historial`
  - Registrar en `app/modules/catalogo/router.py`.

### Pruebas Backend
- `tests/modules/catalogo/test_cu19_asistente.py`:
  - Chat con consulta de producto (ej. "vestido"): verifica respuesta de texto, lista de productos sugeridos y persistencia en BD.
  - Chat con consulta de sucursal / horario: verifica sucursales sugeridas y horarios reales.
  - Chat anónimo (sin token JWT): verifica procesamiento correcto con `id_cliente = None`.
  - Chat autenticado (con Bearer token): verifica asociación con `id_cliente`.
  - Endpoint de historial `GET /asistente/historial`: verifica retorno ordenado de interacciones anteriores.
  - Fallback determinista: verifica respuesta válida sin arrojar excepciones aun con API key ausente o mock de error HTTP.

---

## Bloque 2 — Frontend Web (`Ec-frontend`)

### Archivos a Crear / Modificar
- `src/app/modules/catalogo/cu19_asistente_chatbot/modelos/chatbot.dto.ts`:
  - Interfaces TypeScript `MensajeChatbotIn`, `ProductoChatbotDto`, `SucursalChatbotDto`, `RespuestaChatbotDto`, `MensajeHistorialDto`.
- `src/app/modules/catalogo/cu19_asistente_chatbot/servicios/chatbot.service.ts`:
  - Servicio singleton con Signals: `mensajes$ = signal<MensajeConversacion[]>([])`, `cargando$ = signal<boolean>(false)`, `abierto$ = signal<boolean>(false)`.
  - Métodos: `enviarMensaje(texto: str)`, `cargarHistorial()`, `alternarChat()`, `limpiarConversacion()`.
- `src/app/modules/catalogo/cu19_asistente_chatbot/componentes/widget-chatbot.component.ts` (y `.html`):
  - Botón flotante estilizado en esquina inferior derecha.
  - Ventana flotante con micro-animaciones (apertura/cierre, scroll suave al último mensaje).
  - Tarjetas interactivas de producto con `[routerLink]="['/catalogo', producto.id_producto]"` que cierran el chat o permiten continuar navegando.
  - Botones de preguntas rápidas preconfiguradas.
- Integración en `src/app/app.component.html` (o `layout.component.html`) para disponibilidad omnicanal en toda la boutique.
- Pruebas unitarias en `widget-chatbot.component.spec.ts` y `chatbot.service.spec.ts`.

---

## Bloque 3 — Móvil (`Ec-mobile`)

### Archivos a Crear / Modificar
- `lib/src/modulos/catalogo/cu19_asistente_chatbot/datos/modelos/chatbot_dto.dart`:
  - Clases DTO con `fromJson` y `toJson` para `MensajeChatbotPeticion`, `RespuestaChatbotDto`, `ProductoChatbotDto`.
- `lib/src/modulos/catalogo/cu19_asistente_chatbot/datos/fuentes/chatbot_api.dart`:
  - Fuente HTTP que invoca `POST /api/v1/asistente/chat` y `GET /api/v1/asistente/historial`.
- `lib/src/modulos/catalogo/cu19_asistente_chatbot/presentacion/bloc/chatbot_bloc.dart`:
  - BLoC con estados `ChatbotInicial`, `ChatbotCargando`, `ChatbotListo`, `ChatbotError`.
- `lib/src/modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart`:
  - Interfaz de chat moderna y elegante acorde a la guía de estilo (`EspaciadoApp`, `ColoresApp`).
  - Tarjetas de prendas con navegación directa a `PantallaDetalleProducto`.
  - Chips de sugerencias rápidas.
- Enlace de acceso en la navegación de la app (e.g. en el AppBar de inicio o catálogo).
- Pruebas unitarias y de widgets en `test/modulos/cu19_asistente_test.dart`.

