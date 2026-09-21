import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/coleccion_dto.dart';

class ColeccionesException implements Exception {
  final String mensaje;
  final int? statusCode;

  const ColeccionesException(this.mensaje, {this.statusCode});

  @override
  String toString() => mensaje;
}

abstract class ColeccionesApi {
  Future<ColeccionesActivasResponseDto> obtenerColeccionesActivas({
    int limitePiezasClave = 4,
  });

  Future<ColeccionDetalleDto> obtenerPrendasDeColeccion(int idColeccion);
}

class ColeccionesApiImpl implements ColeccionesApi {
  final http.Client _client;

  ColeccionesApiImpl({http.Client? client}) : _client = client ?? http.Client();

  @override
  Future<ColeccionesActivasResponseDto> obtenerColeccionesActivas({
    int limitePiezasClave = 4,
  }) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}/api/v1/colecciones/activas?limite_piezas_clave=$limitePiezasClave',
    );

    try {
      final response = await _client.get(
        uri,
        headers: {'Accept': 'application/json'},
      );

      if (response.statusCode == 200) {
        final decoded = json.decode(utf8.decode(response.bodyBytes))
            as Map<String, dynamic>;
        return ColeccionesActivasResponseDto.fromJson(decoded);
      } else {
        throw ColeccionesException(
          'Error al cargar colecciones activas (${response.statusCode})',
          statusCode: response.statusCode,
        );
      }
    } on ColeccionesException {
      rethrow;
    } catch (e) {
      throw ColeccionesException('Error de conexión con el Atelier: $e');
    }
  }

  @override
  Future<ColeccionDetalleDto> obtenerPrendasDeColeccion(int idColeccion) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}/api/v1/colecciones/$idColeccion/productos',
    );

    try {
      final response = await _client.get(
        uri,
        headers: {'Accept': 'application/json'},
      );

      if (response.statusCode == 200) {
        final decoded = json.decode(utf8.decode(response.bodyBytes))
            as Map<String, dynamic>;
        return ColeccionDetalleDto.fromJson(decoded);
      } else if (response.statusCode == 404) {
        throw const ColeccionesException(
          'Colección no encontrada',
          statusCode: 404,
        );
      } else {
        throw ColeccionesException(
          'Error al consultar prendas de la colección (${response.statusCode})',
          statusCode: response.statusCode,
        );
      }
    } on ColeccionesException {
      rethrow;
    } catch (e) {
      throw ColeccionesException('Error de conexión con el Atelier: $e');
    }
  }
}
