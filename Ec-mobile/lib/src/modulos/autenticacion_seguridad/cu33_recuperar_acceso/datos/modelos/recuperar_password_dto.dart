// Modelos de transferencia de datos (DTO) para CU33: Recuperar Acceso de Cuenta.

class SolicitarCodigoPeticionDto {
  final String email;

  const SolicitarCodigoPeticionDto({required this.email});

  Map<String, dynamic> toJson() {
    return {
      'email': email.trim().toLowerCase(),
    };
  }
}

class SolicitarCodigoRespuestaDto {
  final String mensaje;
  final int tiempoEsperaSegundos;

  const SolicitarCodigoRespuestaDto({
    required this.mensaje,
    this.tiempoEsperaSegundos = 60,
  });

  factory SolicitarCodigoRespuestaDto.fromJson(Map<String, dynamic> json) {
    return SolicitarCodigoRespuestaDto(
      mensaje: json['mensaje'] as String? ??
          'Si el correo electrónico se encuentra registrado, recibirás un código de verificación.',
      tiempoEsperaSegundos: json['tiempo_espera_segundos'] as int? ?? 60,
    );
  }
}

class RestablecerPasswordPeticionDto {
  final String email;
  final String codigo;
  final String nuevaPassword;
  final String confirmarPassword;

  const RestablecerPasswordPeticionDto({
    required this.email,
    required this.codigo,
    required this.nuevaPassword,
    required this.confirmarPassword,
  });

  Map<String, dynamic> toJson() {
    return {
      'email': email.trim().toLowerCase(),
      'codigo': codigo.replaceAll(' ', '').trim(),
      'nueva_password': nuevaPassword,
      'confirmar_password': confirmarPassword,
    };
  }
}

class RestablecerPasswordRespuestaDto {
  final String mensaje;
  final bool exito;
  final String codigoEvento;

  const RestablecerPasswordRespuestaDto({
    required this.mensaje,
    this.exito = true,
    this.codigoEvento = 'PASSWORD_RESTABLECIDA',
  });

  factory RestablecerPasswordRespuestaDto.fromJson(Map<String, dynamic> json) {
    return RestablecerPasswordRespuestaDto(
      mensaje: json['mensaje'] as String? ?? 'Contraseña restablecida exitosamente.',
      exito: json['exito'] as bool? ?? true,
      codigoEvento: json['codigo_evento'] as String? ?? 'PASSWORD_RESTABLECIDA',
    );
  }
}
