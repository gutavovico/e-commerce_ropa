/// Modelos y DTOs para CU04: Gestionar Perfil del Cliente en Flutter.
/// Mapeo tipado 1:1 con la respuesta JSON de FastAPI.
library;

class ResumenAtelierDto {
  final int visitasRegistradas;
  final int boutiquesVisitadas;
  final String preferenciaTextil;
  final String estatusMembresia;

  const ResumenAtelierDto({
    required this.visitasRegistradas,
    required this.boutiquesVisitadas,
    required this.preferenciaTextil,
    required this.estatusMembresia,
  });

  factory ResumenAtelierDto.fromJson(Map<String, dynamic> json) {
    return ResumenAtelierDto(
      visitasRegistradas: json['visitas_registradas'] as int? ?? 32,
      boutiquesVisitadas: json['boutiques_visitadas'] as int? ?? 4,
      preferenciaTextil: json['preferencia_textil'] as String? ?? '100% Seda & Lana',
      estatusMembresia: json['estatus_membresia'] as String? ?? 'Nivel Platino',
    );
  }

  Map<String, dynamic> toJson() => {
    'visitas_registradas': visitasRegistradas,
    'boutiques_visitadas': boutiquesVisitadas,
    'preferencia_textil': preferenciaTextil,
    'estatus_membresia': estatusMembresia,
  };
}

class PerfilClienteDto {
  final int idUsuario;
  final String numeroSocio;
  final String email;
  final String rol;
  final String fechaRegistro;
  final String miembroDesde;
  final String? ultimoAcceso;
  final String nombres;
  final String apellidos;
  final String? telefono;
  final String? fechaNacimiento;
  final String? genero;
  final String? tallaPreferida;
  final int? ciudadPreferida;
  final bool aceptaMarketing;
  final ResumenAtelierDto resumenAtelier;

  const PerfilClienteDto({
    required this.idUsuario,
    required this.numeroSocio,
    required this.email,
    required this.rol,
    required this.fechaRegistro,
    required this.miembroDesde,
    this.ultimoAcceso,
    required this.nombres,
    required this.apellidos,
    this.telefono,
    this.fechaNacimiento,
    this.genero,
    this.tallaPreferida,
    this.ciudadPreferida,
    required this.aceptaMarketing,
    required this.resumenAtelier,
  });

  factory PerfilClienteDto.fromJson(Map<String, dynamic> json) {
    return PerfilClienteDto(
      idUsuario: json['id_usuario'] as int? ?? 0,
      numeroSocio: json['numero_socio'] as String? ?? '#8402',
      email: json['email'] as String? ?? '',
      rol: json['rol'] as String? ?? 'cliente',
      fechaRegistro: json['fecha_registro'] as String? ?? '',
      miembroDesde: json['miembro_desde'] as String? ?? 'Octubre 2021',
      ultimoAcceso: json['ultimo_acceso'] as String?,
      nombres: json['nombres'] as String? ?? '',
      apellidos: json['apellidos'] as String? ?? '',
      telefono: json['telefono'] as String?,
      fechaNacimiento: json['fecha_nacimiento'] as String?,
      genero: json['genero'] as String?,
      tallaPreferida: json['talla_preferida'] as String?,
      ciudadPreferida: json['ciudad_preferida'] as int?,
      aceptaMarketing: json['acepta_marketing'] as bool? ?? true,
      resumenAtelier: json['resumen_atelier'] != null
          ? ResumenAtelierDto.fromJson(json['resumen_atelier'] as Map<String, dynamic>)
          : const ResumenAtelierDto(
              visitasRegistradas: 32,
              boutiquesVisitadas: 4,
              preferenciaTextil: '100% Seda & Lana',
              estatusMembresia: 'Nivel Platino',
            ),
    );
  }

  Map<String, dynamic> toJson() => {
    'id_usuario': idUsuario,
    'numero_socio': numeroSocio,
    'email': email,
    'rol': rol,
    'fecha_registro': fechaRegistro,
    'miembro_desde': miembroDesde,
    'ultimo_acceso': ultimoAcceso,
    'nombres': nombres,
    'apellidos': apellidos,
    'telefono': telefono,
    'fecha_nacimiento': fechaNacimiento,
    'genero': genero,
    'talla_preferida': tallaPreferida,
    'ciudad_preferida': ciudadPreferida,
    'acepta_marketing': aceptaMarketing,
    'resumen_atelier': resumenAtelier.toJson(),
  };
}

class PerfilClienteUpdateDto {
  final String? nombres;
  final String? apellidos;
  final String? telefono;
  final String? fechaNacimiento;
  final String? genero;
  final String? tallaPreferida;
  final int? ciudadPreferida;
  final bool? aceptaMarketing;

  const PerfilClienteUpdateDto({
    this.nombres,
    this.apellidos,
    this.telefono,
    this.fechaNacimiento,
    this.genero,
    this.tallaPreferida,
    this.ciudadPreferida,
    this.aceptaMarketing,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{};
    if (nombres != null) map['nombres'] = nombres;
    if (apellidos != null) map['apellidos'] = apellidos;
    if (telefono != null) map['telefono'] = telefono;
    if (fechaNacimiento != null) map['fecha_nacimiento'] = fechaNacimiento;
    if (genero != null) map['genero'] = genero;
    if (tallaPreferida != null) map['talla_preferida'] = tallaPreferida;
    if (ciudadPreferida != null) map['ciudad_preferida'] = ciudadPreferida;
    if (aceptaMarketing != null) map['acepta_marketing'] = aceptaMarketing;
    return map;
  }
}

class PedidoMovilDto {
  final String id;
  final String titulo;
  final String origen;
  final String descripcion;
  final String talla;
  final String color;
  final int precio;
  final String fecha;
  final String estado;
  final String referencia;
  final String imagen;

  const PedidoMovilDto({
    required this.id,
    required this.titulo,
    required this.origen,
    required this.descripcion,
    required this.talla,
    required this.color,
    required this.precio,
    required this.fecha,
    required this.estado,
    required this.referencia,
    required this.imagen,
  });
}
