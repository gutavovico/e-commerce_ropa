import { ComponentFixture, TestBed } from '@angular/core/testing';
import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { afterEach, describe, expect, it, vi } from 'vitest';

import { CambioPrendaComponent } from './cambio-prenda.component';

/** Payloads literales generados con los esquemas Pydantic de `cu18_cambio_prenda` y de la caja. */
const VENTA = JSON.parse(
  '{"id_venta":501,"numero_comprobante":"FS-2026-000501","fecha_venta":"2026-11-10T15:00:00Z","cliente_nombre":"Ana Rojas","total":"450.00","dias_transcurridos":5,"plazo_dias":15,"lineas":[{"id_venta_detalle":1,"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","vendidas":2,"ya_cambiadas":0,"cambiables":2,"valor_unitario":"90.00"}]}'
);
const VARIANTE = JSON.parse(
  '{"id_variante":42,"sku":"MSH-CAM-L","id_producto":5,"nombre_producto":"Camisa formal blanca","categoria_nombre":"Camisas formales","talla_codigo":"L","color_nombre":"Blanco","imagen_url":null,"precio_lista":"100.00","precio_final":"100.00","disponible_en_sucursal":3}'
);
const PREVIO = JSON.parse(
  '{"devueltas":[{"tipo":"devuelta","id_venta_detalle":1,"id_variante":41,"sku":"MSH-CAM-M","nombre_producto":"Camisa formal blanca","talla_codigo":"M","color_nombre":"Blanco","cantidad":1,"precio_unitario":"90.00","subtotal":"90.00","motivo_descuento":null}],"nuevas":[{"tipo":"nueva","id_venta_detalle":null,"id_variante":42,"sku":"MSH-CAM-L","nombre_producto":"Camisa formal blanca","talla_codigo":"L","color_nombre":"Blanco","cantidad":1,"precio_unitario":"100.00","subtotal":"100.00","motivo_descuento":null}],"valor_devuelto":"90.00","valor_nuevo":"100.00","diferencia":"10.00"}'
);
const CAMBIO = {
  ...PREVIO,
  id_cambio: 7, numero_comprobante: 'CAM-2026-00001', creado_en: '2026-11-10T15:00:00Z', id_venta: 501,
  comprobante_venta: 'FS-2026-000501', id_sucursal: 3, nombre_sucursal: 'Menshopping Santa Cruz',
  atendido_por: 'Carlos Perez', metodo_pago: 'efectivo', monto_recibido: '20.00', vuelto: '10.00',
  referencia: null, devuelto_al_cliente: '0.00',
};

describe('CambioPrendaComponent (P2-CU18)', () => {
  let fixture: ComponentFixture<CambioPrendaComponent>;
  let http: HttpTestingController;

  function crear(enLinea = true): void {
    TestBed.configureTestingModule({
      imports: [CambioPrendaComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    fixture = TestBed.createComponent(CambioPrendaComponent);
    fixture.componentRef.setInput('enLinea', enLinea);
    http = TestBed.inject(HttpTestingController);
    fixture.detectChanges();
  }

  const raiz = () => fixture.nativeElement as HTMLElement;
  const escribir = (selector: string, valor: string) => {
    const campo = raiz().querySelector(selector) as HTMLInputElement;
    campo.value = valor;
    campo.dispatchEvent(new Event('input'));
    fixture.detectChanges();
  };
  const pulsar = (selector: string) => {
    (raiz().querySelector(selector) as HTMLButtonElement).click();
    fixture.detectChanges();
  };

  afterEach(() => {
    vi.useRealTimers();
    http.verify();
    TestBed.resetTestingModule();
  });

  async function prepararCambio(): Promise<void> {
    escribir('#campo-comprobante-cambio', 'FS-2026-000501');
    pulsar('#btn-buscar-venta-cambio');
    http.expectOne((r) => r.url === '/api/v1/pos/cambios/venta').flush(VENTA);
    fixture.detectChanges();
    expect(raiz().textContent).toContain('2 de 2 por cambiar');

    pulsar('[aria-label="Devolver MSH-CAM-M"]');
    vi.useFakeTimers();
    escribir('#campo-prenda-cambio', 'camisa');
    await vi.advanceTimersByTimeAsync(350);
    http.expectOne((r) => r.url === '/api/v1/pos/variantes').flush([VARIANTE]);
    fixture.detectChanges();
    const opcion = [...raiz().querySelectorAll('button')].find((b) => b.textContent?.includes('(3 disp.)'))!;
    opcion.click();
    fixture.detectChanges();
    const previa = http.expectOne('/api/v1/pos/cambios/previsualizar');
    expect(previa.request.body).toEqual({
      id_venta: 501, id_sucursal: null,
      devueltas: [{ id_venta_detalle: 1, cantidad: 1 }],
      nuevas: [{ id_variante: 42, cantidad: 1 }],
    });
    previa.flush(PREVIO);
    fixture.detectChanges();
  }

  it('AC-1 → AC-9: busca, elige, ve la diferencia del servidor, cobra y muestra el ticket', async () => {
    crear();
    await prepararCambio();
    expect(raiz().querySelector('#diferencia-cambio')?.textContent).toContain('Paga el cliente');
    expect(raiz().querySelector('#diferencia-cambio')?.textContent).toContain('10,00');

    escribir('#campo-monto-cambio', '20');
    pulsar('#btn-registrar-cambio');
    const registro = http.expectOne('/api/v1/pos/cambios');
    expect(registro.request.body.cobro).toEqual({ metodo_pago: 'efectivo', monto_recibido: '20', referencia: null });
    registro.flush(CAMBIO);
    fixture.detectChanges();

    const ticket = raiz().querySelector('#ticket-cambio')!.textContent!;
    expect(ticket).toContain('CAMBIO DE PRENDA CAM-2026-00001');
    expect(ticket).toContain('Venta original: FS-2026-000501');
    expect(ticket).toContain('Vuelto');
  });

  it('AC-3: el plazo vencido se muestra con el mensaje del servidor', () => {
    crear();
    escribir('#campo-comprobante-cambio', 'FS-1');
    pulsar('#btn-buscar-venta-cambio');
    http.expectOne((r) => r.url === '/api/v1/pos/cambios/venta').flush(
      { detail: 'Pasaron 20 días desde la venta y el plazo de cambio es de 15 días.', code: 'PLAZO_DE_CAMBIO_VENCIDO',
        dias_transcurridos: 20, plazo_dias: 15 },
      { status: 409, statusText: 'Conflict' }
    );
    fixture.detectChanges();
    expect(raiz().querySelector('#error-cambio')?.textContent).toContain('Pasaron 20 días');
  });

  it('AC-13: sin conexión no deja registrar', async () => {
    crear(false);
    await prepararCambio();
    expect(raiz().textContent).toContain('Sin conexión: no se puede registrar el cambio.');
    expect((raiz().querySelector('#btn-registrar-cambio') as HTMLButtonElement).disabled).toBe(true);
  });
});
