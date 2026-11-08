import 'dart:convert';
import 'dart:math' as math;

import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/datos/datasources/vestidor_api.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/datos/modelos/vestidor_dto.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/dominio/ajuste_prenda.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/dominio/plataforma_vestidor.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/dominio/prenda_vestidor.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/dominio/prompt_vton.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/dominio/recurso_prenda.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/presentacion/bloc/vestidor_bloc.dart';
import 'package:ec_mobile/src/modulos/catalogo/cu10_vestidor_virtual/presentacion/pantallas/pantalla_vestidor_virtual.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:image/image.dart' as img;

// Payloads literales copiados de las respuestas del backend (TokenVestidorDecartOut, SesionVestidorOut).
const String _jsonToken = '{"token":"eyJhbGciOiJFZERTQSJ9.e30.firma","expira_en_segundos":60,"servicio":"decart_lucy_vton_3.6"}';
const String _jsonSesion = '{"id_sesion_ar":845,"id_cliente":10,"id_producto":22,"dispositivo":"app_flutter",'
    '"motor":"ia","duracion_segundos":45,"fecha_hora":"2026-11-08T05:12:03.512000Z","resultado_url":null,"genero_interes":true}';
const String _json503 = '{"detail":"El servicio externo Decart no está disponible o carece de saldo de créditos.","code":"DECART_NO_DISPONIBLE"}';

const PrendaVestidor _camiseta = PrendaVestidor(
  idProducto: 22,
  nombre: 'Camiseta básica amarilla de algodón',
  categoriaNombre: 'Camisas',
  modeloArUrl: '/ar/camiseta_basica_amarilla_ar.png',
  tallaCodigo: 'M',
  colorNombre: 'Amarillo',
);

/// Datasource falso con respuestas construidas desde los payloads literales.
class _ApiFalsa implements VestidorApi {
  VestidorException? errorToken;
  int tokensPedidos = 0;
  final List<SesionVestidorCrearDto> sesiones = [];

  @override
  Future<TokenVestidorDto> obtenerTokenDecart({required String token}) async {
    tokensPedidos++;
    if (errorToken != null) throw errorToken!;
    return TokenVestidorDto.fromJson(jsonDecode(_jsonToken) as Map<String, dynamic>);
  }

  @override
  Future<SesionVestidorDto> registrarSesion(SesionVestidorCrearDto datos, {required String token}) async {
    sesiones.add(datos);
    return SesionVestidorDto.fromJson(jsonDecode(_jsonSesion) as Map<String, dynamic>);
  }

  @override
  Future<Uint8List> descargarRecurso(String url) async => Uint8List.fromList([1, 2, 3]);
}

VestidorBloc _crearBloc(
  _ApiFalsa api, {
  Duration timeout = const Duration(seconds: 5),
  int limite = 60,
  Duration tick = const Duration(seconds: 1),
}) =>
    VestidorBloc(
      prenda: _camiseta,
      token: 'jwt-cliente',
      api: api,
      timeoutConexion: timeout,
      limiteSegundosRealista: limite,
      tick: tick,
      baseWeb: 'https://fashionstorefront.vercel.app',
      prepararReferencia: (_) async => const ReferenciaVton(base64Jpeg: 'QUJD', ancho: 659, alto: 824),
    );

void main() {
  group('DTOs (payloads literales del backend)', () {
    test('TokenVestidorDto.fromJson', () {
      final dto = TokenVestidorDto.fromJson(jsonDecode(_jsonToken) as Map<String, dynamic>);
      expect(dto.token, startsWith('eyJ'));
      expect(dto.expiraEnSegundos, 60);
      expect(dto.servicio, 'decart_lucy_vton_3.6');
    });

    test('SesionVestidorDto.fromJson', () {
      final dto = SesionVestidorDto.fromJson(jsonDecode(_jsonSesion) as Map<String, dynamic>);
      expect(dto.idSesionAr, 845);
      expect(dto.motor, MotorVestidor.ia);
      expect(dto.duracionSegundos, 45);
      expect(dto.generoInteres, isTrue);
      expect(dto.resultadoUrl, isNull);
      expect(dto.fechaHora, isNotNull);
    });

    test('SesionVestidorCrearDto.toJson coincide con SesionVestidorCrearIn', () {
      const dto = SesionVestidorCrearDto(idProducto: 22, motor: MotorVestidor.local, duracionSegundos: 12);
      expect(dto.toJson(), {
        'id_producto': 22,
        'dispositivo': 'app_flutter',
        'motor': 'local',
        'duracion_segundos': 12,
        'genero_interes': false,
      });
    });
  });

  group('VestidorApiImpl (HTTP real con MockClient)', () {
    test('pide el token con canal=movil, sin cuerpo y con el JWT', () async {
      late http.Request recibida;
      final api = VestidorApiImpl(
        customBaseUrl: 'http://api.test',
        client: MockClient((req) async {
          recibida = req;
          return http.Response(_jsonToken, 200, headers: {'content-type': 'application/json'});
        }),
      );

      final token = await api.obtenerTokenDecart(token: 'jwt-cliente');

      expect(recibida.method, 'POST');
      expect(recibida.url.toString(), 'http://api.test/api/v1/vestidor/token?canal=movil');
      expect(recibida.body, isEmpty);
      expect(recibida.headers['authorization'], 'Bearer jwt-cliente');
      expect(token.expiraEnSegundos, 60);
    });

    test('un 503 del backend es VestidorException con el código de dominio', () async {
      final api = VestidorApiImpl(
        customBaseUrl: 'http://api.test',
        client: MockClient((_) async => http.Response.bytes(utf8.encode(_json503), 503)),
      );

      await expectLater(
        api.obtenerTokenDecart(token: 'jwt-cliente'),
        throwsA(isA<VestidorException>()
            .having((e) => e.codigo, 'codigo', 'DECART_NO_DISPONIBLE')
            .having((e) => e.esDecartNoDisponible, 'esDecartNoDisponible', isTrue)),
      );
    });

    test('registra la sesión con el cuerpo que espera el backend', () async {
      late Map<String, dynamic> cuerpo;
      final api = VestidorApiImpl(
        customBaseUrl: 'http://api.test',
        client: MockClient((req) async {
          cuerpo = jsonDecode(req.body) as Map<String, dynamic>;
          return http.Response(_jsonSesion, 201);
        }),
      );

      final sesion = await api.registrarSesion(
        const SesionVestidorCrearDto(idProducto: 22, motor: MotorVestidor.ia, duracionSegundos: 45, generoInteres: true),
        token: 'jwt-cliente',
      );

      expect(cuerpo['motor'], 'ia');
      expect(cuerpo['dispositivo'], 'app_flutter');
      expect(sesion.idSesionAr, 845);
    });
  });

  group('prompt VTON', () {
    test('usa el patrón de sustitución según la prenda', () {
      expect(construirPromptVton('Camiseta básica amarilla de algodón', 'Camisas'),
          'Substitute the current top with the t-shirt shown in the reference image');
      expect(construirPromptVton('Vestido plisado en seda natural', 'Vestidos'), startsWith('Substitute the current outfit with the dress'));
      expect(construirPromptVton('Pantalón sastre de tiro alto', 'Pantalones'), startsWith('Substitute the current pants with the trousers'));
      expect(construirPromptVton('Trench coat fluido', 'Chaquetas'), startsWith('Add the jacket'));
      expect(construirPromptVton('Pieza N.º 7', 'Faldas'), contains('with the skirt'));
      expect(construirPromptVton('Estopa decorativa', null), 'Substitute the current top with the garment shown in the reference image');
    });
  });

  group('recurso de la prenda', () {
    test('resuelve rutas relativas contra el frontend web', () {
      expect(resolverUrlRecurso('/ar/x.png', 'https://web.test/'), 'https://web.test/ar/x.png');
      expect(resolverUrlRecurso('https://cdn.test/x.png', 'https://web.test'), 'https://cdn.test/x.png');
      expect(resolverUrlRecurso('  ', 'https://web.test'), isNull);
      expect(resolverUrlRecurso(null, 'https://web.test'), isNull);
    });

    test('aplana el PNG transparente sobre blanco y lo codifica en JPEG', () {
      final png = img.Image(width: 600, height: 700, numChannels: 4);
      img.fill(png, color: img.ColorRgba8(0, 0, 0, 0));
      img.fillRect(png, x1: 200, y1: 200, x2: 400, y2: 500, color: img.ColorRgba8(250, 206, 3, 255));

      final referencia = prepararReferenciaVton(Uint8List.fromList(img.encodePng(png)));

      final jpg = img.decodeJpg(base64Decode(referencia.base64Jpeg))!;
      final esquina = jpg.getPixel(5, 5);
      final centro = jpg.getPixel(300, 350);
      expect(esquina.r, greaterThan(245));
      expect(esquina.b, greaterThan(245));
      expect(centro.r, greaterThan(220));
      expect(centro.b, lessThan(60));
      expect(referencia.cumpleTamanoMinimo, isTrue);
    });

    test('rechaza bytes que no son imagen', () {
      expect(() => prepararReferenciaVton(Uint8List.fromList([1, 2, 3])), throwsFormatException);
    });
  });

  group('geometría del Motor 1', () {
    test('traduce coordenadas de ML Kit con rotación y espejo como el ejemplo oficial', () {
      const imagen = Size(640, 480);
      const lienzo = Size(300, 400);
      // Android, rotación 270 (cámara frontal en vertical): ancho y alto se intercambian y se refleja.
      expect(
        traducirPunto(0, 320, tamanoImagen: imagen, tamanoLienzo: lienzo, rotacionGrados: 270, camaraFrontal: true, esIOS: false),
        const Offset(300, 200),
      );
      expect(
        traducirPunto(240, 0, tamanoImagen: imagen, tamanoLienzo: lienzo, rotacionGrados: 90, camaraFrontal: false, esIOS: false),
        const Offset(150, 0),
      );
      // Rotación 0 con cámara frontal: espejo horizontal.
      expect(
        traducirPunto(100, 50,
            tamanoImagen: const Size(300, 400), tamanoLienzo: lienzo, rotacionGrados: 0, camaraFrontal: true, esIOS: true),
        const Offset(200, 50),
      );
    });

    test('calcula centro, anchura y giro desde los hombros', () {
      final ajuste = calcularAjustePrenda(const PuntosTorso(
        hombroIzquierdo: PuntoCorporal(Offset(100, 200), 0.9),
        hombroDerecho: PuntoCorporal(Offset(200, 250), 0.9),
      ))!;
      expect(ajuste.centroHombros, const Offset(150, 225));
      expect(ajuste.ancho, closeTo(math.sqrt(100 * 100 + 50 * 50) / proporcionHombrosPrenda, 1e-9));
      expect(ajuste.rotacion, closeTo(math.atan2(50, 100), 1e-9));
    });

    test('la cámara frontal no invierte el giro (hombros en orden espejo)', () {
      final ajuste = calcularAjustePrenda(const PuntosTorso(
        hombroIzquierdo: PuntoCorporal(Offset(200, 200), 0.9),
        hombroDerecho: PuntoCorporal(Offset(100, 200), 0.9),
      ))!;
      expect(ajuste.rotacion, closeTo(0, 1e-9));
    });

    test('sin hombros fiables no hay ajuste', () {
      expect(
        calcularAjustePrenda(const PuntosTorso(
          hombroIzquierdo: PuntoCorporal(Offset(100, 200), 0.3),
          hombroDerecho: PuntoCorporal(Offset(200, 200), 0.9),
        )),
        isNull,
      );
    });

    test('el suavizado amortigua los saltos entre fotogramas', () {
      final suavizador = SuavizadorAjuste(alfa: 0.5);
      suavizador.suavizar(const AjustePrenda(centroHombros: Offset(100, 100), ancho: 100, rotacion: 0));
      final segundo = suavizador.suavizar(const AjustePrenda(centroHombros: Offset(200, 100), ancho: 200, rotacion: 0.2));
      expect(segundo.centroHombros, const Offset(150, 100));
      expect(segundo.ancho, 150);
      expect(segundo.rotacion, closeTo(0.1, 1e-9));
    });
  });

  group('VestidorBloc', () {
    test('arranca en el Motor 1 y resuelve el recurso contra el frontend web', () {
      final bloc = _crearBloc(_ApiFalsa());
      expect(bloc.estado, isA<VestidorMotorLocal>());
      expect(bloc.urlRecursoPrenda, 'https://fashionstorefront.vercel.app/ar/camiseta_basica_amarilla_ar.png');
      bloc.dispose();
    });

    test('un 503 al pedir el token conmuta al Motor 1 con aviso', () async {
      final api = _ApiFalsa()..errorToken = const VestidorException('sin créditos', codigoHttp: 503, codigo: 'DECART_NO_DISPONIBLE');
      final bloc = _crearBloc(api);

      await bloc.activarModoRealista();

      expect(bloc.estado, isA<VestidorMotorLocal>());
      expect(bloc.errorFallback, contains('no está disponible'));
      bloc.dispose();
    });

    test('prepara token, prompt y prenda para el WebView', () async {
      final bloc = _crearBloc(_ApiFalsa());

      await bloc.activarModoRealista();

      final estado = bloc.estado as VestidorConectandoRealista;
      expect(estado.datos.tokenInicial, startsWith('eyJ'));
      expect(estado.datos.prompt, contains('t-shirt'));
      expect(estado.datos.referenciaBase64, 'QUJD');
      bloc.dispose();
    });

    test('streaming → en curso; al agotar el límite vuelve al Motor 1', () async {
      final bloc = _crearBloc(_ApiFalsa(), limite: 2, tick: const Duration(milliseconds: 20));
      await bloc.activarModoRealista();

      bloc.procesarEventoRealista({'tipo': 'streaming'});
      expect((bloc.estado as VestidorRealistaEnCurso).segundosRestantes, 2);
      expect(bloc.usoRealista, isTrue);

      await Future<void>.delayed(const Duration(milliseconds: 80));
      expect(bloc.estado, isA<VestidorMotorLocal>());
      expect(bloc.aviso, contains('Límite'));
      bloc.dispose();
    });

    test('sin vídeo antes del tiempo de espera, fallback al Motor 1', () async {
      final bloc = _crearBloc(_ApiFalsa(), timeout: const Duration(milliseconds: 30));
      await bloc.activarModoRealista();

      await Future<void>.delayed(const Duration(milliseconds: 60));

      expect(bloc.estado, isA<VestidorMotorLocal>());
      expect(bloc.errorFallback, contains('Tiempo de espera'));
      bloc.dispose();
    });

    test('los errores de la página conmutan al Motor 1 con su causa', () async {
      final bloc = _crearBloc(_ApiFalsa());
      await bloc.activarModoRealista();

      bloc.procesarEventoRealista({'tipo': 'error', 'codigo': 'RED_CRITICA'});

      expect(bloc.estado, isA<VestidorMotorLocal>());
      expect(bloc.errorFallback, contains('red no permite'));
      bloc.dispose();
    });

    test('registra una sola sesión, con motor ia si Decart llegó a emitir', () async {
      final api = _ApiFalsa();
      final bloc = _crearBloc(api);
      await bloc.activarModoRealista();
      bloc.procesarEventoRealista({'tipo': 'streaming'});

      await bloc.registrarSesion(generoInteres: true);
      await bloc.registrarSesion();

      expect(api.sesiones, hasLength(1));
      expect(api.sesiones.single.motor, MotorVestidor.ia);
      expect(api.sesiones.single.generoInteres, isTrue);
      expect(api.sesiones.single.duracionSegundos, 1);
      bloc.dispose();
    });

    test('las re-marcaciones del SDK piden un token nuevo', () async {
      final api = _ApiFalsa();
      final bloc = _crearBloc(api);
      await bloc.activarModoRealista();

      expect(await bloc.solicitarTokenAdicional(), startsWith('eyJ'));
      expect(api.tokensPedidos, 2);
      bloc.dispose();
    });
  });

  group('plataforma', () {
    tearDown(() => debugDefaultTargetPlatformOverride = null);

    test('solo Android e iOS tienen cámara + ML Kit + WebView', () {
      for (final plataforma in TargetPlatform.values) {
        debugDefaultTargetPlatformOverride = plataforma;
        expect(
          vestidorSoportadoEnPlataforma(),
          plataforma == TargetPlatform.android || plataforma == TargetPlatform.iOS,
          reason: plataforma.name,
        );
      }
    });

    testWidgets('en una plataforma sin soporte la pantalla avisa en vez de romperse', (tester) async {
      debugDefaultTargetPlatformOverride = TargetPlatform.windows;
      final bloc = _crearBloc(_ApiFalsa());

      await tester.pumpWidget(MaterialApp(home: PantallaVestidorVirtual(token: 'jwt-cliente', prenda: _camiseta, bloc: bloc)));

      expect(find.text(mensajeVestidorNoSoportado), findsOneWidget);
      debugDefaultTargetPlatformOverride = null;
      await tester.pumpWidget(const SizedBox());
      bloc.dispose();
    });
  });

  group('PantallaVestidorVirtual', () {
    Widget motorLocalFalso(BuildContext context, VestidorBloc bloc,
            {required double escala, required double desplazamientoVertical}) =>
        const Center(child: Text('CAMARA-LOCAL'));
    Widget motorRealistaFalso(BuildContext context, VestidorBloc bloc, DatosSesionRealista datos) =>
        const Center(child: Text('WEBVIEW-DECART'));

    testWidgets('es una hoja con BackButton, conmuta de motor y devuelve «añadir a la bolsa»', (tester) async {
      final api = _ApiFalsa();
      final bloc = _crearBloc(api);
      ResultadoVestidor? resultado;

      await tester.pumpWidget(MaterialApp(
        home: Builder(
          builder: (context) => ElevatedButton(
            onPressed: () async {
              resultado = await Navigator.of(context).push<ResultadoVestidor>(MaterialPageRoute(
                builder: (_) => PantallaVestidorVirtual(
                  token: 'jwt-cliente',
                  prenda: _camiseta,
                  bloc: bloc,
                  constructorMotorLocal: motorLocalFalso,
                  constructorMotorRealista: motorRealistaFalso,
                ),
              ));
            },
            child: const Text('ABRIR'),
          ),
        ),
      ));
      await tester.tap(find.text('ABRIR'));
      await tester.pumpAndSettle();

      expect(find.byType(BackButton), findsOneWidget);
      expect(find.byType(BottomNavigationBar), findsNothing);
      expect(find.text('CAMARA-LOCAL'), findsOneWidget);
      expect(find.text('MOTOR 1 · LOCAL EN EL DISPOSITIVO'), findsOneWidget);
      expect(find.text('M · Amarillo'), findsOneWidget);

      await tester.tap(find.text('MODO REALISTA IA'));
      await tester.pump();
      await tester.pump();
      expect(find.text('WEBVIEW-DECART'), findsOneWidget);
      expect(find.text('MOTOR 2 · CONECTANDO'), findsOneWidget);

      bloc.procesarEventoRealista({'tipo': 'streaming'});
      await tester.pump();
      expect(find.text('MOTOR 2 · DECART LUCY VTON · 60s'), findsOneWidget);

      await tester.tap(find.text('AÑADIR A LA BOLSA'));
      await tester.pumpAndSettle();

      expect(resultado, ResultadoVestidor.anadirABolsa);
      expect(api.sesiones.single.generoInteres, isTrue);
      expect(api.sesiones.single.motor, MotorVestidor.ia);
      bloc.dispose();
    });
  });
}
