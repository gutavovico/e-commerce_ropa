import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/main.dart';

void main() {
  testWidgets('EcMobileApp inicia correctamente con PantallaRegistro', (WidgetTester tester) async {
    await tester.pumpWidget(const EcMobileApp());

    // Verificar presencia de la identidad de marca y elementos del Hero
    expect(find.text('FASHION STORE'), findsOneWidget);
    expect(find.text('REGISTRO PRIVADO'), findsOneWidget);
    expect(find.text('BIENVENIDO A'), findsOneWidget);

    await tester.pump();

    // Verificar campos y botón de alta costura
    expect(find.text('NOMBRE COMPLETO'), findsOneWidget);
    expect(find.text('CORREO ELECTRÓNICO'), findsOneWidget);
    expect(find.text('CONTRASEÑA'), findsOneWidget);
    expect(find.text('CREAR CUENTA EXCLUSIVA'), findsOneWidget);
    expect(find.textContaining('256-BIT SSL SECURED'), findsOneWidget);
  });
}
