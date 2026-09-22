/**
 * Modelos e interfaces TypeScript para CU23: Gestionar Categorias, Tallas y Colores.
 */

export interface CategoriaAdmin {
  id_categoria: number;
  nombre: string;
  id_categoria_padre: number | null;
  padre_nombre?: string | null;
  total_productos: number;
  total_subcategorias: number;
}

export interface CategoriaCrearPayload {
  nombre: string;
  id_categoria_padre: number | null;
}

export interface CategoriaActualizarPayload {
  nombre?: string;
  id_categoria_padre?: number | null;
}

export interface TallaAdmin {
  id_talla: number;
  codigo: string;
  orden: number;
  total_variantes: number;
}

export interface TallaCrearPayload {
  codigo: string;
  orden: number;
}

export interface TallaActualizarPayload {
  codigo?: string;
  orden?: number;
}

export interface ColorAdmin {
  id_color: number;
  nombre: string;
  codigo_hex: string;
  total_variantes: number;
}

export interface ColorCrearPayload {
  nombre: string;
  codigo_hex: string;
}

export interface ColorActualizarPayload {
  nombre?: string;
  codigo_hex?: string;
}

export type TipoAtributo = 'categorias' | 'tallas' | 'colores';
