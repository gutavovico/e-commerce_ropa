import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { MisReservasService } from './mis-reservas.service';
import { MisReservas, Reserva } from '../modelos/reserva.model';

/**
 * Payloads literales calcados de `MisReservasOut`/`ReservaOut` del backend
 * (`Ec-backend/app/modules/reservas/cu13_consultar_cancelar_reservas/esquemas.py`), nunca
 * construidos a mano sobre la interfaz del cliente.
 */
const RESERVA_PENDIENTE: Reserva = {
  id_reserva: 1,
  codigo_reserva: 'RES-2026-0001',
  estado: 'pendiente',
  fecha_hora_atencion: '2026-10-02T15:30:00Z',
  creado_en: '2026-09-29T10:00:00Z',
  sucursal: {
    id_sucursal: 1,
    nombre: 'Atelier Serrano - Madrid',
    direccion: 'Calle Serrano 48',
  },
  items: [
    {
      id_variante: 7,
      nombre_producto: 'Blusa de satén fluido',
      talla_codigo: '38',
      color_nombre: 'Champagne',
      color_hex: '#E8DFCF',
      imagen_url: 'https://cdn.fashionstore.test/blusa.jpg',
      cantidad: 1,
      precio_unitario: '310.00',
    },
  ],
  total_prendas: 1,
  observacion: 'Prefiero probador amplio',
  puede_cancelar: true,
};

const RESERVA_CANCELADA: Reserva = {
  ...RESERVA_PENDIENTE,
  id_reserva: 2,
  codigo_reserva: 'RES-2026-0002',
  estado: 'cancelada',
  puede_cancelar: false,
};

const RESPUESTA_MIS_RESERVAS: MisReservas = {
  resumen: {
    activas: 1,
    proxima: {
      id_reserva: 1,
      fecha_hora_atencion: '2026-10-02T15:30:00Z',
      nombre_sucursal: 'Atelier Serrano - Madrid',
    },
  },
  proximas: [RESERVA_PENDIENTE],
  historial: [RESERVA_CANCELADA],
};

describe('MisReservasService (CU13/CU14)', () => {
  let servicio: MisReservasService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), MisReservasService],
    });
    servicio = TestBed.inject(MisReservasService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('arranca con resumen vacío y sin reservas cargadas', () => {
    expect(servicio.resumen()).toEqual({ activas: 0, proxima: null });
    expect(servicio.misReservas()).toBeNull();
    expect(servicio.cargando()).toBe(false);
  });

  it('carga mis reservas y expone el resumen y las listas por Signals', () => {
    servicio.cargarMisReservas().subscribe();

    const peticion = httpMock.expectOne('/api/v1/reservas/mias');
    expect(peticion.request.method).toBe('GET');
    peticion.flush(RESPUESTA_MIS_RESERVAS);

    expect(servicio.resumen().activas).toBe(1);
    expect(servicio.resumen().proxima?.nombre_sucursal).toBe('Atelier Serrano - Madrid');
    expect(servicio.misReservas()?.proximas).toHaveLength(1);
    expect(servicio.misReservas()?.historial).toHaveLength(1);
    expect(servicio.cargando()).toBe(false);
  });

  it('cancela una reserva y recarga la lista completa desde el servidor', () => {
    servicio.cancelarReserva(1, 'No podré asistir ese día').subscribe();

    const peticionCancelar = httpMock.expectOne('/api/v1/reservas/1/cancelar');
    expect(peticionCancelar.request.method).toBe('POST');
    expect(peticionCancelar.request.body).toEqual({ motivo: 'No podré asistir ese día' });
    peticionCancelar.flush({ ...RESERVA_PENDIENTE, estado: 'cancelada', puede_cancelar: false });

    // Tras el 200, el servicio recarga la lista completa: el servidor decide el nuevo reparto
    // entre "próximas" e "historial", no el cliente.
    const peticionRecarga = httpMock.expectOne('/api/v1/reservas/mias');
    peticionRecarga.flush({
      resumen: { activas: 0, proxima: null },
      proximas: [],
      historial: [{ ...RESERVA_PENDIENTE, estado: 'cancelada', puede_cancelar: false }],
    });

    expect(servicio.misReservas()?.proximas).toHaveLength(0);
    expect(servicio.misReservas()?.historial[0].estado).toBe('cancelada');
    expect(servicio.cancelando()).toBe(false);
  });

  it('traduce el 403 de reserva ajena conservando el mensaje del backend', () => {
    servicio.cancelarReserva(1, 'No es mía').subscribe({ error: () => undefined });

    httpMock.expectOne('/api/v1/reservas/1/cancelar').flush(
      { detail: 'Esta reserva pertenece a otro cliente.', code: 'RESERVA_AJENA' },
      { status: 403, statusText: 'Forbidden' }
    );

    expect(servicio.error()).toBe('Esta reserva pertenece a otro cliente.');
  });

  it('traduce el 409 de reserva no cancelable', () => {
    servicio.cancelarReserva(1, 'Cambié de opinión').subscribe({ error: () => undefined });

    httpMock.expectOne('/api/v1/reservas/1/cancelar').flush(
      {
        detail: "La reserva está en estado 'cancelada' y no admite cancelación.",
        code: 'RESERVA_NO_CANCELABLE',
      },
      { status: 409, statusText: 'Conflict' }
    );

    expect(servicio.error()).toContain('no admite cancelación');
  });

  it('traduce el 422 de motivo inválido', () => {
    servicio.cancelarReserva(1, 'no').subscribe({ error: () => undefined });

    httpMock
      .expectOne('/api/v1/reservas/1/cancelar')
      .flush({ detail: 'Validation error' }, { status: 422, statusText: 'Unprocessable Entity' });

    expect(servicio.error()).toContain('entre 3 y 250 caracteres');
  });

  it('traduce la caída de red sin dejar un mensaje técnico', () => {
    servicio.cargarMisReservas().subscribe({ error: () => undefined });

    httpMock
      .expectOne('/api/v1/reservas/mias')
      .error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });

    expect(servicio.error()).toContain('conectar con el atelier');
  });
});
