// Modelos de transferencia de datos (DTO) para CU02: Iniciar Sesión.
//
// P2-CU02: el login es solo con correo y contraseña. La respuesta trae la empresa del empleado
// (`tenant`) y las tiendas en las que está registrado el cliente (`empresas`).
import '../../../../../core/empresa_actual.dart';

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

  /// Empresa del empleado; null para clientes y super administrador.
  final EmpresaTienda? tenant;

  /// Tiendas disponibles en las que está registrado el cliente; vacía para empleados.
  final List<EmpresaTienda> empresas;

  const LoginRespuestaDto({
    required this.accessToken,
    required this.tokenType,
    required this.idUsuario,
    required this.email,
    required this.nombres,
    required this.apellidos,
    required this.rol,
    this.tenant,
    this.empresas = const [],
  });

  bool get esCliente => rol == 'cliente';

  factory LoginRespuestaDto.fromJson(Map<String, dynamic> json) {
    return LoginRespuestaDto(
      accessToken: json['access_token'] as String? ?? '',
      tokenType: json['token_type'] as String? ?? 'bearer',
      idUsuario: json['id_usuario'] as int,
      email: json['email'] as String? ?? '',
      nombres: json['nombres'] as String? ?? '',
      apellidos: json['apellidos'] as String? ?? '',
      rol: json['rol'] as String? ?? 'cliente',
      tenant: json['tenant'] is Map<String, dynamic>
          ? EmpresaTienda.fromJson(json['tenant'] as Map<String, dynamic>)
          : null,
      empresas: (json['empresas'] as List<dynamic>? ?? const [])
          .whereType<Map<String, dynamic>>()
          .map(EmpresaTienda.fromJson)
          .toList(),
    );
  }
}
