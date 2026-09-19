import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/datos/modelos/login_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/dominio/repositorios/login_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/bloc/login_bloc.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu02_iniciar_sesion/presentacion/pantallas/pantalla_login.dart';

class MockLoginRepositorio implements LoginRepositorio {
  @override
  Future<LoginRespuestaDto> autenticarUsuario(LoginPeticionDto datos) async {
    return const LoginRespuestaDto(
      accessToken: 'token-test',
      tokenType: 'bearer',
      idUsuario: 1,
      email: 'test@fashionstore.com',
      nombres: 'Ana',
      apellidos: 'Garcia',
      rol: 'cliente',
    );
  }
}

void main() {
  Widget crearAppDePrueba(LoginBloc bloc) {
    return MaterialApp(
      home: PantallaLogin(bloc: bloc),
    );
  }

  group('PantallaLogin Widget Tests', () {
    testWidgets('renderiza elementos visuales clave de Fashion Store', (tester) async {
      final bloc = LoginBloc(repositorio: MockLoginRepositorio());
      await tester.pumpWidget(crearAppDePrueba(bloc));
      await tester.pumpAndSettle();

      // Verificar badge superior FS
      expect(find.text('FS'), findsOneWidget);

      // Verificar título de marca y subtítulo
      expect(find.text('— BIENVENIDO DE VUELTA —'), findsOneWidget);
      expect(find.text('FASHION STORE'), findsOneWidget);

      // Verificar etiquetas de formulario
      expect(find.text('CORREO ELECTRÓNICO'), findsOneWidget);
      expect(find.text('CONTRASEÑA'), findsOneWidget);
      expect(find.text('¿Olvidaste tu contraseña?'), findsOneWidget);

      // Verificar botón de submit
      expect(find.text('INICIAR SESIÓN'), findsOneWidget);

      // Verificar texto de pie de registro
      expect(find.text('¿Aún no tienes una cuenta exclusiva?'), findsOneWidget);
      expect(find.text('Regístrate aquí'), findsOneWidget);

      // Verificar insignia de seguridad
      expect(find.text('CONEXIÓN CIFRADA & PRIVACIDAD MAISON'), findsOneWidget);
    });

    testWidgets('alterna visibilidad de contraseña al presionar el icono de ojo', (tester) async {
      final bloc = LoginBloc(repositorio: MockLoginRepositorio());
      await tester.pumpWidget(crearAppDePrueba(bloc));
      await tester.pumpAndSettle();

      final botonOjo = find.byKey(const Key('login_toggle_password_button'));
      expect(botonOjo, findsOneWidget);

      // Verificar que inicialmente el campo está oculto (obscureText = true)
      final passwordFieldFinder = find.byKey(const Key('login_password_field'));
      TextField passwordWidget = tester.widget<TextField>(
        find.descendant(of: passwordFieldFinder, matching: find.byType(TextField)),
      );
      expect(passwordWidget.obscureText, true);

      // Hacer tap en el botón de ojo
      await tester.tap(botonOjo);
      await tester.pumpAndSettle();

      // Verificar que ahora se muestra en texto plano (obscureText = false)
      passwordWidget = tester.widget<TextField>(
        find.descendant(of: passwordFieldFinder, matching: find.byType(TextField)),
      );
      expect(passwordWidget.obscureText, false);
    });

    testWidgets('valida campos vacios al presionar enviar sin datos', (tester) async {
      final bloc = LoginBloc(repositorio: MockLoginRepositorio());
      await tester.pumpWidget(crearAppDePrueba(bloc));
      await tester.pumpAndSettle();

      final botonSubmit = find.byKey(const Key('login_submit_button'));
      await tester.tap(botonSubmit);
      await tester.pumpAndSettle();

      // Deberían mostrarse los mensajes de validación
      expect(find.text('Por favor ingresa tu correo electrónico'), findsOneWidget);
      expect(find.text('Por favor ingresa tu contraseña'), findsOneWidget);
    });
  });
}
