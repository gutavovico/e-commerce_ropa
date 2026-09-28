/**
 * Modelos y DTOs tipados para CU31: Generar reportes ejecutivos y consultas por voz.
 * Nomenclatura oficial: "Generar reportes ejecutivos y consultas por voz"
 */

export type ModuloReporte = 'ventas' | 'reservas' | 'inventario' | 'bitacora';

export type FormatoReporte = 'excel' | 'pdf' | 'csv';

export type RangoTemporal =
  | 'hoy'
  | 'ayer'
  | 'esta_semana'
  | 'este_mes'
  | 'anio_actual'
  | 'personalizado';

export type IntencionVoz = 'exportar' | 'consultar' | 'filtrar';

export interface ComandoVozIn {
  texto_dictado: string;
}

export interface ComandoVozOut {
  texto_dictado: string;
  intencion: IntencionVoz;
  modulo: ModuloReporte;
  formato: FormatoReporte;
  periodo: RangoTemporal;
  id_sucursal?: number | null;
  nombre_sucursal?: string | null;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  confianza: number;
  accion_recomendada: string;
}

export interface ReporteFiltros {
  modulo: ModuloReporte;
  formato: FormatoReporte;
  periodo: RangoTemporal;
  id_sucursal?: number | null;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
}

export interface ResumenFinanciero {
  total_ingresos?: number;
  promedio_ticket?: number;
  total_reservas?: number;
  total_unidades?: number;
  valor_total_inventario?: number;
  total_operaciones?: number;
  [key: string]: any;
}

export interface ReportePrevisualizacion {
  modulo: ModuloReporte;
  formato: FormatoReporte;
  total_registros: number;
  fecha_corte: string;
  nombre_archivo_sugerido: string;
  resumen_financiero?: ResumenFinanciero | null;
}

export interface SucursalOpcionReporte {
  id_sucursal: number;
  nombre: string;
  ciudad?: string;
}
