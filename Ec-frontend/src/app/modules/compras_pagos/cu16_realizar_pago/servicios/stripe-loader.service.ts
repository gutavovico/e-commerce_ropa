import { Injectable } from '@angular/core';
import { Stripe, loadStripe } from '@stripe/stripe-js';

/**
 * Envuelve `loadStripe` de `@stripe/stripe-js` en un servicio inyectable para que las pruebas lo
 * sustituyan vía `TestBed`, sin salir a la red ni cargar el SDK real de Stripe.
 */
@Injectable({ providedIn: 'root' })
export class StripeLoaderService {
  cargar(publishableKey: string): Promise<Stripe | null> {
    return loadStripe(publishableKey);
  }
}
