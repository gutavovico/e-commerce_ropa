import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, catchError, throwError } from 'rxjs';
import {
  RegistroClientePeticion,
  RegistroClienteRespuesta,
} from '../modelos/registro.dto';

@Injectable({
  providedIn: 'root',
})
export class RegistroService {
  private readonly http = inject(HttpClient);
  private readonly endpoint = '/api/v1/autenticacion/registrarse';

  /**
   * Envia la solicitud de registro al backend de FastAPI.
   * @param peticion Datos de entrada validados del nuevo cliente.
   */
  registrar(peticion: RegistroClientePeticion): Observable<RegistroClienteRespuesta> {
    return this.http.post<RegistroClienteRespuesta>(this.endpoint, peticion).pipe(
      catchError((error: HttpErrorResponse) => {
        let mensaje = 'Ocurrió un error inesperado al procesar el registro.';

        if (error.status === 409) {
          mensaje =
            error.error?.detail ||
            'El correo electrónico ya se encuentra registrado en la plataforma.';
        } else if (error.status === 422) {
          mensaje = 'Por favor verifica que todos los campos tengan el formato correcto.';
        } else if (error.status === 400) {
          mensaje = error.error?.detail || 'Datos de registro inválidos.';
        } else if (error.status === 0) {
          mensaje = 'No se pudo conectar con el servidor. Revisa tu conexión de red.';
        }

        return throwError(() => new Error(mensaje));
      })
    );
  }
}
