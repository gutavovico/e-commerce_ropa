import 'dart:convert';
import 'dart:io';
import 'package:http/http.dart' as http;
import 'package:ec_mobile/api_config.dart';
import '../modelos/ciudad_dto.dart';
import '../modelos/sucursal_dto.dart';

/// Excepcion de dominio cuando ocurre un conflicto de integridad (HTTP 409).
class ConflictoOperacionException implements Exception {
  final String mensaje;
  const ConflictoOperacionException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Excepcion de autenticacion (HTTP 401).
class NoAutorizadoException implements Exception {
  final String mensaje;
  const NoAutorizadoException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Excepcion de autorizacion / roles insuficientes (HTTP 403).
class AccesoDenegadoException implements Exception {
  final String mensaje;
  const AccesoDenegadoException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Excepcion de recurso no encontrado (HTTP 404).
class RecursoNoEncontradoException implements Exception {
  final String mensaje;
  const RecursoNoEncontradoException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Excepcion de validacion o datos invalidos (HTTP 422).
class DatosInvalidosException implements Exception {
  final String mensaje;
  const DatosInvalidosException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Excepcion generica para fallos de servidor o red.
class ServidorException implements Exception {
  final String mensaje;
  const ServidorException(this.mensaje);

  @override
  String toString() => mensaje;
}

/// Contrato del datasource remoto HTTP.
abstract class SucursalesRemotoDataSource {
  Future<List<CiudadDto>> obtenerCiudades(String token);
  Future<CiudadDto> crearCiudad(String token, Map<String, dynamic> datos);
  Future<void> eliminarCiudad(String token, int idCiudad);

  Future<List<SucursalDto>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  });
  Future<SucursalDto> crearSucursal(String token, Map<String, dynamic> datos);
  Future<SucursalDto> actualizarSucursal(
    String token,
    int idSucursal,
    Map<String, dynamic> datos,
  );
  Future<SucursalDto> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  );
  Future<void> eliminarSucursal(String token, int idSucursal);
}

/// Implementacion concreta del datasource HTTP utilizando package:http.
class SucursalesRemotoDataSourceImpl implements SucursalesRemotoDataSource {
  final http.Client _client;
  final String _baseUrl;

  SucursalesRemotoDataSourceImpl({
    http.Client? client,
    String? baseUrl,
  })  : _client = client ?? http.Client(),
        _baseUrl = baseUrl ?? ApiConfig.baseUrl;

  Map<String, String> _headers(String token) => {
        HttpHeaders.contentTypeHeader: 'application/json',
        HttpHeaders.acceptHeader: 'application/json',
        HttpHeaders.authorizationHeader: 'Bearer $token',
      };

  Never _procesarError(http.Response response) {
    String detalle = 'Error en la solicitud';
    try {
      final decoded = jsonDecode(response.body);
      if (decoded is Map && decoded.containsKey('detail')) {
        detalle = decoded['detail'].toString();
      }
    } catch (_) {
      detalle = response.reasonPhrase ?? 'Error HTTP ${response.statusCode}';
    }

    if (response.statusCode == 401) {
      throw NoAutorizadoException(
          'Sesion expirada o invalida. Inicie sesion nuevamente.');
    } else if (response.statusCode == 403) {
      throw AccesoDenegadoException(
          'Acceso denegado: se requieren permisos de administrador corporativo.');
    } else if (response.statusCode == 404) {
      throw RecursoNoEncontradoException(detalle);
    } else if (response.statusCode == 409) {
      throw ConflictoOperacionException(detalle);
    } else if (response.statusCode == 422) {
      throw DatosInvalidosException(detalle);
    } else {
      throw ServidorException(detalle);
    }
  }

  @override
  Future<List<CiudadDto>> obtenerCiudades(String token) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/ciudades');
    final response = await _client.get(uri, headers: _headers(token));

    if (response.statusCode == 200) {
      final List<dynamic> lista = jsonDecode(response.body) as List<dynamic>;
      return lista
          .map((item) => CiudadDto.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    _procesarError(response);
  }

  @override
  Future<CiudadDto> crearCiudad(
    String token,
    Map<String, dynamic> datos,
  ) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/ciudades');
    final response = await _client.post(
      uri,
      headers: _headers(token),
      body: jsonEncode(datos),
    );

    if (response.statusCode == 201) {
      return CiudadDto.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    _procesarError(response);
  }

  @override
  Future<void> eliminarCiudad(String token, int idCiudad) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/ciudades/$idCiudad');
    final response = await _client.delete(uri, headers: _headers(token));

    if (response.statusCode == 200) {
      return;
    }
    _procesarError(response);
  }

  @override
  Future<List<SucursalDto>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  }) async {
    final queryParams = <String, String>{};
    if (idCiudad != null) queryParams['id_ciudad'] = idCiudad.toString();
    if (activa != null) queryParams['activa'] = activa.toString();
    if (q != null && q.isNotEmpty) queryParams['q'] = q;

    final uri = Uri.parse('$_baseUrl/api/v1/admin/sucursales')
        .replace(queryParameters: queryParams.isEmpty ? null : queryParams);
    final response = await _client.get(uri, headers: _headers(token));

    if (response.statusCode == 200) {
      final List<dynamic> lista = jsonDecode(response.body) as List<dynamic>;
      return lista
          .map((item) => SucursalDto.fromJson(item as Map<String, dynamic>))
          .toList();
    }
    _procesarError(response);
  }

  @override
  Future<SucursalDto> crearSucursal(
    String token,
    Map<String, dynamic> datos,
  ) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/sucursales');
    final response = await _client.post(
      uri,
      headers: _headers(token),
      body: jsonEncode(datos),
    );

    if (response.statusCode == 201) {
      return SucursalDto.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    _procesarError(response);
  }

  @override
  Future<SucursalDto> actualizarSucursal(
    String token,
    int idSucursal,
    Map<String, dynamic> datos,
  ) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/sucursales/$idSucursal');
    final response = await _client.put(
      uri,
      headers: _headers(token),
      body: jsonEncode(datos),
    );

    if (response.statusCode == 200) {
      return SucursalDto.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    _procesarError(response);
  }

  @override
  Future<SucursalDto> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  ) async {
    final uri =
        Uri.parse('$_baseUrl/api/v1/admin/sucursales/$idSucursal/estado');
    final response = await _client.patch(
      uri,
      headers: _headers(token),
      body: jsonEncode({'activa': activa}),
    );

    if (response.statusCode == 200) {
      return SucursalDto.fromJson(
          jsonDecode(response.body) as Map<String, dynamic>);
    }
    _procesarError(response);
  }

  @override
  Future<void> eliminarSucursal(String token, int idSucursal) async {
    final uri = Uri.parse('$_baseUrl/api/v1/admin/sucursales/$idSucursal');
    final response = await _client.delete(uri, headers: _headers(token));

    if (response.statusCode == 200) {
      return;
    }
    _procesarError(response);
  }
}
