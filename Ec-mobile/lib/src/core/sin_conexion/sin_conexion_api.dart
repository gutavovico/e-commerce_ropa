import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../../api_config.dart';
import '../cliente_http_api.dart';
import '../sesion_manager.dart';
import 'modelos_sin_conexion.dart';

/// Error de la API sin conexión. `codigoHttp == null` significa que no hubo respuesta (sin red o
/// tiempo agotado): la operación se conserva y se reintenta (CU19 A1).
class SinConexionException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const SinConexionException(this.mensaje, {this.codigoHttp, this.codigo});

  bool get esDeRed => codigoHttp == null;

  @override
  String toString() => mensaje;
}

/// P2-CU14 / CU19 · Endpoints `/api/v1/sin-conexion` y `/api/v1/avisos`.
///
/// Usa `ClienteHttpApi`, que añade la cabecera `X-Tenant` de la tienda elegida.
class SinConexionApi {
  final http.Client _cliente;
  final String Function() _baseUrl;
  static const _espera = Duration(seconds: 15);

  SinConexionApi({http.Client? cliente, String Function()? baseUrl})
      : _cliente = cliente ?? ClienteHttpApi(),
        _baseUrl = baseUrl ?? (() => ApiConfig.baseUrl);

  Future<DispositivoDto> registrarDispositivo(
    String identificador, {
    required String token,
    String? tokenPush,
  }) async {
    final cuerpo = <String, dynamic>{
      'identificador': identificador,
      'plataforma': 'flutter',
    };
    if (tokenPush != null && tokenPush.isNotEmpty) {
      cuerpo['token_push'] = tokenPush;
    }
    final datos = await _post(
      '/api/v1/sin-conexion/dispositivos',
      cuerpo,
      token,
      'registrar el dispositivo',
    );
    return DispositivoDto.fromJson(datos as Map<String, dynamic>);
  }

  Future<void> registrarTokenPush(
    String identificador,
    String tokenPush, {
    required String token,
  }) async {
    await _post(
      '/api/v1/sin-conexion/dispositivos/token-push',
      {'identificador': identificador, 'token_push': tokenPush},
      token,
      'registrar el token push',
    );
  }

  /// Devuelve el JSON tal cual: se guarda entero en SQLite.
  Future<Map<String, dynamic>> descargarCatalogo(String identificador, String modo, {required String token}) async {
    final datos = await _get('/api/v1/sin-conexion/catalogo', {'dispositivo': identificador, 'modo': modo}, token,
        'descargar el catálogo');
    return datos as Map<String, dynamic>;
  }

  Future<List<ResultadoOperacionDto>> sincronizar(
    String identificador,
    List<Map<String, dynamic>> operaciones, {
    required String token,
  }) async {
    final datos = await _post('/api/v1/sin-conexion/sincronizar',
        {'dispositivo': identificador, 'operaciones': operaciones}, token, 'sincronizar');
    return [
      for (final r in ((datos as Map<String, dynamic>)['resultados'] as List? ?? const []))
        ResultadoOperacionDto.fromJson(r as Map<String, dynamic>),
    ];
  }

  Future<List<OperacionServidorDto>> operaciones(String identificador, {required String token}) async {
    final datos = await _get('/api/v1/sin-conexion/operaciones', {'dispositivo': identificador}, token,
        'consultar las operaciones');
    return [for (final o in (datos as List)) OperacionServidorDto.fromJson(o as Map<String, dynamic>)];
  }

  Future<BandejaAvisosDto> avisos({required String token}) async {
    final datos = await _get('/api/v1/avisos', const {}, token, 'consultar los avisos');
    return BandejaAvisosDto.fromJson(datos as Map<String, dynamic>);
  }

  Future<void> marcarAvisoLeido(int idAviso, {required String token}) async {
    await _post('/api/v1/avisos/$idAviso/leido', const {}, token, 'marcar el aviso');
  }

  /// `GET /api/v1/health`: comprueba que el servidor responde de verdad, no solo que hay red.
  Future<bool> servidorDisponible() async {
    try {
      final r = await _cliente.get(Uri.parse('${_baseUrl()}/api/v1/health')).timeout(const Duration(seconds: 5));
      return r.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  // ------------------------------------------------------------------------- apoyo

  Map<String, String> _cabeceras(String token) => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
        if (token.isNotEmpty) HttpHeaders.authorizationHeader: 'Bearer $token',
      };

  Future<Object?> _get(String ruta, Map<String, String> parametros, String token, String contexto) =>
      _enviar(() => _cliente
          .get(Uri.parse('${_baseUrl()}$ruta').replace(queryParameters: parametros.isEmpty ? null : parametros),
              headers: _cabeceras(token))
          .timeout(_espera), contexto);

  Future<Object?> _post(String ruta, Object cuerpo, String token, String contexto) => _enviar(
      () => _cliente.post(Uri.parse('${_baseUrl()}$ruta'), headers: _cabeceras(token), body: jsonEncode(cuerpo)).timeout(_espera),
      contexto);

  Future<Object?> _enviar(Future<http.Response> Function() peticion, String contexto) async {
    final http.Response respuesta;
    try {
      respuesta = await peticion();
    } on SocketException {
      throw SinConexionException('Sin conexión al $contexto.');
    } on TimeoutException {
      throw SinConexionException('El servidor tardó demasiado al $contexto.');
    } on http.ClientException {
      throw SinConexionException('Sin conexión al $contexto.');
    }

    final texto = utf8.decode(respuesta.bodyBytes);
    if (respuesta.statusCode >= 200 && respuesta.statusCode < 300) {
      return texto.isEmpty ? null : jsonDecode(texto);
    }
    String mensaje = 'No se pudo $contexto.';
    String? codigo;
    try {
      final error = jsonDecode(texto) as Map<String, dynamic>;
      mensaje = error['detail']?.toString() ?? mensaje;
      codigo = error['code']?.toString();
    } catch (_) {}
    if (respuesta.statusCode == 401) {
      // CU19 A5: se pide iniciar sesión; las operaciones siguen en SQLite.
      SesionManager.instancia.notificarSesionExpirada(mensaje: mensaje);
    }
    throw SinConexionException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }
}
