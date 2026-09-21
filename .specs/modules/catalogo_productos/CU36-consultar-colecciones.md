# Especificación Técnica Permanente: CU36 - Consultar Colecciones

**Código:** CU36  
**Nombre:** Consultar Colecciones Activas y Exploración de Prendas por Colección  
**Paquete de Dominio:** `catalogo_productos`  
**Directorio Funcional:** `cu36_consultar_colecciones`  
**Actores:** Cliente (Registrado y Visitante Anónimo)  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Versión:** 1.0.0 (Línea Base Permanente Consolidada)  
**Estado:** 🟢 Aprobado y Promovido a Especificación Permanente  
**Fuentes de Verdad:**
- Documentación Funcional: `SI2-Parcial1.md` (Catálogo, temporadas, colecciones cápsula, prendas, variantes, existencias físicas).
- Referencia Visual y UX Web: Capturas de referencia Desktop Haute Couture Atelier (Hero con Colección Destacada y 4 piezas clave, sección "Otras colecciones" con cards interactivas, vista de detalle con grilla editorial y botón `← Volver`).
- Referencia Visual y UX Mobile: Capturas de referencia Mobile Atelier (`image_45cf27.png` y `image_45cbbe.png`: Chips de temporada, cuadrícula 2x2 de piezas clave, cards de colecciones con badges y vista de detalle inmersiva con botón de retorno `← Volver`).
- Directriz Arquitectónica Global: Jerarquía de Vistas (Hub-and-Spoke) ([`.specs/architecture/directriz-navegacion-hub-and-spoke.md`](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/.specs/architecture/directriz-navegacion-hub-and-spoke.md)).
- Design System: Tipografía institucional `Outfit`, paleta textil Obsidian/Camel/Marfil de `fashionstore-tokens.md`, y catálogo 100% femenino.

---

## 1. Definición Funcional y Reglas de Negocio

### 1.1 Propósito y Alcance
Proporcionar a los clientes de FashionStore una experiencia editorial omnicanal para explorar colecciones cápsula y colecciones de temporada comercial vigentes, visualizar sus piezas maestras en vitrina y acceder a la lista detallada de prendas de alta costura confeccionadas bajo cada colección, garantizando una transición inmersiva y navegación jerárquica limpia tanto en Web como en Mobile.

### 1.2 Reglas de Negocio Estrictas

1. **Resolución de Temporada Comercial Activa:**
   - La temporada activa se resuelve consultando `fashionstore.temporadas` donde `activa = true` y `fecha_inicio <= CURRENT_DATE <= fecha_fin`.
   - Si ninguna temporada coincide exactamente con la fecha actual, se aplica fallback a la temporada con `activa = true` más reciente por `fecha_inicio DESC`.

2. **Jerarquía Relacional Canónica:**
   - **Temporada ➔ Colecciones:** Una temporada comercial agrupa una o más colecciones (`colecciones.id_temporada -> temporadas.id_temporada`).
   - **Colección ➔ Prendas:** Una colección contiene múltiples prendas de ropa de alta costura (`productos.id_coleccion -> colecciones.id_coleccion`).
   - **Prendas ➔ Variantes:** Cada prenda se desglosa en variantes de talla y color con existencias físicas en sucursales.

3. **Cálculo de Precios y Conteo Real:**
   - Para cada colección, `precio_desde = MIN(productos.precio_base)` calculado sobre prendas activas (`productos.activo = true`).
   - `total_prendas` refleja el conteo real en base de datos de productos activos vinculados a la colección.

4. **Colección Destacada (Hero) y Otras Colecciones:**
   - Se selecciona una colección como `coleccion_destacada` para la temporada activa (marcada con `es_destacada = true` o la colección principal de temporada).
   - Expone hasta 4 `piezas_clave` activas y con stock disponible para exhibición inmediata.
   - Las colecciones secundarias y de archivo se exponen en la sección "Otras colecciones".

5. **Regla de Negocio Global: Catálogo Exclusivamente Femenino:**
   - Toda la indumentaria, prendas y piezas de sastrería son estrictamente para mujeres.
   - Queda totalmente excluida cualquier referencia, prenda o modelo masculino.

6. **Integridad de Datos Reales (Cero Hardcoding):**
   - Todas las prendas y colecciones provienen estrictamente de la base de datos PostgreSQL Neon (`fashionstore.colecciones` y `fashionstore.productos`).
   - Cero productos ficticios o quemados en cliente.

7. **Directriz Arquitectónica de Navegación: Jerarquía Hub-and-Spoke:**
   - `CU36` (`Colecciones` y `DetalleColeccion`) está clasificada normativamente como **Pantalla Secundaria (Hoja / Spoke)**.
   - **Barra de navegación principal (Navbar Web / BottomNavigationBar Mobile): OCULTA / NO DISPONIBLE.**
   - **Botón de regreso (`← Volver` / `leading: BackButton()`): ESTRICTAMENTE OBLIGATORIO.** Retorna a la pantalla previa inmediata (`Inicio` o lista de colecciones).

---

## 2. Arquitectura de Backend (`Ec-backend` - FastAPI + SQLAlchemy 2.0)

### 2.1 Modelos ORM (`app/modules/catalogo/modelos.py`)
Mapeo sobre esquema `fashionstore`:
- `ColeccionORM`: `id_coleccion`, `id_temporada`, `nombre`, `descripcion`, `imagen_url`, `activa`, `es_destacada`.
- `TemporadaORM`: `id_temporada`, `nombre`, `tipo`, `fecha_inicio`, `fecha_fin`, `activa`.
- `ProductoORM`: `id_producto`, `id_categoria`, `id_coleccion`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `activo`.

### 2.2 Esquemas Pydantic (`app/modules/catalogo/cu36_consultar_colecciones/esquemas.py`)
- `ProductoColeccionItemOut`: DTO de prenda con `id_producto`, `nombre`, `descripcion`, `precio_base` (Decimal), `imagen_url`, `badge_editorial`, `subtitulo_textil`, `categoria`, `stock_total_disponible`, `tiene_stock`.
- `ColeccionResumenOut`: DTO de colección con `id_coleccion`, `nombre`, `descripcion`, `temporada_nombre`, `precio_desde`, `total_prendas`, `es_destacada`, `badge_edicion`, `imagen_portada`, `piezas_clave`.
- `ColeccionesActivasResponseOut`: DTO raíz con `temporada_activa_id`, `temporada_activa_nombre`, `coleccion_destacada`, `otras_colecciones`, `total_colecciones`.
- `ColeccionDetalleOut`: DTO de detalle con `id_coleccion`, `nombre`, `descripcion`, `total_prendas`, `mensaje_empty_state`, `productos`.

### 2.3 Endpoints REST (`app/modules/catalogo/cu36_consultar_colecciones/router.py`)
- `GET /api/v1/colecciones/activas` (y alias `/api/v1/catalogo/colecciones/activas`): Retorna `ColeccionesActivasResponseOut`.
- `GET /api/v1/colecciones/{id_coleccion}/productos` (y alias `/api/v1/catalogo/colecciones/{id_coleccion}/productos`): Retorna `ColeccionDetalleOut` (o 404 Not Found si no existe).

---

## 3. Arquitectura Frontend Web (`Ec-frontend` - Angular 19+)

### 3.1 Componentes y Layouts
- **[ColeccionesComponent](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-frontend/src/app/modules/colecciones/paginas/colecciones/colecciones.component.ts):**
  - Vista editorial de colecciones con Hero destacado, 4 piezas clave, y grid interactivo de otras colecciones donde cada card es un botón navegable hacia `/colecciones/:id`.
  - Botón `← Volver` con redirección inmediata a `/inicio`.
- **[ColeccionDetalleComponent](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-frontend/src/app/modules/colecciones/paginas/coleccion-detalle/coleccion-detalle.component.ts):**
  - Grilla de prendas de la colección seleccionada con badges textiles, precios y enlace de compra.
  - Botón `← Volver` hacia `/colecciones`.
- **Enrutamiento Autónomo (Hoja):**
  - Se declaran en `app.routes.ts` fuera del `MainLayoutComponent`, garantizando que la barra de navegación institucional superior no se renderice en estas pantallas secundarias.

---

## 4. Arquitectura Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x)

### 4.1 Pantallas y Estado Reactivo
- **[ColeccionesScreen](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/colecciones_screen.dart):**
  - Reproduce fielmente la experiencia móvil con selector de temporadas, piezas clave en 2x2 y lista vertical de colecciones.
  - Se ejecuta a pantalla completa sin `bottomNavigationBar`.
  - `AppBar` con `leading: BackButton()` funcional.
- **[DetalleColeccionScreen](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/detalle_coleccion_screen.dart):**
  - Grilla 2x2 de prendas con bookmark interactivo, precio en EUR y botón `VER →`.
- **[ColeccionesBloc](file:///c:/Users/tonys/OneDrive/Documentos/contenido/SI2/Parcial1-Ecommerce/Ec-mobile/lib/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/bloc/colecciones_bloc.dart):**
  - Gestión inmutable de estados: `ColeccionesInicial`, `ColeccionesCargando`, `ColeccionesCargado`, `ColeccionesError`.
  - Parsing decimal seguro mediante `double.tryParse` para tipos `num` o cadenas `Decimal` de la API sin `TypeError`.
- **Diseño Responsive y Anti-Overflow:**
  - Relación de aspecto `childAspectRatio: 0.65`, contenedores elásticos en `Expanded` y fotos en `Positioned.fill`, eliminando huecos blancos y asegurando cero desbordamientos `RenderFlex`.

---

## 5. Matriz de Puntos de Control y Verificación (Checkpoints CP-01 a CP-19)

| ID | Capa / Módulo | Criterio de Verificación | Estado |
| :--- | :--- | :--- | :--- |
| **CP-01** | Backend DB | Consultas SQL de temporada activa resuelven por rango de fechas y fallback a `activa = true`. | 🟢 Superado |
| **CP-02** | Backend Cálculo | Cada colección calcula correctamente `precio_desde` y `total_prendas` sobre prendas activas. | 🟢 Superado |
| **CP-03** | Backend Endpoints | Endpoints REST `/api/v1/colecciones/...` retornan códigos 200/404 según contratos Pydantic (100/100 tests). | 🟢 Superado |
| **CP-04** | Frontend Hero | Vista `/colecciones` muestra Colección Destacada con 4 piezas clave, badges y tipografía Outfit. | 🟢 Superado |
| **CP-05** | Frontend Grilla | Sección "Otras colecciones" renderiza cards con badge de edición, temporada y precio de entrada. | 🟢 Superado |
| **CP-06** | Frontend Nav | Clic en card o botón navega a `/colecciones/:id` listando las prendas de la colección. | 🟢 Superado |
| **CP-07** | Frontend Build | Compilación de producción limpia sin errores TypeScript ni estilos rotos (`npm run build`). | 🟢 Superado |
| **CP-08** | Mobile Screen | `ColeccionesScreen` reproduce fichas de diseño: Chips de filtro, piezas clave 2x2 y lista vertical. | 🟢 Superado |
| **CP-09** | Mobile Detalle | `DetalleColeccionScreen` reproduce grilla 2x2 de prendas con bookmark y precio en EUR. | 🟢 Superado |
| **CP-10** | Mobile Static Analysis | Código Flutter estricto, inmutable y conforme a tokens (`flutter analyze` 0 issues). | 🟢 Superado |
| **CP-11** | Mobile Test Suite | Suite completa de tests en Flutter pasando al 100% (77/77 tests totales). | 🟢 Superado |
| **CP-12** | Catálogo Femenino | Cero imágenes de hombres; 100% prendas y modelos de moda femenina exclusiva. | 🟢 Superado |
| **CP-13** | Integridad BD Real | Todas las prendas provienen estrictamente de `fashionstore.productos` en PostgreSQL Neon. | 🟢 Superado |
| **CP-14** | Card Cliqueable | Toda la card de "Otras colecciones" funciona como botón interactivo completo. | 🟢 Superado |
| **CP-15** | Carga de Imágenes | Imágenes de colecciones y prendas responden HTTP 200 con fallback reactivo `onImgError`. | 🟢 Superado |
| **CP-16** | Responsive Safety | Aspect ratio 0.65 y fotos en `Positioned.fill` eliminan huecos blancos y desbordamientos. | 🟢 Superado |
| **CP-17** | Serialización Decimal | Deserialización tolerante de precios monetarios soportando primitivos y cadenas `Decimal`. | 🟢 Superado |
| **CP-18** | Tipografía Outfit | Unificación tipográfica atómica bajo la familia `Outfit`, tracking y paleta de tokens. | 🟢 Superado |
| **CP-19** | Hub-and-Spoke | `CU36` clasificada como Pantalla Secundaria (Hoja): sin barra de navegación global y con `← Volver`. | 🟢 Superado |
