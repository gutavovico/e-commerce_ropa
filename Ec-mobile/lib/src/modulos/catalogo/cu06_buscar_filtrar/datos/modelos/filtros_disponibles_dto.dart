/// DTOs para las opciones de filtros disponibles entregadas por el backend.
class TemporadaFiltroDto {
  final int id;
  final String nombre;
  final String tipo;
  final bool activa;

  const TemporadaFiltroDto({
    required this.id,
    required this.nombre,
    required this.tipo,
    required this.activa,
  });

  factory TemporadaFiltroDto.fromJson(Map<String, dynamic> json) {
    return TemporadaFiltroDto(
      id: json['id'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      tipo: json['tipo'] as String? ?? '',
      activa: json['activa'] as bool? ?? true,
    );
  }
}

class ColeccionFiltroDto {
  final int id;
  final String nombre;
  final int idTemporada;
  final int totalPrendas;

  const ColeccionFiltroDto({
    required this.id,
    required this.nombre,
    required this.idTemporada,
    required this.totalPrendas,
  });

  factory ColeccionFiltroDto.fromJson(Map<String, dynamic> json) {
    return ColeccionFiltroDto(
      id: json['id'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      idTemporada: json['id_temporada'] as int? ?? 0,
      totalPrendas: json['total_prendas'] as int? ?? 0,
    );
  }
}

class TallaFiltroDto {
  final int id;
  final String codigo;
  final int orden;

  const TallaFiltroDto({
    required this.id,
    required this.codigo,
    required this.orden,
  });

  factory TallaFiltroDto.fromJson(Map<String, dynamic> json) {
    return TallaFiltroDto(
      id: json['id'] as int? ?? 0,
      codigo: json['codigo'] as String? ?? '',
      orden: json['orden'] as int? ?? 0,
    );
  }
}

class ColorFiltroDto {
  final int id;
  final String nombre;
  final String codigoHex;

  const ColorFiltroDto({
    required this.id,
    required this.nombre,
    required this.codigoHex,
  });

  factory ColorFiltroDto.fromJson(Map<String, dynamic> json) {
    return ColorFiltroDto(
      id: json['id'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      codigoHex: json['codigo_hex'] as String? ?? '#000000',
    );
  }
}

class RangoPreciosDto {
  final double min;
  final double max;

  const RangoPreciosDto({
    required this.min,
    required this.max,
  });

  factory RangoPreciosDto.fromJson(Map<String, dynamic> json) {
    return RangoPreciosDto(
      min: double.tryParse(json['min']?.toString() ?? '0.0') ?? 0.0,
      max: double.tryParse(json['max']?.toString() ?? '2500.0') ?? 2500.0,
    );
  }
}

class FiltrosDisponiblesDto {
  final List<TemporadaFiltroDto> temporadas;
  final List<ColeccionFiltroDto> colecciones;
  final List<TallaFiltroDto> tallas;
  final List<ColorFiltroDto> colores;
  final RangoPreciosDto rangoPrecios;

  const FiltrosDisponiblesDto({
    required this.temporadas,
    required this.colecciones,
    required this.tallas,
    required this.colores,
    required this.rangoPrecios,
  });

  factory FiltrosDisponiblesDto.fromJson(Map<String, dynamic> json) {
    final rawTemp = json['temporadas'] as List<dynamic>? ?? [];
    final rawCol = json['colecciones'] as List<dynamic>? ?? [];
    final rawTal = json['tallas'] as List<dynamic>? ?? [];
    final rawColor = json['colores'] as List<dynamic>? ?? [];
    final rawPrecios = json['rango_precios'] as Map<String, dynamic>? ?? {};

    return FiltrosDisponiblesDto(
      temporadas: rawTemp.map((t) => TemporadaFiltroDto.fromJson(t as Map<String, dynamic>)).toList(),
      colecciones: rawCol.map((c) => ColeccionFiltroDto.fromJson(c as Map<String, dynamic>)).toList(),
      tallas: rawTal.map((t) => TallaFiltroDto.fromJson(t as Map<String, dynamic>)).toList(),
      colores: rawColor.map((c) => ColorFiltroDto.fromJson(c as Map<String, dynamic>)).toList(),
      rangoPrecios: RangoPreciosDto.fromJson(rawPrecios),
    );
  }
}
