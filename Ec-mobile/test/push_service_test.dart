import 'package:ec_mobile/src/core/push/servicio_push.dart';
import 'package:ec_mobile/src/core/sin_conexion/sin_conexion_api.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/pantallas/pantalla_mis_reservas.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu19_asistente_chatbot/presentacion/pantallas/pantalla_asistente_estilo.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/presentacion/pantallas/pantalla_perfil.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  TestWidgetsFlutterBinding.ensureInitialized();

  group('ServicioPush (FCM · RF37)', () {
    test('NotificacionPush.fromMap deserializa correctamente titulo, cuerpo y datos', () {
      final mapa = {
        'titulo': 'Reserva confirmada',
        'cuerpo': 'Tu cita en Atelier Central está lista',
        'datos': {
          'pantalla': 'reservas',
          'id': '105',
        },
      };

      final notif = NotificacionPush.fromMap(mapa);
      assert(notif.titulo == 'Reserva confirmada');
      assert(notif.cuerpo == 'Tu cita en Atelier Central está lista');
      assert(notif.pantalla == 'reservas');
      assert(notif.idReferencia == '105');
    });

    test('fijarTokenFCM actualiza el token registrado', () {
      final servicio = ServicioPush.instancia;
      servicio.fijarTokenFCM('fcm_token_prueba_123');
      expect(servicio.tokenFCM, 'fcm_token_prueba_123');
    });

    test('registrarTokenEnServidor llama al endpoint con los parámetros adecuados', () async {
      final servicio = ServicioPush.instancia;
      servicio.fijarTokenFCM('token_fcm_456');

      var llamado = false;
      String? cuerpoRecibido;

      final mockClient = MockClient((request) async {
        if (request.url.path.contains('/api/v1/sin-conexion/dispositivos/token-push')) {
          llamado = true;
          cuerpoRecibido = request.body;
          return http.Response('{"ok": true}', 200);
        }
        return http.Response('{"detail": "no encontrado"}', 404);
      });

      final api = SinConexionApi(cliente: mockClient, baseUrl: () => 'http://test-server');

      await servicio.registrarTokenEnServidor(
        api: api,
        identificadorDispositivo: 'uuid-dispositivo-789',
        tokenAuth: 'jwt_token_auth',
      );

      expect(llamado, isTrue);
      expect(cuerpoRecibido, contains('uuid-dispositivo-789'));
      expect(cuerpoRecibido, contains('token_fcm_456'));
    });

    testWidgets('mostrarBannerPrimerPlano despliega un SnackBar boutique in-app', (tester) async {
      final servicio = ServicioPush.instancia;
      const notif = NotificacionPush(
        titulo: 'Pago confirmado',
        cuerpo: 'Tu compra CMP-2026-0001 fue procesada.',
        datos: {'pantalla': 'compras', 'id': '1'},
      );

      var clickVer = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) {
                return ElevatedButton(
                  onPressed: () {
                    servicio.mostrarBannerPrimerPlano(
                      context,
                      notif,
                      alVer: () => clickVer = true,
                    );
                  },
                  child: const Text('DISPARAR PUSH'),
                );
              },
            ),
          ),
        ),
      );

      await tester.tap(find.text('DISPARAR PUSH'));
      await tester.pumpAndSettle();

      expect(find.text('Pago confirmado'), findsOneWidget);
      expect(find.text('Tu compra CMP-2026-0001 fue procesada.'), findsOneWidget);
      expect(find.text('VER'), findsOneWidget);

      await tester.tap(find.text('VER'));
      await tester.pumpAndSettle();

      expect(clickVer, isTrue);
    });

    testWidgets('navegarADestino enruta a PantallaMisReservas cuando pantalla es reservas', (tester) async {
      final navKey = GlobalKey<NavigatorState>();
      final servicio = ServicioPush.instancia;

      const notif = NotificacionPush(
        titulo: 'Reserva',
        cuerpo: 'Cita',
        datos: {'pantalla': 'reservas', 'id': '5'},
      );

      await tester.pumpWidget(
        MaterialApp(
          navigatorKey: navKey,
          home: const Scaffold(body: Text('INICIO')),
        ),
      );

      servicio.navegarADestino(
        navegadorKey: navKey,
        token: 'token_jwt',
        notificacion: notif,
        habilitarImagenesRed: false,
      );
      await tester.pumpAndSettle();

      expect(find.byType(PantallaMisReservas), findsOneWidget);
    });

    testWidgets('navegarADestino enruta a PantallaAsistenteEstilo cuando pantalla es asistente', (tester) async {
      final navKey = GlobalKey<NavigatorState>();
      final servicio = ServicioPush.instancia;

      const notif = NotificacionPush(
        titulo: 'Atelier',
        cuerpo: 'Respuesta lista',
        datos: {'pantalla': 'asistente', 'id': '10'},
      );

      await tester.pumpWidget(
        MaterialApp(
          navigatorKey: navKey,
          home: const Scaffold(body: Text('INICIO')),
        ),
      );

      servicio.navegarADestino(
        navegadorKey: navKey,
        token: 'token_jwt',
        notificacion: notif,
        habilitarImagenesRed: false,
      );
      await tester.pumpAndSettle();

      expect(find.byType(PantallaAsistenteEstilo), findsOneWidget);
    });

    testWidgets('navegarADestino enruta a PantallaPerfil cuando pantalla es compras', (tester) async {
      final navKey = GlobalKey<NavigatorState>();
      final servicio = ServicioPush.instancia;

      const notif = NotificacionPush(
        titulo: 'Pedido',
        cuerpo: 'Listo para recoger',
        datos: {'pantalla': 'compras', 'id': '20'},
      );

      await tester.pumpWidget(
        MaterialApp(
          navigatorKey: navKey,
          home: const Scaffold(body: Text('INICIO')),
        ),
      );

      servicio.navegarADestino(
        navegadorKey: navKey,
        token: 'token_jwt',
        notificacion: notif,
        habilitarImagenesRed: false,
      );
      await tester.pumpAndSettle();

      expect(find.byType(PantallaPerfil), findsOneWidget);
    });

    testWidgets('PantallaPerfil muestra la opción de Notificaciones Push y abre su panel', (tester) async {
      final servicio = ServicioPush.instancia;
      servicio.configurarEstadoParaPruebas(
        permisoConcedido: false,
        preferenciaActiva: false,
        firebaseDisponible: false,
        inicializado: true,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: PantallaPerfil(
            token: 'token_jwt_prueba',
            habilitarImagenesRed: false,
            mostrarBottomNav: false,
          ),
        ),
      );
      await tester.pumpAndSettle();

      final opcionPush = find.byKey(const Key('perfil_opcion_notificaciones'));
      await tester.ensureVisible(opcionPush);
      expect(opcionPush, findsOneWidget);
      expect(find.text('Notificaciones Push'), findsOneWidget);

      await tester.tap(opcionPush);
      await tester.pumpAndSettle();

      expect(find.byKey(const Key('modal_switch_notificaciones')), findsOneWidget);
      expect(find.byKey(const Key('modal_btn_probar_notificacion')), findsOneWidget);
    });

    test('notificarEvento emite notificaciones de eventos y deduplica por clave', () async {
      final servicio = ServicioPush.instancia;
      servicio.configurarEstadoParaPruebas(
        permisoConcedido: true,
        preferenciaActiva: true,
      );

      final recibidas = <NotificacionPush>[];
      final sub = servicio.enPrimerPlano.listen(recibidas.add);

      await servicio.notificarEvento(
        titulo: 'Reserva confirmada',
        cuerpo: 'Tu cita RES-001 fue confirmada.',
        datos: const {'pantalla': 'reservas', 'id': '1'},
        claveDeduplicacion: 'test_res_1',
      );
      // Repetir con la misma clave debe deduplicarse
      await servicio.notificarEvento(
        titulo: 'Reserva confirmada',
        cuerpo: 'Tu cita RES-001 fue confirmada.',
        datos: const {'pantalla': 'reservas', 'id': '1'},
        claveDeduplicacion: 'test_res_1',
      );
      // Otro evento con distinta clave sí se emite
      await servicio.notificarEvento(
        titulo: 'Pago confirmado',
        cuerpo: 'Tu pago de 450 BOB fue aprobado.',
        datos: const {'pantalla': 'compras', 'id': '9'},
        claveDeduplicacion: 'test_pago_9',
      );

      await Future<void>.delayed(const Duration(milliseconds: 20));
      await sub.cancel();

      expect(recibidas.length, 2);
      expect(recibidas[0].titulo, 'Reserva confirmada');
      expect(recibidas[0].pantalla, 'reservas');
      expect(recibidas[1].titulo, 'Pago confirmado');
      expect(recibidas[1].pantalla, 'compras');
    });
  });
}
