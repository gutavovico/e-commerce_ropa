import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu04_gestionar_perfil/datos/modelos/perfil_dto.dart';

void main() {
  group('ResumenAtelierDto Tests', () {
    test('deserializa correctamente desde JSON', () {
      final json = {
        'visitas_registradas': 32,
        'boutiques_visitadas': 4,
        'preferencia_textil': '100% Seda & Lana',
        'estatus_membresia': 'Nivel Platino',
      };

      final dto = ResumenAtelierDto.fromJson(json);

      expect(dto.visitasRegistradas, 32);
      expect(dto.boutiquesVisitadas, 4);
      expect(dto.preferenciaTextil, '100% Seda & Lana');
      expect(dto.estatusMembresia, 'Nivel Platino');
    });

    test('aplica valores por defecto ante campos nulos', () {
      final dto = ResumenAtelierDto.fromJson(const {});

      expect(dto.visitasRegistradas, 32);
      expect(dto.boutiquesVisitadas, 4);
      expect(dto.preferenciaTextil, '100% Seda & Lana');
      expect(dto.estatusMembresia, 'Nivel Platino');
    });
  });

  group('PerfilClienteDto Tests', () {
    test('deserializa correctamente desde JSON de API FastAPI', () {
      final json = {
        'id_usuario': 8402,
        'numero_socio': '#8402',
        'email': 'ana.valenzuela@studio.es',
        'rol': 'cliente',
        'fecha_registro': '2021-10-15T12:00:00Z',
        'miembro_desde': 'Octubre 2021',
        'nombres': 'Ana',
        'apellidos': 'Valenzuela',
        'telefono': '+34 612 884 901',
        'talla_preferida': '38',
        'genero': 'femenino',
        'acepta_marketing': true,
        'resumen_atelier': {
          'visitas_registradas': 32,
          'boutiques_visitadas': 4,
          'preferencia_textil': '100% Seda & Lana',
          'estatus_membresia': 'Nivel Platino',
        },
      };

      final dto = PerfilClienteDto.fromJson(json);

      expect(dto.idUsuario, 8402);
      expect(dto.numeroSocio, '#8402');
      expect(dto.email, 'ana.valenzuela@studio.es');
      expect(dto.nombres, 'Ana');
      expect(dto.apellidos, 'Valenzuela');
      expect(dto.tallaPreferida, '38');
      expect(dto.aceptaMarketing, isTrue);
      expect(dto.resumenAtelier.boutiquesVisitadas, 4);
    });
  });

  group('PerfilClienteUpdateDto Tests', () {
    test('serializa solo campos no nulos a JSON', () {
      const dto = PerfilClienteUpdateDto(
        nombres: 'Camille',
        tallaPreferida: 'M',
        aceptaMarketing: false,
      );

      final json = dto.toJson();

      expect(json['nombres'], 'Camille');
      expect(json['talla_preferida'], 'M');
      expect(json['acepta_marketing'], isFalse);
      expect(json.containsKey('apellidos'), isFalse);
      expect(json.containsKey('telefono'), isFalse);
    });
  });

  group('HistorialComprasMovilDto Tests (CU17)', () {
    test('deserializa respuesta de GET /api/v1/ventas/mias con items', () {
      final json = {
        'total_pedidos': 1,
        'pedidos_completados': 1,
        'pedidos': [
          {
            'id_venta': 42,
            'numero_comprobante': 'FS-2026-000042',
            'fecha_venta': '2026-04-11T15:30:00Z',
            'tipo_venta': 'digital_movil',
            'estado': 'pagada',
            'tipo_entrega': 'domicilio',
            'nombre_sucursal': 'Boutique Equipetrol',
            'subtotal': '890.00',
            'descuento': '0.00',
            'total': '890.00',
            'metodo_pago': 'tarjeta_credito',
            'referencia_pasarela': 'pi_test_42',
            'items': [
              {
                'id_venta_detalle': 101,
                'id_producto': 7,
                'id_variante': 19,
                'sku': 'FS-ABR-007-M-NEG',
                'nombre_producto': 'Abrigo de Lana Merino',
                'talla': 'M',
                'color': 'Negro',
                'cantidad': 1,
                'precio_unitario': '890.00',
                'subtotal_linea': '890.00',
              },
            ],
          },
        ],
      };

      final dto = HistorialComprasMovilDto.fromJson(json);

      expect(dto.totalPedidos, 1);
      expect(dto.pedidosCompletados, 1);
      expect(dto.pedidos.length, 1);
      expect(dto.pedidos.first.numeroComprobante, 'FS-2026-000042');
      expect(dto.pedidos.first.items.first.nombreProducto, 'Abrigo de Lana Merino');
    });
  });
}
