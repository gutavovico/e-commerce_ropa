/**
 * Suite de Pruebas Unitarias para BitacoraAdminComponent (CU30: Consultar bitacora).
 * Nomenclatura oficial: "Consultar bitacora"
 */

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { of } from 'rxjs';
import { BitacoraAdminComponent } from './bitacora-admin.component';
import { BitacoraAdminService } from '../servicios/bitacora-admin.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  BitacoraEventoDetalle,
  BitacoraEventoResumen,
  BitacoraMetricas,
  BitacoraListadoRespuesta,
} from '../modelos/bitacora.dto';

describe('BitacoraAdminComponent', () => {
  let fixture: ComponentFixture<BitacoraAdminComponent>;
  let component: BitacoraAdminComponent;

  const mockAdmin: UsuarioSesion = {
    id_usuario: 1,
    email: 'admin.seguridad@fashionstore.com',
    nombres: 'Carlos',
    apellidos: 'Valdez',
    rol: 'administrador',
    token: 'jwt-token-admin',
  };

  const mockUsuarioActualSignal = signal<UsuarioSesion | null>(mockAdmin);

  const mockEventos: BitacoraEventoResumen[] = [
    {
      id_bitacora: 101,
      id_usuario: 1,
      usuario_nombre: 'Carlos Valdez',
      accion: 'MUTACION_PRECIO',
      tabla_modulo: 'productos',
      direccion_ip: '192.168.1.50',
      severidad: 'WARN',
      creado_en: '2026-09-22T08:30:00Z',
      tiene_payload: true,
    },
    {
      id_bitacora: 102,
      id_usuario: 2,
      usuario_nombre: 'Sistema Admin',
      accion: 'CREAR_USUARIO',
      tabla_modulo: 'usuarios',
      direccion_ip: '127.0.0.1',
      severidad: 'INFO',
      creado_en: '2026-09-22T08:35:00Z',
      tiene_payload: true,
    },
  ];

  const mockMetricas: BitacoraMetricas = {
    total_eventos: 25,
    eventos_criticos: 3,
    advertencias_errores: 7,
    usuarios_activos: 4,
  };

  const mockPaginaResponse: BitacoraListadoRespuesta = {
    items: mockEventos,
    total: 25,
    pagina: 1,
    limite: 20,
    total_paginas: 2,
    metricas: mockMetricas,
  };

  const mockDetalle: BitacoraEventoDetalle = {
    id_bitacora: 101,
    id_usuario: 1,
    usuario_nombre: 'Carlos Valdez',
    accion: 'MUTACION_PRECIO',
    tabla_modulo: 'productos',
    direccion_ip: '192.168.1.50',
    severidad: 'WARN',
    payload_anterior: { precio: 150.0 },
    payload_nuevo: { precio: 180.0 },
    creado_en: '2026-09-22T08:30:00Z',
    tiene_payload: true,
  };

  // Mock service signals
  const eventosSignal = signal<BitacoraEventoResumen[]>([]);
  const metricasSignal = signal<BitacoraMetricas>(mockMetricas);
  const totalEventosSignal = signal<number>(0);
  const totalPaginasSignal = signal<number>(1);
  const paginaActualSignal = signal<number>(1);
  const cargandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const eventoSeleccionadoSignal = signal<BitacoraEventoDetalle | null>(null);
  const cargandoDetalleSignal = signal<boolean>(false);
  const errorDetalleSignal = signal<string | null>(null);

  const mockBitacoraService = {
    eventos: eventosSignal.asReadonly(),
    metricas: metricasSignal.asReadonly(),
    totalEventos: totalEventosSignal.asReadonly(),
    totalPaginas: totalPaginasSignal.asReadonly(),
    paginaActual: paginaActualSignal,
    cargando: cargandoSignal.asReadonly(),
    error: errorSignal.asReadonly(),
    eventoSeleccionado: eventoSeleccionadoSignal.asReadonly(),
    cargandoDetalle: cargandoDetalleSignal.asReadonly(),
    errorDetalle: errorDetalleSignal.asReadonly(),
    listar: vi.fn().mockImplementation(() => {
      eventosSignal.set(mockEventos);
      metricasSignal.set(mockMetricas);
      totalEventosSignal.set(25);
      totalPaginasSignal.set(2);
      return of(mockPaginaResponse);
    }),
    obtenerDetalle: vi.fn().mockImplementation(() => {
      eventoSeleccionadoSignal.set(mockDetalle);
      return of(mockDetalle);
    }),
    cerrarModalDetalle: vi.fn().mockImplementation(() => {
      eventoSeleccionadoSignal.set(null);
    }),
  };

  const mockLoginService = {
    usuarioActual: mockUsuarioActualSignal.asReadonly(),
  };

  beforeEach(async () => {
    mockUsuarioActualSignal.set(mockAdmin);
    eventosSignal.set([]);
    metricasSignal.set(mockMetricas);
    totalEventosSignal.set(0);
    totalPaginasSignal.set(1);
    paginaActualSignal.set(1);
    cargandoSignal.set(false);
    errorSignal.set(null);
    eventoSeleccionadoSignal.set(null);
    cargandoDetalleSignal.set(false);
    errorDetalleSignal.set(null);
    vi.clearAllMocks();

    await TestBed.configureTestingModule({
      imports: [BitacoraAdminComponent],
      providers: [
        provideRouter([]),
        { provide: BitacoraAdminService, useValue: mockBitacoraService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(BitacoraAdminComponent);
    component = fixture.componentInstance;
  });

  it('debe instanciarse correctamente e inicializar datos en ngOnInit', () => {
    fixture.detectChanges();
    expect(component).toBeTruthy();
    expect(mockBitacoraService.listar).toHaveBeenCalledTimes(1);
    expect(component.esAdmin()).toBe(true);
  });

  it('debe detectar correctamente si el usuario no tiene permisos de administrador', () => {
    mockUsuarioActualSignal.set({
      id_usuario: 5,
      email: 'cajero@fashionstore.com',
      nombres: 'Cajero',
      apellidos: 'Uno',
      rol: 'cajero',
      token: 'jwt-token-cajero',
    });
    fixture.detectChanges();
    expect(component.esAdmin()).toBe(false);
  });

  it('debe disparar debounce y llamar a cargarDatos al buscar texto', () => {
    vi.useFakeTimers();
    fixture.detectChanges();
    expect(mockBitacoraService.listar).toHaveBeenCalledTimes(1);

    component.onFiltroTextoChange('MUTACION');
    expect(component.terminoBusqueda()).toBe('MUTACION');
    expect(mockBitacoraService.listar).toHaveBeenCalledTimes(1);

    vi.advanceTimersByTime(350);
    expect(mockBitacoraService.listar).toHaveBeenCalledTimes(2);
    vi.useRealTimers();
  });

  it('debe reiniciar pagina a 1 y recargar datos al cambiar un selector de filtro', () => {
    fixture.detectChanges();
    component.severidadSeleccionada.set('CRITICAL');
    component.onFiltroSelectChange();

    expect(component.paginaActual()).toBe(1);
    expect(mockBitacoraService.listar).toHaveBeenCalled();
  });

  it('debe limpiar todos los filtros correctamente', () => {
    fixture.detectChanges();
    component.fechaInicio.set('2026-09-01');
    component.fechaFin.set('2026-09-22');
    component.severidadSeleccionada.set('WARN');
    component.tablaModuloSeleccionada.set('usuarios');
    component.terminoBusqueda.set('admin');

    component.limpiarFiltros();

    expect(component.fechaInicio()).toBe('');
    expect(component.fechaFin()).toBe('');
    expect(component.severidadSeleccionada()).toBe('');
    expect(component.tablaModuloSeleccionada()).toBe('');
    expect(component.terminoBusqueda()).toBe('');
    expect(component.paginaActual()).toBe(1);
    expect(mockBitacoraService.listar).toHaveBeenCalled();
  });

  it('debe permitir cambiar de pagina si la pagina esta dentro del rango', () => {
    fixture.detectChanges();
    totalPaginasSignal.set(3);

    component.cambiarPagina(2);
    expect(mockBitacoraService.paginaActual()).toBe(2);

    // Fuera de rango no debe llamar
    vi.clearAllMocks();
    component.cambiarPagina(5);
    expect(mockBitacoraService.listar).not.toHaveBeenCalled();
  });

  it('debe abrir y cerrar modal de payload mediante el servicio', () => {
    fixture.detectChanges();

    component.abrirModalPayload(101);
    expect(mockBitacoraService.obtenerDetalle).toHaveBeenCalledWith(101);

    component.cerrarModalPayload();
    expect(mockBitacoraService.cerrarModalDetalle).toHaveBeenCalled();
  });

  it('debe asignar clases correctas segun severidad', () => {
    expect(component.getBadgeSeveridad('CRITICAL')).toContain('bg-red-100');
    expect(component.getBadgeSeveridad('ERROR')).toContain('bg-rose-50');
    expect(component.getBadgeSeveridad('WARN')).toContain('bg-amber-50');
    expect(component.getBadgeSeveridad('INFO')).toContain('bg-slate-100');
  });

  it('debe formatear JSON legiblemente o devolver mensaje por defecto', () => {
    expect(component.formatearJson(null)).toBe('Sin datos registrados.');
    expect(component.formatearJson({ precio: 100 })).toContain('"precio": 100');
  });

  it('debe renderizar la tabla con eventos y los KPIs en el DOM', () => {
    eventosSignal.set(mockEventos);
    metricasSignal.set(mockMetricas);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelector('#kpi-total-eventos')?.textContent).toContain('25');
    expect(compiled.querySelector('#kpi-eventos-criticos')?.textContent).toContain('3');
    expect(compiled.querySelector('#kpi-advertencias-errores')?.textContent).toContain('7');
    expect(compiled.querySelector('#kpi-usuarios-activos')?.textContent).toContain('4');

    const filas = compiled.querySelectorAll('#tabla-bitacora tbody tr');
    expect(filas.length).toBe(2);
    expect(filas[0].textContent).toContain('MUTACION_PRECIO');
    expect(filas[1].textContent).toContain('CREAR_USUARIO');
  });
});
