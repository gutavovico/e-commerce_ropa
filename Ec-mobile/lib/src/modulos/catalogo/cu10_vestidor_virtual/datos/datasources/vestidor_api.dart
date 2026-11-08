import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import '../../../../../../api_config.dart';
import '../../../../../core/sesion_manager.dart';
import '../modelos/vestidor_dto.dart';

/// Excepción de dominio de CU10. Conserva el `code` del backend (`{detail, code}`).
class VestidorException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const VestidorException(this.mensaje, {this.codigoHttp, this.codigo});

  /// Decart no está configurado, no responde o no tiene créditos: activa el fallback al Motor 1.
  bool get esDecartNoDisponible => codigoHttp == 503;
  bool get esSesionExpirada => codigoHttp == 401;

  @override
  String toString() => mensaje;
}

abstract class VestidorApi {
  /// `POST /api/v1/vestidor/token?canal=movil` (sin cuerpo).
  Future<TokenVestidorDto> obtenerTokenDecart({required String token});

  /// `POST /api/v1/vestidor/sesion`.
  Future<SesionVestidorDto> registrarSesion(SesionVestidorCrearDto datos, {required String token});

  /// Descarga el recurso visual de la prenda (`modelo_ar_url` ya resuelto a URL absoluta).
  Future<Uint8List> descargarRecurso(String url);
}

class VestidorApiImpl implements VestidorApi {
  final http.Client _client;
  final String? _customBaseUrl;

  VestidorApiImpl({http.Client? client, String? customBaseUrl})
      : _client = client ?? http.Client(),
        _customBaseUrl = customBaseUrl;

  String get _baseUrl => _customBaseUrl ?? ApiConfig.baseUrl;

  Map<String, String> _cabeceras(String token) => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
        if (token.isNotEmpty) HttpHeaders.authorizationHeader: 'Bearer $token',
      };

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

    throw VestidorException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }

  Future<T> _ejecutar<T>(Future<T> Function() operacion, String contexto) async {
    try {
      return await operacion();
    } on VestidorException {
      rethrow;
    } on SocketException {
      throw VestidorException('No se pudo conectar con el atelier al $contexto.');
    } on TimeoutException {
      throw VestidorException('El atelier tardó demasiado en responder al $contexto.');
    } catch (e) {
      throw VestidorException('Error inesperado al $contexto: $e');
    }
  }

  @override
  Future<TokenVestidorDto> obtenerTokenDecart({required String token}) {
    return _ejecutar(() async {
      // El backend emite el token sin restricción de origen para el canal móvil: el WebView
      // carga la página de Decart como asset local y su `Origin` es `null`.
      final respuesta = await _client
          .post(Uri.parse('$_baseUrl/api/v1/vestidor/token?canal=movil'), headers: _cabeceras(token))
          .timeout(const Duration(seconds: 15));

      return TokenVestidorDto.fromJson(
        _procesar(respuesta, 'El modo realista no está disponible en este momento.'),
      );
    }, 'solicitar el modo realista');
  }

  @override
  Future<SesionVestidorDto> registrarSesion(SesionVestidorCrearDto datos, {required String token}) {
    return _ejecutar(() async {
      final respuesta = await _client
          .post(
            Uri.parse('$_baseUrl/api/v1/vestidor/sesion'),
            headers: _cabeceras(token),
            body: jsonEncode(datos.toJson()),
          )
          .timeout(const Duration(seconds: 10));

      return SesionVestidorDto.fromJson(
        _procesar(respuesta, 'No fue posible registrar la sesión del vestidor.'),
      );
    }, 'registrar la sesión del vestidor');
  }

  @override
  Future<Uint8List> descargarRecurso(String url) {
    return _ejecutar(() async {
      final respuesta = await _client.get(Uri.parse(url)).timeout(const Duration(seconds: 15));
      if (respuesta.statusCode != 200) {
        throw VestidorException(
          'No se pudo descargar la imagen de la prenda (HTTP ${respuesta.statusCode}).',
          codigoHttp: respuesta.statusCode,
        );
      }
      return respuesta.bodyBytes;
    }, 'descargar la imagen de la prenda');
  }
}
