import { ComponentFixture, TestBed } from '@angular/core/testing';
import { signal } from '@angular/core';
import { LoginComponent } from './login.component';
import { LoginService } from '../servicios/login.service';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { LoginRespuesta, UsuarioSesion } from '../modelos/login.dto';

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
    usuarioActual: signal<UsuarioSesion | null>(null),
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

  it('debe iniciar sesión exitosamente y REDIRIGIR a /inicio (no a /perfil)', () => {
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

    expect(router.navigate).toHaveBeenCalledWith(['/inicio']);
    expect(router.navigate).not.toHaveBeenCalledWith(['/perfil']);
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

  it('debe iniciar sesion exitosamente y REDIRIGIR a /caja/cobro si el rol es cajero', () => {
    vi.useFakeTimers();
    mockLoginService.iniciarSesion.mockReturnValue(
      of({
        ...mockLoginRespuesta,
        rol: 'cajero',
      })
    );

    component.formulario.setValue({
      email: 'cajero@fashionstore.com',
      password: 'Password123!',
      recordarDispositivo: true,
    });

    component.onSubmit();
    expect(component.cargando()).toBe(false);
    expect(component.exito()).toBe(true);

    vi.advanceTimersByTime(600);

    expect(router.navigate).toHaveBeenCalledWith(['/caja/cobro']);
  });

  it('debe redirigir directamente a /caja/cobro en ngOnInit si el usuario ya autenticado es cajero', () => {
    mockLoginService.usuarioActual.set({
      id_usuario: 5,
      email: 'cajero@fs.com',
      nombres: 'Cajero',
      apellidos: 'Boutique',
      rol: 'cajero',
      token: 'jwt_cajero',
    });

    component.ngOnInit();
    expect(router.navigate).toHaveBeenCalledWith(['/caja/cobro']);
  });
});
