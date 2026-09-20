import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import {
  RecuperarPasswordService,
  SolicitarCodigoRespuesta,
  RestablecerPasswordRespuesta,
} from './recuperar-password.service';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('RecuperarPasswordService (CU33)', () => {
  let service: RecuperarPasswordService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        RecuperarPasswordService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(RecuperarPasswordService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe enviar POST a /solicitar con el email', () => {
    const mockRespuesta: SolicitarCodigoRespuesta = {
      mensaje: 'Si el correo existe, se envió el código.',
      tiempo_espera_segundos: 60,
    };

    service.solicitarCodigo('cliente@fashionstore.com').subscribe((res) => {
      expect(res).toEqual(mockRespuesta);
    });

    const req = httpMock.expectOne(
      '/api/v1/autenticacion/recuperar-password/solicitar',
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'cliente@fashionstore.com' });
    req.flush(mockRespuesta);
  });

  it('debe enviar POST a /restablecer con los datos de cambio de clave', () => {
    const mockRespuesta: RestablecerPasswordRespuesta = {
      mensaje: 'Contraseña actualizada exitosamente.',
      exito: true,
      codigo_evento: 'PASSWORD_RESTABLECIDA',
    };

    const peticion = {
      email: 'cliente@fashionstore.com',
      codigo: '849201',
      nueva_password: 'NuevaPassword123',
      confirmar_password: 'NuevaPassword123',
    };

    service.restablecerPassword(peticion).subscribe((res) => {
      expect(res).toEqual(mockRespuesta);
    });

    const req = httpMock.expectOne(
      '/api/v1/autenticacion/recuperar-password/restablecer',
    );
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(peticion);
    req.flush(mockRespuesta);
  });
});
