---
name: fashionstore-mobile-sdd
description: Desarrollo de la APLICACIÓN MÓVIL de FashionStore (e-commerce omnicanal premium y vestidor de Realidad Aumentada) con Flutter 3.x y Dart, guiado por Spec-Driven Development (SDD). Úsala SIEMPRE que se pida crear, modificar, revisar, depurar, maquetar o probar pantallas, widgets, estado (Bloc/Riverpod), servicios HTTP, almacenamiento seguro de tokens o el pipeline de Realidad Aumentada (AR) en Ec-mobile/.
---

# FashionStore · Aplicación Móvil con SDD (Flutter 3.x & Dart)

Esta skill gobierna la arquitectura y el desarrollo de la aplicación móvil de **FashionStore** en `Ec-mobile/`. La app ofrece una experiencia nativa fluida de lujo para clientes, integrando exploración de catálogo, reservas de probador en sucursales físicas, compras digitales y un **Vestidor Virtual en Realidad Aumentada (CU10)**.

Todo incremento de código se rige por **Spec-Driven Development (SDD)**: el agente no asume contratos de red ni inventa pantallas sin verificar la especificación aprobada en `.specs/`.

---

## 1. Alcance y Rol del Agente

* **Entorno:** Directorio `Ec-mobile/` (Flutter 3.x, Dart 3+, Android SDK / iOS).
* **Rol:** Principal Mobile Architect & Flutter/AR Specialist.
* **Alcance de Casos de Uso:** La aplicación móvil está enfocada primordialmente en el rol **Cliente**:
  * Autenticación (`CU01` Registro, `CU02` Login, `CU04` Perfil, `CU33` Recuperar acceso).
  * Catálogo y Exploración (`CU05` Consultar catálogo, `CU06` Búsqueda difusa `pg_trgm`, `CU07` Variantes, `CU08` Stock por sucursal, `CU09` Promociones).
  * Experiencia Inmersiva (`CU10` Vestidor Virtual AR).
  * Transacciones Omnicanal (`CU11` Carrito, `CU12-CU14` Reservas de prendas en probadores de tienda, `CU15-CU16` Checkout digital móvil con Stripe, `CU17` Historial de compras).
* **Documentación Técnica de Referencia:**
  * [references/arquitectura-movil.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.agents/skills/fashionstore-mobile-sdd/references/arquitectura-movil.md) → Arquitectura limpia Feature-First, pipeline AR, BLoC/Riverpod, almacenamiento seguro y servicios HTTP.
  * [references/fashionstore-tokens.md](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.agents/skills/fashionstore-mobile-sdd/references/fashionstore-tokens.md) → Especificación idéntica de tokens: paleta Slate/Camel, tipografía Outfit, potencias de 2 (`space-1` a `space-7`) y elevaciones.

---

## 2. Flujo SDD Obligatorio en Mobile

Antes de alterar o generar código dentro de `Ec-mobile/`, se debe ejecutar el siguiente ciclo:

```
┌──────────────────────────────────────────────────────────┐
│ 1. Inspeccionar Especificación (.specs/changes/<CU>/)    │
│    Leer spec.md para entender el flujo móvil y errores   │
├──────────────────────────────────────────────────────────┤
│ 2. Validar Contrato de Integración con FastAPI           │
│    Confirmar endpoints /api/v1/..., headers y DTOs       │
├──────────────────────────────────────────────────────────┤
│ 3. Estructurar en Feature-First (Data, Domain, UI)       │
│    Dividir use cases, DTOs y widgets de presentación     │
├──────────────────────────────────────────────────────────┤
│ 4. Aplicar Tokens a través de AppTheme Centralizado      │
│    Prohibidos colores y EdgeInsets arbitrarios inline    │
├──────────────────────────────────────────────────────────┤
│ 5. Registrar Avance en checkpoint.md                     │
│    Documentar estado de tareas y verificación            │
└──────────────────────────────────────────────────────────┘
```

1. **Lectura de Spec:** Verifica `.specs/changes/<CU>/spec.md` (o `.specs/finalized/<CU>/spec.md`). Identifica precondiciones, flujo del cliente móvil y manejo de errores (ej. sin stock, sucursal cerrada, fallo de cámara en AR).
2. **Validación de Contrato:** Comprueba que las peticiones HTTP coincidan con los schemas del backend (ej. `POST /api/v1/ventas/checkout` con `tipo_venta: "digital_movil"`).
3. **Planificación y Tareas:** Mantén sincronizados `plan.md` y `tasks.md`.
4. **Implementación:** Código tipado en Dart, inmutable, con manejo de estados de carga, error y vacío.
5. **Cierre:** Actualiza `checkpoint.md` antes de pausar o entregar la tarea.

---

## 3. Mapeo de Diseño y Centralización de Tokens (`AppTheme`)

La estética de FASHION STORE exige coherencia milimétrica con la versión web.

### 3.1 Prohibición de Instanciación Arbitraria (Hard Constraint)
* **PROHIBIDO** instanciar valores mágicos o no binarios en widgets:
  ❌ `EdgeInsets.all(10)`, `EdgeInsets.symmetric(horizontal: 15)`, `SizedBox(height: 12)`.
  ❌ `Color(0xFF123456)` o `Colors.black` instanciados de forma directa en pantallas.
* **OBLIGATORIO** consumir exclusivamente los tokens centralizados:
  ✔ `AppSpacing.space4` (16.0), `AppSpacing.space3` (8.0), `AppSpacing.space5` (32.0).
  ✔ `AppColors.primary`, `AppColors.surface`, `AppColors.secondary500` (Camel), `AppColors.slate900`.
  ✔ `AppTypography.headlineMd`, `AppTypography.labelCaps`.
  ✔ `AppRadius.sm` (4.0), `AppRadius.md` (8.0), `AppRadius.full` (9999.0).

### 3.2 Nombre Oficial Normativo
* En toda la aplicación móvil, textos de bienvenida, splash screen y configuraciones, el nombre es **FASHION STORE** (nunca "AURA STUDIO").

---

## 4. Convenciones de Código en Flutter & Dart

### 4.1 Inmutabilidad y Constructores `const`
* Todos los widgets sin estado deben ser `StatelessWidget` con constructores `const`.
* Modelos de datos del dominio deben ser inmutables (`@freezed` o clases con atributos `final` y constructor `const`).

### 4.2 Arquitectura de Capas por Paquete de Dominio y Caso de Uso
Cada incremento se ubica en `lib/src/modulos/<paquete_dominio>/<cu>/` estructurado en:
* `datos/`: Modelos DTO (`fromJson`, `toJson`), datasources HTTP y repositorios de implementación.
* `dominio/`: Entidades puras y casos de uso.
* `presentacion/`: BLoCs/Cubits, estados inmutables, widgets atómicos y pantallas (`_screen.dart`).

### 4.3 Almacenamiento Seguro de Sesión
* Prohibido almacenar tokens JWT en `SharedPreferences`.
* Usar siempre `flutter_secure_storage` mediante `SecureStorageService` para el `access_token`.

### 4.4 Manejo de Errores de Red
* Toda llamada a la API debe capturar `DioException` o fallos de conexión, traduciendo el JSON `{"detail": "...", "code": "..."}` del backend a excepciones de dominio tipadas.
* Los errores se muestran al usuario mediante **Luxury SnackBars** o **BottomSheets** consistentes con el diseño de FASHION STORE.

---

## 5. Módulo de Realidad Aumentada (CU10 - Vestidor Virtual)

Para el caso de uso del vestidor virtual:
1. Validar siempre que el producto tenga configurado `modelo_ar_url`. Si es nulo o vacío, bloquear el botón de AR y mostrar badge informativo.
2. Manejar permisos de cámara con degradación elegante si el usuario los deniega.
3. Registrar la sesión consumiendo `POST /api/v1/vestidor/sesion` enviando `dispositivo: "app_flutter"` y actualizando `genero_interes: true` si el usuario añade la prenda al carrito tras la experiencia.

---

## 6. Definition of Ready & Definition of Done para Mobile

### Definition of Ready (DoR)
1. Caso de uso identificado y spec disponible en `.specs/`.
2. Contrato de API verificado en `backend/main.py` y `references/dominio.md`.
3. Modelos de entrada y salida identificados para generar los DTOs en Dart.
4. Diseños responsive definidos para pantallas de teléfonos (iOS y Android).

### Definition of Done (DoD)
1. Pantalla y widgets construidos sin estilos arbitrarios, usando `AppTheme`.
2. Todos los estados de pantalla implementados: Inicial, Cargando (`shimmer`), Éxito y Error.
3. Tokens JWT almacenados en `flutter_secure_storage`.
4. Sin advertencias de análisis estático (`dart analyze` limpio).
5. Trazabilidad documentada en `checkpoint.md`.
