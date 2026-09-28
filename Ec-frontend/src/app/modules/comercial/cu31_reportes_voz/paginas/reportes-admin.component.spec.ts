/**
 * Pruebas unitarias para ReportesAdminComponent [CU31].
 */

import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of, throwError } from 'rxjs';
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { ReportesAdminComponent } from './reportes-admin.component';
import { ReportesAdminService } from '../servicios/reportes-admin.service';
import { VozReconocimientoService } from '../servicios/voz-reconocimiento.service';
import { LoginService } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/servicios/login.service';
import { UsuarioSesion } from '../../../autenticacion_seguridad/cu02_iniciar_sesion/modelos/login.dto';
import {
  ComandoVozOut,
  ReporteFiltros,
  ReportePrevisualizacion,
} from '../modelos/reportes-voz.dto';

describe('ReportesAdminComponent', () => {
  let fixture: ComponentFixture<ReportesAdminComponent>;
  let component: ReportesAdminComponent;

  const mockAdmin: UsuarioSesion = {
    id_usuario: 1,
    email: 'admin.director@fashionstore.com',
    nombres: 'Elena',
    apellidos: 'Montes',
    rol: 'administrador',
    token: 'jwt-token-valido',
  };

  const usuarioActualSignal = signal<UsuarioSesion | null>(mockAdmin);

  const filtrosSignal = signal<ReporteFiltros>({
    modulo: 'ventas',
    formato: 'excel',
    periodo: 'este_mes',
    id_sucursal: null,
  });

  const prevSignal = signal<ReportePrevisualizacion | null>({
    modulo: 'ventas',
    formato: 'excel',
    total_registros: 15,
    fecha_corte: '2026-09-22T00:00:00Z',
    nombre_archivo_sugerido: 'reporte_ventas_este_mes.xlsx',
    resumen_financiero: { total_ingresos: 4500.0 },
  });

  const generandoSignal = signal<boolean>(false);
  const previsualizandoSignal = signal<boolean>(false);
  const errorSignal = signal<string | null>(null);
  const comandoVozActivoSignal = signal<ComandoVozOut | null>(null);
  const sucursalesSignal = signal<any[]>([]);

  const mockReportesService = {
    filtros: filtrosSignal,
    previsualizacion: prevSignal,
    generando: generandoSignal,
    previsualizando: previsualizandoSignal,
    error: errorSignal,
    comandoVozActivo: comandoVozActivoSignal,
    sucursales: sucursalesSignal,
    cargarPrevisualizacion: vi.fn(() => of(prevSignal())),
    exportarReporte: vi.fn(() => of(new Blob(['mock']))),
    interpretarComandoVoz: vi.fn((inDto) =>
      of({
        texto_dictado: inDto.texto_dictado,
        intencion: 'exportar' as const,
        modulo: 'ventas' as const,
        formato: 'excel' as const,
        periodo: 'este_mes' as const,
        id_sucursal: null,
        confianza: 1.0,
        accion_recomendada: 'ejecutar_exportacion',
      })
    ),
    cargarSucursales: vi.fn(() => of([])),
    actualizarFiltros: vi.fn((parcial) => {
      filtrosSignal.update((f) => ({ ...f, ...parcial }));
    }),
    limpiarError: vi.fn(() => errorSignal.set(null)),
  };

  const escuchandoSignal = signal<boolean>(false);
  const transcripcionSignal = signal<string>('');
  const errorVozSignal = signal<string | null>(null);
  const soportaVozSignal = signal<boolean>(true);

  const mockVozService = {
    escuchando: escuchandoSignal,
    transcripcion: transcripcionSignal,
    errorVoz: errorVozSignal,
    soportaVoz: soportaVozSignal,
    iniciarEscucha: vi.fn(() => escuchandoSignal.set(true)),
    detenerEscucha: vi.fn(() => escuchandoSignal.set(false)),
    reiniciar: vi.fn(() => {
      transcripcionSignal.set('');
      errorVozSignal.set(null);
    }),
  };

  const mockLoginService = {
    usuarioActual: usuarioActualSignal,
  };

  beforeEach(async () => {
    usuarioActualSignal.set(mockAdmin);
    filtrosSignal.set({
      modulo: 'ventas',
      formato: 'excel',
      periodo: 'este_mes',
      id_sucursal: null,
    });
    escuchandoSignal.set(false);
    transcripcionSignal.set('');
    errorVozSignal.set(null);
    errorSignal.set(null);

    await TestBed.configureTestingModule({
      imports: [ReportesAdminComponent],
      providers: [
        provideRouter([]),
        { provide: ReportesAdminService, useValue: mockReportesService },
        { provide: VozReconocimientoService, useValue: mockVozService },
        { provide: LoginService, useValue: mockLoginService },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(ReportesAdminComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crearse e inicializarse correctamente', () => {
    expect(component).toBeTruthy();
    expect(component.esAdmin()).toBe(true);
    expect(mockReportesService.cargarPrevisualizacion).toHaveBeenCalled();
  });

  it('debe renderizar el titulo oficial h1 y las migas de pan institucionales', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const h1 = compiled.querySelector('h1');
    expect(h1?.textContent?.trim()).toBe('Generar reportes ejecutivos y consultas por voz');
    expect(compiled.textContent).toContain('GENERAR REPORTES EJECUTIVOS Y CONSULTAS POR VOZ');
  });

  it('debe alternar el estado del microfono de voz con toggleMicrofono', () => {
    component.toggleMicrofono();
    expect(mockVozService.iniciarEscucha).toHaveBeenCalled();

    escuchandoSignal.set(true);
    transcripcionSignal.set('exportar reporte en excel');
    component.toggleMicrofono();
    expect(mockVozService.detenerEscucha).toHaveBeenCalled();
    expect(component.textoComando()).toBe('exportar reporte en excel');
  });

  it('debe interpretar el comando de voz y sincronizar filtros con el backend', () => {
    component.interpretarComando('descargar inventario de santa cruz en pdf');

    expect(mockReportesService.interpretarComandoVoz).toHaveBeenCalledWith({
      texto_dictado: 'descargar inventario de santa cruz en pdf',
    });
    expect(mockReportesService.cargarPrevisualizacion).toHaveBeenCalled();
  });

  it('debe aplicar un ejemplo rapido de voz con usarEjemploVoz', () => {
    const spy = vi.spyOn(component, 'interpretarComando');
    component.usarEjemploVoz('Ventas este mes en Excel');

    expect(component.textoComando()).toBe('Ventas este mes en Excel');
    expect(spy).toHaveBeenCalledWith('Ventas este mes en Excel');
  });

  it('debe cambiar modulo, formato y periodo manualmente', () => {
    component.seleccionarModulo('reservas');
    expect(mockReportesService.actualizarFiltros).toHaveBeenCalledWith({ modulo: 'reservas' });

    component.seleccionarFormato('pdf');
    expect(mockReportesService.actualizarFiltros).toHaveBeenCalledWith({ formato: 'pdf' });

    component.seleccionarPeriodo('hoy');
    expect(mockReportesService.actualizarFiltros).toHaveBeenCalledWith({ periodo: 'hoy' });
  });

  it('debe bloquear la seleccion de bitacora para usuarios con rol encargado_sucursal', () => {
    const mockEncargado: UsuarioSesion = {
      id_usuario: 5,
      email: 'encargado@fashionstore.com',
      nombres: 'Carlos',
      apellidos: 'Vargas',
      rol: 'encargado_sucursal',
      token: 'jwt-encargado',
    };
    usuarioActualSignal.set(mockEncargado);
    fixture.detectChanges();

    expect(component.esAdmin()).toBe(false);
    expect(component.esEncargado()).toBe(true);

    mockReportesService.actualizarFiltros.mockClear();
    component.seleccionarModulo('bitacora');
    expect(mockReportesService.actualizarFiltros).not.toHaveBeenCalled();
  });

  it('debe ejecutar la descarga del reporte al pulsar el boton principal de exportacion', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    const botonDescargar = compiled.querySelector('#btn-descargar-reporte') as HTMLButtonElement;
    expect(botonDescargar).toBeTruthy();

    component.descargarReporte();
    expect(mockReportesService.exportarReporte).toHaveBeenCalled();
    expect(component.mensajeExito()).toContain('generado y descargado exitosamente');
  });
});
