/**
 * Modelos e interfaces TypeScript para CU11 (Bolsa de Compra) y CU15 (Tramitación del pedido).
 *
 * Son el espejo exacto de los esquemas Pydantic del backend, en
 * `Ec-backend/app/modules/compras_pagos/`. Cualquier divergencia de nombres pasa
 * desapercibida en compilación y sólo se manifiesta como campos vacíos en pantalla, que es
 * justamente lo que ocurrió con la confirmación de reserva de CU12.
 *
 * Los importes viajan como `string`: FastAPI serializa `Decimal` en formato textual para no
 * perder precisión. Nunca se convierten a `number` para operar con ellos.
 */

/** Una prenda de la bolsa, con su precio, boutique de expedición y stock vigente. */
export interface CarritoItem {
  id_carrito_detalle: number;
  id_variante: number;
  id_producto: number;
  nombre_producto: string;
  linea_confeccion: string | null;
  sku: string;
  talla_codigo: string;
  color_nombre: string;
  color_hex: string | null;
  imagen_url: string | null;

  precio_lista: string;
  precio_unitario: string;
  descuento_linea: string;
  motivo_descuento: string | null;

  cantidad: number;
  id_sucursal: number;
  nombre_sucursal: string;
  stock_disponible: number;
  /** Tope para el botón «+»; evita una llamada extra para conocer el límite. */
  cantidad_maxima: number;
  subtotal_linea: string;
}

/**
 * Resumen financiero de la bolsa.
 *
 * `subtotal` agrega precios de lista y `descuento` el ahorro aplicado, de modo que siempre se
 * cumple `total = subtotal - descuento`. La maqueta rotulaba el subtotal ya descontado y volvía
 * a restar el descuento, lo que no cuadraba.
 */
export interface CarritoResumen {
  total_prendas: number;
  total_lineas: number;
  subtotal: string;
  descuento: string;
  total: string;
  /** IVA contenido en el total (21 %). Informativo: los precios ya lo incluyen. */
  iva_incluido: string;
  moneda: string;
}

export interface SucursalExpedicion {
  id_sucursal: number;
  nombre: string;
  total_lineas: number;
}

/** Contrato consolidado de `GET /api/v1/carrito`. */
export interface Carrito {
  id_carrito: number;
  items: CarritoItem[];
  resumen: CarritoResumen;
  /**
   * Fin de la ventana informativa (línea más antigua + 25 min).
   * NO retiene existencias: la garantía firme se obtiene al tramitar el pedido.
   */
  expira_en: string | null;
  sucursales_expedicion: SucursalExpedicion[];
}

export interface ItemAgregarPayload {
  id_variante: number;
  cantidad: number;
  /** Si se omite, el backend elige la boutique con mayor disponibilidad. */
  id_sucursal?: number;
}

export interface ItemCantidadPayload {
  /** Cantidad absoluta, no un incremento: hace la operación idempotente. */
  cantidad: number;
}

// ---------------------------------------------------------------------------
// CU15 — Tramitación del pedido
// ---------------------------------------------------------------------------

export type TipoEntrega = 'domicilio' | 'recogida_boutique';

export interface CheckoutPayload {
  tipo_venta: 'digital_web' | 'digital_movil';
  tipo_entrega: TipoEntrega;
  direccion_envio?: string | null;
  id_sucursal_retiro?: number | null;
  codigo_cupon?: string | null;
}

export interface VentaItem {
  id_venta_detalle: number | null;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  imagen_url: string | null;
  cantidad: number;
  precio_unitario: string;
  subtotal_linea: string;
  id_sucursal: number | null;
  nombre_sucursal: string | null;
}

/** Espejo de `VentaCreadaOut`: la orden lista para la pasarela de pago (CU16). */
export interface VentaCreada {
  id_venta: number;
  numero_comprobante: string;
  estado: string;
  tipo_venta: string;
  tipo_entrega: string;
  direccion_envio: string | null;
  id_sucursal_retiro: number | null;
  nombre_sucursal_retiro: string | null;

  subtotal: string;
  descuento: string;
  total: string;
  iva_incluido: string;
  moneda: string;

  cupon_aplicado: string | null;
  nombre_promocion: string | null;

  items: VentaItem[];
  total_prendas: number;

  fecha_venta: string;
  /** Vencimiento de la retención de existencias (fecha_venta + 25 min). */
  expira_en: string;
  mensaje_confirmacion: string;
}

/** Boutique del directorio de `GET /api/v1/sucursales/activas`. */
export interface BoutiqueRecogida {
  id_sucursal: number;
  nombre: string;
  ciudad: string;
  direccion: string;
  telefono: string | null;
  horario_apertura: string;
  horario_cierre: string;
}
