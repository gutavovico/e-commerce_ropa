/**
 * Modelos y DTOs para CU30: Consultar bitacora.
 * Nomenclatura oficial: "Consultar bitacora"
 */

export type SeveridadBitacora = 'INFO' | 'WARN' | 'ERROR' | 'CRITICAL';
export type CriterioOrdenBitacora =
  | 'creado_en_desc'
  | 'creado_en_asc'
  | 'severidad_desc'
  | 'accion_asc';

export interface BitacoraFiltros {
  fecha_inicio?: string | null;
  fecha_fin?: string | null;
  severidad?: SeveridadBitacora | null;
  tabla_modulo?: string | null;
  accion?: string | null;
  q?: string | null;
  ordenar_por: CriterioOrdenBitacora;
  pagina: number;
  limite: number;
}

export interface BitacoraEventoResumen {
  id_bitacora: number;
  id_usuario: number | null;
  usuario_nombre: string | null;
  accion: string;
  tabla_modulo: string;
  direccion_ip: string | null;
  severidad: SeveridadBitacora;
  tiene_payload: boolean;
  creado_en: string;
}

export interface BitacoraEventoDetalle extends BitacoraEventoResumen {
  payload_anterior: Record<string, unknown> | null;
  payload_nuevo: Record<string, unknown> | null;
}

export interface BitacoraMetricas {
  total_eventos: number;
  eventos_criticos: number;
  advertencias_errores: number;
  usuarios_activos: number;
}

export interface BitacoraListadoRespuesta {
  items: BitacoraEventoResumen[];
  total: number;
  pagina: number;
  limite: number;
  total_paginas: number;
  metricas: BitacoraMetricas;
}
