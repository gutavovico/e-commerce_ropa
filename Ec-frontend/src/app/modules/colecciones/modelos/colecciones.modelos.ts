/**
 * Modelos e interfaces TypeScript para CU36: Consultar Colecciones (Frontend Web).
 * Mapeo 1:1 estricto con los esquemas Pydantic del backend FastAPI.
 */

export interface ColorSwatch {
  nombre: string;
  hex: string;
}

export interface VarianteColeccion {
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

export interface ProductoColeccionItem {
  id_producto: number;
  nombre: string;
  descripcion?: string | null;
  categoria: string;
  id_categoria: number;
  precio_base: number;
  imagen_url?: string | null;
  badge_editorial?: string | null;
  subtitulo_atelier?: string | null;
  tono_principal?: string | null;
  stock_total_disponible: number;
  variantes: VarianteColeccion[];
  colores?: ColorSwatch[];
}

export interface ColeccionResumen {
  id_coleccion: number;
  nombre: string;
  descripcion?: string | null;
  temporada_id: number;
  temporada_nombre: string;
  temporada_tipo?: string | null;
  proveedor_nombre?: string | null;
  taller_origen?: string | null;
  es_destacada: boolean;
  precio_desde: number;
  total_prendas: number;
  piezas_clave: ProductoColeccionItem[];
  imagen_portada?: string | null;
  badge_edicion?: string | null;
  estado_disponibilidad?: string | null;
}

export interface ColeccionesActivasResponse {
  temporada_activa_id?: number | null;
  temporada_activa_nombre?: string | null;
  temporada_activa_tipo?: string | null;
  coleccion_destacada?: ColeccionResumen | null;
  otras_colecciones: ColeccionResumen[];
  total_colecciones: number;
}

export interface ColeccionDetalle {
  id_coleccion: number;
  nombre: string;
  descripcion?: string | null;
  temporada_id: number;
  temporada_nombre: string;
  temporada_tipo?: string | null;
  proveedor_nombre?: string | null;
  taller_origen?: string | null;
  total_prendas: number;
  productos: ProductoColeccionItem[];
  mensaje_empty_state?: string | null;
}
