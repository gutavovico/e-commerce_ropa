import { Injectable, inject, signal } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpParams,
} from '@angular/common/http';
import { Observable, catchError, tap, throwError } from 'rxjs';
import {
  ListaPaginadaUsuarios,
  ParametrosFiltroUsuario,
  ResetPasswordPayload,
  UsuarioActualizarPayload,
  UsuarioAdmin,
  UsuarioCrearPayload,
} from '../modelos/usuario.dto';

@Injectable({
  providedIn: 'root',
})
export class UsuariosAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/usuarios';

  // --- Signals de Estado Reactivo ---
  readonly usuarios = signal<UsuarioAdmin[]>([]);
  readonly totalUsuarios = signal<number>(0);
  readonly usuarioSeleccionado = signal<UsuarioAdmin | null>(null);
  readonly filtros = signal<ParametrosFiltroUsuario>({
    pagina: 1,
    limite: 10,
  });
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  /**
   * Obtiene los encabezados con el token Bearer JWT activo.
   */
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

  /**
   * Interpreta las respuestas de error del backend de FastAPI y jerarquia DomainError.
   */
  interpretarError(err: HttpErrorResponse): string {
    if (err.error?.detail && typeof err.error.detail === 'string') {
      return err.error.detail;
    }
    if (err.status === 401) {
      return 'Sesion no autorizada o expirada. Por favor, inicie sesion nuevamente.';
    }
    if (err.status === 403) {
      return 'Acceso denegado. Se requiere nivel de privilegio Administrador.';
    }
    if (err.status === 404) {
      return 'El usuario solicitado no fue encontrado en el sistema.';
    }
    if (err.status === 409) {
      return 'Conflicto de unicidad o salvaguarda de seguridad del sistema.';
    }
    if (err.status === 422) {
      return 'Datos inconsistentes o regla de negocio no satisfecha.';
    }
    return 'Ocurrio un error inesperado al procesar la operacion.';
  }

  /**
   * Carga el listado paginado de usuarios aplicando filtros multicriterio.
   */
  cargarUsuarios(
    nuevosFiltros?: Partial<ParametrosFiltroUsuario>
  ): Observable<ListaPaginadaUsuarios> {
    this.cargando.set(true);
    this.error.set(null);

    const paramsActuales = {
      ...this.filtros(),
      ...(nuevosFiltros || {}),
    };
    this.filtros.set(paramsActuales);

    let httpParams = new HttpParams()
      .set('pagina', String(paramsActuales.pagina || 1))
      .set('limite', String(paramsActuales.limite || 10));

    if (paramsActuales.q && paramsActuales.q.trim()) {
      httpParams = httpParams.set('q', paramsActuales.q.trim());
    }
    if (paramsActuales.rol && paramsActuales.rol !== 'todos') {
      httpParams = httpParams.set('rol', paramsActuales.rol);
    }
    if (paramsActuales.id_sucursal && paramsActuales.id_sucursal > 0) {
      httpParams = httpParams.set('id_sucursal', String(paramsActuales.id_sucursal));
    }
    if (paramsActuales.activo !== undefined && paramsActuales.activo !== null) {
      httpParams = httpParams.set('activo', String(paramsActuales.activo));
    }

    return this.http
      .get<ListaPaginadaUsuarios>(this.baseUrl, {
        headers: this.obtenerHeaders(),
        params: httpParams,
      })
      .pipe(
        tap((respuesta) => {
          this.usuarios.set(respuesta.items);
          this.totalUsuarios.set(respuesta.total);
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

  /**
   * Consulta individual de la ficha tecnica de un usuario por su ID.
   */
  obtenerUsuarioPorId(idUsuario: number): Observable<UsuarioAdmin> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<UsuarioAdmin>(`${this.baseUrl}/${idUsuario}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((usuario) => {
          this.usuarioSeleccionado.set(usuario);
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

  /**
   * Crea un nuevo usuario corporativo o cliente.
   */
  crearUsuario(payload: UsuarioCrearPayload): Observable<UsuarioAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<UsuarioAdmin>(this.baseUrl, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nuevo) => {
          this.guardando.set(false);
          this.mensajeExito.set(
            `Usuario "${nuevo.nombre_completo}" registrado exitosamente.`
          );
          // Recargar la pagina actual para reflejar el alta
          this.cargarUsuarios().subscribe();
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  /**
   * Actualiza los datos y rol de un usuario existente.
   */
  actualizarUsuario(
    idUsuario: number,
    payload: UsuarioActualizarPayload
  ): Observable<UsuarioAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<UsuarioAdmin>(`${this.baseUrl}/${idUsuario}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizado) => {
          this.guardando.set(false);
          this.mensajeExito.set(
            `Usuario "${actualizado.nombre_completo}" actualizado correctamente.`
          );
          this.cargarUsuarios().subscribe();
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  /**
   * Conmuta el estado de la cuenta entre activo y suspendido.
   */
  cambiarEstado(idUsuario: number, activo: boolean): Observable<UsuarioAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .patch<UsuarioAdmin>(
        `${this.baseUrl}/${idUsuario}/estado`,
        { activo },
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((actualizado) => {
          this.guardando.set(false);
          const accion = activo ? 'activada' : 'suspendida';
          this.mensajeExito.set(`Cuenta de usuario ${accion} exitosamente.`);
          this.cargarUsuarios().subscribe();
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  /**
   * Restablece administrativamente la contrasena de un usuario.
   */
  resetPassword(
    idUsuario: number,
    payload: ResetPasswordPayload
  ): Observable<UsuarioAdmin> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<UsuarioAdmin>(
        `${this.baseUrl}/${idUsuario}/reset-password`,
        payload,
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((actualizado) => {
          this.guardando.set(false);
          this.mensajeExito.set(
            `Contrasena para "${actualizado.nombre_completo}" restablecida exitosamente.`
          );
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  /**
   * Elimina permanentemente un usuario si no cuenta con dependencias.
   */
  eliminarUsuario(idUsuario: number): Observable<void> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .delete<void>(`${this.baseUrl}/${idUsuario}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap(() => {
          this.guardando.set(false);
          this.mensajeExito.set('Usuario eliminado permanentemente del sistema.');
          this.cargarUsuarios().subscribe();
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const msg = this.interpretarError(err);
          this.error.set(msg);
          return throwError(() => new Error(msg));
        })
      );
  }

  /**
   * Limpia los mensajes reactivos de exito o error.
   */
  limpiarMensajes(): void {
    this.error.set(null);
    this.mensajeExito.set(null);
  }
}
