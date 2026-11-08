# Especificación Técnica Formal: Punto de Venta Presencial (POS de caja)

**ID del Cambio:** `CU31-CU32-punto-de-venta-presencial`
**Casos de Uso:** **CU31** — Registrar venta presencial · **CU32** — Procesar venta presencial y emitir
comprobante (`SI2-Parcial1.md`, Ciclo 2, actor **Cajero**).
**Colisión de numeración:** en el código, `CU31` ya nombra el módulo de reportes por voz
(`comercial/cu31_reportes_voz`, que cubre CU34 + CU35). Este cambio usa siempre el par **CU31-CU32** y el
nombre **punto de venta** para no confundirlos (ver D11).
**Módulos afectados:** `compras_pagos` (backend, nuevo `cu31_cu32_punto_venta`) · `reservas` (servicio de
atención en caja) · `autenticacion_seguridad/cu20` (alta de personal en `empleados`) · Web (nueva pantalla
`/admin/pos`). **Mobile excluido** (el cajero opera en la plataforma Web; `SI2-Parcial1.md` §Actores).
**Depende de:** CU11/CU15 (precios, promociones, cupón, comprobante), CU12/CU13 (reservas y su stock),
CU16 (cobro en caja, `ROLES_CAJA`), CU20 (usuarios cajero), CU28 (consulta de ventas).
**Metodología:** Spec-Driven Development (SDD)
**Nivel SDD:** **3 (alto riesgo)** — mueve inventario, registra pagos y consume cupones; un error duplica o
pierde existencias o dinero.
**Fuente de Verdad de Datos:** PostgreSQL en Neon, verificado por introspección el 2026-11-08.
**Estado:** 🟢 **Especificación aprobada el 2026-11-08** (D1–D11 con las opciones recomendadas; D8
ampliada: el comprobante también se exporta en **PDF**).
**Fecha:** 2026-11-08

---

## 0. Hallazgos previos (verificados contra Neon y el código)

### 0.1 Esquema real

| Tabla | Columnas relevantes | Observación |
| :--- | :--- | :--- |
| `ventas` | `numero_comprobante`, `id_cliente` (nulo), `id_sucursal`, `id_cajero` → **`empleados`**, `id_reserva`, `tipo_venta`, `estado`, `subtotal`, `descuento`, `total`, `id_promocion` | Todo lo que el POS necesita existe. **No hace falta DDL.** |
| `venta_detalle` | `id_variante`, `cantidad`, `precio_unitario`, `subtotal_linea` (**GENERATED**), `id_sucursal` | `subtotal_linea` nunca se inserta (CLAUDE.md). |
| `pagos` | `metodo_pago`, `monto`, `estado`, `referencia_pasarela`, `payload_respuesta` (JSONB), `confirmado_en` | El cambio y el monto recibido caben en `payload_respuesta` sin DDL. |
| `empleados` | `id_empleado` (= `usuarios.id_usuario`), `codigo_empleado`, `fecha_contratacion`, `cargo` | **Solo 8 y 9 (administradores) tienen fila.** El cajero 14 y la encargada 13 **no**: con ellos, `ventas.id_cajero` violaría la clave foránea (D3). |
| `usuarios` | `id_sucursal` | El cajero 14 y la encargada 13 están asignados a la sucursal 1. |
| `clientes` | `id_cliente` (= `usuarios.id_usuario`), datos de perfil | **No existe NIT ni documento de identidad**: se busca por nombre, apellidos o correo (D4). |
| `reservas` / `reserva_detalle` | `estado`, `id_sucursal`, `atendido_por`, `atendido_en` / `id_variante`, `cantidad` | `atendido_por`/`atendido_en` existen y nadie los escribe todavía. |

- Enums: `tipo_venta` incluye `presencial`; `metodo_pago`: `efectivo, tarjeta_debito, tarjeta_credito,
  pasarela_digital, qr, transferencia`; `estado_pago`: `pendiente, autorizado, confirmado, rechazado,
  reembolsado`; `estado_reserva`: `pendiente, confirmada, en_atencion, atendida, cancelada, vencida`;
  `tipo_movimiento_inv` incluye `venta`, `venta_confirmada`, `cancelacion_pedido`, `liberacion_reserva`.
- Comprobantes: secuencia `seq_comprobante_venta`, formato `FS-<AAAA>-<NNNNNN>` (CU15).

### 0.2 Modelo de stock ya establecido en el proyecto (el POS lo respeta)

| Momento | Movimiento | Efecto | Dónde existe hoy |
| :--- | :--- | :--- | :--- |
| Retener al crear la orden | `reserva` (referencia `VENTA-{id}`) | `disponible → reservada` | CU15 `_persistir_lineas_y_retener` |
| Apartar por reserva | `reserva` | `disponible → reservada` | CU12 |
| Cobro confirmado | `venta_confirmada` | `reservada −` (sale del almacén) | CU16 `_consolidar_inventario` |
| Anular orden | `cancelacion_pedido` | `reservada → disponible` | CU15 `liberar_existencias_de_venta` |
| Liberar reserva | `liberacion_reserva` | `reservada → disponible` (fila exacta del movimiento `reserva`) | CU13 `_liberar_stock` |

El documento maestro (CU32, paso 7) describe el descuento mediante el trigger `fn_descontar_inventario_venta`.
**Ese trigger está neutralizado desde la migración 0009** (CLAUDE.md): el movimiento lo ejecuta el servicio.

### 0.3 Estado actual de los datos

- **10 ventas `presencial`** sembradas (prefijo `VTA-`, `id_cajero` 8 o 9). Una, `VTA-2026-000028` (id 33,
  sucursal 2, 2 200,00), está **`pendiente` sin pago**: aparecerá como pendiente de cobro.
- Reservas: 2 `pendiente`, 1 `cancelada`, 8 `vencida`.

### 0.4 Lo que existe hoy en el código

- **No hay POS**: ningún endpoint crea una venta `presencial`, y el cajero que inicia sesión en la web ve
  un panel `/admin` con **«0 Activos»**.
- CU16 ya cobra en caja los **pedidos web en efectivo** con recogida en boutique
  (`POST /admin/pagos/{id}/confirmar-efectivo` y `cancelar-efectivo`, roles `ROLES_CAJA`). Su interfaz está
  en el modal de CU28 (`/admin/ventas-reservas`), **ruta que no admite al cajero** (D10).
- Precios y promociones: `CarritoServicio.calcular_lineas` (CU11) y `CheckoutServicio._resolver_cupon`
  (CU15) operan sobre líneas de carrito; el POS necesita la misma lógica sobre líneas por SKU (plan).
- Bitácora: `ServicioBitacoraAuditoria.registrar_evento_seguro` (CU30), ya usada por CU12/13, CU24, CU27.

---

## 1. Decisiones — aprobadas el 2026-11-08 (opciones recomendadas; D8 ampliada con PDF)

### D1. Cuándo se mueve el stock

| | **Opción A (recomendada)** | Opción B |
| :--- | :--- | :--- |
| **Qué** | **Retener al registrar** (CU31: `disponible → reservada`, movimiento `reserva` con referencia `VENTA-{id}`, como CU15) y **consolidar al cobrar** (CU32: `venta_confirmada`). Anular libera (`cancelacion_pedido`). | Solo **validar** en CU31 y **descontar** de `disponible` al cobrar (lectura literal del documento). |
| **Pro** | Mismo modelo que CU15/CU16: un único significado para cada movimiento. La prenda no se pierde mientras el cliente paga. | Una orden abandonada no bloquea stock. |
| **Contra** | Una orden abandonada retiene stock hasta anularse o vencer (D2). | Otra venta (web o caja) puede llevarse la última unidad entre el registro y el cobro: el cobro fallaría con el cliente delante. |

### D2. Órdenes de caja que nadie cobra

- **Recomendada:** el cajero puede **anular** una orden pendiente con motivo; además, **vencimiento perezoso**:
  una orden POS `pendiente` con más de **2 h** se anula al listar o cobrar, liberando su stock. Mismo patrón
  que CU13 (D1) y CU15.
- Alternativa: solo anulación manual (riesgo de stock retenido indefinidamente).

### D3. El cajero debe existir en `empleados` (`ventas.id_cajero`)

| | **Opción A (recomendada)** | Opción B | Opción C |
| :--- | :--- | :--- | :--- |
| **Qué** | CU20 crea la fila de `empleados` al dar de alta o cambiar a un rol de personal (`cajero`, `encargado_sucursal`, `administrador`), con `codigo_empleado = EMP-<id>`. **Regularización única** para el personal ya existente sin fila (13 y 14). | El POS crea la fila al vuelo si falta. | `id_cajero = NULL`; el responsable solo queda en movimientos y bitácora. |
| **Pro** | La nómina se crea donde se gestiona el personal; CU28 muestra el nombre del cajero. | Sin tocar CU20. | Sin escrituras extra. |
| **Contra** | Toca CU20 (un bloque ya cerrado). | Un módulo de ventas creando registros de personal. | CU28 pierde «cajero» en las ventas presenciales. |

Con A, si aun así un usuario de caja no tiene fila, el POS responde `409 EMPLEADO_NO_REGISTRADO`, sin crear
nada.

### D4. Identificación del cliente

El documento pide buscar por **NIT o correo**, pero `clientes` no tiene NIT.
- **Recomendada:** búsqueda por **correo exacto** de un cliente registrado, o **venta anónima**
  (`id_cliente = NULL`, «venta sin registro previo» del documento). El NIT queda fuera de alcance (requiere DDL).
- Alternativa: añadir `clientes.nit` (DDL, y una nueva migración `0012`).

### D5. Venta que procede de una reserva

- **Recomendada:**
  - Se carga por **código o id de reserva**. Solo si es de la **misma sucursal**, está en `pendiente`,
    `confirmada` o `en_atencion`, no ha vencido (regla perezosa de CU13) y no está ya en otra orden de caja
    pendiente.
  - El cliente de la venta es el de la reserva.
  - El cajero puede **quitar** líneas de la reserva (lo que el cliente no se lleva) y **añadir** prendas nuevas.
  - **Las líneas de la reserva no se retienen otra vez**: ya están en `reservada` desde CU12.
  - **Al cobrar:**
    - lo que se lleva se consolida (`venta_confirmada`) en la **fila exacta** del movimiento `reserva`;
    - lo que se quitó se libera (`liberacion_reserva`);
    - la reserva pasa a **`atendida`**, con `atendido_por` (cajero) y `atendido_en`.
  - **Mientras la orden está pendiente:** la reserva queda en `en_atencion`, estado que CU13 no vence ni deja cancelar (ajuste de implementación del 2026-11-08; sin él, el vencimiento perezoso de CU13 podría liberar su stock con la orden en caja).
  - **Si la orden se anula:** la reserva vuelve a `confirmada`, con su stock apartado.
- Alternativa: carga cerrada (se cobra la reserva tal cual; no se puede quitar ni añadir).

### D6. Métodos de pago

- **Recomendada:** **un método por venta**:
  - **`efectivo`:** monto recibido ≥ total. El servidor calcula el cambio; recibido y cambio se guardan en
    `payload_respuesta`.
  - **`tarjeta_debito` / `tarjeta_credito`:** se cobran en el datáfono físico; referencia de autorización
    obligatoria. Si el datáfono la rechaza, el cajero lo registra: pago **`rechazado`** y la venta sigue
    `pendiente`, como dice el documento.
  - **`qr` / `transferencia`:** referencia obligatoria.
  - `pasarela_digital` no se ofrece en caja.
- Alternativa: **pago mixto** (varios pagos parciales que suman el total).

### D7. Promociones y cupón

- **Recomendada:**
  - **Promociones de catálogo automáticas:** misma lógica que CU11/CU15.
  - **Cupón opcional** introducido por el cajero, con las mismas validaciones que CU15.
  - **Momento de consumo del cupón:** se valida al registrar y se **consume al cobrar**. Así, una orden
    anulada no gasta usos; si entre tanto el cupón se agota, el cobro responde `409 CUPON_AGOTADO`.
- Alternativa: solo promociones de catálogo, sin cupón en caja.

### D8. Comprobante

- **Recomendada:**
  - **Vista imprimible en la web**, con formato de ticket de 80 mm (`window.print`), que también sirve como
    copia digital en pantalla.
  - Datos tomados de `GET /pos/ventas/{id}` y reimprimible desde el listado de ventas del día.
  - Muestra el desglose informativo del IVA incluido (21 %), sin persistirlo (CLAUDE.md).
  - La **factura fiscal** queda fuera de alcance.
- **Aprobado además (2026-11-08): exportación en PDF.** El backend genera el comprobante en PDF con
  `reportlab` (ya en `requirements.txt`), en memoria y con el mismo patrón que `cu31_reportes_voz`
  (`StreamingResponse`, `Content-Disposition: attachment`). Formato de ticket de 80 mm de ancho, con los mismos
  datos que la vista imprimible. Solo para ventas `pagada` o `anulada` (una `pendiente` aún no es comprobante
  definitivo: `409 COMPROBANTE_NO_DISPONIBLE`). Botón «Descargar PDF» en el ticket y en el listado del día.

### D9. Roles y sucursal

- **Recomendada:** los mismos `ROLES_CAJA` que CU16:
  - `cajero` y `encargado_sucursal` operan **solo en su sucursal** (`usuarios.id_sucursal`, fija).
  - `administrador` **elige la sucursal** en el POS.
  - Cliente y proveedor: `403`.
- Alternativa: solo `cajero`.

### D10. Cobro en caja de pedidos web en efectivo (CU16)

- **Recomendada:** el POS incluye una pestaña **«Pedidos web por cobrar»** que reutiliza los endpoints de
  CU16 ya existentes (`confirmar-efectivo` / `cancelar-efectivo`). Así el cajero, que no tiene acceso a CU28,
  puede liquidarlos.
- Alternativa: abrir `/admin/ventas-reservas` (CU28) también al cajero.

### D11. Ubicación y nombres

- **Recomendada:**
  - **Backend:** un único submódulo `app/modules/compras_pagos/cu31_cu32_punto_venta/` con prefijo
    `/api/v1/pos`. Mismo criterio que CU13-CU14: un solo servicio para dos casos de uso acoplados.
  - **Web:** `src/app/modules/compras_pagos/cu31_cu32_punto_venta/`, ruta `/admin/pos`.
  - **Panel:** tarjeta «Punto de Venta» en `/admin` para administrador y encargado, junto a sus módulos.
    El cajero tiene la caja como espacio propio: no ve el panel corporativo (entra directo a `/admin/pos`,
    con su nombre y «Cerrar sesión»).
- Alternativa: dos submódulos `cu31_*` y `cu32_*` (más colisión visual con `cu31_reportes_voz`).

---

## A. Especificación Técnica Formal

*(Redactada con las opciones recomendadas; se ajusta si se aprueba otra.)*

### A.1 Máquina de estados

```text
Venta presencial
  (CU31) registrar ──► pendiente ──(CU32) cobrar: pago confirmado ──► pagada
                          │   └──(CU32) cobro rechazado (tarjeta) ──► pendiente (+ pago «rechazado»)
                          └──── anular / vencer (> 2 h) ──────────► anulada

Reserva cargada en caja
  pendiente | confirmada ──(registrar en caja)──► en_atencion ──(venta pagada)──► atendida
                                                      └──(venta anulada)──► confirmada
```

### A.2 Reglas de negocio (EARS)

1. **[POS-01]** El sistema **siempre** recalculará precio unitario, descuento y total en el servidor;
   cualquier importe enviado por el cliente web se ignora.
2. **[POS-02]** **Cuando** el cajero registre una venta, el sistema bloqueará (`SELECT … FOR UPDATE`) la fila de
   inventario de cada línea nueva en la sucursal del POS y rechazará la operación con `409 STOCK_INSUFICIENTE`
   si `cantidad_disponible` no la cubre, sin crear nada.
3. **[POS-03]** **Cuando** el registro tenga éxito, el sistema creará en una única transacción:
   - la venta `presencial` en estado `pendiente`, con `numero_comprobante` de `seq_comprobante_venta`,
     `id_cajero` e `id_reserva`;
   - sus líneas en `venta_detalle`, con `id_sucursal`;
   - la retención de las líneas nuevas (movimiento `reserva` con referencia `VENTA-{id}`, como CU15, con `id_usuario_responsable`);
  - la reserva cargada, si la hay, pasa a `en_atencion`;
   - el evento de bitácora `POS_REGISTRAR_VENTA`.
4. **[POS-04]** **Mientras** el usuario sea `cajero` o `encargado_sucursal`, el sistema solo operará sobre ventas,
   inventario y reservas de **su** sucursal (`403 SUCURSAL_AJENA`).
5. **[POS-05]** **Cuando** se cargue una reserva, el sistema aplicará primero el vencimiento perezoso de CU13. Rechazará
   la reserva con `409 RESERVA_NO_ATENDIBLE` si está vencida, cancelada, atendida o ya en otra orden de caja
   pendiente, y con `403` si es de otra sucursal.
6. **[POS-06]** **Cuando** se cobre una venta en `efectivo` con monto recibido menor que el total, el sistema responderá
   `422 MONTO_INSUFICIENTE` sin registrar nada.
7. **[POS-07]** **Cuando** el cobro se confirme, el sistema hará en una única transacción:
   - pago `confirmado` con `confirmado_en`, y la venta `pagada`;
   - consumo del cupón;
   - consolidación del stock (`venta_confirmada`; fila exacta del movimiento `reserva` para las líneas de
     reserva);
   - liberación de las líneas de reserva quitadas (`liberacion_reserva`);
   - reserva `atendida`;
   - bitácora `POS_COBRAR_VENTA`.
8. **[POS-08]** **Cuando** el cajero registre un rechazo de tarjeta, el sistema guardará un pago `rechazado` y la venta
   seguirá `pendiente`, sin mover stock.
9. **[POS-09]** **Si** se intenta cobrar o anular una venta que no está `pendiente`, el sistema responderá
   `409 VENTA_NO_PENDIENTE` sin efectos (doble clic o doble pestaña no cobran dos veces).
10. **[POS-10]** **Cuando** se anule una venta (manual con motivo, o por vencimiento de 2 h), el sistema la pasará a
    `anulada`, liberará la retención de sus líneas nuevas (`cancelacion_pedido`) y registrará
    `POS_ANULAR_VENTA`. La reserva vuelve a `confirmada` con su stock apartado.

### A.3 Contratos de API (prefijo `/api/v1/pos`, JWT y `ROLES_CAJA`)

| Método y ruta | Propósito | Respuesta |
| :--- | :--- | :--- |
| `GET /variantes?q=` | Buscar prendas por nombre, categoría o SKU: **todas** las coincidencias (máx. 60), con `categoria_nombre` y el stock de la boutique, agotadas incluidas | lista de variantes · mínimo 2 caracteres |
| `GET /variantes/{sku}` | Buscar una prenda por SKU exacto | `{id_variante, sku, producto, talla, color, imagen_url, precio_lista, precio_final, disponible_en_sucursal}` · `404 SKU_NO_ENCONTRADO` |
| `GET /clientes?q=` | Buscar clientes registrados por nombre, apellidos o correo (máx. 20). Sin coincidencias, la venta es presencial sin cuenta | lista `{id_cliente, nombres, apellidos, email}` · mínimo 2 caracteres |
| `GET /clientes/{id}/reservas` | Reservas del cliente que esta caja puede cargar (`pendiente`/`confirmada`, de esta boutique, no vencibles); solo lectura | lista de reservas · `404 CLIENTE_NO_ENCONTRADO` |
| `GET /cupones?q=` | Cupones vigentes con usos disponibles; sin `q`, todos; con `q`, por código o nombre | lista `{codigo, nombre, descripcion, tipo_descuento, valor_descuento, alcance, fecha_fin, usos_restantes}` |
| `GET /reservas/{codigo_o_id}` | Cargar una reserva | `{id_reserva, codigo, estado, cliente, lineas[{id_variante, sku, producto, talla, color, cantidad}]}` · `403` / `409 RESERVA_NO_ATENDIBLE` |
| `POST /ventas/previsualizar` | Totales sin persistir ni consumir cupón (la web no deriva importes) | `{lineas[], subtotal, descuento, total, iva_incluido, cupon_aplicado}` |
| `POST /ventas` (**CU31**) | Registrar la venta presencial | `201` venta `pendiente` completa |
| `GET /ventas?estado=&fecha=` | Pendientes de cobro y ventas del día | lista de ventas de la sucursal |
| `GET /ventas/{id}` | Detalle y datos del comprobante | venta + pagos + desglose de IVA |
| `POST /ventas/{id}/cobrar` (**CU32**) | Cobrar en caja | venta `pagada` + datos del comprobante (o pago `rechazado`) |
| `POST /ventas/{id}/anular` | Anular una orden pendiente | venta `anulada` |
| `GET /ventas/{id}/comprobante.pdf` | Exportar el comprobante | `application/pdf`, `attachment; filename="<numero_comprobante>.pdf"` · `409 COMPROBANTE_NO_DISPONIBLE` si está `pendiente` |

Cuerpo de `POST /ventas`:
```json
{ "id_sucursal": 1, "id_cliente": 10, "id_reserva": null, "codigo_cupon": null,
  "lineas": [{ "id_variante": 137, "cantidad": 1 }],
  "lineas_reserva_excluidas": [] }
```
`id_sucursal` solo lo envía el administrador; para cajero y encargado se toma de su usuario.

Cuerpo de `POST /ventas/{id}/cobrar`:
```json
{ "metodo_pago": "efectivo", "monto_recibido": "50.00", "referencia": null, "aprobado": true }
```
Respuesta (`efectivo`): `{ …venta, "estado": "pagada", "pago": { "metodo_pago": "efectivo", "monto": "45.00",
"monto_recibido": "50.00", "cambio": "5.00", "estado": "confirmado" } }`. Los importes viajan como cadena
(`Decimal`), igual que en el resto de la API.

### A.4 Interfaz Web (`/admin/pos`)

- **Nueva venta:**
  - buscador de prendas por nombre, categoría o SKU que lista todas las coincidencias mientras se escribe
    (talla, color, precio y stock de la boutique; las agotadas se ven pero no se añaden);
  - cliente por nombre o correo, con todas las coincidencias; sin cuenta, «Venta presencial sin cuenta»;
  - al elegir cliente, sus reservas activas en la boutique con botón «Cargar» (y carga por código como alternativa);
  - cupón opcional: con el campo vacío lista todos los vigentes y al escribir filtra por código o nombre;
  - tabla de líneas con cantidad y botón de quitar.
  - Los totales **siempre** proceden de `previsualizar`. Una prenda sin stock no se añade y se avisa.
- **Cobro:** método de pago, monto recibido (efectivo) o referencia y resultado del datáfono (tarjeta).
  El cambio lo devuelve el servidor.
- **Pendientes de cobro y ventas del día:** cobrar, anular (con motivo) y reimprimir.
- **Pedidos web por cobrar** (D10).
- **Comprobante:** vista de ticket de 80 mm con estilos de impresión y botón **«Descargar PDF»**, que
  descarga el `Blob` de `GET /ventas/{id}/comprobante.pdf`.
- **Reglas de la web:** componentes standalone, `OnPush`, Signals, `@if`/`@for`, importes como `string`, y
  los estados vacío, cargando y error (CLAUDE.md).

### A.5 Criterios de aceptación (Gherkin)

```gherkin
Escenario: Venta directa en efectivo con cambio
  Dado un cajero de la sucursal 1 y la variante 137 con 10 unidades disponibles
  Cuando registra 1 unidad y la cobra en efectivo con 50.00 recibidos (total 45.00)
  Entonces la venta queda «pagada» con comprobante FS-AAAA-NNNNNN y cambio 5.00
  Y la fila de inventario pasa por «venta» (disponible 9, reservada 1) y «venta_confirmada» (reservada 0)

Escenario: Stock insuficiente al registrar
  Cuando registra 11 unidades de una variante con 10 disponibles
  Entonces recibe 409 STOCK_INSUFICIENTE y no se crea venta ni movimiento

Escenario: SKU inexistente
  Cuando busca un SKU que no existe
  Entonces recibe 404 SKU_NO_ENCONTRADO

Escenario: Venta desde reserva quitando una prenda
  Dado una reserva «pendiente» de la sucursal 1 con 2 prendas apartadas
  Cuando la carga, quita una prenda y cobra la otra con tarjeta (referencia AUT-123)
  Entonces la prenda cobrada se consolida en la fila exacta del movimiento «reserva»
  Y la prenda quitada vuelve a disponible con «liberacion_reserva»
  Y la reserva pasa a «atendida» con atendido_por = cajero

Escenario: Reserva de otra sucursal o vencida
  Cuando intenta cargar una reserva de la sucursal 2, o una cuya cita pasó hace más de 2 h
  Entonces recibe 403, o 409 RESERVA_NO_ATENDIBLE, respectivamente

Escenario: Efectivo insuficiente
  Cuando cobra en efectivo 40.00 una venta de 45.00
  Entonces recibe 422 MONTO_INSUFICIENTE y la venta sigue «pendiente»

Escenario: Tarjeta rechazada
  Cuando registra el cobro con tarjeta y «aprobado: false»
  Entonces se guarda un pago «rechazado», la venta sigue «pendiente» y el stock no cambia

Escenario: Doble cobro
  Cuando envía dos veces el cobro de la misma venta
  Entonces el segundo recibe 409 VENTA_NO_PENDIENTE y existe un solo pago confirmado

Escenario: Anular una orden pendiente
  Cuando anula una venta pendiente con motivo
  Entonces queda «anulada», su retención vuelve a disponible con «cancelacion_pedido» y el cupón no se consume

Escenario: Orden olvidada
  Dado una venta POS «pendiente» registrada hace más de 2 h
  Cuando el cajero lista las pendientes
  Entonces aparece «anulada» y su stock ha sido liberado

Escenario: Aislamiento por sucursal
  Cuando un cajero de la sucursal 1 intenta cobrar una venta de la sucursal 2
  Entonces recibe 403 SUCURSAL_AJENA

Escenario: Cajero sin ficha de empleado
  Dado un usuario de caja sin fila en «empleados»
  Cuando registra una venta
  Entonces recibe 409 EMPLEADO_NO_REGISTRADO y no se crea nada

Escenario: Precios autoritativos del servidor
  Cuando la web envía un total manipulado
  Entonces el servidor lo ignora y aplica precio + promociones vigentes

Escenario: Exportar el comprobante en PDF
  Dado una venta presencial «pagada»
  Cuando el cajero pulsa «Descargar PDF»
  Entonces recibe un application/pdf llamado <numero_comprobante>.pdf con líneas, totales, método de pago,
  cambio, IVA incluido y cajero
  Y si la venta está «pendiente» recibe 409 COMPROBANTE_NO_DISPONIBLE

Escenario: Acceso denegado
  Cuando un cliente llama a cualquier endpoint /api/v1/pos
  Entonces recibe 403
```

### A.6 Riesgos

| Riesgo | Mitigación |
| :--- | :--- |
| Doble movimiento de stock en líneas de reserva (se retienen dos veces) | Las líneas de reserva **nunca** pasan por la retención de CU31; se consolidan sobre la fila del movimiento `reserva` (patrón de CU13). Pruebas de saldos fila a fila. |
| Doble cobro por concurrencia | `FOR UPDATE` sobre la venta y comprobación de estado `pendiente` en la misma transacción. |
| Cupón agotado entre registro y cobro | `409 CUPON_AGOTADO`; el cajero puede anular y registrar sin cupón. |
| Seguridad: un cajero opera otra sucursal | Alcance derivado del usuario en el servidor, nunca del cuerpo de la petición (salvo el administrador). |
| Los tests en verde con la sesión mockeada no prueban el contrato | Verificación end-to-end contra Neon con una venta directa y una desde reserva (CLAUDE.md). |

### A.7 Fuera de alcance

Factura fiscal, NIT de cliente, pago mixto (salvo que se apruebe), devoluciones de ventas pagadas, arqueo y
cierre de caja, impresión directa a impresora térmica (se usa el diálogo de impresión del navegador), y la app
móvil.
