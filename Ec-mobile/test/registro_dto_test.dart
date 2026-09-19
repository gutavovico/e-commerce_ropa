import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu01_registrarse/datos/modelos/registro_dto.dart';

void main() {
  group('RegistroClienteDto Tests', () {
    test('serializa campos obligatorios y opcionales correctamente a JSON', () {
      const dto = RegistroClienteDto(
        email: 'cliente@fashionstore.com',
        password: 'PasswordSeguro123!',
        nombres: 'Ana María',
        apellidos: 'García Morales',
        telefono: '+591 70012345',
        tallaPreferida: 'm',
      );

      final json = dto.toJson();

      expect(json['email'], 'cliente@fashionstore.com');
      expect(json['password'], 'PasswordSeguro123!');
      expect(json['nombres'], 'Ana María');
      expect(json['apellidos'], 'García Morales');
      expect(json['telefono'], '+591 70012345');
      expect(json['talla_preferida'], 'M');
      expect(json.containsKey('ciudad_preferida'), isFalse);
    });

    test('omite campos opcionales vacíos o nulos', () {
      const dto = RegistroClienteDto(
        email: 'cliente2@fashionstore.com',
        password: 'PasswordSeguro123!',
        nombres: 'Carlos',
        apellidos: 'Pérez',
      );

      final json = dto.toJson();

      expect(json.containsKey('telefono'), isFalse);
      expect(json.containsKey('talla_preferida'), isFalse);
      expect(json.containsKey('ciudad_preferida'), isFalse);
    });
  });

  group('RegistroRespuestaDto Tests', () {
    test('deserializa correctamente desde JSON de API FastAPI', () {
      final json = {
        'id_usuario': 42,
        'email': 'cliente@fashionstore.com',
        'nombres': 'Ana María',
        'apellidos': 'García Morales',
        'rol': 'cliente',
        'token_acceso': 'jwt_fake_token_123',
        'tipo_token': 'bearer',
      };

      final dto = RegistroRespuestaDto.fromJson(json);

      expect(dto.idUsuario, 42);
      expect(dto.email, 'cliente@fashionstore.com');
      expect(dto.nombres, 'Ana María');
      expect(dto.apellidos, 'García Morales');
      expect(dto.rol, 'cliente');
      expect(dto.tokenAcceso, 'jwt_fake_token_123');
      expect(dto.tipoToken, 'bearer');
    });
  });
}
