import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  ComprobanteTransferenciaOut,
  DisponibilidadPublicaOut,
  FiltrosInventario,
  HistorialKardexOut,
  InventarioAjustePayload,
  InventarioCrearPayload,
  InventarioItemAdmin,
  ListaPaginadaInventario,
  TransferenciaPayload,
} from '../modelos/inventario.dto';

@Injectable({
  providedIn: 'root',
})
export class InventarioAdminService {
  private readonly http = inject(HttpClient);
  private readonly adminUrl = '/api/v1/admin/inventario';
  private readonly publicUrl = '/api/v1/inventario';

  // --- Signals de Estado Reactivo ---
  readonly inventario = signal<InventarioItemAdmin[]>([]);
  readonly totalRegistros = signal<number>(0);
  readonly paginaActual = signal<number>(1);
  readonly totalPaginas = signal<number>(1);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);
  readonly kardexActual = signal<HistorialKardexOut | null>(null);
  readonly disponibilidadActual = signal<DisponibilidadPublicaOut | null>(null);
  readonly filtros = signal<FiltrosInventario>({ pagina: 1, limite: 20 });

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

  limpiarKardex(): void {
    this.kardexActual.set(null);
  }

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error inesperado al procesar la operacion de inventario.';
    if (err.error?.detail) {
      mensaje = typeof err.error.detail === 'string' ? err.error.detail : JSON.stringify(err.error.detail);
    } else if (err.status === 401) {
      mensaje = 'Su sesion ha expirado o no tiene credenciales validas.';
    } else if (err.status === 403) {
      mensaje = 'No tiene autorizacion para gestionar las existencias de esta sucursal.';
    } else if (err.status === 404) {
      mensaje = 'El registro de inventario o variante no fue encontrado.';
    } else if (err.status === 409) {
      mensaje = 'Conflicto: Stock insuficiente o inventario ya registrado.';
    } else if (err.status === 422) {
      mensaje = 'Datos de operacion invalidos o entidad inactiva.';
    }
    this.error.set(mensaje);
    return throwError(() => err);
  }

  cargarInventario(filtros?: FiltrosInventario): Observable<ListaPaginadaInventario> {
    this.cargando.set(true);
    this.error.set(null);

    const f = filtros || this.filtros();
    let params = new HttpParams();

    if (
      f.id_sucursal !== undefined &&
      f.id_sucursal !== null &&
      String(f.id_sucursal).trim() !== '' &&
      String(f.id_sucursal) !== 'null' &&
      !isNaN(Number(f.id_sucursal)) &&
      Number(f.id_sucursal) > 0
    ) {
      params = params.set('id_sucursal', Number(f.id_sucursal).toString());
    }

    if (
      f.id_categoria !== undefined &&
      f.id_categoria !== null &&
      String(f.id_categoria).trim() !== '' &&
      String(f.id_categoria) !== 'null' &&
      !isNaN(Number(f.id_categoria)) &&
      Number(f.id_categoria) > 0
    ) {
      params = params.set('id_categoria', Number(f.id_categoria).toString());
    }

    const estadoStock = (f.estado_stock || (f as any).estado || '').toString().trim();
    if (
      estadoStock &&
      estadoStock !== 'todos' &&
      estadoStock !== 'null' &&
      estadoStock !== 'undefined'
    ) {
      params = params.set('estado_stock', estadoStock);
    }

    if (f.q && f.q.trim().length > 0) {
      params = params.set('q', f.q.trim());
    }

    if (f.pagina && !isNaN(Number(f.pagina)) && Number(f.pagina) > 0) {
      params = params.set('pagina', Number(f.pagina).toString());
    }

    if (f.limite && !isNaN(Number(f.limite)) && Number(f.limite) > 0) {
      params = params.set('limite', Number(f.limite).toString());
    }

    return this.http
      .get<ListaPaginadaInventario>(this.adminUrl, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.inventario.set(res.items);
          this.totalRegistros.set(res.total);
          this.paginaActual.set(res.pagina);
          this.totalPaginas.set(res.total_paginas);
          this.filtros.set(f);
          this.cargando.set(false);
        }),
        catchError((err) => {
          this.cargando.set(false);
          return this.manejarError(err);
        })
      );
  }

  crearStockInicial(payload: InventarioCrearPayload): Observable<InventarioItemAdmin> {
    this.guardando.set(true);
    this.limpiarMensajes();

    return this.http
      .post<InventarioItemAdmin>(this.adminUrl, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => {
          this.guardando.set(false);
          this.mensajeExito.set('Existencias iniciales registradas exitosamente en la boutique.');
          // Insertar al inicio de la lista reactiva
          this.inventario.update((actual) => [item, ...actual]);
          this.totalRegistros.update((n) => n + 1);
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }

  ajustarStock(id_inventario: number, payload: InventarioAjustePayload): Observable<InventarioItemAdmin> {
    this.guardando.set(true);
    this.limpiarMensajes();

    return this.http
      .post<InventarioItemAdmin>(`${this.adminUrl}/${id_inventario}/ajuste`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => {
          this.guardando.set(false);
          this.mensajeExito.set('Ajuste de inventario fisico aplicado y registrado en Kardex.');
          // Actualizar el item modificado en la lista reactiva
          this.inventario.update((lista) =>
            lista.map((x) => (x.id_inventario === id_inventario ? item : x))
          );
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }

  transferirMercaderia(payload: TransferenciaPayload): Observable<ComprobanteTransferenciaOut> {
    this.guardando.set(true);
    this.limpiarMensajes();

    return this.http
      .post<ComprobanteTransferenciaOut>(`${this.adminUrl}/transferencia`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((res) => {
          this.guardando.set(false);
          this.mensajeExito.set(res.mensaje || 'Transferencia inter-sucursal completada con exito.');
          // Recargar el inventario para reflejar ambos saldos actualizados
          this.cargarInventario().subscribe();
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }

  cargarKardex(id_inventario: number): Observable<HistorialKardexOut> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<HistorialKardexOut>(`${this.adminUrl}/${id_inventario}/kardex`, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((kardex) => {
          this.kardexActual.set(kardex);
          this.cargando.set(false);
        }),
        catchError((err) => {
          this.cargando.set(false);
          return this.manejarError(err);
        })
      );
  }

  consultarDisponibilidad(id_variante: number): Observable<DisponibilidadPublicaOut> {
    this.cargando.set(true);
    this.error.set(null);

    return this.http
      .get<DisponibilidadPublicaOut>(`${this.publicUrl}/disponibilidad/${id_variante}`)
      .pipe(
        tap((disp) => {
          this.disponibilidadActual.set(disp);
          this.cargando.set(false);
        }),
        catchError((err) => {
          this.cargando.set(false);
          return this.manejarError(err);
        })
      );
  }
}
