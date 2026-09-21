import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach } from 'vitest';
import { AdminDashboardComponent } from './admin-dashboard.component';
import { LoginService } from '../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';

describe('AdminDashboardComponent', () => {
  let fixture: ComponentFixture<AdminDashboardComponent>;
  let component: AdminDashboardComponent;

  const mockAdmin: UsuarioSesion = {
    id_usuario: 99,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-valido',
  };

  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdmin);

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdmin);

    await TestBed.configureTestingModule({
      imports: [AdminDashboardComponent],
      providers: [
        provideRouter([]),
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(AdminDashboardComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente el dashboard', () => {
    expect(component).toBeTruthy();
    expect(component.usuarioEmail()).toBe('admin.director@fashionstore.com');
    expect(component.usuarioNombre()).toBe('Elena Montes');
    expect(component.esAdmin()).toBe(true);
  });

  it('debe renderizar el encabezado con el correo y rol del usuario activo', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Panel de Control Corporativo');
    expect(compiled.textContent).toContain('admin.director@fashionstore.com');
    expect(compiled.textContent).toContain('Administrador');
  });

  it('debe renderizar las seis tarjetas boutique para rol administrador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // Tarjeta 1 (CU21)
    expect(compiled.textContent).toContain('Gestionar sucursales y ciudades');
    // Tarjeta 2 (CU23)
    expect(compiled.textContent).toContain('Gestionar categorias, tallas y colores');
    // Tarjeta 3 (CU22)
    expect(compiled.textContent).toContain('Gestionar productos');
    // Tarjeta 4 (CU20)
    expect(compiled.textContent).toContain('Gestionar usuarios y roles');
    // Tarjeta 5 (CU24)
    expect(compiled.textContent).toContain('Inventario y Existencias');
    // Tarjeta 6 (CU25)
    expect(compiled.textContent).toContain('Gestionar proveedores');

    expect(component.totalModulosActivos()).toBe('6 Activos');
  });

  it('debe contener los enlaces de navegacion hacia /admin/sucursales, /admin/atributos, /admin/productos, /admin/usuarios, /admin/inventario y /admin/proveedores', () => {
    const links = fixture.debugElement.queryAll(By.directive(RouterLink));
    const hrefs = links.map((link) => link.injector.get(RouterLink).href);

    expect(hrefs).toContain('/admin/sucursales');
    expect(hrefs).toContain('/admin/atributos');
    expect(hrefs).toContain('/admin/productos');
    expect(hrefs).toContain('/admin/usuarios');
    expect(hrefs).toContain('/admin/inventario');
    expect(hrefs).toContain('/admin/proveedores');
    expect(hrefs).toContain('/admin');
  });

  it('debe localizar especificamente el boton GESTIONAR PRENDAS y verificar su enlace', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonPrendas = compiled.querySelector('#btn-gestionar-prendas') as HTMLAnchorElement;

    expect(botonPrendas).toBeTruthy();
    expect(botonPrendas.textContent?.toUpperCase()).toContain('GESTIONAR PRODUCTOS');
    expect(botonPrendas.getAttribute('routerLink')).toBe('/admin/productos');
  });

  it('debe localizar el boton GESTIONAR USUARIOS Y ROLES y verificar que apunte a /admin/usuarios', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonUsuarios = compiled.querySelector('#btn-gestionar-usuarios') as HTMLAnchorElement;

    expect(botonUsuarios).toBeTruthy();
    expect(botonUsuarios.textContent?.toUpperCase()).toContain('GESTIONAR USUARIOS Y ROLES');
    expect(botonUsuarios.getAttribute('routerLink')).toBe('/admin/usuarios');
  });

  it('debe localizar el boton GESTIONAR INVENTARIO y verificar que apunte a /admin/inventario', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonInventario = compiled.querySelector('#btn-gestionar-inventario') as HTMLAnchorElement;

    expect(botonInventario).toBeTruthy();
    expect(botonInventario.textContent?.toUpperCase()).toContain('GESTIONAR INVENTARIO');
    expect(botonInventario.getAttribute('routerLink')).toBe('/admin/inventario');
  });

  it('debe localizar el boton GESTIONAR PROVEEDORES y verificar que apunte a /admin/proveedores', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonProveedores = compiled.querySelector('#btn-gestionar-proveedores') as HTMLAnchorElement;

    expect(botonProveedores).toBeTruthy();
    expect(botonProveedores.textContent?.toUpperCase()).toContain('GESTIONAR PROVEEDORES');
    expect(botonProveedores.getAttribute('routerLink')).toBe('/admin/proveedores');
  });

  it('debe mantener activa la tarjeta y el boton GESTIONAR USUARIOS con rol ADMINISTRADOR en mayusculas', () => {
    const mockAdminUpper: UsuarioSesion = {
      id_usuario: 99,
      email: 'admin.director@fashionstore.com',
      nombres: 'Elena',
      apellidos: 'Montes',
      rol: 'ADMINISTRADOR',
      token: 'jwt-token-valido',
    };

    usuarioActualSignal.set(mockAdminUpper);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(true);

    const compiled = fixture.nativeElement as HTMLElement;
    const botonUsuarios = compiled.querySelector('#btn-gestionar-usuarios') as HTMLAnchorElement;

    expect(botonUsuarios).toBeTruthy();
    expect(botonUsuarios.getAttribute('routerLink')).toBe('/admin/usuarios');
  });

  it('debe aplicar segmentacion RBAC: si el rol es encargado_sucursal, mostrar Inventario y Proveedores y ocultar tarjetas de CU20 y CU21', () => {
    const mockEncargado: UsuarioSesion = {
      id_usuario: 50,
      email: 'encargado.central@fashionstore.com',
      nombres: 'Mario',
      apellidos: 'Suarez',
      rol: 'encargado_sucursal',
      token: 'jwt-encargado',
    };

    usuarioActualSignal.set(mockEncargado);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(true);
    expect(component.totalModulosActivos()).toBe('4 Activos');

    const compiled = fixture.nativeElement as HTMLElement;
    // Deben estar visibles
    expect(compiled.textContent).toContain('Gestionar categorias, tallas y colores');
    expect(compiled.textContent).toContain('Gestionar productos');
    expect(compiled.textContent).toContain('Inventario y Existencias');
    expect(compiled.textContent).toContain('Gestionar proveedores');

    // Deben estar estrictamente ocultos
    expect(compiled.textContent).not.toContain('Gestionar sucursales y ciudades');
    expect(compiled.textContent).not.toContain('Gestionar usuarios y roles');

    const botonUsuarios = compiled.querySelector('#btn-gestionar-usuarios');
    const botonSucursales = compiled.querySelector('#btn-gestionar-sucursales');
    const botonInventario = compiled.querySelector('#btn-gestionar-inventario');
    const botonProveedores = compiled.querySelector('#btn-gestionar-proveedores');
    expect(botonUsuarios).toBeNull();
    expect(botonSucursales).toBeNull();
    expect(botonInventario).toBeTruthy();
    expect(botonProveedores).toBeTruthy();
  });

  it('debe ocultar los botones GESTIONAR INVENTARIO y GESTIONAR PROVEEDORES si el rol es cajero o cliente', () => {
    const mockCajero: UsuarioSesion = {
      id_usuario: 12,
      email: 'cajero@fashionstore.com',
      nombres: 'Carlos',
      apellidos: 'Perez',
      rol: 'cajero',
      token: 'jwt-cajero',
    };

    usuarioActualSignal.set(mockCajero);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(false);

    const compiled = fixture.nativeElement as HTMLElement;
    const botonInventario = compiled.querySelector('#btn-gestionar-inventario');
    const botonProveedores = compiled.querySelector('#btn-gestionar-proveedores');
    expect(botonInventario).toBeNull();
    expect(botonProveedores).toBeNull();
  });
});
