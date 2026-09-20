import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/producto_item_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/producto_paginado_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/paginacion_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/filtros_disponibles_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/dominio/repositorios/catalogo_repositorio.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/presentacion/bloc/catalogo_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/presentacion/pantallas/pantalla_buscar_productos.dart';

class MockWidgetCatalogoRepositorio implements CatalogoRepositorio {
  String? ultimoTerminoBuscado;

  @override
  Future<ProductoPaginadoDto> buscarProductos({
    String? q,
    int? temporadaId,
    int? coleccionId,
    int? categoriaId,
    String? talla,
    String? color,
    double? precioMin,
    double? precioMax,
    bool soloEnStock = false,
    String ordenarPor = 'recientes',
    int pagina = 1,
    int limite = 12,
  }) async {
    ultimoTerminoBuscado = q;
    return const ProductoPaginadoDto(
      items: [
        ProductoItemDto(
          idProducto: 101,
          nombre: 'Vestido plisado seda',
          descripcion: 'Vestido largo de seda rojo carmín.',
          categoria: 'Vestidos',
          coleccion: 'Alta Costura',
          temporada: 'Otoño / Invierno 2024',
          precioBase: 890.0,
          imagenUrl: 'https://example.com/vestido.jpg',
          activo: true,
          badgeEditorial: 'EDICIÓN LIMITADA',
          subtituloAtelier: 'ALTA COSTURA',
          tallaSugerida: 'Talla 38',
          colorSugerido: 'Rojo Carmín',
          variantes: [],
        ),
        ProductoItemDto(
          idProducto: 102,
          nombre: 'Blazer lana virgen',
          descripcion: 'Blazer estructurado en lana virgen color camel.',
          categoria: 'Blazers',
          coleccion: 'Sastrería Atelier',
          temporada: 'Otoño / Invierno 2024',
          precioBase: 740.0,
          imagenUrl: 'https://example.com/blazer.jpg',
          activo: true,
          badgeEditorial: 'EN SERRANO',
          subtituloAtelier: 'SASTRERÍA ATELIER',
          tallaSugerida: 'Talla 40',
          colorSugerido: 'Camel',
          variantes: [],
        ),
      ],
      paginacion: PaginacionDto(
        totalRegistros: 2,
        paginaActual: 1,
        limite: 12,
        totalPaginas: 1,
        tieneSiguiente: false,
        tieneAnterior: false,
      ),
    );
  }

  @override
  Future<FiltrosDisponiblesDto> obtenerFiltrosDisponibles() async {
    return const FiltrosDisponiblesDto(
      temporadas: [
        TemporadaFiltroDto(id: 1, nombre: 'Otoño / Invierno 2024', tipo: 'otono_invierno', activa: true),
      ],
      colecciones: [
        ColeccionFiltroDto(id: 1, nombre: 'Alta Costura', idTemporada: 1, totalPrendas: 2),
      ],
      tallas: [
        TallaFiltroDto(id: 1, codigo: '38', orden: 1),
      ],
      colores: [
        ColorFiltroDto(id: 1, nombre: 'Rojo Carmín', codigoHex: '#991B1B'),
      ],
      rangoPrecios: RangoPreciosDto(min: 0.0, max: 2500.0),
    );
  }
}

void main() {
  group('PantallaBuscarProductos Widget Tests', () {
    late MockWidgetCatalogoRepositorio repo;
    late CatalogoBloc bloc;

    setUp(() {
      repo = MockWidgetCatalogoRepositorio();
      bloc = CatalogoBloc(repositorio: repo);
    });

    tearDown(() {
      bloc.dispose();
    });

    Widget crearWidgetPrueba() {
      return MaterialApp(
        home: PantallaBuscarProductos(bloc: bloc),
      );
    }

    testWidgets('renderiza cabecera, barra de busqueda y secciones principales', (tester) async {
      await tester.pumpWidget(crearWidgetPrueba());
      await tester.pumpAndSettle();

      // Cabecera institucional
      expect(find.text('FASHION STORE'), findsOneWidget);
      expect(find.text('Buscar'), findsWidgets);

      // Barra de búsqueda con botón de confirmación BUSCAR
      expect(find.text('Buscar vestidos, blazers, tejidos...'), findsOneWidget);
      expect(find.text('BUSCAR'), findsOneWidget);

      // Temporadas
      expect(find.text('TODAS LAS TEMPORADAS'), findsOneWidget);

      // Filtros refinados y restablecer
      expect(find.text('FILTROS REFINADOS'), findsOneWidget);
      expect(find.text('RESTABLECER'), findsOneWidget);

      // Cabecera de resultados en Outfit
      expect(find.text('Visto recientemente'), findsOneWidget);

      // Prendas mockeadas en el grid
      expect(find.text('Vestido plisado seda'), findsOneWidget);
      expect(find.text('Blazer lana virgen'), findsOneWidget);

      // Búsquedas frecuentes
      expect(find.text('BÚSQUEDAS MÁS FRECUENTES'), findsOneWidget);
      expect(find.text('Vestidos de seda'), findsOneWidget);

      // Bottom Navigation Bar
      expect(find.byType(BottomNavigationBar), findsOneWidget);
      expect(find.text('Inicio'), findsOneWidget);
      expect(find.text('Catálogo'), findsOneWidget);
      expect(find.text('Perfil'), findsOneWidget);
    });

    testWidgets('escribir en busqueda y presionar BUSCAR confirma y limpia el campo', (tester) async {
      await tester.pumpWidget(crearWidgetPrueba());
      await tester.pumpAndSettle();

      // Ingresar texto en el campo de búsqueda
      final inputFinder = find.byType(TextField);
      await tester.enterText(inputFinder, 'vestidos de seda');
      await tester.pump();

      expect(find.text('vestidos de seda'), findsOneWidget);

      // Presionar el botón BUSCAR
      await tester.tap(find.text('BUSCAR'));
      await tester.pumpAndSettle();

      // El campo se limpia automáticamente tras confirmar
      final textField = tester.widget<TextField>(inputFinder);
      expect(textField.controller?.text, isEmpty);

      // El término activo se muestra en el badge editorial y se envió al repo
      expect(repo.ultimoTerminoBuscado, equals('vestidos de seda'));
      expect(find.text('BÚSQUEDA: "vestidos de seda"'), findsOneWidget);
    });

    testWidgets('presionar el boton de filtros abre el modal bottom sheet', (tester) async {
      await tester.pumpWidget(crearWidgetPrueba());
      await tester.pumpAndSettle();

      // Presionar icono tune (filtros avanzados)
      await tester.tap(find.byIcon(Icons.tune));
      await tester.pumpAndSettle();

      // Se despliega el modal
      expect(find.text('FILTROS AVANZADOS ATELIER'), findsOneWidget);
      expect(find.text('RANGO DE INVERSIÓN'), findsOneWidget);
      expect(find.text('ORDENAR POR'), findsOneWidget);
      expect(find.text('APLICAR FILTROS'), findsOneWidget);
      expect(find.text('LIMPIAR TODO'), findsOneWidget);

      // Cerrar modal
      await tester.tap(find.byIcon(Icons.close));
      await tester.pumpAndSettle();

      expect(find.text('FILTROS AVANZADOS ATELIER'), findsNothing);
    });

    testWidgets('presionar RESTABLECER reinicia los filtros', (tester) async {
      await tester.pumpWidget(crearWidgetPrueba());
      await tester.pumpAndSettle();

      // Seleccionar una talla
      await tester.tap(find.text('38'));
      await tester.pumpAndSettle();
      expect(bloc.tallaSeleccionada, equals('38'));

      // Presionar RESTABLECER
      await tester.tap(find.text('RESTABLECER'));
      await tester.pumpAndSettle();

      expect(bloc.tallaSeleccionada, isEmpty);
      expect(bloc.tieneFiltrosActivos, isFalse);
    });
  });
}
