import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { provideHttpClientTesting } from '@angular/common/http/testing';
import { provideRouter, Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { RecuperarPasswordComponent } from './recuperar-password.component';
import { RecuperarPasswordService } from '../servicios/recuperar-password.service';

describe('RecuperarPasswordComponent (CU33)', () => {
  let mockRecuperarService: any;
  let router: Router;

  beforeEach(async () => {
    mockRecuperarService = {
      solicitarCodigo: vi.fn().mockReturnValue(
        of({
          mensaje: 'Si el correo existe se envió el código.',
          tiempo_espera_segundos: 60,
        }),
      ),
      restablecerPassword: vi.fn().mockReturnValue(
        of({
          mensaje: 'Contraseña actualizada exitosamente.',
          exito: true,
          codigo_evento: 'PASSWORD_RESTABLECIDA',
        }),
      ),
    };

    await TestBed.configureTestingModule({
      imports: [RecuperarPasswordComponent],
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        provideRouter([]),
        { provide: RecuperarPasswordService, useValue: mockRecuperarService },
      ],
    }).compileComponents();

    router = TestBed.inject(Router);
    vi.spyOn(router, 'navigate').mockResolvedValue(true);
  });

  it('debe crearse e iniciar en paso solicitar', () => {
    const fixture = TestBed.createComponent(RecuperarPasswordComponent);
    const comp = fixture.componentInstance;
    expect(comp).toBeTruthy();
    expect(comp.pasoActual()).toBe('solicitar');
  });

  it('debe avanzar a paso restablecer tras solicitar código con email válido', () => {
    const fixture = TestBed.createComponent(RecuperarPasswordComponent);
    const comp = fixture.componentInstance;

    comp.formSolicitud.patchValue({ email: 'ana@fashionstore.com' });
    comp.onSolicitarCodigo();

    expect(mockRecuperarService.solicitarCodigo).toHaveBeenCalledWith(
      'ana@fashionstore.com',
    );
    expect(comp.pasoActual()).toBe('restablecer');
    expect(comp.formRestablecer.value.email).toBe('ana@fashionstore.com');
  });

  it('debe evaluar fortaleza de contraseña correctamente', () => {
    const fixture = TestBed.createComponent(RecuperarPasswordComponent);
    fixture.detectChanges();
    const comp = fixture.componentInstance;

    comp.formRestablecer.patchValue({ nueva_password: 'abc' });
    expect(comp.nivelFortaleza()).toBe(1);

    comp.formRestablecer.patchValue({ nueva_password: 'Password123' });
    expect(comp.nivelFortaleza()).toBe(2);

    comp.formRestablecer.patchValue({ nueva_password: 'Password123!' });
    expect(comp.nivelFortaleza()).toBe(3);
  });

  it('debe rechazar restablecimiento si las contraseñas no coinciden', () => {
    const fixture = TestBed.createComponent(RecuperarPasswordComponent);
    const comp = fixture.componentInstance;

    comp.formRestablecer.patchValue({
      email: 'ana@fashionstore.com',
      codigo: '849201',
      nueva_password: 'Password123',
      confirmar_password: 'Password999',
    });

    comp.onRestablecerPassword();
    expect(comp.mensajeError()).toBe('Las contraseñas no coinciden.');
    expect(mockRecuperarService.restablecerPassword).not.toHaveBeenCalled();
  });

  it('debe llamar a restablecerPassword cuando los datos son válidos', () => {
    const fixture = TestBed.createComponent(RecuperarPasswordComponent);
    const comp = fixture.componentInstance;

    comp.formRestablecer.patchValue({
      email: 'ana@fashionstore.com',
      codigo: '849 201',
      nueva_password: 'Password123',
      confirmar_password: 'Password123',
    });

    comp.onRestablecerPassword();
    expect(mockRecuperarService.restablecerPassword).toHaveBeenCalledWith({
      email: 'ana@fashionstore.com',
      codigo: '849201',
      nueva_password: 'Password123',
      confirmar_password: 'Password123',
    });
    expect(comp.mensajeExito()).toBe('Contraseña actualizada exitosamente.');
  });
});
