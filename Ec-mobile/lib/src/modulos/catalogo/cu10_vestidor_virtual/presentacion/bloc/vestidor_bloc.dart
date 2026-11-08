import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../../../../../api_config.dart';
import '../../datos/datasources/vestidor_api.dart';
import '../../datos/modelos/vestidor_dto.dart';
import '../../dominio/prenda_vestidor.dart';
import '../../dominio/prompt_vton.dart';
import '../../dominio/recurso_prenda.dart';

/// Lo que necesita el WebView del Motor 2 para abrir la sesión con Decart.
class DatosSesionRealista {
  final String tokenInicial;
  final String prompt;

  /// JPEG en base64 de la prenda sobre fondo blanco; `null` = Decart trabaja solo con el prompt.
  final String? referenciaBase64;

  const DatosSesionRealista({required this.tokenInicial, required this.prompt, this.referenciaBase64});
}

/// Estados sellados del vestidor.
sealed class EstadoVestidor {
  const EstadoVestidor();
}

/// Motor 1: cámara + ML Kit en el dispositivo. Estado por defecto y destino de todo fallback.
class VestidorMotorLocal extends EstadoVestidor {
  const VestidorMotorLocal();
}

/// Pidiendo token y preparando la imagen de referencia, antes de abrir el WebView.
class VestidorPreparandoRealista extends EstadoVestidor {
  const VestidorPreparandoRealista();
}

/// WebView abierto y conectando con Decart (todavía sin vídeo).
class VestidorConectandoRealista extends EstadoVestidor {
  final DatosSesionRealista datos;
  const VestidorConectandoRealista(this.datos);
}

/// Decart emite el vídeo con la prenda puesta.
class VestidorRealistaEnCurso extends EstadoVestidor {
  final DatosSesionRealista datos;
  final int segundosRestantes;
  const VestidorRealistaEnCurso(this.datos, this.segundosRestantes);
}

/// Orquesta los dos motores de CU10 sin tocar la plataforma: la cámara/ML Kit y el WebView viven
/// en sus widgets; este BLoC decide qué motor está activo, cuándo conmutar y qué registrar.
class VestidorBloc extends ChangeNotifier {
  final PrendaVestidor prenda;
  final String _token;
  final VestidorApi _api;
  final Duration _timeoutConexion;
  final int _limiteSegundosRealista;
  final Duration _tick;
  final String _baseWeb;
  final Future<ReferenciaVton> Function(Uint8List bytes) _prepararReferencia;

  VestidorBloc({
    required this.prenda,
    required String token,
    VestidorApi? api,
    Duration timeoutConexion = const Duration(seconds: 45),
    int limiteSegundosRealista = 60,
    Duration tick = const Duration(seconds: 1),
    String? baseWeb,
    Future<ReferenciaVton> Function(Uint8List bytes)? prepararReferencia,
  })  : _token = token,
        _api = api ?? VestidorApiImpl(),
        _timeoutConexion = timeoutConexion,
        _limiteSegundosRealista = limiteSegundosRealista,
        _tick = tick,
        _baseWeb = baseWeb ?? ApiConfig.webBaseUrl,
        _prepararReferencia = prepararReferencia ?? ((bytes) => compute(prepararReferenciaVton, bytes));

  EstadoVestidor _estado = const VestidorMotorLocal();
  EstadoVestidor get estado => _estado;

  /// Motivo del último fallback automático al Motor 1.
  String? _errorFallback;
  String? get errorFallback => _errorFallback;

  /// Aviso informativo (cola de Decart, límite alcanzado, modo solo prompt…).
  String? _aviso;
  String? get aviso => _aviso;

  int _segundosSesion = 0;
  int get segundosSesion => _segundosSesion;

  /// Si Decart llegó a emitir vídeo: la sesión se registra entonces con `motor = ia`.
  bool _usoRealista = false;
  bool get usoRealista => _usoRealista;

  bool _sesionRegistrada = false;
  bool _liberado = false;
  Timer? _timerSesion;
  Timer? _timerConexion;
  Timer? _timerLimite;

  /// URL absoluta del PNG transparente de la prenda (Motor 1 y referencia del Motor 2).
  String? get urlRecursoPrenda => resolverUrlRecurso(prenda.modeloArUrl, _baseWeb);

  bool get motorLocalActivo => _estado is VestidorMotorLocal;

  void iniciar() {
    _timerSesion ??= Timer.periodic(_tick, (_) {
      _segundosSesion++;
      notifyListeners();
    });
  }

  // ---------------------------------------------------------------------------
  // Motor 2
  // ---------------------------------------------------------------------------

  Future<void> activarModoRealista() async {
    if (_estado is! VestidorMotorLocal) return;
    _errorFallback = null;
    _aviso = null;
    _emitir(const VestidorPreparandoRealista());

    final TokenVestidorDto token;
    try {
      token = await _api.obtenerTokenDecart(token: _token);
    } on VestidorException catch (e) {
      _fallback(e.esSesionExpirada
          ? 'Inicie sesión de nuevo para usar el modo realista. Continuando en el Motor Local.'
          : 'El modo realista con IA (Decart) no está disponible o agotó sus créditos. Continuando en el Motor Local.');
      return;
    }
    if (_estado is! VestidorPreparandoRealista) return; // el cliente volvió al local mientras tanto

    final referencia = await _obtenerReferencia();
    if (_estado is! VestidorPreparandoRealista) return;

    _emitir(VestidorConectandoRealista(DatosSesionRealista(
      tokenInicial: token.token,
      prompt: construirPromptVton(prenda.nombre, prenda.categoriaNombre),
      referenciaBase64: referencia,
    )));

    _timerConexion?.cancel();
    _timerConexion = Timer(_timeoutConexion, () {
      if (_estado is VestidorConectandoRealista) {
        _fallback('Tiempo de espera excedido al conectar el vídeo de Decart. Continuando en el Motor Local.');
      }
    });
  }

  Future<String?> _obtenerReferencia() async {
    final url = urlRecursoPrenda;
    if (url == null) return null;
    try {
      final referencia = await _prepararReferencia(await _api.descargarRecurso(url));
      if (!referencia.cumpleTamanoMinimo) {
        debugPrint('[VESTIDOR] Referencia de ${referencia.ancho}x${referencia.alto}: Decart recomienda $ladoMinimoReferenciaPx px.');
      }
      return referencia.base64Jpeg;
    } catch (e) {
      debugPrint('[VESTIDOR] No se pudo preparar la imagen de la prenda: $e');
      _aviso = 'No se pudo cargar la imagen de la prenda: el modo realista usará solo la descripción.';
      return null;
    }
  }

  /// Token nuevo para cada re-marcación del SDK de Decart (el anterior caduca a los 60 s).
  Future<String?> solicitarTokenAdicional() async {
    try {
      return (await _api.obtenerTokenDecart(token: _token)).token;
    } on VestidorException {
      return null;
    }
  }

  /// Eventos que la página del WebView envía por el canal `Vestidor`.
  void procesarEventoRealista(Map<String, dynamic> evento) {
    if (_estado is! VestidorConectandoRealista && _estado is! VestidorRealistaEnCurso) return;

    switch (evento['tipo']) {
      case 'streaming':
        final actual = _estado;
        if (actual is! VestidorConectandoRealista) return;
        _timerConexion?.cancel();
        _usoRealista = true;
        _aviso = null;
        _emitir(VestidorRealistaEnCurso(actual.datos, _limiteSegundosRealista));
        _iniciarLimite();
      case 'cola':
        _aviso = 'Decart está ocupado: posición ${evento['posicion']} de ${evento['total']} en la cola.';
        notifyListeners();
      case 'capacidad':
        _aviso = 'Decart no tiene capacidad disponible ahora mismo. Reintentando…';
        notifyListeners();
      case 'error':
        _fallback(_mensajeError(evento));
      case 'fin':
        _fallback(_mensajeFin(evento['motivo']?.toString()));
    }
  }

  String _mensajeError(Map<String, dynamic> evento) {
    final codigo = evento['codigo']?.toString();
    final base = switch (codigo) {
      'RED_CRITICA' => 'Su red no permite el vídeo en tiempo real con Decart',
      'CAMARA' => 'El modo realista no pudo abrir la cámara (${evento['detalle'] ?? 'sin detalle'})',
      'SDK' => 'No se pudo cargar el SDK de Decart (¿sin conexión?)',
      _ => 'No fue posible mantener la sesión con Decart Lucy VTON${codigo != null ? ' ($codigo)' : ''}',
    };
    return '$base. Continuando en el Motor Local.';
  }

  String _mensajeFin(String? motivo) {
    final base = switch (motivo) {
      'insufficient_credits' => 'Créditos de Decart agotados',
      'moderation_violation' => 'La imagen no superó la moderación de contenido de Decart',
      _ => 'Decart finalizó la sesión',
    };
    return '$base. Continuando en el Motor Local.';
  }

  void _iniciarLimite() {
    _timerLimite?.cancel();
    _timerLimite = Timer.periodic(_tick, (_) {
      final actual = _estado;
      if (actual is! VestidorRealistaEnCurso) return;
      final restantes = actual.segundosRestantes - 1;
      if (restantes <= 0) {
        _cancelarTimersRealista();
        _aviso = 'Límite de $_limiteSegundosRealista s del modo realista alcanzado (control de costes). Motor Local activado.';
        _emitir(const VestidorMotorLocal());
        return;
      }
      _emitir(VestidorRealistaEnCurso(actual.datos, restantes));
    });
  }

  /// Vuelta manual al Motor 1.
  void volverAMotorLocal() {
    if (_estado is VestidorMotorLocal) return;
    _cancelarTimersRealista();
    _errorFallback = null;
    _aviso = 'Motor Local activado. El vídeo se procesa solo en su teléfono.';
    _emitir(const VestidorMotorLocal());
  }

  void _fallback(String mensaje) {
    _cancelarTimersRealista();
    _errorFallback = mensaje;
    _emitir(const VestidorMotorLocal());
  }

  void _cancelarTimersRealista() {
    _timerConexion?.cancel();
    _timerLimite?.cancel();
  }

  // ---------------------------------------------------------------------------
  // Registro de la sesión (una sola vez)
  // ---------------------------------------------------------------------------

  Future<void> registrarSesion({bool generoInteres = false}) async {
    if (_sesionRegistrada) return;
    _sesionRegistrada = true;
    try {
      await _api.registrarSesion(
        SesionVestidorCrearDto(
          idProducto: prenda.idProducto,
          motor: _usoRealista ? MotorVestidor.ia : MotorVestidor.local,
          duracionSegundos: _segundosSesion < 1 ? 1 : _segundosSesion,
          generoInteres: generoInteres,
        ),
        token: _token,
      );
    } on VestidorException catch (e) {
      // El registro es analítico: su fallo no debe interrumpir al cliente.
      debugPrint('[VESTIDOR] No se registró la sesión: ${e.mensaje}');
    }
  }

  void _emitir(EstadoVestidor nuevo) {
    _estado = nuevo;
    if (!_liberado) notifyListeners();
  }

  @override
  void dispose() {
    _liberado = true;
    _timerSesion?.cancel();
    _cancelarTimersRealista();
    super.dispose();
  }
}
