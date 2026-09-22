/**
 * Servicio HTTP y de Estado Reactivo para CU29: Visualizar indicadores empresariales.
 * Nomenclatura oficial: "Visualizar indicadores empresariales"
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
  ComparativaSucursales,
  DashboardIndicadoresCompleto,
  DistribucionVentas,
  IndicadoresFiltros,
  ItemRankingProducto,
  RankingProductos,
  ResumenEjecutivo,
  SerieTemporalIngresos,
  SucursalDesempeno,
  SucursalOpcion,
} from '../modelos/indicadores.dto';

@Injectable({
  providedIn: 'root',
})
export class IndicadoresAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/indicadores';

  // --- Estado Reactivo Centralizado (Signals) ---
  readonly dashboard = signal<DashboardIndicadoresCompleto | null>(null);
  readonly resumen = signal<ResumenEjecutivo | null>(null);
  readonly serieTemporal = signal<SerieTemporalIngresos | null>(null);
  readonly topProductos = signal<ItemRankingProducto[]>([]);
  readonly distribucion = signal<DistribucionVentas | null>(null);
  readonly comparativa = signal<SucursalDesempeno[]>([]);
  readonly sucursales = signal<SucursalOpcion[]>([]);

  readonly cargando = signal<boolean>(false);
  readonly error = signal<string | null>(null);

  readonly filtros = signal<IndicadoresFiltros>({
    periodo: '30d',
    fecha_desde: null,
    fecha_hasta: null,
    id_sucursal: null,
  });

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

  private construirHttpParams(filtros: IndicadoresFiltros): HttpParams {
    let params = new HttpParams().set('periodo', filtros.periodo);

    if (filtros.fecha_desde) {
      params = params.set('fecha_desde', filtros.fecha_desde);
    }
    if (filtros.fecha_hasta) {
      params = params.set('fecha_hasta', filtros.fecha_hasta);
    }
    if (filtros.id_sucursal !== null && filtros.id_sucursal !== undefined) {
      params = params.set('id_sucursal', String(filtros.id_sucursal));
    }
    return params;
  }

  limpiarError(): void {
    this.error.set(null);
  }

  actualizarFiltros(parcial: Partial<IndicadoresFiltros>): void {
    this.filtros.update((actual) => ({
      ...actual,
      ...parcial,
    }));
    this.consultarDashboardConsolidado().subscribe();
  }

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error al consultar los indicadores empresariales.';
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
      mensaje = 'No cuenta con privilegios autorizados para consultar estos indicadores.';
    } else if (err.status === 422) {
      mensaje = 'El rango temporal seleccionado o los parametros son inconsistentes.';
    }
    this.error.set(mensaje);
    return throwError(() => new Error(mensaje));
  }

  consultarDashboardConsolidado(
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<DashboardIndicadoresCompleto> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    const params = this.construirHttpParams(f);

    return this.http
      .get<DashboardIndicadoresCompleto>(`${this.baseUrl}/dashboard`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.dashboard.set(res);
          this.resumen.set(res.resumen);
          this.serieTemporal.set(res.serie_temporal);
          this.topProductos.set(res.top_productos.productos || []);
          this.distribucion.set(res.distribucion);
          this.comparativa.set(res.comparativa_sucursales?.sucursales || []);
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  consultarResumen(
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<ResumenEjecutivo> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    const params = this.construirHttpParams(f);

    return this.http
      .get<ResumenEjecutivo>(`${this.baseUrl}/resumen`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => this.resumen.set(res)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  consultarSerieTemporal(
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<SerieTemporalIngresos> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    const params = this.construirHttpParams(f);

    return this.http
      .get<SerieTemporalIngresos>(`${this.baseUrl}/serie-temporal`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => this.serieTemporal.set(res)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  consultarTopProductos(
    limite: number = 5,
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<RankingProductos> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    let params = this.construirHttpParams(f).set('limite', String(limite));

    return this.http
      .get<RankingProductos>(`${this.baseUrl}/top-productos`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => this.topProductos.set(res.productos || [])),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  consultarDistribucion(
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<DistribucionVentas> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    const params = this.construirHttpParams(f);

    return this.http
      .get<DistribucionVentas>(`${this.baseUrl}/distribucion`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => this.distribucion.set(res)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  consultarComparativaSucursales(
    filtrosSobrescritos?: Partial<IndicadoresFiltros>
  ): Observable<ComparativaSucursales> {
    this.cargando.set(true);
    this.limpiarError();

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    const params = this.construirHttpParams(f);

    return this.http
      .get<ComparativaSucursales>(`${this.baseUrl}/comparativa-sucursales`, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => this.comparativa.set(res.sucursales || [])),
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
          this.sucursales.set(opciones);
        }),
        catchError(() => [])
      )
      .subscribe();
  }
}
