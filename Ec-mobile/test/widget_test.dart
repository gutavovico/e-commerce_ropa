import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/main.dart';

void main() {
  testWidgets('EcMobileApp inicia correctamente con PantallaLogin como pantalla principal', (WidgetTester tester) async {
    await tester.pumpWidget(const EcMobileApp());

    // Verificar presencia de la identidad de marca de Login
    expect(find.text('FASHION STORE'), findsOneWidget);
    expect(find.text('— BIENVENIDO DE VUELTA —'), findsOneWidget);
    expect(find.text('FS'), findsOneWidget);

    await tester.pump();

    // Verificar campos de credenciales y acciones principales
    expect(find.text('CORREO ELECTRÓNICO'), findsOneWidget);
    expect(find.text('CONTRASEÑA'), findsOneWidget);
    expect(find.text('INICIAR SESIÓN'), findsOneWidget);
    expect(find.text('Recordar en este dispositivo'), findsOneWidget);
    expect(find.text('Regístrate aquí'), findsOneWidget);
    expect(find.textContaining('CONEXIÓN CIFRADA & PRIVACIDAD MAISON'), findsOneWidget);
  });

  testWidgets('EcMobileApp navega de PantallaLogin a PantallaRegistro y regresa', (WidgetTester tester) async {
    // Configurar viewport cómodo para la prueba
    tester.view.physicalSize = const Size(800, 1200);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() => tester.view.resetPhysicalSize());

    await tester.pumpWidget(const EcMobileApp());
    await tester.pump();

    // Tocar "Regístrate aquí"
    final enlaceRegistro = find.byKey(const Key('login_register_link'));
    expect(enlaceRegistro, findsOneWidget);
    await tester.ensureVisible(enlaceRegistro);
    await tester.tap(enlaceRegistro);
    await tester.pumpAndSettle();

    // Verificar que estamos en PantallaRegistro
    expect(find.text('CREAR CUENTA EXCLUSIVA'), findsOneWidget);
    expect(find.text('NOMBRE COMPLETO'), findsOneWidget);

    // Tocar "¿Ya posees una cuenta? Iniciar sesión"
    final enlaceLogin = find.textContaining('Iniciar sesión');
    expect(enlaceLogin, findsOneWidget);
    await tester.ensureVisible(enlaceLogin);
    await tester.tap(enlaceLogin);
    await tester.pumpAndSettle();

    // Verificar que regresó a PantallaLogin
    expect(find.text('INICIAR SESIÓN'), findsOneWidget);
    expect(find.text('— BIENVENIDO DE VUELTA —'), findsOneWidget);
  });
}
