import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../../../../../api_config.dart';
import '../../../../../core/sesion_manager.dart';
import '../modelos/pago_dto.dart';

/// Excepción de dominio de CU16.
///
/// Conserva el `código` que devuelve el backend en `{detail, code}` para que la capa de
/// presentación distinga, por ejemplo, un rechazo de pasarela de una orden ya expirada, sin
/// tener que interpretar el texto del mensaje.
class PagoException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const PagoException(this.mensaje, {this.codigoHttp, this.codigo});

  bool get esPagoRechazado => codigoHttp == 402;
  bool get esOrdenExpirada => codigo == 'ORDEN_EXPIRADA';
  bool get esOrdenYaLiquidada => codigo == 'VENTA_YA_LIQUIDADA';

  @override
  String toString() => mensaje;
}

abstract class PagoApi {
  Future<ResumenPagoDto> obtenerResumenPago(int idVenta, {required String token});

  /// Abre un `PaymentIntent` en Stripe y devuelve su `client_secret`. No recibe ningún dato de
  /// tarjeta: el backend nunca ve el PAN ni el CVV.
  Future<PagoIntentoOutDto> iniciarPago(PagoIniciarInDto datos, {required String token});

  /// Verifica y cierra un cobro digital ya confirmado con Stripe. El servidor decide el
  /// desenlace según lo que Stripe le devuelva, nunca según lo que este cliente reporte.
  Future<PagoConfirmadoDto> confirmarPago(int idPago, {required String token});
}

class PagoApiImpl implements PagoApi {
  final http.Client _client;
  final String? _customBaseUrl;

  PagoApiImpl({http.Client? client, String? customBaseUrl})
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
  /// la aplicación.
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

    throw PagoException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }

  Future<T> _ejecutar<T>(Future<T> Function() operacion, String contexto) async {
    try {
      return await operacion();
    } on PagoException {
      rethrow;
    } on SocketException {
      throw PagoException('No se pudo conectar con el atelier al $contexto.');
    } on TimeoutException {
      throw PagoException('El atelier tardó demasiado en responder al $contexto.');
    } catch (e) {
      throw PagoException('Error inesperado al $contexto: $e');
    }
  }

  @override
  Future<ResumenPagoDto> obtenerResumenPago(int idVenta, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .get(
            Uri.parse('$_baseUrl/api/v1/ventas/$idVenta/resumen-pago'),
            headers: _cabeceras(token),
          )
          .timeout(const Duration(seconds: 8));

      return ResumenPagoDto.fromJson(
        _procesar(respuesta, 'No fue posible cargar el resumen de tu orden.'),
      );
    }, 'consultar el resumen de pago');
  }

  @override
  Future<PagoIntentoOutDto> iniciarPago(PagoIniciarInDto datos, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/pagos/intentos'),
            headers: _cabeceras(token),
            body: jsonEncode(datos.toJson()),
          )
          .timeout(const Duration(seconds: 12));

      return PagoIntentoOutDto.fromJson(
        _procesar(respuesta, 'No fue posible iniciar tu pago.'),
      );
    }, 'iniciar el pago');
  }

  @override
  Future<PagoConfirmadoDto> confirmarPago(int idPago, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/pagos/$idPago/confirmar'),
            headers: _cabeceras(token),
          )
          .timeout(const Duration(seconds: 12));

      return PagoConfirmadoDto.fromJson(
        _procesar(respuesta, 'No fue posible confirmar tu pago.'),
      );
    }, 'confirmar el pago');
  }
}
