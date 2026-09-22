import { Injectable, inject, signal } from '@angular/core';
import { HttpClient, HttpErrorResponse, HttpHeaders, HttpParams } from '@angular/common/http';
import { Observable, tap, catchError, throwError } from 'rxjs';
import {
  FiltrosProveedores,
  ListaPaginadaProveedores,
  ProveedorActualizarPayload,
  ProveedorCrearPayload,
  ProveedorEstadoPayload,
  ProveedorItemAdmin,
} from '../modelos/proveedor.dto';

@Injectable({
  providedIn: 'root',
})
export class ProveedoresAdminService {
  private readonly http = inject(HttpClient);
  private readonly adminUrl = '/api/v1/admin/proveedores';

  // --- Signals de Estado Reactivo ---
  readonly proveedores = signal<ProveedorItemAdmin[]>([]);
  readonly totalRegistros = signal<number>(0);
  readonly paginaActual = signal<number>(1);
  readonly totalPaginas = signal<number>(1);
  readonly cargando = signal<boolean>(false);
  readonly guardando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly mensajeExito = signal<string | null>(null);
  readonly filtros = signal<FiltrosProveedores>({ pagina: 1, limite: 20 });

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

  private manejarError(err: HttpErrorResponse): Observable<never> {
    let mensaje = 'Ocurrio un error inesperado al procesar la operacion de proveedores.';
    if (err.error?.detail) {
      mensaje =
        typeof err.error.detail === 'string'
          ? err.error.detail
          : JSON.stringify(err.error.detail);
    } else if (err.status === 401) {
      mensaje = 'Su sesion ha expirado o no tiene credenciales validas.';
    } else if (err.status === 403) {
      mensaje = 'Acceso denegado: No cuenta con privilegios para gestionar proveedores.';
    } else if (err.status === 404) {
      mensaje = 'El proveedor solicitado no fue encontrado en el padron.';
    } else if (err.status === 409) {
      mensaje = 'Conflicto: Ya existe un proveedor registrado con ese NIT/RUT o Razon Social.';
    } else if (err.status === 422) {
      mensaje = 'Datos invalidos: Compruebe el formato de correo o la longitud de los campos obligatorios.';
    }
    this.error.set(mensaje);
    return throwError(() => err);
  }

  cargarProveedores(filtros?: FiltrosProveedores): Observable<ListaPaginadaProveedores> {
    this.cargando.set(true);
    this.error.set(null);

    const f = filtros || this.filtros();
    let params = new HttpParams();

    if (f.q && f.q.trim().length > 0) {
      params = params.set('q', f.q.trim());
    }

    if (f.estado && f.estado !== 'todos' && f.estado !== 'null') {
      params = params.set('estado', f.estado);
    } else if (f.estado_activo !== undefined && f.estado_activo !== null) {
      params = params.set('estado_activo', f.estado_activo.toString());
    }

    if (f.rubro && f.rubro.trim().length > 0 && f.rubro !== 'todos') {
      params = params.set('rubro', f.rubro.trim());
    }

    if (f.pagina && !isNaN(Number(f.pagina)) && Number(f.pagina) > 0) {
      params = params.set('pagina', Number(f.pagina).toString());
    }

    if (f.limite && !isNaN(Number(f.limite)) && Number(f.limite) > 0) {
      params = params.set('limite', Number(f.limite).toString());
    }

    return this.http
      .get<ListaPaginadaProveedores>(this.adminUrl, {
        headers: this.obtenerHeaders(),
        params,
      })
      .pipe(
        tap((res) => {
          this.proveedores.set(res.items);
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

  crearProveedor(payload: ProveedorCrearPayload): Observable<ProveedorItemAdmin> {
    this.guardando.set(true);
    this.limpiarMensajes();

    return this.http
      .post<ProveedorItemAdmin>(this.adminUrl, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => {
          this.guardando.set(false);
          this.mensajeExito.set('Proveedor registrado exitosamente en el padron comercial.');
          this.proveedores.update((lista) => [item, ...lista]);
          this.totalRegistros.update((n) => n + 1);
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }

  actualizarProveedor(
    id_proveedor: number,
    payload: ProveedorActualizarPayload
  ): Observable<ProveedorItemAdmin> {
    this.guardando.set(true);
    this.limpiarMensajes();

    return this.http
      .put<ProveedorItemAdmin>(`${this.adminUrl}/${id_proveedor}`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => {
          this.guardando.set(false);
          this.mensajeExito.set('Ficha comercial del proveedor actualizada correctamente.');
          this.proveedores.update((lista) =>
            lista.map((x) => (x.id_proveedor === id_proveedor ? item : x))
          );
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }

  listarProveedores(filtros?: FiltrosProveedores): Observable<ListaPaginadaProveedores> {
    return this.cargarProveedores(filtros);
  }

  cambiarEstadoProveedor(
    id_proveedor: number,
    estado: boolean | ProveedorEstadoPayload
  ): Observable<ProveedorItemAdmin> {
    this.guardando.set(true);
    this.limpiarMensajes();

    const estado_activo = typeof estado === 'boolean' ? estado : estado.estado_activo;
    const payload: ProveedorEstadoPayload = { estado_activo };

    return this.http
      .patch<ProveedorItemAdmin>(`${this.adminUrl}/${id_proveedor}/estado`, payload, {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((item) => {
          this.guardando.set(false);
          const accion = estado_activo ? 'reactivado' : 'desactivado (baja logica)';
          this.mensajeExito.set(`Proveedor ${accion} exitosamente.`);
          this.proveedores.update((lista) =>
            lista.map((x) => (x.id_proveedor === id_proveedor ? item : x))
          );
        }),
        catchError((err) => {
          this.guardando.set(false);
          return this.manejarError(err);
        })
      );
  }
}
