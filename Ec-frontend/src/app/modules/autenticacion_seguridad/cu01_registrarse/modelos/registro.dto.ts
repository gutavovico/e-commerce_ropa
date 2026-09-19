/**
 * DTOs para el caso de uso CU01: Registrarse (FashionStore Web).
 */

export interface RegistroClientePeticion {
  email: string;
  password: string;
  nombres: string;
  apellidos: string;
  telefono?: string | null;
  talla_preferida?: string | null;
  ciudad_preferida?: number | null;
}

export interface RegistroClienteRespuesta {
  id_usuario: number;
  email: string;
  nombres: string;
  apellidos: string;
  rol: string;
  token_acceso: string;
  tipo_token: string;
}

export interface ErrorApi {
  detail: string | Array<{ loc: string[]; msg: string; type: string }>;
  code?: string;
}
