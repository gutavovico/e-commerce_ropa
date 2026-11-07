/// Modelos de transferencia de datos (DTO) para CU19: Asistente Inteligente / Chatbot.
library;

class MensajeChatbotPeticion {
  final String mensaje;
  final String canal;
  final int? idSucursalPreferida;

  const MensajeChatbotPeticion({
    required this.mensaje,
    this.canal = 'movil',
    this.idSucursalPreferida,
  });

  Map<String, dynamic> toJson() => {
        'mensaje': mensaje,
        'canal': canal,
        if (idSucursalPreferida != null)
          'id_sucursal_preferida': idSucursalPreferida,
      };
}

class ProductoChatbotSugeridoDto {
  final int idProducto;
  final String nombre;
  final double precio;
  final String? categoria;
  final String? imagenUrl;
  final String? motivo;

  const ProductoChatbotSugeridoDto({
    required this.idProducto,
    required this.nombre,
    required this.precio,
    this.categoria,
    this.imagenUrl,
    this.motivo,
  });

  factory ProductoChatbotSugeridoDto.fromJson(Map<String, dynamic> json) {
    return ProductoChatbotSugeridoDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Prenda Fashion',
      precio: (json['precio'] as num?)?.toDouble() ?? 0.0,
      categoria: json['categoria'] as String?,
      imagenUrl: json['imagen_url'] as String?,
      motivo: json['motivo'] as String?,
    );
  }
}

class SucursalChatbotSugeridaDto {
  final int idSucursal;
  final String nombre;
  final String direccion;
  final String ciudad;
  final String telefono;
  final String? horarioAtencion;

  const SucursalChatbotSugeridaDto({
    required this.idSucursal,
    required this.nombre,
    required this.direccion,
    required this.ciudad,
    required this.telefono,
    this.horarioAtencion,
  });

  factory SucursalChatbotSugeridaDto.fromJson(Map<String, dynamic> json) {
    return SucursalChatbotSugeridaDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      direccion: json['direccion'] as String? ?? '',
      ciudad: json['ciudad'] as String? ?? '',
      telefono: json['telefono'] as String? ?? '',
      horarioAtencion: json['horario_atencion'] as String?,
    );
  }
}

class MensajeChatbotRespuestaDto {
  final int idInteraccion;
  final String respuesta;
  final List<ProductoChatbotSugeridoDto> productosSugeridos;
  final List<SucursalChatbotSugeridaDto> sucursalesSugeridas;
  final List<String> sugerenciasRapidas;
  final int? idSucursalDetectada;

  const MensajeChatbotRespuestaDto({
    required this.idInteraccion,
    required this.respuesta,
    required this.productosSugeridos,
    required this.sucursalesSugeridas,
    required this.sugerenciasRapidas,
    this.idSucursalDetectada,
  });

  factory MensajeChatbotRespuestaDto.fromJson(Map<String, dynamic> json) {
    return MensajeChatbotRespuestaDto(
      idInteraccion: json['id_interaccion'] as int? ?? 0,
      respuesta: json['respuesta'] as String? ?? '',
      productosSugeridos: (json['productos_sugeridos'] as List<dynamic>? ?? [])
          .map((p) =>
              ProductoChatbotSugeridoDto.fromJson(p as Map<String, dynamic>))
          .toList(),
      sucursalesSugeridas: (json['sucursales_sugeridas'] as List<dynamic>? ?? [])
          .map((s) =>
              SucursalChatbotSugeridaDto.fromJson(s as Map<String, dynamic>))
          .toList(),
      sugerenciasRapidas: (json['sugerencias_rapidas'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      idSucursalDetectada: json['id_sucursal_detectada'] as int?,
    );
  }
}

typedef RespuestaChatbotDto = MensajeChatbotRespuestaDto;

class BurbujaMensajeChatbot {
  final String id;
  final bool esUsuario;
  final String texto;
  final String hora;
  final List<ProductoChatbotSugeridoDto> productos;
  final List<SucursalChatbotSugeridaDto> sucursales;

  const BurbujaMensajeChatbot({
    required this.id,
    required this.esUsuario,
    required this.texto,
    required this.hora,
    this.productos = const [],
    this.sucursales = const [],
  });
}
