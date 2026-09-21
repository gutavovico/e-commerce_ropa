import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, finalize, map, of, tap, throwError } from 'rxjs';
import {
  LoginPeticion,
  LoginRespuesta,
  UsuarioSesion,
} from '../modelos/login.dto';

@Injectable({
  providedIn: 'root',
})
export class LoginService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/autenticacion/login';
  private readonly logoutEndpoint = '/api/v1/autenticacion/logout';

  private readonly TOKEN_KEY = 'fashionstore_token';
  private readonly USER_KEY = 'fashionstore_user';

  // Estado reactivo de usuario con Signals
  readonly usuarioActual = signal<UsuarioSesion | null>(this.recuperarSesionInicial());
  readonly estaAutenticado = computed(() => this.usuarioActual() !== null);
  readonly esAdmin = computed(() => this.usuarioActual()?.rol === 'administrador');

  /**
   * Envía las credenciales al backend de FastAPI y emite la respuesta.
   * @param peticion Credenciales y flag de recordar dispositivo.
   */
  iniciarSesion(peticion: LoginPeticion): Observable<LoginRespuesta> {
    return this.http.post<LoginRespuesta>(this.endpoint, peticion).pipe(
      tap((respuesta) => {
        this.guardarSesion(respuesta, peticion.recordar_dispositivo);
      }),
      catchError((error: HttpErrorResponse) => {
        let mensaje = 'Ocurrió un error inesperado al iniciar sesión.';

        if (error.status === 401) {
          mensaje =
            error.error?.detail ||
            'Correo electrónico o contraseña incorrectos. Por favor, verifica tus datos.';
        } else if (error.status === 403) {
          mensaje =
            error.error?.detail ||
            'Tu cuenta se encuentra inactiva o suspendida. Por favor, contacta a soporte.';
        } else if (error.status === 422) {
          mensaje = 'Por favor verifica que el correo y la contraseña tengan el formato correcto.';
        } else if (error.status === 0) {
          mensaje = 'No se pudo conectar con el servidor. Revisa tu conexión de red.';
        } else if (error.error?.detail && typeof error.error.detail === 'string') {
          mensaje = error.error.detail;
        }

        return throwError(() => new Error(mensaje));
      })
    );
  }

  /**
   * Persiste el token y los datos de sesión en el almacenamiento correspondiente.
   */
  private guardarSesion(respuesta: LoginRespuesta, recordar: boolean): void {
    const sesion: UsuarioSesion = {
      id_usuario: respuesta.id_usuario,
      email: respuesta.email,
      nombres: respuesta.nombres,
      apellidos: respuesta.apellidos,
      rol: respuesta.rol,
      token: respuesta.access_token,
    };

    this.usuarioActual.set(sesion);

    try {
      if (typeof window !== 'undefined') {
        const storage = recordar ? localStorage : sessionStorage;
        // Limpiar el storage opuesto para evitar inconsistencias
        (recordar ? sessionStorage : localStorage).removeItem(this.TOKEN_KEY);
        (recordar ? sessionStorage : localStorage).removeItem(this.USER_KEY);

        storage.setItem(this.TOKEN_KEY, respuesta.access_token);
        storage.setItem(this.USER_KEY, JSON.stringify(sesion));
      }
    } catch {
      // Manejo silencioso en entornos sin acceso a storage
    }
  }

  /**
   * Recupera la sesión persistida al iniciar la aplicación.
   */
  private recuperarSesionInicial(): UsuarioSesion | null {
    try {
      if (typeof window !== 'undefined') {
        const userJson =
          localStorage.getItem(this.USER_KEY) || sessionStorage.getItem(this.USER_KEY);
        if (userJson) {
          return JSON.parse(userJson) as UsuarioSesion;
        }
      }
    } catch {
      return null;
    }
    return null;
  }

  /**
   * Obtiene el token JWT activo de la sesión actual.
   */
  obtenerToken(): string | null {
    const sesion = this.usuarioActual();
    if (sesion?.token) {
      return sesion.token;
    }
    try {
      if (typeof window !== 'undefined') {
        return (
          localStorage.getItem(this.TOKEN_KEY) ||
          sessionStorage.getItem(this.TOKEN_KEY)
        );
      }
    } catch {
      return null;
    }
    return null;
  }

  /**
   * Cierra la sesión activa:
   * 1. Notifica al backend en POST /api/v1/autenticacion/logout para revocar el token en el servidor.
   * 2. Purga las credenciales y tokens de localStorage y sessionStorage de forma garantizada.
   * 3. Resetea el signal reactivo usuarioActual (estaAutenticado -> false).
   */
  cerrarSesion(): Observable<void> {
    const token = this.obtenerToken();
    const headers = token
      ? new HttpHeaders({ Authorization: `Bearer ${token}` })
      : undefined;

    return this.http.post(this.logoutEndpoint, {}, { headers }).pipe(
      catchError(() => of(null)), // Resiliencia: si falla la red, continuar con la purga
      finalize(() => {
        this.purgarSesionLocal();
      }),
      map(() => void 0)
    );
  }

  /**
   * Limpia inmediatamente el almacenamiento local y resetea las señales reactivas.
   */
  purgarSesionLocal(): void {
    this.usuarioActual.set(null);
    try {
      if (typeof window !== 'undefined') {
        localStorage.removeItem(this.TOKEN_KEY);
        localStorage.removeItem(this.USER_KEY);
        sessionStorage.removeItem(this.TOKEN_KEY);
        sessionStorage.removeItem(this.USER_KEY);
      }
    } catch {
      // Ignorar errores de storage
    }
  }
}
