/**
 * DTOs e interfaces TypeScript para CU04: Gestionar Perfil del Cliente.
 * Mapeo estricto 1:1 con los esquemas Pydantic del backend de FastAPI.
 */

export interface ResumenAtelier {
  visitas_registradas: number;
  boutiques_visitadas: number;
  preferencia_textil: string;
  estatus_membresia: string;
}

export interface PerfilCliente {
  // Identidad y Cuenta
  id_usuario: number;
  numero_socio: string;
  email: string;
  rol: string;
  fecha_registro: string;
  miembro_desde: string;
  ultimo_acceso?: string | null;

  // Datos Personales
  nombres: string;
  apellidos: string;
  telefono?: string | null;

  // Preferencias y Datos de Cliente
  fecha_nacimiento?: string | null;
  genero?: string | null;
  talla_preferida?: string | null;
  ciudad_preferida?: number | null;
  acepta_marketing: boolean;

  // Resumen Haute Couture
  resumen_atelier: ResumenAtelier;
}

export interface PerfilClienteActualizar {
  nombres?: string;
  apellidos?: string;
  telefono?: string | null;
  fecha_nacimiento?: string | null;
  genero?: string | null;
  talla_preferida?: string | null;
  ciudad_preferida?: number | null;
  acepta_marketing?: boolean;
}

export interface PedidoHistorico {
  id: string;
  titulo: string;
  boutique: string;
  iconoBoutique: 'flagship' | 'paris' | 'online';
  descripcion: string;
  talla: string;
  color: string;
  precio: number;
  fecha: string;
  estado: string;
  referencia: string;
  imagen: string;
}
