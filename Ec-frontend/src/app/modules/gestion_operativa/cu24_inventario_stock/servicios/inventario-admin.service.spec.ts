import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { InventarioAdminService } from './inventario-admin.service';
import {
  ComprobanteTransferenciaOut,
  HistorialKardexOut,
  InventarioAjustePayload,
  InventarioCrearPayload,
  InventarioItemAdmin,
  ListaPaginadaInventario,
  TransferenciaPayload,
} from '../modelos/inventario.dto';

describe('InventarioAdminService', () => {
  let service: InventarioAdminService;
  let httpMock: HttpTestingController;

  const mockItem: InventarioItemAdmin = {
    id_inventario: 1,
    id_sucursal: 10,
    id_variante: 100,
    cantidad_disponible: 15,
    cantidad_reservada: 2,
    stock_total: 17,
    stock_minimo: 5,
    stock_alerta: 8,
    estado: 'disponible',
    estado_calculado: 'optimo',
    actualizado_en: '2026-09-21T10:00:00Z',
    sucursal: {
      id_sucursal: 10,
      nombre: 'Boutique Central',
      ciudad: 'La Paz',
    },
    variante: {
      id_variante: 100,
      id_producto: 50,
      nombre_prenda: 'Chaqueta Cuero Atelier',
      sku: 'BER-CHA-L-NEG',
      talla: 'L',
      color_nombre: 'Negro Obsidiana',
      color_hex: '#0F172A',
      precio_base: 150.0,
      precio_final: 160.0,
      imagen_url: null,
      categoria_nombre: 'Chaquetas',
    },
  };

  const mockLista: ListaPaginadaInventario = {
    items: [mockItem],
    total: 1,
    pagina: 1,
    limite: 20,
    total_paginas: 1,
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        InventarioAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(InventarioAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe instanciarse correctamente con estado inicial limpio', () => {
    expect(service).toBeTruthy();
    expect(service.inventario()).toEqual([]);
    expect(service.cargando()).toBe(false);
    expect(service.guardando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();
  });

  it('debe cargar inventario con query params y actualizar Signals reactivos', () => {
    service.cargarInventario({ id_sucursal: 10, estado_stock: 'optimo', q: 'Chaqueta' }).subscribe((res) => {
      expect(res.items.length).toBe(1);
      expect(res.total).toBe(1);
    });

    const req = httpMock.expectOne((r) =>
      r.url === '/api/v1/admin/inventario' &&
      r.params.get('id_sucursal') === '10' &&
      r.params.get('estado_stock') === 'optimo' &&
      r.params.get('q') === 'Chaqueta'
    );
    expect(req.request.method).toBe('GET');
    req.flush(mockLista);

    expect(service.inventario().length).toBe(1);
    expect(service.totalRegistros()).toBe(1);
    expect(service.cargando()).toBe(false);
  });

  it('debe registrar existencias iniciales y anadir el item al Signal reactivo', () => {
    const payload: InventarioCrearPayload = {
      id_sucursal: 10,
      id_variante: 100,
      cantidad_inicial: 15,
      stock_minimo: 5,
      stock_alerta: 8,
    };

    service.crearStockInicial(payload).subscribe((item) => {
      expect(item.id_inventario).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/admin/inventario');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(mockItem);

    expect(service.inventario().length).toBe(1);
    expect(service.guardando()).toBe(false);
    expect(service.mensajeExito()).toContain('registradas exitosamente');
  });

  it('debe aplicar ajuste manual fisico y actualizar el item en el Signal reactivo', () => {
    // Inicializar con el item previo
    service.inventario.set([mockItem]);

    const itemAjustado: InventarioItemAdmin = {
      ...mockItem,
      cantidad_disponible: 18,
      stock_total: 20,
    };

    const payload: InventarioAjustePayload = {
      tipo_ajuste: 'incremento',
      cantidad: 3,
      motivo: 'Auditoria fisica',
    };

    service.ajustarStock(1, payload).subscribe((item) => {
      expect(item.cantidad_disponible).toBe(18);
    });

    const req = httpMock.expectOne('/api/v1/admin/inventario/1/ajuste');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);
    req.flush(itemAjustado);

    expect(service.inventario()[0].cantidad_disponible).toBe(18);
    expect(service.mensajeExito()).toContain('aplicado');
  });

  it('debe procesar transferencia inter-sucursal y disparar recarga de inventario', () => {
    const payload: TransferenciaPayload = {
      id_sucursal_origen: 10,
      id_sucursal_destino: 20,
      id_variante: 100,
      cantidad: 5,
      motivo: 'Traspaso urgente',
    };

    const mockComprobante: ComprobanteTransferenciaOut = {
      mensaje: 'Transferencia inter-sucursal completada con exito.',
      id_sucursal_origen: 10,
      id_sucursal_destino: 20,
      id_variante: 100,
      sku: 'BER-CHA-L-NEG',
      cantidad_transferida: 5,
      saldo_origen_nuevo: 10,
      saldo_destino_nuevo: 15,
      fecha: '2026-09-21T10:30:00Z',
    };

    service.transferirMercaderia(payload).subscribe((res) => {
      expect(res.cantidad_transferida).toBe(5);
    });

    const reqPost = httpMock.expectOne('/api/v1/admin/inventario/transferencia');
    expect(reqPost.request.method).toBe('POST');
    reqPost.flush(mockComprobante);

    // La transferencia ejecuta cargarInventario() internamente
    const reqGet = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario');
    reqGet.flush(mockLista);

    expect(service.guardando()).toBe(false);
    expect(service.mensajeExito()).toContain('completada con exito');
  });

  it('debe consultar y almacenar el historial de Kardex en kardexActual signal', () => {
    const mockKardex: HistorialKardexOut = {
      id_inventario: 1,
      prenda_sku: 'Chaqueta Cuero Atelier (BER-CHA-L-NEG)',
      sucursal_nombre: 'Boutique Central',
      saldo_actual: 15,
      movimientos: [
        {
          id_movimiento: 1,
          id_inventario: 1,
          tipo_movimiento: 'ingreso_proveedor',
          cantidad: 15,
          saldo_anterior: 0,
          saldo_nuevo: 15,
          motivo: 'Lote inicial',
          referencia_documento: 'GUIA-01',
          id_usuario: 1,
          usuario_nombre: 'Admin General',
          creado_en: '2026-09-21T10:00:00Z',
        },
      ],
    };

    service.cargarKardex(1).subscribe((kardex) => {
      expect(kardex.saldo_actual).toBe(15);
    });

    const req = httpMock.expectOne('/api/v1/admin/inventario/1/kardex');
    expect(req.request.method).toBe('GET');
    req.flush(mockKardex);

    expect(service.kardexActual()).toEqual(mockKardex);
  });

  it('debe consultar disponibilidad publica de variantes sin token', () => {
    service.consultarDisponibilidad(100).subscribe((disp) => {
      expect(disp.sku).toBe('BER-CHA-L-NEG');
    });

    const req = httpMock.expectOne('/api/v1/inventario/disponibilidad/100');
    expect(req.request.method).toBe('GET');
    req.flush({
      id_variante: 100,
      sku: 'BER-CHA-L-NEG',
      nombre_prenda: 'Chaqueta Cuero Atelier',
      sucursales: [],
    });

    expect(service.disponibilidadActual()?.sku).toBe('BER-CHA-L-NEG');
  });

  it('debe capturar y propagar error HTTP 403 con mensaje descriptivo de autorizacion', () => {
    service.cargarInventario({ id_sucursal: 99 }).subscribe({
      error: (err) => {
        expect(err.status).toBe(403);
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario');
    req.flush(
      { detail: 'Acceso denegado: No tiene autorizacion para esta sede.', code: 'SUCURSAL_NO_AUTORIZADA' },
      { status: 403, statusText: 'Forbidden' }
    );

    expect(service.error()).toContain('Acceso denegado');
    expect(service.cargando()).toBe(false);
  });

  it('debe limpiar los mensajes y el panel de kardex al invocar utilitarios', () => {
    service.error.set('Un error');
    service.mensajeExito.set('Exito');
    service.kardexActual.set({ id_inventario: 1, prenda_sku: '', sucursal_nombre: '', saldo_actual: 0, movimientos: [] });

    service.limpiarMensajes();
    expect(service.error()).toBeNull();
    expect(service.mensajeExito()).toBeNull();

    service.limpiarKardex();
    expect(service.kardexActual()).toBeNull();
  });

  it('debe omitir parametros vacios, nulos o estado todos al construir HttpParams', () => {
    service
      .cargarInventario({
        id_sucursal: null,
        id_categoria: null,
        estado_stock: 'todos',
        q: '',
      })
      .subscribe();

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/inventario');
    expect(req.request.params.has('id_sucursal')).toBe(false);
    expect(req.request.params.has('id_categoria')).toBe(false);
    expect(req.request.params.has('estado_stock')).toBe(false);
    expect(req.request.params.has('q')).toBe(false);
    req.flush(mockLista);
  });
});

