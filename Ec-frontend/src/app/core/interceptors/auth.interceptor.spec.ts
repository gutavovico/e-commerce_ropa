import { TestBed } from '@angular/core/testing';
import { HttpClient, HttpErrorResponse, provideHttpClient, withInterceptors } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter } from '@angular/router';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { authInterceptor } from './auth.interceptor';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';

describe('authInterceptor', () => {
  let httpClient: HttpClient;
  let httpTestingController: HttpTestingController;
  let loginService: LoginService;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideRouter([]),
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    httpClient = TestBed.inject(HttpClient);
    httpTestingController = TestBed.inject(HttpTestingController);
    loginService = TestBed.inject(LoginService);
  });

  afterEach(() => {
    httpTestingController.verify();
    localStorage.clear();
    sessionStorage.clear();
  });

  it('debe adjuntar el header Authorization: Bearer <token> cuando existe token', () => {
    vi.spyOn(loginService, 'obtenerToken').mockReturnValue('mi_token_jwt_valido');

    httpClient.get('/api/v1/usuarios/perfil').subscribe();

    const req = httpTestingController.expectOne('/api/v1/usuarios/perfil');
    expect(req.request.headers.get('Authorization')).toBe('Bearer mi_token_jwt_valido');
    req.flush({});
  });

  it('debe purgar la sesión y redirigir cuando recibe un 401 de una ruta protegida', () => {
    const purgarSpy = vi.spyOn(loginService, 'purgarSesionLocal').mockImplementation(() => {});

    httpClient.get('/api/v1/usuarios/perfil').subscribe({
      error: (err: HttpErrorResponse) => {
        expect(err.status).toBe(401);
      },
    });

    const req = httpTestingController.expectOne('/api/v1/usuarios/perfil');
    req.flush('Token expirado', { status: 401, statusText: 'Unauthorized' });

    expect(purgarSpy).toHaveBeenCalledWith(true);
  });

  it('no debe purgar la sesión cuando el 401 proviene del endpoint de login (credenciales erróneas)', () => {
    const purgarSpy = vi.spyOn(loginService, 'purgarSesionLocal').mockImplementation(() => {});

    httpClient.post('/api/v1/autenticacion/login', {}).subscribe({
      error: (err: HttpErrorResponse) => {
        expect(err.status).toBe(401);
      },
    });

    const req = httpTestingController.expectOne('/api/v1/autenticacion/login');
    req.flush('Credenciales inválidas', { status: 401, statusText: 'Unauthorized' });

    expect(purgarSpy).not.toHaveBeenCalled();
  });
});
