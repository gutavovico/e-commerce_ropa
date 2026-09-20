import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/producto_paginado_dto.dart';
import '../modelos/filtros_disponibles_dto.dart';

class CatalogoExcepcion implements Exception {
  final String mensaje;
  final String? codigo;
  final int? statusCode;

  const CatalogoExcepcion(this.mensaje, {this.codigo, this.statusCode});

  @override
  String toString() => mensaje;
}

class CatalogoRemotoDatasource {
  final http.Client _client;

  CatalogoRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  /// Realiza la consulta paginada al catálogo con filtros opcionales.
  Future<ProductoPaginadoDto> buscarProductos({
    String? q,
    int? temporadaId,
    int? coleccionId,
    int? categoriaId,
    String? talla,
    String? color,
    double? precioMin,
    double? precioMax,
    bool soloEnStock = false,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 12,
  }) async {
    final queryParams = <String, String>{
      'pagina': pagina.toString(),
      'limite': limite.toString(),
      'solo_en_stock': soloEnStock.toString(),
      'ordenar_por': ordenarPor,
    };

    if (q != null && q.trim().isNotEmpty) {
      queryParams['q'] = q.trim();
    }
    if (temporadaId != null) {
      queryParams['temporada_id'] = temporadaId.toString();
    }
    if (coleccionId != null) {
      queryParams['coleccion_id'] = coleccionId.toString();
    }
    if (categoriaId != null) {
      queryParams['categoria_id'] = categoriaId.toString();
    }
    if (talla != null && talla.trim().isNotEmpty) {
      queryParams['talla'] = talla.trim();
    }
    if (color != null && color.trim().isNotEmpty) {
      queryParams['color'] = color.trim();
    }
    if (precioMin != null) {
      queryParams['precio_min'] = precioMin.toString();
    }
    if (precioMax != null) {
      queryParams['precio_max'] = precioMax.toString();
    }

    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/productos')
        .replace(queryParameters: queryParams);

    try {
      final response = await _client.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      } catch (_) {
        throw const CatalogoExcepcion(
          'Respuesta no válida del servidor central.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return ProductoPaginadoDto.fromJson(body);
      } else if (response.statusCode == 422) {
        final detalle = body['detail'];
        String msg = 'Criterios de búsqueda no procesables.';
        if (detalle is List && detalle.isNotEmpty) {
          msg = detalle[0]['msg'] ?? msg;
        } else if (detalle is String) {
          msg = detalle;
        }
        throw CatalogoExcepcion(msg, statusCode: 422);
      } else {
        final errorMsg = body['detail'] ?? body['message'] ?? 'Error al consultar catálogo.';
        throw CatalogoExcepcion(errorMsg.toString(), statusCode: response.statusCode);
      }
    } on CatalogoExcepcion {
      rethrow;
    } catch (e) {
      throw CatalogoExcepcion(
        'Imposible conectar con el servidor de catálogo: $e',
        statusCode: 0,
      );
    }
  }

  /// Recupera los metadatos de temporadas, colecciones, tallas y colores.
  Future<FiltrosDisponiblesDto> obtenerFiltrosDisponibles() async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/v1/catalogo/filtros-disponibles');

    try {
      final response = await _client.get(
        uri,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
      );

      final Map<String, dynamic> body;
      try {
        body = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      } catch (_) {
        throw const CatalogoExcepcion(
          'Respuesta no válida del catálogo de filtros.',
          statusCode: 500,
        );
      }

      if (response.statusCode == 200) {
        return FiltrosDisponiblesDto.fromJson(body);
      } else {
        final errorMsg = body['detail'] ?? 'Error al obtener filtros disponibles.';
        throw CatalogoExcepcion(errorMsg.toString(), statusCode: response.statusCode);
      }
    } on CatalogoExcepcion {
      rethrow;
    } catch (e) {
      throw CatalogoExcepcion(
        'Error de red al obtener filtros disponibles: $e',
        statusCode: 0,
      );
    }
  }
}
