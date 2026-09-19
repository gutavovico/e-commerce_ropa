/// Modelos de transferencia de datos (DTO) para CU02: Iniciar Sesión.
class LoginPeticionDto {
  final String email;
  final String password;
  final bool recordarDispositivo;

  const LoginPeticionDto({
    required this.email,
    required this.password,
    this.recordarDispositivo = false,
  });

  Map<String, dynamic> toJson() {
    return {
      'email': email.trim(),
      'password': password,
      'recordar_dispositivo': recordarDispositivo,
    };
  }
}

class LoginRespuestaDto {
  final String accessToken;
  final String tokenType;
  final int idUsuario;
  final String email;
  final String nombres;
  final String apellidos;
  final String rol;

  const LoginRespuestaDto({
    required this.accessToken,
    required this.tokenType,
    required this.idUsuario,
    required this.email,
    required this.nombres,
    required this.apellidos,
    required this.rol,
  });

  factory LoginRespuestaDto.fromJson(Map<String, dynamic> json) {
    return LoginRespuestaDto(
      accessToken: json['access_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'bearer',
      idUsuario: json['id_usuario'] as int,
      email: json['email'] as String? ?? '',
      nombres: json['nombres'] as String? ?? '',
      apellidos: json['apellidos'] as String? ?? '',
      rol: json['rol'] as String? ?? 'cliente',
    );
  }
}
