/**
 * Pruebas unitarias para IndicadoresAdminService (CU29).
 * Nomenclatura oficial: "Visualizar indicadores empresariales"
 */

import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { IndicadoresAdminService } from './indicadores-admin.service';
import {
  ComparativaSucursales,
  DashboardIndicadoresCompleto,
  DistribucionVentas,
  RankingProductos,
  ResumenEjecutivo,
  SerieTemporalIngresos,
  SucursalOpcion,
} from '../modelos/indicadores.dto';

describe('IndicadoresAdminService', () => {
  let service: IndicadoresAdminService;
  let httpMock: HttpTestingController;

  const mockResumen: ResumenEjecutivo = {
    periodo_inicio: '2026-09-01',
    periodo_fin: '2026-09-30',
    ingresos_totales: 45000.0,
    variacion_porcentual: 12.5,
    total_transacciones: 150,
    variacion_porcentual_transacciones: 8.0,
    margen_estimado: 42.5,
    ticket_promedio: 300.0,
    variacion_porcentual_ticket: 4.17,
    unidades_vendidas: 320,
    variacion_porcentual_unidades: 10.2,
  };

  const mockSerieTemporal: SerieTemporalIngresos = {
    agrupacion: 'diaria',
    puntos: [
      {
        etiqueta_tiempo: '2026-09-01',
        fecha_inicio: '2026-09-01',
        monto_ingresos: 1500.0,
        cantidad_ordenes: 5,
      },
    ],
  };

  const mockTopProductos: RankingProductos = {
    limite: 5,
    productos: [
      {
        id_producto: 10,
        nombre_producto: 'Vestido Seda Silk Noir',
        sku_referencia: 'VSN-S-BLK',
        categoria_nombre: 'Vestidos de Gala',
        unidades_vendidas: 25,
        monto_total_generado: 31250.0,
        porcentaje_contribucion: 69.44,
      },
    ],
  };

  const mockDistribucion: DistribucionVentas = {
    por_categoria: [
      {
        id_categoria: 1,
        nombre_categoria: 'Vestidos de Gala',
        monto_facturado: 31250.0,
        unidades_vendidas: 25,
        porcentaje_participacion: 69.44,
      },
    ],
    por_canal: [
      {
        canal_codigo: 'boutique_fisica',
        canal_nombre: 'Boutique Fisica',
        monto_facturado: 25000.0,
        total_ordenes: 80,
        porcentaje_participacion: 55.56,
      },
    ],
  };

  const mockComparativa: ComparativaSucursales = {
    sucursales: [
      {
        id_sucursal: 1,
        nombre_sucursal: 'Boutique Central',
        ciudad: 'La Paz',
        monto_facturado: 25000.0,
        total_ventas: 80,
        ticket_promedio: 312.5,
        porcentaje_red: 55.56,
      },
    ],
  };

  const mockDashboard: DashboardIndicadoresCompleto = {
    resumen: mockResumen,
    serie_temporal: mockSerieTemporal,
    top_productos: mockTopProductos,
    distribucion: mockDistribucion,
    comparativa_sucursales: mockComparativa,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        IndicadoresAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(IndicadoresAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe inicializarse con estado reactivo predeterminado', () => {
    expect(service).toBeTruthy();
    expect(service.dashboard()).toBeNull();
    expect(service.resumen()).toBeNull();
    expect(service.serieTemporal()).toBeNull();
    expect(service.topProductos()).toEqual([]);
    expect(service.distribucion()).toBeNull();
    expect(service.comparativa()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.filtros().periodo).toBe('30d');
  });

  it('debe consultar el dashboard consolidado y actualizar los signals', () => {
    service.consultarDashboardConsolidado().subscribe((res) => {
      expect(res.resumen.ingresos_totales).toBe(45000.0);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/dashboard');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('periodo')).toBe('30d');

    req.flush(mockDashboard);

    expect(service.dashboard()).toEqual(mockDashboard);
    expect(service.resumen()?.ingresos_totales).toBe(45000.0);
    expect(service.topProductos().length).toBe(1);
    expect(service.comparativa().length).toBe(1);
  });

  it('debe consultar el resumen ejecutivo individualmente', () => {
    service.consultarResumen({ periodo: '7d' }).subscribe((res) => {
      expect(res.total_transacciones).toBe(150);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/resumen');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('periodo')).toBe('7d');

    req.flush(mockResumen);

    expect(service.resumen()?.total_transacciones).toBe(150);
  });

  it('debe consultar la serie temporal individualmente', () => {
    service.consultarSerieTemporal({ periodo: '30d' }).subscribe((res) => {
      expect(res.puntos.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/serie-temporal');
    expect(req.request.method).toBe('GET');

    req.flush(mockSerieTemporal);

    expect(service.serieTemporal()?.puntos.length).toBe(1);
  });

  it('debe consultar el ranking de top productos con limite', () => {
    service.consultarTopProductos(10).subscribe((res) => {
      expect(res.productos.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/top-productos');
    expect(req.request.params.get('limite')).toBe('10');

    req.flush(mockTopProductos);

    expect(service.topProductos().length).toBe(1);
  });

  it('debe consultar la distribucion de ventas por categoria y canal', () => {
    service.consultarDistribucion().subscribe((res) => {
      expect(res.por_canal.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/distribucion');
    req.flush(mockDistribucion);

    expect(service.distribucion()?.por_canal.length).toBe(1);
  });

  it('debe consultar la comparativa entre sucursales para administradores', () => {
    service.consultarComparativaSucursales().subscribe((res) => {
      expect(res.sucursales.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/comparativa-sucursales');
    req.flush(mockComparativa);

    expect(service.comparativa().length).toBe(1);
  });

  it('debe capturar error HTTP 403 y actualizar el signal de error', () => {
    service.consultarComparativaSucursales().subscribe({
      error: (err) => {
        expect(err.message).toContain('No cuenta con privilegios autorizados');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/comparativa-sucursales');
    req.flush(null, { status: 403, statusText: 'Forbidden' });

    expect(service.error()).toContain('No cuenta con privilegios autorizados');
  });

  it('debe capturar error HTTP 422 de rango temporal invalido', () => {
    service.consultarResumen().subscribe({
      error: (err) => {
        expect(err.message).toContain('El rango temporal seleccionado');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/indicadores/resumen');
    req.flush(null, { status: 422, statusText: 'Unprocessable Content' });

    expect(service.error()).toContain('El rango temporal seleccionado');
  });

  it('debe cargar sucursales auxiliares', () => {
    const mockSucursales: SucursalOpcion[] = [
      { id_sucursal: 1, nombre: 'Boutique Central', ciudad: 'La Paz' },
    ];

    service.cargarSucursalesAuxiliares();

    const req = httpMock.expectOne('/api/v1/admin/sucursales');
    expect(req.request.method).toBe('GET');
    req.flush(mockSucursales);

    expect(service.sucursales().length).toBe(1);
  });
});
