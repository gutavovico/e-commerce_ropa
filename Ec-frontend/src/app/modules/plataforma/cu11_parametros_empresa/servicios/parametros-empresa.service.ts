import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import { ParametrosEmpresa, ParametrosEmpresaPayload } from '../modelos/parametros-empresa.dto';

/**
 * P2-CU11 · Parámetros de la empresa. El estado se reemplaza siempre con la respuesta del servidor.
 * El JWT lo adjunta `authInterceptor`.
 */
@Injectable({ providedIn: 'root' })
export class ParametrosEmpresaService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/admin/configuracion';

  readonly parametros = signal<ParametrosEmpresa | null>(null);
  readonly cargando = signal(false);
  readonly guardando = signal(false);

  cargar(): Observable<ParametrosEmpresa> {
    this.cargando.set(true);
    return this.http.get<ParametrosEmpresa>(this.endpoint).pipe(
      tap((p) => this.parametros.set(p)),
      catchError((err: HttpErrorResponse) => throwError(() => new Error(this.mensaje(err)))),
      finalize(() => this.cargando.set(false)),
    );
  }

  guardar(payload: ParametrosEmpresaPayload): Observable<ParametrosEmpresa> {
    this.guardando.set(true);
    return this.http.put<ParametrosEmpresa>(this.endpoint, payload).pipe(
      tap((p) => this.parametros.set(p)),
      catchError((err: HttpErrorResponse) => throwError(() => new Error(this.mensaje(err)))),
      finalize(() => this.guardando.set(false)),
    );
  }

  private mensaje(err: HttpErrorResponse): string {
    if (err.status === 0) return 'No fue posible contactar con el servidor. Compruebe su conexión.';
    if (err.status === 422) return 'Algún valor está fuera de su rango. Revise los campos marcados.';
    const detalle = err.error?.detail;
    if (typeof detalle === 'string' && detalle) return detalle;
    if (err.status === 403) return 'Solo el administrador de la empresa puede cambiar la configuración.';
    return 'No se pudo completar la operación. Inténtelo de nuevo.';
  }
}
