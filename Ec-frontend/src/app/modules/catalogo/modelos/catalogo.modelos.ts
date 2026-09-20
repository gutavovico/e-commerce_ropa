/**
 * Modelos e interfaces TypeScript para el módulo de Catálogo y Búsqueda (CU06).
 * Alineado con los esquemas Pydantic del backend de FastAPI.
 */

export interface VarianteResumen {
  id_variante: number;
  sku: string;
  talla: string;
  id_talla: number;
  color: string;
  id_color: number;
  codigo_hex?: string;
  precio_extra: number;
  disponible: boolean;
  cantidad_disponible: number;
}

export interface ProductoItem {
  id_producto: number;
  nombre: string;
  descripcion?: string;
  categoria: string;
  id_categoria: number;
  coleccion?: string;
  id_coleccion?: number;
  temporada?: string;
  id_temporada?: number;
  precio_base: number;
  imagen_url?: string;
  modelo_ar_url?: string;
  activo: boolean;
  badge_editorial?: string;
  subtitulo_atelier?: string;
  talla_sugerida?: string;
  color_sugerido?: string;
  variantes: VarianteResumen[];
  en_favoritos?: boolean;
}

export interface PaginacionMeta {
  total_registros: number;
  pagina_actual: number;
  limite: number;
  total_paginas: number;
  tiene_siguiente: boolean;
  tiene_anterior: boolean;
}

export interface ProductoPaginado {
  items: ProductoItem[];
  paginacion: PaginacionMeta;
  filtros_aplicados: Record<string, any>;
}

export interface OpcionFiltro {
  id: number;
  codigo?: string;
  nombre: string;
  conteo?: number;
  extra?: string;
}

export interface FiltrosDisponibles {
  temporadas: OpcionFiltro[];
  colecciones: OpcionFiltro[];
  categorias: OpcionFiltro[];
  tallas: OpcionFiltro[];
  colores: OpcionFiltro[];
  precio_min_global: number;
  precio_max_global: number;
}

export interface FiltrosBusquedaState {
  q: string;
  temporada_id?: number;
  coleccion_id?: number;
  categoria_id?: number;
  talla?: string;
  color?: string;
  precio_min?: number;
  precio_max?: number;
  solo_en_stock: boolean;
  ordenar_por: 'recientes' | 'precio_asc' | 'precio_desc' | 'nombre_asc' | 'relevancia';
  pagina: number;
  limite: number;
}
