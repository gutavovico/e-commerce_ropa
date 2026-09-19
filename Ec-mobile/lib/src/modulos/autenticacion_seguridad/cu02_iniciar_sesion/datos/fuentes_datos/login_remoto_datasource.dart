import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/login_dto.dart';

class LoginExcepcion implements Exception {
  final String mensaje;
  final String? codigo;
  final int? statusCode;

  const LoginExcepcion(this.mensaje, {this.codigo, this.statusCode});

  @override
  String toString() => mensaje;
}

class LoginRemotoDatasource {
  final http.Client _client;

  LoginRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto dto) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/autenticacion/login');

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
        throw const LoginExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return LoginRespuestaDto.fromJson(body);
      } else if (response.statusCode == 401) {
        final detalle = body['detail'] as String? ??
            'Correo o contraseña incorrectos. Por favor, verifica tus datos.';
        final codigo = body['code'] as String? ?? 'CREDENCIALES_INVALIDAS';
        throw LoginExcepcion(detalle, codigo: codigo, statusCode: 401);
      } else if (response.statusCode == 403) {
        final detalle = body['detail'] as String? ??
            'Tu cuenta se encuentra inactiva o suspendida.';
        final codigo = body['code'] as String? ?? 'CUENTA_INACTIVA';
        throw LoginExcepcion(detalle, codigo: codigo, statusCode: 403);
      } else if (response.statusCode == 422) {
        throw const LoginExcepcion(
          'Por favor, ingresa un correo y contraseña válidos.',
          statusCode: 422,
        );
      } else {
        final detalle = body['detail'] as String? ??
            'Error al procesar el inicio de sesión (HTTP ${response.statusCode}).';
        throw LoginExcepcion(detalle, statusCode: response.statusCode);
      }
    } on LoginExcepcion {
      rethrow;
    } catch (e) {
      throw LoginExcepcion(
        'Error de conexión con el servidor de FashionStore: $e',
      );
    }
  }
}
