# Especificación Técnica SDD: CU18 - Recibir Recomendaciones Personalizadas

**ID del Caso de Uso:** CU18  
**Nombre:** Recibir Recomendaciones Personalizadas con Explicabilidad IA y Stock en Tiempo Real  
**Paquete:** `catalogo` (Catálogo y Exploración)  
**Actores:** Cliente Autenticado y Visitante Anónimo (con degradación controlada a Empty State)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 2 (Feature con Motor de IA / Afinidad y consulta de existencias)  
**Estado:** 🟢 Completado (Bloque 1: Backend, Bloque 2: Frontend & Bloque 3: Mobile)  

---

## 1. Alcance y Reglas de Negocio

1. **Motor de Recomendación basado en Compras Previas:**
   - Consulta el historial de compras del cliente autenticado (`ventas` en estado `'pagada'` -> `venta_detalle` -> `variantes_producto` -> `productos`, `categorias` y `colecciones`).
   - Identifica categorías y colecciones de mayor afinidad/frecuencia del cliente.
   - Recomienda productos que pertenezcan a esas categorías o colecciones afines.
   - **Filtro de Existencias Reales:** Solo se sugieren productos activos (`productos.activo = true`) que tengan existencias físicas (`inventario_sucursal.cantidad_disponible > 0`).
   - **Exclusión de Recompra Inmediata:** Se excluyen del listado los productos que el cliente ya compró en sus pedidos pagados previos.

2. **Caso en Frío / Estado Vacío (Empty State):**
   - Si el usuario no tiene compras registradas en el sistema (o es un visitante sin sesión activa), **no se inventan recomendaciones vacías ni ficticias**.
   - El backend responde `tiene_historial: false`, `items: []` y el mensaje oficial exacto:
     *"Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo"*.

3. **Explicabilidad con IA y Resiliencia sin Costo:**
   - Integración con Google Gemini Flash (vía `app/integrations/gemini_service.py` con `IA_API_KEY`).
   - Genera el campo explicativo `motivo` (ej: *"Basado en tu última adquisición de sastrería y seda en Flagship Serrano"*).
   - **Fallback Determinista Robusto**: Si no se proporciona `IA_API_KEY` o el servicio de IA experimenta fallos o límites de cuota, el backend conmuta de manera transparente a una síntesis estilística Atelier basada en la categoría más adquirida y la sucursal de compra, garantizando costo cero y cero tiempo de inactividad.
   - **Caché y Persistencia**: Se almacenan y consultan los puntajes y motivos en la tabla existente `fashionstore.recomendaciones_ia` (`id_cliente`, `id_producto`, `score_relevancia`, `motivo`, `generado_en`).

---

## 2. Contrato de API (FastAPI)

### Endpoint Principal
- **Ruta:** `GET /api/v1/catalogo/recomendaciones/personalizadas`  
- **Alias:** `GET /api/v1/recomendaciones/personalizadas`  
- **Método:** `GET`  
- **Autenticación:** Opcional vía Bearer JWT (`get_optional_current_user`).

### Parámetros Query
- `limite` (int, opcional, por defecto 6, mín 1, máx 12)
- `id_sucursal` (int, opcional)

### Esquemas Pydantic
- `VarianteRecomendadaOut`: Variante de talla/color con stock disponible.
- `ProductoRecomendadoItemOut`: Datos del producto, badges (`EDICIÓN LIMITADA`, `SASTRERÍA ATELIER`, `BÁSICO DE LUJO`), subtítulo textil, precio en EUR, score de relevancia y motivo individual.
- `RecomendacionesPersonalizadasOut`:
  - `tiene_historial: bool`
  - `motivo_general: Optional[str]`
  - `boutique_referencia: Optional[str]`
  - `mensaje_empty_state: Optional[str]`
  - `total_recomendados: int`
  - `items: List[ProductoRecomendadoItemOut]`

### Códigos de Respuesta HTTP
- `200 OK`: Éxito tanto con recomendaciones como con estado vacío.
- `401 Unauthorized`: Token Bearer malformado o revocado (cuando se envía token no nulo).
- `500 Internal Server Error`: Fallo no controlado capturado por el middleware global.

---

## 3. Entornos de Ejecución y Diagnóstico Multiplataforma

Para evitar ambigüedades operativas y fallos de ejecución en terminales locales:

| Componente | Directorio Raíz | Stack Tecnológico | Archivo de Configuración | Comando de Ejecución Local |
| :--- | :--- | :--- | :--- | :--- |
| **Backend API** | `Ec-backend/` | FastAPI, Python 3.11+, SQLAlchemy 2.0, PostgreSQL | `pyproject.toml`, `.env` | `uvicorn app.main:app --reload --port 8000` |
| **Frontend Web** | `Ec-frontend/` | Angular 19+, TypeScript, Tailwind CSS, Vite/Vitest | `package.json`, `angular.json` | `npm start` (puerto 4200) |
| **Mobile App** | `Ec-mobile/` | Flutter 3.x, Dart, Material 3, BLoC | `pubspec.yaml`, `analysis_options.yaml` | `flutter run -d <device>` (ej. `flutter run -d edge` o `-d windows`) |

### Regla Operativa Normativa:
1. **Comando `flutter run`:** Solo es válido ejecutarse dentro de `Ec-mobile/` (donde reside `pubspec.yaml`).
2. **Soporte Web en Flutter (`Ec-mobile/web/`):** Se integró la plataforma web oficial en `Ec-mobile` (`web/index.html`, `manifest.json`) para permitir la depuración y ejecución rápida de la interfaz móvil en navegadores de escritorio (`flutter run -d edge` o `flutter run -d chrome`) sin obligar al desarrollador a iniciar un emulador de Android/iOS pesado.

