import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/registro_dto.dart';

class RegistroExcepcion implements Exception {
  final String mensaje;
  final String? codigo;
  final int? statusCode;

  const RegistroExcepcion(this.mensaje, {this.codigo, this.statusCode});

  @override
  String toString() => mensaje;
}

class RegistroRemotoDatasource {
  final http.Client _client;

  RegistroRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  Future<RegistroRespuestaDto> registrarCliente(RegistroClienteDto dto) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/autenticacion/registrarse');

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
        throw const RegistroExcepcion(
          'Respuesta del servidor no válida.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 201) {
        return RegistroRespuestaDto.fromJson(body);
      } else if (response.statusCode == 409) {
        final detalle = body['detail'] as String? ??
            'El correo electrónico ya se encuentra registrado.';
        final codigo = body['code'] as String? ?? 'USUARIO_YA_EXISTE';
        throw RegistroExcepcion(detalle, codigo: codigo, statusCode: 409);
      } else if (response.statusCode == 422) {
        throw const RegistroExcepcion(
          'Datos incompletos o con formato incorrecto.',
          statusCode: 422,
        );
      } else {
        final detalle = body['detail'] as String? ??
            'Error al procesar el registro (HTTP ${response.statusCode}).';
        throw RegistroExcepcion(detalle, statusCode: response.statusCode);
      }
    } on RegistroExcepcion {
      rethrow;
    } catch (e) {
      throw RegistroExcepcion(
        'Error de conexión con el servidor de FashionStore: $e',
      );
    }
  }
}
