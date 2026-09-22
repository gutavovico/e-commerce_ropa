/**
 * Modelos e interfaces TypeScript para CU22: Gestionar Prendas, Productos y Variantes (SKUs).
 */

export interface ProductoResumenAdmin {
  id_producto: number;
  nombre: string;
  descripcion: string | null;
  precio_base: number;
  id_categoria: number;
  categoria_nombre: string | null;
  id_coleccion: number | null;
  coleccion_nombre: string | null;
  imagen_url: string | null;
  modelo_ar_url: string | null;
  activo: boolean;
  total_variantes: number;
  stock_total: number;
  creado_en?: string | null;
}

export interface VarianteAdmin {
  id_variante: number;
  id_producto: number;
  id_talla: number;
  talla_codigo: string;
  id_color: number;
  color_nombre: string;
  color_hex: string | null;
  sku: string;
  precio_extra: number;
  precio_final: number;
  activo: boolean;
  stock_disponible: number;
  creado_en?: string | null;
}

export interface ProductoDetalleAdmin extends ProductoResumenAdmin {
  variantes: VarianteAdmin[];
}

export interface ProductoCrearPayload {
  nombre: string;
  id_categoria: number;
  precio_base: number;
  descripcion?: string | null;
  id_coleccion?: number | null;
  imagen_url?: string | null;
  modelo_ar_url?: string | null;
  activo: boolean;
}

export interface ProductoActualizarPayload {
  nombre?: string;
  id_categoria?: number;
  precio_base?: number;
  descripcion?: string | null;
  id_coleccion?: number | null;
  imagen_url?: string | null;
  modelo_ar_url?: string | null;
  activo?: boolean;
}

export interface VarianteItemPayload {
  id_talla: number;
  id_color: number;
  sku?: string | null;
  precio_extra: number;
}

export interface MatrizVariantesPayload {
  ids_tallas: number[];
  ids_colores: number[];
  precio_extra_defecto: number;
}

export interface VarianteEdicionItem {
  id_talla: number;
  talla_codigo: string;
  id_color: number;
  color_nombre: string;
  color_hex: string | null;
  sku: string;
  precio_extra: number;
  precio_final: number;
}

export interface ParametrosFiltroProducto {
  q?: string;
  id_categoria?: number;
  activo?: boolean;
  pagina?: number;
  limite?: number;
}
