import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Configuracion centralizada de red y entornos para Ec-mobile.
class ApiConfig {
  /// URL de produccion en la nube (Render) que opera de forma autonoma
  /// sin requerir conexion por cable a la laptop ni presencia en la misma red local.
  static const String productionUrl = 'https://e-commerce-ropa-4vjn.onrender.com';

  /// Permite sobreescribir la URL base mediante `--dart-define=API_URL=http://...`
  static const String _envApiUrl = String.fromEnvironment('API_URL', defaultValue: '');

  /// URL personalizada configurada en tiempo de ejecucion
  static String? _customUrl;

  /// Puerto por defecto del backend FastAPI local
  static const int port = 8000;

  /// Permite establecer una URL base personalizada en tiempo de ejecucion
  static void setCustomBaseUrl(String url) {
    _customUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
  }

  /// Restablece la URL base a su valor predeterminado
  static void restablecerUrlPredeterminada() {
    _customUrl = null;
  }

  /// Obtiene la URL base de forma dinamica segun el entorno:
  /// 1. Si existe URL personalizada definida por el usuario, tiene maxima prioridad.
  /// 2. Si se especifico `--dart-define=API_URL=...` en compilacion, se utiliza.
  /// 3. En entorno Web: localhost:8000
  /// 4. En dispositivos moviles (Android / iOS): URL de produccion en la nube por defecto,
  ///    permitiendo que la aplicacion funcione en cualquier celular sin cables ni laptop.
  static String get baseUrl {
    if (_customUrl != null && _customUrl!.isNotEmpty) {
      return _customUrl!;
    }

    if (_envApiUrl.isNotEmpty) {
      return _envApiUrl;
    }

    if (kIsWeb) {
      return 'http://localhost:$port';
    }

    if (Platform.isAndroid || Platform.isIOS) {
      return productionUrl;
    } else if (Platform.isMacOS || Platform.isWindows || Platform.isLinux) {
      return 'http://localhost:$port';
    }

    return productionUrl;
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
