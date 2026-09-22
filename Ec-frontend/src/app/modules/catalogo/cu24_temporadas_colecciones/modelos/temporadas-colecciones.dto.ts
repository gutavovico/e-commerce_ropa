/**
 * Contratos de datos (DTO) e interfaces TypeScript para CU24: Gestionar temporadas y colecciones.
 * Nomenclatura oficial: "Gestionar temporadas y colecciones"
 */

export interface TemporadaItem {
  id_temporada: number;
  nombre: string;
  tipo: string | null;
  anio: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado_activo: boolean;
  total_colecciones: number;
  creado_en: string;
  actualizado_en: string;
}

export interface TemporadaCrearDto {
  nombre: string;
  tipo?: string | null;
  anio: number;
  fecha_inicio: string;
  fecha_fin: string;
  estado_activo?: boolean;
}

export interface TemporadaActualizarDto {
  nombre?: string;
  tipo?: string | null;
  anio?: number;
  fecha_inicio?: string;
  fecha_fin?: string;
}

export interface FiltrosTemporadas {
  q?: string;
  anio?: number;
  estado_activo?: 'todos' | 'activas' | 'inactivas';
  ordenar_por?: 'anio_desc' | 'anio_asc' | 'nombre_asc' | 'nombre_desc' | 'fecha_desc';
  pagina?: number;
  limite?: number;
}

export interface RespuestaPaginadaTemporadas {
  items: TemporadaItem[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

export interface ColeccionItem {
  id_coleccion: number;
  id_temporada: number;
  temporada_nombre: string;
  temporada_anio: number;
  nombre: string;
  descripcion: string | null;
  estado_activo: boolean;
  total_productos: number;
  creado_en: string;
  actualizado_en: string;
}

export interface ColeccionCrearDto {
  id_temporada: number;
  nombre: string;
  descripcion?: string | null;
  id_proveedor?: number | null;
  estado_activo?: boolean;
}

export interface ColeccionActualizarDto {
  id_temporada?: number;
  nombre?: string;
  descripcion?: string | null;
  id_proveedor?: number | null;
}

export interface FiltrosColecciones {
  q?: string;
  id_temporada?: number;
  estado_activo?: 'todos' | 'activas' | 'inactivas';
  pagina?: number;
  limite?: number;
}

export interface RespuestaPaginadaColecciones {
  items: ColeccionItem[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}

export interface EstadoConmutarDto {
  estado_activo: boolean;
}

export type PestanaGestion = 'temporadas' | 'colecciones';
