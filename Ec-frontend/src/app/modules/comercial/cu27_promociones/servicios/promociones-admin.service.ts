/**
 * Servicio HTTP y de Estado Reactivo para CU27: Gestionar promociones.
 * Nomenclatura oficial: "Gestionar promociones"
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
  FiltrosPromociones,
  MetricasPromociones,
  PromocionActualizarDto,
  PromocionCrearDto,
  PromocionItem,
  RespuestaPaginadaPromociones,
} from '../modelos/promociones.dto';

@Injectable({
  providedIn: 'root',
})
export class PromocionesAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/promociones';

  // --- Estado Reactivo Centralizado (Signals) ---
  readonly promociones = signal<PromocionItem[]>([]);
  readonly metricas = signal<MetricasPromociones | null>(null);
  readonly promocionSeleccionada = signal<PromocionItem | null>(null);
  readonly totalPromociones = signal<number>(0);
  readonly totalPaginas = signal<number>(1);

  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);

  readonly filtros = signal<FiltrosPromociones>({
    q: '',
    tipo_descuento: 'todos',
    estado_activo: 'todos',
    alcance: 'todos',
    pagina: 1,
    limite: 10,
    ordenar_por: 'creado_en_desc',
  });

  // Colecciones auxiliares para selectores condicionales
  readonly categoriasDisponibles = signal<{ id_categoria: number; nombre: string }[]>([]);
  readonly productosDisponibles = signal<{ id_producto: number; nombre: string }[]>([]);

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

  actualizarFiltros(parcial: Partial<FiltrosPromociones>): void {
    this.filtros.update((actual) => ({
      ...actual,
      ...parcial,
      pagina: parcial.pagina !== undefined ? parcial.pagina : 1,
    }));
    this.listarPromociones().subscribe();
  }

  resetearFiltros(): void {
    this.filtros.set({
      q: '',
      tipo_descuento: 'todos',
      estado_activo: 'todos',
      alcance: 'todos',
      pagina: 1,
      limite: 10,
      ordenar_por: 'creado_en_desc',
    });
    this.listarPromociones().subscribe();
  }

  cambiarPagina(nuevaPagina: number): void {
    if (nuevaPagina < 1 || nuevaPagina > this.totalPaginas()) {
      return;
    }
    this.filtros.update((f) => ({ ...f, pagina: nuevaPagina }));
    this.listarPromociones().subscribe();
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
      mensaje = 'La promocion solicitada no fue encontrada.';
    } else if (err.status === 409) {
      mensaje = 'Conflicto: Ya existe un cupon promocional registrado con este mismo codigo.';
    } else if (err.status === 422) {
      mensaje = 'Los datos suministrados no cumplen con las reglas de validacion.';
    }
    this.error.set(mensaje);
    return throwError(() => new Error(mensaje));
  }

  listarPromociones(
    filtrosSobrescritos?: Partial<FiltrosPromociones>
  ): Observable<RespuestaPaginadaPromociones> {
    this.cargando.set(true);
    this.error.set(null);

    const f = { ...this.filtros(), ...(filtrosSobrescritos || {}) };
    let params = new HttpParams()
      .set('pagina', String(f.pagina || 1))
      .set('limite', String(f.limite || 10));

    if (f.q && f.q.trim()) {
      params = params.set('q', f.q.trim());
    }
    if (f.tipo_descuento && f.tipo_descuento !== 'todos') {
      params = params.set('tipo_descuento', f.tipo_descuento);
    }
    if (f.estado_activo !== 'todos' && f.estado_activo !== undefined) {
      if (f.estado_activo === 'activas' || f.estado_activo === true) {
        params = params.set('estado_activo', 'true');
      } else if (f.estado_activo === 'inactivas' || f.estado_activo === false) {
        params = params.set('estado_activo', 'false');
      }
    }
    if (f.alcance && f.alcance !== 'todos') {
      params = params.set('alcance', f.alcance);
    }
    if (f.ordenar_por) {
      params = params.set('ordenar_por', f.ordenar_por);
    }

    return this.http
      .get<RespuestaPaginadaPromociones>(this.baseUrl, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.promociones.set(res.items || []);
          this.totalPromociones.set(res.total || 0);
          this.totalPaginas.set(res.total_paginas || 1);
          if (res.metricas) {
            this.metricas.set(res.metricas);
          }
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  obtenerPromocionPorId(id: number): Observable<PromocionItem> {
    this.cargando.set(true);
    this.limpiarMensajes();

    return this.http
      .get<PromocionItem>(`${this.baseUrl}/${id}`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((promo) => this.promocionSeleccionada.set(promo)),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.cargando.set(false))
      );
  }

  crearPromocion(dto: PromocionCrearDto): Observable<PromocionItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .post<PromocionItem>(this.baseUrl, dto, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((nueva) => {
          this.mensajeExito.set(
            `Promocion "${nueva.nombre}" creada satisfactoriamente.`
          );
          this.listarPromociones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  actualizarPromocion(
    id: number,
    dto: PromocionActualizarDto
  ): Observable<PromocionItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .put<PromocionItem>(`${this.baseUrl}/${id}`, dto, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((actualizada) => {
          this.mensajeExito.set(
            `Promocion "${actualizada.nombre}" actualizada con exito.`
          );
          this.listarPromociones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  conmutarEstado(
    id: number,
    estado_activo: boolean
  ): Observable<PromocionItem> {
    this.guardando.set(true);
    this.error.set(null);

    return this.http
      .patch<PromocionItem>(
        `${this.baseUrl}/${id}/estado`,
        { estado_activo },
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((actualizada) => {
          const accion = actualizada.estado_activo ? 'reactivada' : 'desactivada';
          this.mensajeExito.set(
            `Promocion "${actualizada.nombre}" ${accion} correctamente.`
          );
          this.listarPromociones().subscribe();
        }),
        catchError((err) => this.manejarError(err)),
        finalize(() => this.guardando.set(false))
      );
  }

  cargarAuxiliares(): void {
    // Categorias para selector condicional
    this.http
      .get<{ id_categoria: number; nombre: string }[]>('/api/v1/admin/categorias', {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((cats) => this.categoriasDisponibles.set(cats || [])),
        catchError(() => [])
      )
      .subscribe();

    // Productos para selector condicional
    this.http
      .get<{ id_producto: number; nombre: string }[]>('/api/v1/admin/productos', {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((prods) => this.productosDisponibles.set(prods || [])),
        catchError(() => [])
      )
      .subscribe();
  }
}
