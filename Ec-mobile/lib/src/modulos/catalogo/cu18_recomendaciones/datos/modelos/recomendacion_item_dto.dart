/// DTOs para el módulo de Recomendaciones Personalizadas (CU18) en Ec-mobile.
class VarianteRecomendadaDto {
  final int idVariante;
  final String sku;
  final String talla;
  final String color;
  final String? codigoHex;
  final double precioExtra;
  final bool disponible;
  final int cantidadDisponible;

  const VarianteRecomendadaDto({
    required this.idVariante,
    required this.sku,
    required this.talla,
    required this.color,
    this.codigoHex,
    required this.precioExtra,
    required this.disponible,
    required this.cantidadDisponible,
  });

  factory VarianteRecomendadaDto.fromJson(Map<String, dynamic> json) {
    return VarianteRecomendadaDto(
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      talla: json['talla'] as String? ?? '38',
      color: json['color'] as String? ?? 'Marfil',
      codigoHex: json['codigo_hex'] as String?,
      precioExtra: double.tryParse(json['precio_extra']?.toString() ?? '0.0') ?? 0.0,
      disponible: json['disponible'] as bool? ?? true,
      cantidadDisponible: json['cantidad_disponible'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_variante': idVariante,
      'sku': sku,
      'talla': talla,
      'color': color,
      'codigo_hex': codigoHex,
      'precio_extra': precioExtra.toStringAsFixed(2),
      'disponible': disponible,
      'cantidad_disponible': cantidadDisponible,
    };
  }
}

class ProductoRecomendadoDto {
  final int idProducto;
  final String nombre;
  final String descripcion;
  final String categoria;
  final String? coleccion;
  final double precioBase;
  final String imagenUrl;
  final String? modeloArUrl;
  final bool activo;
  final String badgeEditorial;
  final String subtituloAtelier;
  final String tonoPrincipal;
  final double scoreRelevancia;
  final String? motivoIndividual;
  final int stockTotalDisponible;
  final List<VarianteRecomendadaDto> variantes;

  const ProductoRecomendadoDto({
    required this.idProducto,
    required this.nombre,
    required this.descripcion,
    required this.categoria,
    this.coleccion,
    required this.precioBase,
    required this.imagenUrl,
    this.modeloArUrl,
    required this.activo,
    required this.badgeEditorial,
    required this.subtituloAtelier,
    required this.tonoPrincipal,
    required this.scoreRelevancia,
    this.motivoIndividual,
    required this.stockTotalDisponible,
    required this.variantes,
  });

  factory ProductoRecomendadoDto.fromJson(Map<String, dynamic> json) {
    final rawVariantes = json['variantes'] as List<dynamic>? ?? [];
    final variantesList = rawVariantes
        .map((v) => VarianteRecomendadaDto.fromJson(v as Map<String, dynamic>))
        .toList();

    return ProductoRecomendadoDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Pieza de Alta Costura',
      descripcion: json['descripcion'] as String? ?? '',
      categoria: json['categoria'] as String? ?? 'Alta Costura',
      coleccion: json['coleccion'] as String?,
      precioBase: double.tryParse(json['precio_base']?.toString() ?? '0.0') ?? 0.0,
      imagenUrl: json['imagen_url'] as String? ??
          'https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800',
      modeloArUrl: json['modelo_ar_url'] as String?,
      activo: json['activo'] as bool? ?? true,
      badgeEditorial: json['badge_editorial'] as String? ?? 'EDICIÓN LIMITADA',
      subtituloAtelier: json['subtitulo_atelier'] as String? ?? 'ALTA COSTURA',
      tonoPrincipal: json['tono_principal'] as String? ?? 'Marfil Puro',
      scoreRelevancia: double.tryParse(json['score_relevancia']?.toString() ?? '0.90') ?? 0.90,
      motivoIndividual: json['motivo_individual'] as String?,
      stockTotalDisponible: json['stock_total_disponible'] as int? ?? 0,
      variantes: variantesList,
    );
  }
}

class RecomendacionesResponseDto {
  final bool tieneHistorial;
  final String? motivoGeneral;
  final String boutiqueReferencia;
  final String? mensajeEmptyState;
  final int totalRecomendados;
  final List<ProductoRecomendadoDto> items;

  const RecomendacionesResponseDto({
    required this.tieneHistorial,
    this.motivoGeneral,
    required this.boutiqueReferencia,
    this.mensajeEmptyState,
    required this.totalRecomendados,
    required this.items,
  });

  factory RecomendacionesResponseDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    final itemsList = rawItems
        .map((item) => ProductoRecomendadoDto.fromJson(item as Map<String, dynamic>))
        .toList();

    return RecomendacionesResponseDto(
      tieneHistorial: json['tiene_historial'] as bool? ?? false,
      motivoGeneral: json['motivo_general'] as String?,
      boutiqueReferencia: json['boutique_referencia'] as String? ?? 'Boutique Serrano (Madrid)',
      mensajeEmptyState: json['mensaje_empty_state'] as String?,
      totalRecomendados: json['total_recomendados'] as int? ?? itemsList.length,
      items: itemsList,
    );
  }

  factory RecomendacionesResponseDto.emptyState() {
    return const RecomendacionesResponseDto(
      tieneHistorial: false,
      motivoGeneral: null,
      boutiqueReferencia: 'Boutique Serrano (Madrid)',
      mensajeEmptyState:
          'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo',
      totalRecomendados: 0,
      items: [],
    );
  }
}
