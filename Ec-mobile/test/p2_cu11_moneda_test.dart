import 'dart:convert';

import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/core/empresa_actual.dart';
import 'package:ec_mobile/src/core/moneda.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';

/// Fix de P2-CU11 · Moneda de la tienda (M6, M8) con payloads literales del backend.
void main() {
  tearDown(EmpresaActual.instancia.limpiar);

  group('formatoImporte', () {
    test('formato boliviano con el símbolo de la moneda', () {
      expect(formatoImporte('1234.5', 'BOB'), 'Bs 1.234,50');
      expect(formatoImporte(98765.43, 'USD'), r'US$ 98.765,43');
      expect(formatoImporte(-5, 'BOB'), '-Bs 5,00');
      expect(formatoImporte(null), '');
      expect(formatoImporte('no-es-numero'), '');
    });

    test('sin moneda indicada usa la de la tienda elegida, y BOB sin tienda', () {
      expect(formatoImporte('10'), 'Bs 10,00');
      EmpresaActual.instancia.elegir(const EmpresaTienda(codigo: 'b', nombre: 'B', moneda: 'USD'));
      expect(formatoImporte('10'), r'US$ 10,00');
      expect(simboloMoneda(), r'US$');
    });
  });

  test('el login trae la moneda de la empresa y de cada tienda del cliente', () {
    // Payload literal de POST /api/v1/autenticacion/login (fix de P2-CU11)
    final json = jsonDecode('''
      {"access_token": "t", "token_type": "bearer", "id_usuario": 14, "email": "c@tienda.com",
       "nombres": "Ana", "apellidos": "Ruiz", "rol": "cliente", "id_sucursal": null, "tenant": null,
       "empresas": [{"codigo": "fashionstore", "nombre": "FASHION STORE", "moneda": "BOB"},
                    {"codigo": "pruebas-b", "nombre": "Empresa B", "moneda": "USD"}]}
    ''') as Map<String, dynamic>;
    final dto = LoginRespuestaDto.fromJson(json);
    expect(dto.empresas.map((e) => e.moneda), ['BOB', 'USD']);
  });

  test('una tienda sin moneda (payload anterior al fix) se trata como BOB', () {
    final tienda = EmpresaTienda.fromJson({'codigo': 'fashionstore', 'nombre': 'FASHION STORE'});
    expect(tienda.moneda, 'BOB');
    expect(tienda.toJson()['moneda'], 'BOB');
  });
}
