import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/datos/datasources/reservas_api.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/bloc/mis_reservas_bloc.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/pantallas/pantalla_mis_reservas.dart';

import 'mocks/mock_reservas_api.dart';

const String kToken = 'jwt-de-prueba';

Widget crearApp(Widget pantalla) {
  return MaterialApp(theme: ThemeData(fontFamily: 'Outfit'), home: pantalla);
}

/// Agranda el viewport de prueba para que las tarjetas de reserva (más altas que 800x600) queden
/// dentro del área visible, en vez de recortadas por el tamaño por defecto del entorno de test.
void agrandarViewport(WidgetTester tester) {
  tester.view.physicalSize = const Size(1080, 2400);
  tester.view.devicePixelRatio = 2.0;
  addTearDown(() {
    tester.view.resetPhysicalSize();
    tester.view.resetDevicePixelRatio();
  });
}

void main() {
  group('PantallaMisReservas', () {
    testWidgets('se abre sin BottomNavigationBar y con botón de retorno', (tester) async {
      agrandarViewport(tester);
      final bloc = MisReservasBloc(api: MockReservasApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      // Pantalla hoja: la barra de 4 pestañas pertenece en exclusiva al hub raíz.
      expect(find.byType(BottomNavigationBar), findsNothing);
      expect(find.byType(BackButton), findsOneWidget);
      expect(find.text('MIS RESERVAS'), findsOneWidget);
    });

    testWidgets('muestra las reservas próximas del servidor con su boutique y fecha', (tester) async {
      agrandarViewport(tester);
      final bloc = MisReservasBloc(api: MockReservasApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('RES-2026-0001'), findsOneWidget);
      expect(find.text('Atelier Serrano - Madrid'), findsWidgets);
      expect(find.textContaining('Blusa de satén fluido'), findsOneWidget);
      expect(find.text('CANCELAR RESERVA'), findsOneWidget);
    });

    testWidgets('la reserva del historial no muestra el botón de cancelar (puede_cancelar=false)',
        (tester) async {
      agrandarViewport(tester);
      final bloc = MisReservasBloc(api: MockReservasApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      await tester.tap(find.textContaining('Historial'));
      await tester.pumpAndSettle();

      expect(find.text('RES-2026-0002'), findsOneWidget);
      expect(find.text('CANCELAR RESERVA'), findsNothing);
    });

    testWidgets('sin reservas activas ni en historial, muestra el estado vacío por pestaña',
        (tester) async {
      agrandarViewport(tester);
      final bloc = MisReservasBloc(
        api: MockReservasApi(respuestaMisReservas: const {
          'resumen': {'activas': 0, 'proxima': null},
          'proximas': [],
          'historial': [],
        }),
        token: kToken,
      );
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Aún no tienes citas de probador agendadas.'), findsOneWidget);

      await tester.tap(find.textContaining('Historial'));
      await tester.pumpAndSettle();

      expect(find.text('No hay reservas en tu historial todavía.'), findsOneWidget);
    });

    testWidgets('un fallo de red muestra el mensaje del servidor con opción de reintentar',
        (tester) async {
      agrandarViewport(tester);
      final bloc = MisReservasBloc(
        api: MockReservasApi(
          excepcionAlCargar: const ReservaException('No se pudo conectar con el atelier.'),
        ),
        token: kToken,
      );
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('No se pudo conectar con el atelier.'), findsOneWidget);
      expect(find.text('REINTENTAR'), findsOneWidget);
    });

    testWidgets(
      'cancelar una reserva abre la hoja, envía el motivo y recarga la lista al confirmar',
      (tester) async {
        agrandarViewport(tester);
        final api = MockReservasApi();
        final bloc = MisReservasBloc(api: api, token: kToken);
        await tester.pumpWidget(crearApp(
          PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
        ));
        await tester.pumpAndSettle();

        await tester.tap(find.text('CANCELAR RESERVA'));
        await tester.pumpAndSettle();

        expect(find.text('Cancelar esta reserva'), findsOneWidget);

        // El botón de confirmar permanece deshabilitado sin un motivo válido (mínimo 3 caracteres).
        final botonConfirmar = find.widgetWithText(ElevatedButton, 'Confirmar cancelación');
        expect(tester.widget<ElevatedButton>(botonConfirmar).onPressed, isNull);

        await tester.enterText(find.byType(TextField), 'Cambio de planes de última hora');
        await tester.pump();

        expect(tester.widget<ElevatedButton>(botonConfirmar).onPressed, isNotNull);

        await tester.tap(botonConfirmar);
        await tester.pumpAndSettle();

        expect(api.llamadasCancelarReserva, 1);
        expect(api.ultimoIdReservaCancelado, 1);
        expect(api.ultimoMotivoEnviado, 'Cambio de planes de última hora');
        // La hoja se cierra sola tras una cancelación exitosa.
        expect(find.text('Cancelar esta reserva'), findsNothing);
      },
    );

    testWidgets(
      'si el backend rechaza la cancelación, la hoja permanece abierta mostrando el motivo',
      (tester) async {
        agrandarViewport(tester);
        final api = MockReservasApi(
          excepcionAlCancelar: const ReservaException(
            'Esta reserva ya no admite cancelación.',
            codigo: 'RESERVA_NO_CANCELABLE',
          ),
        );
        final bloc = MisReservasBloc(api: api, token: kToken);
        await tester.pumpWidget(crearApp(
          PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
        ));
        await tester.pumpAndSettle();

        await tester.tap(find.text('CANCELAR RESERVA'));
        await tester.pumpAndSettle();

        await tester.enterText(find.byType(TextField), 'Motivo cualquiera');
        await tester.pump();
        await tester.tap(find.widgetWithText(ElevatedButton, 'Confirmar cancelación'));
        await tester.pumpAndSettle();

        expect(find.text('Cancelar esta reserva'), findsOneWidget);
        expect(find.text('Esta reserva ya no admite cancelación.'), findsOneWidget);
      },
    );

    testWidgets('el pull-to-refresh recarga la lista contra el servidor', (tester) async {
      agrandarViewport(tester);
      final api = MockReservasApi();
      final bloc = MisReservasBloc(api: api, token: kToken);
      await tester.pumpWidget(crearApp(
        PantallaMisReservas(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();
      expect(api.llamadasObtenerMisReservas, 1);

      await tester.fling(find.byType(ListView), const Offset(0, 300), 800);
      await tester.pumpAndSettle();

      expect(api.llamadasObtenerMisReservas, 2);
    });
  });
}
