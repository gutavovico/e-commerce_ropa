import 'dart:io' show Platform;
import 'package:flutter/foundation.dart' show kIsWeb;

/// Configuración centralizada de red y entornos para Ec-mobile.
class ApiConfig {
  /// Permite sobreescribir la URL base mediante `--dart-define=API_URL=http://...`
  static const String _envApiUrl = String.fromEnvironment('API_URL', defaultValue: '');

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
