import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;

import '../../../../../api_config.dart';
import '../../../../core/cliente_http_api.dart';
import '../../../../core/sesion_manager.dart';
import 'modelos_caja.dart';

/// Error de la caja con el `{detail, code}` del servidor. `codigoHttp == null`: sin conexión.
class CajaException implements Exception {
  final String mensaje;
  final int? codigoHttp;
  final String? codigo;

  const CajaException(this.mensaje, {this.codigoHttp, this.codigo});

  bool get esDeRed => codigoHttp == null;

  @override
  String toString() => mensaje;
}

/// P2-CU16 / CU17 · Endpoints de la caja (`/api/v1/pos`, `/mis-sucursales`, `/admin/pagos`).
///
/// Mismo contrato que la caja web. Usa `ClienteHttpApi()`, que añade `X-Tenant` con la empresa del
/// empleado. El administrador envía la sucursal en cada petición (`id_sucursal`).
class CajaApi {
  final http.Client _cliente;
  final String Function() _baseUrl;
  static const _espera = Duration(seconds: 15);

  CajaApi({http.Client? cliente, String Function()? baseUrl})
      : _cliente = cliente ?? ClienteHttpApi(),
        _baseUrl = baseUrl ?? (() => ApiConfig.baseUrl);

  Future<List<SucursalCaja>> misSucursales({required String token}) async =>
      [for (final s in await _lista('/api/v1/mis-sucursales', const {}, token)) SucursalCaja.fromJson(s)];

  Future<List<VarianteCaja>> buscarVariantes(String texto, {int? idSucursal, required String token}) async => [
        for (final v in await _lista('/api/v1/pos/variantes', {'q': texto, ..._sucursal(idSucursal)}, token))
          VarianteCaja.fromJson(v),
      ];

  Future<List<ClienteCaja>> buscarClientes(String texto, {required String token}) async =>
      [for (final c in await _lista('/api/v1/pos/clientes', {'q': texto}, token)) ClienteCaja.fromJson(c)];

  Future<List<ReservaCaja>> reservasDeCliente(int idCliente, {int? idSucursal, required String token}) async => [
        for (final r in await _lista('/api/v1/pos/clientes/$idCliente/reservas', _sucursal(idSucursal), token))
          ReservaCaja.fromJson(r),
      ];

  Future<ReservaCaja> reserva(String referencia, {int? idSucursal, required String token}) async =>
      ReservaCaja.fromJson(await _objeto('GET', '/api/v1/pos/reservas/${Uri.encodeComponent(referencia)}',
          token: token, parametros: _sucursal(idSucursal)));

  Future<List<CuponCaja>> cupones(String texto, {required String token}) async => [
        for (final c in await _lista('/api/v1/pos/cupones', texto.trim().isEmpty ? const {} : {'q': texto.trim()}, token))
          CuponCaja.fromJson(c),
      ];

  Future<PrevisualizacionCaja> previsualizar(VentaCajaIn venta, {required String token}) async =>
      PrevisualizacionCaja.fromJson(
          await _objeto('POST', '/api/v1/pos/ventas/previsualizar', token: token, cuerpo: venta.toJson()));

  Future<VentaCaja> registrar(VentaCajaIn venta, {required String token}) async =>
      VentaCaja.fromJson(await _objeto('POST', '/api/v1/pos/ventas', token: token, cuerpo: venta.toJson()));

  Future<VentaCaja> cobrar(
    int idVenta, {
    required String metodoPago,
    String? montoRecibido,
    String? referencia,
    bool aprobado = true,
    required String token,
  }) async =>
      VentaCaja.fromJson(await _objeto('POST', '/api/v1/pos/ventas/$idVenta/cobrar', token: token, cuerpo: {
        'metodo_pago': metodoPago,
        'monto_recibido': montoRecibido,
        'referencia': referencia,
        'aprobado': aprobado,
      }));

  Future<VentaCaja> anular(int idVenta, String motivo, {required String token}) async => VentaCaja.fromJson(
      await _objeto('POST', '/api/v1/pos/ventas/$idVenta/anular', token: token, cuerpo: {'motivo': motivo}));

  Future<List<VentaCaja>> ventas({int? idSucursal, String? estado, bool soloHoy = true, required String token}) async => [
        for (final v in await _lista(
            '/api/v1/pos/ventas',
            {..._sucursal(idSucursal), 'solo_hoy': '$soloHoy', 'estado': ?estado},
            token))
          VentaCaja.fromJson(v),
      ];

  Future<VentaCaja> venta(int idVenta, {required String token}) async =>
      VentaCaja.fromJson(await _objeto('GET', '/api/v1/pos/ventas/$idVenta', token: token));

  Future<List<PedidoWebEfectivo>> pedidosWebEfectivo({int? idSucursal, required String token}) async => [
        for (final p in await _lista('/api/v1/pos/pedidos-web-efectivo', _sucursal(idSucursal), token))
          PedidoWebEfectivo.fromJson(p),
      ];

  Future<void> confirmarPedidoWeb(int idPago, {required String token}) async =>
      _objeto('POST', '/api/v1/admin/pagos/$idPago/confirmar-efectivo', token: token, cuerpo: const {});

  Future<void> cancelarPedidoWeb(int idPago, {required String token}) async =>
      _objeto('POST', '/api/v1/admin/pagos/$idPago/cancelar-efectivo', token: token, cuerpo: const {});

  // --------------------------------------------------------------------------- apoyo

  Map<String, String> _sucursal(int? idSucursal) => idSucursal == null ? const {} : {'id_sucursal': '$idSucursal'};

  Future<List<Map<String, dynamic>>> _lista(String ruta, Map<String, String> parametros, String token) async {
    final datos = await _enviar('GET', ruta, token: token, parametros: parametros);
    return [for (final e in (datos as List? ?? const [])) e as Map<String, dynamic>];
  }

  Future<Map<String, dynamic>> _objeto(
    String metodo,
    String ruta, {
    required String token,
    Map<String, String> parametros = const {},
    Object? cuerpo,
  }) async {
    final datos = await _enviar(metodo, ruta, token: token, parametros: parametros, cuerpo: cuerpo);
    return datos is Map<String, dynamic> ? datos : const {};
  }

  Future<Object?> _enviar(
    String metodo,
    String ruta, {
    required String token,
    Map<String, String> parametros = const {},
    Object? cuerpo,
  }) async {
    final uri = Uri.parse('${_baseUrl()}$ruta').replace(queryParameters: parametros.isEmpty ? null : parametros);
    final cabeceras = {
      HttpHeaders.contentTypeHeader: 'application/json',
      HttpHeaders.acceptHeader: 'application/json',
      if (token.isNotEmpty) HttpHeaders.authorizationHeader: 'Bearer $token',
    };
    final http.Response respuesta;
    try {
      respuesta = await (metodo == 'GET'
              ? _cliente.get(uri, headers: cabeceras)
              : _cliente.post(uri, headers: cabeceras, body: jsonEncode(cuerpo ?? const {})))
          .timeout(_espera);
    } on SocketException {
      throw const CajaException('Sin conexión con el servidor.');
    } on TimeoutException {
      throw const CajaException('El servidor tardó demasiado en responder.');
    } on http.ClientException {
      throw const CajaException('Sin conexión con el servidor.');
    }

    final texto = utf8.decode(respuesta.bodyBytes);
    if (respuesta.statusCode >= 200 && respuesta.statusCode < 300) {
      return texto.isEmpty ? null : jsonDecode(texto);
    }
    String mensaje = 'No se pudo completar la operación.';
    String? codigo;
    try {
      final error = jsonDecode(texto) as Map<String, dynamic>;
      final detalle = error['detail'];
      if (detalle is String) mensaje = detalle;
      codigo = error['code']?.toString();
    } catch (_) {}
    if (respuesta.statusCode == 401) SesionManager.instancia.notificarSesionExpirada(mensaje: mensaje);
    throw CajaException(mensaje, codigoHttp: respuesta.statusCode, codigo: codigo);
  }
}
