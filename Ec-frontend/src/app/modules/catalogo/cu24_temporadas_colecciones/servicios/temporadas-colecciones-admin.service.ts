/**
 * Servicio HTTP y de Estado Reactivo para CU24: Gestionar temporadas y colecciones.
 * Nomenclatura oficial: "Gestionar temporadas y colecciones"
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
  ColeccionActualizarDto,
  ColeccionCrearDto,
  ColeccionItem,
  EstadoConmutarDto,
  FiltrosColecciones,
  FiltrosTemporadas,
  PestanaGestion,
  RespuestaPaginadaColecciones,
  RespuestaPaginadaTemporadas,
  TemporadaActualizarDto,
  TemporadaCrearDto,
  TemporadaItem,
} from '../modelos/temporadas-colecciones.dto';

@Injectable({
  providedIn: 'root',
})
export class TemporadasColeccionesAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrlTemporadas = '/api/v1/admin/temporadas';
  private readonly baseUrlColecciones = '/api/v1/admin/colecciones';

  // --- Estado Reactivo Centralizado (Signals) ---
  readonly pestanaActiva = signal<PestanaGestion>('temporadas');

  // Estado de Temporadas
  readonly temporadas = signal<TemporadaItem[]>([]);
  readonly totalTemporadas = signal<number>(0);
  readonly totalPaginasTemporadas = signal<number>(1);
  readonly temporadaSeleccionada = signal<TemporadaItem | null>(null);
  readonly temporadasActivasParaSelector = signal<TemporadaItem[]>([]);
  readonly filtrosTemporadas = signal<FiltrosTemporadas>({
    q: '',
    anio: undefined,
    estado_activo: 'todos',
    ordenar_por: 'anio_desc',
    pagina: 1,
    limite: 10,
  });

  // Estado de Colecciones
  readonly colecciones = signal<ColeccionItem[]>([]);
  readonly totalColecciones = signal<number>(0);
  readonly totalPaginasColecciones = signal<number>(1);
  readonly coleccionSeleccionada = signal<ColeccionItem | null>(null);
  readonly filtrosColecciones = signal<FiltrosColecciones>({
    q: '',
    id_temporada: undefined,
    estado_activo: 'todos',
    pagina: 1,
    limite: 10,
  });

  // Estado de Control y UI
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

  limpiarMensajes(): void {
    this.error.set(null);
    this.mensajeExito.set(null);
  }

  cambiarPestana(pestana: PestanaGestion): void {
    this.pestanaActiva.set(pestana);
    this.limpiarMensajes();
  }

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error en la operacion.';
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
      mensaje = 'No cuenta con privilegios autorizados para esta operacion.';
    } else if (err.status === 404) {
      mensaje = 'El registro solicitado no fue encontrado.';
    } else if (err.status === 409) {
      mensaje = 'Conflicto: Ya existe un registro con la misma denominacion o datos unicos.';
    } else if (err.status === 422) {
      mensaje = 'Los datos suministrados no cumplen con las reglas de validacion.';
    }
    this.error.set(mensaje);
    return throwError(() => err);
  }

  // ==========================================================================
  // OPERACIONES DE TEMPORADAS
  // ==========================================================================

  cargarTemporadas(filtros?: FiltrosTemporadas): Observable<RespuestaPaginadaTemporadas> {
    this.cargando.set(true);
    this.error.set(null);

    const f = filtros || this.filtrosTemporadas();
    let params = new HttpParams();

    if (f.q && f.q.trim().length > 0) {
      params = params.set('q', f.q.trim());
    }
    if (f.anio !== undefined && f.anio !== null && Number(f.anio) >= 2020) {
      params = params.set('anio', f.anio.toString());
    }
    if (f.estado_activo && f.estado_activo !== 'todos') {
      params = params.set('estado_activo', f.estado_activo);
    }
    if (f.ordenar_por) {
      params = params.set('ordenar_por', f.ordenar_por);
    }
    if (f.pagina && Number(f.pagina) > 0) {
      params = params.set('pagina', f.pagina.toString());
    }
    if (f.limite && Number(f.limite) > 0) {
      params = params.set('limite', f.limite.toString());
    }

    return this.http
      .get<RespuestaPaginadaTemporadas>(this.baseUrlTemporadas, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.temporadas.set(res.items);
          this.totalTemporadas.set(res.total);
          this.totalPaginasTemporadas.set(res.total_paginas);
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  cargarTemporadasActivasParaSelector(): Observable<RespuestaPaginadaTemporadas> {
    let params = new HttpParams()
      .set('estado_activo', 'activas')
      .set('limite', '100');

    return this.http
      .get<RespuestaPaginadaTemporadas>(this.baseUrlTemporadas, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.temporadasActivasParaSelector.set(res.items);
        }),
        catchError((err) => this.manejarError(err))
      );
  }

  obtenerTemporadaPorId(id: number): Observable<TemporadaItem> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<TemporadaItem>(`${this.baseUrlTemporadas}/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => this.temporadaSeleccionada.set(item)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  crearTemporada(payload: TemporadaCrearDto): Observable<TemporadaItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<TemporadaItem>(this.baseUrlTemporadas, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nueva) => {
          this.mensajeExito.set(`Temporada "${nueva.nombre}" registrada exitosamente.`);
          this.cargarTemporadas().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  actualizarTemporada(id: number, payload: TemporadaActualizarDto): Observable<TemporadaItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<TemporadaItem>(`${this.baseUrlTemporadas}/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.mensajeExito.set(`Temporada "${actualizada.nombre}" actualizada exitosamente.`);
          this.cargarTemporadas().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  conmutarEstadoTemporada(id: number, estado_activo: boolean): Observable<TemporadaItem> {
    this.guardando.set(true);
    this.error.set(null);

    const payload: EstadoConmutarDto = { estado_activo };
    return this.http
      .patch<TemporadaItem>(`${this.baseUrlTemporadas}/${id}/estado`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((modificada) => {
          const accion = modificada.estado_activo ? 'reactivada' : 'dada de baja';
          this.mensajeExito.set(`Temporada "${modificada.nombre}" ${accion} exitosamente.`);
          this.cargarTemporadas().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  // ==========================================================================
  // OPERACIONES DE COLECCIONES
  // ==========================================================================

  cargarColecciones(filtros?: FiltrosColecciones): Observable<RespuestaPaginadaColecciones> {
    this.cargando.set(true);
    this.error.set(null);

    const f = filtros || this.filtrosColecciones();
    let params = new HttpParams();

    if (f.q && f.q.trim().length > 0) {
      params = params.set('q', f.q.trim());
    }
    if (f.id_temporada !== undefined && f.id_temporada !== null && Number(f.id_temporada) > 0) {
      params = params.set('id_temporada', f.id_temporada.toString());
    }
    if (f.estado_activo && f.estado_activo !== 'todos') {
      params = params.set('estado_activo', f.estado_activo);
    }
    if (f.pagina && Number(f.pagina) > 0) {
      params = params.set('pagina', f.pagina.toString());
    }
    if (f.limite && Number(f.limite) > 0) {
      params = params.set('limite', f.limite.toString());
    }

    return this.http
      .get<RespuestaPaginadaColecciones>(this.baseUrlColecciones, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.colecciones.set(res.items);
          this.totalColecciones.set(res.total);
          this.totalPaginasColecciones.set(res.total_paginas);
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  obtenerColeccionPorId(id: number): Observable<ColeccionItem> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<ColeccionItem>(`${this.baseUrlColecciones}/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => this.coleccionSeleccionada.set(item)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  crearColeccion(payload: ColeccionCrearDto): Observable<ColeccionItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<ColeccionItem>(this.baseUrlColecciones, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nueva) => {
          this.mensajeExito.set(`Coleccion "${nueva.nombre}" registrada exitosamente.`);
          this.cargarColecciones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  actualizarColeccion(id: number, payload: ColeccionActualizarDto): Observable<ColeccionItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<ColeccionItem>(`${this.baseUrlColecciones}/${id}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.mensajeExito.set(`Coleccion "${actualizada.nombre}" actualizada exitosamente.`);
          this.cargarColecciones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  conmutarEstadoColeccion(id: number, estado_activo: boolean): Observable<ColeccionItem> {
    this.guardando.set(true);
    this.error.set(null);

    const payload: EstadoConmutarDto = { estado_activo };
    return this.http
      .patch<ColeccionItem>(`${this.baseUrlColecciones}/${id}/estado`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((modificada) => {
          const accion = modificada.estado_activo ? 'reactivada' : 'dada de baja';
          this.mensajeExito.set(`Coleccion "${modificada.nombre}" ${accion} exitosamente.`);
          this.cargarColecciones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }
}
