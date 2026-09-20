/// DTO para la metadata de paginación del catálogo en Ec-mobile.
class PaginacionDto {
  final int totalRegistros;
  final int paginaActual;
  final int limite;
  final int totalPaginas;
  final bool tieneSiguiente;
  final bool tieneAnterior;

  const PaginacionDto({
    required this.totalRegistros,
    required this.paginaActual,
    required this.limite,
    required this.totalPaginas,
    required this.tieneSiguiente,
    required this.tieneAnterior,
  });

  factory PaginacionDto.fromJson(Map<String, dynamic> json) {
    return PaginacionDto(
      totalRegistros: json['total_registros'] as int? ?? 0,
      paginaActual: json['pagina_actual'] as int? ?? 1,
      limite: json['limite'] as int? ?? 12,
      totalPaginas: json['total_paginas'] as int? ?? 1,
      tieneSiguiente: json['tiene_siguiente'] as bool? ?? false,
      tieneAnterior: json['tiene_anterior'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'total_registros': totalRegistros,
      'pagina_actual': paginaActual,
      'limite': limite,
      'total_paginas': totalPaginas,
      'tiene_siguiente': tieneSiguiente,
      'tiene_anterior': tieneAnterior,
    };
  }

  factory PaginacionDto.vacio() {
    return const PaginacionDto(
      totalRegistros: 0,
      paginaActual: 1,
      limite: 12,
      totalPaginas: 1,
      tieneSiguiente: false,
      tieneAnterior: false,
    );
  }
}
