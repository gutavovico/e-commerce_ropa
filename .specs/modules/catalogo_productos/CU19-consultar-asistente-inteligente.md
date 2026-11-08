# Especificación Técnica Permanente: CU19 — Consultar Asistente Inteligente

**Código:** CU19
**Paquete de Dominio:** `catalogo`
**Backend:** `app/modules/catalogo/cu19_asistente_chatbot/` · `app/integrations/gemini_service.py`
**Frontend:** `src/app/modules/catalogo/cu19_asistente_chatbot/` (widget flotante)
**Mobile:** `lib/src/modulos/catalogo/cu19_asistente_chatbot/` (`PantallaAsistenteEstilo`)
**Actores:** Cliente autenticado o visitante
**Estado:** Aprobado y promovido a permanente (2026-11-08)
**Historial del cambio:** `.specs/finalized/CU19-consultar-asistente-inteligente/` · `CHANGELOG.md` defecto 51

---

## 1. Contratos

### `POST /api/v1/asistente/chat` (JWT opcional)
Entrada `{mensaje (2–1000), canal: "web"|"movil", id_sucursal_preferida?}`.
Salida `{id_interaccion, respuesta, productos_sugeridos[] {id_producto, nombre, precio, categoria, imagen_url, disponible, sucursal_nombre}, sucursales_sugeridas[] {id_sucursal, nombre, direccion, horario}, sugerencias_rapidas[]}`.
Con token se vincula el `id_cliente`; sin él, la consulta es de visitante (`id_cliente = NULL`).

### `GET /api/v1/asistente/historial?limite=15` (JWT obligatorio, 1–50)
Interacciones previas del cliente en orden cronológico: `{id_interaccion, mensaje_usuario, respuesta_ia, canal, creado_en}`.

## 2. Reglas

- **Contexto real (RAG ligero):** antes de llamar al modelo se buscan hasta **3 productos** con stock positivo (acotados a `id_sucursal_preferida` si llega) y hasta **2 sucursales** que coincidan con el mensaje; solo esos datos entran en el prompt. Nunca se inventan prendas, precios ni tiendas.
- **Tono:** asesor de alta costura de «FASHION STORE», conciso (máximo 3 párrafos).
- **Fallback determinista:** sin `IA_API_KEY` o si Gemini no responde en **6 s**, se clasifica la intención por patrones (producto, sucursal u horario, reserva, saludo) y se responde con el mismo estilo y las tarjetas reales encontradas. `GeminiService(api_key="")` fuerza el fallback; solo `None` toma la clave de la configuración (defecto 51).
- Cada intercambio se persiste en `fashionstore.interacciones_chatbot` con su canal.
