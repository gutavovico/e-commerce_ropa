import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/datos/modelos/recuperar_password_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/dominio/repositorios/recuperar_password_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/presentacion/bloc/recuperar_password_bloc.dart';

class MockRecuperarPasswordRepositorioExitoso implements RecuperarPasswordRepositorio {
  @override
  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(SolicitarCodigoPeticionDto datos) async {
    return const SolicitarCodigoRespuestaDto(
      mensaje: 'Código enviado con éxito',
      tiempoEsperaSegundos: 60,
    );
  }

  @override
  Future<RestablecerPasswordRespuestaDto> restablecerPassword(
    RestablecerPasswordPeticionDto datos,
  ) async {
    return const RestablecerPasswordRespuestaDto(
      mensaje: 'Contraseña restablecida exitosamente.',
      exito: true,
    );
  }
}

class MockRecuperarPasswordRepositorioFallido implements RecuperarPasswordRepositorio {
  final String mensajeError;

  MockRecuperarPasswordRepositorioFallido([this.mensajeError = 'Código incorrecto o expirado']);

  @override
  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(SolicitarCodigoPeticionDto datos) async {
    throw Exception(mensajeError);
  }

  @override
  Future<RestablecerPasswordRespuestaDto> restablecerPassword(
    RestablecerPasswordPeticionDto datos,
  ) async {
    throw Exception(mensajeError);
  }
}

void main() {
  group('RecuperarPasswordBloc Tests', () {
    test('estado inicial es RecuperarPasswordInicial y paso solicitar', () {
      final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarPasswordRepositorioExitoso());
      expect(bloc.estado, isA<RecuperarPasswordInicial>());
      expect(bloc.pasoActual, PasoRecuperacion.solicitar);
      expect(bloc.segundosCooldown, 0);
      expect(bloc.nivelFortaleza, 0);
    });

    test('solicitarCodigo emite Cargando y CodigoSolicitadoExitoso, y cambia a restablecer', () async {
      final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarPasswordRepositorioExitoso());
      final estados = <RecuperarPasswordEstado>[];

      bloc.addListener(() {
        estados.add(bloc.estado);
      });

      await bloc.solicitarCodigo('cliente@fashionstore.com');

      expect(estados.length, 2);
      expect(estados[0], isA<RecuperarPasswordCargando>());
      expect(estados[1], isA<CodigoSolicitadoExitoso>());
      expect(bloc.pasoActual, PasoRecuperacion.restablecer);
      expect(bloc.email, 'cliente@fashionstore.com');
      expect(bloc.segundosCooldown, 60);

      bloc.dispose();
    });

    test('solicitarCodigo con email vacío emite RecuperarPasswordError', () async {
      final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarPasswordRepositorioExitoso());
      await bloc.solicitarCodigo('');

      expect(bloc.estado, isA<RecuperarPasswordError>());
      final error = bloc.estado as RecuperarPasswordError;
      expect(error.mensaje, contains('correo'));

      bloc.dispose();
    });

    test('restablecerPassword valida longitud de código, contraseña y coincidencia', () async {
      final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarPasswordRepositorioExitoso());
      bloc.setEmail('cliente@fashionstore.com');

      // 1. Código de menos de 6 dígitos
      await bloc.restablecerPassword(
        codigo: '123',
        nuevaPassword: 'Password123!',
        confirmarPassword: 'Password123!',
      );
      expect(bloc.estado, isA<RecuperarPasswordError>());
      expect((bloc.estado as RecuperarPasswordError).mensaje, contains('6 dígitos'));

      // 2. Contraseña menor a 8 caracteres
      await bloc.restablecerPassword(
        codigo: '123456',
        nuevaPassword: 'corta',
        confirmarPassword: 'corta',
      );
      expect(bloc.estado, isA<RecuperarPasswordError>());
      expect((bloc.estado as RecuperarPasswordError).mensaje, contains('8 caracteres'));

      // 3. Contraseñas no coincidentes
      await bloc.restablecerPassword(
        codigo: '123456',
        nuevaPassword: 'Password123!',
        confirmarPassword: 'OtraPassword123!',
      );
      expect(bloc.estado, isA<RecuperarPasswordError>());
      expect((bloc.estado as RecuperarPasswordError).mensaje, contains('coinciden'));

      // 4. Datos válidos emite RestablecimientoExitoso
      await bloc.restablecerPassword(
        codigo: '123456',
        nuevaPassword: 'PasswordSegura123!',
        confirmarPassword: 'PasswordSegura123!',
      );
      expect(bloc.estado, isA<RestablecimientoExitoso>());

      bloc.dispose();
    });

    test('actualizarFortalezaPassword calcula correctamente niveles 0 a 3', () {
      final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarPasswordRepositorioExitoso());

      bloc.actualizarFortalezaPassword('');
      expect(bloc.nivelFortaleza, 0);

      bloc.actualizarFortalezaPassword('12345678');
      expect(bloc.nivelFortaleza, 1);

      bloc.actualizarFortalezaPassword('Abcdefg1');
      expect(bloc.nivelFortaleza, 2);

      bloc.actualizarFortalezaPassword('Abcdefg123!@#');
      expect(bloc.nivelFortaleza, 3);

      bloc.dispose();
    });
  });
}
