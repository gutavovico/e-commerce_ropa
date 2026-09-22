import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { UsuariosAdminService } from './usuarios-admin.service';
import {
  ListaPaginadaUsuarios,
  UsuarioAdmin,
  UsuarioCrearPayload,
} from '../modelos/usuario.dto';

describe('UsuariosAdminService (CU20)', () => {
  let service: UsuariosAdminService;
  let httpTesting: HttpTestingController;

  const mockUsuario: UsuarioAdmin = {
    id_usuario: 1,
    email: 'admin@fashionstore.com',
    nombres: 'Gustavo',
    apellidos: 'Vico',
    nombre_completo: 'Gustavo Vico',
    telefono: '+591 70000001',
    rol: 'administrador',
    id_sucursal: null,
    sucursal_nombre: null,
    sucursal_ciudad: null,
    activo: true,
    fecha_registro: '2026-09-20T10:00:00Z',
    ultimo_acceso: null,
  };

  const mockLista: ListaPaginadaUsuarios = {
    items: [mockUsuario],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        UsuariosAdminService,
      ],
    });

    service = TestBed.inject(UsuariosAdminService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe crearse correctamente el servicio', () => {
    expect(service).toBeTruthy();
    expect(service.usuarios()).toEqual([]);
    expect(service.totalUsuarios()).toBe(0);
    expect(service.cargando()).toBe(false);
  });

  it('debe cargar usuarios con parametros de filtro y actualizar signals', () => {
    service
      .cargarUsuarios({ q: 'gustavo', rol: 'administrador', pagina: 1 })
      .subscribe((res) => {
        expect(res.items.length).toBe(1);
        expect(res.total).toBe(1);
      });

    const req = httpTesting.expectOne(
      (r) =>
        r.url === '/api/v1/admin/usuarios' &&
        r.params.get('q') === 'gustavo' &&
        r.params.get('rol') === 'administrador'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockLista);

    expect(service.usuarios()).toEqual(mockLista.items);
    expect(service.totalUsuarios()).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe crear un usuario exitosamente y emitir mensaje de exito', () => {
    const payload: UsuarioCrearPayload = {
      email: 'cajero@fashionstore.com',
      password: 'PasswordSeguro2026!',
      nombres: 'Lucia',
      apellidos: 'Roca',
      rol: 'cajero',
      id_sucursal: 2,
    };

    const usuarioCreado: UsuarioAdmin = {
      ...mockUsuario,
      id_usuario: 2,
      email: payload.email,
      nombres: payload.nombres,
      apellidos: payload.apellidos,
      nombre_completo: 'Lucia Roca',
      rol: 'cajero',
      id_sucursal: 2,
    };

    service.crearUsuario(payload).subscribe((res) => {
      expect(res.id_usuario).toBe(2);
      expect(res.rol).toBe('cajero');
    });

    const postReq = httpTesting.expectOne('/api/v1/admin/usuarios');
    expect(postReq.request.method).toBe('POST');
    postReq.flush(usuarioCreado);

    // Debe disparar la recarga automatica de lista
    const getReq = httpTesting.expectOne((r) => r.url === '/api/v1/admin/usuarios');
    getReq.flush(mockLista);

    expect(service.mensajeExito()).toContain('registrado exitosamente');
    expect(service.guardando()).toBe(false);
  });

  it('debe conmutar el estado de un usuario (activar/suspender)', () => {
    const usuarioSuspendido = { ...mockUsuario, activo: false };

    service.cambiarEstado(1, false).subscribe((res) => {
      expect(res.activo).toBe(false);
    });

    const patchReq = httpTesting.expectOne('/api/v1/admin/usuarios/1/estado');
    expect(patchReq.request.method).toBe('PATCH');
    patchReq.flush(usuarioSuspendido);

    const getReq = httpTesting.expectOne((r) => r.url === '/api/v1/admin/usuarios');
    getReq.flush(mockLista);

    expect(service.mensajeExito()).toContain('suspendida exitosamente');
  });

  it('debe restablecer contrasena de un usuario administrativamente', () => {
    service
      .resetPassword(1, { nuevo_password: 'NuevaPassword2026!' })
      .subscribe((res) => {
        expect(res.id_usuario).toBe(1);
      });

    const postReq = httpTesting.expectOne('/api/v1/admin/usuarios/1/reset-password');
    expect(postReq.request.method).toBe('POST');
    postReq.flush(mockUsuario);

    expect(service.mensajeExito()).toContain('restablecida exitosamente');
  });

  it('debe eliminar un usuario permanentemente', () => {
    service.eliminarUsuario(1).subscribe();

    const delReq = httpTesting.expectOne('/api/v1/admin/usuarios/1');
    expect(delReq.request.method).toBe('DELETE');
    delReq.flush(null, { status: 204, statusText: 'No Content' });

    const getReq = httpTesting.expectOne((r) => r.url === '/api/v1/admin/usuarios');
    getReq.flush(mockLista);

    expect(service.mensajeExito()).toContain('eliminado permanentemente');
  });

  it('debe capturar y mapear errores HTTP 409 y 422', () => {
    service.crearUsuario({} as UsuarioCrearPayload).subscribe({
      error: (err) => {
        expect(err.message).toBe('El correo ya existe');
      },
    });

    const postReq = httpTesting.expectOne('/api/v1/admin/usuarios');
    postReq.flush(
      { detail: 'El correo ya existe', code: 'EMAIL_DUPLICADO' },
      { status: 409, statusText: 'Conflict' }
    );

    expect(service.error()).toBe('El correo ya existe');
    expect(service.guardando()).toBe(false);
  });
});
