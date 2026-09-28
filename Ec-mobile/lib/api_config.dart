import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Configuración centralizada de red y entornos para Ec-mobile.
class ApiConfig {
  /// Permite sobreescribir la URL base mediante `--dart-define=API_URL=http://...`
  static const String _envApiUrl = String.fromEnvironment('API_URL', defaultValue: '');

  /// Clave publicable de Stripe (`pk_test_...`/`pk_live_...`), vía
  /// `--dart-define=STRIPE_PUBLISHABLE_KEY=pk_test_...`. No es secreta —Stripe la diseña para
  /// vivir en el cliente—, por eso vive aquí y no en el backend, que solo conoce
  /// `STRIPE_SECRET_KEY`. Vacía por defecto: sin ella, `PagoBloc`/`CheckoutPaymentScreen` no
  /// inicializan el SDK de Stripe y usan en su lugar el panel de «modo simulador», que refleja
  /// lo que hace `StripeService` en el backend cuando tampoco tiene `STRIPE_SECRET_KEY` real.
  static const String stripePublishableKey = String.fromEnvironment(
    'STRIPE_PUBLISHABLE_KEY',
    defaultValue: '',
  );

  /// Puerto por defecto del backend FastAPI
  static const int port = 8000;

  /// Obtiene la URL base de forma dinámica según la plataforma y el entorno de ejecución:
  /// - Android Emulator: 10.0.2.2 (alias de localhost de la máquina host)
  /// - iOS Simulator / Desktop: localhost
  /// - Web: localhost
  /// - Dispositivo físico: configurable vía `--dart-define=API_URL=http://<IP_LOCAL>:8000`
  static String get baseUrl {
    if (_envApiUrl.isNotEmpty) {
      return _envApiUrl;
    }

    if (kIsWeb) {
      return 'http://localhost:$port';
    }

    if (Platform.isAndroid) {
      return 'http://10.0.2.2:$port';
    } else if (Platform.isIOS || Platform.isMacOS || Platform.isWindows || Platform.isLinux) {
      return 'http://localhost:$port';
    }

    return 'http://localhost:$port';
  }

  /// Endpoint de comprobación de salud del backend
  static String get healthEndpoint => '$baseUrl/api/v1/health';

  /// Nombre legible de la plataforma detectada
  static String get platformName {
    if (kIsWeb) return 'Web Browser';
    if (Platform.isAndroid) return 'Android (Emulador: 10.0.2.2)';
    if (Platform.isIOS) return 'iOS (Simulador: localhost)';
    if (Platform.isWindows) return 'Windows Desktop';
    if (Platform.isMacOS) return 'macOS Desktop';
    if (Platform.isLinux) return 'Linux Desktop';
    return 'Desconocido';
  }
}
