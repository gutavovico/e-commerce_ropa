import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/catalogo_dto.dart';

class CatalogoException implements Exception {
  final String mensaje;
  final int? statusCode;

  const CatalogoException(this.mensaje, {this.statusCode});

  @override
  String toString() => mensaje;
}

abstract class CatalogoApi {
  Future<CatalogoResponseDto> consultarCatalogo({
    int? categoriaId,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 6,
  });
}

class CatalogoApiImpl implements CatalogoApi {
  final http.Client _client;

  CatalogoApiImpl({http.Client? client}) : _client = client ?? http.Client();

  @override
  Future<CatalogoResponseDto> consultarCatalogo({
    int? categoriaId,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 6,
  }) async {
    final queryParams = <String, String>{
      'ordenar_por': ordenarPor,
      'pagina': pagina.toString(),
      'limite': limite.toString(),
    };

    if (categoriaId != null) {
      queryParams['categoria_id'] = categoriaId.toString();
    }

    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/catalogo').replace(
      queryParameters: queryParams,
    );

    try {
      final response = await _client.get(
        uri,
        headers: const {'Accept': 'application/json'},
      );

      if (response.statusCode == 200) {
        final decoded = json.decode(utf8.decode(response.bodyBytes))
            as Map<String, dynamic>;
        return CatalogoResponseDto.fromJson(decoded);
      } else {
        throw CatalogoException(
          'Error al cargar el catálogo de prendas (${response.statusCode})',
          statusCode: response.statusCode,
        );
      }
    } on CatalogoException {
      rethrow;
    } catch (e) {
      throw CatalogoException('Error de conexión con el Atelier: $e');
    }
  }
}
