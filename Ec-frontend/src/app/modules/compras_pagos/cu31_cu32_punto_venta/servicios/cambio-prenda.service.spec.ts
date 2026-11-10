import { TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';

import { CambioPrendaService } from './cambio-prenda.service';

/** Payload literal generado con `VentaCambiableOut.model_dump_json` (backend, P2-CU18). */
const VENTA = JSON.parse(
  '{"id_venta":501,"numero_comprobante":"FS-2026-000501","fecha_venta":"2026-11-10T15:00:00Z","cliente_nombre":"Ana Rojas","total":"450.00","dias_transcurridos":5,"plazo_dias":15,"lineas":[{"id_venta_detalle":1,"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","vendidas":2,"ya_cambiadas":0,"cambiables":2,"valor_unitario":"90.00"}]}'
);

describe('CambioPrendaService (P2-CU18)', () => {
  let servicio: CambioPrendaService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({ providers: [provideHttpClient(), provideHttpClientTesting()] });
    servicio = TestBed.inject(CambioPrendaService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('busca la venta por comprobante con la sucursal del administrador y deja los importes como cadena', () => {
    let recibido: unknown;
    servicio.ventaCambiable(' FS-2026-000501 ', 3).subscribe((v) => (recibido = v));
    const peticion = http.expectOne((r) => r.url === '/api/v1/pos/cambios/venta');
    expect(peticion.request.params.get('comprobante')).toBe('FS-2026-000501');
    expect(peticion.request.params.get('id_sucursal')).toBe('3');
    peticion.flush(VENTA);
    expect((recibido as typeof VENTA).lineas[0].valor_unitario).toBe('90.00');
  });

  it('sin sucursal (cajero) no envía id_sucursal; registrar va a POST /pos/cambios', () => {
    servicio.ventaCambiable('FS-1', null).subscribe();
    expect(http.expectOne((r) => r.url === '/api/v1/pos/cambios/venta').request.params.has('id_sucursal')).toBe(false);
    servicio.registrar({ id_venta: 501, id_sucursal: null, devueltas: [], nuevas: [] }).subscribe();
    expect(http.expectOne('/api/v1/pos/cambios').request.method).toBe('POST');
  });
});
