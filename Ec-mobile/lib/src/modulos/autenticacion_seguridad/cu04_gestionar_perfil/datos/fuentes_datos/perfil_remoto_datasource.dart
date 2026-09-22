import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import 'package:ec_mobile/src/core/sesion_manager.dart';
import '../modelos/perfil_dto.dart';

class PerfilExcepcion implements Exception {
  final String mensaje;
  final String? codigo;
  final int? statusCode;

  const PerfilExcepcion(this.mensaje, {this.codigo, this.statusCode});

  @override
  String toString() => mensaje;
}

class PerfilRemotoDatasource {
  final http.Client _client;

  PerfilRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  Future<PerfilClienteDto> obtenerPerfil(String token) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/perfil');

    try {
      final response = await _client.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        throw const PerfilExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return PerfilClienteDto.fromJson(body);
      } else if (response.statusCode == 401) {
        final detalle = body['detail'] as String? ?? 'Sesión expirada o token no válido.';
        final codigo = body['code'] as String? ?? 'TOKEN_INVALIDO';
        SesionManager.instancia.notificarSesionExpirada(mensaje: detalle);
        throw PerfilExcepcion(detalle, codigo: codigo, statusCode: 401);
      } else if (response.statusCode == 403) {
        final detalle = body['detail'] as String? ?? 'Acceso restringido a cuentas cliente.';
        final codigo = body['code'] as String? ?? 'ACCESO_DENEGADO';
        throw PerfilExcepcion(detalle, codigo: codigo, statusCode: 403);
      } else {
        final detalle = body['detail'] as String? ?? 'Error al consultar perfil.';
        throw PerfilExcepcion(detalle, statusCode: response.statusCode);
      }
    } on PerfilExcepcion {
      rethrow;
    } catch (e) {
      throw PerfilExcepcion('Error de conexión al consultar perfil: $e');
    }
  }

  Future<PerfilClienteDto> actualizarPerfil(
    String token,
    PerfilClienteUpdateDto datos,
  ) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/perfil');

    try {
      final response = await _client.patch(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
          'Authorization': 'Bearer $token',
        },
        body: jsonEncode(datos.toJson()),
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        throw const PerfilExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return PerfilClienteDto.fromJson(body);
      } else if (response.statusCode == 422) {
        throw const PerfilExcepcion(
          'Por favor verifica los campos ingresados. Formato de talla o contacto no válido.',
          statusCode: 422,
        );
      } else if (response.statusCode == 401) {
        SesionManager.instancia.notificarSesionExpirada(mensaje: 'Sesión no autorizada.');
        throw const PerfilExcepcion('Sesión no autorizada.', statusCode: 401);
      } else {
        final detalle = body['detail'] as String? ?? 'Error al actualizar perfil.';
        throw PerfilExcepcion(detalle, statusCode: response.statusCode);
      }
    } on PerfilExcepcion {
      rethrow;
    } catch (e) {
      throw PerfilExcepcion('Error de conexión al actualizar perfil: $e');
    }
  }
}
