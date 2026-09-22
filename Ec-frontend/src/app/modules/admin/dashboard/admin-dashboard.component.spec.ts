import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter, Router, RouterLink } from '@angular/router';
import { By } from '@angular/platform-browser';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach, vi } from 'vitest';
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

  it('debe renderizar las trece tarjetas boutique para rol administrador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // Tarjeta 1 (CU21)
    expect(compiled.textContent).toContain('Gestionar sucursales y ciudades');
    // Tarjeta 2 (CU23)
    expect(compiled.textContent).toContain('Gestionar categorias, tallas y colores');
    // Tarjeta 2b (CU24)
    expect(compiled.textContent).toContain('Gestionar temporadas y colecciones');
    // Tarjeta 3 (CU22)
    expect(compiled.textContent).toContain('Gestionar productos');
    // Tarjeta 4 (CU20)
    expect(compiled.textContent).toContain('Gestionar usuarios y roles');
    // Tarjeta 5 (CU24 inv)
    expect(compiled.textContent).toContain('Inventario y Existencias');
    // Tarjeta 6 (CU25)
    expect(compiled.textContent).toContain('Gestionar proveedores');
    // Tarjeta 7 (CU26)
    expect(compiled.textContent).toContain('Consultar inventario global');
    // Tarjeta 8 (CU27)
    expect(compiled.textContent).toContain('Gestionar promociones');
    // Tarjeta 9 (CU28)
    expect(compiled.textContent).toContain('Consultar ventas y reservas');
    // Tarjeta 10 (CU29)
    expect(compiled.textContent).toContain('Visualizar indicadores empresariales');
    // Tarjeta 12 (CU30)
    expect(compiled.textContent).toContain('Consultar bitacora');
    // Tarjeta 13 (CU31)
    expect(compiled.textContent).toContain('Generar reportes ejecutivos y consultas por voz');

    expect(component.totalModulosActivos()).toBe('13 Activos');
  });

  it('debe contener los enlaces de navegacion hacia /admin/sucursales, /admin/atributos, /admin/temporadas-colecciones, /admin/productos, /admin/usuarios, /admin/inventario, /admin/proveedores, /admin/inventario-global, /admin/promociones, /admin/ventas-reservas, /admin/indicadores, /admin/bitacora y /admin/reportes', () => {
    const links = fixture.debugElement.queryAll(By.directive(RouterLink));
    const hrefs = links.map((link) => link.injector.get(RouterLink).href);

    expect(hrefs).toContain('/admin/sucursales');
    expect(hrefs).toContain('/admin/atributos');
    expect(hrefs).toContain('/admin/temporadas-colecciones');
    expect(hrefs).toContain('/admin/productos');
    expect(hrefs).toContain('/admin/usuarios');
    expect(hrefs).toContain('/admin/inventario');
    expect(hrefs).toContain('/admin/proveedores');
    expect(hrefs).toContain('/admin/inventario-global');
    expect(hrefs).toContain('/admin/promociones');
    expect(hrefs).toContain('/admin/ventas-reservas');
    expect(hrefs).toContain('/admin/indicadores');
    expect(hrefs).toContain('/admin/bitacora');
    expect(hrefs).toContain('/admin/reportes');
    expect(hrefs).toContain('/admin');
  });

  it('debe localizar especificamente el boton GESTIONAR PROMOCIONES y verificar su enlace y navegacion', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonPromociones = compiled.querySelector('#btn-gestionar-promociones') as HTMLAnchorElement;

    expect(botonPromociones).toBeTruthy();
    expect(botonPromociones.textContent?.toUpperCase()).toContain('GESTIONAR PROMOCIONES');
    expect(botonPromociones.getAttribute('routerLink')).toBe('/admin/promociones');

    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/promociones', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/promociones');
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

  it('debe localizar el boton CONSULTAR INVENTARIO GLOBAL y verificar que apunte a /admin/inventario-global', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonInvGlobal = compiled.querySelector('#btn-consultar-inventario-global') as HTMLAnchorElement;

    expect(botonInvGlobal).toBeTruthy();
    expect(botonInvGlobal.textContent?.toUpperCase()).toContain('CONSULTAR INVENTARIO GLOBAL');
    expect(botonInvGlobal.getAttribute('routerLink')).toBe('/admin/inventario-global');
  });

  it('debe localizar el boton GESTIONAR TEMPORADAS Y COLECCIONES y verificar que apunte a /admin/temporadas-colecciones', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const boton = compiled.querySelector('#btn-gestionar-temporadas-colecciones') as HTMLAnchorElement;

    expect(boton).toBeTruthy();
    expect(boton.textContent?.toUpperCase()).toContain('GESTIONAR TEMPORADAS Y COLECCIONES');
    expect(boton.getAttribute('routerLink')).toBe('/admin/temporadas-colecciones');
  });

  it('debe invocar navigateByUrl hacia /admin/temporadas-colecciones al ejecutar navegar', () => {
    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/temporadas-colecciones', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/temporadas-colecciones');
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

  it('debe aplicar segmentacion RBAC: si el rol es encargado_sucursal, mostrar Temporadas, Inventario, Proveedores, Inventario Global, Promociones, Ventas/Reservas, Indicadores y Reportes/Voz y ocultar tarjetas de CU20, CU21 y CU30', () => {
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
    expect(component.totalModulosActivos()).toBe('10 Activos');

    const compiled = fixture.nativeElement as HTMLElement;
    // Deben estar visibles
    expect(compiled.textContent).toContain('Gestionar categorias, tallas y colores');
    expect(compiled.textContent).toContain('Gestionar temporadas y colecciones');
    expect(compiled.textContent).toContain('Gestionar productos');
    expect(compiled.textContent).toContain('Inventario y Existencias');
    expect(compiled.textContent).toContain('Gestionar proveedores');
    expect(compiled.textContent).toContain('Consultar inventario global');
    expect(compiled.textContent).toContain('Gestionar promociones');
    expect(compiled.textContent).toContain('Consultar ventas y reservas');
    expect(compiled.textContent).toContain('Visualizar indicadores empresariales');
    expect(compiled.textContent).toContain('Generar reportes ejecutivos y consultas por voz');

    // Deben estar estrictamente ocultos
    expect(compiled.textContent).not.toContain('Gestionar sucursales y ciudades');
    expect(compiled.textContent).not.toContain('Gestionar usuarios y roles');
    expect(compiled.textContent).not.toContain('Consultar bitacora');

    const botonUsuarios = compiled.querySelector('#btn-gestionar-usuarios');
    const botonSucursales = compiled.querySelector('#btn-gestionar-sucursales');
    const botonBitacora = compiled.querySelector('#btn-consultar-bitacora');
    const botonTempCol = compiled.querySelector('#btn-gestionar-temporadas-colecciones');
    const botonInventario = compiled.querySelector('#btn-gestionar-inventario');
    const botonProveedores = compiled.querySelector('#btn-gestionar-proveedores');
    const botonInvGlobal = compiled.querySelector('#btn-consultar-inventario-global');
    const botonPromociones = compiled.querySelector('#btn-gestionar-promociones');
    const botonVentasReservas = compiled.querySelector('#btn-consultar-ventas-reservas');
    const botonIndicadores = compiled.querySelector('#btn-visualizar-indicadores-empresariales');
    const botonReportesVoz = compiled.querySelector('#btn-reportes-voz');
    expect(botonUsuarios).toBeNull();
    expect(botonSucursales).toBeNull();
    expect(botonBitacora).toBeNull();
    expect(botonTempCol).toBeTruthy();
    expect(botonInventario).toBeTruthy();
    expect(botonProveedores).toBeTruthy();
    expect(botonInvGlobal).toBeTruthy();
    expect(botonPromociones).toBeTruthy();
    expect(botonVentasReservas).toBeTruthy();
    expect(botonIndicadores).toBeTruthy();
    expect(botonReportesVoz).toBeTruthy();
    expect(component.totalModulosActivos()).toBe('10 Activos');
  });

  it('debe ocultar los botones de administracion operativa si el rol es cajero o cliente', () => {
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
    const botonTempCol = compiled.querySelector('#btn-gestionar-temporadas-colecciones');
    const botonInventario = compiled.querySelector('#btn-gestionar-inventario');
    const botonProveedores = compiled.querySelector('#btn-gestionar-proveedores');
    const botonInvGlobal = compiled.querySelector('#btn-consultar-inventario-global');
    const botonPromociones = compiled.querySelector('#btn-gestionar-promociones');
    const botonVentasReservas = compiled.querySelector('#btn-consultar-ventas-reservas');
    const botonIndicadores = compiled.querySelector('#btn-visualizar-indicadores-empresariales');
    const botonBitacora = compiled.querySelector('#btn-consultar-bitacora');
    const botonReportesVoz = compiled.querySelector('#btn-reportes-voz');
    expect(botonTempCol).toBeNull();
    expect(botonInventario).toBeNull();
    expect(botonProveedores).toBeNull();
    expect(botonInvGlobal).toBeNull();
    expect(botonPromociones).toBeNull();
    expect(botonVentasReservas).toBeNull();
    expect(botonIndicadores).toBeNull();
    expect(botonBitacora).toBeNull();
    expect(botonReportesVoz).toBeNull();
  });

  it('debe reconocer rol admin como esAdmin=true y mostrar tarjeta Gestionar promociones', () => {
    const mockAdminAlias: UsuarioSesion = {
      id_usuario: 99,
      email: 'admin.alias@fashionstore.com',
      nombres: 'Super',
      apellidos: 'Admin',
      rol: 'admin',
      token: 'jwt-admin-alias',
    };

    usuarioActualSignal.set(mockAdminAlias);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(true);
    expect(component.rolLabel()).toBe('Administrador');

    const compiled = fixture.nativeElement as HTMLElement;
    const botonPromociones = compiled.querySelector('#btn-gestionar-promociones');
    expect(botonPromociones).toBeTruthy();
  });

  it('debe disparar navegar al hacer click en el enlace DOM de btn-gestionar-promociones', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonPromociones = compiled.querySelector('#btn-gestionar-promociones') as HTMLAnchorElement;
    expect(botonPromociones).toBeTruthy();

    const navegarSpy = vi.spyOn(component, 'navegar');
    botonPromociones.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

    expect(navegarSpy).toHaveBeenCalledWith('/admin/promociones', expect.any(MouseEvent));
  });

  it('debe localizar especificamente el boton CONSULTAR VENTAS Y RESERVAS y verificar su enlace y navegacion', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonVentasReservas = compiled.querySelector('#btn-consultar-ventas-reservas') as HTMLAnchorElement;

    expect(botonVentasReservas).toBeTruthy();
    expect(botonVentasReservas.textContent?.toUpperCase()).toContain('CONSULTAR VENTAS Y RESERVAS');
    expect(botonVentasReservas.getAttribute('routerLink')).toBe('/admin/ventas-reservas');

    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/ventas-reservas', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/ventas-reservas');
  });

  it('debe disparar navegar al hacer click en el enlace DOM de btn-consultar-ventas-reservas', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonVentasReservas = compiled.querySelector('#btn-consultar-ventas-reservas') as HTMLAnchorElement;
    expect(botonVentasReservas).toBeTruthy();

    const navegarSpy = vi.spyOn(component, 'navegar');
    botonVentasReservas.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

    expect(navegarSpy).toHaveBeenCalledWith('/admin/ventas-reservas', expect.any(MouseEvent));
  });

  it('debe localizar especificamente el boton VISUALIZAR INDICADORES EMPRESARIALES y verificar su enlace y navegacion', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonIndicadores = compiled.querySelector('#btn-visualizar-indicadores-empresariales') as HTMLAnchorElement;

    expect(botonIndicadores).toBeTruthy();
    expect(botonIndicadores.textContent?.toUpperCase()).toContain('VISUALIZAR INDICADORES EMPRESARIALES');
    expect(botonIndicadores.getAttribute('routerLink')).toBe('/admin/indicadores');

    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/indicadores', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/indicadores');
  });

  it('debe disparar navegar al hacer click en el enlace DOM de btn-visualizar-indicadores-empresariales', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonIndicadores = compiled.querySelector('#btn-visualizar-indicadores-empresariales') as HTMLAnchorElement;
    expect(botonIndicadores).toBeTruthy();

    const navegarSpy = vi.spyOn(component, 'navegar');
    botonIndicadores.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

    expect(navegarSpy).toHaveBeenCalledWith('/admin/indicadores', expect.any(MouseEvent));
  });

  it('debe registrar error y forzar navegacion con navigate([ruta]) si navigateByUrl resuelve false', async () => {
    const router = TestBed.inject(Router);
    vi.spyOn(router, 'navigateByUrl').mockResolvedValue(false as any);
    const navigateSpy = vi.spyOn(router, 'navigate').mockResolvedValue(true as any);
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    component.navegar('/admin/ventas-reservas');
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(errorSpy).toHaveBeenCalledWith(
      '[ROUTER] Navegacion rechazada o fallida hacia:',
      '/admin/ventas-reservas'
    );
    expect(navigateSpy).toHaveBeenCalledWith(['/admin/ventas-reservas']);
    errorSpy.mockRestore();
  });

  it('debe capturar y registrar excepcion en consola si navigateByUrl falla con error', async () => {
    const router = TestBed.inject(Router);
    const errorMock = new Error('Error al cargar modulo');
    vi.spyOn(router, 'navigateByUrl').mockRejectedValue(errorMock);
    const errorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});

    component.navegar('/admin/indicadores');
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(errorSpy).toHaveBeenCalledWith(
      '[ROUTER] Error al cargar modulo o resolver ruta:',
      errorMock
    );
    errorSpy.mockRestore();
  });

  it('debe localizar especificamente el boton CONSULTAR BITACORA y verificar su enlace y directiva dual', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonBitacora = compiled.querySelector('#btn-consultar-bitacora') as HTMLAnchorElement;

    expect(botonBitacora).toBeTruthy();
    expect(botonBitacora.textContent?.toUpperCase()).toContain('CONSULTAR BITACORA');
    expect(botonBitacora.getAttribute('routerLink')).toBe('/admin/bitacora');

    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/bitacora', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/bitacora');
  });

  it('debe despachar el evento click real en el DOM sobre #btn-consultar-bitacora y verificar que router.navigateByUrl se invoque con /admin/bitacora', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonBitacora = compiled.querySelector('#btn-consultar-bitacora') as HTMLAnchorElement;
    expect(botonBitacora).toBeTruthy();

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigateByUrl');
    const navegarSpy = vi.spyOn(component, 'navegar');

    botonBitacora.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

    expect(navegarSpy).toHaveBeenCalledWith('/admin/bitacora', expect.any(MouseEvent));
    expect(navigateSpy).toHaveBeenCalledWith('/admin/bitacora');
  });

  it('debe localizar especificamente el boton GENERAR REPORTES Y VOZ y verificar su enlace y directiva dual', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonReportes = compiled.querySelector('#btn-reportes-voz') as HTMLAnchorElement;

    expect(botonReportes).toBeTruthy();
    expect(botonReportes.textContent?.toUpperCase()).toContain('GENERAR REPORTES Y VOZ');
    expect(botonReportes.getAttribute('routerLink')).toBe('/admin/reportes');

    const router = TestBed.inject(Router);
    const spy = vi.spyOn(router, 'navigateByUrl');
    const mockEvent = new MouseEvent('click');
    const preventDefaultSpy = vi.spyOn(mockEvent, 'preventDefault');

    component.navegar('/admin/reportes', mockEvent);

    expect(preventDefaultSpy).toHaveBeenCalled();
    expect(spy).toHaveBeenCalledWith('/admin/reportes');
  });

  it('debe despachar el evento click real en el DOM sobre #btn-reportes-voz y verificar que router.navigateByUrl se invoque con /admin/reportes', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonReportes = compiled.querySelector('#btn-reportes-voz') as HTMLAnchorElement;
    expect(botonReportes).toBeTruthy();

    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigateByUrl');
    const navegarSpy = vi.spyOn(component, 'navegar');

    botonReportes.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));

    expect(navegarSpy).toHaveBeenCalledWith('/admin/reportes', expect.any(MouseEvent));
    expect(navigateSpy).toHaveBeenCalledWith('/admin/reportes');
  });
});
