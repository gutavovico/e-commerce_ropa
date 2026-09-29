/// DTOs de CU13 (Consultar y cancelar reservas) y CU14 (Consultar estado de reserva).
///
/// Espejo exacto de los esquemas Pydantic del backend en
/// `Ec-backend/app/modules/reservas/cu13_consultar_cancelar_reservas/esquemas.py`. Un único
/// `ReservaDto` cubre ambos casos de uso: ya expone el estado completo de la cita.
///
/// FastAPI serializa `Decimal` como cadena JSON, así que `precio_unitario` se parsea con
/// `parsearImporte`, nunca con un `as num` directo.
library;

import '../../../../compras_pagos/cu11_gestionar_carrito/datos/modelos/carrito_dto.dart'
    show parsearImporte;

class ReservaItemDto {
  final int idVariante;
  final String nombreProducto;
  final String tallaCodigo;
  final String colorNombre;
  final String? colorHex;
  final String? imagenUrl;
  final int cantidad;
  final double precioUnitario;

  const ReservaItemDto({
    required this.idVariante,
    required this.nombreProducto,
    required this.tallaCodigo,
    required this.colorNombre,
    this.colorHex,
    this.imagenUrl,
    required this.cantidad,
    this.precioUnitario = 0.0,
  });

  factory ReservaItemDto.fromJson(Map<String, dynamic> json) {
    return ReservaItemDto(
      idVariante: json['id_variante'] as int? ?? 0,
      nombreProducto: json['nombre_producto'] as String? ?? '',
      tallaCodigo: json['talla_codigo'] as String? ?? '-',
      colorNombre: json['color_nombre'] as String? ?? '-',
      colorHex: json['color_hex'] as String?,
      imagenUrl: json['imagen_url'] as String?,
      cantidad: json['cantidad'] as int? ?? 0,
      precioUnitario: parsearImporte(json['precio_unitario']),
    );
  }
}

class SucursalReservaDto {
  final int idSucursal;
  final String nombre;
  final String direccion;

  const SucursalReservaDto({
    required this.idSucursal,
    required this.nombre,
    required this.direccion,
  });

  factory SucursalReservaDto.fromJson(Map<String, dynamic> json) {
    return SucursalReservaDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? '',
      direccion: json['direccion'] as String? ?? '',
    );
  }
}

class ReservaDto {
  final int idReserva;
  final String codigoReserva;
  final String estado;
  final DateTime? fechaHoraAtencion;
  final DateTime? creadoEn;
  final SucursalReservaDto sucursal;
  final List<ReservaItemDto> items;
  final int totalPrendas;
  final String? observacion;

  /// Decidido en el servidor: el cliente no debe derivar por su cuenta si es cancelable.
  final bool puedeCancelar;

  const ReservaDto({
    required this.idReserva,
    required this.codigoReserva,
    this.estado = 'pendiente',
    this.fechaHoraAtencion,
    this.creadoEn,
    required this.sucursal,
    this.items = const [],
    this.totalPrendas = 0,
    this.observacion,
    this.puedeCancelar = false,
  });

  factory ReservaDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    return ReservaDto(
      idReserva: json['id_reserva'] as int? ?? 0,
      codigoReserva: json['codigo_reserva'] as String? ?? '',
      estado: json['estado'] as String? ?? 'pendiente',
      fechaHoraAtencion: DateTime.tryParse(json['fecha_hora_atencion']?.toString() ?? ''),
      creadoEn: DateTime.tryParse(json['creado_en']?.toString() ?? ''),
      sucursal: SucursalReservaDto.fromJson(
        json['sucursal'] as Map<String, dynamic>? ?? const {},
      ),
      items: rawItems.map((i) => ReservaItemDto.fromJson(i as Map<String, dynamic>)).toList(),
      totalPrendas: json['total_prendas'] as int? ?? 0,
      observacion: json['observacion'] as String?,
      puedeCancelar: json['puede_cancelar'] as bool? ?? false,
    );
  }
}

class ResumenProximaReservaDto {
  final int idReserva;
  final DateTime? fechaHoraAtencion;
  final String nombreSucursal;

  const ResumenProximaReservaDto({
    required this.idReserva,
    this.fechaHoraAtencion,
    required this.nombreSucursal,
  });

  factory ResumenProximaReservaDto.fromJson(Map<String, dynamic> json) {
    return ResumenProximaReservaDto(
      idReserva: json['id_reserva'] as int? ?? 0,
      fechaHoraAtencion: DateTime.tryParse(json['fecha_hora_atencion']?.toString() ?? ''),
      nombreSucursal: json['nombre_sucursal'] as String? ?? '',
    );
  }
}

class ResumenReservasDto {
  final int activas;
  final ResumenProximaReservaDto? proxima;

  const ResumenReservasDto({this.activas = 0, this.proxima});

  factory ResumenReservasDto.fromJson(Map<String, dynamic> json) {
    final proximaJson = json['proxima'] as Map<String, dynamic>?;
    return ResumenReservasDto(
      activas: json['activas'] as int? ?? 0,
      proxima: proximaJson != null ? ResumenProximaReservaDto.fromJson(proximaJson) : null,
    );
  }
}

class MisReservasDto {
  final ResumenReservasDto resumen;
  final List<ReservaDto> proximas;
  final List<ReservaDto> historial;

  const MisReservasDto({
    this.resumen = const ResumenReservasDto(),
    this.proximas = const [],
    this.historial = const [],
  });

  factory MisReservasDto.fromJson(Map<String, dynamic> json) {
    final proximasJson = json['proximas'] as List<dynamic>? ?? [];
    final historialJson = json['historial'] as List<dynamic>? ?? [];
    return MisReservasDto(
      resumen: ResumenReservasDto.fromJson(json['resumen'] as Map<String, dynamic>? ?? const {}),
      proximas: proximasJson.map((r) => ReservaDto.fromJson(r as Map<String, dynamic>)).toList(),
      historial: historialJson.map((r) => ReservaDto.fromJson(r as Map<String, dynamic>)).toList(),
    );
  }
}
