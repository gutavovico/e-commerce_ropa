/// DTOs para el catálogo de productos y variantes en Ec-mobile (CU06).
class VarianteResumenDto {
  final int idVariante;
  final String sku;
  final String talla;
  final String color;
  final String? codigoHex;
  final double precioExtra;
  final bool disponible;

  const VarianteResumenDto({
    required this.idVariante,
    required this.sku,
    required this.talla,
    required this.color,
    this.codigoHex,
    required this.precioExtra,
    required this.disponible,
  });

  factory VarianteResumenDto.fromJson(Map<String, dynamic> json) {
    return VarianteResumenDto(
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      talla: json['talla'] as String? ?? '',
      color: json['color'] as String? ?? '',
      codigoHex: json['codigo_hex'] as String?,
      precioExtra: double.tryParse(json['precio_extra']?.toString() ?? '0.0') ?? 0.0,
      disponible: json['disponible'] as bool? ?? true,
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
    };
  }
}

class ProductoItemDto {
  final int idProducto;
  final String nombre;
  final String descripcion;
  final String categoria;
  final String coleccion;
  final String temporada;
  final double precioBase;
  final String imagenUrl;
  final String? modeloArUrl;
  final bool activo;
  final String badgeEditorial;
  final String subtituloAtelier;
  final String tallaSugerida;
  final String colorSugerido;
  final List<VarianteResumenDto> variantes;

  const ProductoItemDto({
    required this.idProducto,
    required this.nombre,
    required this.descripcion,
    required this.categoria,
    required this.coleccion,
    required this.temporada,
    required this.precioBase,
    required this.imagenUrl,
    this.modeloArUrl,
    required this.activo,
    required this.badgeEditorial,
    required this.subtituloAtelier,
    required this.tallaSugerida,
    required this.colorSugerido,
    required this.variantes,
  });

  factory ProductoItemDto.fromJson(Map<String, dynamic> json) {
    final rawVariantes = json['variantes'] as List<dynamic>? ?? [];
    return ProductoItemDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String? ?? '',
      categoria: json['categoria'] as String? ?? '',
      coleccion: json['coleccion'] as String? ?? '',
      temporada: json['temporada'] as String? ?? '',
      precioBase: double.tryParse(json['precio_base']?.toString() ?? '0.0') ?? 0.0,
      imagenUrl: json['imagen_url'] as String? ?? '',
      modeloArUrl: json['modelo_ar_url'] as String?,
      activo: json['activo'] as bool? ?? true,
      badgeEditorial: json['badge_editorial'] as String? ?? 'ED. LIMITADA',
      subtituloAtelier: json['subtitulo_atelier'] as String? ?? 'ALTA COSTURA',
      tallaSugerida: json['talla_sugerida'] as String? ?? 'Talla 38',
      colorSugerido: json['color_sugerido'] as String? ?? 'Marfil',
      variantes: rawVariantes
          .map((v) => VarianteResumenDto.fromJson(v as Map<String, dynamic>))
          .toList(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_producto': idProducto,
      'nombre': nombre,
      'descripcion': descripcion,
      'categoria': categoria,
      'coleccion': coleccion,
      'temporada': temporada,
      'precio_base': precioBase.toStringAsFixed(2),
      'imagen_url': imagenUrl,
      'modelo_ar_url': modeloArUrl,
      'activo': activo,
      'badge_editorial': badgeEditorial,
      'subtitulo_atelier': subtituloAtelier,
      'talla_sugerida': tallaSugerida,
      'color_sugerido': colorSugerido,
      'variantes': variantes.map((v) => v.toJson()).toList(),
    };
  }
}
