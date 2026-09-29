import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';

import { MisReservas, Reserva, ResumenReservas } from '../modelos/reserva.model';

const RESUMEN_VACIO: ResumenReservas = { activas: 0, proxima: null };

/**
 * Estado reactivo de CU13/CU14 (Consultar y cancelar reservas).
 *
 * Es la única fuente de verdad de las reservas del cliente: tanto la tarjeta del Perfil como la
 * pantalla `/reservas` leen `resumen`/`misReservas` de aquí. El servidor decide `puede_cancelar` y
 * el reparto entre "próximas" e "historial"; este servicio nunca deriva esos datos en cliente.
 */
@Injectable({
  providedIn: 'root',
})
export class MisReservasService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  readonly misReservas = signal<MisReservas | null>(null);
  readonly cargando = signal<boolean>(false);
  readonly cancelando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  /** Para la tarjeta del Perfil: nunca `null` mientras se carga, así el subtítulo no parpadea. */
  readonly resumen = computed(() => this.misReservas()?.resumen ?? RESUMEN_VACIO);

  /**
   * Carga las reservas del cliente autenticado, separadas en próximas e historial.
   */
  cargarMisReservas(): Observable<MisReservas> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http.get<MisReservas>(`${this.baseUrl}/reservas/mias`).pipe(
      tap((datos) => this.misReservas.set(datos)),
      catchError((err: HttpErrorResponse) => this.traducirError(err)),
      finalize(() => this.cargando.set(false))
    );
  }

  /**
   * Cancela una reserva propia. Tras el `200`, se recarga la lista completa desde el servidor en
   * vez de parchear el estado local: es el propio backend quien decide el nuevo reparto entre
   * "próximas" e "historial", el nuevo `resumen.activas`, etc.
   */
  cancelarReserva(idReserva: number, motivo: string): Observable<Reserva> {
    this.cancelando.set(true);
    this.error.set(null);

    return this.http
      .post<Reserva>(`${this.baseUrl}/reservas/${idReserva}/cancelar`, { motivo })
      .pipe(
        tap(() => this.cargarMisReservas().subscribe({ error: () => undefined })),
        catchError((err: HttpErrorResponse) => this.traducirError(err)),
        finalize(() => this.cancelando.set(false))
      );
  }

  private traducirError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'No fue posible completar la operación.';

    if (err.status === 403) {
      mensaje = err.error?.detail || 'Esta reserva pertenece a otro cliente.';
    } else if (err.status === 404) {
      mensaje = err.error?.detail || 'La reserva no existe.';
    } else if (err.status === 409) {
      mensaje = err.error?.detail || 'La reserva no admite esta acción.';
    } else if (err.status === 422) {
      mensaje = 'Indica un motivo de entre 3 y 250 caracteres.';
    } else if (err.status === 0) {
      mensaje = 'No fue posible conectar con el atelier. Comprueba tu conexión.';
    } else if (err.error?.detail) {
      mensaje = err.error.detail;
    }

    this.error.set(mensaje);
    return throwError(() => err);
  }
}
