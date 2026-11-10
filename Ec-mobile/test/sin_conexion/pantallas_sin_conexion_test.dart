import 'dart:async';
import 'dart:convert';

import 'package:ec_mobile/src/core/sin_conexion/almacen_local.dart';
import 'package:ec_mobile/src/core/sin_conexion/modelos_sin_conexion.dart';
import 'package:ec_mobile/src/core/sin_conexion/sin_conexion_api.dart';
import 'package:ec_mobile/src/core/sin_conexion/sin_conexion_servicio.dart';
import 'package:ec_mobile/src/modulos/sincronizacion/cu14_catalogo_local/presentacion/pantalla_catalogo_sin_conexion.dart';
import 'package:ec_mobile/src/modulos/sincronizacion/cu19_sincronizacion/presentacion/pantalla_sincronizacion.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// Paquete literal de `GET /sin-conexion/catalogo` (`CatalogoLocalOut.model_dump_json`), con una
/// sucursal sin existencias.
const _catalogo =
    '{"generado_en":"2026-11-09T15:00:00Z","modo":"completo","moneda":"BOB","productos":[{"id_producto":5,"nombre":"Camisa formal blanca","descripcion":"Algodón","id_categoria":2,"precio_base":"350.00","imagen_url":null,"variantes":[{"id_variante":41,"sku":"MSH-CAM-M","id_talla":2,"id_color":1,"precio":"350.00"}]}],"categorias":[{"id_categoria":2,"nombre":"Camisas formales","id_categoria_padre":null}],"tallas":[{"id_talla":2,"codigo":"M","orden":2}],"colores":[{"id_color":1,"nombre":"Blanco","codigo_hex":"#FFFFFF"}],"promociones":[],"sucursales":[{"id_sucursal":3,"nombre":"Menshopping Santa Cruz","direccion":"Dirección por confirmar","ciudad":"Santa Cruz de la Sierra","horario_apertura":"09:00","horario_cierre":"20:00"},{"id_sucursal":4,"nombre":"Menshopping Beni","direccion":"Dirección por confirmar","ciudad":"Trinidad","horario_apertura":"09:00","horario_cierre":"20:00"}],"existencias":[{"id_variante":41,"id_sucursal":3,"cantidad_disponible":5},{"id_variante":41,"id_sucursal":4,"cantidad_disponible":0}]}';

void main() {
  sqfliteFfiInit();

  late AlmacenSqlite almacen;
  late StreamController<bool> red;
  late SinConexionServicio servicio;

  /// Teléfono ya preparado con conexión antes; ahora sin red.
  Future<void> prepararSinRed(WidgetTester tester) async {
    almacen = AlmacenSqlite(fabrica: databaseFactoryFfi, ruta: inMemoryDatabasePath);
    red = StreamController<bool>();
    servicio = SinConexionServicio(
      almacen: almacen,
      api: SinConexionApi(
        cliente: MockClient((_) async => throw http.ClientException('Sin red')),
        baseUrl: () => 'http://servidor',
      ),
      cambiosDeRed: red.stream,
      enLineaInicial: false,
    );
    await tester.runAsync(() async {
      await almacen.guardarDispositivo(const DispositivoLocal(
        clave: 'menshopping:10',
        identificador: 'uuid',
        codigoCorto: '3F9A',
        parametros: ParametrosSinConexion(
            operacionOfflineHabilitada: true, diasAntiguedadOffline: 7, horasVencimientoReserva: 24, moneda: 'BOB'),
      ));
      await almacen.guardarCatalogo(
          'menshopping', jsonDecode(_catalogo) as Map<String, dynamic>, DateTime.utc(2026, 11, 9, 15));
      await servicio.prepararTienda(codigoTienda: 'menshopping', idCliente: 10, token: 'token');
    });
  }

  tearDown(() async {
    servicio.dispose();
    await red.close();
    await almacen.cerrar();
  });

  testWidgets('reserva sin conexión desde el catálogo guardado (CU14 A4, CU15 A1)', (tester) async {
    await prepararSinRed(tester);
    await tester.pumpWidget(MaterialApp(home: PantallaCatalogoSinConexion(servicio: servicio)));
    await tester.pumpAndSettle();

    expect(find.textContaining('Puede estar desactualizado'), findsOneWidget);
    await tester.tap(find.text('Camisa formal blanca'));
    await tester.pumpAndSettle();

    expect(find.text('Sin existencias'), findsOneWidget); // Beni
    await tester.tap(find.text('Menshopping Santa Cruz'));
    await tester.pumpAndSettle();
    await tester.tap(find.byType(ChoiceChip).first);
    await tester.pumpAndSettle();

    await tester.ensureVisible(find.byKey(const Key('reservar-sin-conexion')));
    await tester.tap(find.byKey(const Key('reservar-sin-conexion')));
    // La escritura en SQLite es E/S real: se le deja terminar fuera del reloj simulado.
    for (var i = 0; i < 5; i++) {
      await tester.runAsync(() => Future<void>.delayed(const Duration(milliseconds: 50)));
      await tester.pump();
    }
    await tester.pumpAndSettle();

    expect(find.textContaining('Reserva PROV-3F9A-000001 guardada'), findsOneWidget);
    final guardadas = await tester.runAsync(() => almacen.operaciones('menshopping:10'));
    expect(guardadas!.single.estado, EstadoOperacion.registradaLocalmente);
    expect(guardadas.single.idSucursal, 3);
  });

  testWidgets('la hoja «Sincronización» muestra cada operación con su estado (RN36)', (tester) async {
    await prepararSinRed(tester);
    await tester.runAsync(() => servicio.reservarSinConexion(
          idSucursal: 3,
          fechaHoraAtencion: DateTime.utc(2026, 11, 10, 14),
          items: [
            {'id_variante': 41, 'cantidad': 1},
          ],
          titulo: 'Camisa formal blanca',
          detalle: 'M · Blanco · Menshopping Santa Cruz',
        ));
    await tester.pumpWidget(MaterialApp(home: PantallaSincronizacion(servicio: servicio)));
    await tester.pumpAndSettle();

    expect(find.byType(BackButton), findsOneWidget); // hoja: con retroceso
    expect(find.text('Sin conexión'), findsOneWidget);
    expect(find.text('Camisa formal blanca'), findsOneWidget);
    expect(find.text('Registrada en el teléfono'), findsOneWidget);
    expect(find.text('PROV-3F9A-000001'), findsOneWidget);
    expect(find.text('Los avisos se consultan con conexión.'), findsOneWidget);
  });
}
