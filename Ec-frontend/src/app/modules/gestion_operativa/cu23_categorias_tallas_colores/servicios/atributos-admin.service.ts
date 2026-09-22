import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  CategoriaAdmin,
  CategoriaActualizarPayload,
  CategoriaCrearPayload,
  ColorAdmin,
  ColorActualizarPayload,
  ColorCrearPayload,
  TallaAdmin,
  TallaActualizarPayload,
  TallaCrearPayload,
} from '../modelos/atributos.dto';

@Injectable({
  providedIn: 'root',
})
export class AtributosAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin';

  // --- Signals de Estado Reactivo ---
  readonly categorias = signal<CategoriaAdmin[]>([]);
  readonly tallas = signal<TallaAdmin[]>([]);
  readonly colores = signal<ColorAdmin[]>([]);
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

  // =========================================================================
  // GESTION DE CATEGORIAS
  // =========================================================================

  cargarCategorias(): Observable<CategoriaAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<CategoriaAdmin[]>(`${this.baseUrl}/categorias`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((data) => {
          this.categorias.set(data);
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

  crearCategoria(payload: CategoriaCrearPayload): Observable<CategoriaAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<CategoriaAdmin>(`${this.baseUrl}/categorias`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nueva) => {
          this.categorias.update((lista) => [...lista, nueva]);
          this.guardando.set(false);
          this.mensajeExito.set(`Categoria "${nueva.nombre}" registrada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  actualizarCategoria(id: number, payload: CategoriaActualizarPayload): Observable<CategoriaAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<CategoriaAdmin>(`${this.baseUrl}/categorias/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.categorias.update((lista) =>
            lista.map((c) => (c.id_categoria === id ? actualizada : c))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Categoria "${actualizada.nombre}" actualizada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  eliminarCategoria(id: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/categorias/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.categorias.update((lista) => lista.filter((c) => c.id_categoria !== id));
          this.guardando.set(false);
          this.mensajeExito.set('Categoria eliminada exitosamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  // =========================================================================
  // GESTION DE TALLAS
  // =========================================================================

  cargarTallas(): Observable<TallaAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<TallaAdmin[]>(`${this.baseUrl}/tallas`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((data) => {
          this.tallas.set(data);
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

  crearTalla(payload: TallaCrearPayload): Observable<TallaAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<TallaAdmin>(`${this.baseUrl}/tallas`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nueva) => {
          this.tallas.update((lista) =>
            [...lista, nueva].sort((a, b) => a.orden - b.orden || a.codigo.localeCompare(b.codigo))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Talla "${nueva.codigo}" registrada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  actualizarTalla(id: number, payload: TallaActualizarPayload): Observable<TallaAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<TallaAdmin>(`${this.baseUrl}/tallas/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.tallas.update((lista) =>
            lista
              .map((t) => (t.id_talla === id ? actualizada : t))
              .sort((a, b) => a.orden - b.orden || a.codigo.localeCompare(b.codigo))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Talla "${actualizada.codigo}" actualizada correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  eliminarTalla(id: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/tallas/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.tallas.update((lista) => lista.filter((t) => t.id_talla !== id));
          this.guardando.set(false);
          this.mensajeExito.set('Talla eliminada exitosamente.');
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  // =========================================================================
  // GESTION DE COLORES
  // =========================================================================

  cargarColores(): Observable<ColorAdmin[]> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<ColorAdmin[]>(`${this.baseUrl}/colores`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((data) => {
          this.colores.set(data);
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

  crearColor(payload: ColorCrearPayload): Observable<ColorAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<ColorAdmin>(`${this.baseUrl}/colores`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nuevo) => {
          this.colores.update((lista) => [...lista, nuevo]);
          this.guardando.set(false);
          this.mensajeExito.set(`Color "${nuevo.nombre}" registrado correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  actualizarColor(id: number, payload: ColorActualizarPayload): Observable<ColorAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<ColorAdmin>(`${this.baseUrl}/colores/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizado) => {
          this.colores.update((lista) =>
            lista.map((c) => (c.id_color === id ? actualizado : c))
          );
          this.guardando.set(false);
          this.mensajeExito.set(`Color "${actualizado.nombre}" actualizado correctamente.`);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  eliminarColor(id: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/colores/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.colores.update((lista) => lista.filter((c) => c.id_color !== id));
          this.guardando.set(false);
          this.mensajeExito.set('Color eliminado exitosamente.');
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
        'Conflicto de integridad: no es posible completar la operacion debido a dependencias activas o duplicidad.'
      );
    }
    if (err.status === 422) {
      return (
        err.error?.detail ||
        'Datos inconsistentes o regla de validacion no satisfecha (ej. referencia circular o formato #HEX invalido).'
      );
    }
    if (err.status === 0) {
      return 'No fue posible contactar con el servidor. Compruebe su conexion a la red.';
    }
    return err.error?.detail || 'Ocurrio un error inesperado al procesar la solicitud.';
  }
}
