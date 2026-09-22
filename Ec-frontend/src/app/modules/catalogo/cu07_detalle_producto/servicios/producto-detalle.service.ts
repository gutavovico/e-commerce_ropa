import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpParams } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  DisponibilidadSucursales,
  ProductoDetalle,
} from '../modelos/producto-detalle.model';

@Injectable({
  providedIn: 'root',
})
export class ProductoDetalleService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  /**
   * CU07 & CU08: Obtiene la ficha técnica completa de una prenda con sus variantes,
   * composición noble, galería multi-toma y recomendaciones de look.
   */
  obtenerDetalle(idProducto: number): Observable<ProductoDetalle> {
    return this.http.get<ProductoDetalle>(`${this.baseUrl}/productos/${idProducto}`);
  }

  /**
   * CU09: Obtiene la disponibilidad física en tiempo real en la red de boutiques
   * para la prenda o variante especificada.
   */
  obtenerDisponibilidad(
    idProducto: number,
    idVariante?: number | null
  ): Observable<DisponibilidadSucursales> {
    let params = new HttpParams();
    if (idVariante) {
      params = params.set('id_variante', idVariante.toString());
    }
    return this.http.get<DisponibilidadSucursales>(
      `${this.baseUrl}/productos/${idProducto}/disponibilidad`,
      { params }
    );
  }
}
