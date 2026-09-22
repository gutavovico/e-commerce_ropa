import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import '../../../../../../api_config.dart';
import '../../../../../core/sesion_manager.dart';
import '../modelos/producto_detalle_dto.dart';

class ProductoDetalleException implements Exception {
  final String mensaje;
  final int? codigoHttp;

  const ProductoDetalleException(this.mensaje, {this.codigoHttp});

  @override
  String toString() => mensaje;
}

abstract class ProductoDetalleApi {
  Future<ProductoDetalleDto> obtenerDetalleProducto(int idProducto);
  Future<DisponibilidadResponseDto> consultarDisponibilidad(
    int idProducto, {
    int? idVariante,
  });
  Future<List<SucursalDisponibilidadDto>> obtenerSucursalesActivas();
  Future<ReservaCreadaOutDto> crearReserva(
    ReservaCrearInDto datos, {
    String? token,
  });
}

class ProductoDetalleApiImpl implements ProductoDetalleApi {
  final http.Client _client;
  final String? _customBaseUrl;

  ProductoDetalleApiImpl({
    http.Client? client,
    String? customBaseUrl,
  })  : _client = client ?? http.Client(),
        _customBaseUrl = customBaseUrl;

  String get _baseUrl => _customBaseUrl ?? ApiConfig.baseUrl;

  @override
  Future<ProductoDetalleDto> obtenerDetalleProducto(int idProducto) async {
    final uri = Uri.parse('$_baseUrl/api/v1/productos/$idProducto');

    try {
      final response = await _client.get(
        uri,
        headers: {
          HttpHeaders.acceptHeader: 'application/json',
        },
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return ProductoDetalleDto.fromJson(decoded);
      } else if (response.statusCode == 404) {
        throw const ProductoDetalleException(
          'La prenda seleccionada no existe en el catálogo.',
          codigoHttp: 404,
        );
      } else {
        throw ProductoDetalleException(
          'Error HTTP ${response.statusCode} al obtener detalle de la prenda.',
          codigoHttp: response.statusCode,
        );
      }
    } on SocketException {
      throw const ProductoDetalleException(
        'Error de conexión con el servidor. Verifica tu conexión a internet.',
      );
    } on TimeoutException {
      throw const ProductoDetalleException(
        'Tiempo de espera agotado al consultar la ficha técnica.',
      );
    } catch (e) {
      if (e is ProductoDetalleException) rethrow;
      throw ProductoDetalleException('Error al cargar detalle del producto: $e');
    }
  }

  @override
  Future<DisponibilidadResponseDto> consultarDisponibilidad(
    int idProducto, {
    int? idVariante,
  }) async {
    final queryParams = <String, String>{};
    if (idVariante != null) {
      queryParams['id_variante'] = idVariante.toString();
    }

    final uri = Uri.parse('$_baseUrl/api/v1/productos/$idProducto/disponibilidad')
        .replace(queryParameters: queryParams.isNotEmpty ? queryParams : null);

    try {
      final response = await _client.get(
        uri,
        headers: {
          HttpHeaders.acceptHeader: 'application/json',
        },
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return DisponibilidadResponseDto.fromJson(decoded);
      } else {
        throw ProductoDetalleException(
          'Error HTTP ${response.statusCode} al consultar stock físico por sucursal.',
          codigoHttp: response.statusCode,
        );
      }
    } on SocketException {
      throw const ProductoDetalleException('Error de conexión al consultar disponibilidad.');
    } on TimeoutException {
      throw const ProductoDetalleException('Tiempo de espera agotado al consultar disponibilidad.');
    } catch (e) {
      if (e is ProductoDetalleException) rethrow;
      throw ProductoDetalleException('Error al consultar stock por boutique: $e');
    }
  }

  @override
  Future<List<SucursalDisponibilidadDto>> obtenerSucursalesActivas() async {
    final uri = Uri.parse('$_baseUrl/api/v1/sucursales/activas');

    try {
      final response = await _client.get(
        uri,
        headers: {
          HttpHeaders.acceptHeader: 'application/json',
        },
      ).timeout(const Duration(seconds: 6));

      if (response.statusCode == 200) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes));
        final List<dynamic> list = decoded is List ? decoded : (decoded['value'] as List? ?? []);
        return list
            .map((s) => SucursalDisponibilidadDto.fromJson(s as Map<String, dynamic>))
            .toList();
      } else {
        throw ProductoDetalleException(
          'Error HTTP ${response.statusCode} al obtener boutiques activas.',
          codigoHttp: response.statusCode,
        );
      }
    } catch (e) {
      if (e is ProductoDetalleException) rethrow;
      throw ProductoDetalleException('Error al cargar boutiques: $e');
    }
  }

  @override
  Future<ReservaCreadaOutDto> crearReserva(
    ReservaCrearInDto datos, {
    String? token,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/v1/reservas');

    try {
      final headers = <String, String>{
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
      };
      if (token != null && token.isNotEmpty) {
        headers[HttpHeaders.authorizationHeader] = 'Bearer $token';
      }

      final response = await _client.post(
        uri,
        headers: headers,
        body: jsonEncode(datos.toJson()),
      ).timeout(const Duration(seconds: 8));

      if (response.statusCode == 200 || response.statusCode == 201) {
        final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return ReservaCreadaOutDto.fromJson(decoded);
      } else {
        String mensajeError = 'No se pudo completar la reserva en la boutique.';
        try {
          final errJson = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
          if (errJson.containsKey('detail')) {
            mensajeError = errJson['detail'].toString();
          }
        } catch (_) {}

        // 401 Unauthorized: sesión expirada → auto-redirect al login
        if (response.statusCode == 401) {
          SesionManager.instancia.notificarSesionExpirada(mensaje: mensajeError);
        }

        throw ProductoDetalleException(
          mensajeError,
          codigoHttp: response.statusCode,
        );
      }
    } on SocketException {
      throw const ProductoDetalleException('Error de conexión al procesar la reserva.');
    } on TimeoutException {
      throw const ProductoDetalleException('Tiempo de espera agotado al coordinar cita en boutique.');
    } catch (e) {
      if (e is ProductoDetalleException) rethrow;
      throw ProductoDetalleException('Error al solicitar cita en boutique: $e');
    }
  }
}
