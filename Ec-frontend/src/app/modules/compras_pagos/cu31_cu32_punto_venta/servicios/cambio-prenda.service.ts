import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { Cambio, CambioIn, CambioPrevio, VentaCambiable } from '../modelos/cambio-prenda.dto';

/**
 * P2-CU18 · Cambio de prenda en caja (`/api/v1/pos/cambios`). Sin estado ni importes derivados: la
 * página muestra lo que devuelve el servidor. El administrador envía la sucursal (`id_sucursal`).
 */
@Injectable({ providedIn: 'root' })
export class CambioPrendaService {
  private readonly http = inject(HttpClient);
  private readonly base = '/api/v1/pos/cambios';

  private sucursal(idSucursal: number | null): HttpParams {
    return idSucursal ? new HttpParams().set('id_sucursal', idSucursal) : new HttpParams();
  }

  ventaCambiable(comprobante: string, idSucursal: number | null): Observable<VentaCambiable> {
    return this.http.get<VentaCambiable>(`${this.base}/venta`, {
      params: this.sucursal(idSucursal).set('comprobante', comprobante.trim()),
    });
  }

  previsualizar(cambio: CambioIn): Observable<CambioPrevio> {
    return this.http.post<CambioPrevio>(`${this.base}/previsualizar`, cambio);
  }

  registrar(cambio: CambioIn): Observable<Cambio> {
    return this.http.post<Cambio>(this.base, cambio);
  }

  cambiosDelDia(idSucursal: number | null): Observable<Cambio[]> {
    return this.http.get<Cambio[]>(this.base, { params: this.sucursal(idSucursal).set('solo_hoy', true) });
  }
}
