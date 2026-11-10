import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

/** Contratos copiados de `Ec-backend/app/modules/sincronizacion/cu20_conflictos/esquemas.py`. */
export interface ConflictoResumen {
  id_conflicto: number;
  tipo: string;
  estado: 'pendiente' | 'reembolso_pendiente' | 'resuelto';
  creado_en: string;
  id_sucursal: number;
  nombre_sucursal: string | null;
  id_venta: number;
  numero_comprobante: string;
  total: string;
  cliente: string | null;
}

export interface ConflictoDetalle extends ConflictoResumen {
  detalle: { motivo?: string; mensaje?: string; esperado?: unknown; encontrado?: unknown; [clave: string]: unknown };
  lineas: { id_variante: number; nombre_producto: string; sku: string; cantidad: number; precio_unitario: string }[];
  pago: { id_pago: number; metodo_pago: string; monto: string; estado: string; confirmado_en: string | null };
  fecha_compra: string;
  aceptado_por: string | null;
  aceptado_en: string | null;
  resuelto_en: string | null;
  referencia_reembolso: string | null;
  intentos_reembolso: number;
  ultimo_error: string | null;
}

export interface ResumenConflictos {
  pendiente: number;
  reembolso_pendiente: number;
}

export interface EstadoCierre {
  es_ultimo_dia_del_mes: boolean;
  reembolsos_pendientes: number;
}

export interface ResultadoCierre {
  forzado: boolean;
  procesados: number;
  reembolsados: number;
  fallidos: { id_conflicto: number; motivo: string }[];
}

/** P2-CU20 · Conflictos de sincronización (administrador y encargado; el cierre, solo el administrador). */
@Injectable({ providedIn: 'root' })
export class ConflictosService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/conflictos-sync';

  listar(estado?: string): Observable<ConflictoResumen[]> {
    return this.http.get<ConflictoResumen[]>(this.base, { params: estado ? { estado } : {} });
  }

  detalle(id: number): Observable<ConflictoDetalle> {
    return this.http.get<ConflictoDetalle>(`${this.base}/${id}`);
  }

  resumen(): Observable<ResumenConflictos> {
    return this.http.get<ResumenConflictos>(`${this.base}/resumen`);
  }

  aceptarReembolso(id: number): Observable<ConflictoDetalle> {
    return this.http.post<ConflictoDetalle>(`${this.base}/${id}/aceptar-reembolso`, {});
  }

  estadoCierre(): Observable<EstadoCierre> {
    return this.http.get<EstadoCierre>(`${this.base}/cierre`);
  }

  procesarCierre(forzar: boolean): Observable<ResultadoCierre> {
    return this.http.post<ResultadoCierre>(`${this.base}/procesar-cierre`, { forzar });
  }
}
