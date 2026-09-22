import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../../../../../api_config.dart';
import '../../../../../core/sesion_manager.dart';
import '../modelos/carrito_dto.dart';

/// Excepción de dominio de la Bolsa de Compra.
///
/// Conserva el `código` que devuelve el backend en `{detail, code}` para que la capa de
/// presentación pueda distinguir, por ejemplo, unas existencias agotadas de una bolsa vacía
/// sin tener que interpretar el texto del mensaje.
class CarritoException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const CarritoException(this.mensaje, {this.codigoHttp, this.codigo});

  bool get esStockInsuficiente => codigo == 'STOCK_INSUFICIENTE';
  bool get esCarritoVacio => codigo == 'CARRITO_VACIO';
  bool get esCuponInvalido => codigo == 'CUPON_INVALIDO';

  @override
  String toString() => mensaje;
}

abstract class CarritoApi {
  Future<CarritoDto> obtenerCarrito({required String token});
  Future<CarritoDto> agregarItem(ItemAgregarInDto datos, {required String token});
  Future<CarritoDto> actualizarCantidad(
    int idCarritoDetalle,
    int cantidad, {
    required String token,
  });
  Future<CarritoDto> eliminarItem(int idCarritoDetalle, {required String token});
  Future<VentaCreadaDto> tramitarPedido(CheckoutInDto datos, {required String token});
  Future<List<BoutiqueRecogidaDto>> obtenerBoutiques();
}

class CarritoApiImpl implements CarritoApi {
  final http.Client _client;
  final String? _customBaseUrl;

  CarritoApiImpl({http.Client? client, String? customBaseUrl})
      : _client = client ?? http.Client(),
        _customBaseUrl = customBaseUrl;

  String get _baseUrl => _customBaseUrl ?? ApiConfig.baseUrl;

  Map<String, String> _cabeceras(String token) => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
        if (token.isNotEmpty) HttpHeaders.authorizationHeader: 'Bearer $token',
      };

  /// Interpreta la respuesta del backend y traduce los errores a excepciones de dominio.
  ///
  /// Un HTTP 401 notifica al [SesionManager], que devuelve al cliente al login desde la raíz de
  /// la aplicación. Sin esa notificación el usuario vería un error genérico sin saber que su
  /// sesión caducó.
  Map<String, dynamic> _procesar(http.Response respuesta, String mensajeGenerico) {
    final cuerpo = utf8.decode(respuesta.bodyBytes);

    if (respuesta.statusCode >= 200 && respuesta.statusCode < 300) {
      return jsonDecode(cuerpo) as Map<String, dynamic>;
    }

    String mensaje = mensajeGenerico;
    String? codigo;
    try {
      final error = jsonDecode(cuerpo) as Map<String, dynamic>;
      if (error['detail'] != null) mensaje = error['detail'].toString();
      if (error['code'] != null) codigo = error['code'].toString();
    } catch (_) {
      // Respuesta sin JSON válido: se conserva el mensaje genérico.
    }

    if (respuesta.statusCode == 401) {
      SesionManager.instancia.notificarSesionExpirada(mensaje: mensaje);
    }

    throw CarritoException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }

  Future<T> _ejecutar<T>(Future<T> Function() operacion, String contexto) async {
    try {
      return await operacion();
    } on CarritoException {
      rethrow;
    } on SocketException {
      throw CarritoException('No se pudo conectar con el atelier al $contexto.');
    } on TimeoutException {
      throw CarritoException('El atelier tardó demasiado en responder al $contexto.');
    } catch (e) {
      throw CarritoException('Error inesperado al $contexto: $e');
    }
  }

  @override
  Future<CarritoDto> obtenerCarrito({required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .get(Uri.parse('$_baseUrl/api/v1/carrito'), headers: _cabeceras(token))
          .timeout(const Duration(seconds: 8));

      return CarritoDto.fromJson(
        _procesar(respuesta, 'No fue posible cargar tu bolsa de compra.'),
      );
    }, 'consultar tu bolsa');
  }

  @override
  Future<CarritoDto> agregarItem(ItemAgregarInDto datos, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/carrito/items'),
            headers: _cabeceras(token),
            body: jsonEncode(datos.toJson()),
          )
          .timeout(const Duration(seconds: 8));

      return CarritoDto.fromJson(
        _procesar(respuesta, 'No fue posible añadir la prenda a tu bolsa.'),
      );
    }, 'añadir la prenda');
  }

  @override
  Future<CarritoDto> actualizarCantidad(
    int idCarritoDetalle,
    int cantidad, {
    required String token,
  }) {
    return _ejecutar(() async {
      final respuesta = await _client
          .patch(
            Uri.parse('$_baseUrl/api/v1/carrito/items/$idCarritoDetalle'),
            headers: _cabeceras(token),
            // Cantidad absoluta, no incremental: la operación es idempotente ante doble toque.
            body: jsonEncode({'cantidad': cantidad}),
          )
          .timeout(const Duration(seconds: 8));

      return CarritoDto.fromJson(
        _procesar(respuesta, 'No fue posible actualizar la cantidad.'),
      );
    }, 'actualizar la cantidad');
  }

  @override
  Future<CarritoDto> eliminarItem(int idCarritoDetalle, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .delete(
            Uri.parse('$_baseUrl/api/v1/carrito/items/$idCarritoDetalle'),
            headers: _cabeceras(token),
          )
          .timeout(const Duration(seconds: 8));

      return CarritoDto.fromJson(
        _procesar(respuesta, 'No fue posible retirar la prenda de tu bolsa.'),
      );
    }, 'retirar la prenda');
  }

  @override
  Future<VentaCreadaDto> tramitarPedido(CheckoutInDto datos, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/ventas/checkout'),
            headers: _cabeceras(token),
            body: jsonEncode(datos.toJson()),
          )
          .timeout(const Duration(seconds: 12));

      return VentaCreadaDto.fromJson(
        _procesar(respuesta, 'No fue posible tramitar tu pedido.'),
      );
    }, 'tramitar el pedido');
  }

  @override
  Future<List<BoutiqueRecogidaDto>> obtenerBoutiques() {
    return _ejecutar(() async {
      final respuesta = await _client
          .get(
            Uri.parse('$_baseUrl/api/v1/sucursales/activas'),
            headers: {HttpHeaders.acceptHeader: 'application/json'},
          )
          .timeout(const Duration(seconds: 8));

      if (respuesta.statusCode == 200) {
        final lista = jsonDecode(utf8.decode(respuesta.bodyBytes)) as List<dynamic>;
        return lista
            .map((b) => BoutiqueRecogidaDto.fromJson(b as Map<String, dynamic>))
            .toList();
      }

      // El directorio de boutiques es accesorio: si falla, la pantalla muestra su estado vacío
      // en lugar de impedir toda la gestión de la bolsa.
      return <BoutiqueRecogidaDto>[];
    }, 'consultar las boutiques');
  }
}
