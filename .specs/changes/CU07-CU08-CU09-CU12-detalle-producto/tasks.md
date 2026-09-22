# Tareas de Implementación: Detalle de Producto, Variantes, Disponibilidad y Reservas

**ID del Cambio:** `CU07-CU08-CU09-CU12-detalle-producto`  
**Metodología:** Spec-Driven Development (SDD)  
**Estado:** 🟢 Bloques 1, 2 y 3 implementados (gate superado el 2026-09-21)  

> **Nota de reconciliación (2026-09-21):** el Bloque 3 (Mobile) figuraba íntegramente sin marcar
> aunque el código, las pantallas y las pruebas ya existían en `Ec-mobile`. Se marca según el
> estado real del repositorio, con una desviación documentada: los DTO de reserva de **T-MO-02**
> no viven en `lib/src/modulos/reservas/cu12_reservar_prendas/datos/modelos/` sino junto al resto
> de la ficha, en `lib/src/modulos/catalogo/cu07_detalle_producto/datos/modelos/producto_detalle_dto.dart`.
> Los defectos de contrato detectados en este bloque están registrados en `checkpoint.md`
> (D-04, D-05, D-06, D-07).  

---

## 1. Bloque 1: Backend (`Ec-backend` - FastAPI + SQLAlchemy + PostgreSQL)

- [x] **T-BE-01**: Crear esquemas Pydantic para Detalle y Variantes en `app/modules/catalogo/cu07_detalle_producto/esquemas.py`:
  - [x] `ComposicionNobleOut` (cuerpo, forro, técnica textil, cuidados).
  - [x] `VarianteDetalleOut` (talla, color, SKU, precios, existencias).
  - [x] `PrendaComplementariaOut` (look sugerido).
  - [x] `ProductoDetalleOut` (ficha consolidada con galería multi-toma y ratings).
- [x] **T-BE-02**: Crear esquemas Pydantic para Disponibilidad por Sucursal en `app/modules/catalogo/cu09_disponibilidad/esquemas.py`:
  - [x] `DisponibilidadSucursalItemOut` y `DisponibilidadSucursalesOut`.
- [x] **T-BE-03**: Crear esquemas Pydantic para Reservas en Boutique en `app/modules/reservas/cu12_reservar_prendas/esquemas.py`:
  - [x] `ReservaItemIn`, `ReservaCrearIn`, `ReservaCreadaOut`.
- [x] **T-BE-04**: Mapear modelos ORM de reservas y movimientos en `app/modules/reservas/modelos.py`:
  - [x] `ReservaORM` (`fashionstore.reservas`), `ReservaDetalleORM` (`fashionstore.reserva_detalle`) y `MovimientoInventarioORM` (`fashionstore.movimientos_inventario`).
  - [x] Configurar relaciones bidireccionales con `SucursalORM`, `VarianteProductoORM` e `InventarioSucursalORM`.
- [x] **T-BE-05**: Implementar repositorio y servicio de Detalle de Producto (CU07 y CU08) en `app/modules/catalogo/cu07_detalle_producto/`:
  - [x] Consulta atómica con `selectinload` de variantes, tallas, colores e inventarios.
  - [x] Generación/resolución de galería multi-ángulo (frontal, textura, espalda, costura).
  - [x] Cálculo de promociones activas y cuotas *Atelier Pay*.
- [x] **T-BE-06**: Implementar repositorio y servicio de Disponibilidad Multisede (CU09) en `app/modules/catalogo/cu09_disponibilidad/`:
  - [x] Consulta de existencias físicas por boutique para la variante solicitada.
- [x] **T-BE-07**: Implementar servicio transaccional de Reservas en Boutique (CU12) en `app/modules/reservas/cu12_reservar_prendas/servicio.py`:
  - [x] Validación de fecha futura y horario de atención de la boutique.
  - [x] Descuento atómico de `cantidad_disponible` e incremento de `cantidad_reservada` en `inventario_sucursal`.
  - [x] Creación de registro en `reservas` y renglones en `reserva_detalle`.
  - [x] Creación obligatoria de registro de auditoría en `movimientos_inventario` (`tipo_movimiento = 'reserva'`).
  - [x] Manejo de excepción de stock insuficiente (`409 Conflict`).
- [x] **T-BE-08**: Implementar y registrar enrutadores REST en `app/modules/catalogo/router.py` y `app/modules/reservas/router.py`:
  - [x] `GET /api/v1/productos/{id_producto}`
  - [x] `GET /api/v1/productos/{id_producto}/disponibilidad`
  - [x] `POST /api/v1/reservas` (con autenticación de usuario).
  - [x] `GET /api/v1/sucursales/activas`
- [x] **T-BE-09**: Escribir pruebas unitarias y de integración en Pytest:
  - [x] `tests/modules/catalogo/test_cu07_detalle_producto.py` (CU07 y CU08).
  - [x] `tests/modules/catalogo/test_cu09_disponibilidad.py` (CU09).
  - [x] `tests/modules/reservas/test_cu12_reservas.py` (CU12).
- [x] **T-BE-10**: Ejecutar suite completa `pytest` garantizando 100% de tests aprobados.

---

## 2. Bloque 2: Frontend Web (`Ec-frontend` - Angular 19+ Standalone)

- [x] **T-FE-01**: Crear modelos e interfaces TypeScript en `src/app/modules/catalogo/cu07_detalle_producto/modelos/`:
  - [x] `ProductoDetalle`, `VarianteDetalle`, `ComposicionNoble`, `DisponibilidadSucursal`, `ReservaCrearPayload`, `ReservaConfirmacion`.
- [x] **T-FE-02**: Crear servicios HTTP en Angular:
  - [x] `ProductoDetalleService` (`obtenerDetalle`, `obtenerDisponibilidad`).
  - [x] `ReservaService` (`crearReservaBoutique`, `obtenerSucursales`).
- [x] **T-FE-03**: Configurar ruta `/productos/:id` en `app.routes.ts`:
  - [x] Declarada fuera de `MainLayoutComponent` para ocultar la barra de navegación institucional superior.
- [x] **T-FE-04**: Crear componente principal `ProductoDetalleComponent` en `src/app/modules/catalogo/cu07_detalle_producto/paginas/`:
  - [x] Cabecera dedicada ligera con botón `← VOLVER` que invoca `Location.back()` nativo.
  - [x] Breadcrumbs: `ATELIER / EDICIONES EXCLUSIVAS / [NOMBRE PRENDA]` y botón de guardados (wishlist).
  - [x] Galería izquierda con fotografía principal, badges de atelier, indicador de modelo y 4 miniaturas rotuladas (*FRONTAL*, *TEXTURA SEDA*, *ESPALDA*, *COSTURA*).
  - [x] Ficha técnica derecha con subtítulo de alta costura, SKU dinámico, título H1, estrellas de valoración VIP, precio con descuento y cuotas *Atelier Pay*.
  - [x] Selector circular de 4 colores artesanales con borde activo.
  - [x] Selector cuadrado de tallas normalizadas con estado inactivo/tachado para tallas sin existencias.
  - [x] Texto dinámico de disponibilidad física en boutiques según variante activa.
  - [x] Botón de compra *"AÑADIR A LA BOLSA"* y botón de cita presencial *"CITA DE PRUEBA BOUTIQUE"*.
  - [x] Sección inferior de Composición & Sostenibilidad (*Limpieza profesional*, *Vapor vertical*, *Almacenamiento*).
  - [x] Vitrina editorial *"COMPLETA EL LOOK ATELIER"* con 3 recomendaciones y CTA de compra completa.
- [x] **T-FE-05**: Implementar componente modal de reserva en boutique (`ModalReservaBoutiqueComponent`):
  - [x] Maquetación fiel a `image_2e295b.png`: tarjeta de prenda seleccionada, selector de boutique con badges de stock, selector de horarios en píldoras, nota de cortesía atelier y botón *"CONFIRMAR RESERVA EN BOUTIQUE"*.
  - [x] Conexión reactiva con `ReservaService` para confirmar la cita.
- [x] **T-FE-06**: Maquetar bloque visual inactivo para Probador AR (CU10):
  - [x] Sección *"SIMULADOR VESTIDOR VIRTUAL & ESCÁNER 3D"* con botón *"INICIAR PROBADOR INTERACTIVO"* y diálogo informativo sin 3D.
- [x] **T-FE-07**: Escribir pruebas unitarias en `producto-detalle.component.spec.ts` y `modal-reserva-boutique.component.spec.ts`:
  - [x] Test de renderizado de galería y ficha técnica.
  - [x] Test de cambio reactivo de talla/color y SKU.
  - [x] Test de apertura del modal de reserva y envío de formulario.
  - [x] Test de retorno con `Location.back()`.
- [x] **T-FE-08**: Ejecutar `ng test` y `ng build` garantizando 0 errores de compilación y pruebas al 100%.

---

## 3. Bloque 3: Mobile Multiplataforma (`Ec-mobile` - Flutter 3.x)

- [x] **T-MO-01**: Crear modelos DTO inmutables en `lib/src/modulos/catalogo/cu07_detalle_producto/datos/modelos/`:
  - [x] `ProductoDetalleDto`, `VarianteDetalleDto`, `ComposicionDto`, `SucursalDisponibilidadDto`.
- [x] **T-MO-02**: Crear modelos DTO de reserva en `lib/src/modulos/reservas/cu12_reservar_prendas/datos/modelos/`:
  - [x] `ReservaPeticionDto`, `ReservaRespuestaDto`.
- [x] **T-MO-03**: Implementar clientes HTTP / Datasources:
  - [x] `ProductoDetalleApi` y `ReservaApi`.
- [x] **T-MO-04**: Implementar BLoCs de estado en `presentacion/bloc/`:
  - [x] `ProductoDetalleBloc` (carga, selección de variante, galería multi-toma, stock).
  - [x] `ReservaBoutiqueBloc` (selección de boutique, franja horaria y envío de reserva).
- [x] **T-MO-05**: Implementar pantalla principal `PantallaProductoDetalle` en `presentacion/pantallas/`:
  - [x] Desplegada a pantalla completa como Hoja (`Navigator.push`) **sin `BottomNavigationBar`**.
  - [x] `AppBar` con botón `← VOLVER` (`leading: IconButton(icon: Icon(Icons.arrow_back), onPressed: () => Navigator.of(context).pop())`) y botón de favoritos.
  - [x] Carrusel de imagen principal con indicador `1/4` y botón flotante en píldora oscura `[ 👁 PROBAR EN AR ]` (CU10 maquetado sin 3D).
  - [x] Fila horizontal deslizable de 4 miniaturas táctiles.
  - [x] Subtítulo de alta costura, SKU dinámico, título principal y precio con descuento.
  - [x] Selectores circulares de color y botones de talla (con estilo tachado para agotadas).
  - [x] Acordeón interactivo `ESPECIFICACIONES & TRAZABILIDAD` (composición de seda natural, técnica de plisado, forro).
  - [x] **Sección integrada de Disponibilidad y Reserva Continua (`image_2e3062.png`)**:
    - Acordeón `Disponibilidad en Boutique` con tarjetas para cada sede (Flagship Serrano, Boutique Saint-Honoré).
    - **Botón directo por sede:** `[ 🏢 RESERVAR EN ESTA BOUTIQUE ]`.
    - Modal BottomSheet para elegir horario y confirmar la reserva presencial.
  - [x] Barra inferior persistente de compra con botón de escaneo y botón *"AÑADIR A LA BOLSA · 890 €"*.
- [x] **T-MO-06**: Escribir pruebas unitarias y de widgets en `test/pantalla_producto_detalle_test.dart`:
  - [x] Test de renderizado sin `BottomNavigationBar` y con botón de regreso.
  - [x] Test de conmutación de variante y actualización de precio/SKU.
  - [x] Test de interacción con botón de reserva por boutique.
- [x] **T-MO-07**: Ejecutar `flutter analyze` y `flutter test` garantizando 0 advertencias y 100% de tests aprobados.
