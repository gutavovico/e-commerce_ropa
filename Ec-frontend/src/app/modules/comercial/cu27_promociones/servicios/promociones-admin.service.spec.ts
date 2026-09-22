/**
 * Pruebas unitarias para PromocionesAdminService (CU27).
 * Nomenclatura oficial: "Gestionar promociones"
 */

import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { PromocionesAdminService } from './promociones-admin.service';
import {
  MetricasPromociones,
  PromocionCrearDto,
  PromocionItem,
  RespuestaPaginadaPromociones,
} from '../modelos/promociones.dto';

describe('PromocionesAdminService', () => {
  let service: PromocionesAdminService;
  let httpMock: HttpTestingController;

  const mockMetricas: MetricasPromociones = {
    promociones_activas: 4,
    cupones_vigentes: 3,
    descuento_promedio: 18.5,
    usos_totales: 85,
  };

  const mockPromocion: PromocionItem = {
    id_promocion: 1,
    nombre: 'Black Velvet VIP',
    descripcion: 'Campana exclusiva de temporada',
    codigo_cupon: 'VELVET25',
    tipo_descuento: 'porcentaje',
    valor_descuento: 25.0,
    fecha_inicio: '2026-10-01T00:00:00',
    fecha_fin: '2026-10-31T23:59:59',
    tope_descuento: 150.0,
    limite_usos: 200,
    usos_actuales: 45,
    alcance: 'global',
    id_categoria: null,
    id_producto: null,
    estado_activo: true,
    creado_en: '2026-09-21T12:00:00Z',
    actualizado_en: '2026-09-21T12:00:00Z',
  };

  const mockRespuestaPaginada: RespuestaPaginadaPromociones = {
    items: [mockPromocion],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
    metricas: mockMetricas,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        PromocionesAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(PromocionesAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe inicializarse con estado reactivo limpio y predeterminado', () => {
    expect(service).toBeTruthy();
    expect(service.promociones()).toEqual([]);
    expect(service.metricas()).toBeNull();
    expect(service.cargando()).toBe(false);
    expect(service.guardando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
    expect(service.totalPromociones()).toBe(0);
  });

  it('debe listar promociones con parametros y actualizar signals reactivos', () => {
    service.listarPromociones().subscribe((res) => {
      expect(res.items.length).toBe(1);
      expect(res.items[0].nombre).toBe('Black Velvet VIP');
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('pagina')).toBe('1');
    expect(req.request.params.get('limite')).toBe('10');

    req.flush(mockRespuestaPaginada);

    expect(service.promociones().length).toBe(1);
    expect(service.totalPromociones()).toBe(1);
    expect(service.metricas()?.promociones_activas).toBe(4);
    expect(service.metricas()?.cupones_vigentes).toBe(3);
  });

  it('debe obtener el detalle de una promocion por su ID', () => {
    service.obtenerPromocionPorId(1).subscribe((promo) => {
      expect(promo.id_promocion).toBe(1);
      expect(promo.codigo_cupon).toBe('VELVET25');
    });

    const req = httpMock.expectOne('/api/v1/admin/promociones/1');
    expect(req.request.method).toBe('GET');
    req.flush(mockPromocion);

    expect(service.promocionSeleccionada()?.id_promocion).toBe(1);
  });

  it('debe crear una promocion exitosamente y desencadenar mensaje de exito', () => {
    const payload: PromocionCrearDto = {
      nombre: 'Nueva Promo',
      tipo_descuento: 'porcentaje',
      valor_descuento: 20.0,
      fecha_inicio: '2026-11-01T00:00:00',
      fecha_fin: '2026-11-15T23:59:59',
      alcance: 'global',
      codigo_cupon: 'PROMO20',
    };

    service.crearPromocion(payload).subscribe((res) => {
      expect(res.nombre).toBe('Nueva Promo');
    });

    const req = httpMock.expectOne('/api/v1/admin/promociones');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);

    req.flush({ ...mockPromocion, nombre: 'Nueva Promo' });

    // Expect list refresh
    const refreshReq = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    refreshReq.flush(mockRespuestaPaginada);

    expect(service.mensajeExito()).toContain('creada satisfactoriamente');
  });

  it('debe actualizar una promocion existente', () => {
    service.actualizarPromocion(1, { valor_descuento: 30.0 }).subscribe((res) => {
      expect(res.valor_descuento).toBe(30.0);
    });

    const req = httpMock.expectOne('/api/v1/admin/promociones/1');
    expect(req.request.method).toBe('PUT');
    req.flush({ ...mockPromocion, valor_descuento: 30.0 });

    const refreshReq = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    refreshReq.flush(mockRespuestaPaginada);

    expect(service.mensajeExito()).toContain('actualizada con exito');
  });

  it('debe conmutar el estado logico (baja logica o reactivacion)', () => {
    service.conmutarEstado(1, false).subscribe((res) => {
      expect(res.estado_activo).toBe(false);
    });

    const req = httpMock.expectOne('/api/v1/admin/promociones/1/estado');
    expect(req.request.method).toBe('PATCH');
    expect(req.request.body).toEqual({ estado_activo: false });
    req.flush({ ...mockPromocion, estado_activo: false });

    const refreshReq = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    refreshReq.flush(mockRespuestaPaginada);

    expect(service.mensajeExito()).toContain('desactivada correctamente');
  });

  it('debe capturar colision de cupon duplicado HTTP 409', () => {
    const payload: PromocionCrearDto = {
      nombre: 'Promo Duplicada',
      tipo_descuento: 'monto_fijo',
      valor_descuento: 50.0,
      fecha_inicio: '2026-10-01T00:00:00',
      fecha_fin: '2026-10-31T23:59:59',
      alcance: 'global',
      codigo_cupon: 'VELVET25',
    };

    service.crearPromocion(payload).subscribe({
      error: (err) => {
        expect(err.message).toContain('Codigo de cupon duplicado');
      },
    });

    const req = httpMock.expectOne('/api/v1/admin/promociones');
    req.flush({ detail: 'Codigo de cupon duplicado' }, { status: 409, statusText: 'Conflict' });

    expect(service.error()).toContain('Codigo de cupon duplicado');
  });

  it('debe capturar error de validacion semantica HTTP 422', () => {
    service.listarPromociones().subscribe({
      error: (err) => {
        expect(err.message).toContain('La fecha de finalizacion debe ser posterior');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    req.flush(
      { detail: 'La fecha de finalizacion debe ser posterior' },
      { status: 422, statusText: 'Unprocessable Content' }
    );

    expect(service.error()).toContain('La fecha de finalizacion debe ser posterior');
  });

  it('debe resetear filtros reactivos a valores iniciales', () => {
    service.filtros.set({
      q: 'Busqueda previa',
      tipo_descuento: 'porcentaje',
      estado_activo: 'activas',
      alcance: 'categoria',
      pagina: 3,
      limite: 20,
      ordenar_por: 'nombre_asc',
    });

    service.resetearFiltros();

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/promociones');
    req.flush(mockRespuestaPaginada);

    expect(service.filtros().q).toBe('');
    expect(service.filtros().tipo_descuento).toBe('todos');
    expect(service.filtros().pagina).toBe(1);
  });
});
