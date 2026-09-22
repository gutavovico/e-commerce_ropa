/**
 * Modelos y DTOs fuertemente tipados para CU25: Gestionar Proveedores.
 * Sincronizados con los esquemas Pydantic v2 del backend FastAPI.
 */

export interface ProveedorItemAdmin {
  id_proveedor: number;
  id_usuario?: number | null;
  razon_social: string;
  nit_rut: string;
  contacto_nombre: string;
  telefono: string;
  email: string;
  direccion: string;
  ciudad: string;
  rubro: string;
  estado_activo: boolean;
  creado_en: string;
  actualizado_en: string;
}

export interface ProveedorCrearPayload {
  razon_social: string;
  nit_rut: string;
  contacto_nombre: string;
  telefono: string;
  email: string;
  direccion: string;
  ciudad: string;
  rubro: string;
}

export interface ProveedorActualizarPayload {
  razon_social?: string;
  nit_rut?: string;
  contacto_nombre?: string;
  telefono?: string;
  email?: string;
  direccion?: string;
  ciudad?: string;
  rubro?: string;
}

export interface ProveedorEstadoPayload {
  estado_activo: boolean;
}

export interface FiltrosProveedores {
  q?: string | null;
  estado_activo?: boolean | null;
  estado?: string | null;
  rubro?: string | null;
  pagina?: number;
  limite?: number;
}

export interface ListaPaginadaProveedores {
  items: ProveedorItemAdmin[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}
