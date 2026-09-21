/**
 * Modelos e interfaces TypeScript para CU05: Consultar Catálogo de Productos.
 * Contrato estricto sincronizado con Pydantic CatalogoOut en Ec-backend.
 */

export interface ColorItem {
  id_color: number;
  nombre: string;
  codigo_hex?: string;
}

export interface CategoriaResumenItem {
  id_categoria: number;
  nombre: string;
  total_prendas: number;
}

export interface ProductoCatalogoItem {
  id_producto: number;
  nombre: string;
  descripcion?: string | null;
  precio_base: number | string;
  precio_final: number | string;
  tiene_descuento: boolean;
  porcentaje_descuento?: number | null;
  imagen_url?: string | null;
  categoria_id: number;
  categoria_nombre: string;
  subtitulo_atelier: string;
  etiqueta_badge?: string | null;
  rating_promedio: number;
  tallas_disponibles: string[];
  colores_disponibles: ColorItem[];
  stock_total_disponible: number;
  tiene_stock: boolean;
  es_favorito: boolean;
}

export interface CatalogoRespuesta {
  resumen_categorias: CategoriaResumenItem[];
  total_articulos: number;
  pagina_actual: number;
  limite: number;
  total_paginas: number;
  tiene_siguiente: boolean;
  tiene_anterior: boolean;
  categoria_seleccionada_id?: number | null;
  items: ProductoCatalogoItem[];
}

export interface ParametrosConsultaCatalogo {
  categoria_id?: number | null;
  ordenar_por?: string;
  pagina?: number;
  limite?: number;
}
