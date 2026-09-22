import { TestBed } from '@angular/core/testing';
import {
  HttpTestingController,
  provideHttpClientTesting,
} from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { describe, it, expect, beforeEach, afterEach } from 'vitest';

import { CarritoService } from './carrito.service';
import { Carrito } from '../modelos/carrito.model';

/**
 * Payload copiado literalmente de una respuesta real de `GET /api/v1/carrito`.
 *
 * Se construye así a propósito: los mocks escritos «a mano» sobre la interfaz del frontend
 * dan por válido un contrato que el servidor nunca envía, que es exactamente lo que ocultó el
 * desajuste de la confirmación de reserva en CU12.
 */
const RESPUESTA_CARRITO: Carrito = {
  id_carrito: 77,
  items: [
    {
      id_carrito_detalle: 44,
      id_variante: 3,
      id_producto: 1,
      nombre_producto: 'Vestido plisado en seda natural',
      linea_confeccion: null,
      sku: 'VES-PLI-40-ROJ',
      talla_codigo: '40',
      color_nombre: 'Rojo Carmín',
      color_hex: '#8C1C2B',
      imagen_url: 'https://cdn.fashionstore.test/vestido.jpg',
      precio_lista: '890.00',
      precio_unitario: '756.50',
      descuento_linea: '133.50',
      motivo_descuento: 'Membresia Prive',
      cantidad: 1,
      id_sucursal: 1,
      nombre_sucursal: 'Atelier Serrano - Madrid',
      stock_disponible: 15,
      cantidad_maxima: 15,
      subtotal_linea: '756.50',
    },
  ],
  resumen: {
    total_prendas: 1,
    total_lineas: 1,
    subtotal: '890.00',
    descuento: '133.50',
    total: '756.50',
    iva_incluido: '131.30',
    moneda: 'EUR',
  },
  expira_en: '2026-09-22T10:25:00Z',
  sucursales_expedicion: [
    { id_sucursal: 1, nombre: 'Atelier Serrano - Madrid', total_lineas: 1 },
  ],
};

describe('CarritoService (CU11 + CU15)', () => {
  let servicio: CarritoService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), CarritoService],
    });
    servicio = TestBed.inject(CarritoService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('arranca con una bolsa vacía y totales en cero', () => {
    expect(servicio.estaVacia()).toBe(true);
    expect(servicio.total()).toBe('0.00');
    expect(servicio.totalPrendas()).toBe(0);
  });

  it('carga la bolsa y expone el resumen financiero por Signals', () => {
    servicio.cargarCarrito().subscribe();

    const peticion = httpMock.expectOne('/api/v1/carrito');
    expect(peticion.request.method).toBe('GET');
    peticion.flush(RESPUESTA_CARRITO);

    expect(servicio.estaVacia()).toBe(false);
    expect(servicio.items().length).toBe(1);
    expect(servicio.subtotal()).toBe('890.00');
    expect(servicio.descuento()).toBe('133.50');
    expect(servicio.total()).toBe('756.50');
    expect(servicio.ivaIncluido()).toBe('131.30');
    expect(servicio.totalPrendas()).toBe(1);
    expect(servicio.hayDescuento()).toBe(true);
    expect(servicio.cargando()).toBe(false);
  });

  it('respeta la invariante total = subtotal - descuento', () => {
    servicio.cargarCarrito().subscribe();
    httpMock.expectOne('/api/v1/carrito').flush(RESPUESTA_CARRITO);

    const subtotal = Number(servicio.subtotal());
    const descuento = Number(servicio.descuento());
    expect(Number(servicio.total())).toBeCloseTo(subtotal - descuento, 2);
  });

  it('envía la cantidad como valor absoluto al modificar una línea', () => {
    servicio.actualizarCantidad(44, 3).subscribe();

    const peticion = httpMock.expectOne('/api/v1/carrito/items/44');
    expect(peticion.request.method).toBe('PATCH');
    // Absoluta, no incremental: hace la operación idempotente ante doble pulsación.
    expect(peticion.request.body).toEqual({ cantidad: 3 });
    peticion.flush(RESPUESTA_CARRITO);
  });

  it('elimina una línea y reemplaza el estado con la bolsa recalculada', () => {
    servicio.cargarCarrito().subscribe();
    httpMock.expectOne('/api/v1/carrito').flush(RESPUESTA_CARRITO);

    const vacia: Carrito = {
      ...RESPUESTA_CARRITO,
      items: [],
      resumen: { ...RESPUESTA_CARRITO.resumen, total_prendas: 0, total_lineas: 0, subtotal: '0.00', descuento: '0.00', total: '0.00', iva_incluido: '0.00' },
      expira_en: null,
      sucursales_expedicion: [],
    };

    servicio.eliminarItem(44).subscribe();
    const peticion = httpMock.expectOne('/api/v1/carrito/items/44');
    expect(peticion.request.method).toBe('DELETE');
    peticion.flush(vacia);

    expect(servicio.estaVacia()).toBe(true);
    expect(servicio.total()).toBe('0.00');
  });

  it('traduce el 409 de stock insuficiente conservando el mensaje del backend', () => {
    servicio.actualizarCantidad(44, 99).subscribe({ error: () => undefined });

    httpMock.expectOne('/api/v1/carrito/items/44').flush(
      {
        detail:
          "No hay existencias suficientes de 'Vestido plisado en seda natural' (Talla 40) " +
          'en Atelier Serrano - Madrid. Disponibles: 15, solicitadas: 99.',
        code: 'STOCK_INSUFICIENTE',
      },
      { status: 409, statusText: 'Conflict' }
    );

    // El texto del backend nombra la prenda y las cifras: es más útil que cualquier genérico.
    expect(servicio.error()).toContain('Disponibles: 15');
    expect(servicio.error()).toContain('Vestido plisado');
  });

  it('traduce el 403 de línea ajena', () => {
    servicio.eliminarItem(99).subscribe({ error: () => undefined });

    httpMock.expectOne('/api/v1/carrito/items/99').flush(
      { detail: 'Esta prenda pertenece a la bolsa de otro cliente.', code: 'CARRITO_AJENO' },
      { status: 403, statusText: 'Forbidden' }
    );

    expect(servicio.error()).toContain('otro cliente');
  });

  it('traduce la caída de red sin dejar un mensaje técnico', () => {
    servicio.cargarCarrito().subscribe({ error: () => undefined });

    httpMock
      .expectOne('/api/v1/carrito')
      .error(new ProgressEvent('error'), { status: 0, statusText: 'Unknown Error' });

    expect(servicio.error()).toContain('conectar con el atelier');
  });

  it('compone el payload de checkout para entrega a domicilio', () => {
    servicio.tipoEntrega.set('domicilio');
    servicio.direccionEnvio.set('  Calle de Claudio Coello 48, 28001 Madrid  ');
    servicio.cuponAplicado.set('MAISON-2025');

    servicio.tramitarPedido().subscribe();

    const peticion = httpMock.expectOne('/api/v1/ventas/checkout');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toEqual({
      tipo_venta: 'digital_web',
      tipo_entrega: 'domicilio',
      direccion_envio: 'Calle de Claudio Coello 48, 28001 Madrid',
      id_sucursal_retiro: null,
      codigo_cupon: 'MAISON-2025',
    });
    // No se envía ningún importe: el servidor es la fuente de verdad del total.
    expect(peticion.request.body).not.toHaveProperty('total');
    peticion.flush({ id_venta: 1, numero_comprobante: 'FS-2026-000001' });
  });

  it('compone el payload de checkout para recogida en boutique', () => {
    servicio.tipoEntrega.set('recogida_boutique');
    servicio.sucursalRetiro.set(1);

    servicio.tramitarPedido().subscribe();

    const peticion = httpMock.expectOne('/api/v1/ventas/checkout');
    expect(peticion.request.body.tipo_entrega).toBe('recogida_boutique');
    expect(peticion.request.body.id_sucursal_retiro).toBe(1);
    expect(peticion.request.body.direccion_envio).toBeNull();
    peticion.flush({ id_venta: 1 });
  });

  it('vacía la bolsa tras tramitar el pedido', () => {
    servicio.cargarCarrito().subscribe();
    httpMock.expectOne('/api/v1/carrito').flush(RESPUESTA_CARRITO);
    expect(servicio.estaVacia()).toBe(false);

    servicio.tipoEntrega.set('domicilio');
    servicio.direccionEnvio.set('Serrano 48');
    servicio.tramitarPedido().subscribe();
    httpMock.expectOne('/api/v1/ventas/checkout').flush({ id_venta: 1 });

    expect(servicio.estaVacia()).toBe(true);
    expect(servicio.totalPrendas()).toBe(0);
  });
});
