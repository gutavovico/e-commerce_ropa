/**
 * Servicio Angular para CU30: Consultar bitacora.
 * Nomenclatura oficial: "Consultar bitacora"
 */

import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import {
  BitacoraEventoDetalle,
  BitacoraEventoResumen,
  BitacoraFiltros,
  BitacoraListadoRespuesta,
  BitacoraMetricas,
} from '../modelos/bitacora.dto';

@Injectable({
  providedIn: 'root',
})
export class BitacoraAdminService {
  private readonly http = inject(HttpClient);
  private readonly loginService = inject(LoginService);
  private readonly endpoint = '/api/v1/admin/bitacora';

  // --- Estado Reactivo con Signals ---
  readonly eventos = signal<BitacoraEventoResumen[]>([]);
  readonly metricas = signal<BitacoraMetricas>({
    total_eventos: 0,
    eventos_criticos: 0,
    advertencias_errores: 0,
    usuarios_activos: 0,
  });
  readonly totalEventos = signal<number>(0);
  readonly totalPaginas = signal<number>(1);
  readonly paginaActual = signal<number>(1);
  readonly limitePorPagina = signal<number>(20);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  readonly eventoSeleccionado = signal<BitacoraEventoDetalle | null>(null);
  readonly cargandoDetalle = signal<boolean>(false);
  readonly errorDetalle = signal<string | null>(null);

  /**
   * Construye las cabeceras HTTP con token Bearer JWT.
   */
  private obtenerHeaders(): HttpHeaders {
    const token = this.loginService.obtenerToken();
    return new HttpHeaders({
      Authorization: `Bearer ${token || ''}`,
    });
  }

  /**
   * Consulta la bitacora de auditoria con filtros multicriterio y metricas.
   */
  listar(filtros: BitacoraFiltros): Observable<BitacoraListadoRespuesta> {
    this.cargando.set(true);
    this.error.set(null);

    let params = new HttpParams()
      .set('ordenar_por', filtros.ordenar_por)
      .set('pagina', filtros.pagina.toString())
      .set('limite', filtros.limite.toString());

    if (filtros.fecha_inicio) {
      params = params.set('fecha_inicio', filtros.fecha_inicio);
    }
    if (filtros.fecha_fin) {
      params = params.set('fecha_fin', filtros.fecha_fin);
    }
    if (filtros.severidad) {
      params = params.set('severidad', filtros.severidad);
    }
    if (filtros.tabla_modulo) {
      params = params.set('tabla_modulo', filtros.tabla_modulo);
    }
    if (filtros.accion) {
      params = params.set('accion', filtros.accion);
    }
    if (filtros.q) {
      params = params.set('q', filtros.q);
    }

    return this.http
      .get<BitacoraListadoRespuesta>(this.endpoint, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((respuesta) => {
          this.eventos.set(respuesta.items || []);
          this.metricas.set(
            respuesta.metricas || {
              total_eventos: 0,
              eventos_criticos: 0,
              advertencias_errores: 0,
              usuarios_activos: 0,
            }
          );
          this.totalEventos.set(respuesta.total);
          this.totalPaginas.set(respuesta.total_paginas);
          this.paginaActual.set(respuesta.pagina);
          this.limitePorPagina.set(respuesta.limite);
        }),
        catchError((err: HttpErrorResponse) => {
          let mensaje = 'Error al cargar la bitacora de auditoria.';
          if (err.status === 403) {
            mensaje = 'Acceso denegado. Se requiere rol de superadministrador.';
          } else if (err.status === 401) {
            mensaje = 'Sesion expirada o invalida. Por favor reingrese al sistema.';
          } else if (err.error?.detail) {
            mensaje = err.error.detail;
          }
          this.error.set(mensaje);
          return throwError(() => new Error(mensaje));
        }),
        finalize(() => {
          this.cargando.set(false);
        })
      );
  }

  /**
   * Obtiene el detalle de un evento unitario de bitacora incluyendo snapshots JSON.
   */
  obtenerDetalle(id_bitacora: number): Observable<BitacoraEventoDetalle> {
    this.cargandoDetalle.set(true);
    this.errorDetalle.set(null);

    return this.http
      .get<BitacoraEventoDetalle>(`${this.endpoint}/${id_bitacora}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((detalle) => {
          this.eventoSeleccionado.set(detalle);
        }),
        catchError((err: HttpErrorResponse) => {
          let mensaje = 'Error al recuperar el detalle del evento de auditoria.';
          if (err.status === 404) {
            mensaje = 'El evento solicitado no existe en la bitacora.';
          } else if (err.error?.detail) {
            mensaje = err.error.detail;
          }
          this.errorDetalle.set(mensaje);
          return throwError(() => new Error(mensaje));
        }),
        finalize(() => {
          this.cargandoDetalle.set(false);
        })
      );
  }

  /**
   * Cierra el modal de inspeccion de payloads de auditoria.
   */
  cerrarModalDetalle(): void {
    this.eventoSeleccionado.set(null);
    this.errorDetalle.set(null);
  }
}
