import 'package:flutter_stripe/flutter_stripe.dart' as stripe;

import '../../../../../../api_config.dart';

/// Desenlace normalizado de confirmar un `PaymentIntent` directamente contra Stripe.
///
/// `aprobado` refleja únicamente que Stripe no devolvió un error al confirmar (o que no hizo
/// falta redirigir): el desenlace **definitivo** lo decide el backend en `confirmar_pago`,
/// que vuelve a consultar a Stripe por su cuenta en vez de confiar en este resultado.
class StripeConfirmacionResultado {
  final bool aprobado;
  final String? mensajeError;

  const StripeConfirmacionResultado({required this.aprobado, this.mensajeError});
}

/// Envuelve el SDK de Stripe para que `PagoBloc` pueda confirmar un cobro sin acoplarse
/// directamente a `package:flutter_stripe`, y para que las pruebas lo sustituyan por un doble.
abstract class StripeGateway {
  /// Sin `STRIPE_PUBLISHABLE_KEY` configurada, no hay SDK real que usar.
  bool get disponible;

  Future<StripeConfirmacionResultado> confirmarPago(String clientSecret);
}

/// Confirma el `PaymentIntent` con los datos que el `CardField` de la pantalla ya capturó en el
/// SDK nativo de Stripe. El backend nunca ve el PAN ni el CVV: solo este SDK y Stripe los tocan.
class StripeGatewayReal implements StripeGateway {
  const StripeGatewayReal();

  @override
  bool get disponible => ApiConfig.stripePublishableKey.isNotEmpty;

  @override
  Future<StripeConfirmacionResultado> confirmarPago(String clientSecret) async {
    try {
      await stripe.Stripe.instance.confirmPayment(
        paymentIntentClientSecret: clientSecret,
        data: const stripe.PaymentMethodParams.card(
          paymentMethodData: stripe.PaymentMethodData(),
        ),
      );
      return const StripeConfirmacionResultado(aprobado: true);
    } on stripe.StripeException catch (e) {
      return StripeConfirmacionResultado(
        aprobado: false,
        mensajeError: e.error.localizedMessage ?? e.error.message,
      );
    } catch (e) {
      return StripeConfirmacionResultado(
        aprobado: false,
        mensajeError: 'Error al procesar el pago con la pasarela bancaria: $e',
      );
    }
  }
}

/// Sin clave publicable real configurada: no hay ningún SDK que confirmar. `PagoBloc` no llega a
/// llamar a este gateway en modo simulador (decide el desenlace por `escenario_prueba`, que
/// resuelve el simulador del backend), pero existe como valor por defecto seguro.
class StripeGatewaySimulado implements StripeGateway {
  const StripeGatewaySimulado();

  @override
  bool get disponible => false;

  @override
  Future<StripeConfirmacionResultado> confirmarPago(String clientSecret) async {
    return const StripeConfirmacionResultado(aprobado: true);
  }
}
