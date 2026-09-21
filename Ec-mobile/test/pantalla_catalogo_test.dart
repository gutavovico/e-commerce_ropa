import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu05_consultar_catalogo/datos/datasources/catalogo_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu05_consultar_catalogo/datos/modelos/catalogo_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/bloc/catalogo_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu05_consultar_catalogo/presentacion/pantallas/pantalla_catalogo.dart';

class MockCatalogoApi implements CatalogoApi {
  final CatalogoResponseDto mockResponse;
  final CatalogoResponseDto? mockEmptyResponse;
  bool shouldThrow;

  MockCatalogoApi({
    CatalogoResponseDto? mockResponse,
    this.mockEmptyResponse,
    this.shouldThrow = false,
  }) : mockResponse = mockResponse ?? _crearRespuestaPorDefecto();

  static CatalogoResponseDto _crearRespuestaPorDefecto() {
    return const CatalogoResponseDto(
      resumenCategorias: [
        CategoriaResumenDto(idCategoria: 1, nombre: 'Chaquetas', totalPrendas: 7),
        CategoriaResumenDto(idCategoria: 2, nombre: 'Vestidos', totalPrendas: 3),
      ],
      totalArticulos: 2,
      paginaActual: 1,
      limite: 6,
      totalPaginas: 1,
      tieneSiguiente: false,
      tieneAnterior: false,
      items: [
        ProductoCatalogoItemDto(
          idProducto: 101,
          nombre: 'Blazer estructurado en lana virgen',
          precioBase: 740.0,
          precioFinal: 740.0,
          tieneDescuento: false,
          categoriaId: 1,
          categoriaNombre: 'Chaquetas',
          subtituloAtelier: 'SASTRERÍA ATELIER',
          etiquetaBadge: 'EDICIÓN LIMITADA',
          tallasDisponibles: ['36', '38'],
          coloresDisponibles: [
            ColorItemDto(idColor: 1, nombre: 'Camel', codigoHex: '#C2A688'),
          ],
          stockTotalDisponible: 12,
          tieneStock: true,
        ),
        ProductoCatalogoItemDto(
          idProducto: 102,
          nombre: 'Vestido largo en satén de seda',
          precioBase: 890.0,
          precioFinal: 712.0,
          tieneDescuento: true,
          porcentajeDescuento: 20,
          categoriaId: 2,
          categoriaNombre: 'Vestidos',
          subtituloAtelier: 'ALTA COSTURA',
          etiquetaBadge: '-20% ATELIER',
          tallasDisponibles: ['38'],
          coloresDisponibles: [
            ColorItemDto(idColor: 2, nombre: 'Marfil', codigoHex: '#FCFBF8'),
          ],
          stockTotalDisponible: 5,
          tieneStock: true,
        ),
      ],
    );
  }

  @override
  Future<CatalogoResponseDto> consultarCatalogo({
    int? categoriaId,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 6,
  }) async {
    if (shouldThrow) {
      throw const CatalogoException('Error simulado de red');
    }

    if (categoriaId == 99 && mockEmptyResponse != null) {
      return mockEmptyResponse!;
    }

    return mockResponse;
  }
}

void main() {
  group('CatalogoGeneralBloc Unit Tests', () {
    test('Estado inicial debe ser CatalogoGeneralInicial', () {
      final bloc = CatalogoGeneralBloc(api: MockCatalogoApi());
      expect(bloc.estado, isA<CatalogoGeneralInicial>());
    });

    test('cargarCatalogo transiciona a CatalogoGeneralCargado con items y resumen', () async {
      final bloc = CatalogoGeneralBloc(api: MockCatalogoApi());
      await bloc.cargarCatalogo();

      expect(bloc.estado, isA<CatalogoGeneralCargado>());
      final cargado = bloc.estado as CatalogoGeneralCargado;
      expect(cargado.totalArticulos, equals(2));
      expect(cargado.productosAcumulados.length, equals(2));
      expect(cargado.resumenCategorias.length, equals(2));
      expect(cargado.totalGlobalPrendas, equals(10));
    });

    test('toggleFavorito agrega y elimina ids del conjunto de favoritos', () async {
      final bloc = CatalogoGeneralBloc(api: MockCatalogoApi());
      await bloc.cargarCatalogo();

      bloc.toggleFavorito(101);
      expect(bloc.favoritos.contains(101), isTrue);

      bloc.toggleFavorito(101);
      expect(bloc.favoritos.contains(101), isFalse);
    });

    test('cambiarModoColumnas actualiza modoColumnas a 1 y 2', () async {
      final bloc = CatalogoGeneralBloc(api: MockCatalogoApi());
      await bloc.cargarCatalogo();

      bloc.cambiarModoColumnas(1);
      expect(bloc.modoColumnas, equals(1));

      bloc.cambiarModoColumnas(2);
      expect(bloc.modoColumnas, equals(2));
    });

    test('Respuesta vacía transiciona a CatalogoGeneralVacio', () async {
      final emptyApi = MockCatalogoApi(
        mockEmptyResponse: const CatalogoResponseDto(
          resumenCategorias: [],
          totalArticulos: 0,
          paginaActual: 1,
          limite: 6,
          totalPaginas: 0,
          tieneSiguiente: false,
          tieneAnterior: false,
          items: [],
        ),
      );

      final bloc = CatalogoGeneralBloc(api: emptyApi);
      await bloc.cargarCatalogo(categoriaId: 99);

      expect(bloc.estado, isA<CatalogoGeneralVacio>());
    });

    test('Fallo de API transiciona a CatalogoGeneralError', () async {
      final failApi = MockCatalogoApi(shouldThrow: true);
      final bloc = CatalogoGeneralBloc(api: failApi);
      await bloc.cargarCatalogo();

      expect(bloc.estado, isA<CatalogoGeneralError>());
    });
  });

  group('PantallaCatalogo Widget Tests', () {
    testWidgets('debe renderizar cabecera, chips de categorías y prendas sin botón volver',
        (tester) async {
      final mockApi = MockCatalogoApi();
      final bloc = CatalogoGeneralBloc(api: mockApi);

      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        MaterialApp(
          home: PantallaCatalogo(
            bloc: bloc,
            habilitarImagenesRed: false,
          ),
        ),
      );

      // Esperar a que el Future de postFrameCallback resuelva
      await tester.pumpAndSettle();

      // 1. Verificar títulos
      expect(find.text('FASHION STORE'), findsOneWidget);
      expect(find.text('Catálogo de Prendas'), findsOneWidget);

      // 2. Verificar que NO haya botón BackButton (Directriz Hub-and-Spoke)
      expect(find.byType(BackButton), findsNothing);

      // 3. Verificar chips de categoría
      expect(find.text('Todos (10)'), findsOneWidget);
      expect(find.text('Chaquetas (7)'), findsOneWidget);
      expect(find.text('Vestidos (3)'), findsOneWidget);

      // 4. Verificar prendas renderizadas en la cuadrícula
      expect(find.text('Blazer estructurado en lana virgen'), findsOneWidget);
      expect(find.text('Vestido largo en satén de seda'), findsOneWidget);
      expect(find.text('SASTRERÍA ATELIER'), findsOneWidget);
      expect(find.text('ALTA COSTURA'), findsOneWidget);

      // 5. Verificar precios
      expect(find.text('740 €'), findsOneWidget);
      expect(find.text('712 €'), findsOneWidget);

      // 6. Verificar sello editorial inferior
      expect(find.text('ATELIER FLAGSHIP MADRID · PARÍS'), findsOneWidget);
    });

    testWidgets('debe permitir interactuar con el botón de wishlist',
        (tester) async {
      final mockApi = MockCatalogoApi();
      final bloc = CatalogoGeneralBloc(api: mockApi);

      await tester.pumpWidget(
        MaterialApp(
          home: PantallaCatalogo(
            bloc: bloc,
            habilitarImagenesRed: false,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Buscar iconos de wishlist
      final iconoFavorito = find.byIcon(Icons.favorite_border).first;
      expect(iconoFavorito, findsOneWidget);

      await tester.tap(iconoFavorito);
      await tester.pumpAndSettle();

      // Debe haberse añadido a favoritos
      expect(bloc.favoritos.contains(101), isTrue);
    });

    testWidgets('debe mostrar estado vacío cuando la categoría no tiene prendas',
        (tester) async {
      final mockApi = MockCatalogoApi(
        mockEmptyResponse: const CatalogoResponseDto(
          resumenCategorias: [
            CategoriaResumenDto(idCategoria: 99, nombre: 'Nupcial', totalPrendas: 0),
          ],
          totalArticulos: 0,
          paginaActual: 1,
          limite: 6,
          totalPaginas: 0,
          tieneSiguiente: false,
          tieneAnterior: false,
          items: [],
        ),
      );
      final bloc = CatalogoGeneralBloc(api: mockApi);

      await tester.pumpWidget(
        MaterialApp(
          home: PantallaCatalogo(
            bloc: bloc,
            habilitarImagenesRed: false,
          ),
        ),
      );

      await tester.pumpAndSettle();

      // Cambiar a categoría vacía
      bloc.seleccionarCategoria(99);
      await tester.pumpAndSettle();

      expect(find.text('COLECCIÓN NO DISPONIBLE'), findsOneWidget);
      expect(find.text('VER TODAS LAS PRENDAS DISPONIBLES'), findsOneWidget);
    });
  });
}
