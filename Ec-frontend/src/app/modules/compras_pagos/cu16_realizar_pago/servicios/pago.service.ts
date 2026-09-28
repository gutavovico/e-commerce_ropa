import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';

import {
  PagoConfirmado,
  PagoIniciarIn,
  PagoIntentoOut,
  ResumenPago,
} from '../modelos/pago.model';

/**
 * Generador simple de UUID v4 para la clave de idempotencia de la pasarela.
 */
export function generarClaveIdempotencia(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) {
    return crypto.randomUUID();
  }
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    const v = c === 'x' ? r : (r & 0x3) | 0x8;
    return v.toString(16);
  });
}

@Injectable({
  providedIn: 'root',
})
export class PagoService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  // --- Signals de Estado ---
  readonly resumen = signal<ResumenPago | null>(null);
  readonly cargando = signal<boolean>(false);
  readonly procesando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly pagoExitoso = signal<PagoConfirmado | null>(null);
  readonly segundosRestantes = signal<number | null>(null);

  private temporizador: ReturnType<typeof setInterval> | null = null;

  /**
   * Obtiene el resumen de la orden congelada para inicializar la pasarela.
   */
  obtenerResumenPago(idVenta: number): Observable<ResumenPago> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<ResumenPago>(`${this.baseUrl}/ventas/${idVenta}/resumen-pago`)
      .pipe(
        tap((resumen) => {
          this.resumen.set(resumen);
          this.iniciarTemporizador(resumen.segundos_restantes);
        }),
        catchError((err: HttpErrorResponse) => {
          const mensaje =
            err.error?.detail ||
            err.error?.mensaje ||
            'No fue posible obtener el resumen de la orden.';
          this.error.set(mensaje);
          return throwError(() => err);
        }),
        finalize(() => this.cargando.set(false))
      );
  }

  /**
   * Abre un `PaymentIntent` en Stripe (`POST /pagos/intentos`) y devuelve su `client_secret`.
   *
   * **No recibe ni envía ningún dato de tarjeta.** El backend nunca ve el PAN ni el CVV
   * (revisado el 2026-09-28): la tarjeta se recolecta en Stripe Elements, en el navegador, y se
   * confirma directamente contra Stripe con ese `client_secret`. Ver `confirmarPago`.
   */
  iniciarPago(datos: PagoIniciarIn): Observable<PagoIntentoOut> {
    this.procesando.set(true);
    this.error.set(null);

    const payload: PagoIniciarIn = {
      ...datos,
      clave_idempotencia: datos.clave_idempotencia || generarClaveIdempotencia(),
    };

    return this.http
      .post<PagoIntentoOut>(`${this.baseUrl}/pagos/intentos`, payload)
      .pipe(
        tap((intento) => {
          if (intento.ya_confirmado && intento.confirmacion) {
            this.pagoExitoso.set(intento.confirmacion);
            this.detenerTemporizador();
          }
        }),
        catchError((err: HttpErrorResponse) => this.traducirError(err)),
        finalize(() => this.procesando.set(false))
      );
  }

  /**
   * Verifica y cierra un cobro digital ya confirmado con Stripe (`POST /pagos/{id_pago}/confirmar`).
   *
   * El servidor nunca toma el desenlace de lo que este cliente reporte: recupera el
   * `PaymentIntent` por su id y decide `aprobado`/`rechazado` según lo que Stripe le devuelva.
   */
  confirmarPago(idPago: number): Observable<PagoConfirmado> {
    this.procesando.set(true);
    this.error.set(null);

    return this.http
      .post<PagoConfirmado>(`${this.baseUrl}/pagos/${idPago}/confirmar`, {})
      .pipe(
        tap((confirmacion) => {
          this.pagoExitoso.set(confirmacion);
          this.detenerTemporizador();
        }),
        catchError((err: HttpErrorResponse) => this.traducirError(err)),
        finalize(() => this.procesando.set(false))
      );
  }

  /**
   * Registra la intención de pago en efectivo en sucursal (`POST /pagos/efectivo`). No cobra
   * nada: el método nunca tocó una tarjeta, así que no pasa por `iniciarPago`/`confirmarPago`.
   */
  registrarPagoEfectivo(idVenta: number, claveIdempotencia?: string): Observable<PagoConfirmado> {
    this.procesando.set(true);
    this.error.set(null);

    const payload = {
      id_venta: idVenta,
      clave_idempotencia: claveIdempotencia || generarClaveIdempotencia(),
    };

    return this.http
      .post<PagoConfirmado>(`${this.baseUrl}/pagos/efectivo`, payload)
      .pipe(
        tap((confirmacion) => {
          this.pagoExitoso.set(confirmacion);
          this.detenerTemporizador();
        }),
        catchError((err: HttpErrorResponse) => this.traducirError(err)),
        finalize(() => this.procesando.set(false))
      );
  }

  private traducirError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Error al procesar el pago.';
    if (err.status === 402) {
      mensaje =
        err.error?.detail ||
        err.error?.mensaje ||
        'La entidad emisora denegó la transacción. Por favor verifica tus datos o prueba con otro medio de pago.';
    } else if (err.status === 409) {
      mensaje =
        err.error?.detail ||
        err.error?.mensaje ||
        'La ventana de reserva ha vencido o la orden no se encuentra disponible.';
      this.segundosRestantes.set(0);
    } else if (err.error?.detail) {
      mensaje =
        typeof err.error.detail === 'string'
          ? err.error.detail
          : JSON.stringify(err.error.detail);
    }
    this.error.set(mensaje);
    return throwError(() => err);
  }

  /**
   * Manejo del temporizador de la ventana de cortesía (25 minutos).
   */
  iniciarTemporizador(segundosIniciales: number): void {
    this.detenerTemporizador();
    this.segundosRestantes.set(Math.max(0, segundosIniciales));

    if (segundosIniciales <= 0) return;

    this.temporizador = setInterval(() => {
      const actual = this.segundosRestantes();
      if (actual === null || actual <= 1) {
        this.segundosRestantes.set(0);
        this.detenerTemporizador();
      } else {
        this.segundosRestantes.set(actual - 1);
      }
    }, 1000);
  }

  detenerTemporizador(): void {
    if (this.temporizador !== null) {
      clearInterval(this.temporizador);
      this.temporizador = null;
    }
  }

  formatearTiempoRestante(segundos: number | null): string {
    if (segundos === null || segundos <= 0) return '00:00';
    const minutos = Math.floor(segundos / 60);
    const segs = segundos % 60;
    return `${minutos.toString().padStart(2, '0')}:${segs.toString().padStart(2, '0')}`;
  }
}
