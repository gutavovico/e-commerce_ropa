import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import { CambioContrasena, PerfilEmpleado, PerfilEmpleadoActualizar } from '../modelos/perfil-empleado.dto';

/** Perfil del empleado. El estado se reemplaza siempre con la respuesta del servidor. */
@Injectable({ providedIn: 'root' })
export class PerfilEmpleadoService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/mi-perfil-empleado';

  readonly perfil = signal<PerfilEmpleado | null>(null);
  readonly cargando = signal(false);
  readonly guardando = signal(false);

  cargar(): Observable<PerfilEmpleado> {
    this.cargando.set(true);
    return this.http.get<PerfilEmpleado>(this.endpoint).pipe(
      tap((p) => this.perfil.set(p)),
      catchError((e: HttpErrorResponse) => throwError(() => new Error(this.mensaje(e)))),
      finalize(() => this.cargando.set(false)),
    );
  }

  actualizar(datos: PerfilEmpleadoActualizar): Observable<PerfilEmpleado> {
    this.guardando.set(true);
    return this.http.patch<PerfilEmpleado>(this.endpoint, datos).pipe(
      tap((p) => this.perfil.set(p)),
      catchError((e: HttpErrorResponse) => throwError(() => new Error(this.mensaje(e)))),
      finalize(() => this.guardando.set(false)),
    );
  }

  cambiarContrasena(datos: CambioContrasena): Observable<void> {
    this.guardando.set(true);
    return this.http.post<void>(`${this.endpoint}/contrasena`, datos).pipe(
      catchError((e: HttpErrorResponse) => throwError(() => new Error(this.mensaje(e)))),
      finalize(() => this.guardando.set(false)),
    );
  }

  private mensaje(e: HttpErrorResponse): string {
    if (e.status === 0) return 'No fue posible contactar con el servidor. Compruebe su conexión.';
    if (e.status === 422) return 'La contraseña nueva necesita 8 caracteres, una mayúscula, una minúscula y un dígito.';
    const detalle = e.error?.detail;
    if (typeof detalle === 'string' && detalle) return detalle;
    return 'No se pudo completar la operación. Inténtelo de nuevo.';
  }
}
