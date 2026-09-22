import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { InventarioGlobalAdminService } from './inventario-global-admin.service';
import {
  InventarioGlobalItem,
  RespuestaInventarioGlobal,
} from '../modelos/inventario-global.dto';

describe('InventarioGlobalAdminService', () => {
  let service: InventarioGlobalAdminService;
  let httpMock: HttpTestingController;

  const mockItem: InventarioGlobalItem = {
    id_variante: 101,
    id_producto: 10,
    nombre_producto: 'Vestido Gala Seda',
    sku: 'VES-GAL-S-NEG',
    categoria: 'Vestidos de Fiesta',
    talla: 'S',
    color: 'Negro',
    swatches_hex: '#000000',
    total_disponible: 12,
    total_reservado: 2,
    total_fisico: 14,
    estado_stock: 'optimo',
    desglose_sucursales: [
      {
        id_sucursal: 1,
        nombre_sucursal: 'Boutique Calacoto',
        ciudad: 'La Paz',
        direccion: 'Av. Ballivian #100',
        telefono: '2790001',
        cantidad_disponible: 12,
        cantidad_reservada: 2,
      },
    ],
  };

  const mockRespuesta: RespuestaInventarioGlobal = {
    items: [mockItem],
    metricas: {
      total_unidades_red: 12,
      variantes_monitoreadas: 1,
      alertas_stock_bajo: 0,
      sedes_activas: 1,
    },
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        InventarioGlobalAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(InventarioGlobalAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe instanciarse correctamente con estado reactivo inicial', () => {
    expect(service).toBeTruthy();
    expect(service.items()).toEqual([]);
    expect(service.totalRegistros()).toBe(0);
    expect(service.totalPaginas()).toBe(1);
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.modalDetalleAbierto()).toBe(false);
    expect(service.itemSeleccionadoDetalle()).toBeNull();
  });

  it('debe cargar el inventario global y actualizar los Signals correspondientes', () => {
    service.cargarInventario().subscribe((res) => {
      expect(res.total).toBe(1);
      expect(res.items.length).toBe(1);
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario/global');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('pagina')).toBe('1');
    expect(req.request.params.get('limite')).toBe('10');
    expect(req.request.params.get('ordenar_por')).toBe('nombre_asc');

    req.flush(mockRespuesta);

    expect(service.items().length).toBe(1);
    expect(service.items()[0].sku).toBe('VES-GAL-S-NEG');
    expect(service.metricas().total_unidades_red).toBe(12);
    expect(service.totalRegistros()).toBe(1);
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
  });

  it('debe enviar parametros de filtrado correctamente cuando estan activos', () => {
    service.filtros.set({
      q: 'Vestido',
      id_categoria: 5,
      id_sucursal: 2,
      estado_stock: 'optimo',
      ordenar_por: 'stock_desc',
      pagina: 2,
      limite: 20,
    });

    service.cargarInventario().subscribe();

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario/global');
    expect(req.request.params.get('q')).toBe('Vestido');
    expect(req.request.params.get('id_categoria')).toBe('5');
    expect(req.request.params.get('id_sucursal')).toBe('2');
    expect(req.request.params.get('estado_stock')).toBe('optimo');
    expect(req.request.params.get('ordenar_por')).toBe('stock_desc');
    expect(req.request.params.get('pagina')).toBe('2');
    expect(req.request.params.get('limite')).toBe('20');

    req.flush(mockRespuesta);
  });

  it('debe manejar errores HTTP y almacenar el mensaje en el Signal error', () => {
    service.cargarInventario().subscribe({
      next: () => {},
      error: (err) => {
        expect(err.status).toBe(500);
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario/global');
    req.flush(
      { detail: 'Fallo interno en motor analitico' },
      { status: 500, statusText: 'Internal Server Error' }
    );

    expect(service.cargando()).toBe(false);
    expect(service.error()).toBe('Fallo interno en motor analitico');
  });

  it('debe abrir y cerrar el modal de detalle logistico actualizando Signals', () => {
    service.abrirDetalle(mockItem);
    expect(service.modalDetalleAbierto()).toBe(true);
    expect(service.itemSeleccionadoDetalle()).toEqual(mockItem);

    service.cerrarDetalle();
    expect(service.modalDetalleAbierto()).toBe(false);
    expect(service.itemSeleccionadoDetalle()).toBeNull();
  });

  it('debe limpiar filtros y restablecer el estado inicial', () => {
    service.filtros.set({
      q: 'Seda',
      id_categoria: 3,
      id_sucursal: 1,
      estado_stock: 'alerta_baja',
      ordenar_por: 'stock_asc',
      pagina: 3,
      limite: 20,
    });

    service.limpiarFiltros();

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario/global');
    expect(req.request.params.get('q')).toBeNull();
    expect(req.request.params.get('pagina')).toBe('1');
    req.flush(mockRespuesta);

    expect(service.filtros().q).toBe('');
    expect(service.filtros().id_categoria).toBeNull();
    expect(service.filtros().estado_stock).toBe('todos');
  });
});
