/**
 * Servicio HTTP y de Estado Reactivo para CU31: Generar reportes ejecutivos y consultas por voz.
 * Nomenclatura oficial: "Generar reportes ejecutivos y consultas por voz"
 */

import { Injectable, inject, signal } from '@angular/core';
import {
  HttpClient,
  HttpErrorResponse,
  HttpHeaders,
  HttpResponse,
} from '@angular/common/http';
import { Observable, catchError, finalize, tap, throwError } from 'rxjs';
import {
  ComandoVozIn,
  ComandoVozOut,
  ReporteFiltros,
  ReportePrevisualizacion,
  SucursalOpcionReporte,
} from '../modelos/reportes-voz.dto';

@Injectable({
  providedIn: 'root',
})
export class ReportesAdminService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/admin/reportes';

  // --- Estado Reactivo Centralizado (Signals) ---
  readonly filtros = signal<ReporteFiltros>({
    modulo: 'ventas',
    formato: 'excel',
    periodo: 'este_mes',
    id_sucursal: null,
    fecha_inicio: null,
    fecha_fin: null,
  });

  readonly previsualizacion = signal<ReportePrevisualizacion | null>(null);
  readonly generando = signal<boolean>(false);
  readonly previsualizando = signal<boolean>(false);
  readonly error = signal<string | null>(null);
  readonly comandoVozActivo = signal<ComandoVozOut | null>(null);
  readonly sucursales = signal<SucursalOpcionReporte[]>([]);

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

  interpretarComandoVoz(peticion: ComandoVozIn): Observable<ComandoVozOut> {
    this.generando.set(true);
    this.error.set(null);

    return this.http
      .post<ComandoVozOut>(
        `${this.baseUrl}/interpretar-voz`,
        peticion,
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((res) => {
          this.comandoVozActivo.set(res);
          // Sincronizar filtros reactivos segun la respuesta de voz
          this.actualizarFiltros({
            modulo: res.modulo,
            formato: res.formato,
            periodo: res.periodo,
            id_sucursal: res.id_sucursal ?? null,
            fecha_inicio: res.fecha_inicio ?? null,
            fecha_fin: res.fecha_fin ?? null,
          });
        }),
        catchError((err: HttpErrorResponse) => {
          const detalle =
            err.error?.detail ||
            'No se pudo interpretar el comando de voz. Intente con otra frase.';
          this.error.set(detalle);
          return throwError(() => err);
        }),
        finalize(() => this.generando.set(false))
      );
  }

  cargarPrevisualizacion(filtros?: ReporteFiltros): Observable<ReportePrevisualizacion> {
    const paramsFiltros = filtros || this.filtros();
    this.previsualizando.set(true);
    this.error.set(null);

    return this.http
      .post<ReportePrevisualizacion>(
        `${this.baseUrl}/previsualizar`,
        paramsFiltros,
        { headers: this.obtenerHeaders() }
      )
      .pipe(
        tap((res) => {
          this.previsualizacion.set(res);
        }),
        catchError((err: HttpErrorResponse) => {
          const detalle =
            err.error?.detail ||
            'Error al calcular la previsualizacion del reporte.';
          this.error.set(detalle);
          return throwError(() => err);
        }),
        finalize(() => this.previsualizando.set(false))
      );
  }

  exportarReporte(filtros?: ReporteFiltros): Observable<HttpResponse<Blob>> {
    const paramsFiltros = filtros || this.filtros();
    this.generando.set(true);
    this.error.set(null);

    const headers = this.obtenerHeaders();

    return this.http
      .post(`${this.baseUrl}/exportar`, paramsFiltros, {
        headers,
        observe: 'response',
        responseType: 'blob',
      })
      .pipe(
        tap((respuesta: HttpResponse<Blob>) => {
          if (respuesta.body) {
            let nombreArchivo = this.extraerNombreArchivo(respuesta);
            if (!nombreArchivo) {
              const extension =
                paramsFiltros.formato === 'excel'
                  ? 'xlsx'
                  : paramsFiltros.formato;
              nombreArchivo = `reporte_${paramsFiltros.modulo}_${Date.now()}.${extension}`;
            }
            this.descargarBlob(respuesta.body, nombreArchivo);
          }
        }),
        catchError((err: HttpErrorResponse) => {
          const detalle =
            'Error al generar y descargar el archivo binario del reporte.';
          this.error.set(detalle);
          return throwError(() => err);
        }),
        finalize(() => this.generando.set(false))
      );
  }

  cargarSucursales(): Observable<SucursalOpcionReporte[]> {
    return this.http
      .get<SucursalOpcionReporte[]>('/api/v1/admin/sucursales', {
        headers: this.obtenerHeaders(),
      })
      .pipe(
        tap((lista) => {
          if (Array.isArray(lista)) {
            this.sucursales.set(lista);
          }
        }),
        catchError((err) => {
          // Si falla o no existe el endpoint, mantener fallback defensivo vacio
          return throwError(() => err);
        })
      );
  }

  actualizarFiltros(parcial: Partial<ReporteFiltros>): void {
    this.filtros.update((actual) => ({
      ...actual,
      ...parcial,
    }));
  }

  limpiarError(): void {
    this.error.set(null);
  }

  descargarBlob(blob: Blob, nombreArchivo: string): void {
    if (typeof window === 'undefined') {
      return;
    }

    try {
      const url = window.URL.createObjectURL(blob);
      const enlace = document.createElement('a');
      enlace.href = url;
      enlace.download = nombreArchivo;
      document.body.appendChild(enlace);
      enlace.click();
      document.body.removeChild(enlace);
      window.URL.revokeObjectURL(url);
    } catch (e) {
      console.error('Error al iniciar la descarga del archivo binario:', e);
    }
  }

  private extraerNombreArchivo(respuesta: HttpResponse<Blob>): string | null {
    const header = respuesta.headers.get('Content-Disposition');
    if (!header) return null;

    const coincidencia = header.match(/filename="?([^";]+)"?/i);
    return coincidencia ? coincidencia[1] : null;
  }
}
