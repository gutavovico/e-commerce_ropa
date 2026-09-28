import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_realizar_pago/datos/modelos/pago_dto.dart';

import 'mocks/mock_pago_api.dart';

void main() {
  group('Contrato CU16 con el backend', () {
    test('ResumenPagoDto.fromJson lee la respuesta real de GET /ventas/{id}/resumen-pago', () {
      final resumen = ResumenPagoDto.fromJson(respuestaResumenPagoBackend);

      expect(resumen.idVenta, 1);
      expect(resumen.numeroComprobante, 'FS-2026-000001');
      expect(resumen.items, hasLength(1));
      // FastAPI serializa Decimal como cadena JSON: debe parsearse con tolerancia.
      expect(resumen.subtotal, 2100.00);
      expect(resumen.descuento, 160.00);
      expect(resumen.total, 1940.00);
      expect(resumen.segundosRestantes, 1500);
      expect(resumen.metodosDisponibles, contains('tarjeta_credito'));
      expect(resumen.esRecogidaBoutique, false);

      final item = resumen.items.first;
      expect(item.nombreProducto, 'Vestido plisado en seda natural');
      expect(item.nombreSucursal, 'Atelier Serrano - Madrid');
      expect(item.precioUnitario, 890.00);
    });

    test('ResumenPagoDto respeta la invariante total = subtotal - descuento', () {
      final resumen = ResumenPagoDto.fromJson(respuestaResumenPagoBackend);
      expect(resumen.subtotal - resumen.descuento, resumen.total);
    });

    test('ResumenPagoDto.esRecogidaBoutique detecta la recogida en boutique', () {
      final resumen = ResumenPagoDto.fromJson({
        ...respuestaResumenPagoBackend,
        'tipo_entrega': 'recogida_boutique',
        'direccion_envio': null,
        'nombre_sucursal_retiro': 'Atelier Serrano - Madrid',
      });
      expect(resumen.esRecogidaBoutique, true);
      expect(resumen.nombreSucursalRetiro, 'Atelier Serrano - Madrid');
    });

    test('PagoConfirmadoDto.fromJson lee la respuesta real de POST /pagos/{id_pago}/confirmar', () {
      final pago = PagoConfirmadoDto.fromJson(respuestaPagoConfirmadoBackend);

      expect(pago.idPago, 505);
      expect(pago.estadoPago, 'confirmado');
      expect(pago.estadoVenta, 'pagada');
      expect(pago.marcaTarjeta, 'VISA');
      // La clave real es `ultimos_digitos`, no `ultimos_digitos_tarjeta`: el mismo defecto de
      // contrato que hubo que corregir en `pago.model.ts` de Web.
      expect(pago.ultimosDigitos, '1111');
      expect(pago.confirmadoEn, isNotNull);
      expect(pago.mensajeConfirmacion, contains('Pago confirmado'));
    });

    test('PagoConfirmadoDto tolera un pago en efectivo pendiente sin confirmadoEn', () {
      final pago = PagoConfirmadoDto.fromJson({
        ...respuestaPagoConfirmadoBackend,
        'estado_pago': 'pendiente',
        'estado_venta': 'pendiente',
        'metodo_pago': 'efectivo',
        'referencia_pasarela': null,
        'marca_tarjeta': null,
        'ultimos_digitos': null,
        'confirmado_en': null,
        'mensaje_confirmacion': 'Pago en efectivo registrado.',
      });

      expect(pago.estadoPago, 'pendiente');
      expect(pago.confirmadoEn, isNull);
      expect(pago.marcaTarjeta, isNull);
    });

    test('PagoIniciarInDto.toJson no lleva ningún dato de tarjeta', () {
      const payload = PagoIniciarInDto(
        idVenta: 1,
        metodoPago: 'tarjeta_credito',
        claveIdempotencia: 'movil-123',
        escenarioPrueba: EscenarioPrueba.aprobado,
      );

      final json = payload.toJson();
      expect(json, {
        'id_venta': 1,
        'metodo_pago': 'tarjeta_credito',
        'clave_idempotencia': 'movil-123',
        'escenario_prueba': 'aprobado',
      });
      expect(json.containsKey('tarjeta'), false);
      expect(json.containsKey('numero'), false);
      expect(json.containsKey('cvv'), false);
    });

    test('PagoIniciarInDto.toJson omite escenario_prueba cuando no se indica (Stripe real)', () {
      const payload = PagoIniciarInDto(idVenta: 1, metodoPago: 'qr');
      expect(payload.toJson().containsKey('escenario_prueba'), false);
    });

    test('PagoIntentoOutDto.fromJson lee la respuesta real de POST /pagos/intentos', () {
      final intento = PagoIntentoOutDto.fromJson(respuestaIntentoPagoBackend);

      expect(intento.idPago, 505);
      expect(intento.clientSecret, 'pi_test_123456789_secret_test');
      expect(intento.yaConfirmado, false);
      expect(intento.confirmacion, isNull);
    });

    test('PagoIntentoOutDto.fromJson deserializa la confirmación embebida en un reenvío idempotente', () {
      final intento = PagoIntentoOutDto.fromJson({
        'id_pago': 505,
        'client_secret': null,
        'ya_confirmado': true,
        'confirmacion': respuestaPagoConfirmadoBackend,
      });

      expect(intento.yaConfirmado, true);
      expect(intento.clientSecret, isNull);
      expect(intento.confirmacion?.estadoPago, 'confirmado');
    });

    test('parsearImporte tolera cadenas, números y valores ausentes', () {
      final resumen = ResumenPagoDto.fromJson({
        ...respuestaResumenPagoBackend,
        'total': 1940,
        'descuento': null,
      });
      expect(resumen.total, 1940.0);
      expect(resumen.descuento, 0.0);
    });
  });
}
