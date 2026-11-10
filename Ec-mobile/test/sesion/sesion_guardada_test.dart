import 'dart:convert';

import 'package:ec_mobile/src/core/empresa_actual.dart';
import 'package:ec_mobile/src/core/sesion_guardada.dart';
import 'package:ec_mobile/src/core/sin_conexion/almacen_local.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// JWT de prueba con el `exp` indicado (la app nunca comprueba la firma).
String tokenQueVence(DateTime vence, {String rol = 'cliente'}) {
  String parte(Map<String, dynamic> m) => base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
  return '${parte({'alg': 'HS256'})}.${parte({'sub': '7', 'rol': rol, 'exp': vence.millisecondsSinceEpoch ~/ 1000})}.firma';
}

void main() {
  sqfliteFfiInit();
  final ahora = DateTime.utc(2026, 11, 10, 15);
  late AlmacenSqlite almacen;
  late SesionGuardada sesiones;
  const menshopping = EmpresaTienda(codigo: 'menshopping', nombre: 'Menshopping');

  setUp(() {
    almacen = AlmacenSqlite(fabrica: databaseFactoryFfi, ruta: inMemoryDatabasePath);
    sesiones = SesionGuardada(almacen: almacen, ahora: () => ahora);
  });

  tearDown(() => almacen.cerrar());

  test('AC-A1: guarda token, usuario y tienda, y los devuelve mientras el token no vence', () async {
    final token = tokenQueVence(ahora.add(const Duration(hours: 3)));
    await sesiones.guardar(SesionPersistida(token: token, nombreUsuario: 'Ana Rojas', rol: 'cliente', empresa: menshopping));
    final leida = await sesiones.leerVigente();
    expect(leida?.token, token);
    expect(leida?.nombreUsuario, 'Ana Rojas');
    expect(leida?.empresa, menshopping);
  });

  test('AC-A3: un token vencido no restaura la sesión y se borra', () async {
    await sesiones.guardar(SesionPersistida(
        token: tokenQueVence(ahora.subtract(const Duration(minutes: 1))), nombreUsuario: 'Ana', rol: 'cliente'));
    expect(await sesiones.leerVigente(), isNull);
    expect(await almacen.valor('__sesion__'), isNull);
  });

  test('AC-A4: borrar la sesión no toca otros datos locales (las operaciones van en su propia tabla, RN37)', () async {
    await almacen.guardarValor('menshopping:7', {'otra': 'cosa'});
    await sesiones.guardar(SesionPersistida(
        token: tokenQueVence(ahora.add(const Duration(hours: 1))), nombreUsuario: 'Ana', rol: 'cliente'));
    await sesiones.borrar();
    expect(await sesiones.leerVigente(), isNull);
    expect(await almacen.valor('menshopping:7'), isNotNull);
  });

  test('un token ilegible se trata como sin sesión', () async {
    await sesiones.guardar(const SesionPersistida(token: 'no-es-un-jwt', nombreUsuario: 'Ana', rol: 'cliente'));
    expect(await sesiones.leerVigente(), isNull);
  });
}
