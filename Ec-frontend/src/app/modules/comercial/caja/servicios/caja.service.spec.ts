import { TestBed } from '@angular/core/testing';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';
import { CajaService } from './caja.service';
import {
  CobroCajaRequest,
  CobroCajaResponse,
  ListadoOrdenesPendientesResponse,
  ListadoReservasPendientesResponse,
  OrdenPendiente,
  ReservaPendienteCaja,
} from '../modelos/caja.dto';

describe('CajaService', () => {
  let service: CajaService;
  let httpTesting: HttpTestingController;

  const mockOrdenes: OrdenPendiente[] = [
    {
      id_venta: 101,
      numero_comprobante: 'FS-2026-000101',
      fecha_venta: '2026-09-28T14:00:00Z',
      id_sucursal: 1,
      nombre_sucursal: 'Boutique Central',
      cliente_nombre: 'Luciana Mendoza',
      tipo_venta: 'presencial',
      estado: 'pendiente',
      subtotal: 500,
      descuento: 0,
      total: 500,
      detalles: [],
    },
  ];

  const mockReservas: ReservaPendienteCaja[] = [
    {
      id_reserva: 42,
      codigo_reserva: 'RES-2026-0042',
      id_cliente: 15,
      cliente_nombre: 'Valeria Rios',
      id_sucursal: 1,
      nombre_sucursal: 'Boutique Central',
      fecha_hora_atencion: '2026-09-28T16:00:00Z',
      estado: 'confirmada',
      canal_origen: 'web',
      prendas: [],
    },
  ];

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), CajaService],
    });

    service = TestBed.inject(CajaService);
    httpTesting = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpTesting.verify();
  });

  it('debe crearse correctamente el servicio e inicializar sus senales', () => {
    expect(service).toBeTruthy();
    expect(service.ordenesPendientes()).toEqual([]);
    expect(service.reservasPendientes()).toEqual([]);
    expect(service.ordenSeleccionada()).toBeNull();
    expect(service.reservaSeleccionada()).toBeNull();
    expect(service.cargando()).toBe(false);
    expect(service.error()).toBeNull();
  });

  it('debe consultar ordenes pendientes y actualizar la senal ordenesPendientes (CU17)', () => {
    const respuestaMock: ListadoOrdenesPendientesResponse = {
      total: 1,
      items: mockOrdenes,
    };

    service.buscarOrdenesPendientes('FS-2026').subscribe((resp) => {
      expect(resp.items.length).toBe(1);
      expect(resp.items[0].numero_comprobante).toBe('FS-2026-000101');
    });

    const req = httpTesting.expectOne((r) => r.url === '/api/v1/caja/ordenes-pendientes');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('q')).toBe('FS-2026');

    req.flush(respuestaMock);

    expect(service.ordenesPendientes().length).toBe(1);
    expect(service.totalOrdenesPendientes()).toBe(1);
  });

  it('debe cobrar una orden, removerla de ordenesPendientes y emitir respuesta (CU17)', () => {
    // Precargar orden en senal
    service.seleccionarOrden(mockOrdenes[0]);

    const payload: CobroCajaRequest = {
      id_venta: 101,
      monto_recibido: 600,
      metodo_pago: 'efectivo',
    };

    const respuestaCobro: CobroCajaResponse = {
      id_pago: 201,
      id_venta: 101,
      numero_comprobante: 'FS-2026-000101',
      monto_total: 500,
      monto_recibido: 600,
      cambio_devuelto: 100,
      metodo_pago: 'efectivo',
      estado_venta: 'pagada',
      estado_pago: 'confirmado',
      cajero_nombre: 'Tony Cajero',
      fecha_cobro: '2026-09-28T14:30:00Z',
    };

    service.cobrarOrden(101, payload).subscribe((resp) => {
      expect(resp.id_pago).toBe(201);
      expect(resp.estado_venta).toBe('pagada');
      expect(resp.cambio_devuelto).toBe(100);
    });

    const req = httpTesting.expectOne('/api/v1/caja/cobrar');
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual(payload);

    req.flush(respuestaCobro);

    expect(service.ordenSeleccionada()).toBeNull();
  });

  it('debe capturar error 422 de monto insuficiente y actualizar senal error', () => {
    const payload: CobroCajaRequest = {
      id_venta: 101,
      monto_recibido: 400,
      metodo_pago: 'efectivo',
    };

    service.cobrarOrden(101, payload).subscribe({
      next: () => {
        expect('No debio tener exito').toBe('Fallo esperado');
      },
      error: (err: Error) => {
        expect(err.message).toContain('El monto entregado es insuficiente');
      },
    });

    const req = httpTesting.expectOne('/api/v1/caja/cobrar');
    req.flush(
      { detail: 'El monto entregado es insuficiente para cubrir el total de la orden.' },
      { status: 422, statusText: 'Unprocessable Entity' }
    );

    expect(service.error()).toContain('El monto entregado es insuficiente');
  });

  it('debe consultar reservas pendientes y actualizar senal reservasPendientes (CU18)', () => {
    const respuestaMock: ListadoReservasPendientesResponse = {
      total: 1,
      items: mockReservas,
    };

    service.buscarReservasPendientes('RES-2026').subscribe((resp) => {
      expect(resp.items.length).toBe(1);
      expect(resp.items[0].codigo_reserva).toBe('RES-2026-0042');
    });

    const req = httpTesting.expectOne((r) => r.url === '/api/v1/caja/reservas-pendientes');
    expect(req.request.method).toBe('GET');
    expect(req.request.params.get('q')).toBe('RES-2026');

    req.flush(respuestaMock);

    expect(service.reservasPendientes().length).toBe(1);
    expect(service.totalReservasPendientes()).toBe(1);
  });

  it('debe confirmar la entrega de una reserva (CU18)', () => {
    service.confirmarEntrega(42, { observaciones: 'Fitting 1' }).subscribe((resp) => {
      expect(resp.estado).toBe('atendida');
      expect(resp.codigo_reserva).toBe('RES-2026-0042');
    });

    const req = httpTesting.expectOne('/api/v1/caja/reservas/42/entregar');
    expect(req.request.method).toBe('POST');
    req.flush({
      id_reserva: 42,
      codigo_reserva: 'RES-2026-0042',
      estado: 'atendida',
      mensaje: 'Entrega completada',
    });
  });

  it('debe marcar inasistencia de reserva y liberar stock (CU18)', () => {
    service.marcarNoAsistio(42).subscribe((resp) => {
      expect(resp.estado).toBe('cancelada');
      expect(resp.items_liberados).toBe(2);
    });

    const req = httpTesting.expectOne('/api/v1/caja/reservas/42/no-asistio');
    expect(req.request.method).toBe('POST');
    req.flush({
      id_reserva: 42,
      codigo_reserva: 'RES-2026-0042',
      estado: 'cancelada',
      items_liberados: 2,
      mensaje: 'Stock liberado',
    });
  });

  it('debe convertir reserva a venta presencial (CU18)', () => {
    service.convertirAVenta(42).subscribe((resp) => {
      expect(resp.id_venta).toBe(105);
      expect(resp.numero_comprobante).toBe('FS-2026-000105');
      expect(resp.total).toBe(450);
    });

    const req = httpTesting.expectOne('/api/v1/caja/reservas/42/convertir-venta');
    expect(req.request.method).toBe('POST');
    req.flush({
      id_venta: 105,
      numero_comprobante: 'FS-2026-000105',
      id_reserva: 42,
      total: 450,
      estado_venta: 'pendiente',
      mensaje: 'Convertida exitosamente',
    });
  });

  it('debe permitir seleccionar y deseleccionar orden y reserva', () => {
    service.seleccionarOrden(mockOrdenes[0]);
    expect(service.ordenSeleccionada()?.id_venta).toBe(101);
    service.seleccionarOrden(null);
    expect(service.ordenSeleccionada()).toBeNull();

    service.seleccionarReserva(mockReservas[0]);
    expect(service.reservaSeleccionada()?.id_reserva).toBe(42);
    service.seleccionarReserva(null);
    expect(service.reservaSeleccionada()).toBeNull();
  });
});
