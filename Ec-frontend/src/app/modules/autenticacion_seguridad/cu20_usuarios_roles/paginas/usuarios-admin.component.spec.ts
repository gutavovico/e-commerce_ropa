import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { UsuariosAdminComponent } from './usuarios-admin.component';
import { UsuariosAdminService } from '../servicios/usuarios-admin.service';
import { SucursalesAdminService } from '../../../gestion_operativa/cu21_sucursales_ciudades/servicios/sucursales-admin.service';
import {
  ListaPaginadaUsuarios,
  UsuarioAdmin,
} from '../modelos/usuario.dto';
import { SucursalAdmin } from '../../../gestion_operativa/cu21_sucursales_ciudades/modelos/sucursal.model';

describe('UsuariosAdminComponent (CU20)', () => {
  let fixture: ComponentFixture<UsuariosAdminComponent>;
  let component: UsuariosAdminComponent;

  const mockUsuarioAdmin: UsuarioAdmin = {
    id_usuario: 1,
    email: 'admin.corporativo@fashionstore.com',
    nombres: 'Gustavo',
    apellidos: 'Vico',
    nombre_completo: 'Gustavo Vico',
    telefono: '+591 70000001',
    rol: 'administrador',
    id_sucursal: null,
    sucursal_nombre: null,
    sucursal_ciudad: null,
    activo: true,
    fecha_registro: '2026-09-20T12:00:00Z',
    ultimo_acceso: null,
  };

  const mockUsuarioCajero: UsuarioAdmin = {
    id_usuario: 2,
    email: 'cajero.calacoto@fashionstore.com',
    nombres: 'Lucia',
    apellidos: 'Roca',
    nombre_completo: 'Lucia Roca',
    telefono: '+591 70000002',
    rol: 'cajero',
    id_sucursal: 10,
    sucursal_nombre: 'Boutique Calacoto Central',
    sucursal_ciudad: 'La Paz',
    activo: true,
    fecha_registro: '2026-09-21T09:00:00Z',
    ultimo_acceso: null,
  };

  const mockUsuariosSignal = signal<UsuarioAdmin[]>([
    mockUsuarioAdmin,
    mockUsuarioCajero,
  ]);
  const totalUsuariosSignal = signal<number>(2);
  const cargandoSignal = signal<boolean>(false);
  const guardandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const mensajeExitoSignal = signal<string | null>(null);

  const mockUsuariosService = {
    usuarios: mockUsuariosSignal,
    totalUsuarios: totalUsuariosSignal,
    cargando: cargandoSignal,
    guardando: guardandoSignal,
    error: errorSignal,
    mensajeExito: mensajeExitoSignal,
    cargarUsuarios: vi.fn().mockReturnValue(
      of({
        items: [mockUsuarioAdmin, mockUsuarioCajero],
        total: 2,
        pagina: 1,
        limite: 10,
        total_paginas: 1,
      } as ListaPaginadaUsuarios)
    ),
    crearUsuario: vi.fn().mockReturnValue(of(mockUsuarioCajero)),
    actualizarUsuario: vi.fn().mockReturnValue(of(mockUsuarioAdmin)),
    cambiarEstado: vi.fn().mockReturnValue(of({ ...mockUsuarioCajero, activo: false })),
    resetPassword: vi.fn().mockReturnValue(of(mockUsuarioCajero)),
    eliminarUsuario: vi.fn().mockReturnValue(of(void 0)),
    limpiarMensajes: vi.fn(),
  };

  const mockSucursal: SucursalAdmin = {
    id_sucursal: 10,
    nombre: 'Boutique Calacoto Central',
    id_ciudad: 1,
    ciudad_nombre: 'La Paz',
    direccion: 'Av. Ballivian #1234',
    telefono: '+591 2 2770000',
    horario_apertura: '09:00',
    horario_cierre: '20:00',
    activa: true,
    total_empleados: 5,
    total_prendas_stock: 120,
    reservas_activas_conteo: 2,
    creado_en: '2026-09-20T10:00:00Z',
  };

  const mockSucursalesSignal = signal<SucursalAdmin[]>([mockSucursal]);
  const mockSucursalesService = {
    sucursales: mockSucursalesSignal,
    cargarSucursales: vi.fn().mockReturnValue(of([mockSucursal])),
  };

  beforeEach(async () => {
    vi.clearAllMocks();
    mockUsuariosSignal.set([mockUsuarioAdmin, mockUsuarioCajero]);
    totalUsuariosSignal.set(2);
    cargandoSignal.set(false);
    guardandoSignal.set(false);
    errorSignal.set(null);
    mensajeExitoSignal.set(null);

    await TestBed.configureTestingModule({
      imports: [UsuariosAdminComponent],
      providers: [
        provideRouter([]),
        { provide: UsuariosAdminService, useValue: mockUsuariosService },
        { provide: SucursalesAdminService, useValue: mockSucursalesService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(UsuariosAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente el componente (AC-15)', () => {
    expect(component).toBeTruthy();
    expect(mockUsuariosService.cargarUsuarios).toHaveBeenCalled();
    expect(mockSucursalesService.cargarSucursales).toHaveBeenCalled();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Gestion de Usuarios y Roles');
    expect(compiled.textContent).toContain('Control de Acceso RBAC');
  });

  it('debe contener el enlace de retorno hacia /admin (AC-16)', () => {
    const returnLink = fixture.debugElement.query(By.css('#link-volver-dashboard'));
    expect(returnLink).toBeTruthy();
    expect(returnLink.injector.get(RouterLink).href).toBe('/admin');
  });

  it('debe renderizar la tabla con monogramas, badges de rol y datos de contacto (AC-17, AC-18)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // Usuario 1: Admin
    expect(compiled.textContent).toContain('Gustavo Vico');
    expect(compiled.textContent).toContain('admin.corporativo@fashionstore.com');
    expect(compiled.textContent).toContain('GV');
    expect(compiled.textContent).toContain('Administrador');
    expect(compiled.textContent).toContain('Sede Central / Global');

    // Usuario 2: Cajero
    expect(compiled.textContent).toContain('Lucia Roca');
    expect(compiled.textContent).toContain('cajero.calacoto@fashionstore.com');
    expect(compiled.textContent).toContain('LR');
    expect(compiled.textContent).toContain('Cajero');
    expect(compiled.textContent).toContain('Boutique Calacoto Central');
  });

  it('debe filtrar la lista de usuarios al ingresar texto de busqueda con debounce (AC-18)', async () => {
    const input = fixture.debugElement.query(By.css('#input-busqueda-usuario')).nativeElement as HTMLInputElement;
    input.value = 'Lucia';
    input.dispatchEvent(new Event('input'));
    fixture.detectChanges();

    expect(component.busquedaTexto()).toBe('Lucia');

    // Esperar que transcurra el debounce (300ms)
    await new Promise((r) => setTimeout(r, 350));
    expect(mockUsuariosService.cargarUsuarios).toHaveBeenCalledWith(
      expect.objectContaining({ q: 'Lucia' })
    );
  });

  it('debe abrir modal de nuevo usuario y condicionar aparicion de sucursal segun el rol (AC-19, AC-20)', () => {
    const botonNuevo = fixture.debugElement.query(By.css('#btn-nuevo-usuario')).nativeElement as HTMLButtonElement;
    botonNuevo.click();
    fixture.detectChanges();

    expect(component.modalUsuarioAbierto()).toBe(true);
    expect(component.modoEdicion()).toBe(false);

    // Por defecto es cliente -> sucursal oculta
    expect(component.esRolOperativo()).toBe(false);

    // Cambiar rol a 'encargado_sucursal' -> sucursal visible y requerida
    component.formUsuario.patchValue({ rol: 'encargado_sucursal' });
    fixture.detectChanges();

    expect(component.esRolOperativo()).toBe(true);
    expect(component.formUsuario.get('id_sucursal')?.hasValidator).toBeTruthy();

    // Cambiar rol a 'administrador' -> sucursal oculta y reseteada a null
    component.formUsuario.patchValue({ rol: 'administrador' });
    fixture.detectChanges();

    expect(component.esRolOperativo()).toBe(false);
    expect(component.formUsuario.get('id_sucursal')?.value).toBeNull();
  });

  it('debe enviar formulario de alta y cerrar modal ante creacion exitosa (AC-19)', () => {
    component.abrirModalCrear();
    fixture.detectChanges();

    component.formUsuario.patchValue({
      email: 'nuevo.cajero@fashionstore.com',
      password: 'PasswordSeguro2026!',
      nombres: 'Pedro',
      apellidos: 'Guzman',
      rol: 'cajero',
      id_sucursal: 10,
    });

    component.guardarUsuario();
    expect(mockUsuariosService.crearUsuario).toHaveBeenCalledWith({
      email: 'nuevo.cajero@fashionstore.com',
      password: 'PasswordSeguro2026!',
      nombres: 'Pedro',
      apellidos: 'Guzman',
      telefono: null,
      rol: 'cajero',
      id_sucursal: 10,
    });
    expect(component.modalUsuarioAbierto()).toBe(false);
  });

  it('debe capturar error HTTP 409 y mostrar Luxury Banner sin cerrar modal ni perder datos (AC-22)', () => {
    mockUsuariosService.crearUsuario.mockReturnValueOnce(
      throwError(() => new Error('El correo electronico ya se encuentra registrado.'))
    );

    component.abrirModalCrear();
    fixture.detectChanges();

    component.formUsuario.patchValue({
      email: 'duplicado@fashionstore.com',
      password: 'PasswordSeguro2026!',
      nombres: 'Ana',
      apellidos: 'Perez',
      rol: 'cliente',
    });

    component.guardarUsuario();
    fixture.detectChanges();

    expect(component.modalUsuarioAbierto()).toBe(true);
    expect(component.errorBanner()).toBe('El correo electronico ya se encuentra registrado.');
    expect(component.formUsuario.get('email')?.value).toBe('duplicado@fashionstore.com');
  });

  it('debe conmutar el estado activo/suspendido de un usuario (AC-21)', () => {
    component.conmutarEstado(mockUsuarioCajero);
    expect(mockUsuariosService.cambiarEstado).toHaveBeenCalledWith(2, false);
  });

  it('debe abrir modal de reseteo de contrasena y enviar nuevo password (AC-20)', () => {
    component.abrirModalReset(mockUsuarioCajero);
    fixture.detectChanges();

    expect(component.modalResetAbierto()).toBe(true);
    expect(component.usuarioResetId()).toBe(2);

    component.formReset.patchValue({ nuevo_password: 'NuevaPassword2026!' });
    component.guardarResetPassword();

    expect(mockUsuariosService.resetPassword).toHaveBeenCalledWith(2, {
      nuevo_password: 'NuevaPassword2026!',
    });
    expect(component.modalResetAbierto()).toBe(false);
  });

  it('debe abrir modal de eliminacion y confirmar baja (AC-21, AC-22)', () => {
    component.abrirModalEliminar(mockUsuarioCajero);
    fixture.detectChanges();

    expect(component.modalEliminarAbierto()).toBe(true);
    expect(component.usuarioEliminarId()).toBe(2);

    component.confirmarEliminacion();
    expect(mockUsuariosService.eliminarUsuario).toHaveBeenCalledWith(2);
    expect(component.modalEliminarAbierto()).toBe(false);
  });
});
