import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/fuentes_datos/sucursales_remoto_datasource.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/ciudad.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/entidades/sucursal.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/dominio/repositorios/sucursales_repositorio.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_bloc.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/presentacion/bloc/sucursales_estado.dart';

class MockSucursalesRepositorio implements SucursalesRepositorio {
  final List<Ciudad> ciudadesSimuladas;
  final List<Sucursal> sucursalesSimuladas;
  final bool simularConflicto;

  MockSucursalesRepositorio({
    this.ciudadesSimuladas = const [],
    this.sucursalesSimuladas = const [],
    this.simularConflicto = false,
  });

  @override
  Future<List<Ciudad>> obtenerCiudades(String token) async =>
      ciudadesSimuladas;

  @override
  Future<Ciudad> crearCiudad(
    String token, {
    required String nombre,
    required String pais,
  }) async {
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
  Future<List<Sucursal>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  }) async =>
      sucursalesSimuladas;

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
    return Sucursal(
      idSucursal: 99,
      idCiudad: idCiudad,
      ciudadNombre: 'Madrid',
      nombre: nombre,
      direccion: direccion,
      telefono: telefono,
      horarioApertura: horarioApertura,
      horarioCierre: horarioCierre,
      activa: true,
      creadoEn: DateTime.now(),
      totalEmpleados: 0,
      totalPrendasStock: 0,
      reservasActivasConteo: 0,
    );
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
    return sucursalesSimuladas.first;
  }

  @override
  Future<Sucursal> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  ) async {
    if (simularConflicto) {
      throw const ConflictoOperacionException(
          'No se puede desactivar la sucursal: mantiene reservas activas o inventario en custodia.');
    }
    return sucursalesSimuladas.first.copyWith(activa: activa);
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
      totalSucursales: 2,
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
    Sucursal(
      idSucursal: 20,
      idCiudad: 2,
      ciudadNombre: 'Barcelona',
      nombre: 'Atelier Paseo de Gracia',
      direccion: 'Passeig de Gracia 88',
      telefono: '+34 934 987 654',
      horarioApertura: '10:30',
      horarioCierre: '21:00',
      activa: false,
      creadoEn: DateTime(2026, 1, 20),
      totalEmpleados: 0,
      totalPrendasStock: 0,
      reservasActivasConteo: 0,
    ),
  ];

  group('SucursalesBloc Tests', () {
    test('estado inicial es SucursalesInicial', () {
      final bloc = SucursalesBloc(
        repositorio: MockSucursalesRepositorio(),
      );
      expect(bloc.estado, isA<SucursalesInicial>());
      expect(bloc.estaCargando, isFalse);
    });

    test('cargarDatos emite SucursalesCargando y luego SucursalesCargado',
        () async {
      final bloc = SucursalesBloc(
        repositorio: MockSucursalesRepositorio(
          ciudadesSimuladas: mockCiudades,
          sucursalesSimuladas: mockSucursales,
        ),
      );

      final estados = <SucursalesEstado>[];
      bloc.addListener(() => estados.add(bloc.estado));

      await bloc.cargarDatos('token_valido');

      expect(estados.length, 2);
      expect(estados[0], isA<SucursalesCargando>());
      expect(estados[1], isA<SucursalesCargado>());

      final cargado = estados[1] as SucursalesCargado;
      expect(cargado.ciudades.length, 2);
      expect(cargado.sucursales.length, 2);
      expect(cargado.totalActivas, 1);
      expect(cargado.totalInactivas, 1);
    });

    test('filtra sucursales reactivamente por ciudad y por busqueda', () async {
      final bloc = SucursalesBloc(
        repositorio: MockSucursalesRepositorio(
          ciudadesSimuladas: mockCiudades,
          sucursalesSimuladas: mockSucursales,
        ),
      );

      await bloc.cargarDatos('token');
      var estado = bloc.estado as SucursalesCargado;
      expect(estado.sucursalesFiltradas.length, 2);

      // Filtro ciudad Madrid (id 1)
      bloc.seleccionarFiltroCiudad(1);
      estado = bloc.estado as SucursalesCargado;
      expect(estado.sucursalesFiltradas.length, 1);
      expect(estado.sucursalesFiltradas.first.nombre, contains('Serrano'));

      // Filtro busqueda textual
      bloc.seleccionarFiltroCiudad(null);
      bloc.actualizarBusqueda('Barcelona');
      estado = bloc.estado as SucursalesCargado;
      expect(estado.sucursalesFiltradas.length, 1);
      expect(estado.sucursalesFiltradas.first.ciudadNombre, 'Barcelona');
    });

    test('cambiarEstadoSucursal con conflicto 409 preserva catalogo y notifica error (AC-14)',
        () async {
      final bloc = SucursalesBloc(
        repositorio: MockSucursalesRepositorio(
          ciudadesSimuladas: mockCiudades,
          sucursalesSimuladas: mockSucursales,
          simularConflicto: true,
        ),
      );

      await bloc.cargarDatos('token');
      await bloc.cambiarEstadoSucursal('token', 10, false);

      final estado = bloc.estado as SucursalesCargado;
      expect(estado.sucursales.length, 2);
      expect(estado.mensajeError, contains('reservas activas'));
      expect(estado.operacionEnCurso, isFalse);
    });

    test('crearSucursal agrega la nueva boutique a la coleccion cargada',
        () async {
      final bloc = SucursalesBloc(
        repositorio: MockSucursalesRepositorio(
          ciudadesSimuladas: mockCiudades,
          sucursalesSimuladas: mockSucursales,
        ),
      );

      await bloc.cargarDatos('token');
      final exito = await bloc.crearSucursal(
        'token',
        idCiudad: 1,
        nombre: 'Atelier Gran Via',
        direccion: 'Gran Via 22',
        horarioApertura: '10:00',
        horarioCierre: '21:00',
      );

      expect(exito, isTrue);
      final estado = bloc.estado as SucursalesCargado;
      expect(estado.sucursales.length, 3);
      expect(estado.mensajeExito, contains('registrada'));
    });
  });
}
