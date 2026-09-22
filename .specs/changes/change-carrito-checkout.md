# Propuesta de Cambio Técnico: Bolsa de Compra y Checkout

**ID del Cambio:** `change-carrito-checkout`
**Módulos Afectados:** `compras_pagos` (nuevo paquete de dominio) · `catalogo` · `reservas`
**Casos de Uso:**
- **CU11** — Gestionar carrito de compras (alta, modificación de cantidades y eliminación de líneas)
- **CU15** — Comprar desde la plataforma (consolidación de orden, tipo de entrega, descuentos y venta en estado `pendiente`)

**Metodología:** Spec-Driven Development (SDD) & Proceso Unificado de Desarrollo de Software (PUDS)
**Nivel SDD:** **3 (alto riesgo)** — toca inventario, transacciones monetarias y concurrencia. Exige sección de riesgos, transacciones explícitas y pruebas de concurrencia; ningún gate puede omitirse.
**Fuentes de Verdad Visuales:** `image_046d3e.png` (Web, dos columnas) · `image_046a5d.png` (Mobile, vertical con footer fijo)
**Fuente de Verdad de Datos:** **La base de datos PostgreSQL desplegada en Neon**, verificada por introspección el 2026-09-22. No `alembic/versions/0001_base_ddl.py`, que no refleja el esquema real (ver §0.1).
**Estado:** 🟢 LOS 3 BLOQUES IMPLEMENTADOS Y VERIFICADOS (Backend · Web · Mobile)
**Fecha:** 2026-09-22

> **Gate de especificación superado el 2026-09-22.** Se aprobaron las cuatro decisiones
> recomendadas de §1 y se autorizó la ejecución del Bloque 1. Las migraciones `0009` (DDL) y
> `0010` (semilla de promociones) están aplicadas sobre Neon; `alembic_version` avanzó a `0010`.
>
> **Verificación del Bloque 1:** `pytest` **158/158** en verde, más una verificación end-to-end
> contra la base real (sin mocks) que recorre bolsa → modificación → eliminación → checkout con
> cupón → retención de existencias → liberación, y deja la base en su estado original.
> Resultados en §E.

---

## Índice

- [0. Hallazgos previos que condicionan el alcance](#0-hallazgos-previos-que-condicionan-el-alcance)
- [1. Decisiones bloqueantes que requieren tu autorización](#1-decisiones-bloqueantes-que-requieren-tu-autorización)
- [A. Especificación Formal Técnica (`spec`)](#a-especificación-formal-técnica-spec)
- [B. Plan de Ejecución Secuencial por Bloques (`plan`)](#b-plan-de-ejecución-secuencial-por-bloques-plan)
- [C. Lista de Tareas Atómicas (`tasks`)](#c-lista-de-tareas-atómicas-tasks)
- [D. Puntos de Control y Verificación (`checkpoints`)](#d-puntos-de-control-y-verificación-checkpoints)

---

## 0. Hallazgos previos que condicionan el alcance

Antes de especificar se inspeccionó el esquema real de Neon y el código existente. Tres hallazgos
alteran el planteamiento de partida y deben resolverse antes de escribir una línea de código.

### 0.1 La migración de Alembic no es fuente de verdad

`alembic/versions/0001_base_ddl.py` describe un esquema que no es el desplegado. Ya provocó una
caída completa de catálogo, búsqueda y colecciones (defecto 34 del `CHANGELOG.md`). **Toda esta
especificación se construye sobre la introspección directa de la base de datos**, cuyo resultado se
transcribe literalmente en §A.1. Cualquier suposición tomada de la migración o del PDF debe
verificarse contra la base antes de implementarse.

### 0.2 «Añadir a la bolsa» no está implementado

El enunciado parte de que la adición desde el detalle ya existe. **No es así.** Hoy es un
incremento de un contador en memoria seguido de un aviso visual:

| Plataforma | Ubicación | Comportamiento real |
| :--- | :--- | :--- |
| Mobile | `producto_detalle_bloc.dart:376-383` | `bolsaContador + 1` y mensaje *«Prenda añadida a la bolsa de compras»* |
| Web | `producto-detalle.component.ts:292-298` | Notificación *«✓ Añadido a la bolsa: …»* |

No existe módulo `carrito` en el backend, ningún endpoint `/api/v1/carrito`, ningún servicio de
carrito en Angular ni BLoC de carrito en Flutter. Las tablas `carritos` y `carrito_detalle` tienen
**0 filas**.

**Consecuencia sobre el alcance:** CU11 debe incluir necesariamente `POST /api/v1/carrito/items` y
la reconversión de ambos botones «Añadir a la bolsa» a llamadas reales persistentes. Sin ello la
pantalla de Bolsa de Compra no tendría nunca contenido que mostrar. Queda incorporado al plan
(tareas `T-BE-05`, `T-FE-07`, `T-MO-07`).

### 0.3 Los datos de los mockups no existen en la base

| Elemento del mockup | Realidad en Neon |
| :--- | :--- |
| `Boutique Saint-Honoré, París` | No existe |
| `Hub Central Madrid` | No existe |
| Sucursales reales (4) | `Atelier Serrano - Madrid`, `Boutique Central - Santa Cruz`, `Boutique Central Equipetrol`, `Tienda de preuba78548` |
| `Beneficio Membresía Privé −160,00 €` | `promociones` tiene **0 filas**; no hay ninguna promoción ni cupón que aplicar |
| `Ana Valenzuela · Calle de Claudio Coello 48` | No existe almacenamiento de direcciones de envío (ver §1.3) |

La regla de dominio «cero datos inventados» del skill de backend prohíbe rellenar estos huecos con
literales. Los mockups se respetan como **estructura visual y jerarquía tipográfica**, pero el
contenido debe provenir de la base. Donde la base no tenga datos, la pantalla muestra su estado
vacío correspondiente, no un valor fabricado.

> **Acción derivada:** para que el cupón y el descuento sean demostrables hace falta sembrar al
> menos una promoción real. Se propone una migración de *seed* (`0004_seed_promociones.py`)
> incluida como tarea `T-BE-10`. Es una inserción de datos, no un cambio de esquema.

### 0.4 El trigger de inventario es incompatible con el checkout propuesto

En la base real existe `trg_descontar_inventario`, `AFTER INSERT ON venta_detalle`, que ejecuta:

```sql
SELECT inv.id_inventario INTO v_id_inventario
FROM fashionstore.inventario_sucursal inv
JOIN fashionstore.ventas v ON v.id_venta = NEW.id_venta
WHERE inv.id_variante = NEW.id_variante
  AND inv.id_sucursal = v.id_sucursal      -- sucursal de la CABECERA
LIMIT 1;                                    -- sin filtrar id_temporada

IF v_id_inventario IS NULL THEN
    RAISE EXCEPTION 'No existe inventario para la variante % en la sucursal de la venta %', …;
END IF;

UPDATE fashionstore.inventario_sucursal
SET cantidad_disponible = cantidad_disponible - NEW.cantidad
WHERE id_inventario = v_id_inventario;
```

Cuatro problemas, en orden de gravedad:

1. **Rompe el carrito multi-sucursal.** Busca el inventario en la sucursal de la *cabecera* de la
   venta. El mockup muestra tres prendas expedidas desde tres sucursales distintas; en cuanto una
   variante no tenga inventario en la sucursal elegida para la cabecera, el trigger lanza
   `RAISE EXCEPTION` y **aborta la transacción completa de checkout**.
2. **Descuenta stock en una venta `pendiente`.** Dispara en el `INSERT`, sin consultar
   `ventas.estado`. Una orden nunca pagada deja stock descontado de forma indefinida, sin
   mecanismo de compensación. Es el riesgo n.º 1 ya registrado en `dominio.md §5`.
3. **`LIMIT 1` sin `id_temporada`.** La clave única de `inventario_sucursal` es
   `(id_variante, id_sucursal, id_temporada)`; con existencias en dos temporadas elige una fila
   arbitraria. Es el mismo defecto corregido en CU12 (defecto 36 del `CHANGELOG.md`).
4. **No valida suficiencia ni responsable.** Puede dejar `cantidad_disponible` en negativo y
   escribe en `movimientos_inventario` sin `id_usuario_responsable`, rompiendo la trazabilidad
   exigida por la constitución de backend.

Además contradice la regla arquitectónica *«toda variación de stock se escribe en
`movimientos_inventario` dentro de la misma transacción»* ejecutada **desde el servicio**, que es
como ya opera CU12 (`ReservaServicio`).

---

## 1. Decisiones bloqueantes que requieren tu autorización

Son cambios de esquema o de reglas de inventario; la constitución de backend los clasifica como
*Ask First*. **No se implementará ninguno sin tu visto bueno explícito.**

### 1.1 Qué hacer con `trg_descontar_inventario`

| | Opción A — **Recomendada** | Opción B | Opción C |
| :--- | :--- | :--- | :--- |
| **Qué** | Reemplazar la función para que no descuente en `INSERT`. El movimiento de stock pasa al servicio, igual que CU12. | Mantener el trigger y forzar carritos de **una sola sucursal**. | Emitir **una venta por sucursal** de expedición. |
| **Multi-sucursal** | ✅ Sí | ❌ No | ⚠️ Sí, pero N órdenes |
| **Stock en venta pendiente** | Retención explícita y reversible | Descuento firme prematuro | Descuento firme prematuro |
| **Impacto en CU16 (pagos)** | Ninguno | Ninguno | Alto: un pago por venta |
| **Fidelidad al mockup** | Total | Ninguna | Parcial |
| **Cambio de esquema** | Sí (reemplazo de función) | No | No |

**Recomendación: Opción A.** Deja el control del inventario en la capa de servicio, que es donde la
arquitectura lo exige y donde CU12 ya lo tiene resuelto y probado. Las demás opciones o contradicen
el diseño visual aprobado o trasladan complejidad a CU16.

### 1.2 Cómo preservar la sucursal de expedición por línea

`carrito_detalle` **sí** tiene `id_sucursal`; `venta_detalle` **no**. Al convertir carrito → venta
se pierde de qué boutique sale cada prenda, dato que el mockup muestra en cada tarjeta
(*«Expedición desde: …»*) y que logística necesita.

**Propuesta:** `ALTER TABLE fashionstore.venta_detalle ADD COLUMN id_sucursal INTEGER
REFERENCES fashionstore.sucursales(id_sucursal);` — aditiva, nullable, sin reescritura de datos
(las tablas están vacías). `ventas.id_sucursal` (NOT NULL) pasa a significar **sucursal
responsable de la orden**: la de mayor importe de la bolsa, o la de recogida si el cliente eligió
Click & Collect.

### 1.3 Dónde guardar tipo de entrega y dirección

`ventas` no tiene ninguna columna para esto. Se necesitan cuatro campos aditivos:

```sql
ALTER TABLE fashionstore.ventas
  ADD COLUMN tipo_entrega VARCHAR(20) NOT NULL DEFAULT 'domicilio',  -- domicilio | recogida_boutique
  ADD COLUMN id_sucursal_retiro INTEGER NULL REFERENCES fashionstore.sucursales(id_sucursal),
  ADD COLUMN direccion_envio TEXT NULL,
  ADD COLUMN id_promocion INTEGER NULL REFERENCES fashionstore.promociones(id_promocion);
```

`id_promocion` da trazabilidad del cupón aplicado, hoy imposible: `ventas.descuento` guarda el
importe pero no su origen.

> **Alternativa sin tocar el esquema:** no persistir el tipo de entrega y tratarlo como dato de
> presentación. Se desaconseja: la orden dejaría de ser reproducible y CU16 no sabría si debe
> cobrar envío ni a dónde despachar.

### 1.4 Qué garantiza realmente el temporizador de stock

El mockup promete *«Las prendas reservadas en tu bolsa se mantienen garantizadas durante 24:06 min»*.

**Propuesta para este ciclo:** el temporizador de la **bolsa** es **informativo**, derivado de
`carrito_detalle.agregado_en + 25 min`, y no retiene stock. La retención real —y verificada contra
inventario— ocurre en el **checkout**, moviendo unidades de `cantidad_disponible` a
`cantidad_reservada`, con vencimiento en `ventas.fecha_venta + 25 min`.

Razón: retener stock por cada prenda que alguien deje en una bolsa abandonada agota el inventario
sin contrapartida y exige un proceso de expiración (cron o *lazy*) que hoy no existe —riesgo n.º 7
de `dominio.md`, aún abierto—. El texto de la interfaz debe ajustarse para no prometer una garantía
que el sistema no da todavía; se propone *«Stock verificado en tiempo real»* en la bolsa y la
garantía firme con cuenta atrás una vez tramitado el pedido.

**Si prefieres la retención desde la bolsa**, dímelo: implica especificar además el proceso de
liberación por expiración, lo que amplía el alcance de este cambio.

### 1.5 Liberación de la retención (dependencia con CU16)

Al tramitar el pedido el stock queda retenido. Debe liberarse cuando:

- el pago se confirma → `cantidad_reservada -= n`, movimiento `venta_confirmada` (**CU16**);
- el pago se rechaza o expiran los 25 min → `cantidad_reservada -= n`,
  `cantidad_disponible += n`, movimiento `cancelacion_pedido`.

CU16 no está en este alcance. **Se propone entregar en este ciclo el servicio de liberación
(`liberar_retencion_venta`) junto con su endpoint administrativo y sus pruebas**, de modo que CU15
no deje inventario bloqueado sin salida. La invocación automática por expiración queda pendiente de
decidir (cron vs. verificación perezosa).

---

## A. Especificación Formal Técnica (`spec`)

### A.1 Esquema real verificado (introspección Neon, 2026-09-22)

```
carritos            id_carrito PK · id_cliente · creado_en · actualizado_en
carrito_detalle     id_carrito_detalle PK · id_carrito · id_variante · id_sucursal · cantidad(def 1) · agregado_en
ventas              id_venta PK · numero_comprobante · id_cliente · id_sucursal(NOT NULL) · id_cajero ·
                    id_reserva · tipo_venta · estado(def 'pendiente') · subtotal(def 0) · descuento(def 0) ·
                    total(def 0) · fecha_venta
venta_detalle       id_venta_detalle PK · id_venta · id_variante · cantidad · precio_unitario ·
                    subtotal_linea  ← GENERATED ALWAYS AS (cantidad * precio_unitario)
inventario_sucursal id_inventario PK · id_variante · id_sucursal · id_temporada ·
                    cantidad_disponible · cantidad_reservada · stock_minimo · estado · stock_alerta
promociones         id_promocion PK · nombre · porcentaje_descuento · fecha_inicio · fecha_fin ·
                    estado_activo · codigo_cupon · tipo_descuento(def 'porcentaje') · valor_descuento ·
                    tope_descuento · limite_usos · usos_actuales · alcance(def 'global') ·
                    id_categoria · id_producto
```

**Enums vigentes:**

| Enum | Valores |
| :--- | :--- |
| `tipo_venta` | `presencial` · `digital_web` · `digital_movil` |
| `estado_venta` | `pendiente` · `pagada` · `anulada` · `devuelta` |
| `tipo_movimiento_inv` | `ingreso_proveedor` · `reserva` · `liberacion_reserva` · `venta` · `devolucion` · `ajuste` · `transferencia_salida` · `transferencia_entrada` · `ajuste_positivo` · `ajuste_negativo` · `venta_confirmada` · `cancelacion_pedido` |

> ⚠️ **Deuda a corregir en este ciclo (sin cambio de esquema):** el enum declarado en
> `Ec-backend/app/modules/reservas/modelos.py` sólo lista 8 de los 12 valores. Escribir
> `venta_confirmada` o `cancelacion_pedido` fallaría en la validación de SQLAlchemy. Tarea `T-BE-01`.

> ⚠️ `venta_detalle.subtotal_linea` es **GENERATED ALWAYS**. El ORM debe mapearla como sólo lectura
> (`Mapped[Decimal] = mapped_column(..., server_default=FetchedValue())` sin incluirla en `INSERT`),
> o PostgreSQL rechazará la escritura.

### A.2 Modelo financiero

La semántica de los tres campos de `ventas` se fija así (el mockup es internamente inconsistente:
rotula «Subtotal artículos 1.940,00 €» y luego resta otros 160 € para totalizar los mismos 1.940 €):

| Campo | Definición | Ejemplo del mockup |
| :--- | :--- | :--- |
| `subtotal` | Σ (`precio_unitario` de lista × `cantidad`), **sin descuentos** | 2.100,00 € |
| `descuento` | Σ descuentos por promoción vigente + cupón aplicado | 160,00 € |
| `total` | `subtotal − descuento` | 1.940,00 € |
| IVA (21 %) | **Sólo presentación.** `total − total / 1,21`. No se persiste: los precios ya lo incluyen | 336,69 € |

- Todo importe es `Decimal`/`NUMERIC`. **Prohibido `float`.**
- `precio_unitario` se **congela** en `venta_detalle` al tramitar. Los cambios de precio posteriores
  no alteran órdenes ya emitidas.
- El servidor recalcula siempre. **Cualquier importe enviado por el cliente se ignora.**

### A.3 Contratos de API

Todos bajo `/api/v1`, con `Authorization: Bearer <jwt>` y rol `cliente`. Errores con el contrato
`{"detail", "code"}` ya vigente.

---

#### `GET /api/v1/carrito`

Devuelve el carrito activo del cliente autenticado, creándolo vacío si no existe.

```jsonc
{
  "id_carrito": 12,
  "items": [
    {
      "id_carrito_detalle": 44,
      "id_variante": 102,
      "id_producto": 1,
      "nombre_producto": "Vestido Plisado en Seda Marfil Natural",
      "linea_confeccion": "ALTA COSTURA",
      "sku": "ATEL-2025-V09-IV-38",
      "talla_codigo": "38",
      "color_nombre": "Seda Marfil",
      "color_hex": "#F5F0EA",
      "imagen_url": "https://…",
      "precio_lista": "1050.00",
      "precio_unitario": "890.00",
      "descuento_linea": "160.00",
      "motivo_descuento": "Membresía Privé",
      "cantidad": 1,
      "id_sucursal": 1,
      "nombre_sucursal": "Atelier Serrano - Madrid",
      "stock_disponible": 2,
      "cantidad_maxima": 2
    }
  ],
  "resumen": {
    "total_prendas": 3,
    "subtotal": "2100.00",
    "descuento": "160.00",
    "total": "1940.00",
    "iva_incluido": "336.69",
    "moneda": "EUR"
  },
  "expira_en": "2026-09-22T10:25:00Z",
  "sucursales_expedicion": [{ "id_sucursal": 1, "nombre": "Atelier Serrano - Madrid", "total_lineas": 2 }]
}
```

- `cantidad_maxima` = `inventario_sucursal.cantidad_disponible` de la temporada vigente, para que el
  botón `+` se deshabilite en el cliente sin una llamada extra.
- `stock_disponible` se consulta **en cada petición**: el stock pudo cambiar desde que se añadió.
- Carrito vacío → `200 OK` con `items: []` y `resumen` en ceros. **Nunca 404.**

| Código | Situación |
| :--- | :--- |
| `200` | Carrito devuelto (con o sin líneas) |
| `401` | Sin sesión válida |

---

#### `POST /api/v1/carrito/items`

Añade una variante. Si la variante ya está en el carrito **para la misma sucursal**, suma
cantidades en lugar de duplicar la línea.

```jsonc
// Petición
{ "id_variante": 102, "cantidad": 1, "id_sucursal": 1 }
```

- `id_sucursal` es opcional: si se omite, el servicio elige la sucursal con mayor
  `cantidad_disponible` para esa variante en la temporada vigente.
- Respuesta: el carrito completo (mismo contrato que `GET /api/v1/carrito`), para que el cliente
  refresque de una sola vez.

| Código | Situación |
| :--- | :--- |
| `201` | Añadido |
| `404` | `VARIANTE_NO_ENCONTRADA` / `SUCURSAL_NO_ENCONTRADA` |
| `409` | `STOCK_INSUFICIENTE` — la cantidad resultante supera lo disponible |
| `422` | `cantidad < 1` |

---

#### `PATCH /api/v1/carrito/items/{id_carrito_detalle}`

Fija la cantidad de una línea (valor absoluto, no incremento: hace la operación idempotente y
segura ante doble pulsación de `+`).

```jsonc
{ "cantidad": 2 }
```

| Código | Situación |
| :--- | :--- |
| `200` | Carrito actualizado (contrato de `GET /api/v1/carrito`) |
| `403` | `CARRITO_AJENO` — la línea pertenece a otro cliente |
| `404` | `LINEA_NO_ENCONTRADA` |
| `409` | `STOCK_INSUFICIENTE` — incluye `disponible` y `solicitada` en el mensaje |
| `422` | `cantidad < 1` (para eliminar se usa `DELETE`, no `cantidad: 0`) |

---

#### `DELETE /api/v1/carrito/items/{id_carrito_detalle}`

| Código | Situación |
| :--- | :--- |
| `200` | Eliminada; devuelve el carrito recalculado |
| `403` | `CARRITO_AJENO` |
| `404` | `LINEA_NO_ENCONTRADA` |

---

#### `POST /api/v1/ventas/checkout`

Convierte el carrito en venta formal. **Transacción única.**

```jsonc
// Petición
{
  "tipo_venta": "digital_web",            // digital_web | digital_movil
  "tipo_entrega": "domicilio",            // domicilio | recogida_boutique
  "direccion_envio": "Calle de Claudio Coello 48, 4º B, 28001 Madrid",
  "id_sucursal_retiro": null,             // obligatorio si tipo_entrega = recogida_boutique
  "codigo_cupon": "MAISON-2025"           // opcional
}
```

**Secuencia transaccional:**

1. Cargar el carrito con `SELECT … FOR UPDATE` sobre las filas de `inventario_sucursal` implicadas.
2. Rechazar con `409 CARRITO_VACIO` si no hay líneas.
3. Revalidar stock línea a línea contra la temporada vigente. Insuficiencia → `409` indicando la
   prenda concreta.
4. Resolver el cupón (§A.4). Inválido → `422`; sin cupón, continuar.
5. Congelar precios y calcular `subtotal`, `descuento`, `total`.
6. Generar `numero_comprobante` único (§A.5).
7. Insertar `ventas` con `estado = 'pendiente'` y la sucursal responsable (§1.2).
8. Insertar `venta_detalle` (sin `subtotal_linea`, que es generada) con su `id_sucursal` de línea.
9. **Retener stock:** `cantidad_disponible -= n`, `cantidad_reservada += n`, más un registro en
   `movimientos_inventario` por línea (`tipo_movimiento = 'reserva'`,
   `referencia_documento = 'VENTA-<id>'`, `id_usuario_responsable`).
10. Vaciar `carrito_detalle`.
11. `COMMIT`.

```jsonc
// Respuesta 201
{
  "id_venta": 1,
  "numero_comprobante": "FS-2026-000001",
  "estado": "pendiente",
  "tipo_venta": "digital_web",
  "tipo_entrega": "domicilio",
  "subtotal": "2100.00", "descuento": "160.00", "total": "1940.00", "iva_incluido": "336.69",
  "items": [ /* líneas congeladas */ ],
  "expira_en": "2026-09-22T10:50:00Z",
  "mensaje_confirmacion": "Tu orden ha sido registrada. Dispones de 25 minutos para completar el pago."
}
```

| Código | Situación |
| :--- | :--- |
| `201` | Venta creada en `pendiente` |
| `401` | Sin sesión |
| `409` | `CARRITO_VACIO` · `STOCK_INSUFICIENTE` |
| `422` | `CUPON_INVALIDO` · `SUCURSAL_RETIRO_REQUERIDA` · `DIRECCION_REQUERIDA` |

---

#### `GET /api/v1/sucursales/activas` — *ya existe*

Se **reutiliza** para el selector de recogida en boutique. Hoy devuelve datos fabricados
(`cantidad_disponible = 5` fijo, boutiques inventadas si la tabla está vacía). Tarea `T-BE-11`:
depurarlo para que sirva exclusivamente sucursales reales.

### A.4 Resolución de cupones

Con `promociones` vacía, la lógica se especifica pero no será demostrable hasta sembrar datos
(`T-BE-10`). Un cupón es válido si:

1. `codigo_cupon` coincide (comparación insensible a mayúsculas);
2. `estado_activo = true`;
3. `now()` entre `fecha_inicio` y `fecha_fin`;
4. `limite_usos IS NULL` **o** `usos_actuales < limite_usos`.

Cálculo según `tipo_descuento`:

| `tipo_descuento` | Fórmula | Tope |
| :--- | :--- | :--- |
| `porcentaje` | `base × valor_descuento / 100` | limitado por `tope_descuento` si no es nulo |
| `monto_fijo` | `valor_descuento` | nunca superior a la base |

La **base** depende de `alcance`: `global` → subtotal completo; `categoria` → sólo líneas de
`id_categoria`; `producto` → sólo líneas de `id_producto`.

Al confirmarse la venta se incrementa `usos_actuales` **dentro de la misma transacción**, con
`UPDATE … SET usos_actuales = usos_actuales + 1 WHERE id_promocion = :id AND (limite_usos IS NULL
OR usos_actuales < limite_usos)`, comprobando filas afectadas. Nunca leer-comprobar-escribir.

### A.5 Generación de `numero_comprobante`

Formato `FS-<AAAA>-<secuencial de 6 dígitos>`. Para garantizar unicidad bajo concurrencia se usa
una **secuencia de PostgreSQL** (`CREATE SEQUENCE fashionstore.seq_comprobante_venta`), no
`MAX(numero)+1`, que es una condición de carrera clásica. Requiere el visto bueno de §1.3 por ser
un objeto nuevo de esquema. Alternativa sin cambio: reintento acotado sobre la violación de
unicidad de `numero_comprobante`.

### A.6 Criterios de Aceptación (Gherkin)

```gherkin
Característica: CU11 — Gestión de la bolsa de compra

  Escenario: Actualización exitosa de cantidad
    Dado que tengo en la bolsa la variante 102 desde "Atelier Serrano - Madrid" con cantidad 1
    Y esa variante tiene 2 unidades disponibles en esa sucursal
    Cuando envío PATCH /api/v1/carrito/items/44 con cantidad 2
    Entonces recibo 200
    Y la línea refleja cantidad 2
    Y el resumen recalcula subtotal, descuento y total en la misma respuesta

  Escenario: Intento de sobrepasar el stock de la sucursal
    Dado que la variante 102 tiene 2 unidades disponibles en "Atelier Serrano - Madrid"
    Cuando envío PATCH /api/v1/carrito/items/44 con cantidad 3
    Entonces recibo 409 con código "STOCK_INSUFICIENTE"
    Y el mensaje indica la prenda, las disponibles y las solicitadas
    Y la cantidad almacenada permanece en 2

  Escenario: Eliminación de una prenda
    Dado que mi bolsa tiene 3 líneas
    Cuando envío DELETE /api/v1/carrito/items/44
    Entonces recibo 200
    Y la bolsa devuelta tiene 2 líneas
    Y el total se ha recalculado sin la prenda eliminada

  Escenario: Bolsa vacía
    Dado que no tengo ninguna prenda en la bolsa
    Cuando consulto GET /api/v1/carrito
    Entonces recibo 200
    Y "items" es una lista vacía
    Y "resumen.total" es "0.00"
    Y no recibo 404

  Escenario: Línea perteneciente a otro cliente
    Dado que la línea 99 pertenece a otro cliente
    Cuando envío PATCH /api/v1/carrito/items/99
    Entonces recibo 403 con código "CARRITO_AJENO"

Característica: CU15 — Tramitación del pedido

  Escenario: Tramitación exitosa con entrega a domicilio
    Dado que mi bolsa tiene 3 prendas con stock suficiente
    Cuando envío POST /api/v1/ventas/checkout con tipo_entrega "domicilio" y una dirección
    Entonces recibo 201
    Y se crea un registro en "ventas" con estado "pendiente"
    Y se crea una línea en "venta_detalle" por cada prenda, con su precio congelado
    Y cada línea conserva su sucursal de expedición
    Y el inventario mueve las unidades de disponible a reservada
    Y se registra un movimiento de inventario por línea con el responsable
    Y mi bolsa queda vacía

  Escenario: Tramitación con bolsa vacía
    Dado que mi bolsa no tiene prendas
    Cuando envío POST /api/v1/ventas/checkout
    Entonces recibo 409 con código "CARRITO_VACIO"
    Y no se crea ningún registro en "ventas"

  Escenario: Recogida en boutique sin indicar sucursal
    Cuando envío POST /api/v1/ventas/checkout con tipo_entrega "recogida_boutique" sin id_sucursal_retiro
    Entonces recibo 422 con código "SUCURSAL_RETIRO_REQUERIDA"

  Escenario: Cupón inválido
    Cuando envío POST /api/v1/ventas/checkout con codigo_cupon "NO-EXISTE"
    Entonces recibo 422 con código "CUPON_INVALIDO"
    Y no se crea ninguna venta

  Escenario: Agotamiento entre la carga de la bolsa y la tramitación
    Dado que otro cliente agotó la variante 102 después de que yo cargara mi bolsa
    Cuando envío POST /api/v1/ventas/checkout
    Entonces recibo 409 con código "STOCK_INSUFICIENTE"
    Y la transacción revierte por completo
    Y ni el inventario ni mi bolsa quedan alterados

  Escenario: Los importes enviados por el cliente se ignoran
    Cuando envío POST /api/v1/ventas/checkout incluyendo "total": "1.00"
    Entonces la venta creada registra el total recalculado por el servidor
```

### A.7 Riesgos (obligatorio en nivel SDD 3)

| Riesgo | Mitigación |
| :--- | :--- |
| Venta simultánea agota stock entre lectura y escritura | `SELECT … FOR UPDATE` sobre `inventario_sucursal` + `UPDATE` condicional comprobando filas afectadas. Prueba de concurrencia obligatoria (`T-BE-09`) |
| Doble pulsación de `TRAMITAR PEDIDO` genera dos ventas | Botón deshabilitado durante la petición + unicidad de `numero_comprobante`; el segundo intento halla la bolsa ya vacía y responde `409 CARRITO_VACIO` |
| Colisión de `numero_comprobante` | Secuencia de PostgreSQL (§A.5) |
| Stock retenido indefinidamente si el pago nunca llega | Servicio `liberar_retencion_venta` (§1.5). La automatización queda pendiente de decisión |
| El trigger vigente aborta el checkout multi-sucursal | Decisión §1.1. **Bloqueante: sin resolverla, CU15 no puede implementarse** |
| Cupón aplicado más veces que su `limite_usos` | `UPDATE` condicional atómico sobre `usos_actuales` (§A.4) |

---

## B. Plan de Ejecución Secuencial por Bloques (`plan`)

> El **Bloque 1 debe completarse y aprobarse antes** de iniciar 2 y 3: ambos clientes consumen sus
> contratos. Los bloques 2 y 3 son paralelizables entre sí.

### Bloque 1 — Backend (`Ec-backend`, FastAPI + SQLAlchemy + PostgreSQL)

Paquete nuevo `app/modules/compras_pagos/`, con `cu11_gestionar_carrito/` y
`cu15_comprar_plataforma/`, siguiendo la estructura de `reservas/cu12_reservar_prendas/`
(`router.py` · `servicio.py` · `repositorio.py` · `esquemas.py`) y `modelos.py` a nivel de paquete.

**Fase 1.1 — Modelos y esquemas Pydantic**
Modelos `CarritoORM`, `CarritoDetalleORM`, `VentaORM`, `VentaDetalleORM` verificados contra el
esquema real, con `subtotal_linea` en sólo lectura y el enum de movimientos completo. Esquemas:
`CarritoItemOut`, `CarritoResumenOut`, `CarritoOut`, `ItemAgregarIn`, `ItemCantidadIn`,
`CheckoutIn`, `VentaCreadaOut`.

**Fase 1.2 — Servicios y endpoints**
`CarritoServicio` (obtener/crear, agregar con consolidación, fijar cantidad, eliminar, recalcular) y
`CheckoutServicio` (validación, cupón, congelación de precios, comprobante, retención de stock,
vaciado de bolsa) en una única unidad de trabajo. Routers finos: sólo HTTP, validación y traducción
de excepciones de dominio. Registro en `main.py`.

**Fase 1.3 — Pruebas (Pytest)**
Un test por criterio de aceptación de §A.6, citando su escenario. Incluye la prueba de concurrencia
del riesgo principal y la verificación de que `carrito_detalle` queda vacío tras el checkout.

### Bloque 2 — Frontend Web (`Ec-frontend`, Angular 19+)

**Fase 2.1 — Enrutamiento**
Ruta `/bolsa` declarada **a nivel raíz, fuera de `MainLayoutComponent`** (pantalla *spoke*), con
`canActivate: [authGuard]`. Debe quedar **después** de la landing (`path: ''`) y **antes** del
comodín, según el guard `app.routes.spec.ts`. Cabecera propia con `← VOLVER AL CATÁLOGO` mediante
`Location.back()`, que preserva filtros y scroll del origen.

**Fase 2.2 — Servicio reactivo**
`CarritoService` con Signals: `items`, `subtotal`, `descuento`, `total`, `ivaIncluido` y
`totalPrendas` como `computed()`; `tipoEntrega`, `cuponAplicado` y `cargando` como `signal()`.
Inyección con `inject()`, sin constructor. Se comparte con el contador de la barra superior.

**Fase 2.3 — Maquetación**
`BolsaCompraComponent` standalone con `OnPush`, dos columnas (`lg:grid-cols-[1fr_380px]`),
apiladas en móvil. Tokens del sistema (`space-1…7`, paleta semántica); prohibidos los valores
arbitrarios de Tailwind. Control de flujo `@if`/`@for` con `track`. Estados obligatorios: carga
(skeleton), error, **bolsa vacía** y contenido.

**Fase 2.4 — Interacción**
Controles `−`/`+` con `+` deshabilitado al alcanzar `cantidad_maxima`; `ELIMINAR` con recálculo
reactivo; temporizador descendente que se limpia en `ngOnDestroy`; selector de entrega que revela
la dirección o el selector de boutique; campo de cupón con validación contra el backend; botón
`TRAMITAR PEDIDO` deshabilitado mientras hay petición en vuelo, con navegación posterior a la
confirmación. Errores 409/422 traducidos a mensajes legibles.

### Bloque 3 — Mobile (`Ec-mobile`, Flutter 3.x)

**Fase 3.1 — Capa de datos**
`lib/src/modulos/compras_pagos/cu11_gestionar_carrito/datos/` con DTO inmutables. **Los `fromJson`
se prueban contra payloads literales del backend**, no con constructores: fue la causa de que los
desajustes de contrato de CU07/CU12 pasaran inadvertidos. `Decimal` llega como cadena JSON: usar
`double.tryParse(valor.toString())`.

**Fase 3.2 — BLoC**
`CarritoBloc` con estados sellados (`Inicial`, `Cargando`, `Cargado`, `Vacio`, `Error`) y eventos
de incremento, decremento, eliminación, cambio de entrega, aplicación de cupón y confirmación.
Actualización optimista con reversión si el backend responde 409.

**Fase 3.3 — Pantalla**
`ShoppingBagScreen` abierta con `Navigator.push`, **sin `bottomNavigationBar`**, `AppBar` con
`leading: BackButton()`. Banner de cuenta atrás, lista de prendas, bloque de destino de envío,
resumen y **footer fijo** (`bottomNavigationBar: SafeArea(child: …)` reservado para la barra de
acción, que no es navegación). Token JWT propagado desde `PantallaPrincipalHub`, siguiendo el
patrón ya corregido en CU07.

---

## C. Lista de Tareas Atómicas (`tasks`)

### Bloque 1 — Backend

- [x] **T-BE-01**: Completar `tipo_movimiento_inv_enum` en `reservas/modelos.py` con los 4 valores ausentes (`ajuste_positivo`, `ajuste_negativo`, `venta_confirmada`, `cancelacion_pedido`).
- [x] **T-BE-02**: Crear `app/modules/compras_pagos/modelos.py` con `CarritoORM`, `CarritoDetalleORM`, `VentaORM` y `VentaDetalleORM`, con `subtotal_linea` en sólo lectura. Verificar con `pytest tests/test_esquema_bd.py`.
- [x] **T-BE-03**: Esquemas Pydantic de CU11 (`CarritoItemOut`, `CarritoResumenOut`, `CarritoOut`, `ItemAgregarIn`, `ItemCantidadIn`).
- [x] **T-BE-04**: Esquemas Pydantic de CU15 (`CheckoutIn`, `VentaItemOut`, `VentaCreadaOut`).
- [x] **T-BE-05**: `CarritoServicio`: obtener/crear carrito, **agregar ítem con consolidación por (variante, sucursal)**, fijar cantidad, eliminar y recalcular resumen.
- [x] **T-BE-06**: `CarritoRepositorio` con resolución de stock por temporada vigente (sin `scalar_one_or_none` sobre claves no únicas) y bloqueo `FOR UPDATE`.
- [x] **T-BE-07**: Router de CU11: `GET /carrito`, `POST /carrito/items`, `PATCH /carrito/items/{id}`, `DELETE /carrito/items/{id}`. Registrar en `main.py`.
- [x] **T-BE-08**: `CheckoutServicio` con la secuencia transaccional de §A.3, resolución de cupón (§A.4), comprobante (§A.5) y retención de stock con movimientos de inventario.
- [x] **T-BE-09**: Suite Pytest: un test por escenario Gherkin de §A.6 **más** prueba de concurrencia de doble checkout simultáneo sobre la última unidad.
- [x] **T-BE-10**: Migración de *seed* `0004_seed_promociones.py` con al menos una promoción vigente y cupón real, para que el descuento sea demostrable.
- [x] **T-BE-11**: Depurar `GET /api/v1/sucursales/activas` eliminando las boutiques inventadas y el `cantidad_disponible = 5` fijo (deuda registrada en el checkpoint de CU07/CU12).
- [x] **T-BE-12**: `liberar_retencion_venta` con su endpoint y pruebas (§1.5).
- [x] **T-BE-13** *(sujeta a §1.1–1.3)*: Migración `0005_checkout_ddl.py` — `venta_detalle.id_sucursal`, campos de entrega en `ventas`, secuencia de comprobante y reemplazo de `fn_descontar_inventario_venta`. **Reversible (`downgrade` obligatorio).**

### Bloque 2 — Frontend Web

- [x] **T-FE-01**: Modelos TypeScript espejo de los esquemas Pydantic en `modules/compras_pagos/cu11_gestionar_carrito/modelos/`.
- [x] **T-FE-02**: `CarritoService` con Signals y `computed()` para el resumen financiero.
- [x] **T-FE-03**: Ruta `/bolsa` fuera de `MainLayoutComponent`, protegida por `authGuard`, respetando el orden verificado por `app.routes.spec.ts`.
- [x] **T-FE-04**: `BolsaCompraComponent` standalone + `OnPush`, layout de dos columnas fiel a `image_046d3e.png`.
- [x] **T-FE-05**: Tarjeta de prenda: imagen, badge, SKU, talla, color, sucursal de expedición, precio con tachado y controles `−`/`+`/`ELIMINAR`.
- [x] **T-FE-06**: Panel de resumen: desglose financiero, selector de entrega, campo de cupón y botón `TRAMITAR PEDIDO`.
- [x] **T-FE-07**: Reconvertir `anadirABolsa()` de `producto-detalle.component.ts` a `POST /api/v1/carrito/items` real, con contador en la barra superior.
- [x] **T-FE-08**: Temporizador descendente con limpieza en `ngOnDestroy`.
- [x] **T-FE-09**: Estado vacío con enlace a `/catalogo`, estado de carga y traducción de errores 409/422.
- [x] **T-FE-10**: Pruebas Vitest: recálculo reactivo, tope de stock en `+`, eliminación, estado vacío y tramitación. Mocks construidos con payloads literales del backend.

### Bloque 3 — Mobile

- [x] **T-MO-01**: DTO en `modulos/compras_pagos/cu11_gestionar_carrito/datos/modelos/` con parseo tolerante de `Decimal`.
- [x] **T-MO-02**: `CarritoApi` (datasource HTTP) con manejo de 401 vía `SesionManager` y traducción de errores de dominio.
- [x] **T-MO-03**: `CarritoBloc` con estados sellados y actualización optimista reversible.
- [x] **T-MO-04**: `ShoppingBagScreen` fiel a `image_046a5d.png`, sin `bottomNavigationBar` de navegación y con `AppBar` de retorno.
- [x] **T-MO-05**: Banner de cuenta atrás, tarjetas de prenda con controles y papelera.
- [x] **T-MO-06**: Bloque de destino de envío, resumen y **footer fijo** con `TRAMITAR PEDIDO`.
- [x] **T-MO-07**: Reconvertir `anadirABolsa` de `producto_detalle_bloc.dart` a llamada real persistente.
- [x] **T-MO-08**: Propagar el token JWT a `ShoppingBagScreen` desde el hub y desde el detalle.
- [x] **T-MO-09**: Pruebas: `fromJson`/`toJson` contra payloads literales, transiciones del BLoC, ausencia de `BottomNavigationBar` y footer fijo visible.

---

## D. Puntos de Control y Verificación (`checkpoints`)

| ID | Capa | Criterio de Aprobación | Método | Estado |
| :--- | :--- | :--- | :--- | :--- |
| **CP-01** | Backend | `GET /api/v1/carrito` devuelve 200 con `items: []` y totales en cero para una bolsa vacía; nunca 404. | Pytest | ✅ |
| **CP-02** | Backend | `PATCH` actualiza la cantidad y devuelve el resumen recalculado en la misma respuesta. | Pytest | ✅ |
| **CP-03** | Backend | Superar el stock de la sucursal responde 409 `STOCK_INSUFICIENTE` y **no** altera la cantidad almacenada. | Pytest | ✅ |
| **CP-04** | Backend | `DELETE` purga la línea de `carrito_detalle` y recalcula el total. | Pytest + consulta a la BD | ✅ |
| **CP-05** | Backend | Operar sobre una línea ajena responde 403 `CARRITO_AJENO`. | Pytest | ✅ |
| **CP-06** | Backend | El checkout persiste `ventas` (estado `pendiente`) y una línea de `venta_detalle` por prenda, con precio congelado y sucursal de expedición. | Pytest + verificación en Neon | ✅ |
| **CP-07** | Backend | El checkout mueve unidades de `cantidad_disponible` a `cantidad_reservada` y registra un movimiento por línea con `id_usuario_responsable`. | Pytest | ✅ |
| **CP-08** | Backend | Un fallo en cualquier punto revierte **toda** la transacción: ni venta, ni inventario, ni vaciado de bolsa. | Pytest con fallo inducido | ✅ |
| **CP-09** | Backend | Dos checkouts simultáneos sobre la última unidad: uno responde 201 y el otro 409; el stock nunca queda negativo. | Prueba de concurrencia | ✅ |
| **CP-10** | Backend | El cupón aplica el descuento correcto según `tipo_descuento` y `alcance`, e incrementa `usos_actuales` atómicamente sin superar `limite_usos`. | Pytest | ✅ |
| **CP-11** | Backend | `numero_comprobante` es único bajo concurrencia. | Prueba de concurrencia | ✅ |
| **CP-12** | Backend | Los importes enviados por el cliente se ignoran; la venta registra el total recalculado. | Pytest | ✅ |
| **CP-13** | Backend | `pytest` completo en verde, incluida la guardia `tests/test_esquema_bd.py`. | `pytest -q` | ✅ |
| **CP-14** | Web | `/bolsa` se renderiza **sin la barra de navegación institucional** y con `← VOLVER AL CATÁLOGO` funcional. | Inspección + Vitest | ✅ |
| **CP-15** | Web | `−`/`+`/`ELIMINAR` recalculan subtotal, descuento y total **al instante**, sin recargar la página. | Vitest sobre Signals | ✅ |
| **CP-16** | Web | `+` se deshabilita al alcanzar `cantidad_maxima`; el 409 del backend se muestra como mensaje legible. | Vitest | ✅ |
| **CP-17** | Web | El selector de entrega alterna entre dirección y boutique, y su elección viaja en el payload del checkout. | Vitest | ✅ |
| **CP-18** | Web | Estado vacío visible con enlace al catálogo cuando no hay prendas. | Vitest | ✅ |
| **CP-19** | Web | `npx tsc --noEmit` sin errores, `ng build` limpio y `ng test` en verde. | Ejecución | ✅ |
| **CP-20** | Mobile | `ShoppingBagScreen` se abre a pantalla completa **sin `BottomNavigationBar`**, con `AppBar` de retorno operativo. | Test de widget | ✅ |
| **CP-21** | Mobile | El footer de `TRAMITAR PEDIDO` permanece fijo y visible durante el scroll, con el total actualizado. | Test de widget | ✅ |
| **CP-22** | Mobile | Los controles de cantidad y la papelera sincronizan con el backend; un 409 revierte la actualización optimista. | Test de BLoC | ✅ |
| **CP-23** | Mobile | Los DTO se validan con `fromJson` sobre payloads literales del backend, no con constructores. | Revisión de código + tests | ✅ |
| **CP-24** | Mobile | `dart analyze` sin incidencias y `flutter test` en verde. | Ejecución | ✅ |
| **CP-25** | Transversal | Web y Mobile consumen **los mismos endpoints con los mismos nombres de campo**, verificado en ambos lados. | Diff de contratos | ✅ |
| **CP-26** | Transversal | Ningún importe, sucursal o prenda mostrado procede de literales en el código: todo viene de PostgreSQL. | Auditoría de código | ✅ |
| **CP-27** | Transversal | Catálogo exclusivamente femenino en todas las tarjetas de la bolsa, incluidos los *fallback*. | Auditoría visual | ✅ |

---

## Resumen para tu decisión

**Listo para implementar sin más autorizaciones:** CU11 completo (§A.3, endpoints de carrito),
el modelo financiero, la resolución de cupones y ambos bloques de cliente.

**Requiere tu decisión antes de tocar código:**

1. **§1.1 — El trigger `trg_descontar_inventario`.** Es el bloqueante duro: mientras siga como
   está, un checkout con prendas de varias sucursales **aborta con excepción de PostgreSQL**.
   Recomendación: Opción A (mover el control del stock al servicio, como ya hace CU12).
2. **§1.2 y §1.3 — Cuatro columnas aditivas y una secuencia** para conservar la sucursal por línea
   y persistir tipo de entrega, dirección y cupón aplicado.
3. **§1.4 — Qué promete el temporizador.** Propuesta: informativo en la bolsa, garantía real de
   25 minutos desde que se tramita el pedido.
4. **§0.2 — Ampliación de alcance confirmada:** «añadir a la bolsa» no existe y queda incorporado.

> ✅ **GATE SUPERADO (2026-09-22):** las cuatro decisiones fueron aprobadas tal y como se
> recomendaban y se autorizó la ejecución del Bloque 1.

---

## E. Resultado de la ejecución del Bloque 1 (Backend)

### E.1 Entregado

| Tarea | Resultado |
| :--- | :--- |
| `T-BE-01` | Enum `tipo_movimiento_inv` sincronizado con los 12 valores reales de PostgreSQL. |
| `T-BE-02` | Paquete `app/modules/compras_pagos/` con `CarritoORM` y `CarritoDetalleORM`. `VentaORM`/`VentaDetalleORM` **no se duplicaron**: ya existían en `catalogo/modelos.py` desde CU18, y redeclararlas producía `InvalidRequestError` por tabla duplicada. Se extendieron allí con las columnas nuevas y se reexportan desde el paquete. |
| `T-BE-03`/`04` | Esquemas Pydantic de bolsa y checkout. `CheckoutIn` no admite importes por diseño. |
| `T-BE-05`/`06` | `CarritoServicio` y `CarritoRepositorio`, con resolución de inventario por temporada vigente y bloqueo opcional. |
| `T-BE-07` | 4 endpoints de CU11 registrados bajo `/api/v1`. |
| `T-BE-08` | `CheckoutServicio` con la secuencia transaccional completa. |
| `T-BE-09` | 33 pruebas nuevas (14 de CU11, 19 de CU15), una por escenario Gherkin más concurrencia. |
| `T-BE-10` | Migración `0010`: bono `MAISON-2025` (10 %, tope 200 €, 500 usos) y «Membresia Prive» (15 %) ligada a los 3 productos activos de mayor precio, resueltos por consulta y no por identificadores inventados. |
| `T-BE-11` | `GET /api/v1/sucursales/activas` depurado: ya no inventa boutiques ni asigna `cantidad_disponible = 5` fijo. |
| `T-BE-12` | `liberar_retencion_venta` con endpoint y pruebas. |
| `T-BE-13` | Migración `0009` aplicada: `venta_detalle.id_sucursal`, campos de entrega y cupón en `ventas`, `seq_comprobante_venta` y neutralización del trigger. |

### E.2 Defectos preexistentes encontrados durante la ejecución

Dos derivas de **tipo** entre el ORM y PostgreSQL, invisibles para la guardia de esquema original
porque esta solo comparaba nombres de columna:

| Defecto | Impacto | Corrección |
| :--- | :--- | :--- |
| `PromocionORM.fecha_inicio`/`fecha_fin` declaradas `Date` siendo `TIMESTAMPTZ` | La validación de vigencia del cupón reventaba con `TypeError: can't compare datetime.datetime to datetime.date`. **Lo detectó la verificación end-to-end, no las pruebas unitarias.** | Tipos alineados a `DateTime(timezone=True)` y comparación normalizada a UTC. |
| `ClienteORM.fecha_nacimiento` declarada `DateTime` siendo `DATE` | CU04 convivía con la deriva mediante comprobaciones de tipo en cada lectura y un `datetime.combine` artificial en cada escritura. | Tipo alineado a `Date` y servicio de perfil simplificado. |

`tests/test_esquema_bd.py` se amplió con `test_los_tipos_del_orm_son_compatibles_con_la_base_de_datos`,
que compara **familias** de tipo (fecha, instante, entero, texto, numérico…) y habría detectado
ambos. Fue precisamente esa guardia ampliada la que encontró el segundo.

### E.3 Verificación end-to-end contra Neon

Flujo completo ejecutado con SQL real sobre el cliente `#7`, con limpieza posterior que restituyó
el stock y dejó las tablas como estaban:

- Bolsa vacía → 200 con total `0.00`, sin ventana informativa.
- Alta de 2 prendas → subtotal `1630.00`, descuento `244.50` (Membresia Prive), total `1385.50`.
  Se cumple la invariante `total = subtotal − descuento`.
- Repetir variante → **consolida** a una sola línea con cantidad 2, no duplica.
- `PATCH` a cantidad 3 → total `2898.50`; `cantidad_maxima` alimenta el tope del botón `+`.
- Exceso de stock → `409 STOCK_INSUFICIENTE` con mensaje que nombra la prenda y las cifras; la
  bolsa no se altera.
- `DELETE` → queda 1 línea, total recalculado a `2269.50`.
- **Checkout con cupón** → `FS-2026-000001`, estado `pendiente`, subtotal `2670.00`,
  descuento `600.50` (400,50 de promoción + 200,00 del bono limitado por su tope), total `2069.50`.
- Persistencia comprobada en PostgreSQL: `tipo_entrega`, `direccion_envio` e `id_promocion`
  guardados; precio congelado `756.50`; `subtotal_linea` calculada por la columna GENERATED
  (`2269.50`); sucursal de expedición conservada por línea.
- Retención: disponible 15 → 12, reservada 0 → 3, con un movimiento `reserva` auditado y su
  usuario responsable.
- **Trigger neutralizado confirmado:** el stock bajó exactamente 3, no 6. Antes de la migración
  `0009` habría habido doble descuento.
- Bolsa vaciada tras tramitar.
- Liberación de retención → 3 unidades devueltas, stock restaurado a (15, 0).

### E.4 Pendiente para los siguientes bloques

- La automatización del vencimiento a los 25 minutos (cron frente a verificación perezosa) sigue
  sin decidir; hoy la liberación es explícita mediante endpoint.
- `alembic upgrade head` continúa sin poder resolver la cadena: la base declara ahora `0010`,
  pero las revisiones `0004`–`0008` no existen como archivos en el repositorio. Las migraciones
  `0009` y `0010` se aplicaron ejecutando su DDL de forma idempotente. Reconciliar la cadena
  completa sigue siendo deuda abierta pendiente de decisión.

---

## F. Resultado de la ejecución del Bloque 2 (Frontend Web)

### F.1 Entregado

| Tarea | Resultado |
| :--- | :--- |
| `T-FE-01` | `modelos/carrito.model.ts`, espejo campo a campo de los esquemas Pydantic. Los importes se tipan como `string`: FastAPI serializa `Decimal` en texto y convertirlos a `number` perdería precisión. |
| `T-FE-02` | `CarritoService` con Signals. `items`, `resumen`, `subtotal`, `descuento`, `total`, `ivaIncluido`, `totalPrendas`, `estaVacia` y `hayDescuento` son `computed()`; el estado de escritura se reemplaza con la respuesta del servidor en cada operación, nunca se deriva en el cliente. |
| `T-FE-03` | Ruta `/bolsa` declarada **fuera de `MainLayoutComponent`**, protegida por `authGuard` y situada después de la landing y antes del comodín. |
| `T-FE-04`/`05`/`06` | `BolsaCompraComponent` standalone + `OnPush`, dos columnas (`lg:grid-cols-[1fr_380px]`) apiladas en móvil, con tarjetas de prenda, panel de resumen, selector de entrega y campo de cupón. |
| `T-FE-07` | `anadirABolsa()` reconvertido a `POST /api/v1/carrito/items`. El contador de la barra superior pasó a derivar de `CarritoService`. |
| `T-FE-08` | Cuenta atrás con `clearInterval` en `ngOnDestroy` y recálculo al cambiar la bolsa. |
| `T-FE-09` | Cuatro estados: carga (skeleton), error con el mensaje de negocio del backend, bolsa vacía con enlace a `/catalogo`, y contenido. |
| `T-FE-10` | 37 pruebas nuevas en Vitest (11 de servicio, 20 de componente, 6 de layout y rutas). |

### F.2 Defecto preexistente corregido

`MainLayoutComponent` mostraba el contador de la bolsa leyendo `CatalogoService.cestaCount`, un
`signal` **inicializado en `2`** que sólo se incrementaba en memoria. La barra superior exhibía
así una cifra inventada, desalineada con la bolsa persistida y que no bajaba nunca al eliminar
prendas. Ahora deriva de `CarritoService.totalPrendas`, y el icono enlaza con `/bolsa`.

El contador se carga sólo si hay sesión activa: sin ella la petición devolvería 401 y dispararía
el redirect del interceptor sobre pantallas que pueden ser públicas.

### F.3 Decisiones de implementación

- **El cupón no se valida en el cliente.** El campo registra la intención y el veredicto llega del
  backend al tramitar, con su mensaje de negocio. Duplicar las reglas de vigencia, tope y límite de
  usos en TypeScript crearía dos fuentes de verdad que se desincronizarían.
- **`anadirABolsa()` no envía `id_sucursal`.** El backend resuelve la boutique con mayor
  disponibilidad para la variante en la temporada vigente; el cliente puede revisarla después en
  la propia bolsa, donde cada línea muestra su origen.
- **El temporizador se recalcula tras cada cambio de la bolsa**, porque la ventana arranca en la
  línea más antigua y eliminar esa línea desplaza el vencimiento.
- **Los textos del temporizador se ajustaron a lo que el sistema garantiza de verdad.** El mockup
  prometía «prendas reservadas en tu bolsa»; la pantalla dice «stock verificado» y aclara que la
  reserva firme se activa al tramitar, conforme a la decisión §1.4.

### F.4 Verificación

`npx tsc --noEmit` sin errores · `ng build` limpio (`bolsa-compra-component`, 26,85 kB lazy) ·
`ng test` **145/145** en verde (108 previos + 37 nuevos), sin regresiones.

---

## G. Resultado de la ejecución del Bloque 3 (Mobile)

### G.1 Entregado

| Tarea | Resultado |
| :--- | :--- |
| `T-MO-01` | `datos/modelos/carrito_dto.dart` con `parsearImporte`, que tolera cadenas, números y ausencias. FastAPI serializa `Decimal` como texto: un `as num` directo lanzaría `TypeError`, el defecto 28 del `CHANGELOG.md`. |
| `T-MO-02` | `CarritoApi` + `CarritoApiImpl`. `CarritoException` conserva el `code` del backend (`STOCK_INSUFICIENTE`, `CARRITO_VACIO`, `CUPON_INVALIDO`) para no tener que interpretar el texto del mensaje. Un 401 notifica al `SesionManager`, que devuelve al login desde la raíz. |
| `T-MO-03` | `CarritoBloc` con estados sellados (`Inicial`, `Cargando`, `Cargado`, `Vacio`, `Error`) y actualización optimista reversible. |
| `T-MO-04` | `ShoppingBagScreen` con `leading: BackButton()` y **sin `BottomNavigationBar`**. |
| `T-MO-05` | Banner de ventana, tarjetas con controles `−`/`+`, papelera, precio tachado y boutique de expedición por línea. |
| `T-MO-06` | Bloque de destino de envío, cupón, resumen y **barra de acción fija** con el total y `TRAMITAR PEDIDO`. |
| `T-MO-07` | `agregarABolsa` reconvertido a `POST /api/v1/carrito/items`. El contador de la ficha procede ahora de la bolsa real. |
| `T-MO-08` | Token propagado a `ShoppingBagScreen` desde el hub (icono en la cabecera de Inicio) y desde la ficha de producto (icono con contador en el `AppBar`). |
| `T-MO-09` | 29 pruebas nuevas: 6 de contrato de DTO, 13 de BLoC, 8 de widget y 2 de la ficha de producto. |

### G.2 Decisiones de implementación

- **La barra inferior fija no vulnera Hub-and-Spoke.** La directriz prohíbe la barra de
  *navegación* de 4 pestañas en las pantallas hoja, no un pie de acción. `bottomNavigationBar`
  aloja aquí el total y el botón de tramitar, que deben permanecer visibles durante el scroll;
  desaparece en cuanto la orden queda confirmada.
- **La bolsa se abre con `Navigator.push`, no como quinta pestaña.** Las pantallas raíz siguen
  siendo exactamente cuatro.
- **La actualización optimista no recalcula importes.** Cambia la cantidad en pantalla al instante
  y revierte si el backend la rechaza, pero los totales se dejan intactos hasta que llega la
  respuesta: recalcularlos en el cliente obligaría a duplicar las reglas de promoción del backend.
- **El aviso de «añadido a la bolsa» se deriva del resultado real.** Antes la pantalla lo mostraba
  incondicionalmente tras pulsar; ahora refleja lo que respondió el servidor, de modo que una
  prenda sin existencias o una sesión caducada no se anuncian como éxito.

### G.3 Defecto corregido durante la ejecución

`RenderFlex overflowed by 1.5 pixels` en dos filas: la cabecera («Bolsa de Compra» + contador) y
la barra de acción (total + botón). Es la quinta aparición de este defecto en el proyecto
(entradas 9, 20, 26 y 31 del `CHANGELOG.md`). Se resolvió con `Expanded`/`Flexible` y elipsis en
lugar de reducir tamaños: así el diseño aguanta importes de más dígitos y textos más largos.

### G.4 Verificación

`dart analyze` **sin incidencias** · `flutter test` **133/133** en verde (104 previos + 29 nuevos).

Contraste de contrato entre las tres plataformas: las claves de `POST /api/v1/ventas/checkout`
(`tipo_venta`, `tipo_entrega`, `direccion_envio`, `id_sucursal_retiro`, `codigo_cupon`) coinciden
campo a campo entre el esquema Pydantic, el servicio Angular y el DTO de Flutter.

---

## H. Estado global del cambio

| Bloque | Estado | Verificación |
| :--- | :--- | :--- |
| 1 — Backend | 🟢 Completado | `pytest` 158/158 + verificación end-to-end contra Neon |
| 2 — Frontend Web | 🟢 Completado | `tsc` limpio · `ng build` limpio · `ng test` 145/145 |
| 3 — Mobile | 🟢 Completado | `dart analyze` 0 incidencias · `flutter test` 133/133 |

**Los 27 checkpoints (CP-01 a CP-27) quedan aprobados.**

### Pendiente de decisión, fuera del alcance de este cambio

- **Automatización del vencimiento de la retención a los 25 minutos** (cron frente a verificación
  perezosa). Hoy `liberar_retencion_venta` existe y está probado, pero debe invocarse de forma
  explícita: una orden abandonada mantiene el stock retenido hasta que alguien la libere. Conviene
  resolverlo antes de producción.
- **Reconciliación de la cadena de migraciones de Alembic.** La base declara `0010`, pero las
  revisiones `0004`–`0008` no existen como archivos en el repositorio, de modo que
  `alembic upgrade head` sigue sin poder resolverla.
- **CU16 (pasarela de pago)** recogerá la orden `pendiente` y convertirá la retención en venta
  firme mediante el movimiento `venta_confirmada`.
