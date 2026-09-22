import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/datos/datasources/carrito_api.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/datos/modelos/carrito_dto.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/presentacion/bloc/carrito_bloc.dart';
import 'package:ec_mobile/src/modulos/compras_pagos/cu11_gestionar_carrito/presentacion/pantallas/shopping_bag_screen.dart';

import 'mocks/mock_carrito_api.dart';

const String kToken = 'jwt-de-prueba';

Widget crearApp(Widget pantalla) {
  return MaterialApp(
    theme: ThemeData(fontFamily: 'Outfit'),
    home: pantalla,
  );
}

void main() {
  // =========================================================================
  // Contrato de los DTO con el backend
  // =========================================================================
  group('Contrato CU11/CU15 con el backend', () {
    test('CarritoDto.fromJson lee la respuesta real de GET /api/v1/carrito', () {
      final carrito = CarritoDto.fromJson(respuestaCarritoBackend);

      expect(carrito.idCarrito, 77);
      expect(carrito.items, hasLength(1));
      expect(carrito.estaVacia, false);

      final item = carrito.items.first;
      expect(item.idCarritoDetalle, 44);
      expect(item.nombreProducto, 'Vestido plisado en seda natural');
      expect(item.nombreSucursal, 'Atelier Serrano - Madrid');
      expect(item.cantidadMaxima, 15);
      // FastAPI serializa Decimal como cadena JSON: debe parsearse con tolerancia.
      expect(item.precioLista, 890.00);
      expect(item.precioUnitario, 756.50);
      expect(item.descuentoLinea, 133.50);
      expect(item.motivoDescuento, 'Membresia Prive');
    });

    test('CarritoResumenDto respeta la invariante total = subtotal - descuento', () {
      final carrito = CarritoDto.fromJson(respuestaCarritoBackend);
      final resumen = carrito.resumen;

      expect(resumen.subtotal, 1780.00);
      expect(resumen.descuento, 267.00);
      expect(resumen.total, 1513.00);
      expect(resumen.subtotal - resumen.descuento, closeTo(resumen.total, 0.001));
      // El IVA va incluido en el precio: es informativo, no se suma.
      expect(resumen.ivaIncluido, 262.62);
    });

    test('VentaCreadaDto.fromJson lee la respuesta real de POST /api/v1/ventas/checkout', () {
      final venta = VentaCreadaDto.fromJson(respuestaVentaBackend);

      expect(venta.numeroComprobante, 'FS-2026-000001');
      expect(venta.estado, 'pendiente');
      expect(venta.total, 1513.00);
      expect(venta.totalPrendas, 2);
      expect(venta.items, hasLength(1));
      expect(venta.items.first.precioUnitario, 756.50);
      expect(venta.expiraEn, isNotNull);
      expect(venta.mensajeConfirmacion, contains('25 minutos'));
    });

    test('CheckoutInDto.toJson usa las claves que exige el backend', () {
      final payload = const CheckoutInDto(
        tipoEntrega: TipoEntrega.domicilio,
        direccionEnvio: '  Calle de Claudio Coello 48  ',
        codigoCupon: 'MAISON-2025',
      ).toJson();

      expect(payload['tipo_venta'], 'digital_movil');
      expect(payload['tipo_entrega'], 'domicilio');
      expect(payload['direccion_envio'], 'Calle de Claudio Coello 48');
      expect(payload['id_sucursal_retiro'], isNull);
      expect(payload['codigo_cupon'], 'MAISON-2025');
      // El servidor es la fuente de verdad de los importes: no se envía ninguno.
      expect(payload.containsKey('total'), isFalse);
      expect(payload.containsKey('subtotal'), isFalse);
    });

    test('CheckoutInDto omite la dirección en la recogida en boutique', () {
      final payload = const CheckoutInDto(
        tipoEntrega: TipoEntrega.recogidaBoutique,
        direccionEnvio: 'Ignorar esta dirección',
        idSucursalRetiro: 1,
      ).toJson();

      expect(payload['tipo_entrega'], 'recogida_boutique');
      expect(payload['id_sucursal_retiro'], 1);
      expect(payload['direccion_envio'], isNull);
    });

    test('parsearImporte tolera cadenas, números y valores ausentes', () {
      expect(parsearImporte('890.00'), 890.0);
      expect(parsearImporte(740), 740.0);
      expect(parsearImporte(null), 0.0);
      expect(parsearImporte('no-es-un-numero'), 0.0);
    });
  });

  // =========================================================================
  // BLoC
  // =========================================================================
  group('CarritoBloc', () {
    test('carga la bolsa y expone el resumen', () async {
      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await bloc.cargarCarrito();

      expect(bloc.estado, isA<CarritoCargado>());
      final estado = bloc.estado as CarritoCargado;
      expect(estado.items, hasLength(1));
      expect(estado.resumen.total, 1513.00);
      expect(bloc.totalPrendas, 2);
    });

    test('una bolsa sin prendas transiciona a CarritoVacio, no a error', () async {
      final bloc = CarritoBloc(api: MockCarritoApi(bolsaVacia: true), token: kToken);
      await bloc.cargarCarrito();

      // El backend responde 200 con lista vacía: es un estado legítimo.
      expect(bloc.estado, isA<CarritoVacio>());
      expect(bloc.totalPrendas, 0);
    });

    test('un fallo de red transiciona a CarritoError con el mensaje del backend', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: _ApiQueFalla(), token: kToken);
      await bloc.cargarCarrito();

      expect(bloc.estado, isA<CarritoError>());
      expect((bloc.estado as CarritoError).mensaje, contains('atelier'));
      expect(api.llamadasAgregar, 0);
    });

    test('incrementar envía la cantidad absoluta', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      final item = (bloc.estado as CarritoCargado).items.first;
      await bloc.incrementar(item);

      expect(api.llamadasActualizar, 1);
      // Cantidad 2 en la bolsa -> se envía 3, no un incremento de 1.
      expect(api.ultimaCantidadEnviada, 3);
    });

    test('no llama al backend si ya se alcanzó el tope de existencias', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      final item = (bloc.estado as CarritoCargado).items.first;
      final topeado = CarritoItemDto(
        idCarritoDetalle: item.idCarritoDetalle,
        idVariante: item.idVariante,
        idProducto: item.idProducto,
        nombreProducto: item.nombreProducto,
        sku: item.sku,
        tallaCodigo: item.tallaCodigo,
        colorNombre: item.colorNombre,
        precioLista: item.precioLista,
        precioUnitario: item.precioUnitario,
        cantidad: 15,
        idSucursal: item.idSucursal,
        nombreSucursal: item.nombreSucursal,
        stockDisponible: 15,
        cantidadMaxima: 15,
        subtotalLinea: item.subtotalLinea,
      );

      final exito = await bloc.incrementar(topeado);

      expect(exito, false);
      expect(api.llamadasActualizar, 0);
      expect(
        (bloc.estado as CarritoCargado).mensajeNotificacion,
        contains('existencias disponibles'),
      );
    });

    test('decrementar no baja de una unidad', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      final item = (bloc.estado as CarritoCargado).items.first;
      final unaUnidad = CarritoItemDto(
        idCarritoDetalle: item.idCarritoDetalle,
        idVariante: item.idVariante,
        idProducto: item.idProducto,
        nombreProducto: item.nombreProducto,
        sku: item.sku,
        tallaCodigo: item.tallaCodigo,
        colorNombre: item.colorNombre,
        precioLista: item.precioLista,
        precioUnitario: item.precioUnitario,
        cantidad: 1,
        idSucursal: item.idSucursal,
        nombreSucursal: item.nombreSucursal,
        stockDisponible: 15,
        cantidadMaxima: 15,
        subtotalLinea: item.subtotalLinea,
      );

      // Para retirar una prenda se usa la papelera, no una cantidad de cero.
      expect(await bloc.decrementar(unaUnidad), false);
      expect(api.llamadasActualizar, 0);
    });

    test('revierte la actualización optimista si el backend la rechaza', () async {
      final api = MockCarritoApi(
        excepcion: const CarritoException(
          'No hay existencias suficientes. Disponibles: 2, solicitadas: 3.',
          codigoHttp: 409,
          codigo: 'STOCK_INSUFICIENTE',
        ),
      );
      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await bloc.cargarCarrito();

      final cantidadPrevia = (bloc.estado as CarritoCargado).items.first.cantidad;

      // Se sustituye el API por uno que falla para la siguiente operación.
      final blocQueFalla = CarritoBloc(api: api, token: kToken);
      await blocQueFalla.cargarCarrito();
      final item = (blocQueFalla.estado as CarritoCargado).items.first;

      final exito = await blocQueFalla.incrementar(item);

      expect(exito, false);
      final estado = blocQueFalla.estado as CarritoCargado;
      // La cifra vuelve a su valor previo: la bolsa del servidor no cambió.
      expect(estado.items.first.cantidad, cantidadPrevia);
      expect(estado.mensajeNotificacion, contains('Disponibles: 2'));
      expect(estado.lineaEnCurso, isNull);
    });

    test('eliminar la última prenda deja la bolsa en estado vacío', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      final item = (bloc.estado as CarritoCargado).items.first;
      await bloc.eliminar(item);

      expect(api.llamadasEliminar, 1);
      expect(bloc.estado, isA<CarritoVacio>());
    });

    test('tramitar exige dirección en la entrega a domicilio', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      expect((bloc.estado as CarritoCargado).puedeTramitar, false);
      expect(await bloc.tramitarPedido(), false);
      expect(api.llamadasCheckout, 0);

      bloc.actualizarDireccion('Calle de Claudio Coello 48, 28001 Madrid');
      expect((bloc.estado as CarritoCargado).puedeTramitar, true);
    });

    test('tramitar exige boutique en la recogida en tienda', () async {
      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await bloc.cargarCarrito();

      bloc.seleccionarEntrega(TipoEntrega.recogidaBoutique);
      expect((bloc.estado as CarritoCargado).puedeTramitar, false);

      bloc.seleccionarBoutique(1);
      expect((bloc.estado as CarritoCargado).puedeTramitar, true);
    });

    test('tramitar vacía la bolsa y expone la orden confirmada', () async {
      final api = MockCarritoApi();
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      bloc.actualizarDireccion('Calle de Claudio Coello 48, 28001 Madrid');
      final exito = await bloc.tramitarPedido();

      expect(exito, true);
      expect(api.llamadasCheckout, 1);
      expect(api.ultimoPayloadCheckout?['tipo_venta'], 'digital_movil');

      final estado = bloc.estado as CarritoCargado;
      expect(estado.ordenConfirmada?.numeroComprobante, 'FS-2026-000001');
      expect(estado.carrito.estaVacia, true);
    });

    test('retira el cupón cuando el backend lo rechaza, para permitir reintentar', () async {
      final api = MockCarritoApi(
        excepcion: const CarritoException(
          "El código 'NO-EXISTE' no corresponde a ninguna invitación.",
          codigoHttp: 400,
          codigo: 'CUPON_INVALIDO',
        ),
      );
      final bloc = CarritoBloc(api: api, token: kToken);
      await bloc.cargarCarrito();

      bloc.actualizarDireccion('Serrano 48');
      bloc.aplicarCupon('NO-EXISTE');
      expect((bloc.estado as CarritoCargado).cuponAplicado, 'NO-EXISTE');

      await bloc.tramitarPedido();

      final estado = bloc.estado as CarritoCargado;
      expect(estado.cuponAplicado, isNull);
      expect(estado.mensajeNotificacion, contains('no corresponde'));
    });

    test('aplicarCupon ignora un código en blanco y recorta espacios', () async {
      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await bloc.cargarCarrito();

      bloc.aplicarCupon('   ');
      expect((bloc.estado as CarritoCargado).cuponAplicado, isNull);

      bloc.aplicarCupon('  MAISON-2025  ');
      expect((bloc.estado as CarritoCargado).cuponAplicado, 'MAISON-2025');
    });
  });

  // =========================================================================
  // Pantalla
  // =========================================================================
  group('ShoppingBagScreen', () {
    testWidgets('se abre sin BottomNavigationBar y con botón de retorno', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      // Pantalla hoja: la barra de 4 pestañas pertenece en exclusiva al hub raíz.
      expect(find.byType(BottomNavigationBar), findsNothing);
      expect(find.byType(BackButton), findsOneWidget);
      expect(find.text('Shopping Bag'), findsOneWidget);
    });

    testWidgets('muestra la barra de acción fija con el total y TRAMITAR PEDIDO',
        (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('TRAMITAR PEDIDO'), findsOneWidget);
      expect(find.text('TOTAL PEDIDO'), findsOneWidget);
      expect(find.textContaining('1513.00'), findsWidgets);
    });

    testWidgets('renderiza la prenda con su boutique de expedición y el descuento',
        (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Vestido plisado en seda natural'), findsOneWidget);
      expect(find.textContaining('Atelier Serrano - Madrid'), findsWidgets);
      expect(find.textContaining('Membresia Prive'), findsOneWidget);
      expect(find.text('Talla: 40 · Color: Rojo Carmín'), findsOneWidget);
    });

    testWidgets('muestra el estado vacío con salida al catálogo', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(bolsaVacia: true), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('Tu bolsa está vacía'), findsOneWidget);
      expect(find.text('EXPLORAR EL CATÁLOGO'), findsOneWidget);
      // Sin prendas no hay nada que tramitar: la barra de acción no se muestra.
      expect(find.text('TRAMITAR PEDIDO'), findsNothing);
    });

    testWidgets('muestra el error con opción de reintentar', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: _ApiQueFalla(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      expect(find.text('REINTENTAR'), findsOneWidget);
    });

    testWidgets('el selector de entrega revela el campo de dirección', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      // Por defecto, entrega a domicilio con su campo de dirección visible.
      expect(find.text('Entrega a Domicilio'), findsOneWidget);
      expect(find.text('Recogida en Boutique Insignia'), findsOneWidget);

      bloc.seleccionarEntrega(TipoEntrega.recogidaBoutique);
      await tester.pumpAndSettle();

      // Al elegir recogida aparece el directorio de boutiques reales.
      expect(find.textContaining('Calle Serrano 48'), findsWidgets);
    });

    testWidgets('el botón de tramitar permanece inhabilitado sin datos de entrega',
        (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      final boton = tester.widget<ElevatedButton>(
        find.ancestor(
          of: find.text('TRAMITAR PEDIDO'),
          matching: find.byType(ElevatedButton),
        ),
      );
      expect(boton.onPressed, isNull);

      bloc.actualizarDireccion('Calle de Claudio Coello 48, 28001 Madrid');
      await tester.pumpAndSettle();

      final botonActivo = tester.widget<ElevatedButton>(
        find.ancestor(
          of: find.text('TRAMITAR PEDIDO'),
          matching: find.byType(ElevatedButton),
        ),
      );
      expect(botonActivo.onPressed, isNotNull);
    });

    testWidgets('muestra la confirmación de la orden tras tramitar', (tester) async {
      tester.view.physicalSize = const Size(1080, 2400);
      tester.view.devicePixelRatio = 2.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      final bloc = CarritoBloc(api: MockCarritoApi(), token: kToken);
      await tester.pumpWidget(crearApp(
        ShoppingBagScreen(token: kToken, bloc: bloc, habilitarImagenesRed: false),
      ));
      await tester.pumpAndSettle();

      bloc.actualizarDireccion('Calle de Claudio Coello 48, 28001 Madrid');
      await bloc.tramitarPedido();
      await tester.pumpAndSettle();

      expect(find.textContaining('FS-2026-000001'), findsOneWidget);
      expect(find.text('CONTINUAR EXPLORANDO'), findsOneWidget);
      // Con la orden ya emitida, la barra de acción desaparece.
      expect(find.text('TRAMITAR PEDIDO'), findsNothing);
    });
  });
}

/// Doble que falla en la carga, para ejercitar el estado de error.
class _ApiQueFalla implements CarritoApi {
  @override
  Future<CarritoDto> obtenerCarrito({required String token}) async {
    throw const CarritoException('No se pudo conectar con el atelier al consultar tu bolsa.');
  }

  @override
  Future<CarritoDto> agregarItem(ItemAgregarInDto datos, {required String token}) async =>
      throw const CarritoException('fallo');

  @override
  Future<CarritoDto> actualizarCantidad(
    int idCarritoDetalle,
    int cantidad, {
    required String token,
  }) async =>
      throw const CarritoException('fallo');

  @override
  Future<CarritoDto> eliminarItem(int idCarritoDetalle, {required String token}) async =>
      throw const CarritoException('fallo');

  @override
  Future<VentaCreadaDto> tramitarPedido(
    CheckoutInDto datos, {
    required String token,
  }) async =>
      throw const CarritoException('fallo');

  @override
  Future<List<BoutiqueRecogidaDto>> obtenerBoutiques() async => [];
}
