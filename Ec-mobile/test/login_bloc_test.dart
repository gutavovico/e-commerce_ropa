import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/bloc/login_bloc.dart';

class MockLoginRepositorioExitoso implements LoginRepositorio {
  @override
  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto datos) async {
    return const LoginRespuestaDto(
      accessToken: 'token-jwt-mock',
      tokenType: 'bearer',
      idUsuario: 12,
      email: 'usuario@fashionstore.com',
      nombres: 'Test',
      apellidos: 'User',
      rol: 'cliente',
    );
  }
}

class MockLoginRepositorioFallido implements LoginRepositorio {
  final String mensajeError;

  MockLoginRepositorioFallido([this.mensajeError = 'Credenciales incorrectas']);

  @override
  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto datos) async {
    throw Exception(mensajeError);
  }
}

void main() {
  group('LoginBloc Tests', () {
    test('estado inicial es LoginInicial', () {
      final bloc = LoginBloc(repositorio: MockLoginRepositorioExitoso());
      expect(bloc.estado, isA<LoginInicial>());
      expect(bloc.estaCargando, false);
    });

    test('iniciarSesion emite LoginCargando y luego LoginExitoso ante credenciales validas', () async {
      final bloc = LoginBloc(repositorio: MockLoginRepositorioExitoso());
      const peticion = LoginPeticionDto(
        email: 'usuario@fashionstore.com',
        password: 'Password123!',
      );

      final estados = <LoginEstado>[];
      bloc.addListener(() {
        estados.add(bloc.estado);
      });

      await bloc.iniciarSesion(peticion);

      expect(estados.length, 2);
      expect(estados[0], isA<LoginCargando>());
      expect(estados[1], isA<LoginExitoso>());

      final estadoExitoso = estados[1] as LoginExitoso;
      expect(estadoExitoso.respuesta.idUsuario, 12);
      expect(estadoExitoso.respuesta.accessToken, 'token-jwt-mock');
    });

    test('iniciarSesion emite LoginCargando y luego LoginFallido ante error', () async {
      final bloc = LoginBloc(
        repositorio: MockLoginRepositorioFallido('Credenciales incorrectas'),
      );
      const peticion = LoginPeticionDto(
        email: 'usuario@fashionstore.com',
        password: 'PasswordIncorrecta!',
      );

      final estados = <LoginEstado>[];
      bloc.addListener(() {
        estados.add(bloc.estado);
      });

      await bloc.iniciarSesion(peticion);

      expect(estados.length, 2);
      expect(estados[0], isA<LoginCargando>());
      expect(estados[1], isA<LoginFallido>());

      final estadoFallido = estados[1] as LoginFallido;
      expect(estadoFallido.mensaje, contains('Credenciales incorrectas'));
    });

    test('reiniciar restablece el estado a LoginInicial', () async {
      final bloc = LoginBloc(repositorio: MockLoginRepositorioExitoso());
      const peticion = LoginPeticionDto(
        email: 'usuario@fashionstore.com',
        password: 'Password123!',
      );

      await bloc.iniciarSesion(peticion);
      expect(bloc.estado, isA<LoginExitoso>());

      bloc.reiniciar();
      expect(bloc.estado, isA<LoginInicial>());
    });
  });
}
