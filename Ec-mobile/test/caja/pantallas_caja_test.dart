import 'dart:async';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/datos/caja_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/bloc/caja_bloc.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/pantallas/pantalla_caja.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/pantallas/pantalla_ventas_caja.dart';
import 'package:flutter/material.dart';
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

  Future<void> abrirCaja(WidgetTester tester, {String rol = 'cajero'}) async {
    await tester.binding.setSurfaceSize(const Size(400, 900));
    await tester.pumpWidget(MaterialApp(
      home: PantallaCaja(token: 'token', nombreEmpleado: 'Carlos Perez', rol: rol, bloc: bloc),
    ));
    await tester.pumpAndSettle();
  }

  Future<void> anadirCamisa(WidgetTester tester) async {
    await tester.enterText(find.byKey(const Key('campo-prenda')), 'camisa');
    await tester.pump(const Duration(milliseconds: 350)); // espera de la búsqueda incremental
    await tester.pumpAndSettle();
    await tester.tap(find.text('Camisa formal blanca · M · Blanco'));
    await tester.pumpAndSettle();
  }

  testWidgets('AC-2/AC-4/AC-5: caja con sucursal, búsqueda y total del servidor', (tester) async {
    await abrirCaja(tester);
    expect(find.textContaining('Carlos Perez · Menshopping Santa Cruz'), findsOneWidget);
    expect(find.text('Sin existencias'), findsNothing);

    await anadirCamisa(tester);
    final total = tester.widget<Text>(find.byKey(const Key('total-caja')));
    expect(total.data, contains('350,00'));
    expect(tester.widget<FilledButton>(find.byKey(const Key('btn-registrar-venta'))).onPressed, isNotNull);
  });

  testWidgets('AC-9 → AC-10 → AC-12: registrar, cobrar en efectivo y ver el comprobante', (tester) async {
    await abrirCaja(tester);
    await anadirCamisa(tester);
    await tester.tap(find.byKey(const Key('btn-registrar-venta')));
    await tester.pumpAndSettle();

    expect(find.text('Cobrar'), findsOneWidget);
    expect(tester.widget<Text>(find.byKey(const Key('total-cobro'))).data, contains('350,00'));
    await tester.enterText(find.byKey(const Key('campo-monto')), '400');
    await tester.tap(find.byKey(const Key('btn-confirmar-cobro')));
    await tester.pumpAndSettle();

    expect(find.byKey(const Key('numero-comprobante')), findsOneWidget);
    expect(find.text('MOV-2026-00501'), findsOneWidget);
    expect(find.text('Atendió: Carlos Perez'), findsOneWidget);
    expect(find.textContaining('50,00'), findsWidgets); // cambio devuelto por el servidor
  });

  testWidgets('AC-15: sin conexión avisa y deshabilita registrar', (tester) async {
    await abrirCaja(tester);
    await anadirCamisa(tester);
    red.add(false);
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('aviso-caja-sin-conexion')), findsOneWidget);
    expect(tester.widget<FilledButton>(find.byKey(const Key('btn-registrar-venta'))).onPressed, isNull);
  });

  testWidgets('AC-2: el cajero no ve «Reportes por voz»; el administrador sí', (tester) async {
    await abrirCaja(tester);
    await tester.tap(find.byKey(const Key('menu-caja')));
    await tester.pumpAndSettle();
    expect(find.text('Reportes por voz'), findsNothing);
    expect(find.text('Cerrar sesión'), findsOneWidget);
  });

  testWidgets('AC-2: el administrador ve «Reportes por voz» en el menú', (tester) async {
    await abrirCaja(tester, rol: 'administrador');
    await tester.tap(find.byKey(const Key('menu-caja')));
    await tester.pumpAndSettle();
    expect(find.text('Reportes por voz'), findsOneWidget);
  });

  testWidgets('AC-3: con varias sucursales pide elegir antes de vender', (tester) async {
    servidor.sucursales = '[${p.sucursal},${p.sucursal2}]';
    await abrirCaja(tester, rol: 'administrador');
    expect(find.text('¿En qué sucursal vendes hoy?'), findsOneWidget);
    await tester.tap(find.text('Menshopping Beni'));
    await tester.pumpAndSettle();
    expect(find.byKey(const Key('campo-prenda')), findsOneWidget);
  });

  testWidgets('AC-13/AC-14: pendientes, pedidos web y anular con motivo', (tester) async {
    await abrirCaja(tester);
    await tester.tap(find.byKey(const Key('btn-ventas-caja')));
    await tester.pumpAndSettle();
    expect(find.byType(PantallaVentasCaja), findsOneWidget);
    expect(find.byType(BackButton), findsOneWidget);
    expect(find.text('WEB-2026-00480'), findsOneWidget);

    await tester.tap(find.byTooltip('Anular'));
    await tester.pumpAndSettle();
    await tester.enterText(find.byKey(const Key('campo-motivo')), 'Cliente desistió');
    await tester.pump(); // el botón se habilita al tener 3 caracteres
    await tester.tap(find.widgetWithText(FilledButton, 'Anular'));
    await tester.pumpAndSettle();
    expect(servidor.cuerpos('/api/v1/pos/ventas/501/anular').single, {'motivo': 'Cliente desistió'});
  });
}
