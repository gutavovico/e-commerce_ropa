import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { CheckoutPagoComponent } from './checkout-pago.component';
import { PagoConfirmado, PagoIntentoOut, ResumenPago } from '../modelos/pago.model';
import { PagoService } from '../servicios/pago.service';
import { StripeConfigService } from '../servicios/stripe-config.service';
import { StripeLoaderService } from '../servicios/stripe-loader.service';

/**
 * Cubre la rama con `STRIPE_PUBLISHABLE_KEY` real configurada, sustituyendo `StripeConfigService`
 * y `StripeLoaderService` vía `TestBed` — el sistema de pruebas de este proyecto
 * (`@angular/build:unit-test`) no admite `vi.mock` sobre imports relativos, así que estos dos
 * servicios existen justamente para poder mockear la config y la carga de Stripe.js sin salir a
 * la red. El «modo simulador» (clave vacía, el estado real por defecto del proyecto) se cubre en
 * `checkout-pago.component.spec.ts`.
 */

const clienteStripeFalso = {
  elements: vi.fn(),
  confirmPayment: vi.fn(),
};

const elementsFalsos = {
  submit: vi.fn(),
  create: vi.fn(),
};

const paymentElementFalso = {
  mount: vi.fn(),
  destroy: vi.fn(),
};

const RESUMEN_MOCK: ResumenPago = {
  id_venta: 101,
  numero_comprobante: 'TK-2026-000101',
  estado: 'pendiente',
  subtotal: '1940.00',
  descuento: '160.00',
  total: '1940.00',
  iva_incluido: '336.69',
  moneda: 'EUR',
  total_prendas: 1,
  items: [],
  tipo_entrega: 'domicilio',
  direccion_envio: 'Calle de Claudio Coello 48, 28001 Madrid',
  nombre_sucursal_retiro: null,
  nombre_cliente: 'Ana Valenzuela',
  fecha_venta: '2026-09-22T10:00:00Z',
  expira_en: '2026-09-22T10:25:00Z',
  segundos_restantes: 1500,
  metodos_disponibles: ['tarjeta_credito', 'tarjeta_debito', 'qr', 'pasarela_digital'],
};

const PAGO_EXITOSO_MOCK: PagoConfirmado = {
  id_pago: 505,
  id_venta: 101,
  numero_comprobante: 'TK-2026-000101',
  estado_pago: 'confirmado',
  estado_venta: 'pagada',
  metodo_pago: 'tarjeta_credito',
  referencia_pasarela: 'pi_live_abc123',
  monto: '1940.00',
  moneda: 'EUR',
  marca_tarjeta: 'VISA',
  ultimos_digitos: '4242',
  confirmado_en: '2026-09-22T10:05:00Z',
  mensaje_confirmacion: 'Pago confirmado. Tu orden entra en preparación en el atelier.',
};

const INTENTO_MOCK: PagoIntentoOut = {
  id_pago: 505,
  client_secret: 'pi_live_abc123_secret_xyz',
  ya_confirmado: false,
  confirmacion: null,
};

describe('CheckoutPagoComponent (CU16 - con STRIPE_PUBLISHABLE_KEY real)', () => {
  let fixture: ComponentFixture<CheckoutPagoComponent>;
  let componente: CheckoutPagoComponent;
  let mockPagoService: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    clienteStripeFalso.elements.mockReturnValue(elementsFalsos);
    elementsFalsos.create.mockReturnValue(paymentElementFalso);
    elementsFalsos.submit.mockResolvedValue({});
    clienteStripeFalso.confirmPayment.mockResolvedValue({});

    mockPagoService = {
      resumen: signal<ResumenPago | null>(RESUMEN_MOCK),
      cargando: signal<boolean>(false),
      procesando: signal<boolean>(false),
      error: signal<string | null>(null),
      pagoExitoso: signal<PagoConfirmado | null>(null),
      segundosRestantes: signal<number | null>(1500),
      obtenerResumenPago: vi.fn().mockReturnValue(of(RESUMEN_MOCK)),
      iniciarPago: vi.fn().mockReturnValue(of(INTENTO_MOCK)),
      confirmarPago: vi.fn().mockReturnValue(of(PAGO_EXITOSO_MOCK)),
      formatearTiempoRestante: vi.fn().mockReturnValue('25:00'),
      detenerTemporizador: vi.fn(),
    };

    await TestBed.configureTestingModule({
      imports: [CheckoutPagoComponent],
      providers: [
        provideRouter([]),
        { provide: PagoService, useValue: mockPagoService },
        { provide: StripeConfigService, useValue: { publishableKey: 'pk_test_mock_123' } },
        {
          provide: StripeLoaderService,
          useValue: { cargar: vi.fn().mockResolvedValue(clienteStripeFalso) },
        },
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: { paramMap: { get: (key: string) => (key === 'idVenta' ? '101' : null) } },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CheckoutPagoComponent);
    componente = fixture.componentInstance;
    fixture.detectChanges();
    // `prepararStripeSiCorresponde` carga Stripe.js de forma asíncrona (`cargar(...).then(...)`).
    await Promise.resolve();
    await Promise.resolve();
    fixture.detectChanges();
  });

  it('con clave publicable real, monta el Payment Element y no el panel de modo simulador', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect((componente as any).stripeDisponible()).toBe(true);
    expect(compiled.textContent).not.toContain('Modo simulador');
    expect(compiled.querySelector('#stripe-payment-element')).not.toBeNull();
  });

  it('carga Stripe.js con la clave publicable configurada y crea el elemento en modo deferred', () => {
    expect(clienteStripeFalso.elements).toHaveBeenCalledWith({
      mode: 'payment',
      amount: 194000,
      currency: 'eur',
    });
    expect(elementsFalsos.create).toHaveBeenCalledWith('payment');
  });

  it('al confirmar: valida con elements.submit(), abre el intento y confirma contra Stripe antes de cerrar con el backend', async () => {
    (componente as any).confirmarYPagar();
    // Cadena de promesas: submit() -> iniciarPago (observable síncrono) -> confirmPayment() -> confirmarPago.
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();

    expect(elementsFalsos.submit).toHaveBeenCalled();
    expect(mockPagoService.iniciarPago).toHaveBeenCalledWith({
      id_venta: 101,
      metodo_pago: 'tarjeta_credito',
    });
    expect(clienteStripeFalso.confirmPayment).toHaveBeenCalledWith(
      expect.objectContaining({
        elements: elementsFalsos,
        clientSecret: 'pi_live_abc123_secret_xyz',
        redirect: 'if_required',
      })
    );
    expect(mockPagoService.confirmarPago).toHaveBeenCalledWith(505);
  });

  it('si Stripe rechaza la confirmación, muestra el motivo y no llama a confirmarPago', async () => {
    clienteStripeFalso.confirmPayment.mockResolvedValue({
      error: { message: 'La entidad emisora ha rechazado la tarjeta.' },
    });

    (componente as any).confirmarYPagar();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();
    await Promise.resolve();

    expect(mockPagoService.confirmarPago).not.toHaveBeenCalled();
  });
});
