/**
 * Modelos e interfaces TypeScript para la vista principal de Inicio (CU18 y CU36).
 * Mapeo 1:1 con los esquemas Pydantic del backend de FastAPI.
 */

export interface VarianteRecomendada {
  id_variante: number;
  sku: string;
  talla: string;
  id_talla: number;
  color: string;
  id_color: number;
  codigo_hex?: string | null;
  precio_extra: number;
  disponible: boolean;
  cantidad_disponible: number;
}

export interface ProductoRecomendadoItem {
  id_producto: number;
  nombre: string;
  descripcion?: string | null;
  categoria: string;
  id_categoria: number;
  coleccion?: string | null;
  id_coleccion?: number | null;
  temporada?: string | null;
  id_temporada?: number | null;
  precio_base: number | string;
  imagen_url?: string | null;
  modelo_ar_url?: string | null;
  activo: boolean;
  badge_editorial?: string | null;
  subtitulo_atelier?: string | null;
  tono_principal?: string | null;
  score_relevancia: number;
  motivo_individual?: string | null;
  stock_total_disponible: number;
  variantes: VarianteRecomendada[];
}

export interface RecomendacionesResponse {
  tiene_historial: boolean;
  motivo_general?: string | null;
  boutique_referencia?: string | null;
  mensaje_empty_state?: string | null;
  total_recomendados: number;
  items: ProductoRecomendadoItem[];
}
