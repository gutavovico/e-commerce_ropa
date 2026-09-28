/**
 * Configuración de desarrollo. `ng serve` usa este archivo; `ng build --configuration production`
 * lo sustituye por `environment.prod.ts` vía `fileReplacements` (`angular.json`).
 *
 * `stripePublishableKey` no es secreta —Stripe la diseña para vivir en el cliente— por eso vive
 * aquí y no en el backend, que solo conoce `STRIPE_SECRET_KEY` (`Ec-backend/.env`).
 *
 * Vacía por defecto: sin una clave de prueba real (`pk_test_...`), `CheckoutPagoComponent` no
 * carga Stripe.js y usa en su lugar el panel de «modo simulador», que refleja lo que hace
 * `StripeService` en el backend cuando tampoco hay `STRIPE_SECRET_KEY` configurada.
 */
export const environment = {
  production: false,
  stripePublishableKey: 'pk_test_51SPwcxFtZ96cb3oeme0YcABM1NotroPSleC1BHFkedwQw94AyFwvsgQ2HZ2MHXuCdAiczbqab2jvIrzyODWihhBr00u4gXLBgC',
};
