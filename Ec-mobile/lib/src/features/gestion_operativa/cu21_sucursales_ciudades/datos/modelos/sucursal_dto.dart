import '../../dominio/entidades/sucursal.dart';

/// DTO para serializacion y deserializacion de sucursales y boutiques.
class SucursalDto {
  final int idSucursal;
  final int idCiudad;
  final String ciudadNombre;
  final String nombre;
  final String direccion;
  final String? telefono;
  final String horarioApertura;
  final String horarioCierre;
  final bool activa;
  final String creadoEn;
  final int totalEmpleados;
  final int totalPrendasStock;
  final int reservasActivasConteo;

  const SucursalDto({
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

  factory SucursalDto.fromJson(Map<String, dynamic> json) {
    return SucursalDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      idCiudad: json['id_ciudad'] as int? ?? 0,
      ciudadNombre: json['ciudad_nombre'] as String? ?? '',
      nombre: json['nombre'] as String? ?? '',
      direccion: json['direccion'] as String? ?? '',
      telefono: json['telefono'] as String?,
      horarioApertura: json['horario_apertura'] as String? ?? '10:00',
      horarioCierre: json['horario_cierre'] as String? ?? '20:30',
      activa: json['activa'] as bool? ?? true,
      creadoEn: json['creado_en'] as String? ?? '',
      totalEmpleados: json['total_empleados'] as int? ?? 0,
      totalPrendasStock: json['total_prendas_stock'] as int? ?? 0,
      reservasActivasConteo: json['reservas_activas_conteo'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_sucursal': idSucursal,
      'id_ciudad': idCiudad,
      'ciudad_nombre': ciudadNombre,
      'nombre': nombre,
      'direccion': direccion,
      'telefono': telefono,
      'horario_apertura': horarioApertura,
      'horario_cierre': horarioCierre,
      'activa': activa,
      'creado_en': creadoEn,
      'total_empleados': totalEmpleados,
      'total_prendas_stock': totalPrendasStock,
      'reservas_activas_conteo': reservasActivasConteo,
    };
  }

  Sucursal toEntity() {
    return Sucursal(
      idSucursal: idSucursal,
      idCiudad: idCiudad,
      ciudadNombre: ciudadNombre,
      nombre: nombre,
      direccion: direccion,
      telefono: telefono,
      horarioApertura: horarioApertura,
      horarioCierre: horarioCierre,
      activa: activa,
      creadoEn: DateTime.tryParse(creadoEn) ?? DateTime.now(),
      totalEmpleados: totalEmpleados,
      totalPrendasStock: totalPrendasStock,
      reservasActivasConteo: reservasActivasConteo,
    );
  }
}
