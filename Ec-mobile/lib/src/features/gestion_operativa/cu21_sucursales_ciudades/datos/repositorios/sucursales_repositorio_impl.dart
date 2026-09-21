import '../../dominio/entidades/ciudad.dart';
import '../../dominio/entidades/sucursal.dart';
import '../../dominio/repositorios/sucursales_repositorio.dart';
import '../fuentes_datos/sucursales_remoto_datasource.dart';

/// Implementacion concreta de SucursalesRepositorio consumiendo el datasource remoto.
class SucursalesRepositorioImpl implements SucursalesRepositorio {
  final SucursalesRemotoDataSource _remotoDataSource;

  SucursalesRepositorioImpl({
    SucursalesRemotoDataSource? remotoDataSource,
  }) : _remotoDataSource =
            remotoDataSource ?? SucursalesRemotoDataSourceImpl();

  @override
  Future<List<Ciudad>> obtenerCiudades(String token) async {
    final dtos = await _remotoDataSource.obtenerCiudades(token);
    return dtos.map((d) => d.toEntity()).toList();
  }

  @override
  Future<Ciudad> crearCiudad(
    String token, {
    required String nombre,
    required String pais,
  }) async {
    final payload = {
      'nombre': nombre.trim(),
      'pais': pais.trim(),
    };
    final dto = await _remotoDataSource.crearCiudad(token, payload);
    return dto.toEntity();
  }

  @override
  Future<void> eliminarCiudad(String token, int idCiudad) async {
    await _remotoDataSource.eliminarCiudad(token, idCiudad);
  }

  @override
  Future<List<Sucursal>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  }) async {
    final dtos = await _remotoDataSource.obtenerSucursales(
      token,
      idCiudad: idCiudad,
      activa: activa,
      q: q,
    );
    return dtos.map((d) => d.toEntity()).toList();
  }

  @override
  Future<Sucursal> crearSucursal(
    String token, {
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  }) async {
    final payload = {
      'id_ciudad': idCiudad,
      'nombre': nombre.trim(),
      'direccion': direccion.trim(),
      'telefono': telefono != null && telefono.trim().isNotEmpty
          ? telefono.trim()
          : null,
      'horario_apertura': horarioApertura.trim(),
      'horario_cierre': horarioCierre.trim(),
    };
    final dto = await _remotoDataSource.crearSucursal(token, payload);
    return dto.toEntity();
  }

  @override
  Future<Sucursal> actualizarSucursal(
    String token,
    int idSucursal, {
    int? idCiudad,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
  }) async {
    final payload = <String, dynamic>{};
    if (idCiudad != null) payload['id_ciudad'] = idCiudad;
    if (nombre != null) payload['nombre'] = nombre.trim();
    if (direccion != null) payload['direccion'] = direccion.trim();
    if (telefono != null) {
      payload['telefono'] =
          telefono.trim().isNotEmpty ? telefono.trim() : null;
    }
    if (horarioApertura != null) {
      payload['horario_apertura'] = horarioApertura.trim();
    }
    if (horarioCierre != null) {
      payload['horario_cierre'] = horarioCierre.trim();
    }

    final dto =
        await _remotoDataSource.actualizarSucursal(token, idSucursal, payload);
    return dto.toEntity();
  }

  @override
  Future<Sucursal> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  ) async {
    final dto = await _remotoDataSource.cambiarEstadoSucursal(
      token,
      idSucursal,
      activa,
    );
    return dto.toEntity();
  }

  @override
  Future<void> eliminarSucursal(String token, int idSucursal) async {
    await _remotoDataSource.eliminarSucursal(token, idSucursal);
  }
}
