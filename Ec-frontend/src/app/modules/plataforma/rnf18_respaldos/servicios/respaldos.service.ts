import { HttpClient, HttpParams, HttpResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

/** RNF18 · Respaldo manual de datos (`GET /api/v1/plataforma/respaldos`), solo super administrador. */
@Injectable({ providedIn: 'root' })
export class RespaldosService {
  private readonly http = inject(HttpClient);

  /** Sin empresa: toda la plataforma. El archivo llega entero (SQL con bloques `COPY`). */
  descargar(idTenant: number | null): Observable<HttpResponse<Blob>> {
    const params = idTenant == null ? undefined : new HttpParams().set('id_tenant', idTenant);
    return this.http.get('/api/v1/plataforma/respaldos', { params, responseType: 'blob', observe: 'response' });
  }
}

/** Nombre del archivo de `Content-Disposition` (o uno por defecto). */
export function nombreDeArchivo(cabecera: string | null): string {
  const coincidencia = /filename="([^"]+)"/.exec(cabecera ?? '');
  return coincidencia?.[1] ?? 'respaldo.sql';
}
