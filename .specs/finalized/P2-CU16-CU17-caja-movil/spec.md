# Requisitos · P2-CU16 y P2-CU17 — Caja en el móvil   Nivel: 2   Estado: ✅ cerrada (2026-11-10)

**ID del cambio:** `P2-CU16-CU17-caja-movil`
**Aprobado por:** Gustavo (usuario) **Fecha:** 2026-11-10
**Fase SDD:** 1 de 4 (Requisitos). Diseño en `plan.md`, tareas en `tasks.md`, puertas en `checkpoint.md`.
**Fuente:** `SI2-Parcial2.md` CU16 (Registrar venta presencial) y CU17 (Procesar venta presencial y
emitir comprobante), ambos «Web/Móvil»; spec permanente de la caja web
`.specs/modules/compras_pagos/CU31-CU32-punto-de-venta-presencial.md`.
**Decisiones del usuario (2026-11-10):** E1 cajero, encargado y administrador entran **directo a la
caja** (el hub queda solo para clientes) · E2 comprobante **en pantalla**, sin PDF ni dependencias
nuevas · E3 se incluyen los **pedidos web por cobrar en efectivo**.
**Nivel 2 porque** solo es un cliente nuevo de contratos que ya existen y están probados
(`/api/v1/pos`, `/api/v1/mis-sucursales`, `/api/v1/admin/pagos`): sin backend, sin migración y sin
reglas de dinero nuevas; el servidor sigue calculando todo.

> **Numeración.** CU16/CU17 del Parcial 2 son CU31/CU32 del Parcial 1 (la caja web, módulo
> `cu31_cu32_punto_venta`). En el móvil, `cu16_realizar_pago` es otro CU (pago electrónico del cliente):
> el módulo nuevo se llama `cu16_cu17_caja` para no confundirlos.

---

## Propósito

Que el cajero, el encargado y el administrador puedan vender y cobrar en la boutique desde la app
móvil con las mismas reglas que la caja web, sin una segunda implementación de cálculos.

## Actores y precondiciones

| Actor | Sucursal | Precondiciones |
| :--- | :--- | :--- |
| Cajero | Las autorizadas (RN07); sin selector si es una | Sesión iniciada, ficha de empleado, conexión |
| Encargado de sucursal | Las autorizadas | Igual |
| Administrador | La que elija entre las de su empresa | Igual |

Plan con «ventas» y suscripción vigente (lo valida el servidor).

## Hallazgos

- Hoy un empleado que entra en la app cae en el hub del cliente (Inicio, Buscar, Catálogo, Perfil),
  que no le sirve; la única pantalla de empleado es «Reportes por voz», dentro de Perfil.
- El backend de la caja está completo y probado (CU31-CU32 web): no hace falta tocarlo.

---

## Requisitos (EARS)

### Entrada (E1)

- **AC-1** Cuando un cajero, encargado o administrador inicia sesión en la app, el sistema deberá abrir
  la pantalla de caja de su empresa, sin el hub del cliente.
- **AC-2** Mientras el empleado esté en la caja, la pantalla deberá mostrar su nombre, la sucursal y
  «Cerrar sesión»; el administrador y el encargado tendrán además «Reportes por voz».
- **AC-3** Si el empleado tiene más de una sucursal autorizada (o es administrador), entonces deberá
  elegir la sucursal antes de vender; con una sola, se usa sin preguntar.

### CU16 · Registrar venta presencial

- **AC-4** Cuando el empleado escribe 2 o más caracteres, el sistema deberá listar las prendas que
  coinciden por nombre, categoría o SKU, con talla, color, precio vigente y existencias en la sucursal.
- **AC-5** Cuando añade una prenda o cambia cantidades, cliente, cupón o reserva, la app deberá mostrar
  subtotal, descuento y total tal como los devuelve `previsualizar` (nunca calculados en el teléfono).
- **AC-6** Si la prenda no tiene existencias en la sucursal, entonces la app no deberá añadirla y lo
  dirá (A1).
- **AC-7** Donde el empleado asocie un cliente (búsqueda por nombre o correo), la app deberá ofrecer
  sus reservas activas para cargarlas, con la opción de excluir líneas; también se podrá cargar una
  reserva por su código. Sin cliente, la venta es presencial sin cuenta.
- **AC-8** Si el cupón no es válido, está vencido o sin usos, entonces la app deberá mostrar el motivo
  del servidor y permitir seguir sin descuento (A2).
- **AC-9** Cuando confirma, el sistema deberá registrar la venta `pendiente` y pasar al cobro; si se
  cancela antes de confirmar, no se registra nada (A3).

### CU17 · Cobrar y emitir comprobante

- **AC-10** Cuando cobra en efectivo, la app deberá pedir el monto recibido y mostrar el cambio que
  devuelve el servidor; un monto menor responde con el error del servidor y no cierra el cobro (A2).
- **AC-11** Cuando cobra con tarjeta, QR o transferencia, la app deberá pedir la referencia y permitir
  registrar «Datáfono rechazó la tarjeta»: la venta sigue pendiente y se puede intentar otro medio (A1).
- **AC-12** Cuando el cobro se confirma, la app deberá mostrar el comprobante en pantalla: número,
  fecha, sucursal, cajero, cliente, líneas, subtotal, descuento, total, IVA incluido, método, recibido
  y cambio (E2).
- **AC-13** Donde haya ventas pendientes o del día, la app deberá listarlas y permitir cobrar, ver el
  comprobante o anular una pendiente con motivo (3–250 caracteres) (A3).
- **AC-14** Donde haya pedidos web con pago en efectivo para la sucursal, la app deberá listarlos y
  permitir confirmar o cancelar su cobro (E3).

### Transversales

- **AC-15** Mientras no haya conexión, la caja deberá decir «Sin conexión» y no permitir registrar ni
  cobrar (CU16 A4, CU17 A4).
- **AC-16** Los importes deberán mostrarse con `formatoImporte` en la moneda de la empresa; nunca «€».
- **AC-17** Cada error del servidor (`{detail, code}`) deberá mostrarse con su mensaje; un 401 lleva al
  login (`SesionManager`).

## Casos de error (los decide el servidor; la app los muestra)

`STOCK_INSUFICIENTE`, `VENTA_VACIA`, `VARIANTE_YA_EN_RESERVA`, `RESERVA_NO_ATENDIBLE`, `SUCURSAL_AJENA`,
`SUCURSAL_REQUERIDA`, `EMPLEADO_NO_REGISTRADO`, `MONTO_REQUERIDO`, `MONTO_INSUFICIENTE`,
`REFERENCIA_REQUERIDA`, `COMPROBANTE_NO_DISPONIBLE`, `SUSCRIPCION_NO_VIGENTE`, `FUNCIONALIDAD_NO_INCLUIDA`.

## Fuera de alcance

- PDF del comprobante, impresión y compartir (E2).
- Lector de código de barras con la cámara.
- Apertura, arqueo y cierre de caja (también fuera en la web).
- Funciones del panel web (inventario, usuarios…) para empleados en el móvil.
- CU18 (cambio de prenda): cambio siguiente.

## Preguntas abiertas

Ninguna: E1–E3 decididas el 2026-11-10.
