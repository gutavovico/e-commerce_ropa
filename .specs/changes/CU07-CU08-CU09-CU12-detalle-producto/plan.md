# Plan de Ejecución Secuencial: Detalle de Producto, Variantes, Disponibilidad y Reservas

**ID del Cambio:** `CU07-CU08-CU09-CU12-detalle-producto`  
**Casos de Uso Integrados:** CU07 (Detalle), CU08 (Variantes Talla/Color), CU09 (Disponibilidad Sucursal), CU12 (Reserva de Cita en Boutique) y CU10 (AR Aislado).  
**Metodología:** Spec-Driven Development (SDD)  
**Estrategia de Ejecución:** Tres bloques independientes y estrictamente secuenciales con puertas de validación.

---

## 1. Bloque 1: Backend (`Ec-backend` - FastAPI + PostgreSQL Neon)

### Fase 1.1: Esquemas Pydantic y Contratos de Datos
- **Módulo:** `app/modules/catalogo/cu07_detalle_producto/esquemas.py` y `app/modules/reservas/cu12_reservar_prendas/esquemas.py`.
- **Definiciones:**
  - `ComposicionNobleOut`: Cuerpo principal, forro interior, técnica textil, instrucciones de conservación.
  - `VarianteDetalleOut`: `id_variante`, `sku`, `id_talla`, `talla_codigo`, `talla_orden`, `id_color`, `color_nombre`, `color_hex`, `precio_extra`, `precio_final_variante`, `stock_total_disponible`, `tiene_stock`.
  - `PrendaComplementariaOut`: Producto recomendado para estilismo integral con precio y foto.
  - `ProductoDetalleOut`: Ficha completa con galería fotográfica (4 tomas de alta fidelidad), calificaciones, precios tachados/descuento, variantes agrupadas y datos de confección noble.
  - `DisponibilidadSucursalItemOut`: `id_sucursal`, `nombre`, `ciudad`, `direccion`, `cantidad_disponible`, `cantidad_reservada`, `estado_stock`, `badge_stock`, `citas_disponibles_texto`.
  - `DisponibilidadSucursalesOut`: Lista de disponibilidad por boutique física.
  - `ReservaCrearIn` y `ReservaItemIn`: Payload de creación de cita presencial con `id_sucursal`, `fecha_hora_atencion`, `canal_origen`, `items` y `observacion`.
  - `ReservaCreadaOut`: Respuesta de confirmación con código de reserva, boutique asignada, horario y cortesías.

### Fase 1.2: Modelos ORM, Servicios y Endpoints Transaccionales
- **Modelos ORM (`app/modules/reservas/modelos.py` y `app/modules/catalogo/modelos.py`):**
  - Mapeo de `ReservaORM` (`fashionstore.reservas`), `ReservaDetalleORM` (`fashionstore.reserva_detalle`) y `MovimientoInventarioORM` (`fashionstore.movimientos_inventario`).
  - Mapeo de relaciones con `SucursalORM`, `ClienteORM`, `VarianteProductoORM` e `InventarioSucursalORM`.
- **Servicios de Dominio:**
  - `ProductoDetalleServicio`: Carga atómica con `selectinload` de variantes, tallas, colores e inventarios. Deducción de galería multi-ángulo y cálculo de promociones activas.
  - `DisponibilidadServicio`: Consulta multisede en tiempo real cruzando `inventario_sucursal` y `sucursales`.
  - `ReservaServicio`: Implementación de la unidad transaccional de reserva:
    1. Verificación de stock disponible (`cantidad_disponible >= cantidad`).
    2. Decremento de `cantidad_disponible` e incremento de `cantidad_reservada`.
    3. Inserción de la cabecera de reserva (`estado = 'pendiente'`).
    4. Inserción de líneas de `reserva_detalle`.
    5. Inserción obligatoria de auditoría en `movimientos_inventario` (`tipo_movimiento = 'reserva'`).
    6. Commit atómico; rollback inmediato y excepción `StockInsuficienteError` (409) ante cualquier inconsistencia.
- **Enrutadores REST:**
  - `GET /api/v1/productos/{id_producto}`
  - `GET /api/v1/productos/{id_producto}/disponibilidad`
  - `POST /api/v1/reservas` (protegido con `get_usuario_actual`).
  - `GET /api/v1/sucursales/activas` (lista de boutiques para el modal de citas).

### Fase 1.3: Suite de Pruebas Unitarias y de Integración (Pytest)
- `tests/modules/catalogo/test_cu07_detalle_producto.py`: Pruebas de consulta de producto, 404 de producto inactivo, variantes y composición.
- `tests/modules/catalogo/test_cu09_disponibilidad.py`: Pruebas de consulta de existencias por sucursal para variantes activas.
- `tests/modules/reservas/test_cu12_reservas.py`: Pruebas de creación de reserva con decremento de `cantidad_disponible`, incremento de `cantidad_reservada`, registro en `movimientos_inventario` y control de 409 ante stock agotado.

---

## 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

### Fase 2.1: Enrutamiento y Cumplimiento Hub-and-Spoke
- En `app.routes.ts`, declarar la ruta `/productos/:id` **fuera de `MainLayoutComponent`**.
- La vista de detalle no incluye la barra de navegación institucional superior, asegurando inmersión editorial de alta costura y cumplimiento estricto del patrón Hub-and-Spoke (Pantalla Secundaria / Hoja).
- Cabecera dedicada ligera con botón interactivo `← VOLVER` que ejecuta `Location.back()` del historial nativo de Angular.

### Fase 2.2: Servicios HTTP Tipados (`ProductoDetalleService` y `ReservaService`)
- Métodos para consultar detalle de producto (`obtenerDetalle(id)`), consultar disponibilidad multisede (`obtenerDisponibilidad(id, idVariante)`) y formalizar reserva en boutique (`crearReserva(payload)`).

### Fase 2.3: Componente Principal `ProductoDetalleComponent`
- **Gestión Reactiva con Signals:**
  - `producto = signal<ProductoDetalle | null>(null)`
  - `varianteSeleccionada = signal<VarianteDetalle | null>(null)`
  - `colorSeleccionadoId = signal<number | null>(null)`
  - `tallaSeleccionadaId = signal<number | null>(null)`
  - `fotoPrincipal = signal<string>('')`
  - `cargando = signal<boolean>(true)`
  - `modalReservaAbierto = signal<boolean>(false)`
  - `esFavorito = signal<boolean>(false)`
- **Maquetación 2 Columnas Fiel a `image_2e2d7e.png`:**
  - Galería izquierda: Fotografía principal con badges (`EDICIÓN LIMITADA`, `ALTA COSTURA LYON`), indicador de modelo, 4 miniaturas rotuladas (*FRONTAL*, *TEXTURA SEDA*, *ESPALDA*, *COSTURA*) con cambio interactivo de vista.
  - Ficha derecha: Subtítulo de alta costura, SKU dinámico, título principal, valoraciones VIP, precio en EUR con descuento y ahorro, selector circular de 4 colores artesanales, botones cuadrados de talla con indicador tachado para tallas sin stock, texto dinámico de disponibilidad por boutique, botón principal *"AÑADIR A LA BOLSA"*, botón secundario *"CITA DE PRUEBA BOUTIQUE"* y bullets de garantías.
  - Secciones inferiores: Tarjetas de composición y conservación noble (*Limpieza profesional*, *Vapor vertical*, *Almacenamiento*) y vitrina *"COMPLETA EL LOOK ATELIER"* con CTA de compra conjunta.

### Fase 2.4: Componente Modal de Reserva en Boutique (`ModalReservaBoutiqueComponent`)
- Reproduce pixel-perfect `image_2e295b.png`:
  - Cabecera con monograma `📅 PRIVATE ATELIER SERVICE` y botón `✕`.
  - Resumen visual de la prenda seleccionada (miniatura, título, talla elegida y precio).
  - Selector de boutique insignia con botones de opción radio (Flagship Serrano Madrid, Boutique Paris Saint-Honoré, Madrid Central Atelier Hub) y badges de stock en tiempo real (*"2 UDS EN STOCK"*, etc.).
  - Selector de fecha y franja horaria preferente en píldoras (*MAÑANA 11:30H*, *MAÑANA 16:30H*, *VIERNES 12:00H*).
  - Nota de cortesía atelier (*champán de bienvenida y ajuste sin coste*).
  - Acciones: Botón *"CANCELAR"* y botón negro *"CONFIRMAR RESERVA EN BOUTIQUE"*.

### Fase 2.5: Integración del Bloque Vestidor Virtual (CU10 Aislado)
- Maquetación del bloque *"SIMULADOR VESTIDOR VIRTUAL & ESCÁNER 3D"* bajo las miniaturas con métricas textiles y botón *"INICIAR PROBADOR INTERACTIVO"* que muestra notificación de cortesía sin invocar lógica 3D.

---

## 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x)

### Fase 3.1: Modelos DTO y Datasources HTTP
- Modelos inmutables en `lib/src/modulos/catalogo/cu07_detalle_producto/datos/modelos/`:
  - `ProductoDetalleDto`, `VarianteDetalleDto`, `ComposicionNobleDto`, `DisponibilidadBoutiqueDto`.
- Modelos de reserva en `lib/src/modulos/reservas/cu12_reservar_prendas/datos/modelos/`:
  - `ReservaCrearDto`, `ReservaConfirmadaDto`.
- Cliente HTTP con manejo de errores de red y tokens.

### Fase 3.2: Gestores de Estado BLoC
- `ProductoDetalleBloc`:
  - Control de carga, selección de color y talla, cambio de fotografía activa y cálculo de disponibilidad.
- `ReservaBoutiqueBloc`:
  - Control de selección de sucursal, fecha/hora y emisión de la reserva con estados: `ReservaInicial`, `ReservaEnviando`, `ReservaExitosa`, `ReservaFallo`.

### Fase 3.3: Pantalla `PantallaProductoDetalle` (Hub-and-Spoke Mobile)
- Ubicada como ruta secundaria (`Navigator.push`) a pantalla completa **sin `BottomNavigationBar`**.
- `AppBar` con botón de regreso `leading: IconButton(icon: Icon(Icons.arrow_back), onPressed: () => Navigator.of(context).pop())` y botón de wishlist en acciones.

### Fase 3.4: Construcción de la Vista Móvil Fiel a `image_2e3062.png`
- Galería con indicador numérico `1/4` y botón flotante en píldora oscura `[ 👁 PROBAR EN AR ]` (CU10 preparado).
- Tira horizontal de 4 miniaturas con scroll táctil.
- Encabezado con línea de atelier, SKU, título, rating en estrellas y precio con descuento.
- Selectores circulares de color con borde activo y selector de tallas cuadradas (con estilo inactivo/tachado para tallas sin existencias).
- Texto dinámico: `● Talla 38: Últimas 2 unidades en Flagship Serrano.`
- Acordeón interactivo `ESPECIFICACIONES & TRAZABILIDAD` con desglose de composición y confección noble.
- **Sección de Disponibilidad y Reserva Continua en Vista Móvil:**
  - Acordeón `Disponibilidad en Boutique`:
    - Tarjeta por cada sucursal con unidades disponibles, dirección y badge de disponibilidad.
    - **Botón directo integrado por boutique:** `[ 🏢 RESERVAR EN ESTA BOUTIQUE ]`.
    - Al pulsar, despliega un BottomSheet elegante para seleccionar la franja horaria y confirmar la cita presencial.
- Barra inferior persistente de compra: Botón con icono de escáner + botón completo `[ 🛍 AÑADIR A LA BOLSA · 890 € ]`.
