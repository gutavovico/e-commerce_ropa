/**
 * DTOs y Modelos TypeScript para CU29: Visualizar indicadores empresariales.
 * Nomenclatura oficial: "Visualizar indicadores empresariales"
 *
 * Contratos alineados con los esquemas Pydantic v2 del backend
 * (app/modules/comercial/cu29_indicadores/esquemas.py).
 */

export type PeriodoFiltro =
  | '7d'
  | '30d'
  | 'mes_actual'
  | 'anio_actual'
  | 'personalizado';

export interface IndicadoresFiltros {
  periodo: PeriodoFiltro;
  fecha_desde?: string | null;
  fecha_hasta?: string | null;
  id_sucursal?: number | null;
}

export interface ResumenEjecutivo {
  periodo_inicio: string;
  periodo_fin: string;
  ingresos_totales: number;
  variacion_porcentual: number;
  total_transacciones: number;
  variacion_porcentual_transacciones: number;
  margen_estimado: number;
  ticket_promedio: number;
  variacion_porcentual_ticket: number;
  unidades_vendidas: number;
  variacion_porcentual_unidades: number;
}

export interface PuntoSerieTemporal {
  etiqueta_tiempo: string;
  fecha_inicio: string;
  monto_ingresos: number;
  cantidad_ordenes: number;
}

export interface SerieTemporalIngresos {
  agrupacion: 'diaria' | 'semanal' | 'mensual';
  puntos: PuntoSerieTemporal[];
}

export interface ItemRankingProducto {
  id_producto: number;
  nombre_producto: string;
  sku_referencia: string;
  categoria_nombre: string;
  unidades_vendidas: number;
  monto_total_generado: number;
  porcentaje_contribucion: number;
}

export interface RankingProductos {
  limite: number;
  productos: ItemRankingProducto[];
}

export interface CategoriaDistribucion {
  id_categoria: number;
  nombre_categoria: string;
  monto_facturado: number;
  unidades_vendidas: number;
  porcentaje_participacion: number;
}

export interface CanalDistribucion {
  canal_codigo: string;
  canal_nombre: string;
  monto_facturado: number;
  total_ordenes: number;
  porcentaje_participacion: number;
}

export interface DistribucionVentas {
  por_categoria: CategoriaDistribucion[];
  por_canal: CanalDistribucion[];
}

export interface SucursalDesempeno {
  id_sucursal: number;
  nombre_sucursal: string;
  ciudad: string;
  monto_facturado: number;
  total_ventas: number;
  ticket_promedio: number;
  porcentaje_red: number;
}

export interface ComparativaSucursales {
  sucursales: SucursalDesempeno[];
}

export interface DashboardIndicadoresCompleto {
  resumen: ResumenEjecutivo;
  serie_temporal: SerieTemporalIngresos;
  top_productos: RankingProductos;
  distribucion: DistribucionVentas;
  comparativa_sucursales?: ComparativaSucursales | null;
}

export interface SucursalOpcion {
  id_sucursal: number;
  nombre: string;
  ciudad: string;
}
