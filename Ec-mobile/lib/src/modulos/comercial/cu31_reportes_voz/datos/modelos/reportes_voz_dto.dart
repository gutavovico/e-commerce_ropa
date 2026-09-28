import 'package:flutter/foundation.dart';

/// Peticion enviada al endpoint de interpretacion semantica de voz.
@immutable
class ComandoVozIn {
  final String textoDictado;

  const ComandoVozIn({required this.textoDictado});

  Map<String, dynamic> toJson() => {
        'texto_dictado': textoDictado,
      };
}

/// Respuesta estructurada emitida por el parser semantico de voz.
@immutable
class ComandoVozOut {
  final String textoDictado;
  final String intencion;
  final String modulo;
  final String formato;
  final String periodo;
  final int? idSucursal;
  final String? nombreSucursal;
  final String? fechaInicio;
  final String? fechaFin;
  final double confianza;
  final String accionRecomendada;

  const ComandoVozOut({
    required this.textoDictado,
    required this.intencion,
    required this.modulo,
    required this.formato,
    required this.periodo,
    this.idSucursal,
    this.nombreSucursal,
    this.fechaInicio,
    this.fechaFin,
    required this.confianza,
    required this.accionRecomendada,
  });

  factory ComandoVozOut.fromJson(Map<String, dynamic> json) {
    return ComandoVozOut(
      textoDictado: json['texto_dictado'] as String? ?? '',
      intencion: json['intencion'] as String? ?? 'consultar',
      modulo: json['modulo'] as String? ?? 'ventas',
      formato: json['formato'] as String? ?? 'excel',
      periodo: json['periodo'] as String? ?? 'este_mes',
      idSucursal: json['id_sucursal'] as int?,
      nombreSucursal: json['nombre_sucursal'] as String?,
      fechaInicio: json['fecha_inicio'] as String?,
      fechaFin: json['fecha_fin'] as String?,
      confianza: (json['confianza'] as num?)?.toDouble() ?? 0.85,
      accionRecomendada:
          json['accion_recomendada'] as String? ?? 'actualizar_filtros',
    );
  }
}

/// Filtros operativos para calcular previsualizacion o exportar reporte.
@immutable
class ReporteFiltrosDto {
  final String modulo;
  final String formato;
  final String periodo;
  final int? idSucursal;
  final String? fechaInicio;
  final String? fechaFin;

  const ReporteFiltrosDto({
    this.modulo = 'ventas',
    this.formato = 'excel',
    this.periodo = 'este_mes',
    this.idSucursal,
    this.fechaInicio,
    this.fechaFin,
  });

  ReporteFiltrosDto copyWith({
    String? modulo,
    String? formato,
    String? periodo,
    int? idSucursal,
    bool resetSucursal = false,
    String? fechaInicio,
    String? fechaFin,
  }) {
    return ReporteFiltrosDto(
      modulo: modulo ?? this.modulo,
      formato: formato ?? this.formato,
      periodo: periodo ?? this.periodo,
      idSucursal: resetSucursal ? null : (idSucursal ?? this.idSucursal),
      fechaInicio: fechaInicio ?? this.fechaInicio,
      fechaFin: fechaFin ?? this.fechaFin,
    );
  }

  Map<String, dynamic> toJson() => {
        'modulo': modulo,
        'formato': formato,
        'periodo': periodo,
        'id_sucursal': idSucursal,
        'fecha_inicio': fechaInicio,
        'fecha_fin': fechaFin,
      };
}

/// Resumen preliminar con conteo y metricas financieras calculadas.
@immutable
class ReportePrevisualizacionDto {
  final String modulo;
  final String formato;
  final int totalRegistros;
  final String fechaCorte;
  final String nombreArchivoSugerido;
  final Map<String, dynamic>? resumenFinanciero;

  const ReportePrevisualizacionDto({
    required this.modulo,
    required this.formato,
    required this.totalRegistros,
    required this.fechaCorte,
    required this.nombreArchivoSugerido,
    this.resumenFinanciero,
  });

  factory ReportePrevisualizacionDto.fromJson(Map<String, dynamic> json) {
    return ReportePrevisualizacionDto(
      modulo: json['modulo'] as String? ?? 'ventas',
      formato: json['formato'] as String? ?? 'excel',
      totalRegistros: json['total_registros'] as int? ?? 0,
      fechaCorte: json['fecha_corte'] as String? ?? '',
      nombreArchivoSugerido: json['nombre_archivo_sugerido'] as String? ?? '',
      resumenFinanciero: json['resumen_financiero'] != null
          ? Map<String, dynamic>.from(json['resumen_financiero'] as Map)
          : null,
    );
  }
}

/// Opcion de sucursal para el selector interactivo.
@immutable
class SucursalOpcionDto {
  final int idSucursal;
  final String nombre;
  final String? ciudad;

  const SucursalOpcionDto({
    required this.idSucursal,
    required this.nombre,
    this.ciudad,
  });

  factory SucursalOpcionDto.fromJson(Map<String, dynamic> json) {
    return SucursalOpcionDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Sucursal',
      ciudad: json['ciudad'] as String?,
    );
  }
}
