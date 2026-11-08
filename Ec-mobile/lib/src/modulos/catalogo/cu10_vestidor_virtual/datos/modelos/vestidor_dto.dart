/// DTOs de CU10 (vestidor virtual). Contratos del backend:
/// - `POST /api/v1/vestidor/token?canal=movil` → `TokenVestidorDecartOut`
/// - `POST /api/v1/vestidor/sesion` → `SesionVestidorOut` (201)
/// - `PATCH /api/v1/vestidor/sesion/{id_sesion_ar}` → `SesionVestidorOut`
library;

int _entero(Object? valor, {int porDefecto = 0}) {
  if (valor is int) return valor;
  if (valor is num) return valor.toInt();
  if (valor is String) return int.tryParse(valor) ?? porDefecto;
  return porDefecto;
}

int? _enteroOpcional(Object? valor) => valor == null ? null : _entero(valor);

/// Motor con el que se hizo la prueba. El backend solo acepta estos dos valores.
enum MotorVestidor {
  local('local'),
  ia('ia');

  final String valorApi;
  const MotorVestidor(this.valorApi);

  static MotorVestidor desdeApi(Object? valor) =>
      MotorVestidor.values.firstWhere((m) => m.valorApi == valor, orElse: () => MotorVestidor.local);
}

/// Token efímero de Decart (~60 s para establecer la conexión). Nunca es la clave permanente.
class TokenVestidorDto {
  final String token;
  final int expiraEnSegundos;
  final String servicio;

  const TokenVestidorDto({required this.token, required this.expiraEnSegundos, required this.servicio});

  factory TokenVestidorDto.fromJson(Map<String, dynamic> json) => TokenVestidorDto(
        token: json['token'] as String? ?? '',
        expiraEnSegundos: _entero(json['expira_en_segundos'], porDefecto: 60),
        servicio: json['servicio'] as String? ?? '',
      );
}

/// Cuerpo de `POST /api/v1/vestidor/sesion` (`SesionVestidorCrearIn`).
class SesionVestidorCrearDto {
  final int idProducto;
  final String dispositivo;
  final MotorVestidor motor;
  final int? duracionSegundos;
  final String? resultadoUrl;
  final bool generoInteres;

  const SesionVestidorCrearDto({
    required this.idProducto,
    this.dispositivo = 'app_flutter',
    required this.motor,
    this.duracionSegundos,
    this.resultadoUrl,
    this.generoInteres = false,
  });

  Map<String, dynamic> toJson() => {
        'id_producto': idProducto,
        'dispositivo': dispositivo,
        'motor': motor.valorApi,
        if (duracionSegundos != null) 'duracion_segundos': duracionSegundos,
        if (resultadoUrl != null) 'resultado_url': resultadoUrl,
        'genero_interes': generoInteres,
      };
}

/// Respuesta `SesionVestidorOut`.
class SesionVestidorDto {
  final int idSesionAr;
  final int idCliente;
  final int idProducto;
  final String? dispositivo;
  final MotorVestidor motor;
  final int? duracionSegundos;
  final DateTime? fechaHora;
  final String? resultadoUrl;
  final bool generoInteres;

  const SesionVestidorDto({
    required this.idSesionAr,
    required this.idCliente,
    required this.idProducto,
    this.dispositivo,
    required this.motor,
    this.duracionSegundos,
    this.fechaHora,
    this.resultadoUrl,
    required this.generoInteres,
  });

  factory SesionVestidorDto.fromJson(Map<String, dynamic> json) => SesionVestidorDto(
        idSesionAr: _entero(json['id_sesion_ar']),
        idCliente: _entero(json['id_cliente']),
        idProducto: _entero(json['id_producto']),
        dispositivo: json['dispositivo'] as String?,
        motor: MotorVestidor.desdeApi(json['motor']),
        duracionSegundos: _enteroOpcional(json['duracion_segundos']),
        fechaHora: DateTime.tryParse(json['fecha_hora'] as String? ?? ''),
        resultadoUrl: json['resultado_url'] as String?,
        generoInteres: json['genero_interes'] as bool? ?? false,
      );
}
