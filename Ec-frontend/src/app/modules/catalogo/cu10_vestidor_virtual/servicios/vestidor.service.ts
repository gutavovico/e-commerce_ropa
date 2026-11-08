import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  SesionVestidorActualizarIn,
  SesionVestidorCrearIn,
  SesionVestidorOut,
  TokenVestidorDecartOut,
} from '../modelos/vestidor.dto';

@Injectable({
  providedIn: 'root',
})
export class VestidorService {
  private readonly http = inject(HttpClient);
  private readonly endpointBase = '/api/v1/vestidor';

  /**
   * Solicita al backend un token efímero de corta duración (~60 s) para conectar con Decart Lucy VTON.
   * La petición no lleva cuerpo (solo autenticación JWT Bearer en cabecera).
   * Si Decart falla, se agotan los créditos o no está disponible, retorna error HTTP 503.
   */
  obtenerTokenDecart(): Observable<TokenVestidorDecartOut> {
    return this.http.post<TokenVestidorDecartOut>(`${this.endpointBase}/token`, {});
  }

  /**
   * Registra la interacción del cliente con el vestidor virtual (Prueba 3).
   * Persiste id_producto, motor ('local' | 'ia'), duracion_segundos e indicador de interés.
   */
  registrarSesion(datos: SesionVestidorCrearIn): Observable<SesionVestidorOut> {
    return this.http.post<SesionVestidorOut>(`${this.endpointBase}/sesion`, datos);
  }

  /**
   * Actualiza el interés comercial o URL de captura tras añadir al carrito o reservar.
   */
  actualizarSesion(
    idSesionAr: number,
    datos: SesionVestidorActualizarIn
  ): Observable<SesionVestidorOut> {
    return this.http.patch<SesionVestidorOut>(
      `${this.endpointBase}/sesion/${idSesionAr}`,
      datos
    );
  }
}

