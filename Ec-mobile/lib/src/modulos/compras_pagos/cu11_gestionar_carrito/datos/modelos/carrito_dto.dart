/// DTO de la Bolsa de Compra (CU11) y de la tramitación del pedido (CU15).
///
/// Son el espejo exacto de los esquemas Pydantic del backend, en
/// `Ec-backend/app/modules/compras_pagos/`. Los nombres de las claves JSON se transcriben
/// literalmente: un desajuste no rompe la compilación y sólo se manifiesta como campos vacíos
/// en pantalla, que es justo lo que ocurrió con la reserva y la galería de CU07/CU12.
///
/// FastAPI serializa `Decimal` como cadena JSON (`"890.00"`), de modo que todo importe se
/// convierte con parseo tolerante y nunca con un `as num` directo.
library;

/// Convierte a `double` un valor que puede llegar como cadena, entero o decimal.
double parsearImporte(dynamic valor) {
  if (valor == null) return 0.0;
  if (valor is num) return valor.toDouble();
  return double.tryParse(valor.toString()) ?? 0.0;
}

/// Una prenda de la bolsa, con su precio, boutique de expedición y stock vigente.
class CarritoItemDto {
  final int idCarritoDetalle;
  final int idVariante;
  final int idProducto;
  final String nombreProducto;
  final String? lineaConfeccion;
  final String sku;
  final String tallaCodigo;
  final String colorNombre;
  final String? colorHex;
  final String? imagenUrl;

  final double precioLista;
  final double precioUnitario;
  final double descuentoLinea;
  final String? motivoDescuento;

  final int cantidad;
  final int idSucursal;
  final String nombreSucursal;
  final int stockDisponible;

  /// Tope para el botón «+»: evita una llamada extra para conocer el límite.
  final int cantidadMaxima;
  final double subtotalLinea;

  const CarritoItemDto({
    required this.idCarritoDetalle,
    required this.idVariante,
    required this.idProducto,
    required this.nombreProducto,
    this.lineaConfeccion,
    required this.sku,
    required this.tallaCodigo,
    required this.colorNombre,
    this.colorHex,
    this.imagenUrl,
    required this.precioLista,
    required this.precioUnitario,
    this.descuentoLinea = 0.0,
    this.motivoDescuento,
    required this.cantidad,
    required this.idSucursal,
    required this.nombreSucursal,
    required this.stockDisponible,
    required this.cantidadMaxima,
    required this.subtotalLinea,
  });

  bool get tieneDescuento => descuentoLinea > 0;
  bool get alcanzoElMaximo => cantidad >= cantidadMaxima;

  factory CarritoItemDto.fromJson(Map<String, dynamic> json) {
    return CarritoItemDto(
      idCarritoDetalle: json['id_carrito_detalle'] as int? ?? 0,
      idVariante: json['id_variante'] as int? ?? 0,
      idProducto: json['id_producto'] as int? ?? 0,
      nombreProducto: json['nombre_producto'] as String? ?? 'Prenda Atelier',
      lineaConfeccion: json['linea_confeccion'] as String?,
      sku: json['sku'] as String? ?? '',
      tallaCodigo: json['talla_codigo'] as String? ?? '-',
      colorNombre: json['color_nombre'] as String? ?? '-',
      colorHex: json['color_hex'] as String?,
      imagenUrl: json['imagen_url'] as String?,
      precioLista: parsearImporte(json['precio_lista']),
      precioUnitario: parsearImporte(json['precio_unitario']),
      descuentoLinea: parsearImporte(json['descuento_linea']),
      motivoDescuento: json['motivo_descuento'] as String?,
      cantidad: json['cantidad'] as int? ?? 1,
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombreSucursal: json['nombre_sucursal'] as String? ?? 'Boutique',
      stockDisponible: json['stock_disponible'] as int? ?? 0,
      cantidadMaxima: json['cantidad_maxima'] as int? ?? 0,
      subtotalLinea: parsearImporte(json['subtotal_linea']),
    );
  }
}

/// Resumen financiero de la bolsa.
///
/// `subtotal` agrega precios de lista y `descuento` el ahorro aplicado, de modo que siempre se
/// cumple `total = subtotal - descuento`.
class CarritoResumenDto {
  final int totalPrendas;
  final int totalLineas;
  final double subtotal;
  final double descuento;
  final double total;

  /// IVA contenido en el total (21 %). Informativo: los precios ya lo incluyen.
  final double ivaIncluido;
  final String moneda;

  const CarritoResumenDto({
    this.totalPrendas = 0,
    this.totalLineas = 0,
    this.subtotal = 0.0,
    this.descuento = 0.0,
    this.total = 0.0,
    this.ivaIncluido = 0.0,
    this.moneda = 'EUR',
  });

  bool get tieneDescuento => descuento > 0;

  factory CarritoResumenDto.fromJson(Map<String, dynamic> json) {
    return CarritoResumenDto(
      totalPrendas: json['total_prendas'] as int? ?? 0,
      totalLineas: json['total_lineas'] as int? ?? 0,
      subtotal: parsearImporte(json['subtotal']),
      descuento: parsearImporte(json['descuento']),
      total: parsearImporte(json['total']),
      ivaIncluido: parsearImporte(json['iva_incluido']),
      moneda: json['moneda'] as String? ?? 'EUR',
    );
  }
}

/// Boutique desde la que se expide parte de la bolsa.
class SucursalExpedicionDto {
  final int idSucursal;
  final String nombre;
  final int totalLineas;

  const SucursalExpedicionDto({
    required this.idSucursal,
    required this.nombre,
    required this.totalLineas,
  });

  factory SucursalExpedicionDto.fromJson(Map<String, dynamic> json) {
    return SucursalExpedicionDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Boutique',
      totalLineas: json['total_lineas'] as int? ?? 0,
    );
  }
}

/// Contrato consolidado de `GET /api/v1/carrito`.
class CarritoDto {
  final int idCarrito;
  final List<CarritoItemDto> items;
  final CarritoResumenDto resumen;

  /// Fin de la ventana informativa (línea más antigua + 25 min).
  /// NO retiene existencias: la garantía firme se obtiene al tramitar el pedido.
  final DateTime? expiraEn;
  final List<SucursalExpedicionDto> sucursalesExpedicion;

  const CarritoDto({
    required this.idCarrito,
    this.items = const [],
    this.resumen = const CarritoResumenDto(),
    this.expiraEn,
    this.sucursalesExpedicion = const [],
  });

  bool get estaVacia => items.isEmpty;
  bool get haySucursalesMultiples => sucursalesExpedicion.length > 1;

  static const CarritoDto vacio = CarritoDto(idCarrito: 0);

  factory CarritoDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];
    final rawSucursales = json['sucursales_expedicion'] as List<dynamic>? ?? [];
    final rawExpira = json['expira_en'] as String?;

    return CarritoDto(
      idCarrito: json['id_carrito'] as int? ?? 0,
      items: rawItems
          .map((i) => CarritoItemDto.fromJson(i as Map<String, dynamic>))
          .toList(),
      resumen: CarritoResumenDto.fromJson(
        json['resumen'] as Map<String, dynamic>? ?? const {},
      ),
      expiraEn: rawExpira == null ? null : DateTime.tryParse(rawExpira),
      sucursalesExpedicion: rawSucursales
          .map((s) => SucursalExpedicionDto.fromJson(s as Map<String, dynamic>))
          .toList(),
    );
  }
}

/// Payload de `POST /api/v1/carrito/items`.
class ItemAgregarInDto {
  final int idVariante;
  final int cantidad;

  /// Si se omite, el backend elige la boutique con mayor disponibilidad.
  final int? idSucursal;

  const ItemAgregarInDto({
    required this.idVariante,
    this.cantidad = 1,
    this.idSucursal,
  });

  Map<String, dynamic> toJson() {
    final datos = <String, dynamic>{
      'id_variante': idVariante,
      'cantidad': cantidad,
    };
    if (idSucursal != null) {
      datos['id_sucursal'] = idSucursal;
    }
    return datos;
  }
}

// ---------------------------------------------------------------------------
// CU15 — Tramitación del pedido
// ---------------------------------------------------------------------------

/// Modalidades de entrega admitidas, alineadas con el CHECK de PostgreSQL.
enum TipoEntrega {
  domicilio('domicilio'),
  recogidaBoutique('recogida_boutique');

  final String valor;
  const TipoEntrega(this.valor);
}

/// Payload de `POST /api/v1/ventas/checkout`.
///
/// Deliberadamente no incluye importes: el servidor recalcula subtotal, descuento y total, e
/// ignora cualquier cifra que envíe el cliente.
class CheckoutInDto {
  final TipoEntrega tipoEntrega;
  final String? direccionEnvio;
  final int? idSucursalRetiro;
  final String? codigoCupon;

  const CheckoutInDto({
    required this.tipoEntrega,
    this.direccionEnvio,
    this.idSucursalRetiro,
    this.codigoCupon,
  });

  Map<String, dynamic> toJson() {
    return {
      'tipo_venta': 'digital_movil',
      'tipo_entrega': tipoEntrega.valor,
      'direccion_envio':
          tipoEntrega == TipoEntrega.domicilio ? direccionEnvio?.trim() : null,
      'id_sucursal_retiro':
          tipoEntrega == TipoEntrega.recogidaBoutique ? idSucursalRetiro : null,
      'codigo_cupon': codigoCupon,
    };
  }
}

/// Línea de la orden con el precio ya congelado.
class VentaItemDto {
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

  const VentaItemDto({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.tallaCodigo,
    required this.colorNombre,
    this.imagenUrl,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotalLinea,
    this.nombreSucursal,
  });

  factory VentaItemDto.fromJson(Map<String, dynamic> json) {
    return VentaItemDto(
      idVariante: json['id_variante'] as int? ?? 0,
      sku: json['sku'] as String? ?? '',
      nombreProducto: json['nombre_producto'] as String? ?? '',
      tallaCodigo: json['talla_codigo'] as String? ?? '-',
      colorNombre: json['color_nombre'] as String? ?? '-',
      imagenUrl: json['imagen_url'] as String?,
      cantidad: json['cantidad'] as int? ?? 1,
      precioUnitario: parsearImporte(json['precio_unitario']),
      subtotalLinea: parsearImporte(json['subtotal_linea']),
      nombreSucursal: json['nombre_sucursal'] as String?,
    );
  }
}

/// Espejo de `VentaCreadaOut`: la orden lista para la pasarela de pago (CU16).
class VentaCreadaDto {
  final int idVenta;
  final String numeroComprobante;
  final String estado;
  final String tipoEntrega;
  final String? direccionEnvio;
  final String? nombreSucursalRetiro;

  final double subtotal;
  final double descuento;
  final double total;
  final double ivaIncluido;

  final String? cuponAplicado;
  final String? nombrePromocion;

  final List<VentaItemDto> items;
  final int totalPrendas;

  final DateTime? fechaVenta;

  /// Vencimiento de la retención de existencias (fecha_venta + 25 min).
  final DateTime? expiraEn;
  final String mensajeConfirmacion;

  const VentaCreadaDto({
    required this.idVenta,
    required this.numeroComprobante,
    this.estado = 'pendiente',
    this.tipoEntrega = 'domicilio',
    this.direccionEnvio,
    this.nombreSucursalRetiro,
    this.subtotal = 0.0,
    this.descuento = 0.0,
    this.total = 0.0,
    this.ivaIncluido = 0.0,
    this.cuponAplicado,
    this.nombrePromocion,
    this.items = const [],
    this.totalPrendas = 0,
    this.fechaVenta,
    this.expiraEn,
    this.mensajeConfirmacion = 'Tu orden ha sido registrada.',
  });

  factory VentaCreadaDto.fromJson(Map<String, dynamic> json) {
    final rawItems = json['items'] as List<dynamic>? ?? [];

    return VentaCreadaDto(
      idVenta: json['id_venta'] as int? ?? 0,
      numeroComprobante: json['numero_comprobante'] as String? ?? 'FS-PENDIENTE',
      estado: json['estado'] as String? ?? 'pendiente',
      tipoEntrega: json['tipo_entrega'] as String? ?? 'domicilio',
      direccionEnvio: json['direccion_envio'] as String?,
      nombreSucursalRetiro: json['nombre_sucursal_retiro'] as String?,
      subtotal: parsearImporte(json['subtotal']),
      descuento: parsearImporte(json['descuento']),
      total: parsearImporte(json['total']),
      ivaIncluido: parsearImporte(json['iva_incluido']),
      cuponAplicado: json['cupon_aplicado'] as String?,
      nombrePromocion: json['nombre_promocion'] as String?,
      items: rawItems
          .map((i) => VentaItemDto.fromJson(i as Map<String, dynamic>))
          .toList(),
      totalPrendas: json['total_prendas'] as int? ?? 0,
      fechaVenta: DateTime.tryParse(json['fecha_venta']?.toString() ?? ''),
      expiraEn: DateTime.tryParse(json['expira_en']?.toString() ?? ''),
      mensajeConfirmacion:
          json['mensaje_confirmacion'] as String? ?? 'Tu orden ha sido registrada.',
    );
  }
}

/// Boutique del directorio de `GET /api/v1/sucursales/activas`.
class BoutiqueRecogidaDto {
  final int idSucursal;
  final String nombre;
  final String ciudad;
  final String direccion;

  const BoutiqueRecogidaDto({
    required this.idSucursal,
    required this.nombre,
    required this.ciudad,
    required this.direccion,
  });

  factory BoutiqueRecogidaDto.fromJson(Map<String, dynamic> json) {
    return BoutiqueRecogidaDto(
      idSucursal: json['id_sucursal'] as int? ?? 0,
      nombre: json['nombre'] as String? ?? 'Boutique',
      ciudad: json['ciudad'] as String? ?? '',
      direccion: json['direccion'] as String? ?? '',
    );
  }
}
