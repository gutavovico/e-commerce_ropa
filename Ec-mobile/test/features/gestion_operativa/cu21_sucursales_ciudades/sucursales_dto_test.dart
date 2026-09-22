import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/ciudad_dto.dart';
import 'package:ec_mobile/src/features/gestion_operativa/cu21_sucursales_ciudades/datos/modelos/sucursal_dto.dart';

void main() {
  group('CiudadDto Tests', () {
    test('deserializa correctamente desde JSON', () {
      final json = {
        'id_ciudad': 1,
        'nombre': 'Madrid',
        'pais': 'Espana',
        'creado_en': '2026-01-10T10:00:00Z',
        'total_sucursales': 3,
      };

      final dto = CiudadDto.fromJson(json);

      expect(dto.idCiudad, 1);
      expect(dto.nombre, 'Madrid');
      expect(dto.pais, 'Espana');
      expect(dto.totalSucursales, 3);

      final entity = dto.toEntity();
      expect(entity.idCiudad, 1);
      expect(entity.nombre, 'Madrid');
      expect(entity.totalSucursales, 3);
    });

    test('aplica valores por defecto ante campos nulos', () {
      final dto = CiudadDto.fromJson(const {});
      expect(dto.idCiudad, 0);
      expect(dto.nombre, '');
      expect(dto.pais, '');
      expect(dto.totalSucursales, 0);
    });

    test('serializa a JSON correctamente', () {
      const dto = CiudadDto(
        idCiudad: 2,
        nombre: 'Barcelona',
        pais: 'Espana',
        creadoEn: '2026-01-12T11:00:00Z',
        totalSucursales: 2,
      );

      final json = dto.toJson();
      expect(json['id_ciudad'], 2);
      expect(json['nombre'], 'Barcelona');
      expect(json['total_sucursales'], 2);
    });
  });

  group('SucursalDto Tests', () {
    test('deserializa correctamente desde JSON', () {
      final json = {
        'id_sucursal': 10,
        'id_ciudad': 1,
        'ciudad_nombre': 'Madrid',
        'nombre': 'Boutique Serrano Haute Couture',
        'direccion': 'Calle de Serrano 45',
        'telefono': '+34 910 123 456',
        'horario_apertura': '10:00',
        'horario_cierre': '20:30',
        'activa': true,
        'creado_en': '2026-01-15T09:00:00Z',
        'total_empleados': 8,
        'total_prendas_stock': 120,
        'reservas_activas_conteo': 3,
      };

      final dto = SucursalDto.fromJson(json);

      expect(dto.idSucursal, 10);
      expect(dto.ciudadNombre, 'Madrid');
      expect(dto.nombre, 'Boutique Serrano Haute Couture');
      expect(dto.activa, isTrue);
      expect(dto.totalEmpleados, 8);
      expect(dto.totalPrendasStock, 120);
      expect(dto.reservasActivasConteo, 3);

      final entity = dto.toEntity();
      expect(entity.idSucursal, 10);
      expect(entity.nombre, 'Boutique Serrano Haute Couture');
      expect(entity.activa, isTrue);
    });

    test('aplica valores por defecto ante campos nulos o ausentes', () {
      final dto = SucursalDto.fromJson(const {});

      expect(dto.idSucursal, 0);
      expect(dto.nombre, '');
      expect(dto.horarioApertura, '10:00');
      expect(dto.horarioCierre, '20:30');
      expect(dto.activa, isTrue);
      expect(dto.totalEmpleados, 0);
    });
  });
}
