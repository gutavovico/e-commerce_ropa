/// Entidad inmutable de dominio para Ciudades Operativas.
class Ciudad {
  final int idCiudad;
  final String nombre;
  final String pais;
  final DateTime creadoEn;
  final int totalSucursales;

  const Ciudad({
    required this.idCiudad,
    required this.nombre,
    required this.pais,
    required this.creadoEn,
    required this.totalSucursales,
  });

  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      other is Ciudad &&
          runtimeType == other.runtimeType &&
          idCiudad == other.idCiudad &&
          nombre == other.nombre &&
          pais == other.pais &&
          totalSucursales == other.totalSucursales;

  @override
  int get hashCode =>
      idCiudad.hashCode ^
      nombre.hashCode ^
      pais.hashCode ^
      totalSucursales.hashCode;
}
