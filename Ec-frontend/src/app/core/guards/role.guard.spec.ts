import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach } from 'vitest';
import { adminOnlyGuard, roleGuard } from './role.guard';
import { LoginService } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../modules/autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';

describe('roleGuard', () => {
  let router: Router;
  const usuarioActualSignal = signal<UsuarioSesion | null>(null);

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        { provide: LoginService, useValue: mockLoginService },
        {
          provide: Router,
          useValue: {
            createUrlTree: (commands: string[]) => commands.join('/'),
          },
        },
      ],
    });

    router = TestBed.inject(Router);
  });

  it('debe redirigir a /login si no hay sesion activa', () => {
    usuarioActualSignal.set(null);
    const guard = roleGuard(['administrador']);
    const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any));

    expect(result).toBe('/login');
  });

  it('debe permitir acceso si el usuario posee uno de los roles permitidos', () => {
    usuarioActualSignal.set({
      id_usuario: 1,
      email: 'admin@fs.com',
      nombres: 'Admin',
      apellidos: 'Principal',
      rol: 'administrador',
      token: 'jwt',
    });

    const guard = roleGuard(['administrador']);
    const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any));

    expect(result).toBe(true);
  });

  it('debe redirigir a /admin si el usuario no cuenta con el rol requerido (ej: encargado_sucursal)', () => {
    usuarioActualSignal.set({
      id_usuario: 2,
      email: 'encargado@fs.com',
      nombres: 'Encargado',
      apellidos: 'Sede',
      rol: 'encargado_sucursal',
      token: 'jwt',
    });

    const guard = roleGuard(['administrador']);
    const result = TestBed.runInInjectionContext(() => guard({} as any, {} as any));

    expect(result).toBe('/admin');
  });

  it('debe validar adminOnlyGuard con exito para rol administrador', () => {
    usuarioActualSignal.set({
      id_usuario: 1,
      email: 'admin@fs.com',
      nombres: 'Admin',
      apellidos: 'Principal',
      rol: 'administrador',
      token: 'jwt',
    });

    const result = TestBed.runInInjectionContext(() =>
      adminOnlyGuard({} as any, {} as any)
    );
    expect(result).toBe(true);
  });

  it('debe conceder acceso tanto con administrador como con ADMINISTRADOR', () => {
    // Rol en minusculas
    usuarioActualSignal.set({
      id_usuario: 1,
      email: 'admin@fs.com',
      nombres: 'Admin',
      apellidos: 'Principal',
      rol: 'administrador',
      token: 'jwt',
    });
    expect(
      TestBed.runInInjectionContext(() => adminOnlyGuard({} as any, {} as any))
    ).toBe(true);

    // Rol en mayusculas
    usuarioActualSignal.set({
      id_usuario: 1,
      email: 'admin@fs.com',
      nombres: 'Admin',
      apellidos: 'Principal',
      rol: 'ADMINISTRADOR',
      token: 'jwt',
    });
    expect(
      TestBed.runInInjectionContext(() => adminOnlyGuard({} as any, {} as any))
    ).toBe(true);

    const guard = roleGuard(['administrador']);
    expect(
      TestBed.runInInjectionContext(() => guard({} as any, {} as any))
    ).toBe(true);
  });
});
