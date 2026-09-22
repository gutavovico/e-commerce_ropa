import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/navegacion/pantalla_principal_hub.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart';

void main() {
  group('PantallaPrincipalHub Navigation Tests (Hub-and-Spoke)', () {
    testWidgets('renderiza las 4 pestañas y saluda con el nombre dinámico del usuario', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: PantallaPrincipalHub(
            token: 'test_token_123',
            nombreUsuario: 'Joaquinita Chumacero',
            habilitarImagenesRed: false,
          ),
        ),
      );
      await tester.pumpAndSettle();

      // 1. Verificar BottomNavigationBar con exactamente las 4 pestañas
      expect(find.byType(BottomNavigationBar), findsOneWidget);
      expect(find.text('Inicio'), findsOneWidget);
      expect(find.text('Buscar'), findsOneWidget);
      expect(find.text('Catálogo'), findsOneWidget);
      expect(find.text('Perfil'), findsOneWidget);

      // 2. Verificar que en la pestaña Inicio se visualiza el saludo con el nombre dinámico
      expect(find.text('BIENVENIDA DE NUEVO'), findsOneWidget);
      expect(find.text('Joaquinita Chumacero'), findsOneWidget);
    });

    testWidgets('permite navegar bidireccionalmente entre Inicio, Buscar, Catálogo y Perfil sin duplicar rutas', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: PantallaPrincipalHub(
            token: 'test_token_123',
            nombreUsuario: 'Joaquinita Chumacero',
            habilitarImagenesRed: false,
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Inicialmente en Inicio (índice 0)
      final indexedStackFinder = find.byType(IndexedStack);
      expect(indexedStackFinder, findsOneWidget);
      final stackWidget = tester.widget<IndexedStack>(indexedStackFinder);
      expect(stackWidget.index, 0);

      // Transición a BUSCAR (índice 1)
      await tester.tap(find.text('Buscar'));
      await tester.pumpAndSettle();
      final stackBuscar = tester.widget<IndexedStack>(indexedStackFinder);
      expect(stackBuscar.index, 1);

      // Transición a CATÁLOGO (índice 2)
      await tester.tap(find.text('Catálogo'));
      await tester.pumpAndSettle();
      final stackCatalogo = tester.widget<IndexedStack>(indexedStackFinder);
      expect(stackCatalogo.index, 2);
      expect(find.byType(PantallaCatalogo), findsOneWidget);

      // Transición a PERFIL (índice 3)
      await tester.tap(find.text('Perfil'));
      await tester.pumpAndSettle();
      final stackPerfil = tester.widget<IndexedStack>(indexedStackFinder);
      expect(stackPerfil.index, 3);
      expect(find.text('Mi Cuenta'), findsOneWidget);

      // Retorno a INICIO (índice 0) desde Perfil
      await tester.tap(find.text('Inicio'));
      await tester.pumpAndSettle();
      final stackRetornoInicio = tester.widget<IndexedStack>(indexedStackFinder);
      expect(stackRetornoInicio.index, 0);
      expect(find.text('Joaquinita Chumacero'), findsOneWidget);
    });
  });
}
