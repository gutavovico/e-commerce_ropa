import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';

void main() {
  group('LoginPeticionDto Tests', () {
    test('serializa campos correctamente a JSON', () {
      const dto = LoginPeticionDto(
        email: '  cliente.valido@fashionstore.com  ',
        password: 'PasswordSeguro123!',
        recordarDispositivo: true,
      );

      final json = dto.toJson();

      expect(json['email'], 'cliente.valido@fashionstore.com');
      expect(json['password'], 'PasswordSeguro123!');
      expect(json['recordar_dispositivo'], true);
    });

    test('usa false por defecto en recordarDispositivo', () {
      const dto = LoginPeticionDto(
        email: 'cliente@fashionstore.com',
        password: 'Password123!',
      );

      final json = dto.toJson();
      expect(json['recordar_dispositivo'], false);
    });
  });

  group('LoginRespuestaDto Tests', () {
    test('deserializa correctamente desde JSON de API FastAPI', () {
      final json = {
        'access_token': 'jwt.token.fashionstore',
        'token_type': 'bearer',
        'id_usuario': 7,
        'email': 'cliente@fashionstore.com',
        'nombres': 'Elena',
        'apellidos': 'Vance',
        'rol': 'cliente',
      };

      final dto = LoginRespuestaDto.fromJson(json);

      expect(dto.accessToken, 'jwt.token.fashionstore');
      expect(dto.tokenType, 'bearer');
      expect(dto.idUsuario, 7);
      expect(dto.email, 'cliente@fashionstore.com');
      expect(dto.nombres, 'Elena');
      expect(dto.apellidos, 'Vance');
      expect(dto.rol, 'cliente');
    });

    test('asigna valores por defecto ante campos nulos', () {
      final json = {
        'id_usuario': 1,
      };

      final dto = LoginRespuestaDto.fromJson(json);

      expect(dto.idUsuario, 1);
      expect(dto.accessToken, '');
      expect(dto.tokenType, 'bearer');
      expect(dto.rol, 'cliente');
    });
  });
}
