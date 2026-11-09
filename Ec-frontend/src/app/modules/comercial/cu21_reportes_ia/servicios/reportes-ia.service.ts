import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ContextoReportesIaEmpresa,
  GenerarReporteIaPeticion,
  SolicitudReporteIaHistorial,
  SolicitudReporteIaResultado,
} from '../modelos/reportes-ia.model';

@Injectable({ providedIn: 'root' })
export class ReportesIaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/reportes-ia';

  obtenerContextoEmpresa(): Observable<ContextoReportesIaEmpresa> {
    return this.http.get<ContextoReportesIaEmpresa>(`${this.baseUrl}/contexto`);
  }

  generarReporte(
    datos: GenerarReporteIaPeticion
  ): Observable<SolicitudReporteIaResultado> {
    return this.http.post<SolicitudReporteIaResultado>(
      `${this.baseUrl}/generar`,
      datos
    );
  }

  listarHistorial(): Observable<SolicitudReporteIaHistorial[]> {
    return this.http.get<SolicitudReporteIaHistorial[]>(
      `${this.baseUrl}/historial`
    );
  }

  exportarSolicitud(
    idSolicitud: number,
    formato: 'pdf' | 'excel'
  ): Observable<Blob> {
    const params = new HttpParams().set('formato', formato);
    return this.http.get(`${this.baseUrl}/${idSolicitud}/exportar`, {
      params,
      responseType: 'blob',
    });
  }
}

