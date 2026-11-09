/**
 * Modelos e interfaces TypeScript para CU21: Gestionar Sucursales y Ciudades.
 * P2-CU04 B6: las ciudades son un catálogo global de solo lectura para el administrador.
 */

export interface Ciudad {
  id_ciudad: number;
  nombre: string;
  pais: string;
  creado_en: string;
  total_sucursales: number;
}

/** P2-CU04 B7: sucursales activas frente al límite del plan (`limite` nulo: sin límite). */
export interface UsoPlanSucursales {
  uso: number;
  limite: number | null;
  plan: string | null;
}

export interface SucursalPublica {
  id_sucursal: number;
  id_ciudad: number;
  ciudad_nombre: string;
  nombre: string;
  direccion: string;
  telefono: string | null;
  horario_apertura: string;
  horario_cierre: string;
}

export interface SucursalAdmin extends SucursalPublica {
  activa: boolean;
  creado_en: string;
  total_empleados: number;
  total_prendas_stock: number;
  reservas_activas_conteo: number;
}

export interface SucursalCrearPayload {
  id_ciudad: number;
  nombre: string;
  direccion: string;
  telefono?: string | null;
  horario_apertura: string;
  horario_cierre: string;
}

export interface SucursalActualizarPayload {
  id_ciudad?: number;
  nombre?: string;
  direccion?: string;
  telefono?: string | null;
  horario_apertura?: string;
  horario_cierre?: string;
}

export interface SucursalEstadoPayload {
  activa: boolean;
}

export interface FiltrosSucursalAdmin {
  id_ciudad?: number | null;
  activa?: boolean | null;
  q?: string;
}
