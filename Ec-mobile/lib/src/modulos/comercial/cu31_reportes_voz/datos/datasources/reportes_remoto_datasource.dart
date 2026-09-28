import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import 'package:ec_mobile/src/core/sesion_manager.dart';
import '../modelos/reportes_voz_dto.dart';

/// Respuesta binaria al exportar un reporte
class ArchivoReporteDescargado {
  final Uint8List bytes;
  final String nombreArchivo;
  final String mediaType;

  const ArchivoReporteDescargado({
    required this.bytes,
    required this.nombreArchivo,
    required this.mediaType,
  });
}

/// Datasource remoto para comunicarse con los endpoints FastAPI de CU31
class ReportesRemotoDatasource {
  final http.Client _client;

  ReportesRemotoDatasource({http.Client? client})
      : _client = client ?? http.Client();

  Map<String, String> _cabeceras(String token) {
    final map = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    if (token.isNotEmpty) {
      map['Authorization'] = 'Bearer $token';
    }
    return map;
  }

  void _manejarErrorHttp(http.Response response) {
    if (response.statusCode == 401) {
      SesionManager.instancia.notificarSesionExpirada(
        mensaje: 'Tu sesion ha expirado. Inicia sesion nuevamente.',
      );
      throw Exception('Sesion expirada (401).');
    }

    String detalle = 'Error en el servidor (${response.statusCode})';
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded['detail'] != null) {
        detalle = decoded['detail'].toString();
      }
    } catch (_) {
      // Ignorar fallback a mensaje generico
    }
    throw Exception(detalle);
  }

  Future<ComandoVozOut> interpretarComandoVoz(
    String token,
    ComandoVozIn peticion,
  ) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/v1/admin/reportes/interpretar-voz');
    final response = await _client.post(
      url,
      headers: _cabeceras(token),
      body: jsonEncode(peticion.toJson()),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ComandoVozOut.fromJson(decoded);
    }

    _manejarErrorHttp(response);
    throw Exception('Fallo inesperado al interpretar comando de voz.');
  }

  Future<ReportePrevisualizacionDto> previsualizarReporte(
    String token,
    ReporteFiltrosDto filtros,
  ) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/v1/admin/reportes/previsualizar');
    final response = await _client.post(
      url,
      headers: _cabeceras(token),
      body: jsonEncode(filtros.toJson()),
    );

    if (response.statusCode == 200) {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      return ReportePrevisualizacionDto.fromJson(decoded);
    }

    _manejarErrorHttp(response);
    throw Exception('Fallo inesperado al previsualizar reporte.');
  }

  Future<ArchivoReporteDescargado> exportarReporte(
    String token,
    ReporteFiltrosDto filtros,
  ) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/v1/admin/reportes/exportar');
    final headers = _cabeceras(token);
    headers['Accept'] = '*/*';

    final response = await _client.post(
      url,
      headers: headers,
      body: jsonEncode(filtros.toJson()),
    );

    if (response.statusCode == 200) {
      String nombreArchivo = 'reporte_${filtros.modulo}_${DateTime.now().millisecondsSinceEpoch}';
      final ext = filtros.formato == 'excel' ? 'xlsx' : filtros.formato;
      nombreArchivo = '$nombreArchivo.$ext';

      final contentDisposition = response.headers['content-disposition'];
      if (contentDisposition != null) {
        final match = RegExp(r'filename="?([^";]+)"?').firstMatch(contentDisposition);
        if (match != null && match.group(1) != null) {
          nombreArchivo = match.group(1)!;
        }
      }

      final mediaType = response.headers['content-type'] ?? 'application/octet-stream';

      return ArchivoReporteDescargado(
        bytes: response.bodyBytes,
        nombreArchivo: nombreArchivo,
        mediaType: mediaType,
      );
    }

    _manejarErrorHttp(response);
    throw Exception('Fallo inesperado al exportar archivo binario.');
  }

  Future<List<SucursalOpcionDto>> obtenerSucursales(String token) async {
    final url = Uri.parse('${ApiConfig.baseUrl}/api/v1/admin/sucursales');
    try {
      final response = await _client.get(url, headers: _cabeceras(token));
      if (response.statusCode == 200) {
        final lista = jsonDecode(utf8.decode(response.bodyBytes)) as List<dynamic>;
        return lista
            .map((item) => SucursalOpcionDto.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    } catch (_) {
      // Fallback a lista vacia si no hay red o endpoint restringido
    }
    return const [];
  }
}
