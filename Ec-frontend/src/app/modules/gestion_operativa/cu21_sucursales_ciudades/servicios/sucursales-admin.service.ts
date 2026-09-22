import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  Ciudad,
  CiudadActualizarPayload,
  CiudadCrearPayload,
  FiltrosSucursalAdmin,
  SucursalAdmin,
  SucursalActualizarPayload,
  SucursalCrearPayload,
} from '../modelos/sucursal.model';

@Injectable({
  providedIn: 'root',
})
export class SucursalesAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin';

  // --- Signals de Estado Reactivo ---
  readonly ciudades = signal<Ciudad[]>([]);
  readonly sucursales = signal<SucursalAdmin[]>([]);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  private obtenerHeaders(): HttpHeaders {
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    if (typeof window !== 'undefined') {
      const token =
        localStorage.getItem('fashionstore_token') ||
        sessionStorage.getItem('fashionstore_token');
      if (token) {
        headers = headers.set('Authorization', `Bearer ${token}`);
      }
    }
    return headers;
  }

  // --- CIUDADES ---

  cargarCiudades(): Observable<Ciudad[]> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<Ciudad[]>(`${this.baseUrl}/ciudades`, { headers: this.obtenerHeaders() })
      .pipe(
        tap((data) => {
          this.ciudades.set(data);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  crearCiudad(payload: CiudadCrearPayload): Observable<Ciudad> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<Ciudad>(`${this.baseUrl}/ciudades`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nuevaCiudad) => {
          this.ciudades.update((lista) => [...lista, nuevaCiudad]);
          this.guardando.set(false);
          this.mensajeExito.set(`Ciudad "${nuevaCiudad.nombre}" registrada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  actualizarCiudad(idCiudad: number, payload: CiudadActualizarPayload): Observable<Ciudad> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<Ciudad>(`${this.baseUrl}/ciudades/${idCiudad}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((ciudadActualizada) => {
          this.ciudades.update((lista) =>
            lista.map((c) => (c.id_ciudad === idCiudad ? ciudadActualizada : c))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Ciudad "${ciudadActualizada.nombre}" actualizada.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  eliminarCiudad(idCiudad: number): Observable<{ mensaje: string }> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<{ mensaje: string }>(`${this.baseUrl}/ciudades/${idCiudad}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.ciudades.update((lista) => lista.filter((c) => c.id_ciudad !== idCiudad));
          this.guardando.set(false);
          this.mensajeExito.set('Ciudad eliminada exitosamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  // --- SUCURSALES ---

  cargarSucursales(filtros?: FiltrosSucursalAdmin): Observable<SucursalAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    let params = new HttpParams();
    if (filtros?.id_ciudad) {
      params = params.set('id_ciudad', filtros.id_ciudad.toString());
    }
    if (filtros?.activa !== undefined && filtros?.activa !== null) {
      params = params.set('activa', filtros.activa.toString());
    }
    if (filtros?.q) {
      params = params.set('q', filtros.q);
    }

    return this.http
      .get<SucursalAdmin[]>(`${this.baseUrl}/sucursales`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((data) => {
          this.sucursales.set(data);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  obtenerSucursal(idSucursal: number): Observable<SucursalAdmin> {
    return this.http.get<SucursalAdmin>(`${this.baseUrl}/sucursales/${idSucursal}`, {
      headers: this.obtenerHeaders(),
    });
  }

  crearSucursal(payload: SucursalCrearPayload): Observable<SucursalAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<SucursalAdmin>(`${this.baseUrl}/sucursales`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nuevaSucursal) => {
          this.sucursales.update((lista) => [nuevaSucursal, ...lista]);
          this.guardando.set(false);
          this.mensajeExito.set(`Boutique "${nuevaSucursal.nombre}" creada con exito.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  actualizarSucursal(
    idSucursal: number,
    payload: SucursalActualizarPayload
  ): Observable<SucursalAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<SucursalAdmin>(`${this.baseUrl}/sucursales/${idSucursal}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((sucursalActualizada) => {
          this.sucursales.update((lista) =>
            lista.map((s) => (s.id_sucursal === idSucursal ? sucursalActualizada : s))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Boutique "${sucursalActualizada.nombre}" actualizada.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  cambiarEstado(idSucursal: number, activa: boolean): Observable<SucursalAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .patch<SucursalAdmin>(
        `${this.baseUrl}/sucursales/${idSucursal}/estado`,
        { activa },
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((sucursalActualizada) => {
          this.sucursales.update((lista) =>
            lista.map((s) => (s.id_sucursal === idSucursal ? sucursalActualizada : s))
          );
          this.guardando.set(false);
          const estadoStr = activa ? 'activada' : 'desactivada';
          this.mensajeExito.set(`Boutique "${sucursalActualizada.nombre}" ${estadoStr}.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  eliminarSucursal(idSucursal: number): Observable<{ mensaje: string }> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<{ mensaje: string }>(`${this.baseUrl}/sucursales/${idSucursal}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.sucursales.update((lista) =>
            lista.filter((s) => s.id_sucursal !== idSucursal)
          );
          this.guardando.set(false);
          this.mensajeExito.set('Sucursal eliminada exitosamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  limpiarMensajes(): void {
    this.error.set(null);
    this.mensajeExito.set(null);
  }

  private interpretarError(err: HttpErrorResponse): string {
    if (err.status === 401) {
      return 'Sesion expirada o no valida. Por favor, inicie sesion nuevamente.';
    }
    if (err.status === 403) {
      return 'Acceso denegado: se requieren privilegios de administrador corporativo.';
    }
    if (err.status === 404) {
      return err.error?.detail || 'El recurso solicitado no fue encontrado.';
    }
    if (err.status === 409) {
      return (
        err.error?.detail ||
        'Conflicto de integridad: no es posible completar la operacion debido a dependencias activas.'
      );
    }
    if (err.status === 422) {
      return 'Datos inconsistentes: verifique que la hora de cierre sea posterior a la apertura.';
    }
    if (err.status === 0) {
      return 'No fue posible contactar con el servidor. Compruebe su conexion a la red.';
    }
    return err.error?.detail || 'Ocurrio un error inesperado al procesar la solicitud.';
  }
}
