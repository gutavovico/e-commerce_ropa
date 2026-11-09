import { TenantService } from '../../../../core/tenant/tenant.service';
import { entrarEnTienda } from '../../../../core/tenant/tenant.testing';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { LoginComponent } from './login.component';
import { LoginService } from '../servicios/login.service';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LoginRespuesta } from '../modelos/login.dto';

describe('LoginComponent (CU02 - Iniciar Sesión)', () => {
  let component: LoginComponent;
  let fixture: ComponentFixture<LoginComponent>;
  let router: Router;

  const mockLoginRespuesta: LoginRespuesta = {
    access_token: 'fake-jwt-token-12345',
    token_type: 'bearer',
    id_usuario: 1,
    email: 'cliente@fashionstore.com',
    nombres: 'Ana',
    apellidos: 'Valenzuela',
    rol: 'cliente',
  };

  const mockLoginService = {
    usuarioActual: signal(null),
    iniciarSesion: vi.fn(),
  };

  beforeEach(async () => {
    mockLoginService.iniciarSesion.mockReset();

    await TestBed.configureTestingModule({
      imports: [LoginComponent],
      providers: [
        provideRouter([]),
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();
    entrarEnTienda(); // P2-CU02: dentro del portal de FASHION STORE

    fixture = TestBed.createComponent(LoginComponent);
    component = fixture.componentInstance;
    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
    fixture.detectChanges();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('debe crearse correctamente', () => {
    expect(component).toBeTruthy();
  });

  it('no debe enviar si el formulario es inválido', () => {
    component.onSubmit();
    expect(mockLoginService.iniciarSesion).not.toHaveBeenCalled();
    expect(component.mensajeError()).toContain('Por favor, ingresa tu correo electrónico');
  });

  it('P2-CU02: un cliente que entra por el portal va al inicio de esa tienda (no a /perfil)', () => {
    vi.useFakeTimers();
    mockLoginService.iniciarSesion.mockReturnValue(of(mockLoginRespuesta));

    component.formulario.setValue({
      email: 'cliente@fashionstore.com',
      password: 'Password123!',
      recordarDispositivo: true,
    });

    component.onSubmit();
    expect(component.cargando()).toBe(false);
    expect(component.exito()).toBe(true);

    // Avanzar el temporizador de 600ms para la redirección
    vi.advanceTimersByTime(600);

    expect(router.navigate).toHaveBeenCalledWith(['/', 'fashionstore', 'inicio']);
    expect(router.navigate).not.toHaveBeenCalledWith(['/perfil']);
  });

  it('P2-CU02: un cliente que entra por el login general va al directorio con sus tiendas', () => {
    vi.useFakeTimers();
    TestBed.inject(TenantService).tenantActual.set(null);
    mockLoginService.iniciarSesion.mockReturnValue(of(mockLoginRespuesta));
    component.formulario.setValue({ email: 'cliente@fashionstore.com', password: 'Password123!', recordarDispositivo: true });

    component.onSubmit();
    vi.advanceTimersByTime(600);

    expect(router.navigate).toHaveBeenCalledWith(['/']);
  });

  it('CU31-CU32: un cajero autenticado entra directo a su caja, no al panel corporativo', () => {
    vi.useFakeTimers();
    mockLoginService.iniciarSesion.mockReturnValue(
      of({ ...mockLoginRespuesta, email: 'cajero@fashionstore.com', rol: 'cajero' })
    );

    component.formulario.setValue({
      email: 'cajero@fashionstore.com',
      password: 'Password123!',
      recordarDispositivo: false,
    });
    component.onSubmit();
    vi.advanceTimersByTime(600);

    expect(router.navigate).toHaveBeenCalledWith(['/admin/pos']);
    expect(router.navigate).not.toHaveBeenCalledWith(['/admin']);
  });

  it('P2-CU05: un super_administrador autenticado entra directo a /admin/plataforma', () => {
    vi.useFakeTimers();
    mockLoginService.iniciarSesion.mockReturnValue(
      of({ ...mockLoginRespuesta, email: 'superadmin@fashionstore.com', rol: 'super_administrador' })
    );

    component.formulario.setValue({
      email: 'superadmin@fashionstore.com',
      password: 'Password123!',
      recordarDispositivo: false,
    });
    component.onSubmit();
    vi.advanceTimersByTime(600);

    expect(router.navigate).toHaveBeenCalledWith(['/admin/plataforma']);
  });

  it('debe mostrar mensaje de error si falla la autenticación', () => {
    mockLoginService.iniciarSesion.mockReturnValue(
      throwError(() => new Error('Correo electrónico o contraseña incorrectos.'))
    );

    component.formulario.setValue({
      email: 'cliente@fashionstore.com',
      password: 'PasswordErroneo!',
      recordarDispositivo: true,
    });

    component.onSubmit();
    expect(component.cargando()).toBe(false);
    expect(component.mensajeError()).toBe('Correo electrónico o contraseña incorrectos.');
  });
});
