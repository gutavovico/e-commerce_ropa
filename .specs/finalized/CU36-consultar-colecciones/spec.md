# Especificación Técnica SDD: CU36 - Consultar Colecciones

**ID del Caso de Uso:** CU36  
**Nombre:** Consultar Colecciones Activas y Exploración de Prendas por Colección  
**Paquete:** `catalogo` (Catálogo y Exploración)  
**Actores:** Cliente Autenticado y Visitante Anónimo  
**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)  
**Nivel de Riesgo:** Nivel 1 (Exploración pública de catálogo, consultas agregadas y navegación editorial)  
**Estado:** 🟢 IMPLEMENTACIÓN Y PRUEBAS 100% COMPLETADAS (Bloques 1, 2 y 3 Verificados - Pendiente Autorización para Consolidación Permanente)  

---

## 1. Alcance y Reglas de Negocio

1. **Resolución de Temporada Comercial Activa:**
   - Consulta `fashionstore.temporadas` donde `activa = true` y `fecha_inicio <= CURRENT_DATE <= fecha_fin`.
   - Fallback a la temporada activa más reciente si no hay coincidencia exacta de fechas.
2. **Jerarquía y Agregación de Colecciones (Relación Canónica):**
   - **Una temporada puede contener una o más colecciones:** Vinculadas mediante clave foránea `colecciones.id_temporada -> temporadas.id_temporada`.
   - **Una colección contiene múltiples prendas de ropa (productos):** Vinculadas mediante clave foránea `productos.id_coleccion -> colecciones.id_coleccion`.
   - **Colección Destacada (Hero):** Identificada como la colección principal de la temporada vigente. Expone hasta 4 piezas clave con existencias físicas.
   - **Otras Colecciones:** Colecciones secundarias e históricas con prendas en archivo.
   - **Cálculo de Precio de Entrada:** Para cada colección, `precio_desde = MIN(productos.precio_base)` para prendas activas.
   - **Total de Prendas:** Conteo real de productos activos (`productos.activo = true`) asociados a la colección en base de datos.
3. **Consulta de Prendas por Colección (`GET /api/v1/colecciones/{id_coleccion}/productos`):**
   - Retorna metadatos editoriales de la colección (nombre, descripción, temporada, taller/proveedor).
   - Retorna array de productos activos con fotos, precios base, badges editoriales, subtítulos textiles y stock consolidado.
   - Si la colección no existe: `404 Not Found`.
   - Si la colección no tiene prendas: `total_prendas: 0`, `productos: []` y estado "Próximo lanzamiento".
4. **REGLA DE NEGOCIO GLOBAL INQUEBRANTABLE (E-COMMERCE EXCLUSIVO PARA MUJERES):**
   - FashionStore es una firma y catálogo **EXCLUSIVAMENTE PARA MUJERES**.
   - Queda estrictamente prohibida la presencia de modelos masculinos, prendas de hombre, sastrería masculina o zapatillas unisex. Todo activo visual y fotografía editorial debe representar alta costura femenina.
5. **FUENTE DE DATOS REALES (CERO PRODUCTOS FICTICIOS O HARDCODEADOS):**
   - Todas las prendas mostradas en frontend y mobile provienen estrictamente de la base de datos PostgreSQL (`fashionstore.productos`).
   - Se prohíbe inventar productos o quemar listas artificiales en el cliente. Si hacen falta productos, se agregan al catálogo de la base de datos con sus variantes e inventario correspondientes.
6. **DIRECTRIZ ARQUITECTÓNICA DE NAVEGACIÓN (JERARQUÍA HUB-AND-SPOKE):**
   - La pantalla de `Colecciones` (`CU36`) y su vista derivada `DetalleColeccion` son formalmente **Pantallas Secundarias (Hojas / Spoke)** nacidas a partir de una acción en `Inicio`.
   - **Barra de navegación (Navbar Web / BottomNavigationBar Mobile): OCULTA / NO DISPONIBLE.** Queda terminantemente prohibido renderizar la barra de navegación principal global en estas pantallas.
   - **Botón de regreso (`← Volver` / `leading: BackButton()`): ESTRICTAMENTE OBLIGATORIO.** Ambas pantallas deben disponer de un encabezado/botón de retroceso funcional que retorne a la pantalla previa desde la que se accedió (`Inicio` desde la vista de colecciones, y `Colecciones` desde la vista de detalle de colección).

---

## 2. Contratos de API REST (FastAPI)

### Endpoint 1: Colecciones Activas
- **Ruta:** `GET /api/v1/colecciones/activas` (y alias `/api/v1/catalogo/colecciones/activas`)
- **Método:** `GET`
- **Autenticación:** Pública (no requiere token).
- **Parámetros:** `limite_piezas_clave: int = 4` (opcional).
- **Esquema de Retorno:** `ColeccionesActivasResponseOut`

### Endpoint 2: Prendas de una Colección
- **Ruta:** `GET /api/v1/colecciones/{id_coleccion}/productos` (y alias `/api/v1/catalogo/colecciones/{id_coleccion}/productos`)
- **Método:** `GET`
- **Autenticación:** Pública.
- **Parámetros Path:** `id_coleccion: int` (obligatorio).
- **Esquema de Retorno:** `ColeccionDetalleOut`

---

## 3. Esquemas Pydantic

- `ProductoColeccionItemOut`: `id_producto`, `nombre`, `descripcion`, `precio_base`, `imagen_url`, `badge_editorial`, `subtitulo_textil`, `categoria`, `colores_disponibles`, `stock_total_disponible`, `tiene_stock`.
- `ColeccionResumenOut`: `id_coleccion`, `nombre`, `descripcion`, `temporada_nombre`, `temporada_tipo`, `proveedor_nombre`, `taller_origen`, `precio_desde`, `total_prendas`, `es_destacada`, `badge_edicion`, `imagen_portada`, `piezas_clave`.
- `ColeccionesActivasResponseOut`: `temporada_activa_id`, `temporada_activa_nombre`, `coleccion_destacada`, `otras_colecciones`, `total_colecciones`.
- `ColeccionDetalleOut`: `id_coleccion`, `nombre`, `descripcion`, `temporada_nombre`, `proveedor_nombre`, `taller_origen`, `total_prendas`, `mensaje_empty_state`, `productos`.

---

## 4. Criterios de Aceptación (Gherkin)

```gherkin
Escenario: Consulta exitosa de colecciones con temporada vigente
  Dado que existe una temporada comercial activa con fecha_inicio <= HOY <= fecha_fin
  Y existen colecciones vinculadas con productos activos y stock disponible
  Cuando un cliente envía una petición GET a "/api/v1/colecciones/activas"
  Entonces el código de respuesta debe ser 200 OK
  Y el payload debe contener la "coleccion_destacada" con hasta 4 piezas clave
  Y el array "otras_colecciones" debe listar las colecciones secundarias con "precio_desde" mayor a 0

Escenario: Consulta de colección existente con listado de prendas
  Dado que existe una colección con id_coleccion = 1 con 4 prendas activas
  Cuando el usuario consulta "GET /api/v1/colecciones/1/productos"
  Entonces el código de respuesta debe ser 200 OK
  Y el campo "total_prendas" debe ser 4
  Y cada producto debe incluir id_producto, nombre, precio_base, badge_editorial y stock_total_disponible

Escenario: Consulta de colección sin productos asociados (Próximo lanzamiento)
  Dado que existe una colección con id_coleccion = 99 sin prendas asignadas
  Cuando el usuario consulta "GET /api/v1/colecciones/99/productos"
  Entonces el código de respuesta debe ser 200 OK
  Y el array "productos" debe estar vacío
  Y "mensaje_empty_state" debe contener "Próximo lanzamiento"

Escenario: Consulta de colección inexistente
  Dado que no existe ninguna colección con id_coleccion = 9999
  Cuando el usuario consulta "GET /api/v1/colecciones/9999/productos"
  Entonces el código de respuesta debe ser 404 Not Found
  Y el detalle del error debe indicar "Colección no encontrada"
```
