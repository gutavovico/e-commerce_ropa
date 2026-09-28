import { Injectable } from '@angular/core';

import { environment } from '../../../../../environments/environment';

/**
 * Envuelve `environment.stripePublishableKey` en un servicio inyectable para que las pruebas
 * puedan sustituirlo vía `TestBed` (`{ provide: StripeConfigService, useValue: ... }`), en vez de
 * mockear el módulo `environment` directamente: el sistema de pruebas de este proyecto
 * (`@angular/build:unit-test`) no admite `vi.mock` sobre imports relativos.
 */
@Injectable({ providedIn: 'root' })
export class StripeConfigService {
  /**
   * No es secreta —Stripe la diseña para vivir en el cliente—, por eso vive en `environment.ts`
   * y no en el backend, que solo conoce `STRIPE_SECRET_KEY`.
   */
  readonly publishableKey = environment.stripePublishableKey;
}
