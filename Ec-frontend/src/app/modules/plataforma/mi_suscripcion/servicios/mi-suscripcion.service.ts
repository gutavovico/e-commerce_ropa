import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import {
  ConfirmarCambioSuscripcionDto,
  IniciarPagoSuscripcionDto,
  IntentoPagoSuscripcion,
  MiSuscripcionResumen,
  PlanDisponibleEmpresa,
} from '../modelos/mi-suscripcion.model';

@Injectable({
  providedIn: 'root',
})
export class MiSuscripcionService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/plataforma/mi-suscripcion';

  obtenerMiSuscripcion(): Observable<MiSuscripcionResumen> {
    return this.http.get<MiSuscripcionResumen>(this.baseUrl);
  }

  listarPlanesDisponibles(): Observable<PlanDisponibleEmpresa[]> {
    return this.http.get<PlanDisponibleEmpresa[]>(`${this.baseUrl}/planes`);
  }

  iniciarPago(datos: IniciarPagoSuscripcionDto): Observable<IntentoPagoSuscripcion> {
    return this.http.post<IntentoPagoSuscripcion>(`${this.baseUrl}/iniciar-pago`, datos);
  }

  confirmarCambioORenovacion(
    datos: ConfirmarCambioSuscripcionDto
  ): Observable<MiSuscripcionResumen> {
    return this.http.post<MiSuscripcionResumen>(`${this.baseUrl}/confirmar`, datos);
  }
}
