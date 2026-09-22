/**
 * Modelos y DTOs fuertemente tipados para CU20: Gestionar Usuarios y Roles (RBAC).
 */

export type RolUsuario =
  | 'administrador'
  | 'encargado_sucursal'
  | 'cajero'
  | 'cliente';

export interface UsuarioAdmin {
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  nombre_completo: string;
  telefono: string | null;
  rol: RolUsuario;
  id_sucursal: number | null;
  sucursal_nombre: string | null;
  sucursal_ciudad: string | null;
  activo: boolean;
  fecha_registro: string;
  ultimo_acceso: string | null;
}

export interface UsuarioCrearPayload {
  email: string;
  password: string;
  nombres: string;
  apellidos: string;
  telefono?: string | null;
  rol: RolUsuario;
  id_sucursal?: number | null;
}

export interface UsuarioActualizarPayload {
  email?: string;
  nombres?: string;
  apellidos?: string;
  telefono?: string | null;
  rol?: RolUsuario;
  id_sucursal?: number | null;
}

export interface ResetPasswordPayload {
  nuevo_password: string;
}

export interface UsuarioEstadoPayload {
  activo: boolean;
}

export interface ParametrosFiltroUsuario {
  q?: string;
  rol?: string;
  id_sucursal?: number;
  activo?: boolean;
  pagina?: number;
  limite?: number;
}

export interface ListaPaginadaUsuarios {
  items: UsuarioAdmin[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
}
