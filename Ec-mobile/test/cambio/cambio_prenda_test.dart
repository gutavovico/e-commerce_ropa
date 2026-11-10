import 'dart:async';
import 'dart:convert';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/datos/caja_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/bloc/caja_bloc.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/pantallas/pantalla_caja.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;

import '../caja/servidor_caja.dart';
import 'payloads_cambio.dart' as p;

/// P2-CU18 en el móvil: se abre desde el menú de la caja y usa los payloads literales del backend.
void main() {
  late ServidorCaja servidor;
  late StreamController<bool> red;
  late CajaBloc caja;
  http.Response Function(http.Request)? venta;

  setUp(() {
    servidor = ServidorCaja();
    venta = null;
    servidor.otrasRutas = (r) => switch (r.url.path) {
          '/api/v1/pos/cambios/venta' => venta?.call(r) ?? ServidorCaja.ok(p.venta),
          '/api/v1/pos/cambios/previsualizar' => ServidorCaja.ok(p.previo),
          '/api/v1/pos/cambios' => ServidorCaja.ok(p.cambio, 201),
          _ => null,
        };
    red = StreamController<bool>();
    caja = CajaBloc(
      token: 'token',
      api: CajaApi(cliente: servidor.cliente, baseUrl: () => 'http://servidor'),
      cambiosDeRed: red.stream,
    );
  });

  tearDown(() async {
    caja.dispose();
    await red.close();
  });

  // La pantalla usa el cliente de la caja: abrirla desde el menú la conecta al servidor falso.
  Future<void> abrirCambio(WidgetTester tester) async {
    await tester.binding.setSurfaceSize(const Size(400, 900));
    await tester.pumpWidget(MaterialApp(
      home: PantallaCaja(token: 'token', nombreEmpleado: 'Carlos Perez', rol: 'cajero', bloc: caja),
    ));
    await tester.pumpAndSettle();
    await tester.tap(find.byKey(const Key('menu-caja')));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Cambio de prenda'));
    await tester.pumpAndSettle();
  }

  Future<void> buscarVenta(WidgetTester tester) async {
    await tester.enterText(find.byKey(const Key('campo-comprobante-cambio')), 'FS-2026-000501');
    await tester.pump();
    await tester.tap(find.byKey(const Key('btn-buscar-venta-cambio')));
    await tester.pumpAndSettle();
  }

  Future<void> elegirCambio(WidgetTester tester) async {
    await buscarVenta(tester);
    expect(find.textContaining('2 de 2 por cambiar'), findsOneWidget);
    await tester.tap(find.byKey(const Key('btn-devolver-MSH-CAM-M')));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('campo-prenda-cambio')), 'camisa');
    await tester.pump(const Duration(milliseconds: 350));
    await tester.pumpAndSettle();
    await tester.tap(find.text('Camisa formal blanca · M · Blanco').last);
    await tester.pumpAndSettle();
  }

  testWidgets('AC-1 → AC-9: busca, elige, ve la diferencia del servidor, cobra y muestra el comprobante',
      (tester) async {
    await abrirCambio(tester);
    expect(find.text('Cambio de prenda'), findsOneWidget);
    expect(find.byType(BackButton), findsOneWidget);

    await elegirCambio(tester);
    final previa = servidor.cuerpos('/api/v1/pos/cambios/previsualizar').last;
    expect(previa['devueltas'], [
      {'id_venta_detalle': 1, 'cantidad': 1}
    ]);
    expect(previa['id_venta'], 501);
    final diferencia = find.byKey(const Key('diferencia-cambio'));
    expect(find.descendant(of: diferencia, matching: find.text('Paga el cliente')), findsOneWidget);
    expect(find.descendant(of: diferencia, matching: find.textContaining('10,00')), findsOneWidget);

    await tester.enterText(find.byKey(const Key('campo-monto-cambio')), '20');
    await tester.tap(find.byKey(const Key('btn-registrar-cambio')));
    await tester.pumpAndSettle();
    final registro = servidor.cuerpos('/api/v1/pos/cambios').single;
    expect(registro['cobro'], {'metodo_pago': 'efectivo', 'monto_recibido': '20', 'referencia': null});

    expect(find.byKey(const Key('comprobante-cambio')), findsOneWidget);
    expect(find.text('Cambio de prenda CAM-2026-00001'), findsOneWidget);
    expect(find.text('Venta original: FS-2026-000501'), findsOneWidget);
    expect(find.text('Vuelto'), findsOneWidget);

    await tester.tap(find.byKey(const Key('btn-nuevo-cambio')));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('campo-comprobante-cambio')), findsOneWidget);
  });

  testWidgets('AC-3: el plazo vencido se muestra con el mensaje del servidor', (tester) async {
    venta = (_) => ServidorCaja.ok(
        jsonEncode({
          'detail': 'Pasaron 20 días desde la venta y el plazo de cambio es de 15 días.',
          'code': 'PLAZO_DE_CAMBIO_VENCIDO',
          'dias_transcurridos': 20,
          'plazo_dias': 15,
        }),
        409);
    await abrirCambio(tester);
    await buscarVenta(tester);
    expect(find.textContaining('Pasaron 20 días'), findsOneWidget);
    expect(find.byKey(const Key('btn-registrar-cambio')), findsNothing);
  });

  testWidgets('AC-13: sin conexión avisa y no deja registrar', (tester) async {
    await abrirCambio(tester);
    await elegirCambio(tester);
    red.add(false);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('aviso-cambio-sin-conexion')), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const Key('btn-registrar-cambio'))).onPressed, isNull);
  });
}
