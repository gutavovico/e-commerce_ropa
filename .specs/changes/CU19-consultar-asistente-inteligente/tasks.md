# Tareas — CU19: Consultar Asistente Inteligente

## Bloque 1 — Backend (`Ec-backend`)

- [x] **T-BE-01:** Crear modelo `InteraccionChatbotORM` en `app/modules/catalogo/cu19_asistente_chatbot/modelos.py` mapeando `fashionstore.interacciones_chatbot`.
- [x] **T-BE-02:** Crear esquemas Pydantic `MensajeChatbotIn`, `ProductoChatbotOut`, `SucursalChatbotOut`, `RespuestaChatbotOut` e `InteraccionChatbotHistorialOut` en `esquemas.py`.
- [x] **T-BE-03:** Implementar `repositorio.py` con métodos para consultar prendas con existencias, sucursales y persistir la interacción en la BD.
- [x] **T-BE-04:** Implementar `servicio.py` con orquestación RAG, formateo de prompt para Google Gemini y fallback determinista inteligente con estilo de alta costura.
- [x] **T-BE-05:** Implementar `router.py` con `POST /api/v1/asistente/chat` y `GET /api/v1/asistente/historial` y registrarlo en `app/modules/catalogo/router.py`.
- [x] **T-BE-06:** Crear suite de pruebas exhaustiva en `tests/modules/catalogo/test_cu19_asistente.py` y verificar que pasen el 100% con `pytest` (505/505 pruebas pasando en total).

## Bloque 2 — Frontend Web (`Ec-frontend`)

- [x] **T-FE-01:** Crear DTOs de TypeScript en `src/app/modules/catalogo/cu19_asistente_chatbot/modelos/chatbot.dto.ts`.
- [x] **T-FE-02:** Implementar `chatbot.service.ts` con gestión de estado reactivo vía Signals (`mensajes`, `cargando`, `abierto`).
- [x] **T-FE-03:** Implementar el componente standalone `widget-chatbot.component.ts` y su plantilla HTML con botón flotante, burbujas de conversación, tarjetas interactivas de prendas con routerLink a `/productos/:id` y chips de preguntas frecuentes.
- [x] **T-FE-04:** Integrar el widget globalmente en la plantilla principal (`app.component.html`).
- [x] **T-FE-05:** Añadir pruebas unitarias en `widget-chatbot.component.spec.ts` y `chatbot.service.spec.ts` y verificar con `npm test -- --watch=false` (562/562 tests pasados) y `npm run build` exitoso.

## Bloque 3 — Móvil (`Ec-mobile`)

- [x] **T-MO-01:** Crear modelos DTO y fuente de datos `chatbot_api.dart` en `lib/src/modulos/catalogo/cu19_asistente_chatbot/datos/`.
- [x] **T-MO-02:** Implementar `chatbot_bloc.dart` con `ChangeNotifier` para manejar el flujo de mensajes, estados de carga y errores de red.
- [x] **T-MO-03:** Construir la pantalla `pantalla_asistente_estilo.dart` con tokens `AppSpacing` y `AppColors`, lista de mensajes, tarjetas interactivas de productos y chips rápidos.
- [x] **T-MO-04:** Añadir FloatingActionButton de acceso al asistente en `PantallaPrincipalHub` de la app.
- [x] **T-MO-05:** Crear pruebas unitarias y de widget en `test/cu19_asistente_test.dart` y verificar con `flutter test` (230/230 tests pasados) y `flutter analyze` (0 errores).
