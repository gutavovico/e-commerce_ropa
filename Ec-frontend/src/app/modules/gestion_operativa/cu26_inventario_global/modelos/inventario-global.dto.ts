/**
 * Contratos y DTOs fuertemente tipados para CU26: Consultar inventario global.
 */

export type EstadoStockGlobal = 'optimo' | 'alerta_baja' | 'agotado';

export type CriterioOrdenacionInventario =
  | 'stock_asc'
  | 'stock_desc'
  | 'nombre_asc'
  | 'nombre_desc'
  | 'sku_asc';

export interface ExistenciaSucursalItem {
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad: string;
  direccion: string;
  telefono: string | null;
  cantidad_disponible: number;
  cantidad_reservada: number;
}

export interface InventarioGlobalItem {
  id_variante: number;
  id_producto: number;
  nombre_producto: string;
  sku: string;
  categoria: string;
  talla: string;
  color: string;
  swatches_hex: string | null;
  total_disponible: number;
  total_reservado: number;
  total_fisico: number;
  estado_stock: EstadoStockGlobal;
  desglose_sucursales: ExistenciaSucursalItem[];
}

export interface MetricasInventarioGlobal {
  total_unidades_red: number;
  variantes_monitoreadas: number;
  alertas_stock_bajo: number;
  sedes_activas: number;
}

export interface FiltrosInventarioGlobal {
  q: string;
  id_categoria: number | null;
  id_sucursal: number | null;
  estado_stock: EstadoStockGlobal | 'todos';
  ordenar_por: CriterioOrdenacionInventario;
  pagina: number;
  limite: number;
}

export interface RespuestaInventarioGlobal {
  items: InventarioGlobalItem[];
  metricas: MetricasInventarioGlobal;
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

// Alias compatibles con la nomenclatura de diseno y backend
export type ExistenciaSucursalItemOut = ExistenciaSucursalItem;
export type InventarioGlobalItemOut = InventarioGlobalItem;
export type MetricasInventarioGlobalOut = MetricasInventarioGlobal;
export type InventarioGlobalFiltros = FiltrosInventarioGlobal;
export type RespuestaInventarioGlobalOut = RespuestaInventarioGlobal;
