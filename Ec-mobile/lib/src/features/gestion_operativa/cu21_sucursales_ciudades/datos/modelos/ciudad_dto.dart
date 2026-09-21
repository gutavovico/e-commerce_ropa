import '../../dominio/entidades/ciudad.dart';

/// DTO para serializacion y deserializacion de ciudades territoriales.
class CiudadDto {
  final int idCiudad;
  final String nombre;
  final String pais;
  final String creadoEn;
  final int totalSucursales;

  const CiudadDto({
    required this.idCiudad,
    required this.nombre,
    required this.pais,
    required this.creadoEn,
    required this.totalSucursales,
  });

  factory CiudadDto.fromJson(Map<String, dynamic> json) {
    return CiudadDto(
      idCiudad: json['id_ciudad'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      pais: json['pais'] as String? ?? '',
      creadoEn: json['creado_en'] as String? ?? '',
      totalSucursales: json['total_sucursales'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_ciudad': idCiudad,
      'nombre': nombre,
      'pais': pais,
      'creado_en': creadoEn,
      'total_sucursales': totalSucursales,
    };
  }

  Ciudad toEntity() {
    return Ciudad(
      idCiudad: idCiudad,
      nombre: nombre,
      pais: pais,
      creadoEn: DateTime.tryParse(creadoEn) ?? DateTime.now(),
      totalSucursales: totalSucursales,
    );
  }
}
