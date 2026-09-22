/**
 * Servicio HTTP y de Estado Reactivo para CU28: Consultar ventas y reservas.
 * Nomenclatura oficial: "Consultar ventas y reservas"
 */

import { Injectable, inject, signal } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpParams,
} from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import {
  MetricasTransaccionales,
  ReservaDetalleCompleto,
  RespuestaPaginadaTransacciones,
  SucursalOpcion,
  TransaccionFiltros,
  VentaDetalleCompleto,
} from '../modelos/ventas-reservas.dto';

@Injectable({
  providedIn: 'root',
})
export class VentasReservasAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/ventas-reservas';

  // --- Estado Reactivo Centralizado (Signals) ---
  readonly transacciones = signal<RespuestaPaginadaTransacciones['items']>([]);
  readonly metricas = signal<MetricasTransaccionales>({
    monto_total_facturado: 0,
    total_ventas_concluidas: 0,
    reservas_activas: 0,
    ticket_promedio: 0,
  });
  readonly totalTransacciones = signal<number>(0);
  readonly totalPaginas = signal<number>(1);

  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  readonly filtros = signal<TransaccionFiltros>({
    q: '',
    tipo_operacion: 'todas',
    estado: 'todos',
    id_sucursal: null,
    fecha_desde: null,
    fecha_hasta: null,
    metodo_pago: null,
    canal_origen: 'todos',
    ordenar_por: 'creado_en_desc',
    pagina: 1,
    limite: 10,
  });

  // Colecciones auxiliares
  readonly sucursalesDisponibles = signal<SucursalOpcion[]>([]);

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

  limpiarError(): void {
    this.error.set(null);
  }

  actualizarFiltros(parcial: Partial<TransaccionFiltros>): void {
    this.filtros.update((actual) => ({
      ...actual,
      ...parcial,
      pagina: parcial.pagina !== undefined ? parcial.pagina : 1,
    }));
    this.listarTransacciones().subscribe();
  }

  resetearFiltros(): void {
    this.filtros.set({
      q: '',
      tipo_operacion: 'todas',
      estado: 'todos',
      id_sucursal: null,
      fecha_desde: null,
      fecha_hasta: null,
      metodo_pago: null,
      canal_origen: 'todos',
      ordenar_por: 'creado_en_desc',
      pagina: 1,
      limite: 10,
    });
    this.listarTransacciones().subscribe();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1 || nuevaPagina > this.totalPaginas()) {
      return;
    }
    this.filtros.update((f) => ({ ...f, pagina: nuevaPagina }));
    this.listarTransacciones().subscribe();
  }

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error al consultar las transacciones.';
    if (err.error?.detail) {
      if (typeof err.error.detail === 'string') {
        mensaje = err.error.detail;
      } else if (err.error.detail.mensaje) {
        mensaje = err.error.detail.mensaje;
      } else {
        mensaje = JSON.stringify(err.error.detail);
      }
    } else if (err.status === 401) {
      mensaje = 'Su sesion ha expirado o no cuenta con credenciales validas.';
    } else if (err.status === 403) {
      mensaje = 'No cuenta con privilegios autorizados para consultar ventas y reservas.';
    } else if (err.status === 404) {
      mensaje = 'La transaccion solicitada no fue localizada en el sistema.';
    } else if (err.status === 422) {
      mensaje = 'Los parametros de consulta suministrados no cumplen con las reglas de validacion.';
    }
    this.error.set(mensaje);
    return throwError(() => new Error(mensaje));
  }

  listarTransacciones(
    filtrosSobrescritos?: Partial<TransaccionFiltros>
  ): Observable<RespuestaPaginadaTransacciones> {
    this.cargando.set(true);
    this.error.set(null);

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    let params = new HttpParams()
      .set('pagina', String(f.pagina || 1))
      .set('limite', String(f.limite || 10));

    if (f.q && f.q.trim()) {
      params = params.set('q', f.q.trim());
    }
    if (f.tipo_operacion && f.tipo_operacion !== 'todas') {
      params = params.set('tipo_operacion', f.tipo_operacion);
    }
    if (f.estado && f.estado !== 'todos') {
      params = params.set('estado', f.estado);
    }
    if (f.id_sucursal) {
      params = params.set('id_sucursal', String(f.id_sucursal));
    }
    if (f.fecha_desde) {
      params = params.set('fecha_desde', f.fecha_desde);
    }
    if (f.fecha_hasta) {
      params = params.set('fecha_hasta', f.fecha_hasta);
    }
    if (f.metodo_pago) {
      params = params.set('metodo_pago', f.metodo_pago);
    }
    if (f.canal_origen && f.canal_origen !== 'todos') {
      params = params.set('canal_origen', f.canal_origen);
    }
    if (f.ordenar_por) {
      params = params.set('ordenar_por', f.ordenar_por);
    }

    return this.http
      .get<RespuestaPaginadaTransacciones>(this.baseUrl, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.transacciones.set(res.items || []);
          this.totalTransacciones.set(res.total || 0);
          this.totalPaginas.set(res.total_paginas || 1);
          if (res.metricas) {
            this.metricas.set(res.metricas);
          }
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  obtenerDetalleVenta(idVenta: number): Observable<VentaDetalleCompleto> {
    this.cargando.set(true);
    this.limpiarError();

    return this.http
      .get<VentaDetalleCompleto>(`${this.baseUrl}/ventas/${idVenta}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  obtenerDetalleReserva(idReserva: number): Observable<ReservaDetalleCompleto> {
    this.cargando.set(true);
    this.limpiarError();

    return this.http
      .get<ReservaDetalleCompleto>(`${this.baseUrl}/reservas/${idReserva}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  cargarSucursalesAuxiliares(): void {
    this.http
      .get<SucursalOpcion[]>('/api/v1/admin/sucursales', {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((suc) => {
          const opciones: SucursalOpcion[] = (suc || []).map((s) => ({
            id_sucursal: s.id_sucursal || 0,
            nombre: s.nombre || '',
            ciudad: s.ciudad || '',
          }));
          this.sucursalesDisponibles.set(opciones);
        }),
        catchError(() => [])
      )
      .subscribe();
  }
}
