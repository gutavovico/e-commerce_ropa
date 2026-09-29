/**
 * Servicio HTTP reactivo para el Modulo de Caja
 * [CU17] Registrar cobro en caja y [CU18] Atender entrega de reserva en boutique.
 */

import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpParams } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import {
  CobroCajaRequest,
  CobroCajaResponse,
  ConfirmarEntregaRequest,
  ConvertirVentaResponse,
  EntregaReservaResponse,
  ListadoOrdenesPendientesResponse,
  ListadoReservasPendientesResponse,
  NoAsistioReservaResponse,
  OrdenPendiente,
  ReservaPendienteCaja,
} from '../modelos/caja.dto';

@Injectable({
  providedIn: 'root',
})
export class CajaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/caja';

  // Estados reactivos internos (Signals)
  private readonly _ordenesPendientes = signal<OrdenPendiente[]>([]);
  private readonly _reservasPendientes = signal<ReservaPendienteCaja[]>([]);
  private readonly _ordenSeleccionada = signal<OrdenPendiente | null>(null);
  private readonly _reservaSeleccionada = signal<ReservaPendienteCaja | null>(null);
  private readonly _cargando = signal<boolean>(false);
  private readonly _error = signal<string | null>(null);

  // Senales publicas de solo lectura
  readonly ordenesPendientes = this._ordenesPendientes.asReadonly();
  readonly reservasPendientes = this._reservasPendientes.asReadonly();
  readonly ordenSeleccionada = this._ordenSeleccionada.asReadonly();
  readonly reservaSeleccionada = this._reservaSeleccionada.asReadonly();
  readonly cargando = this._cargando.asReadonly();
  readonly error = this._error.asReadonly();

  // Senales computadas utiles para la UI
  readonly totalOrdenesPendientes = computed(() => this._ordenesPendientes().length);
  readonly totalReservasPendientes = computed(() => this._reservasPendientes().length);

  /**
   * Establece manualmente la orden seleccionada para atencion en mostrador.
   */
  seleccionarOrden(orden: OrdenPendiente | null): void {
    this._ordenSeleccionada.set(orden);
  }

  /**
   * Establece manualmente la reserva seleccionada para entrega o conversion.
   */
  seleccionarReserva(reserva: ReservaPendienteCaja | null): void {
    this._reservaSeleccionada.set(reserva);
  }

  /**
   * Limpia el mensaje de error activo.
   */
  limpiarError(): void {
    this._error.set(null);
  }

  // =========================================================================
  // METODOS CU17: REGISTRAR COBRO EN CAJA
  // =========================================================================

  /**
   * Consulta las ordenes en estado pendiente dentro de la sucursal del cajero.
   */
  buscarOrdenesPendientes(
    termino?: string,
    fechaDesde?: string,
    fechaHasta?: string
  ): Observable<ListadoOrdenesPendientesResponse> {
    this._cargando.set(true);
    this._error.set(null);

    let params = new HttpParams();
    if (termino && termino.trim()) {
      params = params.set('q', termino.trim());
    }
    if (fechaDesde) {
      params = params.set('fecha_desde', fechaDesde);
    }
    if (fechaHasta) {
      params = params.set('fecha_hasta', fechaHasta);
    }

    return this.http
      .get<ListadoOrdenesPendientesResponse>(`${this.baseUrl}/ordenes-pendientes`, { params })
      .pipe(
        tap((resp) => {
          this._ordenesPendientes.set(resp.items || []);
          // Si la orden seleccionada ya no esta en pendientes, deseleccionar
          const sel = this._ordenSeleccionada();
          if (sel && !resp.items.some((o) => o.id_venta === sel.id_venta)) {
            this._ordenSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  /**
   * Registra el cobro en mostrador de una orden y asienta el comprobante.
   */
  cobrarOrden(idVenta: number, payload: CobroCajaRequest): Observable<CobroCajaResponse> {
    this._cargando.set(true);
    this._error.set(null);

    return this.http
      .post<CobroCajaResponse>(`${this.baseUrl}/cobrar`, payload)
      .pipe(
        tap((resp) => {
          // Remover la orden pagada de la lista local
          this._ordenesPendientes.update((lista) =>
            lista.filter((o) => o.id_venta !== idVenta)
          );
          if (this._ordenSeleccionada()?.id_venta === idVenta) {
            this._ordenSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  // =========================================================================
  // METODOS CU18: ATENDER ENTREGA DE RESERVA EN BOUTIQUE
  // =========================================================================

  /**
   * Consulta las reservas activas y citas de prueba para la boutique del cajero.
   */
  buscarReservasPendientes(
    termino?: string,
    fechaCita?: string
  ): Observable<ListadoReservasPendientesResponse> {
    this._cargando.set(true);
    this._error.set(null);

    let params = new HttpParams();
    if (termino && termino.trim()) {
      params = params.set('q', termino.trim());
    }
    if (fechaCita) {
      params = params.set('fecha_cita', fechaCita);
    }

    return this.http
      .get<ListadoReservasPendientesResponse>(`${this.baseUrl}/reservas-pendientes`, { params })
      .pipe(
        tap((resp) => {
          this._reservasPendientes.set(resp.items || []);
          const sel = this._reservaSeleccionada();
          if (sel && !resp.items.some((r) => r.id_reserva === sel.id_reserva)) {
            this._reservaSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  /**
   * Confirma la entrega de prendas a la clienta para fitting room.
   */
  confirmarEntrega(
    idReserva: number,
    payload?: ConfirmarEntregaRequest
  ): Observable<EntregaReservaResponse> {
    this._cargando.set(true);
    this._error.set(null);

    return this.http
      .post<EntregaReservaResponse>(
        `${this.baseUrl}/reservas/${idReserva}/entregar`,
        payload || {}
      )
      .pipe(
        tap(() => {
          this._reservasPendientes.update((lista) =>
            lista.filter((r) => r.id_reserva !== idReserva)
          );
          if (this._reservaSeleccionada()?.id_reserva === idReserva) {
            this._reservaSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  /**
   * Marca inasistencia de la cita y devuelve las prendas apartadas al stock disponible.
   */
  marcarNoAsistio(idReserva: number): Observable<NoAsistioReservaResponse> {
    this._cargando.set(true);
    this._error.set(null);

    return this.http
      .post<NoAsistioReservaResponse>(
        `${this.baseUrl}/reservas/${idReserva}/no-asistio`,
        {}
      )
      .pipe(
        tap(() => {
          this._reservasPendientes.update((lista) =>
            lista.filter((r) => r.id_reserva !== idReserva)
          );
          if (this._reservaSeleccionada()?.id_reserva === idReserva) {
            this._reservaSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  /**
   * Convierte la reserva en una orden de venta presencial para cobro inmediato en caja.
   */
  convertirAVenta(idReserva: number): Observable<ConvertirVentaResponse> {
    this._cargando.set(true);
    this._error.set(null);

    return this.http
      .post<ConvertirVentaResponse>(
        `${this.baseUrl}/reservas/${idReserva}/convertir-venta`,
        {}
      )
      .pipe(
        tap(() => {
          this._reservasPendientes.update((lista) =>
            lista.filter((r) => r.id_reserva !== idReserva)
          );
          if (this._reservaSeleccionada()?.id_reserva === idReserva) {
            this._reservaSeleccionada.set(null);
          }
        }),
        catchError((err: HttpErrorResponse) => this.procesarErrorHttp(err)),
        finalize(() => this._cargando.set(false))
      );
  }

  /**
   * Procesa de forma defensiva los errores HTTP traduciendolos a mensajes claros.
   */
  private procesarErrorHttp(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error inesperado al procesar la operacion de caja.';

    if (err.status === 401) {
      mensaje = 'Su sesion ha expirado o no es valida. Inicie sesion nuevamente.';
    } else if (err.status === 403) {
      mensaje =
        err.error?.detail ||
        'Acceso restringido: no cuenta con permisos sobre la sucursal de esta orden o reserva.';
    } else if (err.status === 404) {
      mensaje = err.error?.detail || 'El registro solicitado no fue encontrado en el sistema.';
    } else if (err.status === 409) {
      mensaje =
        err.error?.detail ||
        'Conflicto de negocio: la orden o reserva ya fue procesada o se encuentra en estado incompatible.';
    } else if (err.status === 422) {
      mensaje =
        err.error?.detail ||
        'El monto entregado es insuficiente para cubrir el total de la orden.';
    } else if (err.error?.detail && typeof err.error.detail === 'string') {
      mensaje = err.error.detail;
    } else if (err.status === 0) {
      mensaje = 'No se pudo conectar con el servidor. Verifique su conexion de red.';
    }

    this._error.set(mensaje);
    return throwError(() => new Error(mensaje));
  }
}
