/// DTOs inmutables para el caso de uso CU05: Consultar Catálogo de Productos.
/// Mapea los contratos OpenAPI expuestos por Ec-backend en /api/v1/catalogo.
library;

class ColorItemDto {
  final int idColor;
  final String nombre;
  final String? codigoHex;

  const ColorItemDto({
    required this.idColor,
    required this.nombre,
    this.codigoHex,
  });

  factory ColorItemDto.fromJson(Map<String, dynamic> json) {
    return ColorItemDto(
      idColor: json['id_color'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      codigoHex: json['codigo_hex'] as String?,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_color': idColor,
      'nombre': nombre,
      if (codigoHex != null) 'codigo_hex': codigoHex,
    };
  }
}

class CategoriaResumenDto {
  final int idCategoria;
  final String nombre;
  final int totalPrendas;

  const CategoriaResumenDto({
    required this.idCategoria,
    required this.nombre,
    required this.totalPrendas,
  });

  factory CategoriaResumenDto.fromJson(Map<String, dynamic> json) {
    return CategoriaResumenDto(
      idCategoria: json['id_categoria'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      totalPrendas: json['total_prendas'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_categoria': idCategoria,
      'nombre': nombre,
      'total_prendas': totalPrendas,
    };
  }
}

class ProductoCatalogoItemDto {
  final int idProducto;
  final String nombre;
  final String? descripcion;
  final double precioBase;
  final double precioFinal;
  final bool tieneDescuento;
  final int? porcentajeDescuento;
  final String? imagenUrl;
  final int categoriaId;
  final String categoriaNombre;
  final String subtituloAtelier;
  final String? etiquetaBadge;
  final double ratingPromedio;
  final List<String> tallasDisponibles;
  final List<ColorItemDto> coloresDisponibles;
  final int stockTotalDisponible;
  final bool tieneStock;
  final bool esFavorito;

  const ProductoCatalogoItemDto({
    required this.idProducto,
    required this.nombre,
    this.descripcion,
    required this.precioBase,
    required this.precioFinal,
    this.tieneDescuento = false,
    this.porcentajeDescuento,
    this.imagenUrl,
    required this.categoriaId,
    required this.categoriaNombre,
    required this.subtituloAtelier,
    this.etiquetaBadge,
    this.ratingPromedio = 5.0,
    this.tallasDisponibles = const [],
    this.coloresDisponibles = const [],
    this.stockTotalDisponible = 0,
    this.tieneStock = true,
    this.esFavorito = false,
  });

  factory ProductoCatalogoItemDto.fromJson(Map<String, dynamic> json) {
    final precioBaseParsed =
        double.tryParse(json['precio_base']?.toString() ?? '0.0') ?? 0.0;
    final precioFinalParsed = json['precio_final'] != null
        ? (double.tryParse(json['precio_final'].toString()) ?? precioBaseParsed)
        : precioBaseParsed;

    return ProductoCatalogoItemDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String?,
      precioBase: precioBaseParsed,
      precioFinal: precioFinalParsed,
      tieneDescuento: json['tiene_descuento'] as bool? ?? false,
      porcentajeDescuento: json['porcentaje_descuento'] as int?,
      imagenUrl: json['imagen_url'] as String?,
      categoriaId: json['categoria_id'] as int? ?? 0,
      categoriaNombre: json['categoria_nombre'] as String? ?? 'Prendas',
      subtituloAtelier:
          json['subtitulo_atelier'] as String? ?? 'EDICIÓN ATELIER',
      etiquetaBadge: json['etiqueta_badge'] as String?,
      ratingPromedio:
          (json['rating_promedio'] as num?)?.toDouble() ?? 5.0,
      tallasDisponibles: (json['tallas_disponibles'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      coloresDisponibles: (json['colores_disponibles'] as List<dynamic>?)
              ?.map((e) => ColorItemDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      stockTotalDisponible: json['stock_total_disponible'] as int? ?? 0,
      tieneStock: json['tiene_stock'] as bool? ?? true,
      esFavorito: json['es_favorito'] as bool? ?? false,
    );
  }

  ProductoCatalogoItemDto copyWith({
    bool? esFavorito,
  }) {
    return ProductoCatalogoItemDto(
      idProducto: idProducto,
      nombre: nombre,
      descripcion: descripcion,
      precioBase: precioBase,
      precioFinal: precioFinal,
      tieneDescuento: tieneDescuento,
      porcentajeDescuento: porcentajeDescuento,
      imagenUrl: imagenUrl,
      categoriaId: categoriaId,
      categoriaNombre: categoriaNombre,
      subtituloAtelier: subtituloAtelier,
      etiquetaBadge: etiquetaBadge,
      ratingPromedio: ratingPromedio,
      tallasDisponibles: tallasDisponibles,
      coloresDisponibles: coloresDisponibles,
      stockTotalDisponible: stockTotalDisponible,
      tieneStock: tieneStock,
      esFavorito: esFavorito ?? this.esFavorito,
    );
  }
}

class CatalogoResponseDto {
  final List<CategoriaResumenDto> resumenCategorias;
  final int totalArticulos;
  final int paginaActual;
  final int limite;
  final int totalPaginas;
  final bool tieneSiguiente;
  final bool tieneAnterior;
  final int? categoriaSeleccionadaId;
  final List<ProductoCatalogoItemDto> items;

  const CatalogoResponseDto({
    required this.resumenCategorias,
    required this.totalArticulos,
    required this.paginaActual,
    required this.limite,
    required this.totalPaginas,
    required this.tieneSiguiente,
    required this.tieneAnterior,
    this.categoriaSeleccionadaId,
    required this.items,
  });

  factory CatalogoResponseDto.fromJson(Map<String, dynamic> json) {
    return CatalogoResponseDto(
      resumenCategorias: (json['resumen_categorias'] as List<dynamic>?)
              ?.map((e) => CategoriaResumenDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      totalArticulos: json['total_articulos'] as int? ?? 0,
      paginaActual: json['pagina_actual'] as int? ?? 1,
      limite: json['limite'] as int? ?? 8,
      totalPaginas: json['total_paginas'] as int? ?? 0,
      tieneSiguiente: json['tiene_siguiente'] as bool? ?? false,
      tieneAnterior: json['tiene_anterior'] as bool? ?? false,
      categoriaSeleccionadaId: json['categoria_seleccionada_id'] as int?,
      items: (json['items'] as List<dynamic>?)
              ?.map((e) =>
                  ProductoCatalogoItemDto.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }
}
