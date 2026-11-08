/**
 * DTOs para el caso de uso CU02: Iniciar Sesión (FashionStore Web).
 * P2-CU02: el login es solo con correo y contraseña; la respuesta trae la empresa del empleado
 * (`tenant`) y las tiendas del cliente (`empresas`).
 */
import { EmpresaPublica } from '../../../../core/tenant/tenant.models';

export interface LoginPeticion {
  email: string;
  password: string;
  recordar_dispositivo: boolean;
}

export interface LoginRespuesta {
  access_token: string;
  token_type: string;
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  rol: string;
  id_sucursal?: number | null;
  /** Empresa del empleado; null para clientes y super administrador. */
  tenant?: EmpresaPublica | null;
  /** Tiendas disponibles en las que está registrado el cliente; vacía para empleados. */
  empresas?: EmpresaPublica[];
}

export interface UsuarioSesion {
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  rol: string;
  token: string;
  id_sucursal?: number | null;
  /** Empresa del empleado (P2-CU02). */
  tenant?: EmpresaPublica | null;
}

export interface ErrorApiLogin {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
  code?: string;
}
