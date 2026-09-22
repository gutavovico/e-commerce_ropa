import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

import { RegistroComponent } from './registro.component';
import { RegistroService } from '../servicios/registro.service';
import { LoginService } from '../../cu02_iniciar_sesion/servicios/login.service';
import { RegistroClienteRespuesta } from '../modelos/registro.dto';

describe('RegistroComponent (CU01)', () => {
  const mockRespuesta: RegistroClienteRespuesta = {
    id_usuario: 42,
    email: 'madame.dubois@fashionstore.com',
    nombres: 'Madame',
    apellidos: 'Dubois',
    rol: 'cliente',
    token_acceso: 'jwt.de.prueba',
    tipo_token: 'bearer',
  };

  let mockRegistroService: { registrar: ReturnType<typeof vi.fn> };

  beforeEach(async () => {
    localStorage.clear();
    sessionStorage.clear();
    vi.useFakeTimers();

    mockRegistroService = {
      registrar: vi.fn().mockReturnValue(of(mockRespuesta)),
    };

    await TestBed.configureTestingModule({
      imports: [RegistroComponent],
      providers: [
        provideRouter([]),
        { provide: RegistroService, useValue: mockRegistroService },
      ],
    }).compileComponents();
  });

  afterEach(() => {
    vi.useRealTimers();
    localStorage.clear();
    sessionStorage.clear();
  });

  function completarFormulario(comp: RegistroComponent): void {
    comp.formulario.setValue({
      nombreCompleto: 'Madame Dubois',
      email: 'madame.dubois@fashionstore.com',
      password: 'AltaCostura2026',
      terminosAceptados: true,
      notificaciones: true,
    });
  }

  it('debe dejar al usuario autenticado tras registrarse correctamente', () => {
    const fixture = TestBed.createComponent(RegistroComponent);
    const comp = fixture.componentInstance;
    const loginService = TestBed.inject(LoginService);
    fixture.detectChanges();

    completarFormulario(comp);
    comp.enviarRegistro();

    // El registro persistía la sesión con claves propias (`fs_token_acceso`), así que
    // `estaAutenticado()` seguía siendo false y el interceptor no adjuntaba el token.
    expect(loginService.estaAutenticado()).toBe(true);
    expect(loginService.obtenerToken()).toBe('jwt.de.prueba');
    expect(loginService.usuarioActual()?.email).toBe(
      'madame.dubois@fashionstore.com'
    );
  });

  it('debe persistir la sesión con las mismas claves que utiliza el login', () => {
    const fixture = TestBed.createComponent(RegistroComponent);
    const comp = fixture.componentInstance;
    fixture.detectChanges();

    completarFormulario(comp);
    comp.enviarRegistro();

    expect(localStorage.getItem('fashionstore_token')).toBe('jwt.de.prueba');
    expect(localStorage.getItem('fashionstore_user')).toContain(
      'madame.dubois@fashionstore.com'
    );
    // Las claves antiguas ya no deben escribirse.
    expect(localStorage.getItem('fs_token_acceso')).toBeNull();
    expect(localStorage.getItem('fs_usuario')).toBeNull();
  });
});
