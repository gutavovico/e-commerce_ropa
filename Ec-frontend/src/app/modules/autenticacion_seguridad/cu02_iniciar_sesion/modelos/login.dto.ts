/**
 * DTOs para el caso de uso CU02: Iniciar Sesión (FashionStore Web).
 */

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
}

export interface UsuarioSesion {
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  rol: string;
  token: string;
  id_sucursal?: number | null;
}

export interface ErrorApiLogin {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
  code?: string;
}
