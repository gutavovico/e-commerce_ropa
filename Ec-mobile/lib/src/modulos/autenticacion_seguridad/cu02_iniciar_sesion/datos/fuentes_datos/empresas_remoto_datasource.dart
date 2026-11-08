import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import 'package:ec_mobile/src/core/sesion_manager.dart';

import '../../../../../core/cliente_http_api.dart';
import '../../../../../core/empresa_actual.dart';

class EmpresasExcepcion implements Exception {
  final String mensaje;
  final int? statusCode;

  const EmpresasExcepcion(this.mensaje, {this.statusCode});

  @override
  String toString() => mensaje;
}

/// P2-CU02 · Tiendas en las que está registrado el cliente (`GET /api/v1/mis-empresas`).
class EmpresasRemotoDatasource {
  final http.Client _client;

  EmpresasRemotoDatasource({http.Client? client}) : _client = client ?? ClienteHttpApi();

  Future<List<EmpresaTienda>> misEmpresas(String token) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/mis-empresas');
    final http.Response response;
    try {
      response = await _client.get(uri, headers: {
        'Accept': 'application/json',
        'Authorization': 'Bearer $token',
      });
    } catch (_) {
      throw const EmpresasExcepcion('No se pudo conectar con el servidor. Revisa tu conexión.');
    }

    final dynamic cuerpo;
    try {
      cuerpo = jsonDecode(utf8.decode(response.bodyBytes));
    } catch (_) {
      throw EmpresasExcepcion('Respuesta del servidor no válida.', statusCode: response.statusCode);
    }

    if (response.statusCode == 200 && cuerpo is List) {
      return cuerpo.whereType<Map<String, dynamic>>().map(EmpresaTienda.fromJson).toList();
    }
    final detalle = cuerpo is Map<String, dynamic> ? cuerpo['detail'] as String? : null;
    if (response.statusCode == 401) {
      SesionManager.instancia.notificarSesionExpirada(mensaje: detalle);
    }
    throw EmpresasExcepcion(
      detalle ?? 'No se pudieron cargar tus tiendas (HTTP ${response.statusCode}).',
      statusCode: response.statusCode,
    );
  }
}
