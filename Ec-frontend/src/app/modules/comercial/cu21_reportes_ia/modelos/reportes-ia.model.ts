/**
 * Modelos e interfaces TypeScript estrictas para P2-CU21: Generar reporte con IA
 * con soporte de moneda nacional Bolivianos (Bs. / BOB) y tipo de cambio oficial.
 */

import { CatalogoReporteItem } from '../../../plataforma/superadmin/modelos/superadmin.model';

export type EstadoSolicitudReporteIa =
  | 'completada'
  | 'ambigua'
  | 'no_soportada'
  | 'rechazada';

export type FormatoVisualizacionIa =
  | 'tabla'
  | 'barras'
  | 'linea'
  | 'torta'
  | 'ambos';

export interface SucursalResumenReporteIa {
  id_sucursal: number;
  nombre: string;
  ciudad?: string | null;
}

export interface CategoriaResumenReporteIa {
  id_categoria: number;
  nombre: string;
}

export interface ContextoReportesIaEmpresa {
  id_tenant: number;
  nombre_empresa: string;
  moneda_empresa: string;
  simbolo_moneda: string;
  tipo_cambio_bob: number | string;
  catalogo_activo: CatalogoReporteItem[];
  sucursales_activas: SucursalResumenReporteIa[];
  categorias_empresa: CategoriaResumenReporteIa[];
  ejemplos_destacados: string[];
}

export interface GenerarReporteIaPeticion {
  prompt_texto: string;
  codigo_reporte_forzado?: string | null;
  formato_preferido?: FormatoVisualizacionIa | null;
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  id_sucursal?: number | null;
  id_categoria?: number | null;
  tipo_cambio_bob: number;
}

export interface InterpretacionReporteIa {
  estado: EstadoSolicitudReporteIa;
  codigo_reporte: string | null;
  nombre_reporte: string | null;
  vista_origen: string | null;
  fecha_inicio: string | null;
  fecha_fin: string | null;
  id_sucursal: number | null;
  nombre_sucursal: string | null;
  id_categoria: number | null;
  nombre_categoria: string | null;
  tipo_grafico_sugerido: 'tabla' | 'barras' | 'linea' | 'torta';
  formato_visualizacion: FormatoVisualizacionIa;
  explicacion_ia: string;
  origen_motor: string;
}

export interface PuntoGraficoReporte {
  etiqueta: string;
  valor: number;
  valor_secundario?: number | null;
  unidad: string;
}

export interface ExportacionRegistrada {
  formato: 'pdf' | 'excel';
  exportado_en: string;
  usuario_email?: string;
}

export interface SolicitudReporteIaResultado {
  id_solicitud: number;
  estado: EstadoSolicitudReporteIa;
  mensaje_estado: string;
  prompt_original: string;
  codigo_reporte: string | null;
  titulo_reporte: string | null;
  interpretacion: InterpretacionReporteIa;
  moneda: string;
  simbolo_moneda: string;
  tipo_cambio_bob: number | string;
  formato_visualizacion: FormatoVisualizacionIa;
  tipo_grafico: 'tabla' | 'barras' | 'linea' | 'torta';
  columnas: string[];
  filas: (string | number | null)[][];
  serie_grafico: PuntoGraficoReporte[];
  resumen_kpis_bob: Record<string, number | string>;
  sin_datos: boolean;
  ejemplos_sugeridos: string[];
  exportaciones: ExportacionRegistrada[];
  creado_en: string;
}

export interface SolicitudReporteIaHistorial {
  id_solicitud: number;
  id_tenant: number | null;
  id_usuario: number;
  comando_voz_texto: string;
  tipo_reporte: string | null;
  estado: string;
  formato_visualizacion: string;
  mensaje_estado: string | null;
  exportaciones: ExportacionRegistrada[];
  creado_en: string;
}

