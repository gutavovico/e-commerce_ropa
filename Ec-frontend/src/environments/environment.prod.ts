/**
 * Configuración de producción, activada por `fileReplacements` en el build `production`.
 *
 * `stripePublishableKey` debe sustituirse por la clave publicable real de Stripe (`pk_live_...`
 * o `pk_test_...` mientras el proyecto siga en modo de pruebas) antes de desplegar a Vercel.
 */
export const environment = {
  production: true,
  stripePublishableKey: '',
};
