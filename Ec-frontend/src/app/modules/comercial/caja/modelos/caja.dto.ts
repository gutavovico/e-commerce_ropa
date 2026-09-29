/**
 * Modelos y contratos de datos TypeScript para el Modulo de Caja
 * [CU17] Registrar cobro en caja y [CU18] Atender entrega de reserva en boutique.
 */

export type MetodoPagoCaja = 'efectivo' | 'tarjeta_pos' | 'qr_estatico';

export interface DetallePrendaCaja {
  id_venta_detalle: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla: string;
  color: string;
  cantidad: number;
  precio_unitario: number;
  subtotal_linea: number;
}

export interface OrdenPendiente {
  id_venta: number;
  numero_comprobante: string;
  fecha_venta: string;
  id_sucursal: number;
  nombre_sucursal: string;
  id_cliente?: number | null;
  cliente_nombre: string;
  cliente_documento?: string | null;
  cliente_telefono?: string | null;
  tipo_venta: string;
  estado: string;
  subtotal: number;
  descuento: number;
  total: number;
  detalles: DetallePrendaCaja[];
}

export interface ListadoOrdenesPendientesResponse {
  total: number;
  items: OrdenPendiente[];
}

export interface CobroCajaRequest {
  id_venta: number;
  monto_recibido: number;
  metodo_pago: MetodoPagoCaja;
  observaciones?: string;
}

export interface CobroCajaResponse {
  id_pago: number;
  id_venta: number;
  numero_comprobante: string;
  monto_total: number;
  monto_recibido: number;
  cambio_devuelto: number;
  metodo_pago: string;
  estado_venta: string;
  estado_pago: string;
  cajero_id?: number | null;
  cajero_nombre: string;
  fecha_cobro: string;
  observaciones?: string | null;
}

export interface PrendaReservaCaja {
  id_reserva_detalle: number;
  id_variante: number;
  sku: string;
  nombre_producto: string;
  talla: string;
  color: string;
  cantidad: number;
  precio_unitario: number;
  ubicacion_percha?: string | null;
}

export interface ReservaPendienteCaja {
  id_reserva: number;
  codigo_reserva: string;
  id_cliente: number;
  cliente_nombre: string;
  cliente_documento?: string | null;
  cliente_telefono?: string | null;
  id_sucursal: number;
  nombre_sucursal: string;
  fecha_hora_atencion: string;
  estado: string;
  canal_origen: string;
  observacion?: string | null;
  prendas: PrendaReservaCaja[];
}

export interface ListadoReservasPendientesResponse {
  total: number;
  items: ReservaPendienteCaja[];
}

export interface ConfirmarEntregaRequest {
  observaciones?: string;
}

export interface EntregaReservaResponse {
  id_reserva: number;
  codigo_reserva: string;
  estado: string;
  atendido_por?: number | null;
  atendido_en?: string | null;
  mensaje: string;
}

export interface NoAsistioReservaResponse {
  id_reserva: number;
  codigo_reserva: string;
  estado: string;
  items_liberados: number;
  mensaje: string;
}

export interface ConvertirVentaResponse {
  id_venta: number;
  numero_comprobante: string;
  id_reserva: number;
  total: number;
  estado_venta: string;
  mensaje: string;
}
