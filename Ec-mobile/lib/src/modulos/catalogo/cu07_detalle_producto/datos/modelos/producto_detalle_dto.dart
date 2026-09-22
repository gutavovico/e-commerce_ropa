/// DTO principal para el detalle exhaustivo de una prenda (CU07, CU08, CU09)
class ProductoDetalleDto {
  final int idProducto;
  final String nombre;
  final String? descripcion;
  final String subtituloAtelier;
  final String? etiquetaBadge;
  final String skuBase;
  final double precioBase;
  final double precioFinal;
  final bool tieneDescuento;
  final int? porcentajeDescuento;
  final int? categoriaId;
  final String? categoriaNombre;
  final String? imagenUrl;
  final List<ImagenAnguloDto> galeriaAngulos;
  final String? modeloArUrl;
  final String? modeloInfo;
  final ComposicionNobleDto composicion;
  final List<ColorDetalleDto> coloresDisponibles;
  final List<TallaDetalleDto> tallasDisponibles;
  final List<VarianteDetalleDto> variantes;
  final List<PiezaLookDto> piezasLookComplementario;
  final int totalGuardados;

  const ProductoDetalleDto({
    required this.idProducto,
    required this.nombre,
    this.descripcion,
    required this.subtituloAtelier,
    this.etiquetaBadge,
    required this.skuBase,
    required this.precioBase,
    required this.precioFinal,
    required this.tieneDescuento,
    this.porcentajeDescuento,
    this.categoriaId,
    this.categoriaNombre,
    this.imagenUrl,
    required this.galeriaAngulos,
    this.modeloArUrl,
    this.modeloInfo,
    required this.composicion,
    required this.coloresDisponibles,
    required this.tallasDisponibles,
    required this.variantes,
    this.piezasLookComplementario = const [],
    this.totalGuardados = 0,
  });

  factory ProductoDetalleDto.fromJson(Map<String, dynamic> json) {
    // Galería multiángulo. El backend la expone como `galeria` en `ProductoDetalleOut`
    // (Ec-backend/app/modules/catalogo/cu07_detalle_producto/esquemas.py).
    final rawGaleria = json['galeria'] as List<dynamic>? ?? [];
    final galeria = rawGaleria
        .map((g) => ImagenAnguloDto.fromJson(g as Map<String, dynamic>))
        .toList();

    // Composición noble
    final compJson = json['composicion'] as Map<String, dynamic>? ?? {};
    final composicion = ComposicionNobleDto.fromJson(compJson);

    // Colores disponibles
    final rawColores = json['colores_disponibles'] as List<dynamic>? ?? [];
    final colores = rawColores
        .map((c) => ColorDetalleDto.fromJson(c as Map<String, dynamic>))
        .toList();

    // Tallas disponibles
    final rawTallas = json['tallas_disponibles'] as List<dynamic>? ?? [];
    final tallas = rawTallas
        .map((t) => TallaDetalleDto.fromJson(t as Map<String, dynamic>))
        .toList();

    // Variantes
    final rawVariantes = json['variantes'] as List<dynamic>? ?? [];
    final variantes = rawVariantes
        .map((v) => VarianteDetalleDto.fromJson(v as Map<String, dynamic>))
        .toList();

    // Piezas Look complementario
    final rawPiezas = json['piezas_look_complementario'] as List<dynamic>? ?? [];
    final piezas = rawPiezas
        .map((p) => PiezaLookDto.fromJson(p as Map<String, dynamic>))
        .toList();

    return ProductoDetalleDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Prenda Atelier',
      descripcion: json['descripcion'] as String?,
      subtituloAtelier: json['subtitulo_atelier'] as String? ?? 'ALTA COSTURA · ATELIER',
      etiquetaBadge: json['etiqueta_badge'] as String?,
      skuBase: json['sku_base'] as String? ?? 'ATEL-BASE',
      precioBase: _toDouble(json['precio_base']),
      precioFinal: _toDouble(json['precio_final']),
      tieneDescuento: json['tiene_descuento'] as bool? ?? false,
      porcentajeDescuento: json['porcentaje_descuento'] as int?,
      categoriaId: json['categoria_id'] as int?,
      categoriaNombre: json['categoria_nombre'] as String?,
      // `ProductoDetalleOut` emite `imagen_principal`; `imagen_url` es el nombre que usan
      // los DTO de listado (catálogo, piezas complementarias), no el de la ficha.
      imagenUrl: json['imagen_principal'] as String?,
      galeriaAngulos: galeria,
      modeloArUrl: json['modelo_ar_url'] as String?,
      modeloInfo: json['modelo_info'] as String? ?? 'MODELO: 1,77M - TALLA 38 ES',
      composicion: composicion,
      coloresDisponibles: colores,
      tallasDisponibles: tallas,
      variantes: variantes,
      piezasLookComplementario: piezas,
      totalGuardados: json['total_guardados'] as int? ?? 0,
    );
  }

  static double _toDouble(dynamic val) {
    if (val == null) return 0.0;
    if (val is num) return val.toDouble();
    if (val is String) {
      return double.tryParse(val) ?? 0.0;
    }
    return 0.0;
  }
}

/// DTO para ángulos fotográficos de la misma prenda auténtica
class ImagenAnguloDto {
  final String url;
  final String etiqueta;
  final int orden;

  const ImagenAnguloDto({
    required this.url,
    required this.etiqueta,
    required this.orden,
  });

  factory ImagenAnguloDto.fromJson(Map<String, dynamic> json) {
    return ImagenAnguloDto(
      url: json['url'] as String? ?? '',
      etiqueta: json['etiqueta'] as String? ?? 'VISTA ATELIER',
      orden: json['orden'] as int? ?? 1,
    );
  }
}

/// DTO para la ficha técnica y composición noble (CU07)
class ComposicionNobleDto {
  final String cuerpoPrincipal;
  final String forroInterior;
  final String tecnicaTextil;
  final String descripcionConfeccion;
  final List<String> instruccionesCuidado;

  const ComposicionNobleDto({
    required this.cuerpoPrincipal,
    required this.forroInterior,
    required this.tecnicaTextil,
    required this.descripcionConfeccion,
    required this.instruccionesCuidado,
  });

  factory ComposicionNobleDto.fromJson(Map<String, dynamic> json) {
    final rawCuidados = json['instrucciones_cuidado'] as List<dynamic>? ?? [];
    final cuidados = rawCuidados.map((c) => c.toString()).toList();

    return ComposicionNobleDto(
      cuerpoPrincipal: json['cuerpo_principal'] as String? ?? '100% Seda Natural 22 Momme',
      forroInterior: json['forro_interior'] as String? ?? 'Crepé de seda puro transpirable',
      tecnicaTextil: json['tecnica_textil'] as String? ?? 'Plisado artesanal al vapor de Lyon',
      descripcionConfeccion: json['descripcion_confeccion'] as String? ??
          'Textura micro-plisada artesanal con caída orgánica al movimiento.',
      instruccionesCuidado: cuidados.isNotEmpty
          ? cuidados
          : [
              'Limpieza profesional en seco con percloroetileno moderado.',
              'Planchado únicamente vertical mediante vapor suave a distancia mínima de 15 cm.',
              'Conservar en su funda transpirable de algodón incluida para mantener el porte.',
            ],
    );
  }
}

/// DTO de Color disponible
class ColorDetalleDto {
  final int idColor;
  final String nombre;
  final String codigoHex;
  final bool disponible;
  final String? imagenUrl;

  const ColorDetalleDto({
    required this.idColor,
    required this.nombre,
    required this.codigoHex,
    required this.disponible,
    this.imagenUrl,
  });

  factory ColorDetalleDto.fromJson(Map<String, dynamic> json) {
    return ColorDetalleDto(
      idColor: json['id_color'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Color Atelier',
      codigoHex: json['codigo_hex'] as String? ?? '#000000',
      disponible: json['disponible'] as bool? ?? true,
      imagenUrl: json['imagen_url'] as String?,
    );
  }
}

/// DTO de Talla disponible
class TallaDetalleDto {
  final int idTalla;
  final String codigo;
  final int orden;
  final bool disponible;
  final int stockTotal;

  const TallaDetalleDto({
    required this.idTalla,
    required this.codigo,
    required this.orden,
    required this.disponible,
    required this.stockTotal,
  });

  factory TallaDetalleDto.fromJson(Map<String, dynamic> json) {
    return TallaDetalleDto(
      idTalla: json['id_talla'] as int? ?? 0,
      codigo: json['codigo'] as String? ?? '38',
      orden: json['orden'] as int? ?? 1,
      disponible: json['disponible'] as bool? ?? true,
      stockTotal: json['stock_total'] as int? ?? 0,
    );
  }
}

/// DTO de Variante (Color + Talla específica)
class VarianteDetalleDto {
  final int idVariante;
  final int idProducto;
  final int idTalla;
  final String tallaCodigo;
  final int tallaOrden;
  final int idColor;
  final String colorNombre;
  final String colorHex;
  final String sku;
  final double precioExtra;
  final double precioFinalVariante;
  final int stockTotalDisponible;
  final bool tieneStock;
  final String? imagenUrl;

  const VarianteDetalleDto({
    required this.idVariante,
    required this.idProducto,
    required this.idTalla,
    required this.tallaCodigo,
    required this.tallaOrden,
    required this.idColor,
    required this.colorNombre,
    required this.colorHex,
    required this.sku,
    required this.precioExtra,
    required this.precioFinalVariante,
    required this.stockTotalDisponible,
    required this.tieneStock,
    this.imagenUrl,
  });

  factory VarianteDetalleDto.fromJson(Map<String, dynamic> json) {
    return VarianteDetalleDto(
      idVariante: json['id_variante'] as int? ?? 0,
      idProducto: json['id_producto'] as int? ?? 0,
      idTalla: json['id_talla'] as int? ?? 0,
      tallaCodigo: json['talla_codigo'] as String? ?? '38',
      tallaOrden: json['talla_orden'] as int? ?? 1,
      idColor: json['id_color'] as int? ?? 0,
      colorNombre: json['color_nombre'] as String? ?? 'Color',
      colorHex: json['color_hex'] as String? ?? '#000000',
      sku: json['sku'] as String? ?? 'SKU-VAR',
      precioExtra: ProductoDetalleDto._toDouble(json['precio_extra']),
      precioFinalVariante: ProductoDetalleDto._toDouble(json['precio_final_variante']),
      stockTotalDisponible: json['stock_total_disponible'] as int? ?? 0,
      tieneStock: json['tiene_stock'] as bool? ?? false,
      imagenUrl: json['imagen_url'] as String?,
    );
  }
}

/// DTO de Sucursal con disponibilidad física y botón de reserva directa (CU09, CU12)
class SucursalDisponibilidadDto {
  final int idSucursal;
  final String nombre;
  final String ciudad;
  final String direccion;
  final String? telefono;
  final String horarioApertura;
  final String horarioCierre;
  final int cantidadDisponible;
  final int cantidadReservada;
  final String estadoStock;
  final String badgeStock;
  final String citasDisponiblesTexto;
  final bool permiteReservaDirecta;

  const SucursalDisponibilidadDto({
    required this.idSucursal,
    required this.nombre,
    required this.ciudad,
    required this.direccion,
    this.telefono,
    required this.horarioApertura,
    required this.horarioCierre,
    required this.cantidadDisponible,
    required this.cantidadReservada,
    required this.estadoStock,
    required this.badgeStock,
    required this.citasDisponiblesTexto,
    required this.permiteReservaDirecta,
  });

  bool get tieneStockFisico => cantidadDisponible > 0 && permiteReservaDirecta;

  factory SucursalDisponibilidadDto.fromJson(Map<String, dynamic> json) {
    return SucursalDisponibilidadDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Boutique Insignia',
      ciudad: json['ciudad'] as String? ?? 'Madrid',
      direccion: json['direccion'] as String? ?? 'Calle Serrano 48',
      telefono: json['telefono'] as String?,
      horarioApertura: json['horario_apertura'] as String? ?? '09:00',
      horarioCierre: json['horario_cierre'] as String? ?? '20:00',
      cantidadDisponible: json['cantidad_disponible'] as int? ?? 0,
      cantidadReservada: json['cantidad_reservada'] as int? ?? 0,
      estadoStock: json['estado_stock'] as String? ?? 'agotada',
      badgeStock: json['badge_stock'] as String? ?? 'AGOTADA',
      citasDisponiblesTexto: json['citas_disponibles_texto'] as String? ??
          'Citas de prueba disponibles hoy y mañana',
      permiteReservaDirecta: json['permite_reserva_directa'] as bool? ?? false,
    );
  }
}

/// Respuesta de disponibilidad multisede para una variante dada (CU09)
class DisponibilidadResponseDto {
  final int idProducto;
  final int? idVariante;
  final String? sku;
  final List<SucursalDisponibilidadDto> sucursales;
  final int totalDisponibleGlobal;

  const DisponibilidadResponseDto({
    required this.idProducto,
    this.idVariante,
    this.sku,
    required this.sucursales,
    required this.totalDisponibleGlobal,
  });

  factory DisponibilidadResponseDto.fromJson(Map<String, dynamic> json) {
    final rawSucursales = json['sucursales'] as List<dynamic>? ?? [];
    final sucursales = rawSucursales
        .map((s) => SucursalDisponibilidadDto.fromJson(s as Map<String, dynamic>))
        .toList();

    return DisponibilidadResponseDto(
      idProducto: json['id_producto'] as int? ?? 0,
      idVariante: json['id_variante'] as int?,
      sku: json['sku'] as String?,
      sucursales: sucursales,
      totalDisponibleGlobal: json['total_disponible_global'] as int? ?? 0,
    );
  }
}

/// DTO para pieza de look complementario
class PiezaLookDto {
  final int idProducto;
  final String nombre;
  final String subtituloAtelier;
  final String categoria;
  final double precioBase;
  final double precioFinal;
  final String? imagenUrl;

  const PiezaLookDto({
    required this.idProducto,
    required this.nombre,
    required this.subtituloAtelier,
    required this.categoria,
    required this.precioBase,
    required this.precioFinal,
    this.imagenUrl,
  });

  factory PiezaLookDto.fromJson(Map<String, dynamic> json) {
    return PiezaLookDto(
      idProducto: json['id_producto'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Pieza de Look',
      subtituloAtelier: json['subtitulo_atelier'] as String? ?? 'ALTA COSTURA ATELIER',
      categoria: json['categoria'] as String? ?? 'Moda',
      precioBase: ProductoDetalleDto._toDouble(json['precio_base']),
      precioFinal: ProductoDetalleDto._toDouble(json['precio_final']),
      imagenUrl: json['imagen_url'] as String?,
    );
  }
}

/// Payload de entrada para crear una cita de reserva en boutique (CU12).
///
/// Los nombres serializados deben coincidir campo a campo con `ReservaCrearIn`
/// (Ec-backend/app/modules/reservas/cu12_reservar_prendas/esquemas.py). Cuando este DTO
/// enviaba `fecha_reserva`, `notas_cliente` y `lineas`, el endpoint respondía 422 en todos
/// los intentos porque además faltaba `items`, que es obligatorio.
class ReservaCrearInDto {
  final int idSucursal;
  final DateTime fechaHoraAtencion;
  final String canalOrigen;
  final String? observacion;
  final List<ReservaLineaInDto> lineas;

  const ReservaCrearInDto({
    required this.idSucursal,
    required this.fechaHoraAtencion,
    this.canalOrigen = 'movil',
    this.observacion,
    required this.lineas,
  });

  Map<String, dynamic> toJson() {
    return {
      'id_sucursal': idSucursal,
      'fecha_hora_atencion': fechaHoraAtencion.toIso8601String(),
      'canal_origen': canalOrigen,
      'observacion': observacion ?? 'Cita privada de prueba en boutique',
      'items': lineas.map((l) => l.toJson()).toList(),
    };
  }
}

class ReservaLineaInDto {
  final int idVariante;
  final int cantidad;

  const ReservaLineaInDto({
    required this.idVariante,
    this.cantidad = 1,
  });

  Map<String, dynamic> toJson() {
    return {
      'id_variante': idVariante,
      'cantidad': cantidad,
    };
  }
}

/// Respuesta de confirmación de reserva creada (CU12).
///
/// Espejo de `ReservaCreadaOut` (Ec-backend/app/modules/reservas/cu12_reservar_prendas/esquemas.py).
/// Antes leía `fecha_reserva`, `sucursal_nombre`, `total_prendas` y `mensaje`, claves que el
/// backend nunca envía: todos los campos caían en sus valores por defecto y el diálogo de
/// confirmación mostraba datos inventados en lugar de la reserva real.
class ReservaCreadaOutDto {
  final int idReserva;
  final String codigoReserva;
  final String estado;
  final String fechaHoraAtencion;
  final String sucursalNombre;
  final String direccionSucursal;
  final List<ReservaItemOutDto> items;
  final String mensaje;
  final List<String> cortesiasIncluidas;

  const ReservaCreadaOutDto({
    required this.idReserva,
    required this.codigoReserva,
    required this.estado,
    required this.fechaHoraAtencion,
    required this.sucursalNombre,
    this.direccionSucursal = '',
    this.items = const [],
    required this.mensaje,
    this.cortesiasIncluidas = const [],
  });

  /// El backend devuelve las líneas apartadas, no un total agregado.
  int get totalPrendas =>
      items.fold<int>(0, (suma, item) => suma + item.cantidad);

  factory ReservaCreadaOutDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];

    return ReservaCreadaOutDto(
      idReserva: json['id_reserva'] as int? ?? 0,
      codigoReserva: json['codigo_reserva'] as String? ?? 'RES-PENDIENTE',
      estado: json['estado'] as String? ?? 'pendiente',
      fechaHoraAtencion: json['fecha_hora_atencion'] as String? ?? '',
      sucursalNombre: json['nombre_sucursal'] as String? ?? 'Boutique Insignia',
      direccionSucursal: json['direccion_sucursal'] as String? ?? '',
      items: rawItems
          .map((i) => ReservaItemOutDto.fromJson(i as Map<String, dynamic>))
          .toList(),
      mensaje: json['mensaje_confirmacion'] as String? ??
          'Reserva confirmada con éxito.',
      cortesiasIncluidas:
          (json['cortesias_incluidas'] as List<dynamic>? ?? [])
              .map((c) => c as String)
              .toList(),
    );
  }
}

/// Línea de prenda apartada en la cita, espejo de `ReservaItemOut`.
class ReservaItemOutDto {
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String tallaCodigo;
  final String colorNombre;
  final int cantidad;
  final double precioUnitario;

  const ReservaItemOutDto({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.tallaCodigo,
    required this.colorNombre,
    required this.cantidad,
    required this.precioUnitario,
  });

  factory ReservaItemOutDto.fromJson(Map<String, dynamic> json) {
    return ReservaItemOutDto(
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      nombreProducto: json['nombre_producto'] as String? ?? '',
      tallaCodigo: json['talla_codigo'] as String? ?? '',
      colorNombre: json['color_nombre'] as String? ?? '',
      cantidad: json['cantidad'] as int? ?? 1,
      // FastAPI serializa Decimal como string JSON.
      precioUnitario: ProductoDetalleDto._toDouble(json['precio_unitario']),
    );
  }
}
