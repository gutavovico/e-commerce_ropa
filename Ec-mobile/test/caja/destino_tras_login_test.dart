import 'package:ec_mobile/main.dart';
import 'package:flutter_test/flutter_test.dart';

/// P2-CU16/CU17 · decisión E1: el personal de caja entra directo a la caja; el hub es del cliente.
void main() {
  test('cajero, encargado y administrador abren la caja', () {
    for (final rol in ['cajero', 'encargado_sucursal', 'administrador', 'admin', ' Cajero ']) {
      expect(destinoTrasLogin(rol), DestinoSesion.caja, reason: rol);
    }
  });

  test('el cliente elige tienda y el super administrador sigue en el hub', () {
    expect(destinoTrasLogin('cliente'), DestinoSesion.seleccionDeTienda);
    expect(destinoTrasLogin('super_administrador'), DestinoSesion.hub);
  });
}
