import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { signal } from '@angular/core';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import { AlmacenEnMemoria, AlmacenLocal } from './almacen-local';
import { ConectividadService } from './conectividad.service';
import { SinConexionService } from './sin-conexion.service';
import { franjasDeCita } from './franjas-cita';

/**
 * P2-CU14 / CU15 A1 / CU19 en la PWA. Los payloads son literales generados con los esquemas Pydantic
 * del backend (`esquemas.py` de cada CU de `modules/sincronizacion`, con `model_dump_json`), no objetos armados a mano.
 */
const DISPOSITIVO = JSON.parse(
  '{"id_dispositivo":1,"identificador":"3f9a2c1e-1111-4222-8333-444455556666","plataforma":"pwa","codigo_corto":"3F9A","registrado_en":"2026-11-09T15:00:00Z","ultima_descarga_en":null,"operacion_offline_habilitada":true,"dias_antiguedad_offline":7,"horas_vencimiento_reserva":24,"moneda":"BOB"}'
);
const CATALOGO = JSON.parse(
  '{"generado_en":"2026-11-09T15:00:00Z","modo":"completo","moneda":"BOB","productos":[{"id_producto":5,"nombre":"Camisa formal blanca","descripcion":"Algodón","id_categoria":2,"precio_base":"350.00","imagen_url":"/ar/menshopping_camisa.png","variantes":[{"id_variante":41,"sku":"MSH-CAM-M","id_talla":2,"id_color":1,"precio":"350.00"}]}],"categorias":[{"id_categoria":2,"nombre":"Camisas formales","id_categoria_padre":null}],"tallas":[{"id_talla":2,"codigo":"M","orden":2}],"colores":[{"id_color":1,"nombre":"Blanco","codigo_hex":"#FFFFFF"}],"promociones":[],"sucursales":[{"id_sucursal":3,"nombre":"Menshopping Santa Cruz","direccion":"Dirección por confirmar","ciudad":"Santa Cruz de la Sierra","horario_apertura":"09:00","horario_cierre":"20:00"}],"existencias":[{"id_variante":41,"id_sucursal":3,"cantidad_disponible":5}]}'
);
const BANDEJA = JSON.parse(
  '{"no_leidos":1,"avisos":[{"id_aviso":4,"tipo":"reserva_cancelada","titulo":"Reserva PROV-3F9A-000002 cancelada","mensaje":"No pudimos confirmar tu reserva PROV-3F9A-000002: Ya no quedan unidades suficientes en la sucursal.","id_reserva":null,"id_venta":null,"creado_en":"2026-11-09T15:00:00Z","leido":false}]}'
);

function lote(uuid: string, estado: string, extra: Record<string, unknown> = {}) {
  return {
    id_sync_log: 88,
    resultados: [
      {
        uuid, estado, motivo: null, mensaje: 'Reserva confirmada.', codigo_reserva: 'RES-2026-0123',
        id_reserva: 123, id_venta: null, id_conflicto: null, repetida: false, ...extra,
      },
    ],
  };
}

describe('SinConexionService (P2-CU14 / CU19)', () => {
  let servicio: SinConexionService;
  let http: HttpTestingController;
  let almacen: AlmacenEnMemoria;
  const enLinea = signal(true);

  beforeEach(() => {
    enLinea.set(true);
    almacen = new AlmacenEnMemoria();
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: AlmacenLocal, useValue: almacen },
        { provide: ConectividadService, useValue: { enLinea } },
      ],
    });
    servicio = TestBed.inject(SinConexionService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    vi.useRealTimers();
    http.verify();
  });

  /** Deja que corran las promesas encadenadas antes de esperar la siguiente petición. */
  const tic = () => new Promise((r) => setTimeout(r, 0));

  async function prepararConRed(): Promise<void> {
    const preparacion = servicio.prepararTienda('menshopping', 10, true);
    await tic();
    const registro = http.expectOne('/api/v1/sin-conexion/dispositivos');
    expect(registro.request.body.plataforma).toBe('pwa');
    registro.flush(DISPOSITIVO);
    await tic();
    const descarga = http.expectOne((r) => r.url === '/api/v1/sin-conexion/catalogo');
    expect(descarga.request.params.get('modo')).toBe('completo');
    descarga.flush(CATALOGO);
    await tic();
    http.expectOne((r) => r.url === '/api/v1/sin-conexion/operaciones').flush([]);
    await tic();
    http.expectOne('/api/v1/avisos').flush(BANDEJA);
    await preparacion;
  }

  async function reservar() {
    return servicio.reservarSinConexion({
      idSucursal: 3,
      fechaHoraAtencion: '2026-11-10T14:00:00.000Z',
      items: [{ id_variante: 41, cantidad: 1 }],
      resumen: { producto: 'Camisa formal blanca', variante: 'M · Blanco', sucursal: 'Menshopping Santa Cruz' },
    });
  }

  it('prepara la tienda: registra el dispositivo, guarda el catálogo y carga los avisos', async () => {
    await prepararConRed();
    expect(servicio.dispositivo()?.codigoCorto).toBe('3F9A');
    expect(servicio.catalogo()?.productos[0].precio_base).toBe('350.00');
    expect(servicio.avisosNoLeidos()).toBe(1);
    expect((await almacen.catalogo('menshopping'))?.paquete.moneda).toBe('BOB');
  });

  it('sin red trabaja con lo guardado y no llama a la API (CU14 A4)', async () => {
    await prepararConRed();
    enLinea.set(false);
    await servicio.prepararTienda('menshopping', 10, null);
    expect(servicio.catalogo()?.productos.length).toBe(1);
    http.expectNone(() => true);
  });

  it('mientras no se sabe si el cliente está registrado en la tienda no llama a la API', async () => {
    await servicio.prepararTienda('menshopping', 10, null);
    http.expectNone(() => true);
    expect(servicio.preparado()).toBe(false);
  });

  it('un cliente no registrado en la tienda no registra dispositivo ni sincroniza (evita el 403)', async () => {
    await servicio.prepararTienda('menshopping', 10, false);
    expect(await servicio.sincronizar()).toBe(false);
    http.expectNone(() => true);
    expect(servicio.registradoEnTienda()).toBe(false);
  });

  it('una descarga fallida conserva el catálogo anterior (CU14 A2)', async () => {
    await prepararConRed();
    const descarga = servicio.descargarCatalogo();
    http.expectOne((r) => r.url === '/api/v1/sin-conexion/catalogo').flush(null, { status: 0, statusText: 'Sin red' });
    await expect(descarga).rejects.toBeTruthy();
    expect(servicio.catalogo()?.generado_en).toBe('2026-11-09T15:00:00Z');
  });

  it('sin red guarda la reserva con su código provisional y queda pendiente (CU15 A1, RN34)', async () => {
    await prepararConRed();
    enLinea.set(false);
    const primera = await reservar();
    const segunda = await reservar();
    expect(primera.codigoProvisional).toBe('PROV-3F9A-000001');
    expect(segunda.codigoProvisional).toBe('PROV-3F9A-000002');
    expect(primera.estado).toBe('registrada_localmente');
    expect(servicio.pendientes().length).toBe(2);
    expect((await almacen.operaciones('menshopping:10')).length).toBe(2);
  });

  it('al sincronizar aplica el resultado y conserva la operación (RN36, RN37)', async () => {
    await prepararConRed();
    enLinea.set(false);
    const op = await reservar();
    enLinea.set(true);

    const envio = servicio.sincronizar();
    await tic();
    const peticion = http.expectOne('/api/v1/sin-conexion/sincronizar');
    expect(peticion.request.body.operaciones[0]).toEqual(
      expect.objectContaining({ uuid: op.uuid, tipo: 'reserva', id_sucursal: 3, codigo_provisional: 'PROV-3F9A-000001' })
    );
    peticion.flush(lote(op.uuid, 'confirmada'));
    await tic();
    http.expectOne('/api/v1/avisos').flush(BANDEJA);
    expect(await envio).toBe(true);

    const guardada = (await almacen.operaciones('menshopping:10'))[0];
    expect(guardada.estado).toBe('confirmada');
    expect(guardada.codigoReserva).toBe('RES-2026-0123');
    expect(servicio.pendientes().length).toBe(0);
  });

  it('una reserva rechazada guarda el motivo', async () => {
    await prepararConRed();
    enLinea.set(false);
    const op = await reservar();
    enLinea.set(true);
    const envio = servicio.sincronizar();
    await tic();
    http.expectOne('/api/v1/sin-conexion/sincronizar').flush(
      lote(op.uuid, 'rechazada', { motivo: 'STOCK_INSUFICIENTE', mensaje: 'Ya no quedan unidades suficientes en la sucursal.', codigo_reserva: null, id_reserva: null })
    );
    await tic();
    http.expectOne('/api/v1/avisos').flush(BANDEJA);
    await envio;
    expect(servicio.operaciones()[0].estado).toBe('rechazada');
    expect(servicio.operaciones()[0].motivo).toBe('STOCK_INSUFICIENTE');
  });

  it('si falla la red conserva las operaciones y programa un reintento (CU19 A1)', async () => {
    await prepararConRed();
    enLinea.set(false);
    await reservar();
    enLinea.set(true);
    vi.useFakeTimers();
    const envio = servicio.sincronizar();
    await vi.advanceTimersByTimeAsync(0);
    http.expectOne('/api/v1/sin-conexion/sincronizar').flush(null, { status: 0, statusText: 'Sin red' });
    expect(await envio).toBe(false);
    expect(servicio.operaciones()[0].estado).toBe('registrada_localmente');

    await vi.advanceTimersByTimeAsync(5_000); // primer reintento
    http.expectOne('/api/v1/sin-conexion/sincronizar').flush(null, { status: 503, statusText: 'Caído' });
    await vi.advanceTimersByTimeAsync(0);
    expect(servicio.pendientes().length).toBe(1);
  });

  it('con la sesión expirada conserva todo y lo indica (CU19 A5)', async () => {
    await prepararConRed();
    enLinea.set(false);
    await reservar();
    enLinea.set(true);
    const envio = servicio.sincronizar();
    await tic();
    http.expectOne('/api/v1/sin-conexion/sincronizar').flush({ detail: 'Token' }, { status: 401, statusText: 'No autorizado' });
    expect(await envio).toBe(false);
    expect(servicio.sesionExpirada()).toBe(true);
    expect(servicio.pendientes().length).toBe(1);
  });

  it('una tienda que no permite operar sin conexión no deja reservar (CU14 A5)', async () => {
    const preparacion = servicio.prepararTienda('menshopping', 10, true);
    await tic();
    http.expectOne('/api/v1/sin-conexion/dispositivos').flush({ ...DISPOSITIVO, operacion_offline_habilitada: false });
    await tic();
    http.expectOne((r) => r.url === '/api/v1/sin-conexion/catalogo').flush(CATALOGO);
    await tic();
    http.expectOne((r) => r.url === '/api/v1/sin-conexion/operaciones').flush([]);
    await tic();
    http.expectOne('/api/v1/avisos').flush({ no_leidos: 0, avisos: [] });
    await preparacion;
    expect(servicio.puedeReservarSinConexion()).toBe(false);
    await expect(reservar()).rejects.toThrow('no permite reservar sin conexión');
  });

  it('cada tienda guarda lo suyo y al cerrar sesión se borra el catálogo, no las operaciones (RNF03)', async () => {
    await prepararConRed();
    enLinea.set(false);
    await reservar();
    await servicio.prepararTienda('fashionstore', 10, null);
    expect(servicio.catalogo()).toBeNull();
    expect(servicio.operaciones()).toEqual([]);

    await servicio.cerrarSesion();
    expect(await almacen.catalogo('menshopping')).toBeUndefined();
    expect((await almacen.operaciones('menshopping:10')).length).toBe(1);
  });

  it('refresca el estado del conflicto de una operación (CU20, el dispositivo ve el nuevo estado)', async () => {
    await prepararConRed();
    enLinea.set(false);
    const op = await reservar();
    await almacen.guardarOperacion({ ...op, estado: 'en_conflicto' });
    await servicio.prepararTienda('menshopping', 10, null); // recarga lo local, sin red
    enLinea.set(true);
    const refresco = servicio.refrescarEstados();
    await tic();
    // Al volver la red el servicio también sincroniza por su cuenta: se responde a todas las consultas.
    for (const peticion of http.match((r) => r.url === '/api/v1/sin-conexion/operaciones')) {
      peticion.flush([
        {
          uuid: op.uuid, tipo: 'reserva', estado: 'en_conflicto', motivo: 'STOCK_INSUFICIENTE',
          codigo_provisional: 'PROV-3F9A-000001', codigo_reserva: null, id_reserva: null, id_venta: 501,
          registrada_en: op.registradaEn, recibida_en: '2026-11-09T15:00:00Z', estado_conflicto: 'resuelto',
        },
      ]);
    }
    await refresco;
    expect(servicio.operaciones()[0].estadoConflicto).toBe('resuelto');
  });
});

describe('franjasDeCita (P2-CU15, RN25)', () => {
  it('solo ofrece horas dentro del vencimiento y del horario de la tienda', () => {
    const ahora = new Date(2026, 10, 9, 10, 15);
    const franjas = franjasDeCita(ahora, 24, 50);
    const limite = ahora.getTime() + 24 * 3_600_000;
    expect(franjas.length).toBeGreaterThan(0);
    for (const f of franjas) {
      const fecha = new Date(f.iso);
      expect(fecha.getTime()).toBeLessThanOrEqual(limite);
      expect(fecha.getTime()).toBeGreaterThan(ahora.getTime() + 3_600_000);
      expect(fecha.getHours()).toBeGreaterThanOrEqual(9);
      expect(fecha.getHours()).toBeLessThan(20);
    }
    expect(franjas[0].etiqueta).toBe('Hoy 12:00');
  });

  it('con pocas horas de vencimiento por la noche no ofrece ninguna', () => {
    expect(franjasDeCita(new Date(2026, 10, 9, 21, 0), 2)).toEqual([]);
  });
});
