import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/ciudad.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/repositorios/sucursales_repositorio.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_bloc.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/pantallas/sucursales_admin_pantalla.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/widgets/formulario_sucursal_sheet.dart';

class MockSucursalesRepositorioWidget implements SucursalesRepositorio {
  final List<Ciudad> ciudades;
  final List<Sucursal> sucursales;

  MockSucursalesRepositorioWidget({
    required this.ciudades,
    required this.sucursales,
  });

  @override
  Future<List<Ciudad>> obtenerCiudades(String token) async => ciudades;

  @override
  Future<List<Sucursal>> obtenerSucursales(String token,
          {int? idCiudad, bool? activa, String? q}) async =>
      sucursales;

  @override
  Future<Ciudad> crearCiudad(String token,
      {required String nombre, required String pais}) async {
    return Ciudad(
      idCiudad: 99,
      nombre: nombre,
      pais: pais,
      creadoEn: DateTime.now(),
      totalSucursales: 0,
    );
  }

  @override
  Future<void> eliminarCiudad(String token, int idCiudad) async {}

  @override
  Future<Sucursal> crearSucursal(
    String token, {
    required int idCiudad,
    required String nombre,
    required String direccion,
    String? telefono,
    required String horarioApertura,
    required String horarioCierre,
  }) async {
    return sucursales.first;
  }

  @override
  Future<Sucursal> actualizarSucursal(
    String token,
    int idSucursal, {
    int? idCiudad,
    String? nombre,
    String? direccion,
    String? telefono,
    String? horarioApertura,
    String? horarioCierre,
  }) async {
    return sucursales.first;
  }

  @override
  Future<Sucursal> cambiarEstadoSucursal(
      String token, int idSucursal, bool activa) async {
    return sucursales.first.copyWith(activa: activa);
  }

  @override
  Future<void> eliminarSucursal(String token, int idSucursal) async {}
}

void main() {
  final mockCiudades = [
    Ciudad(
      idCiudad: 1,
      nombre: 'Madrid',
      pais: 'Espana',
      creadoEn: DateTime(2026, 1, 10),
      totalSucursales: 1,
    ),
    Ciudad(
      idCiudad: 2,
      nombre: 'Barcelona',
      pais: 'Espana',
      creadoEn: DateTime(2026, 1, 12),
      totalSucursales: 1,
    ),
  ];

  final mockSucursales = [
    Sucursal(
      idSucursal: 10,
      idCiudad: 1,
      ciudadNombre: 'Madrid',
      nombre: 'Boutique Serrano Haute Couture',
      direccion: 'Calle Serrano 45',
      telefono: '+34 910 123 456',
      horarioApertura: '10:00',
      horarioCierre: '20:30',
      activa: true,
      creadoEn: DateTime(2026, 1, 15),
      totalEmpleados: 8,
      totalPrendasStock: 120,
      reservasActivasConteo: 3,
    ),
  ];

  Widget construirPantallaPrueba({SucursalesBloc? bloc}) {
    return MaterialApp(
      home: SucursalesAdminPantalla(
        token: 'token_prueba',
        bloc: bloc ??
            SucursalesBloc(
              repositorio: MockSucursalesRepositorioWidget(
                ciudades: mockCiudades,
                sucursales: mockSucursales,
              ),
            ),
      ),
    );
  }

  group('SucursalesAdminPantalla Widget Tests', () {
    testWidgets('renderiza cabecera editorial, buscador y boton flotante',
        (tester) async {
      await tester.pumpWidget(construirPantallaPrueba());
      await tester.pumpAndSettle();

      expect(find.text('FASHION STORE'), findsOneWidget);
      expect(find.text('Gestion Territorial'), findsOneWidget);
      expect(find.byType(FloatingActionButton), findsOneWidget);
      expect(find.text('NUEVA BOUTIQUE'), findsOneWidget);
      expect(find.byType(TextField), findsOneWidget);
    });

    testWidgets('renderiza tarjetas de sucursal con monograma e indicadores',
        (tester) async {
      await tester.pumpWidget(construirPantallaPrueba());
      await tester.pumpAndSettle();

      expect(find.text('Boutique Serrano Haute Couture'), findsOneWidget);
      expect(find.text('Calle Serrano 45'), findsOneWidget);
      expect(find.text('10:00 - 20:30'), findsOneWidget);
      expect(find.text('ACTIVA'), findsOneWidget);
      expect(find.text('PERSONAL'), findsOneWidget);
      expect(find.text('STOCK'), findsOneWidget);
      expect(find.text('RESERVAS'), findsOneWidget);
    });

    testWidgets('despliega BottomSheet al presionar NUEVA BOUTIQUE (AC-18)',
        (tester) async {
      await tester.pumpWidget(construirPantallaPrueba());
      await tester.pumpAndSettle();

      final fab = find.byType(FloatingActionButton);
      await tester.tap(fab);
      await tester.pumpAndSettle();

      expect(find.byType(FormularioSucursalSheet), findsOneWidget);
      expect(find.text('REGISTRAR BOUTIQUE'), findsOneWidget);
    });

    testWidgets('despliega dialogo confirmatorio al pulsar switch (AC-17)',
        (tester) async {
      await tester.pumpWidget(construirPantallaPrueba());
      await tester.pumpAndSettle();

      final switchWidget = find.byType(Switch);
      expect(switchWidget, findsOneWidget);

      await tester.tap(switchWidget);
      await tester.pumpAndSettle();

      expect(find.text('Confirmar desactivar'), findsOneWidget);
      expect(find.text('CANCELAR'), findsOneWidget);
      expect(find.text('CONFIRMAR'), findsOneWidget);
    });
  });
}
