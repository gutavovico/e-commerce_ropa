/**
 * Pruebas unitarias para ReportesAdminService [CU31].
 */

import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { ReportesAdminService } from './reportes-admin.service';
import {
  ComandoVozIn,
  ComandoVozOut,
  ReporteFiltros,
  ReportePrevisualizacion,
} from '../modelos/reportes-voz.dto';

describe('ReportesAdminService', () => {
  let service: ReportesAdminService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        ReportesAdminService,
      ],
    });

    service = TestBed.inject(ReportesAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
    vi.restoreAllMocks();
  });

  it('debe crearse con senales reactivas y valores por defecto', () => {
    expect(service).toBeTruthy();
    expect(service.filtros().modulo).toBe('ventas');
    expect(service.filtros().formato).toBe('excel');
    expect(service.filtros().periodo).toBe('este_mes');
    expect(service.generando()).toBe(false);
    expect(service.previsualizando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.previsualizacion()).toBeNull();
  });

  it('debe interpretar comando de voz y sincronizar filtros reactivos', () => {
    const peticion: ComandoVozIn = {
      texto_dictado: 'exportar inventario de santa cruz en pdf',
    };

    const respuestaMock: ComandoVozOut = {
      texto_dictado: 'exportar inventario de santa cruz en pdf',
      intencion: 'exportar',
      modulo: 'inventario',
      formato: 'pdf',
      periodo: 'este_mes',
      id_sucursal: 2,
      nombre_sucursal: 'Santa Cruz Equipetrol',
      fecha_inicio: null,
      fecha_fin: null,
      confianza: 0.95,
      accion_recomendada: 'ejecutar_exportacion',
    };

    service.interpretarComandoVoz(peticion).subscribe((res) => {
      expect(res).toEqual(respuestaMock);
    });

    const req = httpMock.expectOne('/api/v1/admin/reportes/interpretar-voz');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(peticion);
    req.flush(respuestaMock);

    expect(service.comandoVozActivo()).toEqual(respuestaMock);
    expect(service.filtros().modulo).toBe('inventario');
    expect(service.filtros().formato).toBe('pdf');
    expect(service.filtros().id_sucursal).toBe(2);
  });

  it('debe solicitar previsualizacion y actualizar la senal previsualizacion', () => {
    const filtros: ReporteFiltros = {
      modulo: 'ventas',
      formato: 'excel',
      periodo: 'hoy',
      id_sucursal: null,
    };

    const mockPrev: ReportePrevisualizacion = {
      modulo: 'ventas',
      formato: 'excel',
      total_registros: 42,
      fecha_corte: '2026-09-22T04:00:00Z',
      nombre_archivo_sugerido: 'reporte_ventas_hoy.xlsx',
      resumen_financiero: {
        total_ingresos: 12500.5,
        promedio_ticket: 297.63,
      },
    };

    service.cargarPrevisualizacion(filtros).subscribe((res) => {
      expect(res).toEqual(mockPrev);
    });

    const req = httpMock.expectOne('/api/v1/admin/reportes/previsualizar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(filtros);
    req.flush(mockPrev);

    expect(service.previsualizacion()).toEqual(mockPrev);
  });

  it('debe solicitar la exportacion binaria y disparar la descarga del Blob', () => {
    const descargarBlobSpy = vi.spyOn(service, 'descargarBlob').mockImplementation(() => {});

    const mockBlob = new Blob(['contenido binario simulado'], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    });

    service.exportarReporte().subscribe((res) => {
      expect(res.body).toBeTruthy();
    });

    const req = httpMock.expectOne('/api/v1/admin/reportes/exportar');
    expect(req.request.method).toBe('POST');
    req.flush(mockBlob, {
      headers: {
        'Content-Disposition': 'attachment; filename="reporte_ventas_test.xlsx"',
      },
    });

    expect(descargarBlobSpy).toHaveBeenCalledWith(
      expect.any(Blob),
      'reporte_ventas_test.xlsx'
    );
  });

  it('debe actualizar los filtros manualmente con actualizarFiltros', () => {
    service.actualizarFiltros({
      modulo: 'reservas',
      periodo: 'esta_semana',
    });

    expect(service.filtros().modulo).toBe('reservas');
    expect(service.filtros().periodo).toBe('esta_semana');
    expect(service.filtros().formato).toBe('excel');
  });

  it('debe limpiar el error activo con limpiarError', () => {
    service.limpiarError();
    expect(service.error()).toBeNull();
  });
});
