# Especificación Técnica Permanente: CU10 - Utilizar vestidor virtual

**Código:** CU10
**Paquete de Dominio:** `catalogo`
**Backend:** `app/modules/catalogo/cu10_vestidor_virtual/` · `app/integrations/decart_service.py`
**Frontend:** `src/app/modules/catalogo/cu10_vestidor_virtual/`
**Mobile:** `lib/src/modulos/catalogo/cu10_vestidor_virtual/` · `assets/vestidor/decart_vton.html`
**Actor:** Cliente autenticado
**Estado:** Aprobado y promovido a permanente (2026-11-08)
**Historial del cambio:** `.specs/finalized/CU10-utilizar-vestidor-virtual/` · `CHANGELOG.md` defectos 46, 47 y 48

---

## 1. Dos motores, en orden de prioridad

| Motor | Web | Móvil | Coste |
| :--- | :--- | :--- | :--- |
| **1 · Local** (por defecto, destino de todo fallback) | Cámara + PNG de la prenda superpuesto, ajuste manual de tamaño y altura (sin seguimiento corporal, por decisión del usuario) | Cámara frontal + `google_mlkit_pose_detection`: la prenda se ancla a la línea de hombros (posición, escala y giro suavizados) | Cero; el vídeo no sale del dispositivo |
| **2 · Realista** (opcional) | `@decartai/sdk` (Lucy VTON 3.6) en la página | WebView con `@decartai/sdk@0.2.14` desde jsDelivr | Decart, por segundo de generación |

## 2. Contratos

### `POST /api/v1/vestidor/token[?canal=web|movil]`
Sin cuerpo; JWT obligatorio. Devuelve `{token, expira_en_segundos, servicio}`. Token efímero (60 s), `allowedModels: ["lucy-vton-3.6"]`, `maxSessionDuration: 60`.
- `canal=web` (por defecto): `allowedOrigins` = `CORS_ORIGINS`.
- `canal=movil`: sin `allowedOrigins` (el WebView carga la página como `file://`, Origin `null`).
- `503` si Decart no está configurado, no responde o no tiene créditos → fallback al Motor 1. Timeout de emisión: 10 s.

### `POST /api/v1/vestidor/sesion` → 201
`{id_producto, dispositivo, motor: 'local'|'ia', duracion_segundos, resultado_url?, genero_interes}`. Exige `productos.modelo_ar_url` (`422 SIN_MODELO_AR`). Una sola sesión por apertura del vestidor; `motor = ia` si Decart llegó a emitir vídeo; `genero_interes = true` al añadir a la bolsa desde el vestidor.

### `PATCH /api/v1/vestidor/sesion/{id_sesion_ar}`
Actualiza `resultado_url` o `genero_interes`.

## 3. Reglas

1. **Imagen de referencia:** la prenda sola (`modelo_ar_url`, PNG transparente), aplanada sobre blanco y en JPEG; nunca la foto de catálogo con una modelo vistiéndola. Mínimo recomendado 512 px.
2. **Prompt:** patrón de Decart «Substitute the current … with the … shown in the reference image» / «Add the jacket …» según el tipo de prenda (nombre, luego categoría).
3. **Token por marcación:** `apiKeyProvider`; el primer token es el ya emitido y cada reintento pide otro.
4. **Tiempos:** chequeo de conectividad previo (≤ 5 s, `critical` → fallback inmediato); 45 s sin vídeo → fallback; 60 s de modo realista → vuelta al Motor 1 (control de costes, independiente de la vida del token).
5. **Sesiones huérfanas:** una conexión que resuelve tras cancelar, cerrar o agotar el tiempo se desconecta al instante.
6. **Plataformas:** el vestidor móvil solo existe en Android e iOS (iOS ≥ 15.5); en web/escritorio la app avisa y no lo abre.
7. **Recursos relativos:** `/ar/...` se resuelve contra el frontend (`WEB_URL` en móvil) y `/static/...` contra el backend; nada más se reescribe.

## 4. Configuración que no debe perderse

- `angular.json`: asset `frame-metadata-worker.js` de `@decartai/sdk` a la raíz y `serve.options.prebundle.exclude: ["@decartai/sdk"]`. Sin ellos LiveKit no envía fotogramas (defecto 46).
- `render.yaml`: `DECART_API_KEY` (`sync: false`, valor en el panel de Render) y el dominio real del frontend en `CORS_ORIGINS`.
- Móvil: permiso `CAMERA` (Android), `NSCameraUsageDescription` e `IPHONEOS_DEPLOYMENT_TARGET = 15.5` (iOS).
