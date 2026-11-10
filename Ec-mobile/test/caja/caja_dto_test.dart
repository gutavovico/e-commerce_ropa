import 'dart:convert';

import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/datos/modelos_caja.dart';
import 'package:flutter_test/flutter_test.dart';

import 'payloads_caja.dart' as p;

Map<String, dynamic> _j(String s) => jsonDecode(s) as Map<String, dynamic>;

void main() {
  group('DTO de la caja con payloads literales del backend (P2-CU16/CU17)', () {
    test('variante: precios como cadena y existencias en la sucursal', () {
      final v = VarianteCaja.fromJson(_j(p.variante));
      expect(v.precioFinal, '350.00');
      expect(v.disponible, 5);
      expect(v.talla, 'M');
      expect(VarianteCaja.fromJson(_j(p.varianteAgotada)).disponible, 0);
    });

    test('previsualización: totales del servidor', () {
      final t = PrevisualizacionCaja.fromJson(_j(p.previsualizacion));
      expect((t.subtotal, t.descuento, t.total, t.ivaIncluido), ('350.00', '0.00', '350.00', '40.27'));
      expect(t.lineas.single.subtotalLinea, '350.00');
      expect(t.lineas.single.origen, 'caja');
    });

    test('venta pagada: comprobante con cambio devuelto por el servidor', () {
      final v = VentaCaja.fromJson(_j(p.ventaPagada));
      expect(v.numeroComprobante, 'MOV-2026-00501');
      expect(v.pendiente, isFalse);
      expect(v.cajeroNombre, 'Carlos Perez');
      expect(v.pagoConfirmado!.cambio, '50.00');
      expect(v.pagoConfirmado!.montoRecibido, '400.00');
      expect(v.totales.total, '350.00');
      expect(VentaCaja.fromJson(_j(p.ventaPendiente)).pendiente, isTrue);
    });

    test('reserva, cliente, cupón, pedido web y sucursal', () {
      final r = ReservaCaja.fromJson(_j(p.reserva));
      expect(r.codigo, 'RES-2026-0123');
      expect(r.cliente!.nombreCompleto, 'Ana Rojas');
      expect(r.lineas.single.cantidad, 1);
      expect(CuponCaja.fromJson(_j(p.cupon)).usosRestantes, 5);
      final w = PedidoWebEfectivo.fromJson(_j(p.pedidoWeb));
      expect((w.idPago, w.total), (77, '280.00'));
      expect(SucursalCaja.fromJson(_j(p.sucursal)).esPrincipal, isTrue);
    });

    test('el cuerpo de la venta solo lleva variantes y cantidades (el servidor calcula)', () {
      const venta = VentaCajaIn(idSucursal: 3, codigoCupon: 'OTONO10', lineas: {41: 2});
      expect(venta.toJson(), {
        'id_sucursal': 3,
        'id_cliente': null,
        'reserva': null,
        'codigo_cupon': 'OTONO10',
        'lineas': [
          {'id_variante': 41, 'cantidad': 2},
        ],
        'lineas_reserva_excluidas': <int>[],
      });
    });
  });
}
