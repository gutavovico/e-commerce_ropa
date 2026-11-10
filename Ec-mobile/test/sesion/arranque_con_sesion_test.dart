import 'package:ec_mobile/main.dart';
import 'package:ec_mobile/src/core/empresa_actual.dart';
import 'package:ec_mobile/src/core/sesion_guardada.dart';
import 'package:ec_mobile/src/core/sesion_manager.dart';
import 'package:ec_mobile/src/core/sin_conexion/almacen_local.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_seleccion_empresa.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu16_cu17_caja/presentacion/pantallas/pantalla_caja.dart';
import 'package:ec_mobile/src/navegacion/pantalla_principal_hub.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'sesion_guardada_test.dart' show tokenQueVence;

/// Almacén en memoria: en una prueba de widgets, SQLite (ffi) no termina dentro del reloj simulado.
class _AlmacenEnMemoria implements AlmacenLocal {
  final valores = <String, Map<String, dynamic>>{};

  @override
  Future<Map<String, dynamic>?> valor(String clave) async => valores[clave];

  @override
  Future<void> guardarValor(String clave, Map<String, dynamic> valor) async => valores[clave] = valor;

  @override
  Future<void> borrarValor(String clave) async => valores.remove(clave);

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

/// Defecto del bloque 3 · AC-A2/AC-A3: la app entra con la sesión guardada, sin pasar por el login.
void main() {
  late _AlmacenEnMemoria almacen;
  late SesionGuardada sesiones;
  final token = tokenQueVence(DateTime.now().add(const Duration(hours: 5)));

  setUp(() {
    almacen = _AlmacenEnMemoria();
    sesiones = SesionGuardada(almacen: almacen);
    EmpresaActual.instancia.limpiar();
  });

  Future<void> arrancar(WidgetTester tester, SesionPersistida? sesion) async {
    await tester.binding.setSurfaceSize(const Size(400, 900));
    await tester.pumpWidget(EcMobileApp(sesionInicial: sesion, sesionGuardada: sesiones));
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 300));
  }

  testWidgets('sin sesión guardada arranca en el login', (tester) async {
    await arrancar(tester, null);
    expect(find.byType(PantallaLogin), findsOneWidget);
  });

  testWidgets('AC-A2: un cajero con sesión vigente entra directo a su caja, con la empresa de su cuenta',
      (tester) async {
    const empresa = EmpresaTienda(codigo: 'menshopping', nombre: 'Menshopping');
    await arrancar(tester, SesionPersistida(token: token, nombreUsuario: 'Carlos Perez', rol: 'cajero', empresa: empresa));
    expect(find.byType(PantallaLogin), findsNothing);
    expect(find.byType(PantallaCaja), findsOneWidget);
    expect(EmpresaActual.instancia.empresa, empresa);
  });

  testWidgets('AC-A2: un cliente con tienda guardada entra directo al hub de esa tienda', (tester) async {
    const tienda = EmpresaTienda(codigo: 'menshopping', nombre: 'Menshopping');
    // Token sin rol de cliente: así el hub no arranca la base local real (SQLite y red del sistema),
    // que no existe en una prueba de widgets; el destino lo decide el rol guardado.
    final tokenSinServicio = tokenQueVence(DateTime.now().add(const Duration(hours: 5)), rol: 'prueba');
    await arrancar(tester, SesionPersistida(token: tokenSinServicio, nombreUsuario: 'Ana Rojas', rol: 'cliente', empresa: tienda));
    expect(find.byType(PantallaSeleccionEmpresa), findsNothing);
    expect(find.byType(PantallaPrincipalHub), findsOneWidget);
    expect(EmpresaActual.instancia.empresa, tienda);
  });

  testWidgets('AC-A2: un cliente que aún no eligió tienda vuelve a la selección de tienda', (tester) async {
    await arrancar(tester, SesionPersistida(token: token, nombreUsuario: 'Ana Rojas', rol: 'cliente'));
    expect(find.byType(PantallaSeleccionEmpresa), findsOneWidget);
  });

  testWidgets('AC-A3: un 401 lleva al login y borra la sesión guardada', (tester) async {
    final sesion = SesionPersistida(token: token, nombreUsuario: 'Carlos Perez', rol: 'cajero');
    await sesiones.guardar(sesion);
    await arrancar(tester, sesion);
    SesionManager.instancia.notificarSesionExpirada(mensaje: 'Tu sesión expiró.');
    await tester.pump();
    await tester.pump(const Duration(milliseconds: 500));
    expect(find.byType(PantallaLogin), findsOneWidget);
    expect(almacen.valores, isEmpty);
  });
}
