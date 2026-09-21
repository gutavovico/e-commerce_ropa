import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/fuentes_datos/sucursales_remoto_datasource.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/ciudad_dto.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/sucursal_dto.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/repositorios/sucursales_repositorio_impl.dart';

class MockSucursalesRemotoDataSource implements SucursalesRemotoDataSource {
  final List<CiudadDto> ciudadesSimuladas;
  final List<SucursalDto> sucursalesSimuladas;
  final bool simularErrorConflicto;

  MockSucursalesRemotoDataSource({
    this.ciudadesSimuladas = const [],
    this.sucursalesSimuladas = const [],
    this.simularErrorConflicto = false,
  });

  @override
  Future<List<CiudadDto>> obtenerCiudades(String token) async {
    return ciudadesSimuladas;
  }

  @override
  Future<CiudadDto> crearCiudad(
      String token, Map<String, dynamic> datos) async {
    if (simularErrorConflicto) {
      throw const ConflictoOperacionException('Ciudad ya registrada');
    }
    return CiudadDto(
      idCiudad: 99,
      nombre: datos['nombre'] as String,
      pais: datos['pais'] as String,
      creadoEn: '2026-02-01T10:00:00Z',
      totalSucursales: 0,
    );
  }

  @override
  Future<void> eliminarCiudad(String token, int idCiudad) async {
    if (simularErrorConflicto) {
      throw const ConflictoOperacionException('Ciudad con dependencias');
    }
  }

  @override
  Future<List<SucursalDto>> obtenerSucursales(
    String token, {
    int? idCiudad,
    bool? activa,
    String? q,
  }) async {
    return sucursalesSimuladas;
  }

  @override
  Future<SucursalDto> crearSucursal(
      String token, Map<String, dynamic> datos) async {
    if (simularErrorConflicto) {
      throw const ConflictoOperacionException('Sucursal duplicada');
    }
    return SucursalDto(
      idSucursal: 99,
      idCiudad: datos['id_ciudad'] as int,
      ciudadNombre: 'Madrid',
      nombre: datos['nombre'] as String,
      direccion: datos['direccion'] as String,
      horarioApertura: datos['horario_apertura'] as String,
      horarioCierre: datos['horario_cierre'] as String,
      activa: true,
      creadoEn: '2026-02-01T10:00:00Z',
      totalEmpleados: 0,
      totalPrendasStock: 0,
      reservasActivasConteo: 0,
    );
  }

  @override
  Future<SucursalDto> actualizarSucursal(
    String token,
    int idSucursal,
    Map<String, dynamic> datos,
  ) async {
    return sucursalesSimuladas.first;
  }

  @override
  Future<SucursalDto> cambiarEstadoSucursal(
    String token,
    int idSucursal,
    bool activa,
  ) async {
    if (simularErrorConflicto) {
      throw const ConflictoOperacionException(
          'No se puede desactivar la sucursal: mantiene reservas activas');
    }
    final s = sucursalesSimuladas.first;
    return SucursalDto(
      idSucursal: s.idSucursal,
      idCiudad: s.idCiudad,
      ciudadNombre: s.ciudadNombre,
      nombre: s.nombre,
      direccion: s.direccion,
      horarioApertura: s.horarioApertura,
      horarioCierre: s.horarioCierre,
      activa: activa,
      creadoEn: s.creadoEn,
      totalEmpleados: s.totalEmpleados,
      totalPrendasStock: s.totalPrendasStock,
      reservasActivasConteo: s.reservasActivasConteo,
    );
  }

  @override
  Future<void> eliminarSucursal(String token, int idSucursal) async {}
}

void main() {
  const mockCiudadDto = CiudadDto(
    idCiudad: 1,
    nombre: 'Madrid',
    pais: 'Espana',
    creadoEn: '2026-01-10T10:00:00Z',
    totalSucursales: 1,
  );

  const mockSucursalDto = SucursalDto(
    idSucursal: 10,
    idCiudad: 1,
    ciudadNombre: 'Madrid',
    nombre: 'Boutique Serrano',
    direccion: 'Calle Serrano 45',
    telefono: '+34 910 123 456',
    horarioApertura: '10:00',
    horarioCierre: '20:30',
    activa: true,
    creadoEn: '2026-01-15T10:00:00Z',
    totalEmpleados: 5,
    totalPrendasStock: 80,
    reservasActivasConteo: 0,
  );

  group('SucursalesRepositorioImpl Tests', () {
    test('obtenerCiudades mapea DTOs a entidades de dominio', () async {
      final repo = SucursalesRepositorioImpl(
        remotoDataSource: MockSucursalesRemotoDataSource(
          ciudadesSimuladas: [mockCiudadDto],
        ),
      );

      final ciudades = await repo.obtenerCiudades('token');
      expect(ciudades.length, 1);
      expect(ciudades.first.nombre, 'Madrid');
    });

    test('obtenerSucursales mapea DTOs a entidades de dominio', () async {
      final repo = SucursalesRepositorioImpl(
        remotoDataSource: MockSucursalesRemotoDataSource(
          sucursalesSimuladas: [mockSucursalDto],
        ),
      );

      final sucursales = await repo.obtenerSucursales('token');
      expect(sucursales.length, 1);
      expect(sucursales.first.nombre, 'Boutique Serrano');
      expect(sucursales.first.activa, isTrue);
    });

    test('cambiarEstadoSucursal propaga excepcion de conflicto 409',
        () async {
      final repo = SucursalesRepositorioImpl(
        remotoDataSource: MockSucursalesRemotoDataSource(
          sucursalesSimuladas: [mockSucursalDto],
          simularErrorConflicto: true,
        ),
      );

      expect(
        () => repo.cambiarEstadoSucursal('token', 10, false),
        throwsA(isA<ConflictoOperacionException>()),
      );
    });
  });
}
