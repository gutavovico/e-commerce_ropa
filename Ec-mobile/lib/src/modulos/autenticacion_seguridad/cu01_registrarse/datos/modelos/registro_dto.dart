/// Modelos de transferencia de datos (DTO) para CU01: Registrarse.
class RegistroClienteDto {
  final String email;
  final String password;
  final String nombres;
  final String apellidos;
  final String? telefono;
  final String? tallaPreferida;
  final int? ciudadPreferida;

  const RegistroClienteDto({
    required this.email,
    required this.password,
    required this.nombres,
    required this.apellidos,
    this.telefono,
    this.tallaPreferida,
    this.ciudadPreferida,
  });

  Map<String, dynamic> toJson() {
    final map = <String, dynamic>{
      'email': email.trim(),
      'password': password,
      'nombres': nombres.trim(),
      'apellidos': apellidos.trim(),
    };

    if (telefono != null && telefono!.trim().isNotEmpty) {
      map['telefono'] = telefono!.trim();
    }
    if (tallaPreferida != null && tallaPreferida!.trim().isNotEmpty) {
      map['talla_preferida'] = tallaPreferida!.trim().toUpperCase();
    }
    if (ciudadPreferida != null) {
      map['ciudad_preferida'] = ciudadPreferida;
    }

    return map;
  }
}

class RegistroRespuestaDto {
  final int idUsuario;
  final String email;
  final String nombres;
  final String apellidos;
  final String rol;
  final String tokenAcceso;
  final String tipoToken;

  const RegistroRespuestaDto({
    required this.idUsuario,
    required this.email,
    required this.nombres,
    required this.apellidos,
    required this.rol,
    required this.tokenAcceso,
    required this.tipoToken,
  });

  factory RegistroRespuestaDto.fromJson(Map<String, dynamic> json) {
    return RegistroRespuestaDto(
      idUsuario: json['id_usuario'] as int,
      email: json['email'] as String? ?? '',
      nombres: json['nombres'] as String? ?? '',
      apellidos: json['apellidos'] as String? ?? '',
      rol: json['rol'] as String? ?? 'cliente',
      tokenAcceso: json['token_acceso'] as String? ?? '',
      tipoToken: json['tipo_token'] as String? ?? 'bearer',
    );
  }
}
