import { Injectable, inject, signal } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpParams,
} from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import {
  FiltrosInventarioGlobal,
  InventarioGlobalItem,
  MetricasInventarioGlobal,
  RespuestaInventarioGlobal,
} from '../modelos/inventario-global.dto';

@Injectable({
  providedIn: 'root',
})
export class InventarioGlobalAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/inventario/global';

  // --- Signals de Estado Reactivo ---
  readonly items = signal<InventarioGlobalItem[]>([]);
  readonly metricas = signal<MetricasInventarioGlobal>({
    total_unidades_red: 0,
    variantes_monitoreadas: 0,
    alertas_stock_bajo: 0,
    sedes_activas: 0,
  });
  readonly totalRegistros = signal<number>(0);
  readonly totalPaginas = signal<number>(1);
  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  readonly filtros = signal<FiltrosInventarioGlobal>({
    q: '',
    id_categoria: null,
    id_sucursal: null,
    estado_stock: 'todos',
    ordenar_por: 'nombre_asc',
    pagina: 1,
    limite: 10,
  });

  readonly itemSeleccionadoDetalle = signal<InventarioGlobalItem | null>(null);
  readonly modalDetalleAbierto = signal<boolean>(false);

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

  limpiarMensajes(): void {
    this.error.set(null);
  }

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error al consultar el inventario global consolidado.';
    if (err.error?.detail) {
      mensaje =
        typeof err.error.detail === 'string'
          ? err.error.detail
          : JSON.stringify(err.error.detail);
    } else if (err.status === 401) {
      mensaje = 'Su sesion ha expirado o no cuenta con credenciales validas.';
    } else if (err.status === 403) {
      mensaje = 'No cuenta con privilegios autorizados para consultar el inventario global.';
    } else if (err.status === 404) {
      mensaje = 'El recurso solicitado o filtro indicado no fue encontrado.';
    } else if (err.status === 422) {
      mensaje = 'Los parametros de busqueda o paginacion suministrados son invalidos.';
    }
    this.error.set(mensaje);
    return throwError(() => err);
  }

  cargarInventario(): Observable<RespuestaInventarioGlobal> {
    this.cargando.set(true);
    this.error.set(null);

    const f = this.filtros();
    let params = new HttpParams()
      .set('pagina', f.pagina.toString())
      .set('limite', f.limite.toString())
      .set('ordenar_por', f.ordenar_por);

    if (f.q.trim()) {
      params = params.set('q', f.q.trim());
    }
    if (f.id_categoria !== null) {
      params = params.set('id_categoria', f.id_categoria.toString());
    }
    if (f.id_sucursal !== null) {
      params = params.set('id_sucursal', f.id_sucursal.toString());
    }
    if (f.estado_stock && f.estado_stock !== 'todos') {
      params = params.set('estado_stock', f.estado_stock);
    }

    const headers = this.obtenerHeaders();

    return this.http
      .get<RespuestaInventarioGlobal>(this.baseUrl, { params, headers })
      .pipe(
        tap((res) => {
          this.items.set(res.items);
          this.metricas.set(res.metricas);
          this.totalRegistros.set(res.total);
          this.totalPaginas.set(res.total_paginas);
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => {
          this.cargando.set(false);
        })
      );
  }

  actualizarFiltros(cambios: Partial<FiltrosInventarioGlobal>): void {
    this.filtros.update((actual) => ({
      ...actual,
      ...cambios,
      pagina: cambios.pagina !== undefined ? cambios.pagina : 1,
    }));
    this.cargarInventario().subscribe({
      error: () => {},
    });
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina >= 1 && nuevaPagina <= this.totalPaginas()) {
      this.actualizarFiltros({ pagina: nuevaPagina });
    }
  }

  limpiarFiltros(): void {
    this.filtros.set({
      q: '',
      id_categoria: null,
      id_sucursal: null,
      estado_stock: 'todos',
      ordenar_por: 'nombre_asc',
      pagina: 1,
      limite: 10,
    });
    this.cargarInventario().subscribe({
      error: () => {},
    });
  }

  abrirDetalle(item: InventarioGlobalItem): void {
    this.itemSeleccionadoDetalle.set(item);
    this.modalDetalleAbierto.set(true);
  }

  cerrarDetalle(): void {
    this.itemSeleccionadoDetalle.set(null);
    this.modalDetalleAbierto.set(false);
  }
}
