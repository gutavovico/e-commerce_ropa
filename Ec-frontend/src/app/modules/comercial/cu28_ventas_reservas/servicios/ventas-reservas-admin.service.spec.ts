/**
 * Pruebas unitarias para VentasReservasAdminService (CU28).
 * Nomenclatura oficial: "Consultar ventas y reservas"
 */

import { TestBed } from '@angular/core/testing';
import {
  provideHttpClientTesting,
  HttpTestingController,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { VentasReservasAdminService } from './ventas-reservas-admin.service';
import {
  MetricasTransaccionales,
  ReservaDetalleCompleto,
  RespuestaPaginadaTransacciones,
  SucursalOpcion,
  TransaccionResumenItem,
  VentaDetalleCompleto,
} from '../modelos/ventas-reservas.dto';

describe('VentasReservasAdminService', () => {
  let service: VentasReservasAdminService;
  let httpMock: HttpTestingController;

  const mockMetricas: MetricasTransaccionales = {
    monto_total_facturado: 15450.0,
    total_ventas_concluidas: 24,
    reservas_activas: 7,
    ticket_promedio: 643.75,
  };

  const mockItem: TransaccionResumenItem = {
    id_transaccion: 101,
    tipo_operacion: 'venta',
    codigo_comprobante: 'VTA-00101',
    fecha: '2026-09-22T10:30:00Z',
    id_cliente: 1,
    nombre_cliente: 'Carolina Herrera',
    email_cliente: 'carolina@luxury.com',
    telefono_cliente: '+591 70012345',
    id_sucursal: 1,
    nombre_sucursal: 'Boutique Central',
    ciudad_sucursal: 'La Paz',
    canal: 'sucursal',
    estado: 'completada',
    total_monto: 1250.0,
    cantidad_items: 1,
  };

  const mockRespuestaPaginada: RespuestaPaginadaTransacciones = {
    items: [mockItem],
    total: 1,
    pagina: 1,
    limite: 10,
    total_paginas: 1,
    metricas: mockMetricas,
  };

  const mockVentaDetalle: VentaDetalleCompleto = {
    id_venta: 101,
    numero_comprobante: 'VTA-00101',
    fecha_venta: '2026-09-22T10:30:00Z',
    estado: 'completada',
    tipo_venta: 'directa',
    subtotal: 1200.0,
    descuento: 0.0,
    total: 1250.0,
    id_sucursal: 1,
    nombre_sucursal: 'Boutique Central',
    ciudad_sucursal: 'La Paz',
    id_cliente: 1,
    nombre_cliente: 'Carolina Herrera',
    email_cliente: 'carolina@luxury.com',
    telefono_cliente: '+591 70012345',
    cajero_nombre: 'Pedro Cajero',
    lineas: [
      {
        id_detalle: 1,
        id_variante: 10,
        sku: 'VSN-S-BLK',
        nombre_producto: 'Vestido Seda Silk Noir',
        talla: 'S',
        color: 'Negro',
        codigo_hex: '#000000',
        cantidad: 1,
        precio_unitario: 1250.0,
        subtotal_linea: 1250.0,
        imagen_url: null,
      },
    ],
    pagos: [
      {
        id_pago: 1,
        metodo_pago: 'tarjeta_credito',
        monto: 1250.0,
        estado: 'completado',
        referencia_pasarela: 'AUTH-99441',
        creado_en: '2026-09-22T10:30:00Z',
        confirmado_en: '2026-09-22T10:31:00Z',
      },
    ],
  };

  const mockReservaDetalle: ReservaDetalleCompleto = {
    id_reserva: 202,
    codigo_reserva: 'RES-00202',
    fecha_hora_atencion: '2026-09-25T18:00:00Z',
    creado_en: '2026-09-22T11:00:00Z',
    estado: 'confirmada',
    canal_origen: 'web',
    observacion: 'Prueba de vestido nupcial',
    id_sucursal: 1,
    nombre_sucursal: 'Boutique Central',
    ciudad_sucursal: 'La Paz',
    id_cliente: 2,
    nombre_cliente: 'Valentina Rossi',
    email_cliente: 'valentina@fashion.it',
    telefono_cliente: '+591 71198765',
    atendido_por_nombre: 'Elena Asesora',
    lineas: [
      {
        id_detalle: 2,
        id_variante: 15,
        sku: 'BVI-M-NVY',
        nombre_producto: 'Blazer Velvet Imperial',
        talla: 'M',
        color: 'Azul Marino',
        codigo_hex: '#000080',
        cantidad: 1,
        precio_unitario: 890.0,
        subtotal_linea: 890.0,
        imagen_url: null,
      },
    ],
  };

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        VentasReservasAdminService,
        provideHttpClient(),
        provideHttpClientTesting(),
      ],
    });

    service = TestBed.inject(VentasReservasAdminService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('debe inicializarse con estado reactivo predeterminado', () => {
    expect(service).toBeTruthy();
    expect(service.transacciones()).toEqual([]);
    expect(service.totalTransacciones()).toBe(0);
    expect(service.totalPaginas()).toBe(1);
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
    expect(service.metricas().monto_total_facturado).toBe(0);
    expect(service.filtros().pagina).toBe(1);
  });

  it('debe listar transacciones y actualizar signals reactivos con exito', () => {
    service.listarTransacciones().subscribe((res) => {
      expect(res.items.length).toBe(1);
      expect(res.items[0].codigo_comprobante).toBe('VTA-00101');
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('pagina')).toBe('1');
    expect(req.request.params.get('limite')).toBe('10');

    req.flush(mockRespuestaPaginada);

    expect(service.transacciones().length).toBe(1);
    expect(service.totalTransacciones()).toBe(1);
    expect(service.metricas().monto_total_facturado).toBe(15450.0);
    expect(service.metricas().total_ventas_concluidas).toBe(24);
  });

  it('debe enviar parametros de filtro multicriterio al backend', () => {
    service.actualizarFiltros({
      q: 'Carolina',
      tipo_operacion: 'venta',
      estado: 'completada',
      id_sucursal: 3,
      fecha_desde: '2026-09-01',
      fecha_hasta: '2026-09-30',
      metodo_pago: 'tarjeta_credito',
      canal_origen: 'sucursal',
      ordenar_por: 'total_desc',
      pagina: 2,
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    expect(req.request.params.get('q')).toBe('Carolina');
    expect(req.request.params.get('tipo_operacion')).toBe('venta');
    expect(req.request.params.get('estado')).toBe('completada');
    expect(req.request.params.get('id_sucursal')).toBe('3');
    expect(req.request.params.get('fecha_desde')).toBe('2026-09-01');
    expect(req.request.params.get('fecha_hasta')).toBe('2026-09-30');
    expect(req.request.params.get('metodo_pago')).toBe('tarjeta_credito');
    expect(req.request.params.get('canal_origen')).toBe('sucursal');
    expect(req.request.params.get('ordenar_por')).toBe('total_desc');
    expect(req.request.params.get('pagina')).toBe('2');

    req.flush(mockRespuestaPaginada);
  });

  it('debe obtener el detalle completo de una venta por ID', () => {
    service.obtenerDetalleVenta(101).subscribe((detalle) => {
      expect(detalle.id_venta).toBe(101);
      expect(detalle.numero_comprobante).toBe('VTA-00101');
      expect(detalle.lineas.length).toBe(1);
      expect(detalle.pagos.length).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/admin/ventas-reservas/ventas/101');
    expect(req.request.method).toBe('GET');
    req.flush(mockVentaDetalle);
  });

  it('debe obtener el detalle completo de una reserva por ID', () => {
    service.obtenerDetalleReserva(202).subscribe((detalle) => {
      expect(detalle.id_reserva).toBe(202);
      expect(detalle.codigo_reserva).toBe('RES-00202');
      expect(detalle.lineas.length).toBe(1);
    });

    const req = httpMock.expectOne('/api/v1/admin/ventas-reservas/reservas/202');
    expect(req.request.method).toBe('GET');
    req.flush(mockReservaDetalle);
  });

  it('debe cargar sucursales auxiliares para el selector de filtros', () => {
    const mockSucursales: SucursalOpcion[] = [
      { id_sucursal: 1, nombre: 'Boutique Central', ciudad: 'La Paz' },
      { id_sucursal: 2, nombre: 'Boutique Sur', ciudad: 'Santa Cruz' },
    ];

    service.cargarSucursalesAuxiliares();

    const req = httpMock.expectOne('/api/v1/admin/sucursales');
    expect(req.request.method).toBe('GET');
    req.flush(mockSucursales);

    expect(service.sucursalesDisponibles().length).toBe(2);
    expect(service.sucursalesDisponibles()[0].nombre).toBe('Boutique Central');
  });

  it('debe capturar y formatear errores semanticos de autorizacion HTTP 403', () => {
    service.listarTransacciones().subscribe({
      error: (err) => {
        expect(err.message).toContain('No cuenta con privilegios autorizados');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    req.flush(null, { status: 403, statusText: 'Forbidden' });

    expect(service.error()).toContain('No cuenta con privilegios autorizados');
  });

  it('debe capturar errores de rango de fechas o validacion HTTP 422', () => {
    service.listarTransacciones().subscribe({
      error: (err) => {
        expect(err.message).toContain('Los parametros de consulta suministrados');
      },
    });

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    req.flush(null, { status: 422, statusText: 'Unprocessable Content' });

    expect(service.error()).toContain('Los parametros de consulta suministrados');
  });

  it('debe cambiar de pagina si se encuentra dentro de limites validos', () => {
    service.totalPaginas.set(5);

    service.cambiarPagina(3);

    const req = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    expect(req.request.params.get('pagina')).toBe('3');
    req.flush(mockRespuestaPaginada);

    expect(service.filtros().pagina).toBe(3);

    // Si la pagina es invalida, no emite solicitud
    service.cambiarPagina(99);
    httpMock.expectNone((r) => r.params.get('pagina') === '99');
  });

  it('debe resetear los filtros y reconsultar el listado', () => {
    service.actualizarFiltros({ q: 'Texto previo', pagina: 4 });
    const req1 = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    req1.flush(mockRespuestaPaginada);

    service.resetearFiltros();
    const req2 = httpMock.expectOne((r) => r.url === '/api/v1/admin/ventas-reservas');
    req2.flush(mockRespuestaPaginada);

    expect(service.filtros().q).toBe('');
    expect(service.filtros().pagina).toBe(1);
    expect(service.filtros().tipo_operacion).toBe('todas');
  });
});
