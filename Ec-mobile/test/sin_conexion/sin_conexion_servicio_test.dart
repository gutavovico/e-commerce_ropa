import 'dart:async';
import 'dart:convert';

import 'package:ec_mobile/src/core/sin_conexion/almacen_local.dart';
import 'package:ec_mobile/src/core/sin_conexion/franjas_cita.dart';
import 'package:ec_mobile/src/core/sin_conexion/modelos_sin_conexion.dart';
import 'package:ec_mobile/src/core/sin_conexion/sin_conexion_api.dart';
import 'package:ec_mobile/src/core/sin_conexion/sin_conexion_servicio.dart';
import 'package:ec_mobile/src/core/sin_conexion/token_jwt.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:sqflite_common_ffi/sqflite_ffi.dart';

/// P2-CU14 / CU15 A1 / CU19 en Flutter. Los payloads son literales generados con los esquemas
/// Pydantic del backend (`model_dump_json`), no objetos armados sobre los DTO: así se ejercita
/// `fromJson` de verdad (lección de CU12, ver CLAUDE.md).
const _dispositivo =
    '{"id_dispositivo":1,"identificador":"3f9a2c1e-1111-4222-8333-444455556666","plataforma":"flutter","codigo_corto":"3F9A","registrado_en":"2026-11-09T15:00:00Z","ultima_descarga_en":null,"operacion_offline_habilitada":true,"dias_antiguedad_offline":7,"horas_vencimiento_reserva":24,"moneda":"BOB"}';
const _catalogo =
    '{"generado_en":"2026-11-09T15:00:00Z","modo":"completo","moneda":"BOB","productos":[{"id_producto":5,"nombre":"Camisa formal blanca","descripcion":"Algodón","id_categoria":2,"precio_base":"350.00","imagen_url":"/ar/menshopping_camisa.png","variantes":[{"id_variante":41,"sku":"MSH-CAM-M","id_talla":2,"id_color":1,"precio":"350.00"}]}],"categorias":[{"id_categoria":2,"nombre":"Camisas formales","id_categoria_padre":null}],"tallas":[{"id_talla":2,"codigo":"M","orden":2}],"colores":[{"id_color":1,"nombre":"Blanco","codigo_hex":"#FFFFFF"}],"promociones":[],"sucursales":[{"id_sucursal":3,"nombre":"Menshopping Santa Cruz","direccion":"Dirección por confirmar","ciudad":"Santa Cruz de la Sierra","horario_apertura":"09:00","horario_cierre":"20:00"}],"existencias":[{"id_variante":41,"id_sucursal":3,"cantidad_disponible":5}]}';
const _bandeja =
    '{"no_leidos":1,"avisos":[{"id_aviso":4,"tipo":"reserva_cancelada","titulo":"Reserva PROV-3F9A-000002 cancelada","mensaje":"No pudimos confirmar tu reserva PROV-3F9A-000002: Ya no quedan unidades suficientes en la sucursal.","id_reserva":null,"id_venta":null,"creado_en":"2026-11-09T15:00:00Z","leido":false}]}';

String _lote(String uuid, String estado, {String? motivo, String? codigo}) => jsonEncode({
      'id_sync_log': 88,
      'resultados': [
        {
          'uuid': uuid,
          'estado': estado,
          'motivo': motivo,
          'mensaje': estado == 'confirmada' ? 'Reserva confirmada.' : 'Ya no quedan unidades suficientes en la sucursal.',
          'codigo_reserva': codigo,
          'id_reserva': codigo == null ? null : 123,
          'id_venta': null,
          'id_conflicto': null,
          'repetida': false,
        },
      ],
    });

/// Servidor falso: responde según la ruta y guarda lo que recibe.
class _Servidor {
  final peticiones = <http.Request>[];
  bool sinRed = false;
  String Function(Map<String, dynamic> cuerpo) respuestaSincronizar = (_) => '{"id_sync_log":1,"resultados":[]}';

  late final MockClient cliente = MockClient((peticion) async {
    peticiones.add(peticion);
    if (sinRed) throw http.ClientException('Sin red');
    final ruta = peticion.url.path;
    http.Response ok(String cuerpo) =>
        http.Response.bytes(utf8.encode(cuerpo), 200, headers: {'content-type': 'application/json'});
    return switch (ruta) {
      '/api/v1/sin-conexion/dispositivos' => ok(_dispositivo),
      '/api/v1/sin-conexion/catalogo' => ok(_catalogo),
      '/api/v1/sin-conexion/operaciones' => ok('[]'),
      '/api/v1/avisos' => ok(_bandeja),
      '/api/v1/sin-conexion/sincronizar' =>
        ok(respuestaSincronizar(jsonDecode(peticion.body) as Map<String, dynamic>)),
      '/api/v1/health' => ok('{"status":"ok"}'),
      _ => http.Response('{}', 404),
    };
  });

  Iterable<Map<String, dynamic>> cuerposSincronizados() => peticiones
      .where((p) => p.url.path == '/api/v1/sin-conexion/sincronizar')
      .map((p) => jsonDecode(p.body) as Map<String, dynamic>);
}

void main() {
  sqfliteFfiInit();

  late _Servidor servidor;
  late AlmacenSqlite almacen;
  late StreamController<bool> red;
  late SinConexionServicio servicio;

  setUp(() {
    servidor = _Servidor();
    almacen = AlmacenSqlite(fabrica: databaseFactoryFfi, ruta: inMemoryDatabasePath);
    red = StreamController<bool>();
    servicio = SinConexionServicio(
      almacen: almacen,
      api: SinConexionApi(cliente: servidor.cliente, baseUrl: () => 'http://servidor'),
      cambiosDeRed: red.stream,
    );
  });

  tearDown(() async {
    servicio.dispose();
    await red.close();
    await almacen.cerrar();
  });

  Future<void> preparar() =>
      servicio.prepararTienda(codigoTienda: 'menshopping', idCliente: 10, token: 'token');

  Future<OperacionLocal> reservar() => servicio.reservarSinConexion(
        idSucursal: 3,
        fechaHoraAtencion: DateTime.utc(2026, 11, 10, 14),
        items: [
          {'id_variante': 41, 'cantidad': 1},
        ],
        titulo: 'Camisa formal blanca',
        detalle: 'M · Blanco · Menshopping Santa Cruz',
      );

  group('DTO con payloads literales del backend', () {
    test('catálogo: importes como cadena y existencias por variante y sucursal', () {
      final c = CatalogoLocal.fromJson(jsonDecode(_catalogo) as Map<String, dynamic>);
      expect(c.productos.single.precioBase, '350.00');
      expect(c.productos.single.variantes.single.precio, '350.00');
      expect(c.tallas[2], 'M');
      expect(c.disponible(41, 3), 5);
      expect(c.disponible(41, 99), 0);
    });

    test('dispositivo y bandeja', () {
      final d = DispositivoDto.fromJson(jsonDecode(_dispositivo) as Map<String, dynamic>);
      expect(d.codigoCorto, '3F9A');
      expect(d.parametros.horasVencimientoReserva, 24);
      final b = BandejaAvisosDto.fromJson(jsonDecode(_bandeja) as Map<String, dynamic>);
      expect(b.noLeidos, 1);
      expect(b.avisos.single.tipo, 'reserva_cancelada');
    });
  });

  test('prepara la tienda: dispositivo Flutter, catálogo en SQLite y avisos', () async {
    await preparar();
    final registro = servidor.peticiones.firstWhere((p) => p.url.path == '/api/v1/sin-conexion/dispositivos');
    expect(jsonDecode(registro.body)['plataforma'], 'flutter');
    expect(registro.headers['Authorization'], 'Bearer token');
    expect(servicio.preparado, isTrue);
    expect(servicio.catalogo!.productos.single.nombre, 'Camisa formal blanca');
    expect(servicio.avisosNoLeidos, 1);
    expect((await almacen.catalogo('menshopping'))!.$1.moneda, 'BOB');
  });

  test('sin red trabaja con lo guardado (CU14 A4) y no llama a la API', () async {
    await preparar();
    servidor.peticiones.clear();
    await servicio.forzarEstadoDeRed(false);
    await preparar();
    expect(servicio.catalogo, isNotNull);
    expect(servidor.peticiones, isEmpty);
  });

  test('una descarga fallida conserva el catálogo anterior (CU14 A2)', () async {
    await preparar();
    servidor.sinRed = true;
    await expectLater(servicio.descargarCatalogo(), throwsA(isA<SinConexionException>()));
    expect(servicio.catalogo, isNotNull);
  });

  test('reserva sin red: código PROV correlativo y pendiente (CU15 A1, RN34)', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    final a = await reservar();
    final b = await reservar();
    expect(a.codigoProvisional, 'PROV-3F9A-000001');
    expect(b.codigoProvisional, 'PROV-3F9A-000002');
    expect(servicio.pendientes.length, 2);
    expect((await almacen.operaciones('menshopping:10')).length, 2);
  });

  test('al volver la red sincroniza, guarda el resultado y conserva la operación (RN36, RN37)', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    final op = await reservar();
    servidor.respuestaSincronizar = (_) => _lote(op.uuid, 'confirmada', codigo: 'RES-2026-0123');
    await servicio.forzarEstadoDeRed(true);

    final enviado = servidor.cuerposSincronizados().single['operaciones'][0] as Map<String, dynamic>;
    expect(enviado['uuid'], op.uuid);
    expect(enviado['codigo_provisional'], 'PROV-3F9A-000001');
    final guardada = (await almacen.operaciones('menshopping:10')).single;
    expect(guardada.estado, EstadoOperacion.confirmada);
    expect(guardada.codigoReserva, 'RES-2026-0123');
    expect(servicio.pendientes, isEmpty);
  });

  test('una reserva rechazada guarda el motivo', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    final op = await reservar();
    servidor.respuestaSincronizar = (_) => _lote(op.uuid, 'rechazada', motivo: 'STOCK_INSUFICIENTE');
    await servicio.forzarEstadoDeRed(true);
    expect(servicio.operaciones.single.estado, EstadoOperacion.rechazada);
    expect(servicio.operaciones.single.motivo, 'STOCK_INSUFICIENTE');
  });

  test('si falla la red al enviar, la operación vuelve a pendiente (CU19 A1)', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    await reservar();
    servidor.sinRed = true;
    await servicio.forzarEstadoDeRed(true);
    expect(servicio.operaciones.single.estado, EstadoOperacion.registradaLocalmente);
    expect((await almacen.operaciones('menshopping:10')).single.pendiente, isTrue);
  });

  test('la compra interrumpida solo envía id_venta e id_pago', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    final op = await servicio.registrarCompraInterrumpida(idVenta: 501, idPago: 90, comprobante: 'MOV-2026-00501');
    servidor.respuestaSincronizar = (_) => _lote(op!.uuid, 'en_conflicto', motivo: 'STOCK_INSUFICIENTE');
    await servicio.forzarEstadoDeRed(true);
    final enviado = servidor.cuerposSincronizados().single['operaciones'][0] as Map<String, dynamic>;
    expect(enviado['tipo'], 'compra_interrumpida');
    expect(enviado['datos'], {'id_venta': 501, 'id_pago': 90});
    expect(servicio.operaciones.single.estado, EstadoOperacion.enConflicto);
  });

  test('una tienda que no permite operar sin conexión no deja reservar (CU14 A5)', () async {
    await preparar();
    final local = await almacen.dispositivo('menshopping:10');
    await almacen.guardarDispositivo(local!.copyWith(
      parametros: const ParametrosSinConexion(
          operacionOfflineHabilitada: false, diasAntiguedadOffline: 7, horasVencimientoReserva: 24, moneda: 'BOB'),
    ));
    await servicio.forzarEstadoDeRed(false);
    await preparar();
    expect(servicio.puedeReservarSinConexion, isFalse);
    await expectLater(reservar(), throwsA(isA<SinConexionException>()));
  });

  test('al cerrar sesión se borra el catálogo, nunca las operaciones (RNF03)', () async {
    await preparar();
    await servicio.forzarEstadoDeRed(false);
    await reservar();
    await servicio.cerrarSesion();
    expect(await almacen.catalogo('menshopping'), isNull);
    expect((await almacen.operaciones('menshopping:10')).length, 1);
  });

  group('franjasDeCita (P2-CU15, RN25)', () {
    test('solo horas dentro del vencimiento y del horario de la tienda', () {
      final ahora = DateTime(2026, 11, 9, 10, 15);
      final franjas = franjasDeCita(ahora, 24, maximo: 50);
      expect(franjas.first.etiqueta, 'Hoy 12:00');
      for (final f in franjas) {
        expect(f.instante.isAfter(ahora.add(const Duration(hours: 1))), isTrue);
        expect(f.instante.isAfter(ahora.add(const Duration(hours: 24))), isFalse);
        expect(f.instante.hour, inInclusiveRange(9, 19));
      }
    });

    test('con poco plazo por la noche no ofrece ninguna', () {
      expect(franjasDeCita(DateTime(2026, 11, 9, 21), 2), isEmpty);
    });
  });

  test('lee el id y el rol del JWT sin validarlo (la firma la comprueba el servidor)', () {
    String parte(Map<String, dynamic> m) => base64Url.encode(utf8.encode(jsonEncode(m))).replaceAll('=', '');
    final token = '${parte({'alg': 'HS256'})}.${parte({'sub': '10', 'rol': 'cliente'})}.firma';
    expect(leerToken(token), (idUsuario: 10, rol: 'cliente'));
    expect(leerToken('no-es-un-jwt'), (idUsuario: null, rol: null));
  });
}
