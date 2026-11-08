/**
 * DTOs e Interfaces para CU10: Utilizar Vestidor Virtual (Dos Motores: Local e IA Decart).
 *
 * Mapea los contratos de API de FastAPI:
 * - POST /api/v1/vestidor/token
 * - POST /api/v1/vestidor/sesion
 * - PATCH /api/v1/vestidor/sesion/{id_sesion_ar}
 */

export type TipoMotorVestidor = 'local' | 'ia';

export interface TokenVestidorDecartOut {
  token: string;
  expira_en_segundos: number;
  servicio: string;
}

export interface SesionVestidorCrearIn {
  id_producto: number;
  dispositivo?: string;
  motor: TipoMotorVestidor;
  duracion_segundos?: number;
  resultado_url?: string;
  genero_interes?: boolean;
}

export interface SesionVestidorActualizarIn {
  resultado_url?: string;
  genero_interes?: boolean;
}

export interface SesionVestidorOut {
  id_sesion_ar: number;
  id_cliente: number;
  id_producto: number;
  dispositivo?: string;
  motor: TipoMotorVestidor;
  duracion_segundos?: number;
  fecha_hora: string;
  resultado_url?: string;
  genero_interes: boolean;
}

export interface MetricasAjusteTextil {
  toleranciaBusto: string;
  elasticidad: string;
  caidaTextil: string;
  holguraSisaMm: number;
  estaturaReferenciaM: number;
}

