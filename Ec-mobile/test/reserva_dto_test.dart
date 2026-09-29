import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/reservas/cu13_consultar_cancelar_reservas/datos/modelos/reserva_dto.dart';

import 'mocks/mock_reservas_api.dart';

void main() {
  group('Contrato CU13/CU14 con el backend', () {
    test('MisReservasDto.fromJson lee la respuesta real de GET /reservas/mias', () {
      final mias = MisReservasDto.fromJson(respuestaMisReservasBackend);

      expect(mias.resumen.activas, 1);
      expect(mias.resumen.proxima?.idReserva, 1);
      expect(mias.resumen.proxima?.nombreSucursal, 'Atelier Serrano - Madrid');
      expect(mias.proximas, hasLength(1));
      expect(mias.historial, hasLength(1));
    });

    test('ReservaDto.fromJson de una reserva próxima expone puede_cancelar del servidor', () {
      final mias = MisReservasDto.fromJson(respuestaMisReservasBackend);
      final reserva = mias.proximas.first;

      expect(reserva.idReserva, 1);
      expect(reserva.codigoReserva, 'RES-2026-0001');
      expect(reserva.estado, 'pendiente');
      expect(reserva.puedeCancelar, true);
      expect(reserva.sucursal.nombre, 'Atelier Serrano - Madrid');
      expect(reserva.totalPrendas, 1);
      expect(reserva.observacion, 'Prefiero probador amplio');

      final item = reserva.items.first;
      expect(item.nombreProducto, 'Blusa de satén fluido');
      expect(item.tallaCodigo, '38');
      expect(item.colorNombre, 'Champagne');
      // FastAPI serializa Decimal como cadena JSON: debe parsearse con tolerancia.
      expect(item.precioUnitario, 310.00);
    });

    test('una reserva del historial (vencida) llega con puede_cancelar en false', () {
      final mias = MisReservasDto.fromJson(respuestaMisReservasBackend);
      final reserva = mias.historial.first;

      expect(reserva.estado, 'vencida');
      expect(reserva.puedeCancelar, false);
      expect(reserva.items.first.imagenUrl, isNull);
      expect(reserva.observacion, isNull);
    });

    test('ResumenReservasDto tolera la ausencia de próxima reserva', () {
      final mias = MisReservasDto.fromJson({
        'resumen': {'activas': 0, 'proxima': null},
        'proximas': [],
        'historial': [],
      });

      expect(mias.resumen.activas, 0);
      expect(mias.resumen.proxima, isNull);
      expect(mias.proximas, isEmpty);
    });

    test('MisReservasDto por defecto (constructor const) no tiene reservas', () {
      const mias = MisReservasDto();
      expect(mias.resumen.activas, 0);
      expect(mias.proximas, isEmpty);
      expect(mias.historial, isEmpty);
    });

    test('ReservaDto.fromJson de la confirmación de cancelación', () {
      final reserva = ReservaDto.fromJson(respuestaReservaCanceladaBackend);

      expect(reserva.estado, 'cancelada');
      expect(reserva.puedeCancelar, false);
      expect(reserva.items, isEmpty);
    });
  });
}
