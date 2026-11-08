/**
 * DTOs del punto de venta presencial (CU31-CU32): espejo de
 * `Ec-backend/app/modules/compras_pagos/cu31_cu32_punto_venta/esquemas.py`.
 *
 * FastAPI serializa `Decimal` como cadena JSON: los importes se tipan como `string` y nunca se
 * convierten a `number` ni se derivan en el cliente (CLAUDE.md).
 */

export type MetodoPagoCaja = 'efectivo' | 'tarjeta_debito' | 'tarjeta_credito' | 'qr' | 'transferencia';
export type EstadoVentaPos = 'pendiente' | 'pagada' | 'anulada';

export interface LineaPosIn {
  id_variante: number;
  cantidad: number;
}

export interface VentaPosIn {
  id_sucursal?: number | null;
  id_cliente?: number | null;
  reserva?: string | null;
  codigo_cupon?: string | null;
  lineas: LineaPosIn[];
  lineas_reserva_excluidas: number[];
}

export interface CobroPosIn {
  metodo_pago: MetodoPagoCaja;
  monto_recibido?: string | null;
  referencia?: string | null;
  aprobado: boolean;
}

export interface VariantePos {
  id_variante: number;
  sku: string;
  id_producto: number;
  nombre_producto: string;
  categoria_nombre: string | null;
  talla_codigo: string;
  color_nombre: string;
  imagen_url: string | null;
  precio_lista: string;
  precio_final: string;
  disponible_en_sucursal: number;
}

export interface ClientePos {
  id_cliente: number;
  nombres: string;
  apellidos: string;
  email: string;
}

export interface LineaReservaPos {
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  cantidad: number;
}

export interface ReservaPos {
  id_reserva: number;
  codigo: string;
  estado: string;
  fecha_hora_atencion: string;
  cliente: ClientePos | null;
  lineas: LineaReservaPos[];
}

export interface LineaVentaPos {
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla_codigo: string;
  color_nombre: string;
  imagen_url: string | null;
  cantidad: number;
  precio_lista: string;
  precio_unitario: string;
  subtotal_linea: string;
  motivo_descuento: string | null;
  origen: 'reserva' | 'caja';
}

export interface PagoPos {
  id_pago: number;
  metodo_pago: string;
  monto: string;
  estado: string;
  referencia: string | null;
  monto_recibido: string | null;
  cambio: string | null;
  creado_en: string;
  confirmado_en: string | null;
}

export interface TotalesPos {
  subtotal: string;
  descuento: string;
  total: string;
  iva_incluido: string;
  cupon_aplicado: string | null;
}

export interface PrevisualizacionPos extends TotalesPos {
  lineas: LineaVentaPos[];
  lineas_reserva_excluidas: LineaReservaPos[];
}

export interface VentaPos extends TotalesPos {
  id_venta: number;
  numero_comprobante: string;
  estado: EstadoVentaPos;
  fecha_venta: string;
  id_sucursal: number;
  nombre_sucursal: string;
  direccion_sucursal: string | null;
  cajero_nombre: string | null;
  cliente: ClientePos | null;
  reserva_codigo: string | null;
  lineas: LineaVentaPos[];
  lineas_reserva_excluidas: LineaReservaPos[];
  pagos: PagoPos[];
}

/** Cupón vigente con usos disponibles. Describe el cupón; el descuento lo calcula `previsualizar`. */
export interface CuponPos {
  codigo: string;
  nombre: string;
  descripcion: string | null;
  tipo_descuento: 'porcentaje' | 'monto_fijo' | string;
  valor_descuento: string;
  alcance: string;
  fecha_fin: string;
  usos_restantes: number | null;
}

export interface PedidoWebEfectivo {
  id_pago: number;
  id_venta: number;
  numero_comprobante: string;
  cliente_nombre: string | null;
  total: string;
  creado_en: string;
}

export interface SucursalOpcion {
  id_sucursal: number;
  nombre: string;
}

export const ETIQUETA_METODO: Record<string, string> = {
  efectivo: 'Efectivo',
  tarjeta_debito: 'Tarjeta de débito',
  tarjeta_credito: 'Tarjeta de crédito',
  qr: 'QR',
  transferencia: 'Transferencia',
};
