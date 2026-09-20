import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/producto_item_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/producto_paginado_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/paginacion_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/datos/modelos/filtros_disponibles_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/dominio/repositorios/catalogo_repositorio.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu06_buscar_filtrar/presentacion/bloc/catalogo_bloc.dart';

class MockCatalogoRepositorio implements CatalogoRepositorio {
  bool debeFallar = false;
  String? ultimoQ;
  String? ultimaTalla;
  String? ultimoColor;
  int? ultimaColeccionId;
  int? ultimaTemporadaId;

  final ProductoPaginadoDto mockPaginado = const ProductoPaginadoDto(
    items: [
      ProductoItemDto(
        idProducto: 1,
        nombre: 'Vestido plisado seda',
        descripcion: 'Vestido confeccionado en seda pura rojo carmín.',
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
        variantes: [
          VarianteResumenDto(
            idVariante: 1,
            sku: 'VES-PLI-38-ROJ',
            talla: '38',
            color: 'Rojo Carmín',
            codigoHex: '#991B1B',
            precioExtra: 0.0,
            disponible: true,
          ),
        ],
      ),
    ],
    paginacion: PaginacionDto(
      totalRegistros: 1,
      paginaActual: 1,
      limite: 12,
      totalPaginas: 1,
      tieneSiguiente: false,
      tieneAnterior: false,
    ),
  );

  final FiltrosDisponiblesDto mockFiltros = const FiltrosDisponiblesDto(
    temporadas: [
      TemporadaFiltroDto(id: 1, nombre: 'Otoño / Invierno 2024', tipo: 'otono_invierno', activa: true),
    ],
    colecciones: [
      ColeccionFiltroDto(id: 1, nombre: 'Alta Costura', idTemporada: 1, totalPrendas: 5),
    ],
    tallas: [
      TallaFiltroDto(id: 1, codigo: '38', orden: 1),
    ],
    colores: [
      ColorFiltroDto(id: 1, nombre: 'Rojo Carmín', codigoHex: '#991B1B'),
    ],
    rangoPrecios: RangoPreciosDto(min: 0.0, max: 2500.0),
  );

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
    if (debeFallar) {
      throw Exception('Fallo de red simulado');
    }
    ultimoQ = q;
    ultimaTalla = talla;
    ultimoColor = color;
    ultimaColeccionId = coleccionId;
    ultimaTemporadaId = temporadaId;
    return mockPaginado;
  }

  @override
  Future<FiltrosDisponiblesDto> obtenerFiltrosDisponibles() async {
    if (debeFallar) {
      throw Exception('Error al obtener filtros');
    }
    return mockFiltros;
  }
}

void main() {
  group('CatalogoBloc Tests (CU06 Mobile)', () {
    late MockCatalogoRepositorio repo;
    late CatalogoBloc bloc;

    setUp(() {
      repo = MockCatalogoRepositorio();
      bloc = CatalogoBloc(repositorio: repo);
    });

    tearDown(() {
      bloc.dispose();
    });

    test('estado inicial es CatalogoInicial', () {
      expect(bloc.estado, isA<CatalogoInicial>());
      expect(bloc.terminoBusquedaActivo, isEmpty);
      expect(bloc.temporadaSeleccionada, equals('Todas las temporadas'));
      expect(bloc.coleccionSeleccionada, isEmpty);
      expect(bloc.tallaSeleccionada, isEmpty);
      expect(bloc.colorSeleccionado, isEmpty);
    });

    test('inicializar carga filtros y productos correctamente', () async {
      await bloc.inicializar();

      expect(bloc.estado, isA<CatalogoCargado>());
      final cargado = bloc.estado as CatalogoCargado;
      expect(cargado.productos.length, equals(1));
      expect(cargado.productos.first.nombre, equals('Vestido plisado seda'));
      expect(bloc.filtrosDisponibles, isNotNull);
    });

    test('confirmarBusqueda actualiza termino y ejecuta consulta', () async {
      await bloc.inicializar();
      await bloc.confirmarBusqueda(nuevoTermino: 'vestido');

      expect(bloc.terminoBusquedaActivo, equals('vestido'));
      expect(repo.ultimoQ, equals('vestido'));
      expect(bloc.estado, isA<CatalogoCargado>());
    });

    test('quitarTerminoBusqueda limpia el filtro activo', () async {
      await bloc.inicializar();
      await bloc.confirmarBusqueda(nuevoTermino: 'blazer');
      expect(bloc.terminoBusquedaActivo, equals('blazer'));

      await bloc.quitarTerminoBusqueda();
      expect(bloc.terminoBusquedaActivo, isEmpty);
      expect(repo.ultimoQ, isNull);
    });

    test('filtros de coleccion, talla y color se actualizan y envian al repo', () async {
      await bloc.inicializar();
      bloc.seleccionarTemporada('Otoño / Invierno 2024');
      bloc.alternarColeccion('Alta Costura');
      bloc.seleccionarTalla('38');
      bloc.seleccionarColor('Rojo Carmín');

      await bloc.confirmarBusqueda();

      expect(repo.ultimaTemporadaId, equals(1));
      expect(repo.ultimaColeccionId, equals(1));
      expect(repo.ultimaTalla, equals('38'));
      expect(repo.ultimoColor, equals('Rojo Carmín'));
    });

    test('restablecerFiltros restaura valores por defecto', () async {
      await bloc.inicializar();
      bloc.seleccionarTalla('38');
      await bloc.confirmarBusqueda(nuevoTermino: 'seda');

      expect(bloc.tieneFiltrosActivos, isTrue);

      await bloc.restablecerFiltros();

      expect(bloc.tieneFiltrosActivos, isFalse);
      expect(bloc.terminoBusquedaActivo, isEmpty);
      expect(bloc.tallaSeleccionada, isEmpty);
      expect(repo.ultimoQ, isNull);
      expect(repo.ultimaTalla, isNull);
    });

    test('alternarFavorito agrega y quita ids correctamente', () {
      expect(bloc.favoritosIds.contains(1), isFalse);

      bloc.alternarFavorito(1);
      expect(bloc.favoritosIds.contains(1), isTrue);

      bloc.alternarFavorito(1);
      expect(bloc.favoritosIds.contains(1), isFalse);
    });

    test('aplicarBusquedaFrecuente asigna termino y consulta', () async {
      await bloc.inicializar();
      await bloc.aplicarBusquedaFrecuente('Vestidos de seda');

      expect(bloc.terminoBusquedaActivo, equals('Vestidos de seda'));
      expect(repo.ultimoQ, equals('Vestidos de seda'));
    });

    test('limpiarHistorial vacia las sugerencias', () {
      expect(bloc.busquedasFrecuentes, isNotEmpty);
      bloc.limpiarHistorial();
      expect(bloc.busquedasFrecuentes, isEmpty);
    });

    test('emite CatalogoError ante fallo del repositorio', () async {
      repo.debeFallar = true;
      await bloc.inicializar();

      expect(bloc.estado, isA<CatalogoError>());
      final error = bloc.estado as CatalogoError;
      expect(error.mensaje, contains('Fallo de red simulado'));
    });
  });
}
