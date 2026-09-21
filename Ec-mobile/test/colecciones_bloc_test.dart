import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/datos/datasources/colecciones_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/datos/modelos/coleccion_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu36_consultar_colecciones/presentacion/bloc/colecciones_bloc.dart';

class MockColeccionesApi implements ColeccionesApi {
  bool debeFallarActivas = false;
  bool debeFallarPrendas = false;

  final ColeccionesActivasResponseDto mockActivas =
      const ColeccionesActivasResponseDto(
    temporadaActivaId: 1,
    temporadaActivaNombre: 'Otoño / Invierno 2024',
    totalColecciones: 3,
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
      imagenPortada: 'https://images.unsplash.com/photo-1',
      piezasClave: [
        ProductoColeccionItemDto(
          idProducto: 1,
          nombre: 'Vestido plisado seda',
          descripcion: 'Vestido en seda pura rojo carmín.',
          precioBase: 890.0,
          imagenUrl: 'https://images.unsplash.com/vestido',
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
        imagenPortada: 'https://images.unsplash.com/milano',
        piezasClave: [],
      ),
    ],
  );

  final ColeccionDetalleDto mockDetalle = const ColeccionDetalleDto(
    idColeccion: 1,
    nombre: 'Sastrería en Lana Virgen & Seda Natural',
    descripcion: 'Colección de sastrería artesanal.',
    temporadaNombre: 'Otoño / Invierno 2024',
    tallerOrigen: 'Molinos de Biella & Lyon',
    totalPrendas: 2,
    mensajeEmptyState: null,
    productos: [
      ProductoColeccionItemDto(
        idProducto: 1,
        nombre: 'Vestido plisado seda',
        precioBase: 890.0,
        badgeEditorial: 'EDICIÓN LIMITADA',
        subtituloTextil: 'SEDA LYON',
        categoria: 'Vestidos',
        stockTotalDisponible: 15,
        tieneStock: true,
      ),
      ProductoColeccionItemDto(
        idProducto: 2,
        nombre: 'Blazer lana estructurado',
        precioBase: 740.0,
        badgeEditorial: 'SASTRERÍA ATELIER',
        subtituloTextil: 'BIELLA 380G',
        categoria: 'Sastrería',
        stockTotalDisponible: 8,
        tieneStock: true,
      ),
    ],
  );

  @override
  Future<ColeccionesActivasResponseDto> obtenerColeccionesActivas({
    int limitePiezasClave = 4,
  }) async {
    if (debeFallarActivas) {
      throw const ColeccionesException('Fallo de red en colecciones activas');
    }
    return mockActivas;
  }

  @override
  Future<ColeccionDetalleDto> obtenerPrendasDeColeccion(int idColeccion) async {
    if (debeFallarPrendas) {
      throw const ColeccionesException('Fallo al obtener detalle');
    }
    return mockDetalle;
  }
}

void main() {
  group('ColeccionesBloc Tests', () {
    late MockColeccionesApi api;
    late ColeccionesBloc bloc;

    setUp(() {
      api = MockColeccionesApi();
      bloc = ColeccionesBloc(api: api);
    });

    test('estado inicial es ColeccionesInicial', () {
      expect(bloc.estado, isA<ColeccionesInicial>());
      expect(bloc.cestaCount, equals(0));
      expect(bloc.chipSeleccionado, equals('COLECCIÓN DESTACADA'));
    });

    test('cargarColeccionesActivas exitoso emite ColeccionesCargadas', () async {
      await bloc.cargarColeccionesActivas();

      expect(bloc.estado, isA<ColeccionesCargadas>());
      final estado = bloc.estado as ColeccionesCargadas;
      expect(estado.totalColecciones, equals(3));
      expect(estado.temporadaNombre, equals('Otoño / Invierno 2024'));
      expect(estado.destacada, isNotNull);
      expect(estado.destacada!.nombre,
          equals('Sastrería en Lana Virgen & Seda Natural'));
      expect(estado.destacada!.piezasClave.length, equals(1));
      expect(estado.otrasColecciones.length, equals(1));
    });

    test('cargarColeccionesActivas fallido emite ColeccionesError', () async {
      api.debeFallarActivas = true;

      await bloc.cargarColeccionesActivas();

      expect(bloc.estado, isA<ColeccionesError>());
      final estado = bloc.estado as ColeccionesError;
      expect(estado.mensaje, contains('Fallo de red'));
    });

    test('seleccionarChip actualiza el chip y el estado', () async {
      await bloc.cargarColeccionesActivas();

      bloc.seleccionarChip('ENVÍO ATELIER');

      expect(bloc.chipSeleccionado, equals('ENVÍO ATELIER'));
      final estado = bloc.estado as ColeccionesCargadas;
      expect(estado.chipSeleccionado, equals('ENVÍO ATELIER'));
    });

    test('cargarPrendasColeccion actualiza detalleActual con éxito', () async {
      await bloc.cargarPrendasColeccion(1);

      expect(bloc.cargandoDetalle, isFalse);
      expect(bloc.errorDetalle, isNull);
      expect(bloc.detalleActual, isNotNull);
      expect(bloc.detalleActual!.idColeccion, equals(1));
      expect(bloc.detalleActual!.productos.length, equals(2));
    });

    test('alternarBookmark añade y quita IDs de productos', () {
      expect(bloc.esBookmark(1), isFalse);

      bloc.alternarBookmark(1);
      expect(bloc.esBookmark(1), isTrue);
      expect(bloc.bookmarks.contains(1), isTrue);

      bloc.alternarBookmark(1);
      expect(bloc.esBookmark(1), isFalse);
    });

    test('agregarACesta incrementa contador y setea mensaje toast', () {
      const item = ProductoColeccionItemDto(
        idProducto: 1,
        nombre: 'Vestido plisado seda',
        precioBase: 890.0,
        badgeEditorial: 'EDICIÓN LIMITADA',
        subtituloTextil: 'SEDA LYON',
        categoria: 'Vestidos',
        stockTotalDisponible: 10,
        tieneStock: true,
      );

      bloc.agregarACesta(item);

      expect(bloc.cestaCount, equals(1));
      expect(bloc.mensajeToast, contains('Vestido plisado seda'));

      bloc.limpiarMensajeToast();
      expect(bloc.mensajeToast, isNull);
    });

    test('Serialización y deserialización de DTOs JSON', () {
      final jsonDto = {
        'id_coleccion': 10,
        'nombre': 'Colección Cápsula',
        'descripcion': 'Cápsula de satén.',
        'temporada_nombre': 'Invierno 2024',
        'temporada_tipo': 'otoño_invierno',
        'taller_origen': 'Lyon',
        'precio_desde': 500.0,
        'total_prendas': 3,
        'es_destacada': true,
        'badge_edicion': 'EDICIÓN 01',
        'imagen_portada': 'https://example.com/portada.jpg',
        'piezas_clave': [
          {
            'id_producto': 101,
            'nombre': 'Top Satén',
            'precio_base': 220.0,
            'badge_editorial': 'EXCLUSIVO',
            'subtitulo_textil': 'SATÉN',
            'categoria': 'Tops',
            'colores_disponibles': ['#000000'],
            'stock_total_disponible': 5,
            'tiene_stock': true,
          }
        ],
      };

      final dto = ColeccionResumenDto.fromJson(jsonDto);
      expect(dto.idColeccion, equals(10));
      expect(dto.piezasClave.length, equals(1));
      expect(dto.piezasClave.first.precioBase, equals(220.0));

      final serialized = dto.toJson();
      expect(serialized['id_coleccion'], equals(10));
      expect(serialized['nombre'], equals('Colección Cápsula'));
    });

    test('Deserialización de precios en formato String ("310.00" de FastAPI Decimal)', () {
      final jsonConStrings = {
        'id_coleccion': 1,
        'nombre': 'Sastrería en Lana Virgen & Seda Natural',
        'temporada_nombre': 'Primavera-Verano 2026',
        'temporada_tipo': 'primavera_verano',
        'taller_origen': 'Molinos de Biella & Lyon',
        'precio_desde': '310.00', // Enviado como String por FastAPI Decimal
        'total_prendas': 4,
        'es_destacada': true,
        'badge_edicion': 'EDICIÓN VIGENTE',
        'piezas_clave': [
          {
            'id_producto': 1,
            'nombre': 'Vestido Seda',
            'precio_base': '890.00', // Enviado como String por FastAPI Decimal
            'badge_editorial': 'ALTA COSTURA',
            'subtitulo_textil': 'SEDA LYON',
            'categoria': 'Vestidos',
            'stock_total_disponible': 10,
            'tiene_stock': true,
          }
        ],
      };

      final dto = ColeccionResumenDto.fromJson(jsonConStrings);
      expect(dto.precioDesde, equals(310.0));
      expect(dto.piezasClave.first.precioBase, equals(890.0));
    });
  });
}
