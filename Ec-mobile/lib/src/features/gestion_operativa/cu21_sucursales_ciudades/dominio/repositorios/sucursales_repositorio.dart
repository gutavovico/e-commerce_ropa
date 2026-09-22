import '../entidades/ciudad.dart';
import '../entidades/sucursal.dart';

/// Contrato abstracto del repositorio para la administracion de sucursales y ciudades.
abstract class SucursalesRepositorio {
  /// Consulta el catalogo administrativo de ciudades.
  Future<List<Ciudad>> obtenerCiudades(String token);

  /// Registra una nueva ciudad operativa.
  Future<Ciudad> crearCiudad(
    String token, {
    required String nombre,
    required String pais,
  });

  /// Elimina una ciudad sin dependencias operativas activas.
  Future<void> eliminarCiudad(String token, int idCiudad);

  /// Consulta el listado administrativo consolidado de sucursales.
  Future<List<Sucursal>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  });

  /// Registra una nueva boutique o sucursal de alta costura.
  Future<Sucursal> crearSucursal(
    String token, {
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  });

  /// Actualiza los datos de una boutique existente.
  Future<Sucursal> actualizarSucursal(
    String token,
    int idSucursal, {
    int? idCiudad,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
  });

  /// Alterna el estado activo/inactivo de una boutique.
  Future<Sucursal> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  );

  /// Elimina una sucursal sin operaciones pendientes.
  Future<void> eliminarSucursal(String token, int idSucursal);
}
