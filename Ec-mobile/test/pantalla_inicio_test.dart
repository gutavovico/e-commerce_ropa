import 'dart:async';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu18_recomendaciones/datos/datasources/recomendaciones_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu18_recomendaciones/datos/modelos/recomendacion_item_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu18_recomendaciones/presentacion/bloc/inicio_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu18_recomendaciones/presentacion/pantallas/pantalla_inicio.dart';

class MockRecomendacionesApi implements RecomendacionesApi {
  final bool tieneHistorial;
  final List<ProductoRecomendadoDto> items;

  MockRecomendacionesApi({
    this.tieneHistorial = true,
    this.items = const [
      ProductoRecomendadoDto(
        idProducto: 1,
        nombre: 'Vestido plisado en seda natural',
        descripcion: 'Caída etérea con plisado manual.',
        categoria: 'Vestidos',
        precioBase: 890.0,
        imagenUrl: 'https://example.com/vestido.jpg',
        activo: true,
        badgeEditorial: 'EDICIÓN N.º 12/50',
        subtituloAtelier: 'ALTA COSTURA',
        tonoPrincipal: 'Marfil Puro',
        scoreRelevancia: 0.96,
        stockTotalDisponible: 5,
        variantes: [],
      ),
      ProductoRecomendadoDto(
        idProducto: 2,
        nombre: 'Blazer estructurado en lana virgen',
        descripcion: 'Lana virgen italiana certificada.',
        categoria: 'Sastrería',
        precioBase: 740.0,
        imagenUrl: 'https://example.com/blazer.jpg',
        activo: true,
        badgeEditorial: 'LANA 100%',
        subtituloAtelier: 'BIELLA 1850',
        tonoPrincipal: 'Camel Puro',
        scoreRelevancia: 0.92,
        stockTotalDisponible: 8,
        variantes: [],
      ),
    ],
  });

  @override
  Future<RecomendacionesResponseDto> obtenerRecomendaciones({
    String? token,
    int limite = 6,
    int? idSucursal,
  }) async {
    return RecomendacionesResponseDto(
      tieneHistorial: tieneHistorial,
      motivoGeneral: 'Basado en tu última adquisición de sastrería y seda en Flagship Serrano (Madrid).',
      boutiqueReferencia: 'Boutique Serrano (Madrid)',
      mensajeEmptyState:
          'Aún no contamos con suficientes interacciones o compras previas para personalizar tu selección. Explora nuestras colecciones activas para descubrir piezas afines a tu estilo',
      totalRecomendados: items.length,
      items: items,
    );
  }
}

class TestHttpOverrides extends HttpOverrides {
  @override
  HttpClient createHttpClient(SecurityContext? context) {
    return _MockHttpClient();
  }
}

class _MockHttpClient extends Fake implements HttpClient {
  @override
  Future<HttpClientRequest> getUrl(Uri url) async => _MockHttpClientRequest();
}

class _MockHttpClientRequest extends Fake implements HttpClientRequest {
  @override
  Future<HttpClientResponse> close() async => _MockHttpClientResponse();
}

class _MockHttpClientResponse extends Fake implements HttpClientResponse {
  @override
  int get statusCode => 200;
  @override
  int get contentLength => _kTransparentImage.length;
  @override
  HttpClientResponseCompressionState get compressionState =>
      HttpClientResponseCompressionState.notCompressed;
  @override
  StreamSubscription<List<int>> listen(
    void Function(List<int> event)? onData, {
    Function? onError,
    void Function()? onDone,
    bool? cancelOnError,
  }) {
    return Stream<List<int>>.fromIterable([_kTransparentImage]).listen(
      onData,
      onError: onError,
      onDone: onDone,
      cancelOnError: cancelOnError,
    );
  }
}

final Uint8List _kTransparentImage = Uint8List.fromList([
  0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0x00, 0x00, 0x00, 0x0D,
  0x49, 0x48, 0x44, 0x52, 0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
  0x08, 0x06, 0x00, 0x00, 0x00, 0x1F, 0x15, 0xC4, 0x89, 0x00, 0x00, 0x00,
  0x0A, 0x49, 0x44, 0x41, 0x54, 0x78, 0x9C, 0x63, 0x00, 0x01, 0x00, 0x00,
  0x05, 0x00, 0x01, 0x0D, 0x0A, 0x2D, 0xB4, 0x00, 0x00, 0x00, 0x00, 0x49,
  0x45, 0x4E, 0x44, 0xAE, 0x42, 0x60, 0x82,
]);

void main() {
  setUp(() {
    HttpOverrides.global = TestHttpOverrides();
  });

  tearDown(() {
    HttpOverrides.global = null;
  });

  testWidgets('PantallaInicio renderiza cabecera, chip boutique y saludo de bienvenida', (tester) async {
    final mockApi = MockRecomendacionesApi();
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('FASHION STORE'), findsOneWidget);
    expect(find.text('BOUTIQUE SERRANO (MADRID)'), findsOneWidget);
    expect(find.text('BIENVENIDA DE NUEVO'), findsOneWidget);
    expect(find.text('Ana Valenzuela'), findsOneWidget);
  });

  testWidgets('PantallaInicio renderiza Hero Banner con tag NUEVA TEMPORADA y botón CTA', (tester) async {
    final mockApi = MockRecomendacionesApi();
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('• NUEVA TEMPORADA'), findsOneWidget);
    expect(find.textContaining('Visita nuestra'), findsOneWidget);
    expect(find.text('EXPLORAR COLECCIÓN'), findsOneWidget);
  });

  testWidgets('PantallaInicio renderiza cards de recomendación con compras previas (CU18)', (tester) async {
    final mockApi = MockRecomendacionesApi(tieneHistorial: true);
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Recomendado para ti'), findsOneWidget);
    expect(find.text('Ver catálogo'), findsOneWidget);
    expect(find.text('Vestido plisado en seda natural'), findsOneWidget);
    expect(find.text('890 €'), findsOneWidget);
    expect(find.text('Blazer estructurado en lana virgen'), findsOneWidget);
    expect(find.text('740 €'), findsOneWidget);
    expect(find.text('+ BOLSA'), findsNWidgets(2));
  });

  testWidgets('PantallaInicio renderiza Empty State oficial cuando no tiene historial', (tester) async {
    final mockApi = MockRecomendacionesApi(tieneHistorial: false, items: const []);
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Personalización Atelier'), findsOneWidget);
    expect(
      find.textContaining('Aún no contamos con suficientes interacciones o compras previas'),
      findsOneWidget,
    );
    expect(find.text('EXPLORAR CATÁLOGO COMPLETO →'), findsOneWidget);
  });

  testWidgets('PantallaInicio renderiza sección Experiencia Atelier y garantías', (tester) async {
    final mockApi = MockRecomendacionesApi();
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.text('Experiencia Atelier'), findsOneWidget);
    expect(find.text('Patronaje a Medida en Serrano'), findsOneWidget);
    expect(find.text('Entrega con Guante Blanco'), findsOneWidget);
  });

  testWidgets('PantallaInicio presionar + BOLSA incrementa contador y muestra toast', (tester) async {
    final mockApi = MockRecomendacionesApi();
    final bloc = InicioBloc(api: mockApi);

    await tester.pumpWidget(
      MaterialApp(
        home: PantallaInicio(bloc: bloc),
      ),
    );
    await tester.pumpAndSettle();

    expect(bloc.cestaCount, 0);

    final botonBolsa = find.text('+ BOLSA').first;
    await tester.ensureVisible(botonBolsa);
    await tester.pumpAndSettle();

    await tester.tap(botonBolsa);
    await tester.pump();

    expect(bloc.cestaCount, 1);
    expect(find.textContaining('ha sido añadida a tu bolsa de compra'), findsOneWidget);
  });
}
