import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/datos/datasources/colecciones_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/datos/modelos/coleccion_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/bloc/colecciones_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/colecciones_screen.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/pantallas/detalle_coleccion_screen.dart';

class MockColeccionesApiWidgets implements ColeccionesApi {
  final ColeccionesActivasResponseDto mockActivas =
      const ColeccionesActivasResponseDto(
    temporadaActivaId: 1,
    temporadaActivaNombre: 'Otoño / Invierno 2024',
    totalColecciones: 2,
    coleccionDestacada: ColeccionResumenDto(
      idColeccion: 1,
      nombre: 'Sastrería en Lana Virgen & Seda Natural',
      descripcion:
          'Líneas puras y patronaje contemporáneo confeccionado en Biella y Lyon.',
      temporadaNombre: 'Otoño / Invierno 2024',
      temporadaTipo: 'otoño_invierno',
      tallerOrigen: 'Molinos de Biella & Lyon',
      precioDesde: 310.0,
      totalPrendas: 4,
      esDestacada: true,
      badgeEdicion: 'EDICIÓN Nº 07 ATELIER',
      imagenPortada: null,
      piezasClave: [
        ProductoColeccionItemDto(
          idProducto: 1,
          nombre: 'Vestido plisado seda',
          descripcion: 'Vestido en seda pura rojo carmín.',
          precioBase: 890.0,
          imagenUrl: null,
          badgeEditorial: 'EDICIÓN LIMITADA',
          subtituloTextil: 'SEDA LYON · ALTA COSTURA',
          categoria: 'Vestidos',
          coloresDisponibles: ['#991B1B'],
          stockTotalDisponible: 15,
          tieneStock: true,
        ),
      ],
    ),
    otrasColecciones: [
      ColeccionResumenDto(
        idColeccion: 2,
        nombre: 'Edición Milano: Punto & Lino',
        descripcion: 'Hilaturas fluidas de lino y punto fino.',
        temporadaNombre: 'Primavera / Verano 2024',
        temporadaTipo: 'primavera_verano',
        tallerOrigen: 'Molinos de Biella & Como',
        precioDesde: 340.0,
        totalPrendas: 6,
        esDestacada: false,
        badgeEdicion: 'EDICIÓN SS24 MILANO',
        imagenPortada: null,
        piezasClave: [],
      ),
    ],
  );

  final ColeccionDetalleDto mockDetalle = const ColeccionDetalleDto(
    idColeccion: 2,
    nombre: 'Edición Milano: Punto & Lino',
    descripcion: 'Hilaturas fluidas de lino y punto fino.',
    temporadaNombre: 'Primavera / Verano 2024',
    tallerOrigen: 'Molinos de Biella & Como',
    totalPrendas: 1,
    mensajeEmptyState: null,
    productos: [
      ProductoColeccionItemDto(
        idProducto: 10,
        nombre: 'Camisa Lino Italiano',
        precioBase: 340.0,
        badgeEditorial: 'ALTA COSTURA',
        subtituloTextil: 'LINO COMO',
        categoria: 'Camisas',
        stockTotalDisponible: 12,
        tieneStock: true,
      ),
    ],
  );

  @override
  Future<ColeccionesActivasResponseDto> obtenerColeccionesActivas({
    int limitePiezasClave = 4,
  }) async {
    return mockActivas;
  }

  @override
  Future<ColeccionDetalleDto> obtenerPrendasDeColeccion(int idColeccion) async {
    return mockDetalle;
  }
}

void main() {
  group('CU36 Mobile Widget Tests', () {
    testWidgets(
        'ColeccionesScreen renderiza AppBar, título, chips y secciones',
        (tester) async {
      tester.view.physicalSize = const Size(390 * 2, 844 * 2);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      final api = MockColeccionesApiWidgets();
      final bloc = ColeccionesBloc(api: api);

      await tester.pumpWidget(
        MaterialApp(
          home: ColeccionesScreen(bloc: bloc),
        ),
      );

      // Esperar carga inicial
      await tester.pumpAndSettle();

      // Verificar AppBar
      expect(find.text('FASHION STORE'), findsOneWidget);

      // Verificar H1 Colecciones (pantalla secundaria sin BottomNavigationBar)
      expect(find.text('Colecciones'), findsOneWidget);

      // Verificar Chips
      expect(find.text('COLECCIÓN DESTACADA'), findsOneWidget);
      expect(find.text('ORIGEN CERTIFICADO'), findsOneWidget);
      expect(find.text('ENVÍO ATELIER'), findsOneWidget);

      // Verificar Colección Destacada
      expect(find.text('Sastrería en Lana Virgen & Seda Natural'),
          findsOneWidget);
      expect(find.text('EDICIÓN Nº 07 ATELIER'), findsOneWidget);
      expect(find.text('Vestido plisado seda'), findsOneWidget);
      expect(find.text('890 €'), findsOneWidget);
      expect(find.text('VER COLECCIÓN COMPLETA'), findsOneWidget);

      // Verificar Otras colecciones
      expect(find.text('Otras colecciones'), findsOneWidget);
      expect(find.text('Edición Milano: Punto & Lino'), findsOneWidget);
      expect(find.text('VER COLECCIÓN'), findsOneWidget);
    });

    testWidgets('Pulsar en un chip de filtro actualiza el chip activo',
        (tester) async {
      tester.view.physicalSize = const Size(390 * 2, 844 * 2);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      final api = MockColeccionesApiWidgets();
      final bloc = ColeccionesBloc(api: api);

      await tester.pumpWidget(
        MaterialApp(
          home: ColeccionesScreen(bloc: bloc),
        ),
      );

      await tester.pumpAndSettle();

      // Pulsar en chip 'ORIGEN CERTIFICADO'
      await tester.ensureVisible(find.text('ORIGEN CERTIFICADO'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('ORIGEN CERTIFICADO'));
      await tester.pumpAndSettle();

      expect(bloc.chipSeleccionado, equals('ORIGEN CERTIFICADO'));
    });

    testWidgets(
        'Pulsar en una tarjeta de otra colección navega a DetalleColeccionScreen',
        (tester) async {
      tester.view.physicalSize = const Size(390 * 2, 844 * 2);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      final api = MockColeccionesApiWidgets();
      final bloc = ColeccionesBloc(api: api);

      await tester.pumpWidget(
        MaterialApp(
          home: ColeccionesScreen(bloc: bloc),
        ),
      );

      await tester.pumpAndSettle();

      // Desplazarse verticalmente para visualizar la sección Otras colecciones
      await tester.drag(find.byType(ColeccionesScreen), const Offset(0, -600));
      await tester.pumpAndSettle();

      // Pulsar en tarjeta o texto de "VER COLECCIÓN"
      await tester.tap(find.text('VER COLECCIÓN'));
      await tester.pumpAndSettle();

      // Debe estar en DetalleColeccionScreen
      expect(find.byType(DetalleColeccionScreen), findsOneWidget);
      expect(find.text('Camisa Lino Italiano'), findsOneWidget);
      expect(find.text('340 €'), findsOneWidget);
    });

    testWidgets('DetalleColeccionScreen renderiza prendas y toggle de bookmark',
        (tester) async {
      tester.view.physicalSize = const Size(390 * 2, 844 * 2);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      final api = MockColeccionesApiWidgets();
      final bloc = ColeccionesBloc(api: api);

      await tester.pumpWidget(
        MaterialApp(
          home: DetalleColeccionScreen(
            idColeccion: 2,
            nombreColeccionInicial: 'Edición Milano: Punto & Lino',
            bloc: bloc,
          ),
        ),
      );

      await tester.pumpAndSettle();

      expect(find.text('Edición Milano: Punto & Lino'), findsOneWidget);
      expect(find.text('Molinos de Biella & Como'), findsOneWidget);
      expect(find.text('PIEZAS DE ALTA COSTURA (1)'), findsOneWidget);
      expect(find.text('Camisa Lino Italiano'), findsOneWidget);

      // Probar bookmark
      expect(bloc.esBookmark(10), isFalse);
      await tester.tap(find.byIcon(Icons.bookmark_border));
      await tester.pumpAndSettle();
      expect(bloc.esBookmark(10), isTrue);
    });
  });
}
