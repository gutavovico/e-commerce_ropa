# Plan de Implementación: CU13 — Consultar y Cancelar Reservas

Referencia normativa: `spec.md` de este directorio. Este plan asume las **opciones recomendadas** de
§1 (D1-A, D2, D3, D4, D5); si alguna cambia, se ajusta antes de escribir código.

Orden de ejecución con gate entre bloques (constitución del proyecto): **Backend → Web → Mobile**.

---

## Bloque 1 — Backend (`Ec-backend`)

### 1.1 Estructura

```
app/modules/reservas/cu13_consultar_cancelar_reservas/
    __init__.py
    esquemas.py      # ReservaOut, ReservaItemOut, SucursalReservaOut, MisReservasOut, ResumenReservasOut, ReservaCancelarIn
    repositorio.py   # consultas y bloqueos; sin lógica de negocio
    servicio.py      # listar_mis_reservas, cancelar_reserva, _vencer_si_corresponde, _liberar_stock
    router.py        # GET /reservas/mias, POST /reservas/{id_reserva}/cancelar
app/modules/reservas/router.py   # incluir el router nuevo ANTES de cualquier /reservas/{id}
```

Modelos: `ReservaORM`/`ReservaDetalleORM` viven en `comercial/cu28_ventas_reservas/modelos.py` y se
reexportan desde `reservas/modelos.py`; se **reutilizan**, no se redeclaran (tabla duplicada →
`InvalidRequestError`). `MovimientoInventarioORM` e `InventarioSucursalORM`, igual.

### 1.2 Piezas

- **Constantes** (`servicio.py`): `ESTADOS_CANCELABLES = ("pendiente", "confirmada")`,
  `TOLERANCIA_VENCIMIENTO = timedelta(hours=2)` (D1), `MOTIVO_VENCIMIENTO = "Vencida sin atención"`.
- **Código de reserva:** extraer a una función compartida el formato `RES-{año}-{id:04d}` que hoy
  está incrustado en `ReservaServicio.crear_reserva_presencial`, y usarla desde CU12 y CU13 (sin
  duplicar la regla).
- **`listar_mis_reservas(db, usuario)`**
  1. Cargar las reservas con `id_cliente == usuario.id_usuario` (`selectinload` de detalles → variante
     → producto/talla/color, y sucursal).
  2. Para cada `pendiente`/`confirmada` con `fecha_hora_atencion + tolerancia < ahora` →
     `_vencer_si_corresponde` (bloquea la cabecera, revalida, libera stock, `estado='vencida'`).
     Un único `COMMIT` si hubo cambios.
  3. Separar en `proximas` (pendiente/confirmada/en_atencion, orden ascendente) e `historial`
     (resto, orden descendente); calcular `resumen` y `puede_cancelar` en el servidor.
- **`cancelar_reserva(db, usuario, id_reserva, motivo)`** — secuencia exacta de `spec.md` §A.2.
- **`_liberar_stock(db, reserva, usuario, observacion)`** — compartido por cancelar y vencer:
  por cada línea, movimiento `reserva` → `id_inventario` → fila `FOR UPDATE` → validar
  `cantidad_reservada >= n` → mover unidades → movimiento `liberacion_reserva` con saldos reales.
- **Repositorio:** `buscar_reservas_de_cliente`, `obtener_reserva_para_actualizar` (`FOR UPDATE`),
  `buscar_movimiento_reserva(id_reserva, id_variante)` (join a `inventario_sucursal` para filtrar por
  variante), `obtener_inventario_por_id` (`FOR UPDATE`), `registrar_movimiento_liberacion`.
- **Bitácora:** `CANCELAR_RESERVA` (y `VENCER_RESERVA` para el perezoso) vía
  `ServicioBitacoraAuditoria.registrar_evento_seguro`, como hace CU12.
- **Errores:** `NotFoundError`, `AuthorizationError`, `ConflictError` de `core/errors.py`; el
  servicio no importa `fastapi`.

### 1.3 Pruebas (`tests/modules/reservas/test_cu13_consultar_cancelar.py`)

Un test por escenario Gherkin, más:
- La fila liberada es la del movimiento de CU12 aunque exista otra temporada con más stock.
- `cantidad_reservada` insuficiente → `409` y ningún cambio.
- Una reserva ya vencida no se vuelve a liberar al listar de nuevo (idempotencia del perezoso).
- `GET /reservas/mias` no expone reservas de otro cliente.

**Verificación end-to-end contra Neon** en transacción revertida: crear una reserva real con CU12,
cancelarla con CU13, comprobar saldos y movimientos; y listar para confirmar que las 9 reservas
vencidas actuales se reportarían como `vencida` con su stock liberado (sin persistir).

---

## Bloque 2 — Web (`Ec-frontend`)

### 2.1 Estructura

```
src/app/modules/reservas/cu13_consultar_cancelar_reservas/
    modelos/reserva.model.ts                 # espejo de ReservaOut/MisReservasOut; importes como string
    servicios/mis-reservas.service.ts        # Signals: misReservas, cargando, cancelando, error
    paginas/mis-reservas.component.{ts,html,spec.ts}
    componentes/modal-cancelar-reserva.component.{ts,html,spec.ts}
```

### 2.2 Navegación (Hub-and-Spoke)

- Ruta nueva `reservas` al **nivel raíz** de `app.routes.ts` (hoja, fuera de `MainLayoutComponent`),
  con `authGuard`, antes del comodín `**`. Cabecera propia con `← Volver` vía `Location.back()`.
- Actualizar `app.routes.spec.ts` para cubrir la ruta nueva y conservar el orden (landing antes del
  layout, comodín al final).

### 2.3 Tarjeta del Perfil (sustituye «Bolsa de Compra»)

En `perfil.component.html` (líneas ~260-285), misma anatomía que la tarjeta vecina «Wishlist»:

| Elemento | Contenido |
| :--- | :--- |
| Icono | Calendario, sobre el cuadro negro (`primary`) que hoy lleva la bolsa |
| Eyebrow | `CITAS DE PROBADOR` |
| Título | `Mis Reservas` |
| Subtítulo | `{activas} reservas activas · Próxima: {fecha} en {sucursal}`; sin activas: `Sin citas agendadas` |
| Botón | `VER MIS RESERVAS` → `routerLink="/reservas"` |

Los datos salen de `resumen` de `GET /reservas/mias` (servicio de CU13 inyectado en el Perfil). Se
elimina el literal «3 Artículos seleccionados · 1.250 €». Mientras carga: skeleton en el subtítulo;
si falla: el subtítulo se oculta pero el botón sigue funcionando.

### 2.4 Pantalla «Mis Reservas» (`/reservas`)

Lenguaje visual de la página *Mi Cuenta* actual (tarjetas blancas `rounded-3xl`, borde
`neutral-100`, Outfit, eyebrows en mayúsculas espaciadas, botones negros `rounded-2xl`):

1. **Cabecera:** `← Volver` · chip `CITAS PRIVADAS DE PROBADOR` · título `Mis Reservas` ·
   subtítulo con el recuento de activas.
2. **Selector segmentado:** `Próximas` / `Historial`.
3. **Tarjeta de reserva:**
   - Fila superior: `codigo_reserva` + badge de estado.
   - Bloque de cita: fecha grande (`jueves 2 de octubre`), hora, y sucursal con dirección.
   - Rejilla de prendas: miniatura, nombre, `Talla · Color` (con muestra de `color_hex`), cantidad.
   - Nota del cliente (`observacion`), si existe.
   - Pie: `Cancelar reserva` (botón contorneado en tono de error) **solo si `puede_cancelar`**.
4. **Modal de cancelación:** resumen (código, fecha, sucursal), `textarea` de motivo obligatorio
   (3-250, contador), botones `Mantener reserva` / `Confirmar cancelación` (este último deshabilitado
   mientras `cancelando()`). Tras el `200`, el servicio **reemplaza su estado con la respuesta del
   servidor** y muestra el aviso «Reserva cancelada. Las prendas vuelven a estar disponibles en
   {sucursal}.»
5. **Estados obligatorios:** skeleton, vacío (`Aún no tienes citas de probador` + `EXPLORAR CATÁLOGO`
   → `/catalogo`), error con reintento, y traducción de `403/404/409/422` a mensajes legibles usando
   el `detail` del backend.

**Badges de estado** (HEX de `fashionstore-tokens.md`, porque el Tailwind por CDN no define los
tokens de color semánticos; espaciados con `space-*`):

| Estado | Fondo | Texto | Etiqueta |
| :--- | :--- | :--- | :--- |
| `pendiente` | `surface-container` `#EDEEF0` | `on-surface-variant` `#45474A` | Pendiente de confirmación |
| `confirmada` | `secondary-container` `#ECDECB` | `on-secondary-container` `#6B6152` | Confirmada |
| `en_atencion` | `primary-container` `#1B1C1D` | `#FFFFFF` | En atención |
| `atendida` | `surface-container-high` `#E8E8EA` | `on-surface` `#1A1C1D` | Atendida |
| `cancelada` | `error-container` `#FFDAD6` | `on-error-container` `#93000A` | Cancelada |
| `vencida` | `surface-dim` `#D9DADC` | `outline` `#75777A` | Vencida |

Reglas de la constitución: standalone, `OnPush`, Signals, `inject()`, `@if/@for` con `track`.

### 2.5 Pruebas

Vitest vía `ng test` (nunca `npx vitest`), con **payloads literales copiados del backend**:
servicio (listar, cancelar, errores), página (estados, pestañas, botón visible solo con
`puede_cancelar`), modal (validación del motivo, doble clic) y tarjeta del Perfil (sin literales
inventados, estado sin reservas).

---

## Bloque 3 — Mobile (`Ec-mobile`)

### 3.1 Estructura

```
lib/src/modulos/reservas/cu13_consultar_cancelar_reservas/
    datos/modelos/reserva_dto.dart              # fromJson tolerante (parsearImporte para precios)
    datos/datasources/reservas_api.dart         # 401 → SesionManager, errores → ReservaException
    presentacion/bloc/mis_reservas_bloc.dart    # ChangeNotifier + sealed: Inicial, Cargando, Listo, Cancelando, Error
    presentacion/pantallas/pantalla_mis_reservas.dart
    presentacion/widgets/hoja_cancelar_reserva.dart   # bottom sheet con motivo obligatorio
```

### 3.2 Navegación y UI

- En `pantalla_perfil.dart` (líneas ~679-717) la tarjeta negra «BOLSA · 3 · Artículos · 1.250 € ·
  IR AL CHECKOUT →» pasa a «RESERVAS · {activas} · Próxima: {fecha} · VER MIS RESERVAS →», con
  `onTap` → `Navigator.push(PantallaMisReservas(token: widget.token))`.
- `PantallaMisReservas`: hoja del patrón Hub-and-Spoke → `AppBar` con `leading: BackButton()` y
  **sin** `bottomNavigationBar`. `TabBar` Próximas/Historial, tarjetas equivalentes a las de Web,
  `RefreshIndicator`, estados vacío/error/carga.
- Textos variables con `Expanded` + `TextOverflow.ellipsis` (regla de `CLAUDE.md` contra
  `RenderFlex overflowed`), nunca reduciendo fuentes.
- Tokens de `fashionstore-mobile-sdd/references/fashionstore-tokens.md`.

### 3.3 Pruebas

`pago_dto_test`-style: DTO desde payload literal del backend; BLoC (listar, cancelar, 409, 401);
widget (sin `BottomNavigationBar`, `BackButton`, botón de cancelar solo si `puede_cancelar`, hoja con
motivo obligatorio). Viewport agrandado en los widget tests. `dart analyze` → «No issues found!».

---

## Documentación al cerrar cada bloque

- `tasks.md` y `checkpoint.md` de este directorio.
- `CHANGELOG.md` y `.specs/CHANGELOG.md`: entrada nueva para la retención indefinida de stock por
  reservas vencidas (defecto real, §0.3) y para la eliminación de los literales inventados de la
  tarjeta del Perfil (§0.4).

## Fuera de alcance (se señala, no se toca)

- Resto de datos inventados del Perfil: «32 Visitas registradas», «4 Boutiques (Madrid, París,
  Milán, Londres)», «100% Seda & Lana», «Nivel Platino», «12 Prendas guardadas».
- Transiciones de tienda (`confirmada`, `en_atencion`, `atendida`) y cancelación desde CU28.
- Proceso programado (cron) de vencimiento: sigue siendo la decisión pendiente global del proyecto.
