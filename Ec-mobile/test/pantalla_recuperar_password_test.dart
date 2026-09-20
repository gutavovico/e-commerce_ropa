import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/datos/modelos/recuperar_password_dto.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/dominio/repositorios/recuperar_password_repositorio.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/presentacion/bloc/recuperar_password_bloc.dart';
import 'package:ec_mobile/src/modulos/autenticacion_seguridad/cu33_recuperar_acceso/presentacion/pantallas/pantalla_recuperar_password.dart';

class MockRecuperarRepositorio implements RecuperarPasswordRepositorio {
  @override
  Future<SolicitarCodigoRespuestaDto> solicitarCodigo(SolicitarCodigoPeticionDto datos) async {
    return const SolicitarCodigoRespuestaDto(mensaje: 'Código enviado', tiempoEsperaSegundos: 60);
  }

  @override
  Future<RestablecerPasswordRespuestaDto> restablecerPassword(
    RestablecerPasswordPeticionDto datos,
  ) async {
    return const RestablecerPasswordRespuestaDto(mensaje: 'Éxito', exito: true);
  }
}

void main() {
  testWidgets('PantallaRecuperarPassword renderiza paso solicitar con badge FS y campos', (tester) async {
    final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarRepositorio());

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaRecuperarPassword(bloc: bloc),
      ),
    );

    // Monograma FS y Títulos editoriales
    expect(find.text('FS'), findsOneWidget);
    expect(find.text('— RESTABLECER ACCESO —'), findsOneWidget);
    expect(find.text('FASHION STORE'), findsOneWidget);

    // Campo de correo en paso inicial
    expect(find.text('CORREO ELECTRÓNICO'), findsOneWidget);
    expect(find.byKey(const Key('recuperar_email_field')), findsOneWidget);
    expect(find.text('ENVIAR CÓDIGO →'), findsOneWidget);

    // Enlace de regreso y escudo
    expect(find.textContaining('Iniciar sesión'), findsOneWidget);
    expect(find.byIcon(Icons.shield_outlined), findsOneWidget);
  });

  testWidgets('PantallaRecuperarPassword renderiza paso restablecer con fidelidad visual a la imagen', (tester) async {
    final bloc = RecuperarPasswordBloc(repositorio: MockRecuperarRepositorio());
    bloc.setEmail('cliente@fashionstore.com');
    bloc.cambiarPaso(PasoRecuperacion.restablecer);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaRecuperarPassword(bloc: bloc),
      ),
    );

    // Rótulos de campos
    expect(find.text('CÓDIGO DE VERIFICACIÓN (6 DÍGITOS)'), findsOneWidget);
    expect(find.text('REENVIAR'), findsOneWidget);
    expect(find.byKey(const Key('recuperar_codigo_field')), findsOneWidget);

    expect(find.text('NUEVA CONTRASEÑA'), findsOneWidget);
    expect(find.byKey(const Key('recuperar_nueva_password_field')), findsOneWidget);

    expect(find.text('CONFIRMAR CONTRASEÑA'), findsOneWidget);
    expect(find.byKey(const Key('recuperar_confirmar_password_field')), findsOneWidget);

    // Botón de acción principal
    expect(find.text('ACTUALIZAR Y ACCEDER →'), findsOneWidget);

    // Probar ingreso de contraseña para verificar el medidor de fortaleza
    await tester.enterText(find.byKey(const Key('recuperar_nueva_password_field')), 'PasswordFuerte123!');
    await tester.pump();

    expect(bloc.nivelFortaleza, greaterThanOrEqualTo(2));
  });
}
