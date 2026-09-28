import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/datasources/pago_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/presentacion/bloc/pago_bloc.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/presentacion/pantallas/checkout_payment_screen.dart';

import 'mocks/mock_pago_api.dart';

const String kToken = 'jwt-de-prueba';

Widget crearApp(Widget pantalla) {
  return MaterialApp(theme: ThemeData(fontFamily: 'Outfit'), home: pantalla);
}

/// Agranda el viewport de prueba para que toda la pantalla (incluidas las tres tarjetas de
/// método de pago) quede dentro del área visible del `ListView`, en vez de recortada por el
/// tamaño por defecto de 800x600 del entorno de test.
void agrandarViewport(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

void main() {
  group('CheckoutPaymentScreen', () {
    testWidgets('se abre sin BottomNavigationBar y con botón de retorno', (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      // Pantalla hoja: la barra de 4 pestañas pertenece en exclusiva al hub raíz.
      expect(find.byType(BottomNavigationBar), findsNothing);
      expect(find.byType(BackButton), findsOneWidget);
      expect(find.text('PAGO SEGURO'), findsOneWidget);
    });

    testWidgets('muestra el monto real de la orden y la barra de acción fija', (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('1940.00'), findsWidgets);
      expect(find.textContaining('CONFIRMAR Y PAGAR'), findsOneWidget);
    });

    testWidgets('alternar a Bizum/QR muestra la cuenta atrás e instrucciones numeradas',
        (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Bizum / Código QR'));
      await tester.pump();

      expect(find.textContaining('Expira en:'), findsOneWidget);
      expect(find.textContaining('Abre tu app bancaria'), findsOneWidget);
      expect(find.textContaining('#ATEL-'), findsOneWidget);
    });

    testWidgets(
      'sin STRIPE_PUBLISHABLE_KEY configurada (el estado real de este entorno de pruebas), '
      'muestra el panel de modo simulador en vez de un formulario de tarjeta',
      (tester) async {
        agrandarViewport(tester);
        final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
        await tester.pumpWidget(crearApp(
          CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
        ));
        await tester.pumpAndSettle();

        expect(find.textContaining('Modo simulador'), findsOneWidget);
        expect(find.text('✅ Pago Aprobado'), findsOneWidget);
        // El backend nunca recibe datos de tarjeta (revisado el 2026-09-28): tampoco hay ningún
        // campo que pueda recolectarlos aquí cuando no hay SDK de Stripe real inicializado.
        expect(find.widgetWithText(TextField, 'Número de tarjeta'), findsNothing);
      },
    );

    testWidgets('procesa el pago en modo simulador (escenario aprobado) y muestra la confirmación',
        (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      // "✅ Pago Aprobado" ya viene seleccionado por defecto.
      await tester.tap(find.textContaining('CONFIRMAR Y PAGAR'));
      await tester.pumpAndSettle();

      expect(find.textContaining('FS-2026-000001'), findsOneWidget);
      expect(find.text('CONTINUAR EXPLORANDO'), findsOneWidget);
      expect(find.textContaining('CONFIRMAR Y PAGAR'), findsNothing);
    });

    testWidgets('un rechazo 402 muestra el motivo y permite reintentar sin perder la orden',
        (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(
        api: MockPagoApi(
          excepcionAlConfirmar: const PagoException(
            'La entidad emisora ha rechazado el pago.',
            codigoHttp: 402,
            codigo: 'PAGO_RECHAZADO',
          ),
        ),
        token: kToken,
      );
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      await tester.tap(find.text('❌ Rechazo Genérico'));
      await tester.pump();
      await tester.tap(find.textContaining('CONFIRMAR Y PAGAR'));
      await tester.pumpAndSettle();

      expect(find.textContaining('La entidad emisora ha rechazado el pago.'), findsOneWidget);
      // La orden sigue viva: el botón de pago sigue disponible para reintentar.
      expect(find.textContaining('CONFIRMAR Y PAGAR'), findsOneWidget);
    });

    testWidgets('no muestra ningún checkbox de "Guardar tarjeta" (descartado en la especificación)',
        (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.textContaining('Guardar tarjeta'), findsNothing);
      expect(find.byType(Checkbox), findsNothing);
    });

    testWidgets('muestra el estado de error con retorno a la bolsa si la orden no pudo cargarse',
        (tester) async {
      agrandarViewport(tester);
      final bloc = PagoBloc(
        api: MockPagoApi(
          excepcionAlCargar: const PagoException('La orden ya fue liquidada.', codigo: 'VENTA_NO_PAGABLE'),
        ),
        token: kToken,
      );
      await tester.pumpWidget(crearApp(
        CheckoutPaymentScreen(idVenta: 1, token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('No pudimos abrir tu orden de pago'), findsOneWidget);
      expect(find.textContaining('La orden ya fue liquidada.'), findsOneWidget);
      expect(find.text('VOLVER A LA BOLSA'), findsOneWidget);
    });
  });
}
