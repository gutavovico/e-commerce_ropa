import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/recomendacion_item_dto.dart';

abstract class RecomendacionesApi {
  Future<RecomendacionesResponseDto> obtenerRecomendaciones({
    String? token,
    int limite = 6,
    int? idSucursal,
  });
}

class RecomendacionesApiImpl implements RecomendacionesApi {
  final http.Client _client;

  RecomendacionesApiImpl({http.Client? client}) : _client = client ?? http.Client();

  @override
  Future<RecomendacionesResponseDto> obtenerRecomendaciones({
    String? token,
    int limite = 6,
    int? idSucursal,
  }) async {
    final queryParams = <String, String>{
      'limite': limite.toString(),
    };
    if (idSucursal != null) {
      queryParams['id_sucursal'] = idSucursal.toString();
    }

    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/catalogo/recomendaciones/personalizadas')
        .replace(queryParameters: queryParams);

    final headers = <String, String>{
      HttpHeaders.acceptHeader: 'application/json',
    };
    if (token != null && token.isNotEmpty) {
      headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
    }

    try {
      final response = await _client.get(uri, headers: headers).timeout(
            const Duration(seconds: 5),
          );

      if (response.statusCode == 200) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return RecomendacionesResponseDto.fromJson(decoded);
      } else {
        return RecomendacionesResponseDto.emptyState();
      }
    } catch (_) {
      // Degradación elegante en caso de desconexión
      return RecomendacionesResponseDto.emptyState();
    }
  }

  void dispose() {
    _client.close();
  }
}
