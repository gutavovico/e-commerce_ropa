import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  DisponibilidadSucursalItem,
  ReservaConfirmacion,
  ReservaCrearPayload,
} from '../modelos/producto-detalle.model';

@Injectable({
  providedIn: 'root',
})
export class ReservaService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1';

  /**
   * Obtiene el directorio de boutiques insignia activas para el modal de citas presenciales.
   */
  obtenerSucursalesActivas(): Observable<DisponibilidadSucursalItem[]> {
    return this.http.get<DisponibilidadSucursalItem[]>(`${this.baseUrl}/sucursales/activas`);
  }

  /**
   * CU12: Crea una cita de prueba presencial en boutique reservando las prendas solicitadas.
   */
  crearReservaBoutique(payload: ReservaCrearPayload): Observable<ReservaConfirmacion> {
    return this.http.post<ReservaConfirmacion>(`${this.baseUrl}/reservas`, payload);
  }
}
