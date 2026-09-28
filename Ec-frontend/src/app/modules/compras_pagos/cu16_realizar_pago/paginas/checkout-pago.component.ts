import {
  ChangeDetectionStrategy,
  Component,
  OnDestroy,
  OnInit,
  computed,
  inject,
  signal,
} from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { Stripe, StripeElements, StripePaymentElement } from '@stripe/stripe-js';

import { EscenarioPrueba, MetodoPago } from '../modelos/pago.model';
import { PagoService } from '../servicios/pago.service';
import { StripeConfigService } from '../servicios/stripe-config.service';
import { StripeLoaderService } from '../servicios/stripe-loader.service';

/** Duración informativa del código Bizum/QR mostrado en pantalla (§0.6 de la especificación). */
const SEGUNDOS_CODIGO_QR = 5 * 60;

/** Clave de `sessionStorage` para reanudar la confirmación si Stripe redirige fuera de la página. */
const CLAVE_SESION_ID_PAGO = 'fs_pago_id_pago_en_curso';

@Component({
  selector: 'app-checkout-pago',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './checkout-pago.component.html',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class CheckoutPagoComponent implements OnInit, OnDestroy {
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  protected readonly pagoService = inject(PagoService);
  private readonly stripeConfig = inject(StripeConfigService);
  private readonly stripeLoader = inject(StripeLoaderService);

  // --- Estado del Componente ---
  protected readonly idVenta = signal<number>(0);
  protected readonly metodoSeleccionado = signal<MetodoPago>('tarjeta_credito');

  // Cuenta atrás propia del código Bizum/QR, independiente de la ventana de la orden.
  protected readonly segundosCodigoQr = signal<number>(SEGUNDOS_CODIGO_QR);
  private temporizadorQr: ReturnType<typeof setInterval> | null = null;

  // --- Stripe Elements (revisado el 2026-09-28: el backend nunca recibe la tarjeta) ---
  /**
   * Sin `STRIPE_PUBLISHABLE_KEY` real configurada (`environments/environment.ts`), no se carga
   * Stripe.js: se muestra en su lugar el panel de «modo simulador», que refleja el mismo
   * comportamiento del backend cuando tampoco tiene `STRIPE_SECRET_KEY` real.
   */
  protected readonly stripeDisponible = computed(() => !!this.stripeConfig.publishableKey);
  protected readonly montandoStripe = signal(false);
  protected readonly stripeListo = signal(false);
  protected readonly escenarioPrueba = signal<EscenarioPrueba>('aprobado');
  private stripe: Stripe | null = null;
  private elements: StripeElements | null = null;
  private paymentElement: StripePaymentElement | null = null;

  // --- Computados ---
  protected readonly resumen = this.pagoService.resumen;
  protected readonly cargando = this.pagoService.cargando;
  protected readonly procesando = this.pagoService.procesando;
  protected readonly error = this.pagoService.error;
  protected readonly pagoExitoso = this.pagoService.pagoExitoso;
  protected readonly segundosRestantes = this.pagoService.segundosRestantes;

  /** Formato dinámico del temporizador: MM:SS */
  protected readonly tiempoRestanteFormateado = computed(() => {
    return this.pagoService.formatearTiempoRestante(this.segundosRestantes());
  });

  /** Cálculo de cuota en 3 plazos con Atelier Pay */
  protected readonly cuota3Plazos = computed(() => {
    const r = this.resumen();
    if (!r) return '0,00 €';
    const totalNum = Number(r.total) || 0;
    const cuota = totalNum / 3;
    return `${cuota.toFixed(2).replace('.', ',')} €`;
  });

  /** Boutiques reales de expedición de la orden, sin repetir (nunca literales inventados). */
  protected readonly sucursalesExpedicion = computed(() => {
    const items = this.resumen()?.items ?? [];
    const nombres = items
      .map((item) => item.nombre_sucursal)
      .filter((nombre): nombre is string => !!nombre);
    return Array.from(new Set(nombres));
  });

  /** Código corto de referencia para el simulador de Bizum/QR, derivado del comprobante real. */
  protected readonly codigoCortoQr = computed(() => {
    const comprobante = this.resumen()?.numero_comprobante;
    if (!comprobante) return '';
    const digitos = comprobante.replace(/\D/g, '');
    return `#ATEL-${digitos.slice(-4) || comprobante}`;
  });

  /** La orden se recoge en boutique en vez de enviarse a domicilio. */
  protected readonly esRecogidaBoutique = computed(
    () => this.resumen()?.tipo_entrega === 'recogida_boutique'
  );

  /** Solo se muestra la línea de beneficio cuando la orden tiene descuento real aplicado. */
  protected readonly hayDescuento = computed(() => Number(this.resumen()?.descuento) > 0);

  ngOnInit(): void {
    const paramId = this.route.snapshot.paramMap.get('idVenta');
    const id = Number(paramId);
    if (!id || isNaN(id)) {
      this.router.navigate(['/bolsa']);
      return;
    }
    this.idVenta.set(id);

    if (this.intentarReanudarTrasRedireccionDeStripe()) {
      return;
    }

    this.cargarResumen();
  }

  protected cargarResumen(): void {
    this.pagoService.obtenerResumenPago(this.idVenta()).subscribe({
      next: () => {
        this.prepararStripeSiCorresponde();
      },
      error: () => {
        // En caso de que la orden no exista o sea inválida, el error ya está en el signal.
      },
    });
  }

  protected seleccionarMetodo(metodo: MetodoPago): void {
    this.metodoSeleccionado.set(metodo);
    if (metodo === 'qr') {
      this.iniciarCuentaAtrasQr();
    } else {
      this.detenerCuentaAtrasQr();
    }
    this.prepararStripeSiCorresponde();
  }

  protected seleccionarEscenarioPrueba(escenario: EscenarioPrueba): void {
    this.escenarioPrueba.set(escenario);
  }

  /**
   * Monta el Payment Element de Stripe en cuanto se conoce el importe de la orden, antes de que
   * el cliente pulse «Confirmar y Pagar». Es el patrón de «recolectar antes de crear el
   * PaymentIntent»: el `client_secret` real solo se pide al backend en el envío.
   */
  private prepararStripeSiCorresponde(): void {
    const metodo = this.metodoSeleccionado();
    if (metodo !== 'tarjeta_credito' && metodo !== 'tarjeta_debito') return;
    if (!this.stripeDisponible() || this.stripeListo() || this.montandoStripe()) return;

    const r = this.resumen();
    if (!r) return;

    this.montandoStripe.set(true);
    this.stripeLoader
      .cargar(this.stripeConfig.publishableKey)
      .then((stripe) => {
        if (!stripe) {
          this.error.set('No fue posible cargar la pasarela de pago. Recarga la página.');
          return;
        }
        this.stripe = stripe;
        const centimos = Math.round(Number(r.total) * 100);
        this.elements = stripe.elements({ mode: 'payment', amount: centimos, currency: 'eur' });
        this.paymentElement = this.elements.create('payment');
        // El contenedor se pinta en el siguiente ciclo de Angular; se monta justo después.
        setTimeout(() => this.paymentElement?.mount('#stripe-payment-element'), 0);
        this.stripeListo.set(true);
      })
      .finally(() => this.montandoStripe.set(false));
  }

  /** Cuenta atrás informativa del código Bizum/QR mostrado en pantalla (§0.6). */
  private iniciarCuentaAtrasQr(): void {
    this.detenerCuentaAtrasQr();
    this.segundosCodigoQr.set(SEGUNDOS_CODIGO_QR);
    this.temporizadorQr = setInterval(() => {
      const actual = this.segundosCodigoQr();
      if (actual <= 1) {
        this.segundosCodigoQr.set(0);
        this.detenerCuentaAtrasQr();
      } else {
        this.segundosCodigoQr.set(actual - 1);
      }
    }, 1000);
  }

  private detenerCuentaAtrasQr(): void {
    if (this.temporizadorQr !== null) {
      clearInterval(this.temporizadorQr);
      this.temporizadorQr = null;
    }
  }

  protected formatearTiempoCodigoQr(): string {
    return this.pagoService.formatearTiempoRestante(this.segundosCodigoQr());
  }

  ngOnDestroy(): void {
    this.pagoService.detenerTemporizador();
    this.detenerCuentaAtrasQr();
    this.paymentElement?.destroy();
  }

  /**
   * Punto de entrada único del botón «Confirmar y Pagar», para los cuatro métodos.
   */
  protected confirmarYPagar(): void {
    const metodo = this.metodoSeleccionado();

    if (metodo === 'tarjeta_credito' || metodo === 'tarjeta_debito') {
      if (this.stripeDisponible()) {
        this.pagarConStripe(metodo);
      } else {
        this.pagarEnModoSimulador(metodo);
      }
      return;
    }

    // Bizum/QR y PayPal: simulaciones decorativas del proyecto, sin pasarela real detrás
    // (ver `spec.md` de CU16). Se aprueban siempre para poder demostrar el flujo.
    this.pagoService.iniciarPago({ id_venta: this.idVenta(), metodo_pago: metodo, escenario_prueba: 'aprobado' })
      .subscribe({
        next: (intento) => this.confirmarSiHaceFalta(intento),
        error: () => window.scrollTo({ top: 120, behavior: 'smooth' }),
      });
  }

  /** Cobro real: el cliente confirma la tarjeta directamente contra Stripe, sin pasar por aquí. */
  private pagarConStripe(metodo: MetodoPago): void {
    const stripe = this.stripe;
    const elements = this.elements;
    if (!stripe || !elements) return;

    this.pagoService.procesando.set(true);
    this.pagoService.error.set(null);

    elements
      .submit()
      .then(({ error: errorEnvio }) => {
        if (errorEnvio) {
          this.error.set(errorEnvio.message ?? 'Revisa los datos de la tarjeta.');
          this.pagoService.procesando.set(false);
          return;
        }

        this.pagoService.iniciarPago({ id_venta: this.idVenta(), metodo_pago: metodo }).subscribe({
          next: (intento) => {
            if (intento.ya_confirmado) {
              this.pagoService.procesando.set(false);
              window.scrollTo({ top: 0, behavior: 'smooth' });
              return;
            }
            if (!intento.client_secret) {
              this.error.set('La pasarela no devolvió un cobro que confirmar.');
              this.pagoService.procesando.set(false);
              return;
            }

            sessionStorage.setItem(CLAVE_SESION_ID_PAGO, String(intento.id_pago));

            stripe
              .confirmPayment({
                elements,
                clientSecret: intento.client_secret,
                confirmParams: { return_url: window.location.href },
                redirect: 'if_required',
              })
              .then(({ error: errorConfirmacion }) => {
                if (errorConfirmacion) {
                  this.error.set(
                    errorConfirmacion.message || 'La entidad emisora ha rechazado la tarjeta.'
                  );
                  this.pagoService.procesando.set(false);
                  window.scrollTo({ top: 120, behavior: 'smooth' });
                  return;
                }
                // Sin `error`, Stripe ya evaluó el cargo (o no hizo falta redirigir). El
                // servidor decide el desenlace final por su cuenta, nunca por lo que este
                // cliente le reporte.
                this.cerrarConBackend(intento.id_pago);
              });
          },
          error: () => {
            this.pagoService.procesando.set(false);
            window.scrollTo({ top: 120, behavior: 'smooth' });
          },
        });
      });
  }

  /** Sin clave real de Stripe: el desenlace lo decide `escenario_prueba`, no una tarjeta real. */
  private pagarEnModoSimulador(metodo: MetodoPago): void {
    this.pagoService
      .iniciarPago({
        id_venta: this.idVenta(),
        metodo_pago: metodo,
        escenario_prueba: this.escenarioPrueba(),
      })
      .subscribe({
        next: (intento) => this.confirmarSiHaceFalta(intento),
        error: () => window.scrollTo({ top: 120, behavior: 'smooth' }),
      });
  }

  private confirmarSiHaceFalta(intento: { id_pago: number; ya_confirmado: boolean }): void {
    if (intento.ya_confirmado) {
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }
    this.cerrarConBackend(intento.id_pago);
  }

  private cerrarConBackend(idPago: number): void {
    this.pagoService.confirmarPago(idPago).subscribe({
      next: () => {
        sessionStorage.removeItem(CLAVE_SESION_ID_PAGO);
        window.scrollTo({ top: 0, behavior: 'smooth' });
      },
      error: () => {
        sessionStorage.removeItem(CLAVE_SESION_ID_PAGO);
        window.scrollTo({ top: 120, behavior: 'smooth' });
      },
    });
  }

  /**
   * Si Stripe redirigió a esta misma página tras un método que exigió salir de ella (algunos
   * exigen redirección incluso con `redirect: 'if_required'`), retoma la confirmación con el
   * `id_pago` que se guardó antes de enviar. Devuelve `true` si asumió el control del arranque.
   */
  private intentarReanudarTrasRedireccionDeStripe(): boolean {
    const params = new URLSearchParams(window.location.search);
    const clientSecretDeRetorno = params.get('payment_intent_client_secret');
    const idPagoGuardado = sessionStorage.getItem(CLAVE_SESION_ID_PAGO);

    if (!clientSecretDeRetorno || !idPagoGuardado) return false;

    this.pagoService.procesando.set(true);
    this.pagoService
      .obtenerResumenPago(this.idVenta())
      .subscribe({ next: () => this.cerrarConBackend(Number(idPagoGuardado)) });
    return true;
  }

  protected volverABolsa(): void {
    this.router.navigate(['/bolsa']);
  }

  protected irACatalogo(): void {
    this.router.navigate(['/catalogo']);
  }
}
