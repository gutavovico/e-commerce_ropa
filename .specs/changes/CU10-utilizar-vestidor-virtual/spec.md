# Especificación — CU10: Utilizar Vestidor Virtual (Dos Motores: Local e IA Generativa Decart)

## 1. Contexto y Decisión Técnica

En `SI2-Parcial1.md` (secciones 1.1, 1.2, 1.4, 2.1.3, 2.2, 2.3, 2.4.1 y 2.5), el caso de uso **CU10. Utilizar vestidor virtual** permite al cliente autenticado visualizar interactivamente cómo luce una prenda de alta costura sobre su cuerpo en tiempo real a través de la cámara de su dispositivo móvil.

El vestidor virtual adopta una **arquitectura de dos motores en orden estricto de prioridad**:

### Motor 1 — Local (Principal, siempre disponible)
- **Tecnología:** App móvil Flutter con cámara en directo y detección de puntos clave corporales (hombros, torso, cadera) mediante el paquete oficial `google_mlkit_pose_detection`.
- **Renderizado 2D/3D:** La imagen 2D de la prenda (PNG con fondo transparente obtenida desde `productos.modelo_ar_url`) se escala, rota y deforma sobre el torso del cliente adaptándose anatómicamente a sus movimientos y postura.
- **Ventajas:** Procesamiento 100% en el dispositivo (Edge AI), latencia nula, costo cero de inferencia y máxima privacidad (el video de la cámara nunca sale del teléfono ni se envía a terceros).
- **Disponibilidad:** Es el motor por defecto y el flujo principal que garantiza disponibilidad continua aun sin conexión a servicios externos.

### Motor 2 — Realista con IA Generativa (Opcional, "Modo Realista")
- **Tecnología:** Servicio cloud de Decart ejecutando el modelo **Lucy VTON** en tiempo real a 720p. El cliente transmite el video de su cámara junto con la imagen de la prenda; el servicio devuelve el video con la prenda puesta, conservando el movimiento y la forma del cuerpo del cliente.
- **Seguridad de Credenciales:** La clave permanente de Decart reside exclusivamente en variables de entorno del backend FastAPI (`DECART_API_KEY`). El backend expone `POST /api/v1/vestidor/token` para entregar un token de cliente efímero (~60 s, como tiempo máximo para establecer la conexión con Decart) a la app autenticada.
- **Arquitectura en Flutter:** Al no existir SDK de Decart para Flutter, la app abre un `WebView` que carga una página web local/interna con el SDK de JavaScript (`@decartai/sdk`), pasando el token efímero y la URL de la prenda.
- **Costos y Duración:** Facturación por segundo de generación activa (Lucy VTON 720p: USD 0.02/s en modo estándar, USD 0.04/s en modo fast; cuentas nuevas reciben créditos de prueba a validar). Se impone una duración máxima de sesión realista de 60 segundos como regla de negocio para control de costos (independiente del token efímero de conexión).
- **Fallback Automático:** Si el Motor 2 falla (sin internet, créditos agotados, token rechazado, permisos denegados en el WebView o corte de streaming), el sistema conmuta automáticamente al Motor 1 (Local) con un aviso informativo y sin interrumpir la experiencia.

---

## 2. Esquema de Base de Datos

Tabla `fashionstore.sesiones_vestidor_virtual`:

```sql
CREATE TABLE fashionstore.sesiones_vestidor_virtual (
    id_sesion_ar        BIGSERIAL PRIMARY KEY,
    id_cliente          BIGINT NOT NULL REFERENCES fashionstore.clientes(id_cliente),
    id_producto         BIGINT NOT NULL REFERENCES fashionstore.productos(id_producto),
    dispositivo         VARCHAR(50), -- android / ios / web
    motor               VARCHAR(10) NOT NULL DEFAULT 'local' CHECK (motor IN ('local', 'ia')),
    duracion_segundos   INTEGER CHECK (duracion_segundos IS NULL OR duracion_segundos >= 0),
    fecha_hora          TIMESTAMPTZ NOT NULL DEFAULT now(),
    resultado_url       VARCHAR(500),
    genero_interes      BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX idx_ar_cliente ON fashionstore.sesiones_vestidor_virtual(id_cliente);
CREATE INDEX idx_ar_producto ON fashionstore.sesiones_vestidor_virtual(id_producto);
```

---

## 3. Contratos de la API REST

### 3.1 `POST /api/v1/vestidor/token` (Nuevo — Motor 2 Decart)

Genera un token de cliente temporal de Decart para el modo realista.

- **Autenticación:** Obligatoria (`obtener_usuario_actual` vía cabecera `Authorization: Bearer <jwt>`).
- **Cuerpo de la petición:** Sin cuerpo (solo cabecera `Authorization: Bearer <jwt>`). La app móvil obtiene la imagen de la prenda directamente del catálogo, no del endpoint de token.
- **Parámetro de consulta `canal`** (`web` por defecto | `movil`) — *delta del Bloque 3*: con `web` el token se restringe a los orígenes de `CORS_ORIGINS` (`allowedOrigins`); con `movil` se emite sin esa restricción, porque el WebView carga la página de Decart como asset local y su `Origin` es `null` (verificado: Decart responde «Origin not allowed», cierre 1008, a un token web desde `Origin: null`). El token móvil conserva vida de 60 s, `allowedModels: ["lucy-vton-3.6"]` y `maxSessionDuration: 60`. Cualquier otro valor → `422`.
- **Respuesta `200 OK`:**
```json
{
  "token": "decart_client_token_abc123xyz...",
  "expira_en_segundos": 60,
  "servicio": "decart_lucy_vton_720p"
}
```
- **Errores:**
  - `401 Unauthorized`: Usuario sin sesión activa.
  - `503 Service Unavailable`: Decart API no responde o saldo de créditos no disponible (provoca fallback en la app).

---

### 3.2 `POST /api/v1/vestidor/sesion` (Prueba 3 Actualizada)

Registra la sesión de prueba virtual en el vestidor.

- **Autenticación:** Obligatoria.
- **Código de éxito:** `201 Created`

#### Payload de Entrada (`SesionVestidorCrearIn`)
```json
{
  "id_producto": 42,
  "dispositivo": "android",
  "motor": "local",
  "duracion_segundos": 45,
  "resultado_url": "https://fashionstore.com/renders/ar_capture_845.jpg",
  "genero_interes": true
}
```

#### Respuesta `201 Created` (`SesionVestidorOut`)
```json
{
  "id_sesion_ar": 845,
  "id_cliente": 10,
  "id_producto": 42,
  "dispositivo": "android",
  "motor": "local",
  "duracion_segundos": 45,
  "fecha_hora": "2026-09-13T16:44:28Z",
  "resultado_url": "https://fashionstore.com/renders/ar_capture_845.jpg",
  "genero_interes": true
}
```

---

### 3.3 `PATCH /api/v1/vestidor/sesion/{id_sesion_ar}`

Actualiza el interés comercial (`genero_interes = true`) o captura generada tras añadir a la bolsa o agendar cita.

---

## 4. Requisitos No Funcionales y Reglas de Negocio

1. **Privacidad de Video:** Con el Motor 1 local, los fotogramas se procesan estrictamente en la memoria RAM del teléfono móvil y jamás salen del dispositivo. Con el Motor 2, se requiere consentimiento informado explícito del usuario antes de iniciar la transmisión a Decart. FashionStore no almacena transmisiones de video, únicamente la fotografía capturada si el cliente decide guardarla.
2. **Seguridad de Tokens:** La clave maestra de Decart reside únicamente en el backend (`DECART_API_KEY`). La aplicación móvil solo recibe tokens efímeros (~60 s como tiempo máximo para establecer la conexión con Decart) emitidos por `/api/v1/vestidor/token`.
3. **Disponibilidad y Fallback:** El vestidor virtual está garantizado al 100% mediante el Motor 1 local. El Motor 2 es opcional; si ocurre cualquier falla (timeout, sin créditos, error de red), el sistema degrada automáticamente al Motor 1 local.
4. **Control de Costos:** Se limita la sesión en modo realista a un máximo de 60 segundos por regla de negocio de control de costos (concepto separado e independiente del token de conexión), registrando `duracion_segundos` en la base de datos para auditoría y facturación.
5. **Rendimiento:** El motor local debe operar de forma fluida en dispositivos móviles de gama media; la tasa de cuadros aceptable se definirá y validará en las pruebas de campo.
