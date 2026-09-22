export type TipoDescuento = 'porcentaje' | 'monto_fijo';
export type AlcancePromocion = 'global' | 'categoria' | 'producto';
export type EstadoVigencia = 'vigente' | 'proxima' | 'expirada';

export interface PromocionItem {
  id_promocion: number;
  nombre: string;
  descripcion: string | null;
  codigo_cupon: string | null;
  tipo_descuento: TipoDescuento;
  valor_descuento: number;
  fecha_inicio: string;
  fecha_fin: string;
  tope_descuento: number | null;
  limite_usos: number | null;
  usos_actuales: number;
  alcance: AlcancePromocion;
  id_categoria: number | null;
  id_producto: number | null;
  estado_activo: boolean;
  creado_en?: string;
  actualizado_en?: string;
  categoria_nombre?: string | null;
  producto_nombre?: string | null;
}

export interface PromocionCrearDto {
  nombre: string;
  descripcion?: string | null;
  codigo_cupon?: string | null;
  tipo_descuento: TipoDescuento;
  valor_descuento: number;
  fecha_inicio: string;
  fecha_fin: string;
  tope_descuento?: number | null;
  limite_usos?: number | null;
  alcance: AlcancePromocion;
  id_categoria?: number | null;
  id_producto?: number | null;
  estado_activo?: boolean;
}

export interface PromocionActualizarDto {
  nombre?: string;
  descripcion?: string | null;
  codigo_cupon?: string | null;
  tipo_descuento?: TipoDescuento;
  valor_descuento?: number;
  fecha_inicio?: string;
  fecha_fin?: string;
  tope_descuento?: number | null;
  limite_usos?: number | null;
  alcance?: AlcancePromocion;
  id_categoria?: number | null;
  id_producto?: number | null;
  estado_activo?: boolean;
}

export interface EstadoConmutarDto {
  estado_activo: boolean;
}

export interface FiltrosPromociones {
  q?: string;
  tipo_descuento?: TipoDescuento | 'todos';
  estado_activo?: 'todos' | 'activas' | 'inactivas' | boolean;
  alcance?: AlcancePromocion | 'todos';
  pagina?: number;
  limite?: number;
  ordenar_por?: string;
}

export interface MetricasPromociones {
  promociones_activas: number;
  cupones_vigentes: number;
  descuento_promedio: number;
  usos_totales: number;
}

export interface RespuestaPaginadaPromociones {
  items: PromocionItem[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
  metricas?: MetricasPromociones;
}
