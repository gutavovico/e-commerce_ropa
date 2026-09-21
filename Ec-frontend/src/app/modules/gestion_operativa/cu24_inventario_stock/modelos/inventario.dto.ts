/**
 * Modelos y DTOs para CU24: Gestionar Inventario, Stock y Existencias por Sucursal.
 * Contratos fuertemente tipados sincronizados con FastAPI / PostgreSQL Neon.
 */

export type EstadoStock = 'optimo' | 'alerta_baja' | 'agotado';

export type TipoMovimientoInventario =
  | 'ingreso_proveedor'
  | 'ajuste_positivo'
  | 'ajuste_negativo'
  | 'transferencia_salida'
  | 'transferencia_entrada'
  | 'venta_confirmada'
  | 'cancelacion_pedido'
  | 'reserva'
  | 'liberacion_reserva'
  | 'venta'
  | 'devolucion'
  | 'ajuste';

export type TipoAjusteManual = 'incremento' | 'decremento';

export interface DatosVarianteInventario {
  id_variante: number;
  id_producto: number;
  nombre_prenda: string;
  sku: string;
  talla: string;
  color_nombre: string;
  color_hex: string;
  precio_base: number;
  precio_final: number;
  imagen_url?: string | null;
  categoria_nombre: string;
}

export interface DatosSucursalInventario {
  id_sucursal: number;
  nombre: string;
  ciudad: string;
}

export interface InventarioItemAdmin {
  id_inventario: number;
  id_sucursal: number;
  id_variante: number;
  cantidad_disponible: number;
  cantidad_reservada: number;
  stock_total: number;
  stock_minimo: number;
  stock_alerta: number;
  estado: string;
  estado_calculado: EstadoStock;
  actualizado_en: string;
  sucursal: DatosSucursalInventario;
  variante: DatosVarianteInventario;
}

export interface MovimientoKardexAdmin {
  id_movimiento: number;
  id_inventario: number;
  tipo_movimiento: TipoMovimientoInventario | string;
  cantidad: number;
  saldo_anterior: number;
  saldo_nuevo: number;
  motivo: string;
  referencia_documento?: string | null;
  id_usuario?: number | null;
  usuario_nombre?: string | null;
  creado_en: string;
}

export interface HistorialKardexOut {
  id_inventario: number;
  prenda_sku: string;
  sucursal_nombre: string;
  saldo_actual: number;
  movimientos: MovimientoKardexAdmin[];
}

export interface InventarioCrearPayload {
  id_sucursal: number;
  id_variante: number;
  id_temporada?: number;
  cantidad_inicial: number;
  stock_minimo: number;
  stock_alerta: number;
  referencia_documento?: string;
  observacion?: string;
}

export interface InventarioAjustePayload {
  tipo_ajuste: TipoAjusteManual;
  cantidad: number;
  motivo: string;
  referencia_documento?: string;
}

export interface TransferenciaPayload {
  id_sucursal_origen: number;
  id_sucursal_destino: number;
  id_variante: number;
  cantidad: number;
  motivo: string;
}

export interface ComprobanteTransferenciaOut {
  mensaje: string;
  id_sucursal_origen: number;
  id_sucursal_destino: number;
  id_variante: number;
  sku: string;
  cantidad_transferida: number;
  saldo_origen_nuevo: number;
  saldo_destino_nuevo: number;
  fecha: string;
}

export interface FiltrosInventario {
  id_sucursal?: number | null;
  id_categoria?: number | null;
  estado_stock?: string | null;
  q?: string | null;
  pagina?: number;
  limite?: number;
}

export interface ListaPaginadaInventario {
  items: InventarioItemAdmin[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

export interface DisponibilidadSucursalOut {
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad: string;
  direccion: string;
  cantidad_disponible: number;
  estado: string;
}

export interface DisponibilidadPublicaOut {
  id_variante: number;
  sku: string;
  nombre_prenda: string;
  sucursales: DisponibilidadSucursalOut[];
}
