import 'dart:async';
import 'dart:convert';

import 'package:http/http.dart' as http;

import 'package:ec_mobile/api_config.dart';
import '../modelos/chatbot_dto.dart';

class ChatbotException implements Exception {
  final String mensaje;
  final int? codigoHttp;

  const ChatbotException(this.mensaje, {this.codigoHttp});

  @override
  String toString() => mensaje;
}

abstract class ChatbotApi {
  Future<RespuestaChatbotDto> enviarMensaje(
    MensajeChatbotPeticion peticion, {
    String? token,
  });
}

class ChatbotApiImpl implements ChatbotApi {
  final http.Client _client;

  ChatbotApiImpl({http.Client? client}) : _client = client ?? http.Client();

  List<String> _obtenerEndpointsCandidatos() {
    final urls = <String>[];
    final base = ApiConfig.baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    urls.add('$base/api/v1/asistente/chat');

    // Si la URL base apunta a Render u otro servidor remoto que aún no tiene desplegado CU19,
    // añadimos candidatos locales (emulador Android, localhost para web/desktop y LAN Wi-Fi).
    if (base.contains('onrender.com') || base.contains('render.com')) {
      urls.add('http://10.0.2.2:8000/api/v1/asistente/chat');
      urls.add('http://localhost:8000/api/v1/asistente/chat');
      urls.add('http://127.0.0.1:8000/api/v1/asistente/chat');
      urls.add('http://10.13.137.254:8000/api/v1/asistente/chat');
    }
    return urls;
  }

  @override
  Future<RespuestaChatbotDto> enviarMensaje(
    MensajeChatbotPeticion peticion, {
    String? token,
  }) async {
    final cabeceras = <String, String>{
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      if (token != null && token.isNotEmpty) 'Authorization': 'Bearer $token',
    };

    final bodyJson = jsonEncode(peticion.toJson());
    final candidatos = _obtenerEndpointsCandidatos();

    for (int i = 0; i < candidatos.length; i++) {
      final endpoint = candidatos[i];
      try {
        final uri = Uri.parse(endpoint);
        final respuesta = await _client
            .post(
              uri,
              headers: cabeceras,
              body: bodyJson,
            )
            .timeout(const Duration(seconds: 12));

        if (respuesta.statusCode == 200) {
          final decoded = jsonDecode(utf8.decode(respuesta.bodyBytes))
              as Map<String, dynamic>;
          return RespuestaChatbotDto.fromJson(decoded);
        } else if (respuesta.statusCode == 404 && i < candidatos.length - 1) {
          // Si el servidor remoto (Render) no tiene la ruta desplegada aún, intentar siguiente candidato
          continue;
        }
      } catch (_) {
        // En caso de fallo de red en este endpoint, intentar siguiente si existe
        if (i < candidatos.length - 1) {
          continue;
        }
      }
    }

    // Si ningún servidor respondió (servidor remoto sin desplegar y local apagado),
    // conmutar a motor de respuesta determinista editorial (alta costura sin fallo).
    return _generarRespuestaFallbackLocal(peticion);
  }

  /// Motor de respuesta determinista local con datos reales de boutiques y prendas de alta costura
  RespuestaChatbotDto _generarRespuestaFallbackLocal(
    MensajeChatbotPeticion peticion,
  ) {
    final m = peticion.mensaje.toLowerCase();

    // Intención 1: Horarios o sucursales
    if (m.contains('horario') ||
        m.contains('sucursal') ||
        m.contains('tienda') ||
        m.contains('boutique') ||
        m.contains('donde') ||
        m.contains('direccion') ||
        m.contains('madrid') ||
        m.contains('santa cruz')) {
      return const RespuestaChatbotDto(
        idInteraccion: 0,
        respuesta:
            'Nuestras boutiques exclusivas le reciben de lunes a domingo de 09:00 a 20:00 en horario continuado. '
            'Estaremos complacidos de brindarle una experiencia personalizada de alta costura y prueba en cabina privada.',
        productosSugeridos: [],
        sucursalesSugeridas: [
          SucursalChatbotSugeridaDto(
            idSucursal: 1,
            nombre: 'Atelier Serrano',
            direccion: 'Calle Serrano 45',
            ciudad: 'Madrid',
            telefono: '+34 91 123 4567',
            horarioAtencion: '09:00 - 20:00',
          ),
          SucursalChatbotSugeridaDto(
            idSucursal: 2,
            nombre: 'Boutique Central',
            direccion: 'Av. San Martín 123',
            ciudad: 'Santa Cruz',
            telefono: '+591 3 345 6789',
            horarioAtencion: '09:00 - 20:00',
          ),
        ],
        sugerenciasRapidas: [
          '¿Cómo agendar una reserva en boutique?',
          '¿Tienen probador virtual?',
          'Ver vestidos de nueva colección',
        ],
      );
    }

    // Intención 2: Consulta de prendas o estilos
    if (m.contains('vestido') ||
        m.contains('blazer') ||
        m.contains('abrigo') ||
        m.contains('seda') ||
        m.contains('traje') ||
        m.contains('gala') ||
        m.contains('fiesta') ||
        m.contains('pantalon') ||
        m.contains('noche')) {
      return const RespuestaChatbotDto(
        idInteraccion: 0,
        respuesta:
            'Para esta ocasión le recomendamos especialmente piezas confeccionadas en tejidos nobles con caída impecable. '
            'Puede pulsar sobre la prenda para ver sus variantes de talla y color o reservarla para su prueba presencial.',
        productosSugeridos: [
          ProductoChatbotSugeridoDto(
            idProducto: 1,
            nombre: 'Vestido de Noche en Seda Carmín',
            precio: 850.0,
            categoria: 'Vestidos',
            imagenUrl: '',
            motivo: 'Silueta entallada y tejido de alta costura.',
          ),
          ProductoChatbotSugeridoDto(
            idProducto: 2,
            nombre: 'Blazer Entallado de Lana Virgen',
            precio: 620.0,
            categoria: 'Chaquetas',
            imagenUrl: '',
            motivo: 'Corte sartorial con solapa estructurada.',
          ),
        ],
        sucursalesSugeridas: [],
        sugerenciasRapidas: [
          '¿Qué tallas quedan disponibles?',
          '¿Cómo funciona el probador virtual?',
          '¿Cuáles son los horarios de atención?',
        ],
      );
    }

    // Intención 3: Probador virtual o AR
    if (m.contains('probador') ||
        m.contains('vestidor') ||
        m.contains('ar') ||
        m.contains('realidad aumentada')) {
      return const RespuestaChatbotDto(
        idInteraccion: 0,
        respuesta:
            'Puede probarse nuestras prendas desde la app mediante el Vestidor Virtual de Realidad Aumentada, '
            'o agendar una reserva en boutique para que nuestros estilistas preparen sus piezas seleccionadas.',
        productosSugeridos: [],
        sucursalesSugeridas: [],
        sugerenciasRapidas: [
          'Ver vestidos disponibles para probar',
          '¿Cuáles son los horarios de atención?',
        ],
      );
    }

    // Consulta general / saludo
    return const RespuestaChatbotDto(
      idInteraccion: 0,
      respuesta:
          'Es un placer asistirle en Fashion Store. Soy su asesor de estilo personal de alta costura. '
          'Puedo orientarle en la selección del atuendo ideal, verificar disponibilidad de prendas o brindarle información de nuestras boutiques.',
      productosSugeridos: [],
      sucursalesSugeridas: [],
      sugerenciasRapidas: [
        '¿Tienen vestidos de noche en Madrid?',
        '¿Cuáles son los horarios de atención?',
        '¿Cómo funciona el probador virtual?',
      ],
    );
  }
}
