import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { LoginService } from './login.service';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

describe('LoginService & Logout (CU03)', () => {
  let service: LoginService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        LoginService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(LoginService);
    httpMock = TestBed.inject(HttpTestingController);

    localStorage.clear();
    sessionStorage.clear();
  });

  afterEach(() => {
    httpMock.verify();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('debe inicializarse sin usuario autenticado', () => {
    expect(service.usuarioActual()).toBeNull();
    expect(service.estaAutenticado()).toBe(false);
  });

  it('debe purgar la sesión localmente y emitir null en usuarioActual', () => {
    localStorage.setItem('fashionstore_token', 'token_prueba');
    localStorage.setItem('fashionstore_user', JSON.stringify({ id_usuario: 1 }));

    service.purgarSesionLocal();

    expect(service.usuarioActual()).toBeNull();
    expect(service.estaAutenticado()).toBe(false);
    expect(localStorage.getItem('fashionstore_token')).toBeNull();
    expect(localStorage.getItem('fashionstore_user')).toBeNull();
  });

  it('debe enviar POST a /api/v1/autenticacion/logout y purgar la sesión en éxito', () => {
    localStorage.setItem('fashionstore_token', 'jwt_valido_123');

    service.cerrarSesion().subscribe();

    const req = httpMock.expectOne('/api/v1/autenticacion/logout');
    expect(req.request.method).toBe('POST');
    expect(req.request.headers.get('Authorization')).toBe('Bearer jwt_valido_123');

    req.flush({ mensaje: 'Sesión finalizada exitosamente.', revocado: true });

    expect(service.usuarioActual()).toBeNull();
    expect(localStorage.getItem('fashionstore_token')).toBeNull();
  });

  it('debe purgar la sesión localmente de forma resiliente incluso si el backend falla con 500', () => {
    localStorage.setItem('fashionstore_token', 'jwt_fallido');

    service.cerrarSesion().subscribe();

    const req = httpMock.expectOne('/api/v1/autenticacion/logout');
    req.flush('Error interno', { status: 500, statusText: 'Server Error' });

    expect(service.usuarioActual()).toBeNull();
    expect(localStorage.getItem('fashionstore_token')).toBeNull();
  });
});
