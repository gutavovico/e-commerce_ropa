// DTOs inmutables para el caso de uso CU36: Consultar Colecciones.
// Mapea los contratos OpenAPI expuestos por Ec-backend en /api/v1/colecciones/...

class ProductoColeccionItemDto {
  final int idProducto;
  final String nombre;
  final String? descripcion;
  final double precioBase;
  final String? imagenUrl;
  final String badgeEditorial;
  final String subtituloTextil;
  final String categoria;
  final List<String> coloresDisponibles;
  final int stockTotalDisponible;
  final bool tieneStock;

  const ProductoColeccionItemDto({
    required this.idProducto,
    required this.nombre,
    this.descripcion,
    required this.precioBase,
    this.imagenUrl,
    required this.badgeEditorial,
    required this.subtituloTextil,
    required this.categoria,
    this.coloresDisponibles = const [],
    required this.stockTotalDisponible,
    required this.tieneStock,
  });

  factory ProductoColeccionItemDto.fromJson(Map<String, dynamic> json) {
    return ProductoColeccionItemDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String?,
      precioBase:
          double.tryParse(json['precio_base']?.toString() ?? '0.0') ?? 0.0,
      imagenUrl: json['imagen_url'] as String?,
      badgeEditorial: json['badge_editorial'] as String? ?? 'ALTA COSTURA',
      subtituloTextil: json['subtitulo_textil'] as String? ?? 'TEJIDO NOBLE',
      categoria: json['categoria'] as String? ?? 'Prendas',
      coloresDisponibles: (json['colores_disponibles'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      stockTotalDisponible: json['stock_total_disponible'] as int? ?? 0,
      tieneStock: json['tiene_stock'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_producto': idProducto,
      'nombre': nombre,
      'descripcion': descripcion,
      'precio_base': precioBase,
      'imagen_url': imagenUrl,
      'badge_editorial': badgeEditorial,
      'subtitulo_textil': subtituloTextil,
      'categoria': categoria,
      'colores_disponibles': coloresDisponibles,
      'stock_total_disponible': stockTotalDisponible,
      'tiene_stock': tieneStock,
    };
  }
}

class ColeccionResumenDto {
  final int idColeccion;
  final String nombre;
  final String? descripcion;
  final String temporadaNombre;
  final String temporadaTipo;
  final String? proveedorNombre;
  final String tallerOrigen;
  final double precioDesde;
  final int totalPrendas;
  final bool esDestacada;
  final String badgeEdicion;
  final String? imagenPortada;
  final List<ProductoColeccionItemDto> piezasClave;

  const ColeccionResumenDto({
    required this.idColeccion,
    required this.nombre,
    this.descripcion,
    required this.temporadaNombre,
    required this.temporadaTipo,
    this.proveedorNombre,
    required this.tallerOrigen,
    required this.precioDesde,
    required this.totalPrendas,
    required this.esDestacada,
    required this.badgeEdicion,
    this.imagenPortada,
    this.piezasClave = const [],
  });

  factory ColeccionResumenDto.fromJson(Map<String, dynamic> json) {
    return ColeccionResumenDto(
      idColeccion: json['id_coleccion'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String?,
      temporadaNombre: json['temporada_nombre'] as String? ?? '',
      temporadaTipo: json['temporada_tipo'] as String? ?? 'regular',
      proveedorNombre: json['proveedor_nombre'] as String?,
      tallerOrigen: json['taller_origen'] as String? ?? 'Atelier FashionStore',
      precioDesde:
          double.tryParse(json['precio_desde']?.toString() ?? '0.0') ?? 0.0,
      totalPrendas: json['total_prendas'] as int? ?? 0,
      esDestacada: json['es_destacada'] as bool? ?? false,
      badgeEdicion: json['badge_edicion'] as String? ?? 'EDICIÓN VIGENTE',
      imagenPortada: json['imagen_portada'] as String?,
      piezasClave: (json['piezas_clave'] as List<dynamic>?)
              ?.map((item) =>
                  ProductoColeccionItemDto.fromJson(item as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_coleccion': idColeccion,
      'nombre': nombre,
      'descripcion': descripcion,
      'temporada_nombre': temporadaNombre,
      'temporada_tipo': temporadaTipo,
      'proveedor_nombre': proveedorNombre,
      'taller_origen': tallerOrigen,
      'precio_desde': precioDesde,
      'total_prendas': totalPrendas,
      'es_destacada': esDestacada,
      'badge_edicion': badgeEdicion,
      'imagen_portada': imagenPortada,
      'piezas_clave': piezasClave.map((e) => e.toJson()).toList(),
    };
  }
}

class ColeccionesActivasResponseDto {
  final int? temporadaActivaId;
  final String? temporadaActivaNombre;
  final ColeccionResumenDto? coleccionDestacada;
  final List<ColeccionResumenDto> otrasColecciones;
  final int totalColecciones;

  const ColeccionesActivasResponseDto({
    this.temporadaActivaId,
    this.temporadaActivaNombre,
    this.coleccionDestacada,
    this.otrasColecciones = const [],
    required this.totalColecciones,
  });

  factory ColeccionesActivasResponseDto.fromJson(Map<String, dynamic> json) {
    return ColeccionesActivasResponseDto(
      temporadaActivaId: json['temporada_activa_id'] as int?,
      temporadaActivaNombre: json['temporada_activa_nombre'] as String?,
      coleccionDestacada: json['coleccion_destacada'] != null
          ? ColeccionResumenDto.fromJson(
              json['coleccion_destacada'] as Map<String, dynamic>)
          : null,
      otrasColecciones: (json['otras_colecciones'] as List<dynamic>?)
              ?.map((item) =>
                  ColeccionResumenDto.fromJson(item as Map<String, dynamic>))
              .toList() ??
          const [],
      totalColecciones: json['total_colecciones'] as int? ?? 0,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'temporada_activa_id': temporadaActivaId,
      'temporada_activa_nombre': temporadaActivaNombre,
      'coleccion_destacada': coleccionDestacada?.toJson(),
      'otras_colecciones': otrasColecciones.map((e) => e.toJson()).toList(),
      'total_colecciones': totalColecciones,
    };
  }
}

class ColeccionDetalleDto {
  final int idColeccion;
  final String nombre;
  final String? descripcion;
  final String temporadaNombre;
  final String? proveedorNombre;
  final String tallerOrigen;
  final int totalPrendas;
  final String? mensajeEmptyState;
  final List<ProductoColeccionItemDto> productos;

  const ColeccionDetalleDto({
    required this.idColeccion,
    required this.nombre,
    this.descripcion,
    required this.temporadaNombre,
    this.proveedorNombre,
    required this.tallerOrigen,
    required this.totalPrendas,
    this.mensajeEmptyState,
    this.productos = const [],
  });

  factory ColeccionDetalleDto.fromJson(Map<String, dynamic> json) {
    return ColeccionDetalleDto(
      idColeccion: json['id_coleccion'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      descripcion: json['descripcion'] as String?,
      temporadaNombre: json['temporada_nombre'] as String? ?? '',
      proveedorNombre: json['proveedor_nombre'] as String?,
      tallerOrigen: json['taller_origen'] as String? ?? 'Atelier FashionStore',
      totalPrendas: json['total_prendas'] as int? ?? 0,
      mensajeEmptyState: json['mensaje_empty_state'] as String?,
      productos: (json['productos'] as List<dynamic>?)
              ?.map((item) =>
                  ProductoColeccionItemDto.fromJson(item as Map<String, dynamic>))
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id_coleccion': idColeccion,
      'nombre': nombre,
      'descripcion': descripcion,
      'temporada_nombre': temporadaNombre,
      'proveedor_nombre': proveedorNombre,
      'taller_origen': tallerOrigen,
      'total_prendas': totalPrendas,
      'mensaje_empty_state': mensajeEmptyState,
      'productos': productos.map((e) => e.toJson()).toList(),
    };
  }
}
