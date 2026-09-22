import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { VentasReservasAdminComponent } from './ventas-reservas-admin.component';
import { VentasReservasAdminService } from '../servicios/ventas-reservas-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  MetricasTransaccionales,
  RespuestaPaginadaTransacciones,
  TransaccionResumenItem,
  SucursalOpcion,
} from '../modelos/ventas-reservas.dto';
import { of } from 'rxjs';

describe('VentasReservasAdminComponent', () => {
  let fixture: ComponentFixture<VentasReservasAdminComponent>;
  let component: VentasReservasAdminComponent;

  const mockAdmin: UsuarioSesion = {
    id_usuario: 99,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-valido',
  };

  const mockMetricas: MetricasTransaccionales = {
    monto_total_facturado: 125000.50,
    total_ventas_concluidas: 48,
    reservas_activas: 12,
    ticket_promedio: 2604.18,
  };

  const mockTransacciones: TransaccionResumenItem[] = [
    {
      id_transaccion: 1,
      tipo_operacion: 'venta',
      codigo_comprobante: 'VNT-2026-00001',
      fecha: '2026-09-20T14:30:00Z',
      id_cliente: 10,
      nombre_cliente: 'Maria Garcia',
      email_cliente: 'maria.garcia@correo.com',
      telefono_cliente: '70012345',
      id_sucursal: 1,
      nombre_sucursal: 'Boutique Central',
      ciudad_sucursal: 'La Paz',
      canal: 'presencial',
      estado: 'pagada',
      total_monto: 4500.00,
      cantidad_items: 3,
    },
    {
      id_transaccion: 5,
      tipo_operacion: 'reserva',
      codigo_comprobante: 'RSV-2026-00005',
      fecha: '2026-09-21T10:00:00Z',
      id_cliente: 15,
      nombre_cliente: 'Carlos Lopez',
      email_cliente: 'carlos.lopez@correo.com',
      telefono_cliente: null,
      id_sucursal: 2,
      nombre_sucursal: 'Boutique Sur',
      ciudad_sucursal: 'Cochabamba',
      canal: 'web',
      estado: 'pendiente',
      total_monto: 0,
      cantidad_items: 2,
    },
  ];

  const mockSucursales: SucursalOpcion[] = [
    { id_sucursal: 1, nombre: 'Boutique Central', ciudad: 'La Paz' },
    { id_sucursal: 2, nombre: 'Boutique Sur', ciudad: 'Cochabamba' },
  ];

  const transaccionesSignal = signal<TransaccionResumenItem[]>(mockTransacciones);
  const metricasSignal = signal<MetricasTransaccionales>(mockMetricas);
  const totalTransaccionesSignal = signal<number>(2);
  const totalPaginasSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const sucursalesSignal = signal<SucursalOpcion[]>(mockSucursales);
  const filtrosSignal = signal<Record<string, unknown>>({});
  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdmin);

  const mockServicio = {
    transacciones: transaccionesSignal,
    metricas: metricasSignal,
    totalTransacciones: totalTransaccionesSignal,
    totalPaginas: totalPaginasSignal,
    cargando: cargandoSignal,
    error: errorSignal,
    sucursalesDisponibles: sucursalesSignal,
    filtros: filtrosSignal,
    listarTransacciones: vi.fn().mockReturnValue(of({
      items: mockTransacciones,
      metricas: mockMetricas,
      total: 2,
      pagina: 1,
      limite: 10,
      total_paginas: 1,
    } as RespuestaPaginadaTransacciones)),
    obtenerDetalleVenta: vi.fn().mockReturnValue(of({})),
    obtenerDetalleReserva: vi.fn().mockReturnValue(of({})),
    cargarSucursalesAuxiliares: vi.fn(),
    limpiarError: vi.fn(),
    actualizarFiltros: vi.fn(),
    resetearFiltros: vi.fn(),
    cambiarPagina: vi.fn(),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdmin);
    transaccionesSignal.set(mockTransacciones);
    metricasSignal.set(mockMetricas);
    totalTransaccionesSignal.set(2);
    totalPaginasSignal.set(1);
    cargandoSignal.set(false);
    errorSignal.set(null);
    sucursalesSignal.set(mockSucursales);

    vi.clearAllMocks();
    mockServicio.listarTransacciones.mockReturnValue(of({
      items: mockTransacciones,
      metricas: mockMetricas,
      total: 2,
      pagina: 1,
      limite: 10,
      total_paginas: 1,
    } as RespuestaPaginadaTransacciones));

    await TestBed.configureTestingModule({
      imports: [VentasReservasAdminComponent],
      providers: [
        provideRouter([]),
        { provide: VentasReservasAdminService, useValue: mockServicio },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(VentasReservasAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente el componente', () => {
    expect(component).toBeTruthy();
    expect(component.esAdmin()).toBe(true);
  });

  it('debe cargar transacciones al inicializarse (ngOnInit)', () => {
    expect(mockServicio.listarTransacciones).toHaveBeenCalled();
  });

  it('debe cargar sucursales auxiliares si el usuario es administrador', () => {
    expect(mockServicio.cargarSucursalesAuxiliares).toHaveBeenCalled();
  });

  it('debe renderizar el encabezado con titulo "Consultar ventas y reservas"', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Consultar ventas y reservas');
  });

  it('debe renderizar breadcrumbs institucionales con navegacion al panel principal', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('INICIO');
    expect(compiled.textContent).toContain('ADMINISTRACION');
    expect(compiled.textContent).toContain('CONSULTAR VENTAS Y RESERVAS');
  });

  // --- Tests de KPIs ---
  it('debe renderizar los 4 KPIs cuantitativos con datos de metricas', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const kpiMonto = compiled.querySelector('#kpi-monto-facturado');
    const kpiVentas = compiled.querySelector('#kpi-ventas-concluidas');
    const kpiReservas = compiled.querySelector('#kpi-reservas-activas');
    const kpiTicket = compiled.querySelector('#kpi-ticket-promedio');

    expect(kpiMonto).toBeTruthy();
    expect(kpiVentas).toBeTruthy();
    expect(kpiReservas).toBeTruthy();
    expect(kpiTicket).toBeTruthy();

    expect(kpiVentas!.textContent?.trim()).toContain('48');
    expect(kpiReservas!.textContent?.trim()).toContain('12');
  });

  // --- Tests de Filtros ---
  it('debe renderizar controles de filtrado (busqueda, tipo, estado, canal)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#filtro-busqueda')).toBeTruthy();
    expect(compiled.querySelector('#filtro-tipo-operacion')).toBeTruthy();
    expect(compiled.querySelector('#filtro-estado')).toBeTruthy();
    expect(compiled.querySelector('#filtro-canal')).toBeTruthy();
  });

  it('debe renderizar selector de sucursal para administrador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const selectSucursal = compiled.querySelector('#filtro-sucursal');
    expect(selectSucursal).toBeTruthy();
  });

  it('debe ocultar selector de sucursal para encargado_sucursal', () => {
    const mockEncargado: UsuarioSesion = {
      id_usuario: 50,
      email: 'encargado@fashionstore.com',
      nombres: 'Mario',
      apellidos: 'Suarez',
      rol: 'encargado_sucursal',
      token: 'jwt-encargado',
    };
    usuarioActualSignal.set(mockEncargado);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(true);

    const compiled = fixture.nativeElement as HTMLElement;
    const selectSucursal = compiled.querySelector('#filtro-sucursal');
    expect(selectSucursal).toBeNull();
  });

  it('debe renderizar el boton de restablecer filtros', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const boton = compiled.querySelector('#btn-resetear-filtros');
    expect(boton).toBeTruthy();
    expect(boton!.textContent?.trim()).toContain('Restablecer filtros');
  });

  it('debe ejecutar busqueda con debounce al escribir en el campo de texto', () => {
    vi.useFakeTimers();
    const input = fixture.nativeElement.querySelector('#filtro-busqueda') as HTMLInputElement;
    expect(input).toBeTruthy();

    input.value = 'VNT-2026';
    input.dispatchEvent(new Event('input', { bubbles: true }));

    // Antes del debounce no debe haber llamado cargarDatos adicional
    const callCountAntes = mockServicio.listarTransacciones.mock.calls.length;

    vi.advanceTimersByTime(300);

    expect(mockServicio.listarTransacciones.mock.calls.length).toBeGreaterThan(callCountAntes);
    vi.useRealTimers();
  });

  // --- Tests de Tabla ---
  it('debe renderizar la tabla maestra con transacciones', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Registro de Transacciones');
    expect(compiled.textContent).toContain('2 registros');
    expect(compiled.textContent).toContain('VNT-2026-00001');
    expect(compiled.textContent).toContain('RSV-2026-00005');
    expect(compiled.textContent).toContain('Maria Garcia');
    expect(compiled.textContent).toContain('Carlos Lopez');
  });

  it('debe renderizar badges semanticos de tipo operacion (venta/reserva)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const badges = compiled.querySelectorAll('span');
    const tipoTextos = Array.from(badges).map(b => b.textContent?.trim().toLowerCase());
    expect(tipoTextos).toContain('venta');
    expect(tipoTextos).toContain('reserva');
  });

  it('debe renderizar badges semanticos de estado', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Pagada');
    expect(compiled.textContent).toContain('Pendiente');
  });

  it('debe mostrar mensaje de tabla vacia cuando no hay transacciones', () => {
    transaccionesSignal.set([]);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('No se encontraron transacciones');
  });

  // --- Tests de Modal ---
  it('debe abrir el modal al hacer click en boton Detalle de una venta', () => {
    expect(component.modalDetalleAbierto()).toBe(false);

    component.verDetalle(mockTransacciones[0]);

    expect(mockServicio.obtenerDetalleVenta).toHaveBeenCalledWith(1);
  });

  it('debe abrir el modal al hacer click en boton Detalle de una reserva', () => {
    expect(component.modalDetalleAbierto()).toBe(false);

    component.verDetalle(mockTransacciones[1]);

    expect(mockServicio.obtenerDetalleReserva).toHaveBeenCalledWith(5);
  });

  it('debe cerrar el modal al llamar cerrarModal', () => {
    component.modalDetalleAbierto.set(true);
    component.cerrarModal();

    expect(component.modalDetalleAbierto()).toBe(false);
    expect(component.detalleVenta()).toBeNull();
    expect(component.detalleReserva()).toBeNull();
  });

  it('debe cerrar el modal al presionar Escape', () => {
    component.modalDetalleAbierto.set(true);
    const event = new KeyboardEvent('keydown', { key: 'Escape' });
    component.onKeydown(event);

    expect(component.modalDetalleAbierto()).toBe(false);
  });

  it('debe cerrar el modal al hacer click en el overlay', () => {
    component.modalDetalleAbierto.set(true);
    const overlayElement = document.createElement('div');
    overlayElement.classList.add('modal-overlay');
    const event = new MouseEvent('click', { bubbles: true });
    Object.defineProperty(event, 'target', { value: overlayElement });

    component.onOverlayClick(event);

    expect(component.modalDetalleAbierto()).toBe(false);
  });

  // --- Tests de Formateo ---
  it('debe formatear montos correctamente en formato BOB', () => {
    const formateado = component.formatearMonto(1500.50);
    expect(formateado).toContain('1');
    expect(formateado).toContain('500');
  });

  it('debe formatear estados reemplazando guiones bajos por espacios', () => {
    expect(component.formatearEstado('en_atencion')).toBe('En Atencion');
    expect(component.formatearEstado('pagada')).toBe('Pagada');
  });

  it('debe retornar clases CSS semanticas para badges de estado', () => {
    expect(component.badgeClaseEstado('pagada')).toContain('emerald');
    expect(component.badgeClaseEstado('pendiente')).toContain('amber');
    expect(component.badgeClaseEstado('anulada')).toContain('rose');
    expect(component.badgeClaseEstado('en_atencion')).toContain('blue');
  });

  it('debe retornar clases CSS semanticas para badges de tipo', () => {
    expect(component.badgeClaseTipo('venta')).toContain('indigo');
    expect(component.badgeClaseTipo('reserva')).toContain('violet');
  });

  // --- Tests de Paginacion ---
  it('debe cambiar de pagina correctamente', () => {
    totalPaginasSignal.set(3);
    fixture.detectChanges();

    component.cambiarPagina(2);
    expect(component.paginaActual()).toBe(2);
  });

  it('no debe cambiar a pagina menor que 1', () => {
    component.paginaActual.set(1);
    component.cambiarPagina(0);
    expect(component.paginaActual()).toBe(1);
  });

  it('no debe cambiar a pagina mayor que el total', () => {
    totalPaginasSignal.set(3);
    component.paginaActual.set(3);
    component.cambiarPagina(4);
    expect(component.paginaActual()).toBe(3);
  });

  // --- Tests de Banners ---
  it('debe mostrar banner de error cuando hay un error', () => {
    errorSignal.set('Error de prueba');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Error de prueba');
  });

  it('debe limpiar banners al llamar limpiarBanners', () => {
    component.errorBanner.set('Error temporal');
    component.limpiarBanners();
    expect(component.errorBanner()).toBeNull();
  });

  // --- Tests de Reseteo de Filtros ---
  it('debe resetear todos los filtros a sus valores por defecto', () => {
    component.busquedaTexto.set('test');
    component.filtroTipoOperacion.set('venta');
    component.filtroEstado.set('pagada');

    component.resetearFiltros();

    expect(component.busquedaTexto()).toBe('');
    expect(component.filtroTipoOperacion()).toBe('todas');
    expect(component.filtroEstado()).toBe('todos');
    expect(component.paginaActual()).toBe(1);
  });

  // --- Test de Indicador de Carga ---
  it('debe renderizar indicador de carga cuando cargando es true', () => {
    cargandoSignal.set(true);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Cargando transacciones...');
  });

  // --- Test del boton Volver ---
  it('debe renderizar el boton Volver al Panel Principal con enlace a /admin', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonVolver = compiled.querySelector('#btn-volver-dashboard-ventas-reservas') as HTMLAnchorElement;
    expect(botonVolver).toBeTruthy();
    expect(botonVolver.textContent?.trim()).toContain('Volver al Panel Principal');
    expect(botonVolver.getAttribute('routerLink')).toBe('/admin');
  });
});
