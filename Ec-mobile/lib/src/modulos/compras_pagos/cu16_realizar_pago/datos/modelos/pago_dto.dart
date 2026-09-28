/// DTO de CU16: Realizar Pago Electrónico.
///
/// Son el espejo exacto de los esquemas Pydantic del backend, en
/// `Ec-backend/app/modules/compras_pagos/cu16_realizar_pago/esquemas.py`. Los nombres de las
/// claves JSON se transcriben literalmente: un desajuste no rompe la compilación y sólo se
/// manifiesta como campos vacíos en pantalla, que es justo lo que ocultó los defectos de
/// contrato de CU07/CU12 y el que arrastraba `pago.model.ts` en Web hasta que se corrigió.
///
/// FastAPI serializa `Decimal` como cadena JSON (`"890.00"`), de modo que todo importe se
/// convierte con parseo tolerante y nunca con un `as num` directo.
library;

import '../../../cu11_gestionar_carrito/datos/modelos/carrito_dto.dart' show parsearImporte;

/// Línea de la orden con el precio ya congelado por CU15.
class PagoItemDto {
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String tallaCodigo;
  final String colorNombre;
  final String? imagenUrl;
  final int cantidad;
  final double precioUnitario;
  final double subtotalLinea;
  final String? nombreSucursal;

  const PagoItemDto({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.tallaCodigo,
    required this.colorNombre,
    this.imagenUrl,
    required this.cantidad,
    this.precioUnitario = 0.0,
    this.subtotalLinea = 0.0,
    this.nombreSucursal,
  });

  factory PagoItemDto.fromJson(Map<String, dynamic> json) {
    return PagoItemDto(
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      nombreProducto: json['nombre_producto'] as String? ?? '',
      tallaCodigo: json['talla_codigo'] as String? ?? '-',
      colorNombre: json['color_nombre'] as String? ?? '-',
      imagenUrl: json['imagen_url'] as String?,
      cantidad: json['cantidad'] as int? ?? 0,
      precioUnitario: parsearImporte(json['precio_unitario']),
      subtotalLinea: parsearImporte(json['subtotal_linea']),
      nombreSucursal: json['nombre_sucursal'] as String?,
    );
  }
}

/// Datos necesarios para inicializar la pasarela sobre una orden `pendiente`
/// (`GET /api/v1/ventas/{id_venta}/resumen-pago`).
class ResumenPagoDto {
  final int idVenta;
  final String numeroComprobante;
  final String estado;

  final double subtotal;
  final double descuento;
  final double total;
  final double ivaIncluido;
  final String moneda;
  final int totalPrendas;

  final List<PagoItemDto> items;

  final String tipoEntrega;
  final String? direccionEnvio;
  final String? nombreSucursalRetiro;
  final String? nombreCliente;

  final DateTime? fechaVenta;
  final DateTime? expiraEn;

  /// Calculado en el servidor: el cliente no debe derivarlo de su propio reloj.
  final int segundosRestantes;
  final List<String> metodosDisponibles;

  const ResumenPagoDto({
    required this.idVenta,
    required this.numeroComprobante,
    this.estado = 'pendiente',
    this.subtotal = 0.0,
    this.descuento = 0.0,
    this.total = 0.0,
    this.ivaIncluido = 0.0,
    this.moneda = 'EUR',
    this.totalPrendas = 0,
    this.items = const [],
    this.tipoEntrega = 'domicilio',
    this.direccionEnvio,
    this.nombreSucursalRetiro,
    this.nombreCliente,
    this.fechaVenta,
    this.expiraEn,
    this.segundosRestantes = 0,
    this.metodosDisponibles = const [],
  });

  bool get esRecogidaBoutique => tipoEntrega == 'recogida_boutique';

  factory ResumenPagoDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    final rawMetodos = json['metodos_disponibles'] as List<dynamic>? ?? [];

    return ResumenPagoDto(
      idVenta: json['id_venta'] as int? ?? 0,
      numeroComprobante: json['numero_comprobante'] as String? ?? '',
      estado: json['estado'] as String? ?? 'pendiente',
      subtotal: parsearImporte(json['subtotal']),
      descuento: parsearImporte(json['descuento']),
      total: parsearImporte(json['total']),
      ivaIncluido: parsearImporte(json['iva_incluido']),
      moneda: json['moneda'] as String? ?? 'EUR',
      totalPrendas: json['total_prendas'] as int? ?? 0,
      items: rawItems.map((i) => PagoItemDto.fromJson(i as Map<String, dynamic>)).toList(),
      tipoEntrega: json['tipo_entrega'] as String? ?? 'domicilio',
      direccionEnvio: json['direccion_envio'] as String?,
      nombreSucursalRetiro: json['nombre_sucursal_retiro'] as String?,
      nombreCliente: json['nombre_cliente'] as String?,
      fechaVenta: DateTime.tryParse(json['fecha_venta']?.toString() ?? ''),
      expiraEn: DateTime.tryParse(json['expira_en']?.toString() ?? ''),
      segundosRestantes: json['segundos_restantes'] as int? ?? 0,
      metodosDisponibles: rawMetodos.map((m) => m.toString()).toList(),
    );
  }
}

/// Escenario determinista que el simulador del backend usa para decidir el desenlace de
/// `confirmar_pago` cuando no hay `STRIPE_SECRET_KEY` real configurada. Con Stripe real este
/// parámetro no existe en la API y se ignora.
enum EscenarioPrueba { aprobado, rechazado, fondosInsuficientes }

extension EscenarioPruebaJson on EscenarioPrueba {
  String get valorJson => switch (this) {
        EscenarioPrueba.aprobado => 'aprobado',
        EscenarioPrueba.rechazado => 'rechazado',
        EscenarioPrueba.fondosInsuficientes => 'fondos_insuficientes',
      };
}

/// Payload de `POST /api/v1/pagos/intentos`.
///
/// No lleva ningún dato de tarjeta: el backend nunca recibe el PAN ni el CVV (revisado el
/// 2026-09-28). Ver `PagoIntentoOutDto` y la nota de §A.2 en `spec.md` de CU16.
class PagoIniciarInDto {
  final int idVenta;
  final String metodoPago;
  final String? claveIdempotencia;
  final EscenarioPrueba? escenarioPrueba;

  const PagoIniciarInDto({
    required this.idVenta,
    required this.metodoPago,
    this.claveIdempotencia,
    this.escenarioPrueba,
  });

  Map<String, dynamic> toJson() => {
        'id_venta': idVenta,
        'metodo_pago': metodoPago,
        if (claveIdempotencia != null) 'clave_idempotencia': claveIdempotencia,
        if (escenarioPrueba != null) 'escenario_prueba': escenarioPrueba!.valorJson,
      };
}

/// Respuesta de `POST /api/v1/pagos/intentos`: lo que el cliente necesita para confirmar el
/// `PaymentIntent` directamente contra Stripe, sin pasar por este backend.
class PagoIntentoOutDto {
  final int idPago;
  final String? clientSecret;
  final bool yaConfirmado;
  final PagoConfirmadoDto? confirmacion;

  const PagoIntentoOutDto({
    required this.idPago,
    this.clientSecret,
    this.yaConfirmado = false,
    this.confirmacion,
  });

  factory PagoIntentoOutDto.fromJson(Map<String, dynamic> json) {
    final confirmacionJson = json['confirmacion'] as Map<String, dynamic>?;
    return PagoIntentoOutDto(
      idPago: json['id_pago'] as int? ?? 0,
      clientSecret: json['client_secret'] as String?,
      yaConfirmado: json['ya_confirmado'] as bool? ?? false,
      confirmacion:
          confirmacionJson != null ? PagoConfirmadoDto.fromJson(confirmacionJson) : null,
    );
  }
}

/// Confirmación del cobro (`PagoConfirmadoOut`).
///
/// `estadoPago` llega `confirmado` para tarjeta/Bizum/PayPal, con `confirmadoEn` resuelto.
class PagoConfirmadoDto {
  final int idPago;
  final int idVenta;
  final String numeroComprobante;
  final String estadoPago;
  final String estadoVenta;
  final String metodoPago;

  final String? referenciaPasarela;
  final double monto;
  final String moneda;

  final String? marcaTarjeta;
  final String? ultimosDigitos;

  final DateTime? confirmadoEn;
  final String mensajeConfirmacion;

  const PagoConfirmadoDto({
    required this.idPago,
    required this.idVenta,
    required this.numeroComprobante,
    this.estadoPago = 'confirmado',
    this.estadoVenta = 'pagada',
    required this.metodoPago,
    this.referenciaPasarela,
    this.monto = 0.0,
    this.moneda = 'EUR',
    this.marcaTarjeta,
    this.ultimosDigitos,
    this.confirmadoEn,
    this.mensajeConfirmacion = 'Pago confirmado.',
  });

  factory PagoConfirmadoDto.fromJson(Map<String, dynamic> json) {
    return PagoConfirmadoDto(
      idPago: json['id_pago'] as int? ?? 0,
      idVenta: json['id_venta'] as int? ?? 0,
      numeroComprobante: json['numero_comprobante'] as String? ?? '',
      estadoPago: json['estado_pago'] as String? ?? 'confirmado',
      estadoVenta: json['estado_venta'] as String? ?? 'pagada',
      metodoPago: json['metodo_pago'] as String? ?? '',
      referenciaPasarela: json['referencia_pasarela'] as String?,
      monto: parsearImporte(json['monto']),
      moneda: json['moneda'] as String? ?? 'EUR',
      marcaTarjeta: json['marca_tarjeta'] as String?,
      ultimosDigitos: json['ultimos_digitos'] as String?,
      confirmadoEn: json['confirmado_en'] != null
          ? DateTime.tryParse(json['confirmado_en'].toString())
          : null,
      mensajeConfirmacion:
          json['mensaje_confirmacion'] as String? ?? 'Pago confirmado.',
    );
  }
}
