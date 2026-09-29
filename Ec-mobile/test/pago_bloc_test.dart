import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/datasources/pago_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/datasources/stripe_gateway.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/modelos/pago_dto.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/presentacion/bloc/pago_bloc.dart';

import 'mocks/mock_pago_api.dart';

const String kToken = 'jwt-de-prueba';

/// Doble de [StripeGateway] para las pruebas que simulan un SDK de Stripe real inicializado.
/// Sin inyectarlo, `PagoBloc` usa `StripeGatewayReal()`, cuya `disponible` depende de
/// `ApiConfig.stripePublishableKey` — vacía en este entorno de pruebas (sin `--dart-define`), así
/// que la mayoría de los casos abajo ejercitan el «modo simulador» de forma natural.
class _StripeGatewayFalso implements StripeGateway {
  final bool _disponible;
  final bool aprobar;
  int llamadas = 0;

  _StripeGatewayFalso({bool disponible = true, this.aprobar = true}) : _disponible = disponible;

  @override
  bool get disponible => _disponible;

  @override
  Future<StripeConfirmacionResultado> confirmarPago(String clientSecret) async {
    llamadas++;
    if (aprobar) return const StripeConfirmacionResultado(aprobado: true);
    return const StripeConfirmacionResultado(
      aprobado: false,
      mensajeError: 'La entidad emisora ha rechazado la tarjeta.',
    );
  }
}

void main() {
  group('PagoBloc', () {
    test('carga el resumen y expone PagoListo con tarjeta_credito por defecto', () async {
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);

      await bloc.cargarResumen(1);

      final estado = bloc.estado;
      expect(estado, isA<PagoListo>());
      expect((estado as PagoListo).metodoSeleccionado, 'tarjeta_credito');
      expect(estado.escenarioPrueba, EscenarioPrueba.aprobado);
      expect(estado.resumen.numeroComprobante, 'FS-2026-000001');
    });

    test('un fallo de red al cargar el resumen transiciona a PagoError', () async {
      final bloc = PagoBloc(
        api: MockPagoApi(
          excepcionAlCargar: const PagoException('La orden ya fue liquidada.', codigo: 'VENTA_NO_PAGABLE'),
        ),
        token: kToken,
      );

      await bloc.cargarResumen(1);

      expect(bloc.estado, isA<PagoError>());
      expect((bloc.estado as PagoError).mensaje, 'La orden ya fue liquidada.');
    });

    test('seleccionarMetodo cambia el método activo sin perder el resumen', () async {
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      await bloc.cargarResumen(1);

      bloc.seleccionarMetodo('qr');

      final estado = bloc.estado as PagoListo;
      expect(estado.metodoSeleccionado, 'qr');
      expect(estado.resumen.idVenta, 1);
    });

    test('sin STRIPE_PUBLISHABLE_KEY configurada, stripeDisponible es false', () {
      final bloc = PagoBloc(api: MockPagoApi(), token: kToken);
      expect(bloc.stripeDisponible, false);
    });

    test(
      'confirmarYPagar con tarjeta en modo simulador abre el intento sin ningún dato de '
      'tarjeta y lo cierra con confirmarPago',
      () async {
        final api = MockPagoApi();
        final bloc = PagoBloc(api: api, token: kToken);
        await bloc.cargarResumen(1);

        final exito = await bloc.confirmarYPagar();

        expect(exito, true);
        expect(bloc.estado, isA<PagoExitoso>());
        expect(api.llamadasIniciarPago, 1);
        expect(api.llamadasConfirmarPago, 1);
        expect(api.ultimoPayloadIniciar?['metodo_pago'], 'tarjeta_credito');
        expect(api.ultimoPayloadIniciar?['escenario_prueba'], 'aprobado');
        // La misma clave se genera una sola vez por intento.
        expect(api.ultimoPayloadIniciar?['clave_idempotencia'], isNotNull);
        // El backend nunca recibe ningún dato de tarjeta (revisado el 2026-09-28).
        expect(api.ultimoPayloadIniciar!.containsKey('tarjeta'), false);
      },
    );

    test('seleccionarEscenarioPrueba cambia el desenlace que se envía al iniciar el pago', () async {
      final api = MockPagoApi();
      final bloc = PagoBloc(api: api, token: kToken);
      await bloc.cargarResumen(1);

      bloc.seleccionarEscenarioPrueba(EscenarioPrueba.fondosInsuficientes);
      await bloc.confirmarYPagar();

      expect(api.ultimoPayloadIniciar?['escenario_prueba'], 'fondos_insuficientes');
    });

    test(
      'Bizum/QR se abre siempre con escenario "aprobado", sin depender del selector del simulador',
      () async {
        final api = MockPagoApi();
        final bloc = PagoBloc(api: api, token: kToken);
        await bloc.cargarResumen(1);
        bloc.seleccionarMetodo('qr');
        bloc.seleccionarEscenarioPrueba(EscenarioPrueba.rechazado);

        final exito = await bloc.confirmarYPagar();

        expect(exito, true);
        expect(api.ultimoPayloadIniciar?['metodo_pago'], 'qr');
        expect(api.ultimoPayloadIniciar?['escenario_prueba'], 'aprobado');
      },
    );

    test('un rechazo 402 al confirmar transiciona a PagoRechazado y conserva la orden para reintentar', () async {
      final api = MockPagoApi(
        excepcionAlConfirmar: const PagoException(
          'La entidad emisora ha rechazado el pago.',
          codigoHttp: 402,
          codigo: 'PAGO_RECHAZADO',
        ),
      );
      final bloc = PagoBloc(api: api, token: kToken);
      await bloc.cargarResumen(1);

      final exito = await bloc.confirmarYPagar();

      expect(exito, false);
      final estado = bloc.estado;
      expect(estado, isA<PagoRechazado>());
      expect((estado as PagoRechazado).motivo, 'La entidad emisora ha rechazado el pago.');
      // La orden sigue viva: se puede reintentar sin recargar el resumen.
      expect(estado.resumen.idVenta, 1);
    });

    test('una orden expirada (409 al iniciar) transiciona a PagoError, no a PagoRechazado', () async {
      final api = MockPagoApi(
        excepcionAlIniciar: const PagoException(
          'La ventana de la orden ha vencido.',
          codigoHttp: 409,
          codigo: 'ORDEN_EXPIRADA',
        ),
      );
      final bloc = PagoBloc(api: api, token: kToken);
      await bloc.cargarResumen(1);

      await bloc.confirmarYPagar();

      expect(bloc.estado, isA<PagoError>());
    });

    test('reintentar tras un rechazo reutiliza el resumen ya cargado', () async {
      final apiRechaza = MockPagoApi(
        excepcionAlConfirmar: const PagoException('Rechazado.', codigoHttp: 402, codigo: 'PAGO_RECHAZADO'),
      );
      final bloc = PagoBloc(api: apiRechaza, token: kToken);
      await bloc.cargarResumen(1);
      await bloc.confirmarYPagar();

      bloc.seleccionarMetodo('pasarela_digital');

      expect(bloc.estado, isA<PagoListo>());
      expect((bloc.estado as PagoListo).metodoSeleccionado, 'pasarela_digital');
    });

    test('si iniciar devuelve ya_confirmado, transiciona directo a PagoExitoso sin llamar a confirmarPago', () async {
      final api = MockPagoApi(
        respuestaIniciar: {
          'id_pago': 505,
          'client_secret': null,
          'ya_confirmado': true,
          'confirmacion': respuestaPagoConfirmadoBackend,
        },
      );
      final bloc = PagoBloc(api: api, token: kToken);
      await bloc.cargarResumen(1);

      final exito = await bloc.confirmarYPagar();

      expect(exito, true);
      expect(bloc.estado, isA<PagoExitoso>());
      expect(api.llamadasConfirmarPago, 0);
    });

    test(
      'con un StripeGateway real disponible, confirma contra Stripe antes de cerrar con el backend',
      () async {
        final api = MockPagoApi();
        final gateway = _StripeGatewayFalso();
        final bloc = PagoBloc(api: api, stripeGateway: gateway, token: kToken);
        await bloc.cargarResumen(1);

        expect(bloc.stripeDisponible, true);

        final exito = await bloc.confirmarYPagar();

        expect(exito, true);
        expect(gateway.llamadas, 1);
        // Con Stripe real, el backend no recibe `escenario_prueba`: el desenlace lo decide Stripe.
        expect(api.ultimoPayloadIniciar?['escenario_prueba'], isNull);
        expect(api.llamadasConfirmarPago, 1);
      },
    );

    test(
      'si Stripe rechaza la confirmación, transiciona a PagoRechazado sin llamar a confirmarPago del backend',
      () async {
        final api = MockPagoApi();
        final gateway = _StripeGatewayFalso(aprobar: false);
        final bloc = PagoBloc(api: api, stripeGateway: gateway, token: kToken);
        await bloc.cargarResumen(1);

        final exito = await bloc.confirmarYPagar();

        expect(exito, false);
        expect(bloc.estado, isA<PagoRechazado>());
        expect(api.llamadasConfirmarPago, 0);
      },
    );

    test(
      'un error inesperado que no es PagoException al cargar el resumen transiciona a PagoError sin congelar',
      () async {
        final bloc = PagoBloc(
          api: _ApiQueLanzaErrorInesperado(),
          token: kToken,
        );

        await bloc.cargarResumen(1);

        expect(bloc.estado, isA<PagoError>());
        expect((bloc.estado as PagoError).mensaje, contains('Error inesperado'));
      },
    );

    test(
      'un error inesperado o de plataforma durante confirmarYPagar transiciona a PagoRechazado sin congelar en PagoProcesando',
      () async {
        final api = _ApiQueFallaInesperadamenteEnIniciar();
        final bloc = PagoBloc(api: api, token: kToken);
        await bloc.cargarResumen(1);

        final exito = await bloc.confirmarYPagar();

        expect(exito, false);
        expect(bloc.estado, isA<PagoRechazado>());
        expect((bloc.estado as PagoRechazado).motivo, contains('Fallo inesperado'));
      },
    );
  });
}

class _ApiQueLanzaErrorInesperado extends MockPagoApi {
  @override
  Future<ResumenPagoDto> obtenerResumenPago(int idVenta, {required String token}) async {
    throw const FormatException('Payload corrupto');
  }
}

class _ApiQueFallaInesperadamenteEnIniciar extends MockPagoApi {
  @override
  Future<PagoIntentoOutDto> iniciarPago(PagoIniciarInDto datos, {required String token}) async {
    throw Exception('Error nativo de plataforma');
  }
}

