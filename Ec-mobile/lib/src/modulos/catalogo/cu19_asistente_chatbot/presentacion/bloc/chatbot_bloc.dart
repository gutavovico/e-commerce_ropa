import 'dart:async';

import 'package:flutter/foundation.dart';

import '../../../../../core/push/servicio_push.dart';
import '../../datos/datasources/chatbot_api.dart';
import '../../datos/modelos/chatbot_dto.dart';

// --- EVENTOS ---

abstract class ChatbotEvento {
  const ChatbotEvento();
}

class ChatbotEventoEnviarMensaje extends ChatbotEvento {
  final String texto;
  final int? idSucursal;

  const ChatbotEventoEnviarMensaje(this.texto, {this.idSucursal});
}

class ChatbotEventoReiniciarConversacion extends ChatbotEvento {
  const ChatbotEventoReiniciarConversacion();
}

// --- ESTADO ---

class ChatbotEstado {
  final List<BurbujaMensajeChatbot> mensajes;
  final List<String> sugerenciasRapidas;
  final bool cargando;
  final String? error;

  const ChatbotEstado({
    required this.mensajes,
    required this.sugerenciasRapidas,
    this.cargando = false,
    this.error,
  });

  factory ChatbotEstado.inicial() {
    final ahora = DateTime.now();
    final hora =
        '${ahora.hour.toString().padLeft(2, '0')}:${ahora.minute.toString().padLeft(2, '0')}';
    return ChatbotEstado(
      mensajes: [
        BurbujaMensajeChatbot(
          id: 'bienvenida',
          esUsuario: false,
          texto:
              'Bienvenido a Fashion Store. Soy su asistente de estilismo personal de alta costura. ¿En qué puedo asesorarle hoy?',
          hora: hora,
        ),
      ],
      sugerenciasRapidas: const [
        '¿Tienen vestidos de noche en Madrid?',
        '¿Cuáles son los horarios de atención?',
        '¿Cómo funciona el probador virtual?',
      ],
      cargando: false,
    );
  }

  ChatbotEstado copyWith({
    List<BurbujaMensajeChatbot>? mensajes,
    List<String>? sugerenciasRapidas,
    bool? cargando,
    String? error,
    bool clearError = false,
  }) {
    return ChatbotEstado(
      mensajes: mensajes ?? this.mensajes,
      sugerenciasRapidas: sugerenciasRapidas ?? this.sugerenciasRapidas,
      cargando: cargando ?? this.cargando,
      error: clearError ? null : (error ?? this.error),
    );
  }
}

// --- BLOC ---

class ChatbotBloc extends ChangeNotifier {
  static ChatbotBloc? _instanciaCompartida;

  /// Retorna la instancia compartida de sesión para que el chat no se reinicie
  /// al presionar el botón "atrás" en el móvil.
  static ChatbotBloc obtenerInstanciaCompartida({ChatbotApi? api, String? token}) {
    _instanciaCompartida ??= ChatbotBloc(api: api, token: token);
    return _instanciaCompartida!;
  }

  /// Limpia la instancia compartida exclusivamente al cerrar sesión
  static void purgarSesion() {
    _instanciaCompartida?.reiniciarConversacion();
    _instanciaCompartida?._mensajesNoLeidos = false;
    _instanciaCompartida = null;
  }

  final ChatbotApi _api;
  final String? _token;

  ChatbotEstado _estado = ChatbotEstado.inicial();
  ChatbotEstado get estado => _estado;

  bool _chatAbierto = false;
  bool _mensajesNoLeidos = false;

  bool get mensajesNoLeidos => _mensajesNoLeidos;
  bool get chatAbierto => _chatAbierto;

  void marcarChatAbierto() {
    _chatAbierto = true;
    if (_mensajesNoLeidos) {
      _mensajesNoLeidos = false;
      notifyListeners();
    }
  }

  void marcarChatCerrado() {
    _chatAbierto = false;
  }

  void marcarMensajesNoLeidos(bool valor) {
    _mensajesNoLeidos = valor;
    notifyListeners();
  }

  ChatbotBloc({
    ChatbotApi? api,
    String? token,
  })  : _api = api ?? ChatbotApiImpl(),
        _token = token;

  String _obtenerHoraActual() {
    final ahora = DateTime.now();
    return '${ahora.hour.toString().padLeft(2, '0')}:${ahora.minute.toString().padLeft(2, '0')}';
  }

  /// Despacho por eventos para compatibilidad con la arquitectura BLoC
  void add(ChatbotEvento evento) {
    if (evento is ChatbotEventoEnviarMensaje) {
      enviarMensaje(evento.texto, idSucursal: evento.idSucursal);
    } else if (evento is ChatbotEventoReiniciarConversacion) {
      reiniciarConversacion();
    }
  }

  /// Reinicia la conversación al saludo inicial (consultas esporádicas sin persistencia forzada)
  void reiniciarConversacion() {
    _estado = ChatbotEstado.inicial();
    _mensajesNoLeidos = false;
    notifyListeners();
  }

  /// Envía un mensaje del usuario al backend y procesa la respuesta del Asistente
  Future<void> enviarMensaje(String texto, {int? idSucursal}) async {
    final trimmed = texto.trim();
    if (trimmed.isEmpty || _estado.cargando) return;

    final horaMsg = _obtenerHoraActual();

    // 1. Añadir mensaje del usuario inmediatamente al feed
    final mensajesConUsuario = List<BurbujaMensajeChatbot>.from(_estado.mensajes)
      ..add(
        BurbujaMensajeChatbot(
          id: 'usr-${DateTime.now().millisecondsSinceEpoch}',
          esUsuario: true,
          texto: trimmed,
          hora: horaMsg,
        ),
      );

    _estado = _estado.copyWith(
      mensajes: mensajesConUsuario,
      cargando: true,
      clearError: true,
    );
    notifyListeners();

    try {
      final peticion = MensajeChatbotPeticion(
        mensaje: trimmed,
        canal: 'movil',
        idSucursalPreferida: idSucursal,
      );

      final respuesta = await _api.enviarMensaje(peticion, token: _token);

      final mensajesConBot = List<BurbujaMensajeChatbot>.from(_estado.mensajes)
        ..add(
          BurbujaMensajeChatbot(
            id: 'bot-${respuesta.idInteraccion}',
            esUsuario: false,
            texto: respuesta.respuesta,
            hora: _obtenerHoraActual(),
            productos: respuesta.productosSugeridos,
            sucursales: respuesta.sucursalesSugeridas,
          ),
        );

      _estado = _estado.copyWith(
        mensajes: mensajesConBot,
        sugerenciasRapidas: respuesta.sugerenciasRapidas.isNotEmpty
            ? respuesta.sugerenciasRapidas
            : _estado.sugerenciasRapidas,
        cargando: false,
      );
      if (!_chatAbierto) {
        _mensajesNoLeidos = true;
        unawaited(
          ServicioPush.instancia.notificarEvento(
            titulo: 'Tu Asistente de Estilo respondió',
            cuerpo: respuesta.respuesta.length > 100
                ? '${respuesta.respuesta.substring(0, 97)}...'
                : respuesta.respuesta,
            datos: {'pantalla': 'asistente', 'id': '${respuesta.idInteraccion}'},
            claveDeduplicacion: 'chatbot_${respuesta.idInteraccion}',
          ),
        );
      }
      notifyListeners();
    } on ChatbotException catch (e) {
      final mensajesConFallo = List<BurbujaMensajeChatbot>.from(_estado.mensajes)
        ..add(
          BurbujaMensajeChatbot(
            id: 'err-${DateTime.now().millisecondsSinceEpoch}',
            esUsuario: false,
            texto:
                'Disculpe la molestia, en este momento el servicio de asesoría remota experimenta una pausa. Por favor explore nuestro catálogo de alta costura o consulte en nuestras boutiques.',
            hora: _obtenerHoraActual(),
          ),
        );

      _estado = _estado.copyWith(
        mensajes: mensajesConFallo,
        cargando: false,
        error: e.mensaje,
      );
      if (!_chatAbierto) {
        _mensajesNoLeidos = true;
      }
      notifyListeners();
    } catch (e) {
      final mensajesConFallo = List<BurbujaMensajeChatbot>.from(_estado.mensajes)
        ..add(
          BurbujaMensajeChatbot(
            id: 'err-${DateTime.now().millisecondsSinceEpoch}',
            esUsuario: false,
            texto:
                'Ha ocurrido un inconveniente al conectar con el asistente. Intente nuevamente en unos instantes.',
            hora: _obtenerHoraActual(),
          ),
        );

      _estado = _estado.copyWith(
        mensajes: mensajesConFallo,
        cargando: false,
        error: e.toString(),
      );
      if (!_chatAbierto) {
        _mensajesNoLeidos = true;
      }
      notifyListeners();
    }
  }

  void close() {
    // Para compatibilidad con dispose
  }
}
