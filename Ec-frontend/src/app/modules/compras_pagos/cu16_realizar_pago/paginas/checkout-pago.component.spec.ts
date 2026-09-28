import { ComponentFixture, TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, provideRouter } from '@angular/router';
import { signal } from '@angular/core';
import { of } from 'rxjs';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { CheckoutPagoComponent } from './checkout-pago.component';
import { PagoService } from '../servicios/pago.service';
import { PagoConfirmado, PagoIntentoOut, ResumenPago } from '../modelos/pago.model';

/**
 * Este archivo cubre el «modo simulador»: `environments/environment.ts` trae
 * `stripePublishableKey: ''` por defecto (sin una clave real de Stripe configurada), que es el
 * estado real del proyecto hoy. El componente entonces no carga Stripe.js — no hay red que
 * mockear— y muestra en su lugar el panel de escenarios deterministas, el mismo mecanismo que ya
 * usa `StripeService` en el backend cuando tampoco tiene `STRIPE_SECRET_KEY` real (revisado el
 * 2026-09-28). El caso con clave real configurada se cubre aparte, en
 * `checkout-pago-stripe-real.component.spec.ts`.
 */

const RESUMEN_MOCK: ResumenPago = {
  id_venta: 101,
  numero_comprobante: 'TK-2026-000101',
  estado: 'pendiente',
  subtotal: '1940.00',
  descuento: '160.00',
  total: '1940.00',
  iva_incluido: '336.69',
  moneda: 'EUR',
  total_prendas: 3,
  items: [
    {
      id_variante: 1,
      sku: 'VES-SED-38-MAR',
      nombre_producto: 'Vestido Seda Marfil',
      talla_codigo: '38',
      color_nombre: 'Marfil',
      imagen_url: 'https://images.test/vestido.jpg',
      cantidad: 1,
      precio_unitario: '890.00',
      subtotal_linea: '890.00',
      nombre_sucursal: 'FLAGSHIP SERRANO',
    },
    {
      id_variante: 2,
      sku: 'BLA-LAN-40-CAM',
      nombre_producto: 'Blazer Lana Camel',
      talla_codigo: '40',
      color_nombre: 'Camel',
      imagen_url: 'https://images.test/blazer.jpg',
      cantidad: 1,
      precio_unitario: '740.00',
      subtotal_linea: '740.00',
      nombre_sucursal: 'SAINT-HONORÉ PARÍS',
    },
    {
      id_variante: 3,
      sku: 'BLU-SAT-38-CHA',
      nombre_producto: 'Blusa Satén Champagne',
      talla_codigo: '38',
      color_nombre: 'Champagne',
      imagen_url: 'https://images.test/blusa.jpg',
      cantidad: 1,
      precio_unitario: '310.00',
      subtotal_linea: '310.00',
      nombre_sucursal: 'HUB CENTRAL',
    },
  ],
  tipo_entrega: 'domicilio',
  direccion_envio: 'Calle de Claudio Coello 48, 4º Derecha, 28001 Madrid',
  nombre_sucursal_retiro: null,
  nombre_cliente: 'Ana Valenzuela',
  fecha_venta: '2026-09-22T10:00:00Z',
  expira_en: '2026-09-22T10:25:00Z',
  segundos_restantes: 1500,
  metodos_disponibles: ['tarjeta_credito', 'tarjeta_debito', 'qr', 'pasarela_digital'],
};

// Payload literal calcado del esquema `PagoConfirmadoOut` del backend (nunca construido a mano
// sobre la interfaz del cliente): id_pago, id_venta, numero_comprobante, estado_pago,
// estado_venta, metodo_pago, referencia_pasarela, monto, moneda, marca_tarjeta,
// ultimos_digitos, confirmado_en, mensaje_confirmacion.
const PAGO_EXITOSO_MOCK: PagoConfirmado = {
  id_pago: 505,
  id_venta: 101,
  numero_comprobante: 'TK-2026-000101',
  estado_pago: 'confirmado',
  estado_venta: 'pagada',
  metodo_pago: 'tarjeta_credito',
  referencia_pasarela: 'pi_sbx_123456789',
  monto: '1940.00',
  moneda: 'EUR',
  marca_tarjeta: 'VISA',
  ultimos_digitos: '4242',
  confirmado_en: '2026-09-22T10:05:00Z',
  mensaje_confirmacion: 'Pago confirmado. Tu orden entra en preparación en el atelier.',
};

// Payload literal calcado de `PagoIntentoOut`: lo que devuelve `POST /pagos/intentos`.
const INTENTO_MOCK: PagoIntentoOut = {
  id_pago: 505,
  client_secret: 'pi_sbx_123456789_secret_sbx',
  ya_confirmado: false,
  confirmacion: null,
};

describe('CheckoutPagoComponent (CU16 - Pasarela Stripe, modo simulador)', () => {
  let fixture: ComponentFixture<CheckoutPagoComponent>;
  let componente: CheckoutPagoComponent;
  let mockPagoService: any;

  beforeEach(async () => {
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
        {
          provide: ActivatedRoute,
          useValue: {
            snapshot: {
              paramMap: {
                get: (key: string) => (key === 'idVenta' ? '101' : null),
              },
            },
          },
        },
      ],
    }).compileComponents();

    fixture = TestBed.createComponent(CheckoutPagoComponent);
    componente = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('debe crear el componente y consultar el resumen de pago de la orden', () => {
    expect(componente).toBeTruthy();
    expect(mockPagoService.obtenerResumenPago).toHaveBeenCalledWith(101);
  });

  it('debe renderizar el título de resumen de la orden y el monto de 1.940,00 €', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Resumen de la Orden');
    expect(compiled.textContent).toContain('1940.00 €');
  });

  it('sin clave publicable real, muestra el panel de modo simulador en vez del formulario de Stripe', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Modo simulador');
    expect(compiled.querySelector('#stripe-payment-element')).toBeNull();
    expect((componente as any).stripeDisponible()).toBe(false);
    expect((componente as any).escenarioPrueba()).toBe('aprobado');
  });

  it('no expone ningún campo para número, CVV o expiración de tarjeta', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    // El backend nunca recibe datos de tarjeta (revisado el 2026-09-28): el componente tampoco
    // los recolecta cuando no hay Stripe.js real cargado.
    expect(compiled.querySelector('input[type="password"]')).toBeNull();
    expect(compiled.textContent).not.toContain('Código CVV');
  });

  it('permite elegir el escenario de prueba del simulador', () => {
    (componente as any).seleccionarEscenarioPrueba('rechazado');
    fixture.detectChanges();
    expect((componente as any).escenarioPrueba()).toBe('rechazado');
  });

  it('confirmar con tarjeta en modo simulador abre el intento con el escenario elegido y lo cierra', () => {
    (componente as any).seleccionarEscenarioPrueba('fondos_insuficientes');
    (componente as any).confirmarYPagar();

    expect(mockPagoService.iniciarPago).toHaveBeenCalledWith({
      id_venta: 101,
      metodo_pago: 'tarjeta_credito',
      escenario_prueba: 'fondos_insuficientes',
    });
    expect(mockPagoService.confirmarPago).toHaveBeenCalledWith(505);
  });

  it('debe permitir cambiar a Bizum / Código QR', () => {
    (componente as any).seleccionarMetodo('qr');
    fixture.detectChanges();

    expect((componente as any).metodoSeleccionado()).toBe('qr');
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Bizum / Código QR');
  });

  it('muestra cuenta atrás propia e instrucciones numeradas al seleccionar Bizum/QR', () => {
    (componente as any).seleccionarMetodo('qr');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Expira en:');
    expect(compiled.textContent).toContain('Abre tu app bancaria');
    expect(compiled.textContent).toContain('Escanea el código');
    expect(compiled.textContent).toContain('#ATEL-0101'); // últimos 4 dígitos de TK-2026-000101
    expect((componente as any).segundosCodigoQr()).toBeLessThanOrEqual(300);
  });

  it('confirmar con Bizum/QR siempre se aprueba, sin depender del selector del simulador', () => {
    (componente as any).seleccionarMetodo('qr');
    (componente as any).confirmarYPagar();

    expect(mockPagoService.iniciarPago).toHaveBeenCalledWith({
      id_venta: 101,
      metodo_pago: 'qr',
      escenario_prueba: 'aprobado',
    });
    expect(mockPagoService.confirmarPago).toHaveBeenCalledWith(505);
  });

  it('no muestra el checkbox de "Guardar tarjeta" (descartado en la especificación §1.5.1)', () => {
    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).not.toContain('Guardar tarjeta');
    expect((componente as any).guardarTarjeta).toBeUndefined();
    expect((componente as any).toggleGuardarTarjeta).toBeUndefined();
  });

  it('detiene los temporizadores de la orden y del código QR al destruirse', () => {
    (componente as any).seleccionarMetodo('qr');
    fixture.destroy();
    expect(mockPagoService.detenerTemporizador).toHaveBeenCalled();
  });

  it('muestra "Recogida en Boutique" en vez de "Entrega a Domicilio" cuando la orden se recoge en tienda', () => {
    mockPagoService.resumen.set({
      ...RESUMEN_MOCK,
      tipo_entrega: 'recogida_boutique',
      direccion_envio: null,
      nombre_sucursal_retiro: 'Atelier Serrano - Madrid',
    });
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('Recogida en Boutique Programada');
    expect(compiled.textContent).toContain('Atelier Serrano - Madrid');
    expect(compiled.textContent).not.toContain('Entrega a Domicilio Programada');
  });

  it('muestra el skeleton de carga mientras no llega el resumen de la orden', () => {
    mockPagoService.cargando.set(true);
    mockPagoService.resumen.set(null);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.querySelectorAll('.animate-pulse').length).toBeGreaterThan(0);
    expect(compiled.textContent).not.toContain('Resumen de la Orden');
  });

  it('muestra un estado de error con retorno a la bolsa si la orden no pudo cargarse', () => {
    mockPagoService.cargando.set(false);
    mockPagoService.resumen.set(null);
    mockPagoService.error.set('La orden ya fue liquidada.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('No pudimos abrir tu orden de pago');
    expect(compiled.textContent).toContain('La orden ya fue liquidada.');
    expect(compiled.textContent).toContain('Volver a la bolsa');
  });

  it('el botón "Volver a la bolsa" navega a /bolsa', () => {
    const router = TestBed.inject(Router);
    const navigateSpy = vi.spyOn(router, 'navigate');

    (componente as any).volverABolsa();

    expect(navigateSpy).toHaveBeenCalledWith(['/bolsa']);
  });

  it('alternar a Bizum/QR oculta el panel de tarjeta', () => {
    (componente as any).seleccionarMetodo('qr');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).not.toContain('Modo simulador');
    expect(compiled.querySelector('#stripe-payment-element')).toBeNull();
  });

  it('un rechazo 402 muestra el motivo y conserva la orden para reintentar', () => {
    mockPagoService.error.set('La entidad emisora ha rechazado el pago.');
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('La entidad emisora ha rechazado el pago.');
    expect(compiled.textContent).toContain('Tus prendas continúan reservadas');
    // La orden sigue disponible: no se pierde el resumen tras el rechazo.
    expect(mockPagoService.resumen()).not.toBeNull();
  });

  it('el recibo de confirmación usa los nombres de campo reales del backend', () => {
    mockPagoService.pagoExitoso.set(PAGO_EXITOSO_MOCK);
    fixture.detectChanges();

    const compiled = fixture.nativeElement as HTMLElement;
    expect(compiled.textContent).toContain('TK-2026-000101');
    expect(compiled.textContent).toContain('pi_sbx_123456789');
    expect(compiled.textContent).toContain('VISA terminada en 4242');
    expect(compiled.textContent).toContain(
      'Pago confirmado. Tu orden entra en preparación en el atelier.'
    );
  });
});
