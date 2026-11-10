import 'dart:async';
import 'dart:convert';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/datos/caja_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/datos/modelos_caja.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/bloc/caja_bloc.dart';
import 'package:flutter_test/flutter_test.dart';

import 'payloads_caja.dart' as p;
import 'servidor_caja.dart';

void main() {
  late ServidorCaja servidor;
  late StreamController<bool> red;
  late CajaBloc bloc;

  setUp(() {
    servidor = ServidorCaja();
    red = StreamController<bool>();
    bloc = CajaBloc(
      token: 'token',
      api: CajaApi(cliente: servidor.cliente, baseUrl: () => 'http://servidor'),
      cambiosDeRed: red.stream,
    );
  });

  tearDown(() async {
    bloc.dispose();
    await red.close();
  });

  final variante = VarianteCaja.fromJson(jsonDecode(p.variante) as Map<String, dynamic>);
  final agotada = VarianteCaja.fromJson(jsonDecode(p.varianteAgotada) as Map<String, dynamic>);

  test('AC-3: con una sola sucursal entra directo y carga las ventas del día y los pedidos web', () async {
    await bloc.iniciar();
    expect(bloc.estado, isA<CajaOperando>());
    expect(bloc.sucursal!.nombre, 'Menshopping Santa Cruz');
    expect(bloc.pendientes.single.numeroComprobante, 'MOV-2026-00501');
    expect(bloc.pedidosWeb.single.idPago, 77);
    final ventas = servidor.peticiones.firstWhere((r) => r.url.path == '/api/v1/pos/ventas');
    expect(ventas.url.queryParameters['id_sucursal'], '3');
    expect(ventas.headers['Authorization'], 'Bearer token');
  });

  test('AC-3: con varias sucursales pide elegir antes de vender', () async {
    servidor.sucursales = '[${p.sucursal},${p.sucursal2}]';
    await bloc.iniciar();
    expect(bloc.estado, isA<CajaEligiendoSucursal>());
    await bloc.elegirSucursal(bloc.sucursales.last);
    expect(bloc.sucursal!.idSucursal, 4);
  });

  test('AC-4/AC-5: añadir una prenda pide los totales al servidor y los muestra tal cual', () async {
    await bloc.iniciar();
    await bloc.agregar(variante);
    expect(bloc.previsualizacion!.total, '350.00');
    expect(bloc.previsualizacion!.ivaIncluido, '40.27');
    final cuerpo = servidor.cuerpos('/api/v1/pos/ventas/previsualizar').last;
    expect(cuerpo['lineas'], [
      {'id_variante': 41, 'cantidad': 1},
    ]);
    expect(cuerpo['id_sucursal'], 3);
    expect(cuerpo.containsKey('total'), isFalse); // ningún importe sale del teléfono
  });

  test('AC-6: una prenda sin existencias no se añade', () async {
    await bloc.iniciar();
    await bloc.agregar(agotada);
    expect(bloc.lineas, isEmpty);
    expect(bloc.mensaje, contains('No hay existencias'));
    expect(servidor.cuerpos('/api/v1/pos/ventas/previsualizar'), isEmpty);
  });

  test('AC-7: al elegir cliente ofrece sus reservas y se pueden cargar excluyendo líneas', () async {
    await bloc.iniciar();
    final cliente = (await bloc.buscarClientes('ana')).single;
    await bloc.elegirCliente(cliente);
    expect(bloc.reservasDelCliente.single.codigo, 'RES-2026-0123');
    await bloc.cargarReserva(bloc.reservasDelCliente.single);
    await bloc.alternarExclusion(41);
    final cuerpo = servidor.cuerpos('/api/v1/pos/ventas/previsualizar').last;
    expect(cuerpo['reserva'], 'RES-2026-0123');
    expect(cuerpo['id_cliente'], 10);
    expect(cuerpo['lineas_reserva_excluidas'], [41]);
  });

  test('AC-8: un cupón inválido se quita con el motivo y se sigue sin descuento', () async {
    servidor.previsualizar = (r) => (jsonDecode(r.body) as Map)['codigo_cupon'] == null
        ? ServidorCaja.ok(p.previsualizacion)
        : ServidorCaja.error(400, 'CUPON_INVALIDO', "El código 'MALO' ha caducado.");
    await bloc.iniciar();
    await bloc.agregar(variante);
    await bloc.aplicarCupon('MALO');
    expect(bloc.cupon, isNull);
    expect(bloc.mensaje, "El código 'MALO' ha caducado.");
    expect(bloc.previsualizacion!.total, '350.00');
  });

  test('un error que no es de cupón no se oculta (p. ej. stock)', () async {
    servidor.previsualizar = (_) => ServidorCaja.error(409, 'STOCK_INSUFICIENTE', 'Sin stock.');
    await bloc.iniciar();
    await bloc.agregar(variante);
    expect(bloc.previsualizacion, isNull);
    expect(bloc.mensaje, 'Sin stock.');
    expect(bloc.puedeRegistrar, isFalse);
  });

  test('AC-9 y AC-10: registrar y cobrar en efectivo con el cambio del servidor', () async {
    await bloc.iniciar();
    await bloc.agregar(variante);
    final venta = await bloc.registrar();
    expect(venta!.pendiente, isTrue);
    expect(bloc.ventaEnCobro!.idVenta, 501);
    expect(bloc.lineas, isEmpty); // la venta en curso pasó al cobro

    final pagada = await bloc.cobrar(metodoPago: 'efectivo', montoRecibido: '400.00');
    expect(pagada!.pendiente, isFalse);
    expect(pagada.pagoConfirmado!.cambio, '50.00');
    expect(bloc.ventaEnCobro, isNull);
    expect(servidor.cuerpos('/api/v1/pos/ventas/501/cobrar').single,
        {'metodo_pago': 'efectivo', 'monto_recibido': '400.00', 'referencia': null, 'aprobado': true});
  });

  test('AC-10: monto insuficiente muestra el error del servidor y no cierra el cobro', () async {
    servidor.cobrar = (_) => ServidorCaja.error(400, 'MONTO_INSUFICIENTE', 'El monto recibido es menor que el total.');
    await bloc.iniciar();
    await bloc.agregar(variante);
    await bloc.registrar();
    expect(await bloc.cobrar(metodoPago: 'efectivo', montoRecibido: '100.00'), isNull);
    expect(bloc.mensaje, 'El monto recibido es menor que el total.');
    expect(bloc.ventaEnCobro!.idVenta, 501);
  });

  test('AC-11: el rechazo del datáfono deja la venta pendiente para otro medio', () async {
    servidor.cobrar = (_) => ServidorCaja.ok(p.ventaPendiente);
    await bloc.iniciar();
    await bloc.agregar(variante);
    await bloc.registrar();
    final resultado = await bloc.cobrar(metodoPago: 'tarjeta_credito', referencia: 'AUT-123', aprobado: false);
    expect(resultado!.pendiente, isTrue);
    expect(bloc.ventaEnCobro!.idVenta, 501);
    expect(bloc.mensaje, contains('rechazado por el datáfono'));
    expect(servidor.cuerpos('/api/v1/pos/ventas/501/cobrar').single['aprobado'], isFalse);
  });

  test('AC-13 y AC-14: anular con motivo y resolver un pedido web en efectivo', () async {
    await bloc.iniciar();
    expect(await bloc.anular(501, 'El cliente se arrepintió'), isTrue);
    expect(servidor.cuerpos('/api/v1/pos/ventas/501/anular').single, {'motivo': 'El cliente se arrepintió'});
    expect(await bloc.resolverPedidoWeb(bloc.pedidosWeb.single, confirmar: true), isTrue);
    expect(servidor.peticiones.any((r) => r.url.path == '/api/v1/admin/pagos/77/confirmar-efectivo'), isTrue);
  });

  test('AC-15: sin conexión no deja registrar ni cobrar', () async {
    await bloc.iniciar();
    await bloc.agregar(variante);
    expect(bloc.puedeRegistrar, isTrue);
    red.add(false);
    await Future<void>.delayed(Duration.zero);
    expect(bloc.enLinea, isFalse);
    expect(bloc.puedeRegistrar, isFalse);
    expect(await bloc.registrar(), isNull);
    expect(servidor.cuerpos('/api/v1/pos/ventas'), isEmpty);
  });
}
