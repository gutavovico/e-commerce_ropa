/// Entidad inmutable de dominio para Boutiques y Sucursales.
class Sucursal {
  final int idSucursal;
  final int idCiudad;
  final String ciudadNombre;
  final String nombre;
  final String direccion;
  final String? telefono;
  final String horarioApertura;
  final String horarioCierre;
  final bool activa;
  final DateTime creadoEn;
  final int totalEmpleados;
  final int totalPrendasStock;
  final int reservasActivasConteo;

  const Sucursal({
    required this.idSucursal,
    required this.idCiudad,
    required this.ciudadNombre,
    required this.nombre,
    required this.direccion,
    this.telefono,
    required this.horarioApertura,
    required this.horarioCierre,
    required this.activa,
    required this.creadoEn,
    required this.totalEmpleados,
    required this.totalPrendasStock,
    required this.reservasActivasConteo,
  });

  Sucursal copyWith({
    int? idSucursal,
    int? idCiudad,
    String? ciudadNombre,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
    bool? activa,
    DateTime? creadoEn,
    int? totalEmpleados,
    int? totalPrendasStock,
    int? reservasActivasConteo,
  }) {
    return Sucursal(
      idSucursal: idSucursal ?? this.idSucursal,
      idCiudad: idCiudad ?? this.idCiudad,
      ciudadNombre: ciudadNombre ?? this.ciudadNombre,
      nombre: nombre ?? this.nombre,
      direccion: direccion ?? this.direccion,
      telefono: telefono ?? this.telefono,
      horarioApertura: horarioApertura ?? this.horarioApertura,
      horarioCierre: horarioCierre ?? this.horarioCierre,
      activa: activa ?? this.activa,
      creadoEn: creadoEn ?? this.creadoEn,
      totalEmpleados: totalEmpleados ?? this.totalEmpleados,
      totalPrendasStock: totalPrendasStock ?? this.totalPrendasStock,
      reservasActivasConteo:
          reservasActivasConteo ?? this.reservasActivasConteo,
    );
  }

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Sucursal &&
          runtimeType == other.runtimeType &&
          idSucursal == other.idSucursal &&
          activa == other.activa &&
          nombre == other.nombre;

  @override
  int get hashCode => idSucursal.hashCode ^ activa.hashCode ^ nombre.hashCode;
}
