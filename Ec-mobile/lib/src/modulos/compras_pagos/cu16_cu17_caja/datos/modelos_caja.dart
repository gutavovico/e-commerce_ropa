import 'package:flutter/foundation.dart';

/// P2-CU16 / CU17 · Contratos de `/api/v1/pos` (`cu31_cu32_punto_venta/esquemas.py`) y de
/// `/api/v1/mis-sucursales`. Los importes llegan como cadena (`Decimal`) y se conservan como `String`:
/// se muestran con `formatoImporte`, nunca se recalculan en el teléfono.

int _entero(Object? v, [int porDefecto = 0]) =>
    v is int ? v : (v is num ? v.toInt() : int.tryParse(v?.toString() ?? '') ?? porDefecto);
String _texto(Object? v) => v?.toString() ?? '';
String? _textoONulo(Object? v) => v?.toString();
DateTime? _fecha(Object? v) => DateTime.tryParse(v?.toString() ?? '');
List<Map<String, dynamic>> _lista(Object? v) => [for (final e in (v as List? ?? const [])) e as Map<String, dynamic>];

/// Métodos de cobro en caja (`MetodoPagoCaja`).
const List<String> metodosCobro = ['efectivo', 'tarjeta_debito', 'tarjeta_credito', 'qr', 'transferencia'];
const Map<String, String> nombreMetodo = {
  'efectivo': 'Efectivo',
  'tarjeta_debito': 'Tarjeta de débito',
  'tarjeta_credito': 'Tarjeta de crédito',
  'qr': 'QR',
  'transferencia': 'Transferencia',
};

@immutable
class SucursalCaja {
  final int idSucursal;
  final String nombre;
  final String ciudad;
  final bool esPrincipal;

  const SucursalCaja({required this.idSucursal, required this.nombre, required this.ciudad, this.esPrincipal = false});

  factory SucursalCaja.fromJson(Map<String, dynamic> j) => SucursalCaja(
        idSucursal: _entero(j['id_sucursal']),
        nombre: _texto(j['nombre']),
        ciudad: _texto(j['ciudad']),
        esPrincipal: j['es_principal'] == true,
      );
}

@immutable
class VarianteCaja {
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String? categoria;
  final String talla;
  final String color;
  final String precioLista;
  final String precioFinal;
  final int disponible;

  const VarianteCaja({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.categoria,
    required this.talla,
    required this.color,
    required this.precioLista,
    required this.precioFinal,
    required this.disponible,
  });

  factory VarianteCaja.fromJson(Map<String, dynamic> j) => VarianteCaja(
        idVariante: _entero(j['id_variante']),
        sku: _texto(j['sku']),
        nombreProducto: _texto(j['nombre_producto']),
        categoria: _textoONulo(j['categoria_nombre']),
        talla: _texto(j['talla_codigo']),
        color: _texto(j['color_nombre']),
        precioLista: _texto(j['precio_lista']),
        precioFinal: _texto(j['precio_final']),
        disponible: _entero(j['disponible_en_sucursal']),
      );
}

@immutable
class ClienteCaja {
  final int idCliente;
  final String nombres;
  final String apellidos;
  final String email;

  const ClienteCaja({required this.idCliente, required this.nombres, required this.apellidos, required this.email});

  String get nombreCompleto => '$nombres $apellidos'.trim();

  factory ClienteCaja.fromJson(Map<String, dynamic> j) => ClienteCaja(
        idCliente: _entero(j['id_cliente']),
        nombres: _texto(j['nombres']),
        apellidos: _texto(j['apellidos']),
        email: _texto(j['email']),
      );
}

@immutable
class LineaReservaCaja {
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String talla;
  final String color;
  final int cantidad;

  const LineaReservaCaja({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.talla,
    required this.color,
    required this.cantidad,
  });

  factory LineaReservaCaja.fromJson(Map<String, dynamic> j) => LineaReservaCaja(
        idVariante: _entero(j['id_variante']),
        sku: _texto(j['sku']),
        nombreProducto: _texto(j['nombre_producto']),
        talla: _texto(j['talla_codigo']),
        color: _texto(j['color_nombre']),
        cantidad: _entero(j['cantidad']),
      );
}

@immutable
class ReservaCaja {
  final int idReserva;
  final String codigo;
  final String estado;
  final DateTime? fechaHoraAtencion;
  final ClienteCaja? cliente;
  final List<LineaReservaCaja> lineas;

  const ReservaCaja({
    required this.idReserva,
    required this.codigo,
    required this.estado,
    required this.fechaHoraAtencion,
    required this.cliente,
    required this.lineas,
  });

  factory ReservaCaja.fromJson(Map<String, dynamic> j) => ReservaCaja(
        idReserva: _entero(j['id_reserva']),
        codigo: _texto(j['codigo']),
        estado: _texto(j['estado']),
        fechaHoraAtencion: _fecha(j['fecha_hora_atencion']),
        cliente: j['cliente'] == null ? null : ClienteCaja.fromJson(j['cliente'] as Map<String, dynamic>),
        lineas: [for (final l in _lista(j['lineas'])) LineaReservaCaja.fromJson(l)],
      );
}

@immutable
class CuponCaja {
  final String codigo;
  final String nombre;
  final String tipoDescuento;
  final String valorDescuento;
  final int? usosRestantes;

  const CuponCaja({
    required this.codigo,
    required this.nombre,
    required this.tipoDescuento,
    required this.valorDescuento,
    this.usosRestantes,
  });

  factory CuponCaja.fromJson(Map<String, dynamic> j) => CuponCaja(
        codigo: _texto(j['codigo']),
        nombre: _texto(j['nombre']),
        tipoDescuento: _texto(j['tipo_descuento']),
        valorDescuento: _texto(j['valor_descuento']),
        usosRestantes: j['usos_restantes'] == null ? null : _entero(j['usos_restantes']),
      );
}

@immutable
class LineaVentaCaja {
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String talla;
  final String color;
  final int cantidad;
  final String precioLista;
  final String precioUnitario;
  final String subtotalLinea;
  final String? motivoDescuento;

  /// `reserva` o `caja`.
  final String origen;

  const LineaVentaCaja({
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.talla,
    required this.color,
    required this.cantidad,
    required this.precioLista,
    required this.precioUnitario,
    required this.subtotalLinea,
    required this.motivoDescuento,
    required this.origen,
  });

  factory LineaVentaCaja.fromJson(Map<String, dynamic> j) => LineaVentaCaja(
        idVariante: _entero(j['id_variante']),
        sku: _texto(j['sku']),
        nombreProducto: _texto(j['nombre_producto']),
        talla: _texto(j['talla_codigo']),
        color: _texto(j['color_nombre']),
        cantidad: _entero(j['cantidad']),
        precioLista: _texto(j['precio_lista']),
        precioUnitario: _texto(j['precio_unitario']),
        subtotalLinea: _texto(j['subtotal_linea']),
        motivoDescuento: _textoONulo(j['motivo_descuento']),
        origen: _textoONulo(j['origen']) ?? 'caja',
      );
}

@immutable
class PagoCaja {
  final int idPago;
  final String metodoPago;
  final String monto;
  final String estado;
  final String? referencia;
  final String? montoRecibido;
  final String? cambio;

  const PagoCaja({
    required this.idPago,
    required this.metodoPago,
    required this.monto,
    required this.estado,
    this.referencia,
    this.montoRecibido,
    this.cambio,
  });

  factory PagoCaja.fromJson(Map<String, dynamic> j) => PagoCaja(
        idPago: _entero(j['id_pago']),
        metodoPago: _texto(j['metodo_pago']),
        monto: _texto(j['monto']),
        estado: _texto(j['estado']),
        referencia: _textoONulo(j['referencia']),
        montoRecibido: _textoONulo(j['monto_recibido']),
        cambio: _textoONulo(j['cambio']),
      );
}

/// Totales que calcula el servidor (`previsualizar`).
@immutable
class PrevisualizacionCaja {
  final String subtotal;
  final String descuento;
  final String total;
  final String ivaIncluido;
  final String? cuponAplicado;
  final List<LineaVentaCaja> lineas;
  final List<LineaReservaCaja> lineasReservaExcluidas;

  const PrevisualizacionCaja({
    required this.subtotal,
    required this.descuento,
    required this.total,
    required this.ivaIncluido,
    required this.cuponAplicado,
    required this.lineas,
    required this.lineasReservaExcluidas,
  });

  factory PrevisualizacionCaja.fromJson(Map<String, dynamic> j) => PrevisualizacionCaja(
        subtotal: _texto(j['subtotal']),
        descuento: _texto(j['descuento']),
        total: _texto(j['total']),
        ivaIncluido: _texto(j['iva_incluido']),
        cuponAplicado: _textoONulo(j['cupon_aplicado']),
        lineas: [for (final l in _lista(j['lineas'])) LineaVentaCaja.fromJson(l)],
        lineasReservaExcluidas: [for (final l in _lista(j['lineas_reserva_excluidas'])) LineaReservaCaja.fromJson(l)],
      );
}

/// Una venta de caja con los datos del comprobante (`VentaPosOut`).
@immutable
class VentaCaja {
  final int idVenta;
  final String numeroComprobante;
  final String estado;
  final DateTime? fechaVenta;
  final int idSucursal;
  final String nombreSucursal;
  final String? direccionSucursal;
  final String? cajeroNombre;
  final ClienteCaja? cliente;
  final String? reservaCodigo;
  final PrevisualizacionCaja totales;
  final List<PagoCaja> pagos;

  const VentaCaja({
    required this.idVenta,
    required this.numeroComprobante,
    required this.estado,
    required this.fechaVenta,
    required this.idSucursal,
    required this.nombreSucursal,
    required this.direccionSucursal,
    required this.cajeroNombre,
    required this.cliente,
    required this.reservaCodigo,
    required this.totales,
    required this.pagos,
  });

  bool get pendiente => estado == 'pendiente';

  /// El pago que cerró la venta (el último confirmado), si lo hay.
  PagoCaja? get pagoConfirmado => pagos.where((p) => p.estado == 'confirmado').lastOrNull;

  factory VentaCaja.fromJson(Map<String, dynamic> j) => VentaCaja(
        idVenta: _entero(j['id_venta']),
        numeroComprobante: _texto(j['numero_comprobante']),
        estado: _texto(j['estado']),
        fechaVenta: _fecha(j['fecha_venta']),
        idSucursal: _entero(j['id_sucursal']),
        nombreSucursal: _texto(j['nombre_sucursal']),
        direccionSucursal: _textoONulo(j['direccion_sucursal']),
        cajeroNombre: _textoONulo(j['cajero_nombre']),
        cliente: j['cliente'] == null ? null : ClienteCaja.fromJson(j['cliente'] as Map<String, dynamic>),
        reservaCodigo: _textoONulo(j['reserva_codigo']),
        totales: PrevisualizacionCaja.fromJson(j),
        pagos: [for (final p in _lista(j['pagos'])) PagoCaja.fromJson(p)],
      );
}

@immutable
class PedidoWebEfectivo {
  final int idPago;
  final int idVenta;
  final String numeroComprobante;
  final String? clienteNombre;
  final String total;
  final DateTime? creadoEn;

  const PedidoWebEfectivo({
    required this.idPago,
    required this.idVenta,
    required this.numeroComprobante,
    required this.clienteNombre,
    required this.total,
    required this.creadoEn,
  });

  factory PedidoWebEfectivo.fromJson(Map<String, dynamic> j) => PedidoWebEfectivo(
        idPago: _entero(j['id_pago']),
        idVenta: _entero(j['id_venta']),
        numeroComprobante: _texto(j['numero_comprobante']),
        clienteNombre: _textoONulo(j['cliente_nombre']),
        total: _texto(j['total']),
        creadoEn: _fecha(j['creado_en']),
      );
}

/// Cuerpo de `previsualizar` y de `registrar` (`VentaPosIn`): solo variantes y cantidades.
@immutable
class VentaCajaIn {
  final int? idSucursal;
  final int? idCliente;
  final String? reserva;
  final String? codigoCupon;
  final Map<int, int> lineas;
  final List<int> lineasReservaExcluidas;

  const VentaCajaIn({
    this.idSucursal,
    this.idCliente,
    this.reserva,
    this.codigoCupon,
    this.lineas = const {},
    this.lineasReservaExcluidas = const [],
  });

  Map<String, dynamic> toJson() => {
        'id_sucursal': idSucursal,
        'id_cliente': idCliente,
        'reserva': reserva,
        'codigo_cupon': codigoCupon,
        'lineas': [
          for (final e in lineas.entries) {'id_variante': e.key, 'cantidad': e.value},
        ],
        'lineas_reserva_excluidas': lineasReservaExcluidas,
      };
}
