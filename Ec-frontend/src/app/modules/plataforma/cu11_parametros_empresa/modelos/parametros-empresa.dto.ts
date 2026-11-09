/**
 * P2-CU11 · Parámetros de la empresa.
 * Spec: `.specs/finalized/P2-CU11-parametros-empresa/spec.md` §3.
 */

/** Respuesta de `GET`/`PUT /api/v1/admin/configuracion`. */
export interface ParametrosEmpresa {
  moneda: 'BOB' | 'USD';
  zona_horaria: string;
  horas_vencimiento_reserva: number;
  dias_cambio_prenda: number;
  operacion_offline_habilitada: boolean;
  dias_antiguedad_offline: number;
  actualizado_en: string;
  /** Fix de P2-CU11 (M3): la empresa ya tiene ventas o pagos y no puede cambiar de moneda. */
  moneda_bloqueada: boolean;
}

/** Fix de P2-CU11 (M4): la única zona horaria admitida. */
export const ZONAS_HORARIAS = [{ valor: 'America/La_Paz', nombre: 'Bolivia (America/La_Paz)' }] as const;

/** Parámetros editables (fix de P2-CU11: también moneda y zona horaria). */
export type ParametrosEmpresaPayload = Pick<
  ParametrosEmpresa,
  | 'moneda'
  | 'zona_horaria'
  | 'horas_vencimiento_reserva'
  | 'dias_cambio_prenda'
  | 'operacion_offline_habilitada'
  | 'dias_antiguedad_offline'
>;

/** C3: los mismos rangos que valida el servidor. */
export const RANGOS_PARAMETROS = {
  horas_vencimiento_reserva: { min: 1, max: 168, porDefecto: 24 },
  dias_cambio_prenda: { min: 0, max: 90, porDefecto: 15 },
  dias_antiguedad_offline: { min: 1, max: 30, porDefecto: 7 },
} as const;
