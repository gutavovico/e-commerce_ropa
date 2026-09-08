import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/main.dart';

void main() {
  testWidgets('EcMobileApp smoke test and structure validation', (WidgetTester tester) async {
    await tester.pumpWidget(const EcMobileApp());

    // Verificar que la AppBar y los títulos principales existan
    expect(find.text('Ecommerce Mobile'), findsOneWidget);
    expect(find.text('Comprobación de Conectividad'), findsOneWidget);
    expect(find.text('FLUTTER + FASTAPI INTEGRATION'), findsOneWidget);

    await tester.pump();

    // Comprobar que el botón de consultar/reintentar esté presente
    expect(find.textContaining('backend'), findsWidgets);
  });
}
