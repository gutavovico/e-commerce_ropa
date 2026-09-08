import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'api_config.dart';

/// Modelo de datos para la respuesta del endpoint de salud
class HealthStatus {
  final String status;
  final String? service;
  final String? timestamp;
  final String rawJson;

  const HealthStatus({
    required this.status,
    this.service,
    this.timestamp,
    required this.rawJson,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json, String raw) {
    return HealthStatus(
      status: json['status'] as String? ?? 'desconocido',
      service: json['service'] as String?,
      timestamp: json['timestamp'] as String?,
      rawJson: raw,
    );
  }

  bool get isOnline => status.toLowerCase() == 'online';
}

/// Servicio de red para comunicarse con el backend FastAPI
class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  /// Consume el endpoint `GET /api/v1/health`
  Future<HealthStatus> checkHealth({String? customBaseUrl}) async {
    final baseUrl = customBaseUrl ?? ApiConfig.baseUrl;
    final uri = Uri.parse('$baseUrl/api/v1/health');

    try {
      final response = await _client
          .get(
            uri,
            headers: {
              HttpHeaders.acceptHeader: 'application/json',
            },
          )
          .timeout(const Duration(seconds: 5));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        return HealthStatus.fromJson(decoded, response.body);
      } else {
        throw HttpException(
          'Error HTTP ${response.statusCode}: ${response.reasonPhrase}',
          uri: uri,
        );
      }
    } on SocketException catch (e) {
      throw Exception(
        'No se pudo conectar a $uri.\n'
        'Verifica que FastAPI esté corriendo en el puerto 8000 y que la IP sea accesible desde este dispositivo.\n'
        'Detalle: ${e.message}',
      );
    } on TimeoutException {
      throw Exception('Tiempo de espera agotado al consultar $uri (timeout 5s).');
    } catch (e) {
      throw Exception('Error al consultar salud del backend: $e');
    }
  }

  void dispose() {
    _client.close();
  }
}
