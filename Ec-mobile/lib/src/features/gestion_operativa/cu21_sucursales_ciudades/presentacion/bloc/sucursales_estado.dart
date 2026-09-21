import '../../dominio/entidades/ciudad.dart';
import '../../dominio/entidades/sucursal.dart';

/// Jerarquia de estados sellados inmutables para el flujo de administracion territorial.
sealed class SucursalesEstado {
  const SucursalesEstado();
}

/// Estado inicial previo a cualquier peticion de red.
class SucursalesInicial extends SucursalesEstado {
  const SucursalesInicial();
}

/// Estado de carga mientras se consultan las ciudades y sucursales.
class SucursalesCargando extends SucursalesEstado {
  const SucursalesCargando();
}

/// Estado con catalogos cargados y soporte de filtrado reactivo y operaciones atómicas.
class SucursalesCargado extends SucursalesEstado {
  final List<Ciudad> ciudades;
  final List<Sucursal> sucursales;
  final int? ciudadFiltroId;
  final bool? estadoFiltro;
  final String busqueda;
  final String? mensajeExito;
  final String? mensajeError;
  final bool operacionEnCurso;

  const SucursalesCargado({
    required this.ciudades,
    required this.sucursales,
    this.ciudadFiltroId,
    this.estadoFiltro,
    this.busqueda = '',
    this.mensajeExito,
    this.mensajeError,
    this.operacionEnCurso = false,
  });

  /// Lista de sucursales filtrada en memoria segun los criterios seleccionados.
  List<Sucursal> get sucursalesFiltradas {
    final query = busqueda.trim().toLowerCase();
    return sucursales.where((s) {
      // Filtro por ciudad
      if (ciudadFiltroId != null && s.idCiudad != ciudadFiltroId) {
        return false;
      }
      // Filtro por estado activo/inactivo
      if (estadoFiltro != null && s.activa != estadoFiltro) {
        return false;
      }
      // Filtro por texto
      if (query.isNotEmpty) {
        final enNombre = s.nombre.toLowerCase().contains(query);
        final enDireccion = s.direccion.toLowerCase().contains(query);
        final enCiudad = s.ciudadNombre.toLowerCase().contains(query);
        if (!enNombre && !enDireccion && !enCiudad) {
          return false;
        }
      }
      return true;
    }).toList();
  }

  int get totalBoutiques => sucursales.length;
  int get totalActivas => sucursales.where((s) => s.activa).length;
  int get totalInactivas => sucursales.where((s) => !s.activa).length;

  SucursalesCargado copyWith({
    List<Ciudad>? ciudades,
    List<Sucursal>? sucursales,
    int? Function()? ciudadFiltroId,
    bool? Function()? estadoFiltro,
    String? busqueda,
    String? Function()? mensajeExito,
    String? Function()? mensajeError,
    bool? operacionEnCurso,
  }) {
    return SucursalesCargado(
      ciudades: ciudades ?? this.ciudades,
      sucursales: sucursales ?? this.sucursales,
      ciudadFiltroId:
          ciudadFiltroId != null ? ciudadFiltroId() : this.ciudadFiltroId,
      estadoFiltro: estadoFiltro != null ? estadoFiltro() : this.estadoFiltro,
      busqueda: busqueda ?? this.busqueda,
      mensajeExito: mensajeExito != null ? mensajeExito() : this.mensajeExito,
      mensajeError: mensajeError != null ? mensajeError() : this.mensajeError,
      operacionEnCurso: operacionEnCurso ?? this.operacionEnCurso,
    );
  }
}

/// Estado de error general no recuperable o fallo critico de red.
class SucursalesError extends SucursalesEstado {
  final String mensaje;
  final String? codigo;

  const SucursalesError(this.mensaje, {this.codigo});
}
