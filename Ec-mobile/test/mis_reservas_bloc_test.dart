import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/datos/datasources/reservas_api.dart';
import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/presentacion/bloc/mis_reservas_bloc.dart';

import 'mocks/mock_reservas_api.dart';

const String kToken = 'jwt-de-prueba';

void main() {
  group('MisReservasBloc', () {
    test('cargarMisReservas transiciona Inicial -> Cargando -> Listo con las reservas del servidor', () async {
      final api = MockReservasApi();
      final bloc = MisReservasBloc(api: api, token: kToken);

      expect(bloc.estado, isA<ReservasInicial>());

      await bloc.cargarMisReservas();

      expect(bloc.estado, isA<ReservasListo>());
      final estado = bloc.estado as ReservasListo;
      expect(estado.misReservas.proximas, hasLength(1));
      expect(estado.misReservas.historial, hasLength(1));
      expect(estado.misReservas.resumen.activas, 1);
      expect(api.llamadasObtenerMisReservas, 1);
    });

    test('un fallo de red al cargar transiciona a ReservasError', () async {
      final api = MockReservasApi(
        excepcionAlCargar: const ReservaException('No se pudo conectar con el atelier.'),
      );
      final bloc = MisReservasBloc(api: api, token: kToken);

      await bloc.cargarMisReservas();

      expect(bloc.estado, isA<ReservasError>());
      expect((bloc.estado as ReservasError).mensaje, 'No se pudo conectar con el atelier.');
    });

    test('cancelarReserva exitosa recarga la lista completa y desactiva cancelando', () async {
      final api = MockReservasApi();
      final bloc = MisReservasBloc(api: api, token: kToken);
      await bloc.cargarMisReservas();

      final exito = await bloc.cancelarReserva(1, 'Cambio de planes');

      expect(exito, true);
      expect(bloc.cancelando, false);
      expect(bloc.errorCancelacion, isNull);
      expect(api.llamadasCancelarReserva, 1);
      expect(api.ultimoIdReservaCancelado, 1);
      expect(api.ultimoMotivoEnviado, 'Cambio de planes');
      // Se recarga la lista completa: es el servidor quien decide el nuevo reparto.
      expect(api.llamadasObtenerMisReservas, 2);
    });

    test('cancelarReserva fallida conserva el estado ya cargado y expone errorCancelacion', () async {
      final api = MockReservasApi(
        excepcionAlCancelar: const ReservaException(
          'Esta reserva ya no admite cancelación.',
          codigo: 'RESERVA_NO_CANCELABLE',
        ),
      );
      final bloc = MisReservasBloc(api: api, token: kToken);
      await bloc.cargarMisReservas();

      final exito = await bloc.cancelarReserva(1, 'Cambio de planes');

      expect(exito, false);
      expect(bloc.cancelando, false);
      expect(bloc.errorCancelacion, 'Esta reserva ya no admite cancelación.');
      // El listado ya cargado no desaparece por un fallo de cancelación en vuelo.
      expect(bloc.estado, isA<ReservasListo>());
    });

    test('limpiarErrorCancelacion borra el mensaje de error tras mostrarlo', () async {
      final api = MockReservasApi(
        excepcionAlCancelar: const ReservaException('Reserva ajena.', codigo: 'RESERVA_AJENA'),
      );
      final bloc = MisReservasBloc(api: api, token: kToken);
      await bloc.cargarMisReservas();
      await bloc.cancelarReserva(1, 'Motivo cualquiera');
      expect(bloc.errorCancelacion, isNotNull);

      bloc.limpiarErrorCancelacion();

      expect(bloc.errorCancelacion, isNull);
    });
  });
}
