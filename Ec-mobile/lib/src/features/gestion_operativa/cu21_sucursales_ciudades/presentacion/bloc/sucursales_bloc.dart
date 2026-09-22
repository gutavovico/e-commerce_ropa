import 'package:flutter/foundation.dart';
import '../../dominio/repositorios/sucursales_repositorio.dart';
import '../../datos/repositorios/sucursales_repositorio_impl.dart';
import '../../datos/fuentes_datos/sucursales_remoto_datasource.dart';
import 'sucursales_estado.dart';

/// Controlador / BLoC para la administracion de boutiques y ciudades territoriales.
class SucursalesBloc extends ChangeNotifier {
  final SucursalesRepositorio _repositorio;

  SucursalesBloc({SucursalesRepositorio? repositorio})
      : _repositorio = repositorio ?? SucursalesRepositorioImpl();

  SucursalesEstado _estado = const SucursalesInicial();
  SucursalesEstado get estado => _estado;

  bool get estaCargando => _estado is SucursalesCargando;

  /// Carga inicial consolidada de ciudades y sucursales.
  Future<void> cargarDatos(String token) async {
    _estado = const SucursalesCargando();
    notifyListeners();

    try {
      final ciudades = await _repositorio.obtenerCiudades(token);
      final sucursales = await _repositorio.obtenerSucursales(token);

      _estado = SucursalesCargado(
        ciudades: ciudades,
        sucursales: sucursales,
      );
      notifyListeners();
    } catch (e) {
      _estado = SucursalesError(e.toString());
      notifyListeners();
    }
  }

  /// Actualiza el filtro de ciudad activa (o null para todas).
  void seleccionarFiltroCiudad(int? idCiudad) {
    final actual = _estado;
    if (actual is SucursalesCargado) {
      _estado = actual.copyWith(
        ciudadFiltroId: () => idCiudad,
      );
      notifyListeners();
    }
  }

  /// Actualiza el termino de busqueda textual.
  void actualizarBusqueda(String query) {
    final actual = _estado;
    if (actual is SucursalesCargado) {
      _estado = actual.copyWith(
        busqueda: query,
      );
      notifyListeners();
    }
  }

  /// Actualiza el filtro de estado operativo (todas / activas / inactivas).
  void actualizarFiltroEstado(bool? activa) {
    final actual = _estado;
    if (actual is SucursalesCargado) {
      _estado = actual.copyWith(
        estadoFiltro: () => activa,
      );
      notifyListeners();
    }
  }

  /// Alterna el estado operativo de una boutique (AC-17).
  Future<void> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool nuevoEstado,
  ) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      final actualizada = await _repositorio.cambiarEstadoSucursal(
        token,
        idSucursal,
        nuevoEstado,
      );

      final nuevaLista = actual.sucursales.map((s) {
        return s.idSucursal == idSucursal ? actualizada : s;
      }).toList();

      final estadoStr = nuevoEstado ? 'activada' : 'desactivada';
      _estado = actual.copyWith(
        sucursales: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Boutique "${actualizada.nombre}" $estadoStr.',
      );
      notifyListeners();
    } on ConflictoOperacionException catch (e) {
      // Conflicto de dominio 409: retener vista y desplegar advertencia
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
    }
  }

  /// Registra una nueva boutique (AC-18).
  Future<bool> crearSucursal(
    String token, {
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  }) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return false;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      final nueva = await _repositorio.crearSucursal(
        token,
        idCiudad: idCiudad,
        nombre: nombre,
        direccion: direccion,
        telefono: telefono,
        horarioApertura: horarioApertura,
        horarioCierre: horarioCierre,
      );

      final nuevaLista = [nueva, ...actual.sucursales];
      _estado = actual.copyWith(
        sucursales: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Boutique "${nueva.nombre}" registrada con exito.',
      );
      notifyListeners();
      return true;
    } on ConflictoOperacionException catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
      return false;
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
      return false;
    }
  }

  /// Actualiza una boutique existente.
  Future<bool> actualizarSucursal(
    String token,
    int idSucursal, {
    int? idCiudad,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
  }) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return false;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      final actualizada = await _repositorio.actualizarSucursal(
        token,
        idSucursal,
        idCiudad: idCiudad,
        nombre: nombre,
        direccion: direccion,
        telefono: telefono,
        horarioApertura: horarioApertura,
        horarioCierre: horarioCierre,
      );

      final nuevaLista = actual.sucursales.map((s) {
        return s.idSucursal == idSucursal ? actualizada : s;
      }).toList();

      _estado = actual.copyWith(
        sucursales: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Boutique "${actualizada.nombre}" actualizada.',
      );
      notifyListeners();
      return true;
    } on ConflictoOperacionException catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
      return false;
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
      return false;
    }
  }

  /// Elimina una sucursal del sistema.
  Future<bool> eliminarSucursal(String token, int idSucursal) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return false;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      await _repositorio.eliminarSucursal(token, idSucursal);
      final nuevaLista =
          actual.sucursales.where((s) => s.idSucursal != idSucursal).toList();

      _estado = actual.copyWith(
        sucursales: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Sucursal eliminada exitosamente.',
      );
      notifyListeners();
      return true;
    } on ConflictoOperacionException catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
      return false;
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
      return false;
    }
  }

  /// Registra una nueva ciudad metropolitana.
  Future<bool> crearCiudad(
    String token, {
    required String nombre,
    required String pais,
  }) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return false;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      final nueva = await _repositorio.crearCiudad(
        token,
        nombre: nombre,
        pais: pais,
      );

      final nuevaLista = [...actual.ciudades, nueva];
      _estado = actual.copyWith(
        ciudades: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Ciudad "${nueva.nombre}" registrada.',
      );
      notifyListeners();
      return true;
    } on ConflictoOperacionException catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
      return false;
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
      return false;
    }
  }

  /// Elimina una ciudad territorial.
  Future<bool> eliminarCiudad(String token, int idCiudad) async {
    final actual = _estado;
    if (actual is! SucursalesCargado) return false;

    _estado = actual.copyWith(
      operacionEnCurso: true,
      mensajeError: () => null,
      mensajeExito: () => null,
    );
    notifyListeners();

    try {
      await _repositorio.eliminarCiudad(token, idCiudad);
      final nuevaLista =
          actual.ciudades.where((c) => c.idCiudad != idCiudad).toList();

      _estado = actual.copyWith(
        ciudades: nuevaLista,
        operacionEnCurso: false,
        mensajeExito: () => 'Ciudad eliminada del catalogo territorial.',
      );
      notifyListeners();
      return true;
    } on ConflictoOperacionException catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.mensaje,
      );
      notifyListeners();
      return false;
    } catch (e) {
      _estado = actual.copyWith(
        operacionEnCurso: false,
        mensajeError: () => e.toString(),
      );
      notifyListeners();
      return false;
    }
  }

  /// Limpia los mensajes visuales de retroalimentacion.
  void limpiarAlertas() {
    final actual = _estado;
    if (actual is SucursalesCargado) {
      _estado = actual.copyWith(
        mensajeError: () => null,
        mensajeExito: () => null,
      );
      notifyListeners();
    }
  }
}
