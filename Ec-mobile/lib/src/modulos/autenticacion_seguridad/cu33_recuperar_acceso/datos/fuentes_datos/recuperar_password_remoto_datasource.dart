import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/recuperar_password_dto.dart';

class RecuperarPasswordExcepcion implements Exception {
  final String mensaje;
  final String? codigo;
  final int? statusCode;

  const RecuperarPasswordExcepcion(this.mensaje, {this.codigo, this.statusCode});

  @override
  String toString() => mensaje;
}

class RecuperarPasswordRemotoDatasource {
  final http.Client _client;

  RecuperarPasswordRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(
    SolicitarCodigoPeticionDto dto,
  ) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}/api/v1/autenticacion/recuperar-password/solicitar',
    );

    try {
      final response = await _client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(dto.toJson()),
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        throw const RecuperarPasswordExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return SolicitarCodigoRespuestaDto.fromJson(body);
      } else if (response.statusCode == 422) {
        final detalle = body['detail'];
        String msg = 'El formato del correo electrónico no es válido.';
        if (detalle is List && detalle.isNotEmpty) {
          msg = detalle[0]['msg'] as String? ?? msg;
        }
        throw RecuperarPasswordExcepcion(msg, statusCode: 422);
      } else {
        final detalle = body['detail'] as String? ??
            'Error al procesar la solicitud de recuperación.';
        final codigo = body['code'] as String?;
        throw RecuperarPasswordExcepcion(
          detalle,
          codigo: codigo,
          statusCode: response.statusCode,
        );
      }
    } on RecuperarPasswordExcepcion {
      rethrow;
    } catch (e) {
      throw RecuperarPasswordExcepcion(
        'Error de conexión con el servidor: $e',
        statusCode: 0,
      );
    }
  }

  Future<RestablecerPasswordRespuestaDto> restablecerPassword(
    RestablecerPasswordPeticionDto dto,
  ) async {
    final uri = Uri.parse(
      '${ApiConfig.baseUrl}/api/v1/autenticacion/recuperar-password/restablecer',
    );

    try {
      final response = await _client.post(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: jsonEncode(dto.toJson()),
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(response.body) as Map<String, dynamic>;
      } catch (_) {
        throw const RecuperarPasswordExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return RestablecerPasswordRespuestaDto.fromJson(body);
      } else if (response.statusCode == 400) {
        final detalle = body['detail'] as String? ??
            'El código ingresado es incorrecto o ha caducado.';
        final codigo = body['code'] as String? ?? 'CODIGO_INVALIDO';
        throw RecuperarPasswordExcepcion(detalle, codigo: codigo, statusCode: 400);
      } else if (response.statusCode == 422) {
        final detalle = body['detail'];
        String msg = 'Datos de restablecimiento no válidos.';
        if (detalle is List && detalle.isNotEmpty) {
          msg = detalle[0]['msg'] as String? ?? msg;
        } else if (detalle is String) {
          msg = detalle;
        }
        throw RecuperarPasswordExcepcion(msg, statusCode: 422);
      } else {
        final detalle = body['detail'] as String? ??
            'No se pudo restablecer la contraseña.';
        final codigo = body['code'] as String?;
        throw RecuperarPasswordExcepcion(
          detalle,
          codigo: codigo,
          statusCode: response.statusCode,
        );
      }
    } on RecuperarPasswordExcepcion {
      rethrow;
    } catch (e) {
      throw RecuperarPasswordExcepcion(
        'Error de conexión con el servidor: $e',
        statusCode: 0,
      );
    }
  }
}
