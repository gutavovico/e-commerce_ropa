import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/datos/modelos/recuperar_password_dto.dart';

void main() {
  group('SolicitarCodigoPeticionDto Tests', () {
    test('normaliza el correo eliminando espacios y convirtiendo a minúsculas', () {
      const dto = SolicitarCodigoPeticionDto(email: '  Usuario.VIP@FashionStore.com  ');
      final json = dto.toJson();
      expect(json['email'], 'usuario.vip@fashionstore.com');
    });
  });

  group('SolicitarCodigoRespuestaDto Tests', () {
    test('deserializa correctamente desde JSON', () {
      final json = {
        'mensaje': 'Código enviado con éxito',
        'tiempo_espera_segundos': 45,
      };
      final dto = SolicitarCodigoRespuestaDto.fromJson(json);
      expect(dto.mensaje, 'Código enviado con éxito');
      expect(dto.tiempoEsperaSegundos, 45);
    });

    test('usa valores por defecto ante campos ausentes', () {
      final dto = SolicitarCodigoRespuestaDto.fromJson({});
      expect(dto.mensaje, contains('código de verificación'));
      expect(dto.tiempoEsperaSegundos, 60);
    });
  });

  group('RestablecerPasswordPeticionDto Tests', () {
    test('normaliza código eliminando espacios interiores', () {
      const dto = RestablecerPasswordPeticionDto(
        email: '  Usuario@FashionStore.com ',
        codigo: ' 849 201 ',
        nuevaPassword: 'NuevaPassword123!',
        confirmarPassword: 'NuevaPassword123!',
      );
      final json = dto.toJson();
      expect(json['email'], 'usuario@fashionstore.com');
      expect(json['codigo'], '849201');
      expect(json['nueva_password'], 'NuevaPassword123!');
      expect(json['confirmar_password'], 'NuevaPassword123!');
    });
  });

  group('RestablecerPasswordRespuestaDto Tests', () {
    test('deserializa correctamente desde JSON', () {
      final json = {
        'mensaje': 'Contraseña actualizada con éxito.',
        'exito': true,
        'codigo_evento': 'PASSWORD_RESTABLECIDA',
      };
      final dto = RestablecerPasswordRespuestaDto.fromJson(json);
      expect(dto.mensaje, 'Contraseña actualizada con éxito.');
      expect(dto.exito, true);
      expect(dto.codigoEvento, 'PASSWORD_RESTABLECIDA');
    });
  });
}
