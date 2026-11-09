/** Contratos de `/api/v1/mi-perfil-empleado` (copiados del backend). */

export interface EmpresaPerfil {
  codigo: string;
  nombre: string;
  moneda: string;
}

export interface SucursalPerfil {
  id_sucursal: number;
  nombre: string | null;
  es_principal: boolean;
}

export interface PerfilEmpleado {
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  telefono: string | null;
  rol: string;
  empresa: EmpresaPerfil | null;
  /** El administrador opera en todas las sucursales de su empresa (RN07). */
  todas_las_sucursales: boolean;
  sucursales: SucursalPerfil[];
  ultimo_acceso: string | null;
}

export interface PerfilEmpleadoActualizar {
  nombres?: string;
  apellidos?: string;
  telefono?: string | null;
}

export interface CambioContrasena {
  contrasena_actual: string;
  contrasena_nueva: string;
}

export const NOMBRES_ROL: Record<string, string> = {
  administrador: 'Administrador',
  encargado_sucursal: 'Encargado de sucursal',
  cajero: 'Cajero',
};
