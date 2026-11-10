import 'package:flutter/foundation.dart';

import '../../cu16_cu17_caja/datos/caja_api.dart';

/// P2-CU18 · Contratos de `/api/v1/pos/cambios` (`cu18_cambio_prenda/esquemas.py`). Los importes
/// llegan como cadena (`Decimal`) y se conservan como `String`: nunca se calculan en el teléfono.

int _entero(Object? v) => v is int ? v : (v is num ? v.toInt() : int.tryParse(v?.toString() ?? '') ?? 0);
String _texto(Object? v) => v?.toString() ?? '';
String? _textoONulo(Object? v) => v?.toString();
List<Map<String, dynamic>> _lista(Object? v) => [for (final e in (v as List? ?? const [])) e as Map<String, dynamic>];

@immutable
class LineaCambiable {
  final int idVentaDetalle;
  final int idVariante;
  final String sku;
  final String nombreProducto;
  final String talla;
  final String color;
  final int vendidas;
  final int cambiables;

  /// Lo pagado por unidad, con su parte del cupón (decisión F2).
  final String valorUnitario;

  const LineaCambiable({
    required this.idVentaDetalle,
    required this.idVariante,
    required this.sku,
    required this.nombreProducto,
    required this.talla,
    required this.color,
    required this.vendidas,
    required this.cambiables,
    required this.valorUnitario,
  });

  factory LineaCambiable.fromJson(Map<String, dynamic> j) => LineaCambiable(
        idVentaDetalle: _entero(j['id_venta_detalle']),
        idVariante: _entero(j['id_variante']),
        sku: _texto(j['sku']),
        nombreProducto: _texto(j['nombre_producto']),
        talla: _texto(j['talla_codigo']),
        color: _texto(j['color_nombre']),
        vendidas: _entero(j['vendidas']),
        cambiables: _entero(j['cambiables']),
        valorUnitario: _texto(j['valor_unitario']),
      );
}

@immutable
class VentaCambiable {
  final int idVenta;
  final String numeroComprobante;
  final String? clienteNombre;
  final int diasTranscurridos;
  final int plazoDias;
  final List<LineaCambiable> lineas;

  const VentaCambiable({
    required this.idVenta,
    required this.numeroComprobante,
    required this.clienteNombre,
    required this.diasTranscurridos,
    required this.plazoDias,
    required this.lineas,
  });

  factory VentaCambiable.fromJson(Map<String, dynamic> j) => VentaCambiable(
        idVenta: _entero(j['id_venta']),
        numeroComprobante: _texto(j['numero_comprobante']),
        clienteNombre: _textoONulo(j['cliente_nombre']),
        diasTranscurridos: _entero(j['dias_transcurridos']),
        plazoDias: _entero(j['plazo_dias']),
        lineas: [for (final l in _lista(j['lineas'])) LineaCambiable.fromJson(l)],
      );
}

@immutable
class LineaCambio {
  final String tipo;
  final int idVariante;
  final String nombreProducto;
  final String talla;
  final int cantidad;
  final String subtotal;

  const LineaCambio({
    required this.tipo,
    required this.idVariante,
    required this.nombreProducto,
    required this.talla,
    required this.cantidad,
    required this.subtotal,
  });

  factory LineaCambio.fromJson(Map<String, dynamic> j) => LineaCambio(
        tipo: _texto(j['tipo']),
        idVariante: _entero(j['id_variante']),
        nombreProducto: _texto(j['nombre_producto']),
        talla: _texto(j['talla_codigo']),
        cantidad: _entero(j['cantidad']),
        subtotal: _texto(j['subtotal']),
      );
}

/// Previsualización y comprobante del cambio (`CambioPrevioOut` / `CambioOut`).
@immutable
class CambioPrenda {
  final List<LineaCambio> devueltas;
  final List<LineaCambio> nuevas;
  final String valorDevuelto;
  final String valorNuevo;

  /// nuevo − devuelto: positivo, paga el cliente; negativo, se le devuelve en efectivo (F1).
  final String diferencia;
  final String? numeroComprobante;
  final String? comprobanteVenta;
  final String? nombreSucursal;
  final String? atendidoPor;
  final DateTime? creadoEn;
  final String? metodoPago;
  final String? montoRecibido;
  final String? vuelto;
  final String? referencia;
  final String devueltoAlCliente;

  const CambioPrenda({
    required this.devueltas,
    required this.nuevas,
    required this.valorDevuelto,
    required this.valorNuevo,
    required this.diferencia,
    this.numeroComprobante,
    this.comprobanteVenta,
    this.nombreSucursal,
    this.atendidoPor,
    this.creadoEn,
    this.metodoPago,
    this.montoRecibido,
    this.vuelto,
    this.referencia,
    this.devueltoAlCliente = '0.00',
  });

  bool get pagaElCliente => (num.tryParse(diferencia) ?? 0) > 0;
  bool get seDevuelveAlCliente => (num.tryParse(diferencia) ?? 0) < 0;

  factory CambioPrenda.fromJson(Map<String, dynamic> j) => CambioPrenda(
        devueltas: [for (final l in _lista(j['devueltas'])) LineaCambio.fromJson(l)],
        nuevas: [for (final l in _lista(j['nuevas'])) LineaCambio.fromJson(l)],
        valorDevuelto: _texto(j['valor_devuelto']),
        valorNuevo: _texto(j['valor_nuevo']),
        diferencia: _texto(j['diferencia']),
        numeroComprobante: _textoONulo(j['numero_comprobante']),
        comprobanteVenta: _textoONulo(j['comprobante_venta']),
        nombreSucursal: _textoONulo(j['nombre_sucursal']),
        atendidoPor: _textoONulo(j['atendido_por']),
        creadoEn: DateTime.tryParse(_texto(j['creado_en'])),
        metodoPago: _textoONulo(j['metodo_pago']),
        montoRecibido: _textoONulo(j['monto_recibido']),
        vuelto: _textoONulo(j['vuelto']),
        referencia: _textoONulo(j['referencia']),
        devueltoAlCliente: _textoONulo(j['devuelto_al_cliente']) ?? '0.00',
      );
}

/// P2-CU18 · Endpoints de cambio de prenda, con el manejo de errores de la caja (`CajaException`).
class CambioPrendaApi {
  final CajaApi _caja;

  CambioPrendaApi({CajaApi? caja}) : _caja = caja ?? CajaApi();

  Map<String, String> _sucursal(int? id) => id == null ? const {} : {'id_sucursal': '$id'};

  Future<VentaCambiable> ventaCambiable(String comprobante, {int? idSucursal, required String token}) async =>
      VentaCambiable.fromJson(await _caja.solicitar('GET', '/api/v1/pos/cambios/venta',
          token: token, parametros: {'comprobante': comprobante.trim(), ..._sucursal(idSucursal)}) as Map<String, dynamic>);

  Future<CambioPrenda> previsualizar(Map<String, dynamic> cuerpo, {required String token}) async => CambioPrenda.fromJson(
      await _caja.solicitar('POST', '/api/v1/pos/cambios/previsualizar', token: token, cuerpo: cuerpo) as Map<String, dynamic>);

  Future<CambioPrenda> registrar(Map<String, dynamic> cuerpo, {required String token}) async => CambioPrenda.fromJson(
      await _caja.solicitar('POST', '/api/v1/pos/cambios', token: token, cuerpo: cuerpo) as Map<String, dynamic>);
}
