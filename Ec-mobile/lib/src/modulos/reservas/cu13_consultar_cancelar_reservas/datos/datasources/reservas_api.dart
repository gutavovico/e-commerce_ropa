import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../../../../../api_config.dart';
import '../../../../../core/sesion_manager.dart';
import '../modelos/reserva_dto.dart';

/// Excepción de dominio de CU13/CU14.
///
/// Conserva el `código` que devuelve el backend en `{detail, code}`, igual que `PagoException`.
class ReservaException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const ReservaException(this.mensaje, {this.codigoHttp, this.codigo});

  bool get esNoCancelable => codigo == 'RESERVA_NO_CANCELABLE';
  bool get esAjena => codigo == 'RESERVA_AJENA';
  bool get esVencida => codigo == 'RESERVA_VENCIDA';

  @override
  String toString() => mensaje;
}

abstract class ReservasApi {
  Future<MisReservasDto> obtenerMisReservas({required String token});
  Future<ReservaDto> cancelarReserva(int idReserva, String motivo, {required String token});
}

class ReservasApiImpl implements ReservasApi {
  final http.Client _client;
  final String? _customBaseUrl;

  ReservasApiImpl({http.Client? client, String? customBaseUrl})
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

    throw ReservaException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }

  Future<T> _ejecutar<T>(Future<T> Function() operacion, String contexto) async {
    try {
      return await operacion();
    } on ReservaException {
      rethrow;
    } on SocketException {
      throw ReservaException('No se pudo conectar con el atelier al $contexto.');
    } on TimeoutException {
      throw ReservaException('El atelier tardó demasiado en responder al $contexto.');
    } catch (e) {
      throw ReservaException('Error inesperado al $contexto: $e');
    }
  }

  @override
  Future<MisReservasDto> obtenerMisReservas({required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .get(
            Uri.parse('$_baseUrl/api/v1/reservas/mias'),
            headers: _cabeceras(token),
          )
          .timeout(const Duration(seconds: 8));

      return MisReservasDto.fromJson(
        _procesar(respuesta, 'No fue posible cargar tus reservas.'),
      );
    }, 'consultar tus reservas');
  }

  @override
  Future<ReservaDto> cancelarReserva(int idReserva, String motivo, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/reservas/$idReserva/cancelar'),
            headers: _cabeceras(token),
            body: jsonEncode({'motivo': motivo}),
          )
          .timeout(const Duration(seconds: 10));

      return ReservaDto.fromJson(
        _procesar(respuesta, 'No fue posible cancelar la reserva.'),
      );
    }, 'cancelar la reserva');
  }
}
