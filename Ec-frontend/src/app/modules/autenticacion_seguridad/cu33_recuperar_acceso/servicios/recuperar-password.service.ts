import { inject, Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface SolicitarCodigoPeticion {
  email: string;
}

export interface SolicitarCodigoRespuesta {
  mensaje: string;
  tiempo_espera_segundos: number;
}

export interface RestablecerPasswordPeticion {
  email: string;
  codigo: string;
  nueva_password: string;
  confirmar_password: string;
}

export interface RestablecerPasswordRespuesta {
  mensaje: string;
  exito: boolean;
  codigo_evento: string;
}

@Injectable({
  providedIn: 'root',
})
export class RecuperarPasswordService {
  private readonly http = inject(HttpClient);
  private readonly baseUrl = '/api/v1/autenticacion/recuperar-password';

  /**
   * Solicita el envío de un código OTP de 6 dígitos al correo del usuario.
   */
  solicitarCodigo(email: string): Observable<SolicitarCodigoRespuesta> {
    return this.http.post<SolicitarCodigoRespuesta>(`${this.baseUrl}/solicitar`, {
      email,
    });
  }

  /**
   * Valida el código OTP y actualiza la contraseña del usuario.
   */
  restablecerPassword(
    datos: RestablecerPasswordPeticion,
  ): Observable<RestablecerPasswordRespuesta> {
    return this.http.post<RestablecerPasswordRespuesta>(
      `${this.baseUrl}/restablecer`,
      datos,
    );
  }
}
