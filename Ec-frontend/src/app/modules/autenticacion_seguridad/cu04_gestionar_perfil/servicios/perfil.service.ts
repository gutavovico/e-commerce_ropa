import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import { Router } from '@angular/router';
import {
  HistorialCompras,
  PedidoHistorico,
  PerfilCliente,
  PerfilClienteActualizar,
} from '../modelos/perfil.dto';

@Injectable({
  providedIn: 'root',
})
export class PerfilService {
  private readonly http = inject(HttpClient);
  private readonly router = inject(Router);
  private readonly endpoint = '/api/v1/perfil';
  private readonly historialEndpoint = '/api/v1/ventas/mias';

  private readonly TOKEN_KEY = 'fashionstore_token';

  // --- Estado Reactivo con Signals ---
  readonly perfil = signal<PerfilCliente | null>(null);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);
  readonly modalEdicionAbierto = signal<boolean>(false);

  // --- Estado Reactivo de CU17: Historial de Compras (Cero datos inventados) ---
  readonly pedidos = signal<PedidoHistorico[]>([]);
  readonly totalPedidos = signal<number>(0);
  readonly pedidosCompletados = signal<number>(0);
  readonly cargandoPedidos = signal<boolean>(false);

  /**
   * Obtiene el token JWT persistido en localStorage o sessionStorage.
   */
  obtenerToken(): string | null {
    if (typeof window === 'undefined') {
      return null;
    }
    return (
      localStorage.getItem(this.TOKEN_KEY) ||
      sessionStorage.getItem(this.TOKEN_KEY)
    );
  }

  /**
   * Genera las cabeceras HTTP de autorización con Bearer token.
   */
  private obtenerHeaders(): HttpHeaders {
    const token = this.obtenerToken();
    let headers = new HttpHeaders({
      'Content-Type': 'application/json',
    });
    if (token) {
      headers = headers.set('Authorization', `Bearer ${token}`);
    }
    return headers;
  }

  /**
   * Carga los datos del perfil del cliente desde el backend.
   */
  cargarPerfil(): Observable<PerfilCliente> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<PerfilCliente>(this.endpoint, { headers: this.obtenerHeaders() })
      .pipe(
        tap((data) => {
          this.perfil.set(data);
          this.cargando.set(false);
        }),
        catchError((err: HttpErrorResponse) => {
          this.cargando.set(false);
          const errorMsg = this.interpretarError(err);
          this.error.set(errorMsg);

          if (err.status === 401) {
            this.router.navigate(['/login']);
          }

          return throwError(() => new Error(errorMsg));
        })
      );
  }

  /**
   * Carga el historial real de compras del cliente autenticado (CU17: GET /api/v1/ventas/mias).
   */
  cargarHistorialCompras(): Observable<HistorialCompras> {
    this.cargandoPedidos.set(true);

    return this.http
      .get<HistorialCompras>(this.historialEndpoint, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((datos) => {
          this.pedidos.set(datos.pedidos ?? []);
          this.totalPedidos.set(datos.total_pedidos ?? 0);
          this.pedidosCompletados.set(datos.pedidos_completados ?? 0);
        }),
        finalize(() => this.cargandoPedidos.set(false))
      );
  }

  /**
   * Envía la actualización de perfil al backend (PATCH /api/v1/perfil).
   */
  actualizarPerfil(datos: PerfilClienteActualizar): Observable<PerfilCliente> {
    this.guardando.set(true);
    this.error.set(null);
    this.mensajeExito.set(null);

    return this.http
      .patch<PerfilCliente>(this.endpoint, datos, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((perfilActualizado) => {
          this.perfil.set(perfilActualizado);
          this.guardando.set(false);
          this.mensajeExito.set('Información personal actualizada con éxito.');
          this.cerrarModalEdicion();
          this.sincronizarSesionStorage(perfilActualizado);
        }),
        catchError((err: HttpErrorResponse) => {
          this.guardando.set(false);
          const errorMsg = this.interpretarError(err);
          this.error.set(errorMsg);
          return throwError(() => new Error(errorMsg));
        })
      );
  }

  /**
   * Sincroniza nombres y apellidos actualizados en el almacenamiento de sesión.
   */
  private sincronizarSesionStorage(p: PerfilCliente): void {
    if (typeof window === 'undefined') return;
    try {
      const userKey = 'fashionstore_user';
      for (const storage of [localStorage, sessionStorage]) {
        const item = storage.getItem(userKey);
        if (item) {
          const user = JSON.parse(item);
          user.nombres = p.nombres;
          user.apellidos = p.apellidos;
          storage.setItem(userKey, JSON.stringify(user));
        }
      }
    } catch {
      // Ignorar errores de almacenamiento
    }
  }

  /**
   * Control de apertura y cierre del modal de edición.
   */
  abrirModalEdicion(): void {
    this.error.set(null);
    this.modalEdicionAbierto.set(true);
  }

  cerrarModalEdicion(): void {
    this.modalEdicionAbierto.set(false);
  }

  limpiarMensajes(): void {
    this.error.set(null);
    this.mensajeExito.set(null);
  }

  /**
   * Traduce códigos de error HTTP a mensajes legibles de alta costura.
   */
  private interpretarError(err: HttpErrorResponse): string {
    if (err.status === 401) {
      return 'Su sesión ha expirado o no es válida. Por favor inicie sesión nuevamente.';
    }
    if (err.status === 403) {
      return 'Acceso restringido. Esta sección es exclusiva para cuentas de cliente.';
    }
    if (err.status === 422) {
      return 'Por favor verifique los datos ingresados. Formato de talla o contacto no válido.';
    }
    if (err.status === 0) {
      return 'No fue posible contactar con los servidores de Fashion Store. Compruebe su conexión.';
    }
    return (
      err.error?.detail ||
      'Ocurrió un error al procesar la información de su perfil.'
    );
  }
}
