import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders } from '@angular/common/http';
import { Observable, catchError, tap, throwError } from 'rxjs';
import { Router } from '@angular/router';
import {
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

  private readonly TOKEN_KEY = 'fashionstore_token';

  // --- Estado Reactivo con Signals ---
  readonly perfil = signal<PerfilCliente | null>(null);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);
  readonly modalEdicionAbierto = signal<boolean>(false);

  // Pedidos históricos conforme al mockup de alta costura
  readonly pedidos = signal<PedidoHistorico[]>([
    {
      id: 'PED-001',
      titulo: 'Vestido plisado en seda natural',
      boutique: 'FLAGSHIP SERRANO (MADRID)',
      iconoBoutique: 'flagship',
      descripcion: 'Seda natural mora 100% · Talla 38 · Color Marfil',
      talla: '38',
      color: 'Marfil',
      precio: 890,
      fecha: '24 OCT 2024 · ENTREGADO EN TIENDA',
      estado: 'ENTREGADO',
      referencia: 'REF: MAD-70614',
      imagen: 'https://images.unsplash.com/photo-1595777457583-95e059d581b8?auto=format&fit=crop&w=400&q=80',
    },
    {
      id: 'PED-002',
      titulo: 'Blazer estructurado lana virgen',
      boutique: 'BOUTIQUE SAINT-HONORÉ (PARÍS)',
      iconoBoutique: 'paris',
      descripcion: 'Lana virgen italiana · Talla 40 · Color Camel',
      talla: '40',
      color: 'Camel',
      precio: 740,
      fecha: '28 SEP 2024 · A DOMICILIO',
      estado: 'ENTREGADO',
      referencia: 'REF: PAR-20412',
      imagen: 'https://images.unsplash.com/photo-1591047139829-d91aecb6caea?auto=format&fit=crop&w=400&q=80',
    },
    {
      id: 'PED-003',
      titulo: 'Blusa de satén fluido marfil',
      boutique: 'MADRID CENTRAL HUB (ONLINE)',
      iconoBoutique: 'online',
      descripcion: 'Satén de seda marfil · Talla 38',
      talla: '38',
      color: 'Marfil',
      precio: 310,
      fecha: '10 AGO 2024 · ENTREGADO',
      estado: 'ENTREGADO',
      referencia: 'REF: ONL-07832',
      imagen: 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?auto=format&fit=crop&w=400&q=80',
    },
  ]);

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
