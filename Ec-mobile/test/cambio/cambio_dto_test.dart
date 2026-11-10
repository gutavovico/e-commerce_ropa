import 'dart:convert';

import 'package:ec_mobile/src/modulos/compras_pagos/cu18_cambio_prenda/datos/cambio_prenda_api.dart';
import 'package:flutter_test/flutter_test.dart';

import 'payloads_cambio.dart' as p;

Map<String, dynamic> _j(String s) => jsonDecode(s) as Map<String, dynamic>;

void main() {
  test('venta cambiable: lo que queda y el valor pagado por unidad', () {
    final v = VentaCambiable.fromJson(_j(p.venta));
    expect((v.diasTranscurridos, v.plazoDias), (5, 15));
    expect(v.lineas.single.cambiables, 2);
    expect(v.lineas.single.valorUnitario, '90.00');
  });

  test('previsualización y comprobante: importes como cadena del servidor', () {
    final previo = CambioPrenda.fromJson(_j(p.previo));
    expect((previo.valorDevuelto, previo.valorNuevo, previo.diferencia), ('90.00', '100.00', '10.00'));
    expect(previo.pagaElCliente, isTrue);
    final c = CambioPrenda.fromJson(_j(p.cambio));
    expect(c.numeroComprobante, 'CAM-2026-00001');
    expect((c.montoRecibido, c.vuelto), ('20.00', '10.00'));
    expect(c.nuevas.single.talla, 'L');
  });
}
