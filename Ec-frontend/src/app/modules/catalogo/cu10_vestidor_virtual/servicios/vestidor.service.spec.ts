import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { VestidorService } from './vestidor.service';
import {
  SesionVestidorCrearIn,
  SesionVestidorOut,
  TokenVestidorDecartOut,
} from '../modelos/vestidor.dto';

describe('VestidorService (CU10)', () => {
  let service: VestidorService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [VestidorService, provideHttpClient(), provideHttpClientTesting()],
    });

    service = TestBed.inject(VestidorService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe crearse exitosamente', () => {
    expect(service).toBeTruthy();
  });

  it('debe solicitar token efímero a POST /api/v1/vestidor/token sin cuerpo en la petición', () => {
    const respuestaMock: TokenVestidorDecartOut = {
      token: 'decart_client_token_test_123',
      expira_en_segundos: 60,
      servicio: 'decart_lucy_vton_720p',
    };

    service.obtenerTokenDecart().subscribe((res) => {
      expect(res.token).toBe('decart_client_token_test_123');
      expect(res.expira_en_segundos).toBe(60);
      expect(res.servicio).toBe('decart_lucy_vton_720p');
    });

    const req = httpMock.expectOne('/api/v1/vestidor/token');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({});
    req.flush(respuestaMock);
  });

  it('debe registrar sesión de vestidor en POST /api/v1/vestidor/sesion (Prueba 3)', () => {
    const payload: SesionVestidorCrearIn = {
      id_producto: 42,
      dispositivo: 'web',
      motor: 'local',
      duracion_segundos: 45,
      resultado_url: 'https://fashionstore.com/renders/test.jpg',
      genero_interes: true,
    };

    const respuestaMock: SesionVestidorOut = {
      id_sesion_ar: 845,
      id_cliente: 10,
      id_producto: 42,
      dispositivo: 'web',
      motor: 'local',
      duracion_segundos: 45,
      fecha_hora: '2026-09-13T16:44:28Z',
      resultado_url: 'https://fashionstore.com/renders/test.jpg',
      genero_interes: true,
    };

    service.registrarSesion(payload).subscribe((res) => {
      expect(res.id_sesion_ar).toBe(845);
      expect(res.motor).toBe('local');
      expect(res.duracion_segundos).toBe(45);
      expect(res.genero_interes).toBe(true);
    });

    const req = httpMock.expectOne('/api/v1/vestidor/sesion');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(respuestaMock);
  });

  it('debe actualizar una sesión existente en PATCH /api/v1/vestidor/sesion/:id', () => {
    const respuestaMock: SesionVestidorOut = {
      id_sesion_ar: 845,
      id_cliente: 10,
      id_producto: 42,
      dispositivo: 'web',
      motor: 'ia',
      duracion_segundos: 60,
      fecha_hora: '2026-09-13T16:45:00Z',
      resultado_url: 'https://fashionstore.com/captura.jpg',
      genero_interes: true,
    };

    service
      .actualizarSesion(845, { genero_interes: true, resultado_url: 'https://fashionstore.com/captura.jpg' })
      .subscribe((res) => {
        expect(res.genero_interes).toBe(true);
        expect(res.resultado_url).toBe('https://fashionstore.com/captura.jpg');
      });

    const req = httpMock.expectOne('/api/v1/vestidor/sesion/845');
    expect(req.request.method).toBe('PATCH');
    req.flush(respuestaMock);
  });
});
