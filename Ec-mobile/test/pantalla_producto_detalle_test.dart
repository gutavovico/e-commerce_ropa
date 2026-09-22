import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/datos/datasources/producto_detalle_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/datos/modelos/producto_detalle_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/presentacion/bloc/producto_detalle_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu07_detalle_producto/presentacion/pantallas/pantalla_producto_detalle.dart';

class MockProductoDetalleApi implements ProductoDetalleApi {
  final ProductoDetalleDto mockDetalle;
  final DisponibilidadResponseDto mockDisponibilidad;
  final List<SucursalDisponibilidadDto> mockSucursales;
  final ReservaCreadaOutDto mockReserva;
  bool shouldThrow;

  MockProductoDetalleApi({
    ProductoDetalleDto? mockDetalle,
    DisponibilidadResponseDto? mockDisponibilidad,
    List<SucursalDisponibilidadDto>? mockSucursales,
    ReservaCreadaOutDto? mockReserva,
    this.shouldThrow = false,
  })  : mockDetalle = mockDetalle ?? _crearDetalleMock(),
        mockDisponibilidad = mockDisponibilidad ?? _crearDisponibilidadMock(),
        mockSucursales = mockSucursales ?? _crearSucursalesMock(),
        mockReserva = mockReserva ?? _crearReservaMock();

  static ProductoDetalleDto _crearDetalleMock() {
    return const ProductoDetalleDto(
      idProducto: 1,
      nombre: 'Vestido Plisado en Seda Marfil Natural',
      descripcion: 'Vestido largo de alta costura con micro-plisado artesanal.',
      subtituloAtelier: 'ALTA COSTURA · MILÁN / LYON',
      etiquetaBadge: 'EDICIÓN LIMITADA',
      skuBase: 'ATEL-2025-V09',
      precioBase: 1050.0,
      precioFinal: 890.0,
      tieneDescuento: true,
      porcentajeDescuento: 15,
      categoriaId: 2,
      categoriaNombre: 'Vestidos',
      imagenUrl: 'https://images.unsplash.com/photo-vestido-marfil.jpg',
      galeriaAngulos: [
        ImagenAnguloDto(
          url: 'https://images.unsplash.com/photo-vestido-marfil.jpg?crop=center',
          etiqueta: 'FRONTAL',
          orden: 1,
        ),
        ImagenAnguloDto(
          url: 'https://images.unsplash.com/photo-vestido-marfil.jpg?crop=top',
          etiqueta: 'TEXTURA & SEDA',
          orden: 2,
        ),
        ImagenAnguloDto(
          url: 'https://images.unsplash.com/photo-vestido-marfil.jpg?crop=left',
          etiqueta: 'SILUETA & CAÍDA',
          orden: 3,
        ),
        ImagenAnguloDto(
          url: 'https://images.unsplash.com/photo-vestido-marfil.jpg?crop=bottom',
          etiqueta: 'ACABADO & COSTURA',
          orden: 4,
        ),
      ],
      modeloArUrl: null,
      modeloInfo: 'MODELO: 1,77M - TALLA 38 ES',
      composicion: ComposicionNobleDto(
        cuerpoPrincipal: '100% Seda Natural 22 Momme',
        forroInterior: 'Crepé de seda puro transpirable',
        tecnicaTextil: 'Plisado artesanal al vapor de Lyon',
        descripcionConfeccion:
            'Cada paño requiere 48 horas de moldeado térmico manual.',
        instruccionesCuidado: [
          'Limpieza profesional en seco con percloroetileno moderado.',
          'Planchado únicamente vertical mediante vapor suave.',
        ],
      ),
      coloresDisponibles: [
        ColorDetalleDto(
          idColor: 1,
          nombre: 'Seda Marfil',
          codigoHex: '#F5F0EA',
          disponible: true,
        ),
        ColorDetalleDto(
          idColor: 2,
          nombre: 'Negro Azabache',
          codigoHex: '#1A1A1A',
          disponible: true,
        ),
      ],
      tallasDisponibles: [
        TallaDetalleDto(
          idTalla: 1,
          codigo: '36',
          orden: 1,
          disponible: true,
          stockTotal: 5,
        ),
        TallaDetalleDto(
          idTalla: 2,
          codigo: '38',
          orden: 2,
          disponible: true,
          stockTotal: 10,
        ),
        TallaDetalleDto(
          idTalla: 3,
          codigo: '40',
          orden: 3,
          disponible: true,
          stockTotal: 0,
        ),
      ],
      variantes: [
        // Marfil: 36 (stock 2), 38 (stock 5), 40 (stock 0)
        VarianteDetalleDto(
          idVariante: 101,
          idProducto: 1,
          idTalla: 1,
          tallaCodigo: '36',
          tallaOrden: 1,
          idColor: 1,
          colorNombre: 'Seda Marfil',
          colorHex: '#F5F0EA',
          sku: 'ATEL-2025-V09-IV-36',
          precioExtra: 0.0,
          precioFinalVariante: 890.0,
          stockTotalDisponible: 2,
          tieneStock: true,
        ),
        VarianteDetalleDto(
          idVariante: 102,
          idProducto: 1,
          idTalla: 2,
          tallaCodigo: '38',
          tallaOrden: 2,
          idColor: 1,
          colorNombre: 'Seda Marfil',
          colorHex: '#F5F0EA',
          sku: 'ATEL-2025-V09-IV-38',
          precioExtra: 0.0,
          precioFinalVariante: 890.0,
          stockTotalDisponible: 5,
          tieneStock: true,
        ),
        VarianteDetalleDto(
          idVariante: 103,
          idProducto: 1,
          idTalla: 3,
          tallaCodigo: '40',
          tallaOrden: 3,
          idColor: 1,
          colorNombre: 'Seda Marfil',
          colorHex: '#F5F0EA',
          sku: 'ATEL-2025-V09-IV-40',
          precioExtra: 0.0,
          precioFinalVariante: 890.0,
          stockTotalDisponible: 0,
          tieneStock: false,
        ),
        // Negro: 36 (stock 0), 38 (stock 4), 40 (stock 3)
        VarianteDetalleDto(
          idVariante: 104,
          idProducto: 1,
          idTalla: 1,
          tallaCodigo: '36',
          tallaOrden: 1,
          idColor: 2,
          colorNombre: 'Negro Azabache',
          colorHex: '#1A1A1A',
          sku: 'ATEL-2025-V09-BK-36',
          precioExtra: 0.0,
          precioFinalVariante: 920.0,
          stockTotalDisponible: 0,
          tieneStock: false,
        ),
        VarianteDetalleDto(
          idVariante: 105,
          idProducto: 1,
          idTalla: 2,
          tallaCodigo: '38',
          tallaOrden: 2,
          idColor: 2,
          colorNombre: 'Negro Azabache',
          colorHex: '#1A1A1A',
          sku: 'ATEL-2025-V09-BK-38',
          precioExtra: 30.0,
          precioFinalVariante: 920.0,
          stockTotalDisponible: 4,
          tieneStock: true,
        ),
      ],
      totalGuardados: 42,
    );
  }

  static DisponibilidadResponseDto _crearDisponibilidadMock() {
    return const DisponibilidadResponseDto(
      idProducto: 1,
      idVariante: 102,
      sku: 'ATEL-2025-V09-IV-38',
      sucursales: [
        SucursalDisponibilidadDto(
          idSucursal: 1,
          nombre: 'Flagship Serrano (Madrid)',
          ciudad: 'Madrid',
          direccion: 'Calle de Serrano 44, Salamanca',
          telefono: '+34 910 234 567',
          horarioApertura: '10:00',
          horarioCierre: '20:30',
          cantidadDisponible: 3,
          cantidadReservada: 1,
          estadoStock: 'disponible',
          badgeStock: '3 UDS EN STOCK',
          citasDisponiblesTexto: 'Citas disponibles hoy y mañana',
          permiteReservaDirecta: true,
        ),
        SucursalDisponibilidadDto(
          idSucursal: 2,
          nombre: 'Boutique Saint-Honoré (Paris)',
          ciudad: 'Paris',
          direccion: 'Rue du Faubourg Saint-Honoré 12',
          telefono: '+33 1 42 68 00 00',
          horarioApertura: '10:00',
          horarioCierre: '19:30',
          cantidadDisponible: 0,
          cantidadReservada: 0,
          estadoStock: 'agotada',
          badgeStock: 'AGOTADO',
          citasDisponiblesTexto: 'Próxima recepción en 48h',
          permiteReservaDirecta: false,
        ),
      ],
      totalDisponibleGlobal: 3,
    );
  }

  static List<SucursalDisponibilidadDto> _crearSucursalesMock() {
    return _crearDisponibilidadMock().sucursales;
  }

  /// Payload literal de `ReservaCreadaOut` tal y como lo emite
  /// `POST /api/v1/reservas` (Ec-backend/app/modules/reservas/cu12_reservar_prendas/esquemas.py).
  static const Map<String, dynamic> respuestaReservaBackend = {
    'id_reserva': 501,
    'codigo_reserva': 'RES-2026-0501',
    'id_sucursal': 1,
    'nombre_sucursal': 'Flagship Serrano (Madrid)',
    'direccion_sucursal': 'Calle de Serrano 44, Salamanca',
    'fecha_hora_atencion': '2026-09-22T11:30:00Z',
    'estado': 'pendiente',
    'canal_origen': 'movil',
    'items': [
      {
        'id_reserva_detalle': 1,
        'id_variante': 10,
        'sku': 'ATEL-2025-VD9-38-MAR',
        'nombre_producto': 'Vestido Plisado en Seda Marfil Natural',
        'talla_codigo': '38',
        'color_nombre': 'Seda Marfil',
        'cantidad': 1,
        'precio_unitario': '890.00',
      },
    ],
    'mensaje_confirmacion':
        'Cita de prueba presencial confirmada con nuestro equipo de sastrería.',
    'cortesias_incluidas': [
      'Champán de cortesía o infusión artesanal de bienvenida',
    ],
    'creado_en': '2026-09-21T10:00:00Z',
  };

  /// Se deserializa con `fromJson` a propósito: construir el DTO con su constructor
  /// saltaba el mapeo de claves, que es justo donde estaban los desajustes de contrato
  /// que dejaban la reserva en 422 y el diálogo con datos inventados.
  static ReservaCreadaOutDto _crearReservaMock() {
    return ReservaCreadaOutDto.fromJson(respuestaReservaBackend);
  }

  @override
  Future<ProductoDetalleDto> obtenerDetalleProducto(int idProducto) async {
    if (shouldThrow) {
      throw const ProductoDetalleException('Error simulado al cargar prenda.');
    }
    return mockDetalle;
  }

  @override
  Future<DisponibilidadResponseDto> consultarDisponibilidad(
    int idProducto, {
    int? idVariante,
  }) async {
    if (shouldThrow) {
      throw const ProductoDetalleException('Error simulado en stock.');
    }
    return mockDisponibilidad;
  }

  @override
  Future<List<SucursalDisponibilidadDto>> obtenerSucursalesActivas() async {
    return mockSucursales;
  }

  @override
  Future<ReservaCreadaOutDto> crearReserva(
    ReservaCrearInDto datos, {
    String? token,
  }) async {
    if (shouldThrow) {
      throw const ProductoDetalleException('Error simulado al reservar cita.');
    }
    return mockReserva;
  }
}

void main() {
  group('ProductoDetalleBloc Unit Tests', () {
    test('Estado inicial debe ser ProductoDetalleInicial', () {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      expect(bloc.estado, isA<ProductoDetalleInicial>());
    });

    test('cargarDetalle transiciona a ProductoDetalleCargado con variante inicial y stock', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      expect(bloc.estado, isA<ProductoDetalleCargado>());
      final cargado = bloc.estado as ProductoDetalleCargado;
      expect(cargado.producto.idProducto, 1);
      expect(cargado.colorSeleccionado?.nombre, 'Seda Marfil');
      expect(cargado.tallaSeleccionada?.codigo, '36');
      expect(cargado.varianteActiva?.sku, 'ATEL-2025-V09-IV-36');
      expect(cargado.sucursales.length, 2);
    });

    test('seleccionarColor en cascada actualiza tallas y variante activa', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      final cargado = bloc.estado as ProductoDetalleCargado;
      final colorNegro = cargado.producto.coloresDisponibles[1];

      // Cambiar a Negro Azabache
      bloc.seleccionarColor(colorNegro);

      final nuevoEstado = bloc.estado as ProductoDetalleCargado;
      expect(nuevoEstado.colorSeleccionado?.nombre, 'Negro Azabache');
      // En Negro, la talla 36 tiene stock 0, por lo que debe seleccionar la primera disponible (talla 38)
      expect(nuevoEstado.tallaSeleccionada?.codigo, '38');
      expect(nuevoEstado.varianteActiva?.sku, 'ATEL-2025-V09-BK-38');
      expect(nuevoEstado.precioActual, 920.0);
    });

    test('seleccionarTalla actualiza variante activa y SKU correspondiente', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      final cargado = bloc.estado as ProductoDetalleCargado;
      final talla38 = cargado.producto.tallasDisponibles[1]; // 38

      bloc.seleccionarTalla(talla38);

      final nuevoEstado = bloc.estado as ProductoDetalleCargado;
      expect(
        nuevoEstado.stockAdvertenciaTexto,
        anyOf(contains('Últimas 5 unidades'), contains('Disponible')),
      );
    });

    test('cambiarIndiceGaleria rota de imagen 0 a 3', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      bloc.cambiarIndiceGaleria(2);
      var estado = bloc.estado as ProductoDetalleCargado;
      expect(estado.indiceGaleria, 2);

      bloc.cambiarIndiceGaleria(3);
      estado = bloc.estado as ProductoDetalleCargado;
      expect(estado.indiceGaleria, 3);
    });

    test('toggleFavorito y agregarABolsa notifican reactivamente', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      bloc.toggleFavorito();
      var estado = bloc.estado as ProductoDetalleCargado;
      expect(estado.esFavorito, true);
      expect(estado.mensajeNotificacion, contains('Deseos Atelier'));

      bloc.agregarABolsa();
      estado = bloc.estado as ProductoDetalleCargado;
      expect(estado.bolsaContador, 1);
      expect(estado.mensajeNotificacion, contains('bolsa de compras'));
    });

    test('confirmarReserva coordina cita privada en boutique', () async {
      final bloc = ProductoDetalleBloc(api: MockProductoDetalleApi());
      await bloc.cargarDetalle(1);

      final exito = await bloc.confirmarReserva(
        idSucursal: 1,
        fechaReserva: DateTime.now().add(const Duration(days: 1)),
      );

      expect(exito, true);
      final estado = bloc.estado as ProductoDetalleCargado;
      expect(estado.ultimaReserva?.codigoReserva, 'RES-2026-0501');
      expect(estado.mensajeNotificacion, contains('RES-2026-0501'));
    });
  });

  group('PantallaProductoDetalle Widget Tests', () {
    Widget crearAppPrueba({ProductoDetalleBloc? bloc}) {
      return MaterialApp(
        theme: ThemeData(fontFamily: 'Outfit'),
        home: PantallaProductoDetalle(
          idProducto: 1,
          habilitarImagenesRed: false,
          bloc: bloc ?? ProductoDetalleBloc(api: MockProductoDetalleApi()),
        ),
      );
    }

    testWidgets('renderiza cabecera, nombre, rating VIP y precio de la prenda', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      // Nombre y subtítulo de alta costura
      expect(find.text('Vestido Plisado en Seda Marfil Natural'), findsOneWidget);
      expect(find.text('ALTA COSTURA · MILÁN / LYON'), findsWidgets);
      expect(find.text('4.9 · 38 reseñas VIP'), findsOneWidget);
      expect(find.text('890 €'), findsWidgets);
    });

    testWidgets('cumple Directriz Hub-and-Spoke: botón VOLVER presente y ausencia de BottomNavigationBar', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      // Botón funcional de regreso en AppBar
      expect(find.text('VOLVER'), findsOneWidget);
      expect(find.byIcon(Icons.arrow_back), findsOneWidget);

      // No posee BottomNavigationBar propia (es una pantalla hoja)
      expect(find.byType(BottomNavigationBar), findsNothing);
    });

    testWidgets('renderiza galería con indicador 1 / 4 y botón flotante PROBAR EN AR', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      // Indicador de foto
      expect(find.text('1 / 4'), findsOneWidget);

      // Botón AR CU10
      expect(find.text('PROBAR EN AR'), findsOneWidget);
      expect(find.byIcon(Icons.view_in_ar), findsOneWidget);

      // Presionar PROBAR EN AR abre modal informativo sin errores
      await tester.tap(find.text('PROBAR EN AR'));
      await tester.pumpAndSettle();

      expect(find.text('VESTIDOR VIRTUAL AR ATELIER'), findsOneWidget);
      expect(find.text('COMPRENDIDO'), findsOneWidget);

      await tester.tap(find.text('COMPRENDIDO'));
      await tester.pumpAndSettle();
    });

    testWidgets('renderiza acordeón de composición noble con técnica textil y cuidados', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(
        find.text('Composición & Confección Noble'),
        200,
        scrollable: find.byType(Scrollable).first,
      );

      expect(find.text('Composición & Confección Noble'), findsOneWidget);
      expect(find.text('100% Seda Natural 22 Momme'), findsOneWidget);
      expect(find.text('Crepé de seda puro transpirable'), findsOneWidget);
      expect(find.text('Plisado artesanal al vapor de Lyon'), findsOneWidget);
    });

    testWidgets('renderiza disponibilidad por sucursal con botón RESERVAR EN ESTA BOUTIQUE', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      await tester.scrollUntilVisible(
        find.text('Disponibilidad en Boutique'),
        200,
        scrollable: find.byType(Scrollable).first,
      );

      expect(find.text('Disponibilidad en Boutique'), findsOneWidget);
      expect(find.text('Flagship Serrano (Madrid)'), findsOneWidget);
      expect(find.text('DISPONIBLE (3 UDS.)'), findsOneWidget);
      expect(find.text('RESERVAR EN ESTA BOUTIQUE'), findsWidgets);
    });

    testWidgets('presionar RESERVAR EN ESTA BOUTIQUE despliega BottomSheet con franjas y confirmación', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      final botonReserva = find.text('RESERVAR EN ESTA BOUTIQUE').first;
      await tester.scrollUntilVisible(
        botonReserva,
        200,
        scrollable: find.byType(Scrollable).first,
      );

      // Tocar botón directo de reserva en Flagship Serrano
      await tester.tap(botonReserva);
      await tester.pumpAndSettle();

      // Modal BottomSheet CU12
      expect(find.text('RESERVAR CITA DE PRUEBA EN BOUTIQUE'), findsOneWidget);
      expect(find.text('1. SELECCIONA LA BOUTIQUE INSIGNIA'), findsOneWidget);
      expect(find.text('2. FECHA Y HORA PREFERENTE'), findsOneWidget);
      expect(find.text('MAÑANA 11:30H'), findsOneWidget);
      expect(find.text('CONFIRMAR RESERVA EN BOUTIQUE'), findsOneWidget);

      // Confirmar reserva
      await tester.tap(find.text('CONFIRMAR RESERVA EN BOUTIQUE'));
      await tester.pumpAndSettle();

      // Diálogo de confirmación
      expect(find.text('CITA CONFIRMADA'), findsOneWidget);
      expect(find.textContaining('RES-2026-0501'), findsOneWidget);

      await tester.tap(find.text('ENTENDIDO'));
      await tester.pumpAndSettle();
    });

    testWidgets('barra persistente inferior permite añadir prenda a la bolsa', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(crearAppPrueba());
      await tester.pumpAndSettle();

      // Botón inferior persistente
      final botonBolsa = find.text('AÑADIR A LA BOLSA · 890 €');
      expect(botonBolsa, findsOneWidget);

      await tester.tap(botonBolsa);
      await tester.pump();

      expect(find.text('Prenda añadida a la bolsa de compras'), findsOneWidget);
    });
  });

  // Los DTO se construían con sus constructores en todos los tests, de modo que el mapeo
  // de claves JSON nunca se ejercitaba. Este grupo valida el contrato contra el backend.
  group('Contrato CU07/CU12 con el backend', () {
    test('ReservaCrearInDto.toJson usa las claves que exige ReservaCrearIn', () {
      final payload = ReservaCrearInDto(
        idSucursal: 1,
        fechaHoraAtencion: DateTime.utc(2026, 9, 22, 11, 30),
        canalOrigen: 'movil',
        observacion: 'Cita privada de prueba en boutique',
        lineas: const [ReservaLineaInDto(idVariante: 10, cantidad: 2)],
      );

      final json = payload.toJson();

      expect(json.keys, containsAll(<String>[
        'id_sucursal',
        'fecha_hora_atencion',
        'canal_origen',
        'observacion',
        'items',
      ]));
      // Las claves antiguas provocaban un 422 en cada intento de reserva.
      expect(json.containsKey('fecha_reserva'), isFalse);
      expect(json.containsKey('notas_cliente'), isFalse);
      expect(json.containsKey('lineas'), isFalse);

      final items = json['items'] as List<dynamic>;
      expect(items, hasLength(1));
      expect((items.first as Map<String, dynamic>)['id_variante'], 10);
      expect((items.first as Map<String, dynamic>)['cantidad'], 2);
    });

    test('ReservaCreadaOutDto.fromJson lee la respuesta real de POST /api/v1/reservas', () {
      final reserva = ReservaCreadaOutDto.fromJson(
        MockProductoDetalleApi.respuestaReservaBackend,
      );

      expect(reserva.idReserva, 501);
      expect(reserva.codigoReserva, 'RES-2026-0501');
      expect(reserva.sucursalNombre, 'Flagship Serrano (Madrid)');
      expect(reserva.direccionSucursal, 'Calle de Serrano 44, Salamanca');
      expect(reserva.fechaHoraAtencion, '2026-09-22T11:30:00Z');
      expect(
        reserva.mensaje,
        'Cita de prueba presencial confirmada con nuestro equipo de sastrería.',
      );
      expect(reserva.cortesiasIncluidas, hasLength(1));
      // El total se deriva de las líneas: el backend no envía `total_prendas`.
      expect(reserva.totalPrendas, 1);
      // FastAPI serializa Decimal como string.
      expect(reserva.items.first.precioUnitario, 890.0);
    });

    test('ProductoDetalleDto.fromJson lee imagen_principal y galeria', () {
      final producto = ProductoDetalleDto.fromJson(const {
        'id_producto': 1,
        'nombre': 'Vestido Plisado en Seda Marfil Natural',
        'precio_base': '1050.00',
        'precio_final': '890.00',
        'imagen_principal': 'https://cdn.fashionstore.test/vestido-frontal.jpg',
        'galeria': [
          {
            'url': 'https://cdn.fashionstore.test/vestido-frontal.jpg',
            'etiqueta': 'FRONTAL',
            'orden': 1,
          },
          {
            'url': 'https://cdn.fashionstore.test/vestido-espalda.jpg',
            'etiqueta': 'ESPALDA',
            'orden': 2,
          },
        ],
      });

      // Con las claves antiguas (`imagen_url`, `galeria_angulos`) la ficha mostraba
      // siempre el placeholder y ningún carrusel multiángulo.
      expect(
        producto.imagenUrl,
        'https://cdn.fashionstore.test/vestido-frontal.jpg',
      );
      expect(producto.galeriaAngulos, hasLength(2));
      expect(producto.galeriaAngulos.first.etiqueta, 'FRONTAL');
    });
  });
}
