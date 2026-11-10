import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

import 'payloads_caja.dart' as p;

/// Servidor falso de la caja: responde con payloads literales y guarda lo recibido.
class ServidorCaja {
  final peticiones = <http.Request>[];
  String sucursales = '[${p.sucursal}]';
  http.Response Function(http.Request)? previsualizar;
  http.Response Function(http.Request)? cobrar;

  static http.Response ok(String cuerpo, [int estado = 200]) =>
      http.Response.bytes(utf8.encode(cuerpo), estado, headers: {'content-type': 'application/json'});

  static http.Response error(int estado, String codigo, String detalle) =>
      ok(jsonEncode({'detail': detalle, 'code': codigo}), estado);

  late final MockClient cliente = MockClient((r) async {
    peticiones.add(r);
    final ruta = r.url.path;
    if (ruta == '/api/v1/mis-sucursales') return ok(sucursales);
    if (ruta == '/api/v1/pos/variantes') return ok('[${p.variante},${p.varianteAgotada}]');
    if (ruta == '/api/v1/pos/clientes') return ok('[${p.cliente}]');
    if (ruta == '/api/v1/pos/clientes/10/reservas') return ok('[${p.reserva}]');
    if (ruta == '/api/v1/pos/ventas/previsualizar') return previsualizar?.call(r) ?? ok(p.previsualizacion);
    if (ruta == '/api/v1/pos/ventas' && r.method == 'POST') return ok(p.ventaPendiente, 201);
    if (ruta == '/api/v1/pos/ventas') return ok('[${p.ventaPendiente}]');
    if (ruta == '/api/v1/pos/ventas/501/cobrar') return cobrar?.call(r) ?? ok(p.ventaPagada);
    if (ruta == '/api/v1/pos/ventas/501/anular') return ok(p.ventaPendiente.replaceFirst('"pendiente"', '"anulada"'));
    if (ruta == '/api/v1/pos/pedidos-web-efectivo') return ok('[${p.pedidoWeb}]');
    if (ruta.startsWith('/api/v1/admin/pagos/77/')) return ok('{}');
    return ok('{}', 404);
  });

  Iterable<Map<String, dynamic>> cuerpos(String ruta) =>
      peticiones.where((r) => r.url.path == ruta && r.method == 'POST').map((r) => jsonDecode(r.body) as Map<String, dynamic>);
}
